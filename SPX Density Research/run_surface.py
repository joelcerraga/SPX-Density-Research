"""Synthetic multi-maturity experiment, Figures 10-11 and explorer data.

All maturities belong to one synthetic valuation setup, not a date series.
Run build_surface_html.py afterwards to refresh the self-contained explorer.
"""
from dataclasses import asdict
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import trapezoid
from scipy.special import ndtr

from src.constrained import fit_density
from src.density import Parameters, call_price, exact_density
from src.surface import calendar_diagnostic, interval_probability, normalised_calls

ROOT = Path(__file__).resolve().parent
DAYS = [30, 60, 90, 120, 180, 240, 300, 365]
SEED_BASE = 20260920
PENALTY = 1e-6


def main():
    records, fits, parameters, slices = [], [], [], []
    quotes, bins = [], []
    levels = np.linspace(3000, 11000, 401)
    kappa = np.linspace(.3, 2.2, 1901)
    normalised, known_calls = [], []
    for days in DAYS:
        p = Parameters(maturity=days / 365)
        F, D = p.forward, np.exp(-p.rate * p.maturity)
        v = p.volatility * np.sqrt(p.maturity)
        strikes = F * np.linspace(np.exp(-2.5 * v), np.exp(2.5 * v), 81)
        truth = call_price(strikes, p)
        noise = np.random.default_rng(SEED_BASE + days).uniform(-.5, .5, len(strikes))
        observed = truth + noise
        if np.any(observed < 0):
            raise RuntimeError("Negative synthetic price; revise the experiment explicitly, not by clipping.")
        edges = np.linspace(.3 * F, 2.2 * F, 121)
        fit = fit_density(strikes, observed, F, D, edges, PENALTY)
        midpoint_strikes = (strikes[1:] + strikes[:-1]) / 2
        dense = np.linspace(edges[0], edges[-1], 40001)
        mu = np.log(p.spot) + (p.rate - p.dividend - .5 * p.volatility ** 2) * p.maturity
        outside = ndtr((np.log(edges[0]) - mu) / v) + ndtr(-(np.log(edges[-1]) - mu) / v)
        price_curve = fit.prices(F * kappa)
        slopes = np.diff(price_curve) / np.diff(F * kappa)
        record = {
            "days": days, "years": p.maturity, "seed": SEED_BASE + days,
            "forward": F, "discount_factor": D, "iterations": fit.iterations,
            "strike_range": [float(strikes[0]), float(strikes[-1])],
            "support": [float(edges[0]), float(edges[-1])],
            "minimum_input_price": float(observed.min()),
            "mass": float(fit.mass.sum()),
            "mean": float(fit.mass @ ((edges[1:] + edges[:-1]) / 2)),
            "minimum_bin_mass": float(fit.mass.min()),
            "noisy_price_rmse": float(np.sqrt(np.mean((fit.prices(strikes) - observed) ** 2))),
            "withheld_clean_price_rmse": float(np.sqrt(np.mean(
                (fit.prices(midpoint_strikes) - call_price(midpoint_strikes, p)) ** 2))),
            "density_l1_on_support": float(trapezoid(np.abs(fit.density(dense) - exact_density(dense, p)), dense)),
            "known_mass_outside_support": float(outside),
            "fitted_mass_in_display_window": interval_probability(fit, levels[0], levels[-1]),
            "monotonicity_violations": int(np.count_nonzero(slopes > 1e-8)),
            "convexity_violations": int(np.count_nonzero(np.diff(slopes) < -1e-8)),
        }
        if (abs(record["mass"] - 1) > 1e-8 or abs(record["mean"] / F - 1) > 1e-8
                or record["minimum_bin_mass"] < -1e-10
                or record["monotonicity_violations"] or record["convexity_violations"]):
            raise RuntimeError("A fitted marginal failed validation.")
        records.append(record)
        fits.append(fit)
        parameters.append(p)
        normalised.append(normalised_calls(fit, kappa))
        known_calls.append(call_price(F * kappa, p) / (D * F))
        # Duplicate each edge in the line path so the selected slice is a true
        # histogram, even though the 3D sheet interpolates its sampled vertices.
        step_x = np.repeat(edges, 2)[1:-1]
        step_y = np.repeat(fit.mass / np.diff(edges), 2)
        slices.append({"days": days, "years": p.maturity,
                       "known": exact_density(levels, p).tolist(),
                       "fitted": fit.density(levels).tolist(),
                       "step_x": step_x.tolist(), "step_y": step_y.tolist()})
        quotes.extend(np.c_[np.full(len(strikes), days), strikes, truth, noise, observed])
        bins.extend(np.c_[np.full(len(fit.mass), days), edges[:-1], edges[1:], fit.mass])
    times = [p.maturity for p in parameters]
    calendar = calendar_diagnostic(times, kappa, normalised)
    known_calendar = calendar_diagnostic(times, kappa, known_calls)
    # Distinguish checks supported by both quote ranges from extrapolated wings.
    changes = np.diff(np.asarray(normalised), axis=0)
    overlap_comparisons = overlap_violations = 0
    for i, pair in enumerate(calendar["pairs"]):
        left, right = records[i:i + 2]
        lower = max(left["strike_range"][0] / left["forward"], right["strike_range"][0] / right["forward"])
        upper = min(left["strike_range"][1] / left["forward"], right["strike_range"][1] / right["forward"])
        mask = (kappa >= lower) & (kappa <= upper)
        pair["shared_quote_moneyness_range"] = [lower, upper]
        pair["shared_quote_range_comparisons"] = int(mask.sum())
        pair["shared_quote_range_violations"] = int(np.count_nonzero(changes[i, mask] < -calendar["tolerance"]))
        overlap_comparisons += pair["shared_quote_range_comparisons"]
        overlap_violations += pair["shared_quote_range_violations"]
    calendar["shared_quote_range_comparisons"] = overlap_comparisons
    calendar["shared_quote_range_violations"] = overlap_violations
    report = {
        "status": "synthetic_only", "observation_dates": None,
        "base_parameters": {key: value for key, value in asdict(Parameters()).items() if key != "maturity"},
        "days": DAYS, "day_count": "synthetic horizon / 365, not a contract settlement calculation",
        "noise": {"distribution": "independent uniform", "bounds": [-.5, .5],
                  "standard_deviation": float(1 / np.sqrt(12)), "seed_rule": "20260920 + horizon_days"},
        "quotes_per_maturity": 81, "bins_per_maturity": 120, "penalty": PENALTY,
        "penalty_selection": "Retained Milestone 3 baseline for every maturity; no maturity-specific tuning",
        "strike_rule": "81 equally spaced strikes between F exp(-2.5 sigma sqrt(T)) and F exp(2.5 sigma sqrt(T))",
        "support_rule": "120 equal-width bins on [0.3 F(T), 2.2 F(T)]",
        "display_range": [float(levels[0]), float(levels[-1])],
        "display_interpolation": "Straight graphical joins only; no fitted intermediate maturities",
        "calendar": calendar, "known_calendar": known_calendar, "marginals": records,
    }
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "figures").mkdir(exist_ok=True)
    (ROOT / "results/surface_validation.json").write_text(json.dumps(report, indent=2) + "\n")
    payload = {"levels": levels.tolist(), "slices": slices, "report": report}
    (ROOT / "results/maturity_surface.json").write_text(json.dumps(payload, separators=(",", ":")) + "\n")
    np.savetxt(ROOT / "results/maturity_quotes.csv", quotes, delimiter=",",
               header="horizon_days,strike,known_price,added_noise,noisy_price", comments="")
    np.savetxt(ROOT / "results/maturity_bin_masses.csv", bins, delimiter=",",
               header="horizon_days,left_edge,right_edge,probability_mass", comments="")
    make_figures(levels, times, fits, parameters)
    print(json.dumps(report, indent=2))
    return report


