"""Seven declared fitting choices on two synthetic benchmark families.

Reuses Milestone 4 strike grids and noise. Earlier notebooks/results are read
only. No benchmark density or tail probability is supplied to the estimator.
"""
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from run_joint import load_inputs
from src.joint import fit_maturities
from src.robustness import (BASE_ALPHA, BENCHMARKS, full_density_error,
                            histogram_risk, study_settings, true_risk)
from src.surface import calendar_diagnostic

ROOT = Path(__file__).resolve().parent
NAMES = {"lognormal": "Single lognormal", "mixture": "Two-lognormal mixture"}


def main():
    previous, parameters, legacy, strikes, old_prices = load_inputs()
    old_quotes = np.loadtxt(ROOT / "results/maturity_quotes.csv", delimiter=",", skiprows=1)
    noise = [old_quotes[old_quotes[:, 0] == d, 3] for d in previous["days"]]
    settings = study_settings()
    report = {"status": "synthetic_only", "days": previous["days"],
        "base_parameters": previous["base_parameters"], "base_roughness_coefficient": BASE_ALPHA,
        "design": "Seven declared settings, two known benchmarks, one shared fixed noise realization; no parameter selection",
        "initialisation": "Clarabel internal initialisation; no benchmark weights or density supplied",
        "input_sha256": {name: hashlib.sha256((ROOT / "results" / name).read_bytes()).hexdigest()
                         for name in ("maturity_quotes.csv", "surface_validation.json", "joint_validation.json")},
        "settings": [{**s, "edges": s["edges"].tolist()} for s in settings], "benchmarks": {},
        "limitations": ["Sensitivity ranges are not statistical confidence intervals",
                        "One noise realization, one strike-coverage design and fixed known forwards",
                        "Calendar acceptance applies to adjacent supplied maturities at tolerance 1e-8",
                        "No empirical calibration, parameter recommendation or historical animation"]}
    all_fits, quote_rows, mass_rows, metric_rows = {}, [], [], []
    for key, benchmark in BENCHMARKS.items():
        prices = [benchmark.prices(k, p) + e for k, p, e in zip(strikes, parameters, noise)]
        if key == "lognormal":
            for original, regenerated in zip(old_prices, prices):
                np.testing.assert_allclose(original, regenerated, rtol=0, atol=1e-10)
            prices = old_prices
        if any(np.any(y < 0) for y in prices):
            raise ValueError("Negative synthetic input price; no clipping is allowed.")
        for d, k, p, e, y in zip(previous["days"], strikes, parameters, noise, prices):
            quote_rows.extend(zip([key] * len(k), [d] * len(k), k, benchmark.prices(k, p), e, y))
        grid = np.linspace(.1, 3., 2901)
        clean_normalised = [benchmark.prices(grid * p.forward, p) / (np.exp(-p.rate*p.maturity)*p.forward)
                            for p in parameters]
        clean_calendar = calendar_diagnostic([p.maturity for p in parameters], grid, clean_normalised)
        if clean_calendar["violations"]:
            raise RuntimeError("The synthetic benchmark failed its calendar check.")
        result = {"name": NAMES[key], "weights": list(benchmark.weights),
                  "volatilities": list(benchmark.volatilities), "clean_calendar": clean_calendar, "cases": {}}
        all_fits[key] = {}
        for s in settings:
            print(f'Fitting {key}: {s["label"]} ...', flush=True)
            joint = fit_maturities(strikes, prices, [p.forward for p in parameters],
                [f.discount for f in legacy], [p.maturity for p in parameters], s["edges"],
                penalty=s["penalty"], max_solver_iterations=200, residual_form=True, solver_backend="clarabel")
            rows = []
            for d, k, p, y, fit in zip(previous["days"], strikes, parameters, prices, joint.fits):
                withheld = (k[1:] + k[:-1]) / 2
                error = full_density_error(fit, benchmark, p.maturity)
                risk, known = histogram_risk(fit), true_risk(benchmark, p.maturity)
                row = {"days": d, "years": p.maturity, "forward": p.forward,
                    "discount": fit.discount, "mass": float(fit.mass.sum()), "minimum_bin_mass": float(fit.mass.min()),
                    "noisy_price_rmse": float(np.sqrt(np.mean((fit.prices(k) - y)**2))),
                    "withheld_clean_price_rmse": float(np.sqrt(np.mean((fit.prices(withheld) - benchmark.prices(withheld,p))**2))),
                    "density_error": error, "risk": risk, "known_risk": known}
                rows.append(row)
                metric_rows.append({"benchmark": key, "setting": s["id"], "days": d,
                    "withheld_rmse": row["withheld_clean_price_rmse"], "full_density_l1": error["full_domain"],
                    "known_outside_support": error["outside_support_probability"],
                    **{f"fitted_{k}": v for k,v in risk.items()}, **{f"known_{k}":v for k,v in known.items()}})
                mass_rows.extend(zip([key]*len(fit.mass), [s["id"]]*len(fit.mass), [d]*len(fit.mass),
                                     fit.edges[:-1], fit.edges[1:], fit.mass))
            case = {"marginals": rows, "solver": joint.solver, "calendar": joint.continuous_check,
                    "pooled_withheld_price_rmse": float(np.sqrt(np.mean([r["withheld_clean_price_rmse"]**2 for r in rows]))),
                    "mean_full_density_l1": float(np.mean([r["density_error"]["full_domain"] for r in rows])),
                    "maximum_quadrature_change": max(r["density_error"]["quadrature_change"] for r in rows),
                    "maximum_quadrature_error_estimate": max(r["density_error"]["quadrature_error_estimate"] for r in rows)}
            result["cases"][s["id"]] = case
            all_fits[key][s["id"]] = joint.fits
            print(f'{key:9} | {s["label"]:16} | RMSE {case["pooled_withheld_price_rmse"]:.6f} | '
                  f'full L1 {case["mean_full_density_l1"]:.6f} | calendar {joint.continuous_check["passes"]}', flush=True)
        report["benchmarks"][key] = result
    report["case_count"] = len(settings)*len(BENCHMARKS)
    report["marginal_count"] = report["case_count"]*len(parameters)
    report["all_calendar_checks_pass"] = all(c["calendar"]["passes"] for b in report["benchmarks"].values() for c in b["cases"].values())
    (ROOT / "results/robustness_validation.json").write_text(json.dumps(report, indent=2) + "\n")
    for name, header, rows in [
        ("robustness_quotes.csv", ["benchmark","horizon_days","strike","clean_call","noise","observed_call"], quote_rows),
        ("robustness_bin_masses.csv", ["benchmark","setting","horizon_days","left_edge","right_edge","mass"], mass_rows),
        ("robustness_metrics.csv", list(metric_rows[0]), [list(row.values()) for row in metric_rows])]:
        with (ROOT / "results" / name).open("w", newline="") as out:
            writer = csv.writer(out); writer.writerow(header); writer.writerows(rows)
    make_figures(report, all_fits, parameters[-1], settings)
    write_tables(report)
    return report


