"""Declared repeated-noise experiment; no data-dependent parameter selection."""
from dataclasses import asdict
import hashlib
import json

import numpy as np

from src.density import Parameters
from src.joint import fit_maturities
from src.robustness import BENCHMARKS, full_density_error, histogram_risk, true_risk

DAYS = (30, 60, 90, 120, 180, 240, 300, 365)
REPETITIONS = 50
SEED = 20260921
AMPLITUDES = (0.1, 0.5)
EDGES = np.linspace(0.3, 2.2, 121)
PENALTY = 1e-6
COVERAGES = {
    "original": {"label": "Original 81", "indices": np.arange(20, 101)},
    "sparse": {"label": "Sparse 41", "indices": np.arange(20, 101, 2)},
    "central": {"label": "Central 41", "indices": np.arange(40, 81)},
    "extended": {"label": "Extended 121", "indices": np.arange(121)},
}
NAMES = {"lognormal": "Single lognormal", "mixture": "Two-lognormal mixture"}
RISK_FIELDS = ("below_0_8_forward", "above_1_2_forward", "above_1_8_forward", "normalised_variance")


def parameters():
    return [Parameters(maturity=d/365) for d in DAYS]


def master_strikes(p):
    """Keep the previous 81 *linearly spaced strikes*, extend by 20 each side."""
    v = p.volatility * np.sqrt(p.maturity)
    original = p.forward * np.linspace(np.exp(-2.5*v), np.exp(2.5*v), 81)
    step = (original[-1] - original[0]) / 80
    return np.r_[original[0] + step*np.arange(-20, 0), original,
                 original[-1] + step*np.arange(1, 21)]


def random_draws(repetition):
    if not isinstance(repetition, int) or repetition < 0:
        raise ValueError("A nonnegative integer repetition is required.")
    # A reproducible child stream, independent of task scheduling and coverage.
    seed = np.random.SeedSequence(SEED, spawn_key=(repetition,))
    rng = np.random.Generator(np.random.PCG64(seed))
    before = rng.bit_generator.state
    u = rng.uniform(-1., 1., (len(DAYS), 121))
    return u, {"repetition": repetition, "entropy": SEED,
               "spawn_key": [repetition], "initial_state": before,
               "final_state": rng.bit_generator.state}


def bounded_quotes(clean, amplitude, draws):
    clean, draws = np.asarray(clean, float), np.asarray(draws, float)
    if (clean.shape != draws.shape or not np.all(np.isfinite(clean))
            or np.any(clean <= 0) or not np.all(np.isfinite(draws))
            or np.any(np.abs(draws) > 1) or not np.isfinite(amplitude) or amplitude < 0):
        raise ValueError("Positive clean prices, matching bounded draws and nonnegative amplitude required.")
    width = np.minimum(amplitude, clean / 2)
    error = width * draws
    return clean + error, error, width


def scalar_summary(values, truth=None):
    """Finite-sample mean, empirical SD and Monte Carlo SE of the mean."""
    values = np.asarray(values, float)
    if values.ndim != 1 or len(values) < 2 or not np.all(np.isfinite(values)):
        raise ValueError("At least two finite scalar repetitions required.")
    n = len(values)
    mean, sd = float(values.mean()), float(values.std(ddof=1))
    result = {"n": n, "mean": mean, "sd": sd, "mcse": sd/np.sqrt(n),
              "minimum": float(values.min()), "maximum": float(values.max())}
    if truth is not None:
        if not np.isfinite(truth):
            raise ValueError("Finite truth required.")
        errors = values - truth
        mse = errors**2
        result.update(truth=float(truth), bias=mean-truth, rmse=float(np.sqrt(mse.mean())),
                      mse=float(mse.mean()), mse_mcse=float(mse.std(ddof=1)/np.sqrt(n)))
    return result


def paired_summary(left, right):
    a, b = np.asarray(left, float), np.asarray(right, float)
    if a.shape != b.shape:
        raise ValueError("Paired results must have matching shapes.")
    return scalar_summary(a-b)


def case_specs():
    specs = []
    for key in BENCHMARKS:
        for coverage in COVERAGES:
            specs.append({"benchmark": key, "coverage": coverage, "amplitude": 0., "repetition": -1})
            for amplitude in AMPLITUDES:
                for repetition in range(REPETITIONS):
                    specs.append({"benchmark": key, "coverage": coverage,
                                  "amplitude": amplitude, "repetition": repetition})
    for spec in specs:
        code = int(round(10*spec["amplitude"]))
        rep = "clean" if spec["repetition"] == -1 else f'r{spec["repetition"]:02}'
        spec["id"] = f'{spec["benchmark"]}_{spec["coverage"]}_a{code}_{rep}'
    return specs