def make_figures(levels, times, fits, parameters):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    fig = plt.figure(figsize=(10.5, 6.8))
    ax = fig.add_subplot(111, projection="3d")
    x, y = np.meshgrid(levels, times)
    z = np.array([fit.density(levels) for fit in fits])
    ax.plot_surface(x, y, z, cmap="viridis", rcount=len(times), ccount=len(levels),
                    linewidth=0, antialiased=True, alpha=.94)
    for t, row in zip(times, z):
        ax.plot(levels, np.full_like(levels, t), row, color="#16364c", lw=.5, alpha=.6)
    ax.set_xlabel("Terminal index level (index points)", labelpad=12)
    ax.set_ylabel("Time to expiry (years)", labelpad=12)
    ax.set_zlabel("Density (per index point)", labelpad=13)
    ax.ticklabel_format(axis="z", style="sci", scilimits=(0, 0))
    ax.view_init(elev=27, azim=-63)
    fig.subplots_adjust(left=.01, right=.9, top=.98, bottom=.1)
    save(fig, 10, "maturity_surface")
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), constrained_layout=True,
                             sharex=True, sharey=True)
    for ax, index in zip(axes.flat, [0, 2, 4, 7]):
        fit, p = fits[index], parameters[index]
        ax.plot(levels, exact_density(levels, p), color="#16364c", ls="--", lw=1.6,
                label="Known lognormal density")
        ax.stairs(fit.mass / np.diff(fit.edges), fit.edges, color="#218a87", lw=1.3,
                  label="Constrained histogram")
        ax.text(.96, .91, f"{DAYS[index]} days", ha="right", transform=ax.transAxes)
        ax.set_xlim(levels[0], levels[-1])
        ax.set_ylim(bottom=0)
        ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
        ax.grid(alpha=.15)
    fig.legend(*axes[0, 0].get_legend_handles_labels(), loc="outside upper center", ncol=2, frameon=False)
    for ax in axes[-1]:
        ax.set_xlabel("Terminal index level (index points)")
    for ax in axes[:, 0]:
        ax.set_ylabel("Density (per index point)")
    save(fig, 11, "maturity_slices")


def save(fig, number, name):
    for extension in ("png", "svg"):
        fig.savefig(ROOT / f"figures/figure_{number:02}_{name}.{extension}", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