def make_figures(report, fits, p, settings):
    navy, teal, orange = "#16364c", "#218a87", "#cf8b51"
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 7.4), constrained_layout=True)
    levels = np.linspace(2800, 16000, 3301)
    for row, (key, benchmark) in enumerate(BENCHMARKS.items()):
        values = np.array([fits[key][s["id"]][-1].density(levels) for s in settings])
        base = fits[key]["baseline"][-1]
        truth = benchmark.density(levels/p.forward, p.maturity)/p.forward
        for ax, bounds in zip(axes[row], [(3000,11000),(9000,15500)]):
            ax.fill_between(levels,values.min(axis=0),values.max(axis=0),color="#b5c7cc",alpha=.65,label="Range across seven settings")
            ax.plot(levels,truth,color=navy,ls=":",lw=2,label="Known density")
            ax.stairs(base.mass/np.diff(base.edges),base.edges,color=teal,lw=1.3,label="Baseline joint fit")
            ax.set_xlim(*bounds)
            ax.set_ylim(bottom=0)
            if bounds[0] == 9000:
                visible = (levels>=bounds[0]) & (levels<=bounds[1])
                ax.set_ylim(0,1.12*max(truth[visible].max(),values[:,visible].max()))
            ax.ticklabel_format(axis="y",style="sci",scilimits=(0,0))
            ax.grid(alpha=.15)
        axes[row,0].set_ylabel(NAMES[key]+"\nDensity (per index point)")
    for ax in axes[-1]: ax.set_xlabel("Terminal index level (index points)")
    fig.legend(*axes[0,0].get_legend_handles_labels(),loc="outside upper center",ncol=3,frameon=False,fontsize=9)
    save(fig,15,"density_sensitivity")
    fig, axes = plt.subplots(1,2,figsize=(10.5,4.8),constrained_layout=True)
    y = np.arange(len(settings))
    for ax, field, xlabel in zip(axes,["pooled_withheld_price_rmse","mean_full_density_l1"],
            ["Pooled withheld-price RMSE (index points)","Mean full-domain density L1 (dimensionless)"]):
        for key, offset, color in [("lognormal",-.13,navy),("mixture",.13,orange)]:
            values=[report["benchmarks"][key]["cases"][s["id"]][field] for s in settings]
            ax.scatter(values,y+offset,label=NAMES[key],color=color,s=34)
        ax.set_yticks(y,[s["label"] for s in settings]);ax.invert_yaxis();ax.set_xlabel(xlabel);ax.grid(axis="x",alpha=.2)
        ax.set_xlim(left=0)
    fig.legend(*axes[0].get_legend_handles_labels(),loc="outside upper center",ncol=2,frameon=False)
    save(fig,16,"price_density_tradeoff")
    fig, axes = plt.subplots(1,2,figsize=(10.5,5),sharey=True,constrained_layout=True)
    for ax,(key,benchmark) in zip(axes,BENCHMARKS.items()):
        for offset,field,label,color,marker in [(-.18,"below_0_8_forward","P(S < 0.8F)",navy,"o"),
                (0.,"above_1_2_forward","P(S > 1.2F)",teal,"s"),(.18,"above_1_8_forward","P(S > 1.8F)",orange,"D")]:
            values=[100*(report["benchmarks"][key]["cases"][s["id"]]["marginals"][-1]["risk"][field]
                         -true_risk(benchmark,p.maturity)[field]) for s in settings]
            ax.scatter(values,y+offset,label=label,color=color,marker=marker,s=30)
        ax.axvline(0,color="#6f8088",lw=.8);ax.set_xlabel(NAMES[key]+"\nProbability error (percentage points)");ax.grid(axis="x",alpha=.2)
    axes[0].set_yticks(y,[s["label"] for s in settings]);axes[0].invert_yaxis()
    fig.legend(*axes[0].get_legend_handles_labels(),loc="outside upper center",ncol=3,frameon=False)
    save(fig,17,"tail_probability_sensitivity")