def protocol():
    ps = parameters()
    return {"stage": 7, "status": "synthetic_only", "repetitions": REPETITIONS,
        "seed": SEED, "rng": "PCG64 with SeedSequence child spawn_key=(repetition,)",
        "days": list(DAYS), "base_parameters": {k:v for k,v in asdict(ps[0]).items() if k != "maturity"},
        "amplitudes": list(AMPLITUDES), "noise": "min(a, clean_call/2) * U[-1,1]; no clipping",
        "coverage": {k:{"label":v["label"], "indices":v["indices"].tolist()} for k,v in COVERAGES.items()},
        "master_strikes": [master_strikes(p).tolist() for p in ps],
        "edges": EDGES.tolist(), "penalty": PENALTY,
        "solver": {"backend":"clarabel", "residual_form":True, "max_solver_iterations":200,
                   "max_rounds":15, "calendar_tolerance":1e-8, "refinement_target":1e-9},
        "evaluation": "120 arithmetic midpoints of master strikes per maturity, fixed across coverage patterns",
        "parameter_selection": "None; retained Milestone 6 baseline support, bins and penalty",
        "benchmark": {k:{"weights":b.weights,"volatilities":b.volatilities} for k,b in BENCHMARKS.items()},
        "planned_noisy_fits": len(BENCHMARKS)*len(COVERAGES)*len(AMPLITUDES)*REPETITIONS,
        "planned_clean_fits": len(BENCHMARKS)*len(COVERAGES),
        "precision_scope": "50 repeats fixed after a runtime/feasibility pilot; MCSE is reported, not assumed negligible"}


def fit_case(spec):
    benchmark = BENCHMARKS[spec["benchmark"]]
    ps, indices = parameters(), COVERAGES[spec["coverage"]]["indices"]
    master = [master_strikes(p) for p in ps]
    clean = [benchmark.prices(k,p) for k,p in zip(master,ps)]
    draws = (np.zeros((len(DAYS),121)) if spec["repetition"] < 0
             else random_draws(spec["repetition"])[0])
    generated = [bounded_quotes(c,spec["amplitude"],u) for c,u in zip(clean,draws)]
    strikes, prices = [k[indices] for k in master], [q[0][indices] for q in generated]
    joint = fit_maturities(strikes, prices, [p.forward for p in ps],
        [np.exp(-p.rate*p.maturity) for p in ps], [p.maturity for p in ps], EDGES,
        penalty=PENALTY, max_solver_iterations=200, residual_form=True, solver_backend="clarabel")
    marginals, all_errors, original_errors = [], [], []
    interpolation_errors, extrapolation_errors = [], []
    for d,p,k,selected,fit,(y,noise,width) in zip(DAYS,ps,master,strikes,joint.fits,generated):
        withheld = (k[1:] + k[:-1]) / 2
        error = fit.prices(withheld) - benchmark.prices(withheld,p)
        inside = (withheld > selected[0]) & (withheld < selected[-1])
        all_errors.extend(error.tolist())
        original_errors.extend(error[20:100].tolist())
        interpolation_errors.extend(error[inside].tolist())
        extrapolation_errors.extend(error[~inside].tolist())
        density = full_density_error(fit,benchmark,p.maturity)
        marginals.append({"days":d,"forward":p.forward,"discount":fit.discount,
            "quote_count":len(indices),"quote_min_ratio":float(selected[0]/p.forward),
            "quote_max_ratio":float(selected[-1]/p.forward),
            "minimum_observed_call":float(y[indices].min()),
            "bounded_noise_quotes":int(np.sum(width[indices] < spec["amplitude"])),
            "effective_noise_sd_rms":float(np.sqrt(np.mean(width[indices]**2/3))),
            "input_noise_rmse":float(np.sqrt(np.mean(noise[indices]**2))),
            "validation_rmse":float(np.sqrt(np.mean(error**2))),
            "density_error":density,"risk":histogram_risk(fit),
            "known_risk":true_risk(benchmark,p.maturity),
            "mass":float(fit.mass.sum()),"minimum_mass":float(fit.mass.min())})
    def rmse(x):
        return float(np.sqrt(np.mean(np.asarray(x)**2))) if len(x) else None
    return {"spec":spec,"status":"accepted","weights":joint.weights.tolist(),
        "solver":joint.solver,"calendar":joint.continuous_check,"marginals":marginals,
        "metrics":{"validation_rmse":rmse(all_errors),"original_range_rmse":rmse(original_errors),
                   "within_quote_range_rmse":rmse(interpolation_errors),
                   "outside_quote_range_rmse":rmse(extrapolation_errors),
                   "mean_full_density_l1":float(np.mean([m["density_error"]["full_domain"] for m in marginals]))}}


def signature(root):
    names = ["src/density.py","src/constrained.py","src/surface.py","src/joint.py",
             "src/robustness.py","src/repeated.py","run_repeated.py"]
    hashes = {n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in names}
    payload = {"protocol":protocol(),"code_sha256":hashes}
    return hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest(), hashes
