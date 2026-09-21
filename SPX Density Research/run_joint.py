"""Compare independent and joint fits on the unchanged Milestone 4 inputs."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import trapezoid

from src.constrained import DensityFit
from src.density import Parameters, call_price, exact_density
from src.joint import continuous_calendar_check, fit_maturities
from src.surface import calendar_diagnostic, interval_probability, normalised_calls

ROOT = Path(__file__).resolve().parent


def load_inputs():
    previous = json.loads((ROOT / "results/surface_validation.json").read_text())
    quotes = np.loadtxt(ROOT / "results/maturity_quotes.csv", delimiter=",", skiprows=1)
    bins = np.loadtxt(ROOT / "results/maturity_bin_masses.csv", delimiter=",", skiprows=1)
    parameters, legacy, strikes, prices = [], [], [], []
    for row in previous["marginals"]:
        p = Parameters(**previous["base_parameters"], maturity=row["years"])
        b = bins[bins[:, 0] == row["days"]]
        q = quotes[quotes[:, 0] == row["days"]]
        if len(b) != 120 or len(q) != 81:
            raise ValueError("This comparison requires the complete eight-horizon Milestone 4 inputs.")
        np.testing.assert_allclose(q[:, 2], call_price(q[:, 1], p), rtol=1e-12, atol=1e-10)
        np.testing.assert_allclose(q[:, 4], q[:, 2] + q[:, 3], rtol=1e-12, atol=1e-10)
        fit = DensityFit(np.r_[b[:, 1], b[-1, 2]], b[:, 3], row["discount_factor"], row["forward"], 1e-6, 0, 0.)
        parameters.append(p)
        legacy.append(fit)
        strikes.append(q[:, 1])
        prices.append(q[:, 4])
    return previous, parameters, legacy, strikes, prices


def describe(fits, parameters, strikes, prices, days, edges, enforce_calendar):
    records = []
    kappa = np.linspace(.3, 2.2, 1901)
    calls = []
    for fit, p, k, y, day in zip(fits, parameters, strikes, prices, days):
        dense = np.linspace(fit.edges[0], fit.edges[-1], 40001)
        withheld = (k[1:] + k[:-1]) / 2
        slopes = np.diff(fit.prices(kappa * fit.forward)) / np.diff(kappa * fit.forward)
        records.append({"days": day, "years": p.maturity, "forward": fit.forward,
            "discount_factor": fit.discount, "mass": float(fit.mass.sum()),
            "normalised_mean": float(fit.mass @ ((edges[1:] + edges[:-1]) / 2)),
            "minimum_bin_mass": float(fit.mass.min()),
            "noisy_price_rmse": float(np.sqrt(np.mean((fit.prices(k) - y) ** 2))),
            "withheld_clean_price_rmse": float(np.sqrt(np.mean((fit.prices(withheld) - call_price(withheld, p)) ** 2))),
            "density_l1_on_support": float(trapezoid(abs(fit.density(dense) - exact_density(dense, p)), dense)),
            "fitted_mass_in_display_window": interval_probability(fit, 3000, 11000),
            "monotonicity_violations": int(np.count_nonzero(slopes > 1e-8)),
            "convexity_violations": int(np.count_nonzero(np.diff(slopes) < -1e-8))})
        calls.append(normalised_calls(fit, kappa))
    check, _ = continuous_calendar_check(edges, np.array([f.mass for f in fits]))
    sampled = calendar_diagnostic([p.maturity for p in parameters], kappa, calls)
    sampled["constraint_enforced"] = enforce_calendar
    return {"marginals": records, "continuous_calendar": check, "sampled_calendar": sampled,
            "pooled_withheld_price_rmse": float(np.sqrt(np.mean([r["withheld_clean_price_rmse"] ** 2 for r in records]))),
            "pooled_noisy_price_rmse": float(np.sqrt(np.mean([r["noisy_price_rmse"] ** 2 for r in records]))),
            "mean_density_l1_on_support": float(np.mean([r["density_l1_on_support"] for r in records]))}


def main():
    previous, parameters, legacy, strikes, prices = load_inputs()
    edges = np.linspace(.3, 2.2, 121)
    args = (strikes, prices, [p.forward for p in parameters],
            [f.discount for f in legacy], [p.maturity for p in parameters], edges)
    warm = np.array([f.mass for f in legacy])
    control = fit_maturities(*args, enforce_calendar=False, initial_weights=warm)
    joint = fit_maturities(*args, enforce_calendar=True, initial_weights=warm)
    cases = {}
    for name, fits, enforced in (("legacy", legacy, False), ("control", control.fits, False), ("joint", joint.fits, True)):
        cases[name] = describe(fits, parameters, strikes, prices, previous["days"], edges, enforced)
    cases["control"]["solver"] = control.solver
    cases["joint"]["solver"] = joint.solver
    assert cases["joint"]["continuous_calendar"]["passes"]
    assert cases["joint"]["sampled_calendar"]["violations"] == 0
    report = {"status": "synthetic_only", "observation_dates": None,
              "input_sha256": {name: hashlib.sha256((ROOT / "results" / name).read_bytes()).hexdigest()
                               for name in ("maturity_quotes.csv", "maturity_bin_masses.csv", "surface_validation.json")},
              "days": previous["days"], "normalised_edges": edges.tolist(), "penalty": 1e-6,
              "comparison": "Same prices, forwards, discount factors, bins and penalty; OSQP control isolates calendar constraints",
              "cases": cases,
              "joint_objective_increase_percent": 100 * (joint.solver["objective_sum"] / control.solver["objective_sum"] - 1),
              "limits": ["Discrete fitted maturities only; displayed joins are not an interpolation model",
                         "Continuous-strike check uses floating-point arithmetic with 1e-8 acceptance tolerance",
                         "Finite support and extrapolated tails remain modelling assumptions",
                         "No empirical SPX calibration or historical-date animation"]}
    (ROOT / "results/joint_validation.json").write_text(json.dumps(report, indent=2) + "\n")
    rows = []
    levels = np.linspace(3000, 11000, 401)
    slices = []
    for day, p, old, independent, combined in zip(previous["days"], parameters, legacy, control.fits, joint.fits):
        rows.extend(np.c_[np.full(120, day), combined.edges[:-1], combined.edges[1:], old.mass, independent.mass, combined.mass])
        slices.append({"days": day, "years": p.maturity, "known": exact_density(levels, p).tolist(),
                       "control": independent.density(levels).tolist(), "joint": combined.density(levels).tolist(),
                       "step_x": np.repeat(combined.edges, 2)[1:-1].tolist(),
                       "control_step": np.repeat(independent.mass / np.diff(independent.edges), 2).tolist(),
                       "joint_step": np.repeat(combined.mass / np.diff(combined.edges), 2).tolist()})
    np.savetxt(ROOT / "results/joint_bin_masses.csv", rows, delimiter=",",
               header="horizon_days,left_edge,right_edge,legacy_mass,control_mass,joint_mass", comments="")
    detail_k = np.linspace(1.5, 2.2, 701)
    calendar_detail = {"moneyness": detail_k.tolist(), "earlier_days": previous["days"][-2],
                       "later_days": previous["days"][-1]}
    for name, fits in (("control", control.fits), ("joint", joint.fits)):
        calendar_detail[name] = (normalised_calls(fits[-1], detail_k)
                                 - normalised_calls(fits[-2], detail_k)).tolist()
    payload = {"levels": levels.tolist(), "slices": slices, "report": report, "calendar_detail": calendar_detail}
    (ROOT / "results/joint_surface.json").write_text(json.dumps(payload, separators=(",", ":")) + "\n")
    make_figures(control.fits, joint.fits, parameters, levels)
    summary = {name: {"sampled_violations": result["sampled_calendar"]["violations"],
                      "minimum_continuous_gap": result["continuous_calendar"]["minimum_gap"],
                      "pooled_withheld_rmse": result["pooled_withheld_price_rmse"],
                      "mean_density_l1": result["mean_density_l1_on_support"]} for name, result in cases.items()}
    print(json.dumps({"cases": summary, "joint_objective_increase_percent": report["joint_objective_increase_percent"],
                      "joint_solver": joint.solver}, indent=2))
    return report


def make_figures(control, joint, parameters, levels):
    navy, orange, teal = "#16364c", "#cf8b51", "#218a87"
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    kappa = np.linspace(.3, 2.2, 3001)
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.5), constrained_layout=True)
    for ax, bounds in zip(axes, [(1.3, 2.2), (1.68, 1.88)]):
        for fits, color, style, label in ((control, orange, "--", "Independent control (OSQP)"),
                                         (joint, teal, "-", "Joint fit (OSQP)")):
            gap = normalised_calls(fits[-1], kappa) - normalised_calls(fits[-2], kappa)
            ax.plot(kappa, gap, color=color, ls=style, label=label)
        ax.axhline(0, color=navy, lw=.7)
        ax.set_xlim(*bounds)
        ax.set_xlabel("Forward moneyness, K/F (dimensionless)")
        ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
        ax.grid(alpha=.15)
    axes[0].set_ylabel("365-day minus 300-day normalised call")
    visible = (kappa >= 1.3) & (kappa <= 2.2)
    gaps = np.concatenate([(normalised_calls(fits[-1], kappa) - normalised_calls(fits[-2], kappa))[visible]
                           for fits in (control, joint)])
    padding = .08 * np.ptp(gaps)
    axes[0].set_ylim(gaps.min() - padding, gaps.max() + padding)
    # Explicit zoom in both directions reveals the previously offending wing.
    axes[1].set_ylim(-2.1e-4, 8e-5)
    fig.legend(*axes[0].get_legend_handles_labels(), loc="outside upper center", ncol=2, frameon=False)
    save(fig, 12, "calendar_gap")
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.5), constrained_layout=True)
    p = parameters[-1]
    full = np.linspace(.3 * p.forward, 2.2 * p.forward, 2001)
    for ax, bounds in zip(axes, [(3000, 11000), (9000, 12500)]):
        ax.plot(full, exact_density(full, p), color=navy, ls=":", lw=2, label="Known lognormal density")
        for fit, color, style, label in ((control[-1], orange, "--", "Independent control"), (joint[-1], teal, "-", "Joint fit")):
            ax.stairs(fit.mass / np.diff(fit.edges), fit.edges, color=color, ls=style, label=label)
        ax.set_xlim(*bounds)
        ax.set_xlabel("Terminal index level (index points)")
        ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
        ax.grid(alpha=.15)
    axes[0].set_ylabel("Density (per index point)")
    axes[1].set_ylim(-1e-7, 4.5e-5)
    fig.legend(*axes[0].get_legend_handles_labels(), loc="outside upper center", ncol=3, frameon=False)
    save(fig, 13, "joint_density_comparison")
    fig = plt.figure(figsize=(10.5, 6.8))
    ax = fig.add_subplot(111, projection="3d")
    x, y = np.meshgrid(levels, [p.maturity for p in parameters])
    z = np.array([f.density(levels) for f in joint])
    ax.plot_surface(x, y, z, cmap="viridis", rcount=len(joint), ccount=len(levels), linewidth=0, alpha=.94)
    ax.set_xlabel("Terminal index level (index points)", labelpad=12)
    ax.set_ylabel("Time to expiry (years)", labelpad=12)
    ax.set_zlabel("Density (per index point)", labelpad=13)
    ax.ticklabel_format(axis="z", style="sci", scilimits=(0, 0))
    ax.view_init(elev=27, azim=-63)
    fig.subplots_adjust(left=.01, right=.9, top=.98, bottom=.1)
    save(fig, 14, "joint_maturity_surface")


def save(fig, number, name):
    for extension in ("png", "svg"):
        fig.savefig(ROOT / f"figures/figure_{number:02}_{name}.{extension}", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
