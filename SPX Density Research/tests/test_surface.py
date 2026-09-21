"""Multi-maturity numerical diagnostics and exported-file integrity checks."""
from html.parser import HTMLParser
import json
from pathlib import Path
import unittest

import numpy as np

from src.constrained import DensityFit
from src.density import Parameters, call_price, exact_density
from src.surface import calendar_diagnostic, interval_probability, normalised_calls

ROOT = Path(__file__).resolve().parents[1]


class SurfaceTests(unittest.TestCase):
    def setUp(self):
        # A uniform distribution on [0,2], mean one, divided into four bins.
        self.fit = DensityFit(np.linspace(0, 2, 5), np.full(4, .25), .9, 1., 0., 0, 0.)

    def test_normalised_call_against_uniform_formula(self):
        kappa = np.array([0., .25, 1., 1.75, 2., 3.])
        np.testing.assert_allclose(normalised_calls(self.fit, kappa),
                                   np.maximum(2 - kappa, 0) ** 2 / 4, atol=1e-12)

    def test_exact_probability_respects_partial_bins(self):
        self.assertAlmostEqual(interval_probability(self.fit, .15, 1.65), .75)
        self.assertAlmostEqual(interval_probability(self.fit, -10., 10.), 1.)
        self.assertEqual(interval_probability(self.fit, 3., 4.), 0.)
        self.assertEqual(interval_probability(self.fit, .75, .75), 0.)
        with self.assertRaises(ValueError):
            interval_probability(self.fit, 2., 1.)

    def test_calendar_flags_a_decrease_without_repairing_it(self):
        calls = np.array([[.5, .2, .01], [.6, .19, .0099999999]])
        before = calls.copy()
        result = calendar_diagnostic([.1, .2], [.5, 1., 1.5], calls)
        self.assertEqual(result["violations"], 1)
        self.assertAlmostEqual(result["maximum_decrease"], .01)
        self.assertEqual(result["pairs"][0]["minimum_change_moneyness"], 1.)
        self.assertFalse(result["constraint_enforced"])
        np.testing.assert_array_equal(calls, before)

    def test_calendar_and_normalisation_reject_invalid_inputs(self):
        for times in ([.2, .1], [.1, .1], [0, .1], [.1, float("nan")], [.1]):
            with self.assertRaises(ValueError):
                calendar_diagnostic(times, [1., 2.], np.ones((2, 2)))
        for grid in ([2., 1.], [-1., 1.], [1., 1.], [1., float("inf")]):
            with self.assertRaises(ValueError):
                calendar_diagnostic([.1, .2], grid, np.ones((2, 2)))
        for values in (np.ones((2, 3)), [[1., 2.], [1., float("nan")]]):
            with self.assertRaises(ValueError):
                calendar_diagnostic([.1, .2], [1., 2.], values)
        with self.assertRaises(ValueError):
            calendar_diagnostic([.1, .2], [1., 2.], np.ones((2, 2)), -1.)
        for grid in ([-1.], [float("nan")], [[1., 2.]]):
            with self.assertRaises(ValueError):
                normalised_calls(self.fit, grid)

    def test_saved_surface_matches_bin_masses_and_benchmark(self):
        payload = json.loads((ROOT / "results/maturity_surface.json").read_text())
        report = json.loads((ROOT / "results/surface_validation.json").read_text())
        self.assertEqual(report, payload["report"])
        self.assertEqual(report["status"], "synthetic_only")
        self.assertIsNone(report["observation_dates"])
        bins = np.loadtxt(ROOT / "results/maturity_bin_masses.csv", delimiter=",", skiprows=1)
        kappa = np.linspace(.3, 2.2, 1901)
        fitted_calls, known_calls = [], []
        for record, displayed in zip(report["marginals"], payload["slices"]):
            rows = bins[bins[:, 0] == record["days"]]
            fit = DensityFit(np.r_[rows[:, 1], rows[-1, 2]], rows[:, 3],
                             record["discount_factor"], record["forward"], 1e-6, 0, 0.)
            self.assertEqual(len(fit.mass), 120)
            self.assertGreaterEqual(fit.mass.min(), 0.)
            self.assertAlmostEqual(fit.mass.sum(), 1., places=8)
            self.assertAlmostEqual(fit.mass @ ((fit.edges[1:] + fit.edges[:-1]) / 2) / fit.forward, 1., places=8)
            p = Parameters(maturity=record["days"] / 365)
            np.testing.assert_allclose(displayed["fitted"], fit.density(payload["levels"]), atol=1e-14)
            np.testing.assert_allclose(displayed["known"], exact_density(payload["levels"], p), atol=1e-14)
            self.assertAlmostEqual(interval_probability(fit, 3000, 11000), record["fitted_mass_in_display_window"], places=12)
            self.assertLess(record["withheld_clean_price_rmse"], .3)
            self.assertLess(record["density_l1_on_support"], .08)
            fitted_calls.append(normalised_calls(fit, kappa))
            known_calls.append(call_price(kappa * fit.forward, p) / (fit.discount * fit.forward))
        times = [r["years"] for r in report["marginals"]]
        observed = calendar_diagnostic(times, kappa, fitted_calls)
        self.assertEqual(observed["violations"], report["calendar"]["violations"])
        self.assertGreater(observed["violations"], 0)  # Do not silently mask the observed limitation.
        self.assertAlmostEqual(observed["maximum_decrease"], report["calendar"]["maximum_decrease"], places=12)
        self.assertEqual(calendar_diagnostic(times, kappa, known_calls)["violations"], 0)
        overlap_count = overlap_violations = 0
        for i, pair in enumerate(report["calendar"]["pairs"]):
            a, b = report["marginals"][i:i + 2]
            lo = max(a["strike_range"][0] / a["forward"], b["strike_range"][0] / b["forward"])
            hi = min(a["strike_range"][1] / a["forward"], b["strike_range"][1] / b["forward"])
            mask = (kappa >= lo) & (kappa <= hi)
            decreases = np.asarray(fitted_calls[i + 1]) - fitted_calls[i]
            overlap_count += int(mask.sum())
            overlap_violations += int(np.count_nonzero(decreases[mask] < -1e-8))
        self.assertEqual(overlap_count, report["calendar"]["shared_quote_range_comparisons"])
        self.assertEqual(overlap_violations, report["calendar"]["shared_quote_range_violations"])

    def test_offline_html_embeds_correct_data_and_licence(self):
        class Scripts(HTMLParser):
            def __init__(self):
                super().__init__()
                self.remote = []
                self.capture = False
                self.data = ""

            def handle_starttag(self, tag, attrs):
                attributes = dict(attrs)
                if tag == "script":
                    if "src" in attributes:
                        self.remote.append(attributes["src"])
                    self.capture = attributes.get("id") == "experiment-data"

            def handle_endtag(self, tag):
                if tag == "script":
                    self.capture = False

            def handle_data(self, data):
                if self.capture:
                    self.data += data

        document = (ROOT / "interactive/density_surface.html").read_text()
        parser = Scripts()
        parser.feed(document)
        self.assertEqual(parser.remote, [])
        self.assertEqual(json.loads(parser.data), json.loads((ROOT / "results/maturity_surface.json").read_text()))
        self.assertIn("plotly.js v3.1.0", document)
        self.assertIn("Permission is hereby granted", document)
        self.assertNotIn("__EXPERIMENT_DATA__", document)
        self.assertIn("not historical dates", document)

    def test_notebook_captions_follow_embedded_figures(self):
        notebook = json.loads((ROOT / "04_density_surface.ipynb").read_text())
        cells = notebook["cells"]
        self.assertFalse(notebook["metadata"]["project_execution"]["historical_animation"])
        for number in (10, 11):
            prefix = f"Figure {number}."
            caption = next(i for i, c in enumerate(cells) if "".join(c["source"]).strip().startswith(prefix))
            self.assertIn("attachments", cells[caption - 1])
        code = [c for c in cells if c["cell_type"] == "code"]
        self.assertEqual(len(code), 1)
        self.assertEqual(code[0]["execution_count"], 1)
        self.assertTrue(code[0]["outputs"])


if __name__ == "__main__":
    unittest.main()
