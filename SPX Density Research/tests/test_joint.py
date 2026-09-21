"""Analytical calendar verification, joint fitting and saved-result checks."""
import base64
import hashlib
import json
from pathlib import Path
import re
import unittest

import numpy as np

from src.constrained import DensityFit, payoff_matrix
from src.joint import continuous_calendar_check, fit_maturities

ROOT = Path(__file__).resolve().parents[1]


class JointTests(unittest.TestCase):
    def setUp(self):
        self.edges = np.linspace(0, 2, 9)
        self.first = np.full(8, .125)
        self.delta = np.array([.1, -.125, -.125, .3, -.125, -.0125, -.125, .1125])
        self.second = self.first + self.delta

    def test_violation_between_knots_is_detected(self):
        # Both distributions are nonnegative, unit mass, and mean one. All
        # boundary prices are ordered; the gap is nevertheless negative inside.
        for w in (self.first, self.second):
            self.assertGreaterEqual(w.min(), 0)
            self.assertAlmostEqual(w.sum(), 1)
            self.assertAlmostEqual(w @ ((self.edges[1:] + self.edges[:-1]) / 2), 1)
        knot_gaps = payoff_matrix(self.edges, self.edges, 1.) @ self.delta
        self.assertGreaterEqual(knot_gaps.min(), -1e-14)
        check, cuts = continuous_calendar_check(self.edges, [self.first, self.second])
        self.assertFalse(check["passes"])
        self.assertAlmostEqual(check["minimum_gap"], -.009375)
        self.assertAlmostEqual(check["pairs"][0]["minimum_moneyness"], .875)
        self.assertIn(.875, cuts[0])

    def test_analytical_minimum_agrees_with_dense_independent_evaluation(self):
        grid = np.linspace(0, 2.5, 20001)
        values = payoff_matrix(grid, self.edges, 1.) @ self.delta
        check, _ = continuous_calendar_check(self.edges, [self.first, self.second])
        self.assertAlmostEqual(float(values.min()), check["minimum_gap"], places=10)

    def test_equal_slices_have_zero_calendar_gap(self):
        report, cuts = continuous_calendar_check(self.edges, [self.first, self.first])
        self.assertTrue(report["passes"])
        self.assertEqual(report["minimum_gap"], 0)
        self.assertEqual(cuts, [[]])

    def test_joint_solver_repairs_a_nonlognormal_counterexample(self):
        forwards, discounts = [100., 110.], [.99, .97]
        kappa = np.linspace(0, 2, 33)
        k = [F * kappa for F in forwards]
        y = [D * F * (payoff_matrix(kappa, self.edges, 1.) @ w)
             for D, F, w in zip(discounts, forwards, [self.first, self.second])]
        initial = np.array([self.first, self.second])
        independent = fit_maturities(k, y, forwards, discounts, [.1, .2], self.edges,
                                     penalty=0, enforce_calendar=False, initial_weights=initial)
        joint = fit_maturities(k, y, forwards, discounts, [.1, .2], self.edges,
                               penalty=0, enforce_calendar=True, initial_weights=initial)
        self.assertFalse(independent.continuous_check["passes"])
        self.assertTrue(joint.continuous_check["passes"])
        self.assertGreater(joint.solver["objective_sum"], independent.solver["objective_sum"])
        self.assertGreaterEqual(joint.weights.min(), -1e-9)
        np.testing.assert_allclose(joint.weights.sum(axis=1), 1, atol=1e-8)
        np.testing.assert_allclose(joint.weights @ ((self.edges[1:] + self.edges[:-1]) / 2), 1, atol=1e-8)

    def test_invalid_inputs_fail_before_fitting(self):
        for weights in ([self.first], np.full((2, 7), .1), [[float("nan")] * 8] * 2):
            with self.assertRaises(ValueError):
                continuous_calendar_check(self.edges, weights)
        for edge in ([0, .5, .4, 2], [2, 3, 4, 5], [0, 1, 2]):
            with self.assertRaises(ValueError):
                continuous_calendar_check(edge, [self.first, self.second])
        for times in ([.2, .1], [.1, .1], [0, .1]):
            with self.assertRaises(ValueError):
                fit_maturities([[.5, 1., 1.5]] * 2, [[.5, .2, .1]] * 2,
                               [1, 1], [1, 1], times, self.edges)
        with self.assertRaises(ValueError):
            fit_maturities([[.5, 1, 1.5]] * 2, [[.5, -.1, .1]] * 2,
                           [1, 1], [1, 1], [.1, .2], self.edges)
        with self.assertRaises(ValueError):
            fit_maturities([[.5, 1, 1.5]] * 2, [[.5, .2, .1]] * 2,
                           1., [1, 1], [.1, .2], self.edges)

    def test_saved_weights_independently_reproduce_calendar_result(self):
        report = json.loads((ROOT / "results/joint_validation.json").read_text())
        data = np.loadtxt(ROOT / "results/joint_bin_masses.csv", delimiter=",", skiprows=1)
        for name, column in [("control", 4), ("joint", 5)]:
            weights = np.array([data[data[:, 0] == day, column] for day in report["days"]])
            check, _ = continuous_calendar_check(report["normalised_edges"], weights)
            expected = report["cases"][name]["continuous_calendar"]
            self.assertEqual(check["passes"], expected["passes"])
            self.assertAlmostEqual(check["minimum_gap"], expected["minimum_gap"], places=12)
            grid = np.linspace(.3, 2.2, 1901)
            values = payoff_matrix(grid, report["normalised_edges"], 1.) @ weights.T
            count = int(np.count_nonzero(np.diff(values, axis=1) < -1e-8))
            self.assertEqual(count, report["cases"][name]["sampled_calendar"]["violations"])
        self.assertTrue(report["cases"]["joint"]["continuous_calendar"]["passes"])
        self.assertEqual(report["cases"]["joint"]["sampled_calendar"]["violations"], 0)
        self.assertGreater(report["cases"]["control"]["sampled_calendar"]["violations"], 0)
        self.assertLess(report["cases"]["joint"]["pooled_withheld_price_rmse"], .3)
        self.assertLess(report["cases"]["joint"]["mean_density_l1_on_support"], .08)

    def test_notebook_figures_captions_and_execution_are_complete(self):
        notebook = json.loads((ROOT / "05_joint_density.ipynb").read_text())
        cells = notebook["cells"]
        self.assertEqual(len({c["id"] for c in cells}), len(cells))
        code = [c for c in cells if c["cell_type"] == "code"]
        self.assertTrue(code)
        self.assertTrue(all(c["execution_count"] is not None and c["outputs"] for c in code))
        self.assertFalse(any(o["output_type"] == "error" for c in code for o in c["outputs"]))
        figures = []
        for index, cell in enumerate(cells):
            for name, attachment in cell.get("attachments", {}).items():
                number = int(re.search(r"figure_(\d+)_", name)[1])
                figures.append(number)
                self.assertEqual(base64.b64decode(attachment["image/png"]), (ROOT / "figures" / name).read_bytes())
                self.assertTrue("".join(cells[index + 1]["source"]).lstrip().startswith(f"Figure {number}."))
        self.assertEqual(figures, [12, 13, 14])
        markdown = "\n".join("".join(c["source"]) for c in cells if c["cell_type"] == "markdown")
        self.assertEqual(re.findall(r"\\tag\{(\d+)\}", markdown), ["16", "17", "18", "19"])

    def test_export_matches_probabilities_and_preserved_inputs(self):
        payload = json.loads((ROOT / "results/joint_surface.json").read_text())
        html = (ROOT / "interactive/joint_density_surface.html").read_text()
        embedded = re.search(r'<script id="experiment-data" type="application/json">(.*?)</script>', html, re.S)[1]
        self.assertEqual(json.loads(embedded), payload)
        self.assertIsNone(re.search(r'<script[^>]+src=["\']https?://', html))
        for name, digest in payload["report"]["input_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT / "results" / name).read_bytes()).hexdigest(), digest)
        data = np.loadtxt(ROOT / "results/joint_bin_masses.csv", delimiter=",", skiprows=1)
        for item in payload["slices"]:
            rows = data[data[:, 0] == item["days"]]
            edges = np.r_[rows[:, 1], rows[-1, 2]]
            np.testing.assert_allclose(item["step_x"], np.repeat(edges, 2)[1:-1])
            for name, column in [("control", 4), ("joint", 5)]:
                fit = DensityFit(edges, rows[:, column], 1., 1., 0., 0, 0.)
                np.testing.assert_allclose(item[name], fit.density(payload["levels"]), atol=1e-15, rtol=1e-12)
                np.testing.assert_allclose(item[name + "_step"], np.repeat(rows[:, column] / np.diff(edges), 2))