def save(fig, number, name):
    for extension in ("png","svg"):
        fig.savefig(ROOT / f"figures/figure_{number:02}_{name}.{extension}",dpi=180)
    plt.close(fig)


def write_tables(report):
    blocks = {}
    lines = ["Table 11. Declared sensitivity settings. Support is in forward-normalised terminal levels; lambda is the coefficient passed to Equation (12).",
             "", "| Setting | Support | Bins | Roughness multiple | Lambda |", "|---|---|---:|---:|---:|"]
    for s in report["settings"]:
        e=s["edges"]
        lines.append(f'| {s["label"]} | [{e[0]:.6f}, {e[-1]:.6f}] | {len(e)-1} | {s["alpha_multiple"]:g} | {s["penalty"]:.7g} |')
    blocks["SETTINGS_TABLE"]="\n".join(lines)
    lines=["Table 12. Recovery accuracy across all eight fitted horizons. Each calendar entry refers to the interval-level check at tolerance $10^{-8}$. Density error includes benchmark probability outside the chosen support.",
           "", "| Benchmark | Setting | Withheld-price RMSE (points) | Mean full-domain density $L_1$ | Calendar check |", "|---|---|---:|---:|---|"]
    for key,b in report["benchmarks"].items():
        for s in report["settings"]:
            c=b["cases"][s["id"]]
            lines.append(f'| {NAMES[key]} | {s["label"]} | {c["pooled_withheld_price_rmse"]:.6f} | {c["mean_full_density_l1"]:.6f} | {"Pass" if c["calendar"]["passes"] else "FAIL"} |')
    blocks["RESULTS_TABLE"]="\n".join(lines)
    lines=["Table 13. Known values and fitted ranges at 365 days across the seven declared settings. Probabilities are percentages; normalised variance is dimensionless. Ranges are sensitivity summaries, not confidence intervals.",
           "", "| Benchmark | Quantity | Known value | Minimum fitted | Maximum fitted |", "|---|---|---:|---:|---:|"]
    for key,b in report["benchmarks"].items():
        for field,label,mult in [("below_0_8_forward","P(S < 0.8F), %",100),("above_1_2_forward","P(S > 1.2F), %",100),
                ("above_1_8_forward","P(S > 1.8F), %",100),("normalised_variance","Var(S/F)",1)]:
            rows=[c["marginals"][-1] for c in b["cases"].values()]
            values=[r["risk"][field]*mult for r in rows]
            lines.append(f'| {NAMES[key]} | {label} | {rows[0]["known_risk"][field]*mult:.6f} | {min(values):.6f} | {max(values):.6f} |')
    blocks["RISK_TABLE"]="\n".join(lines)
    (ROOT / "results/robustness_tables.json").write_text(json.dumps(blocks,indent=2)+"\n")


if __name__ == "__main__":
    main()
