"""Predeclared noisy-price selection and fixed-event forward sensitivity study."""
from dataclasses import replace
import hashlib
import json

import numpy as np

from src.joint import fit_maturities
from src.repeated import (BENCHMARKS, COVERAGES, DAYS, EDGES, PENALTY,
                          bounded_quotes, master_strikes, parameters)
from src.robustness import full_density_error, histogram_risk, true_risk

REPETITIONS = 20
SEED = (20260921, 8)
AMPLITUDE = .5
CANDIDATES = (1e-7, 1e-6, 1e-5)
PATTERNS = ("original", "extended")
SHIFTS = (-.005, -.001, 0., .001, .005)


def random_draws(repetition):
    if not isinstance(repetition, int) or repetition < 0:
        raise ValueError("A nonnegative integer repetition is required.")
    sequence = np.random.SeedSequence(SEED, spawn_key=(repetition,))
    rng = np.random.Generator(np.random.PCG64(sequence))
    before = rng.bit_generator.state
    draws = rng.uniform(-1, 1, (len(DAYS), 121))
    return draws, {"repetition": repetition, "entropy": list(SEED),
                   "spawn_key": [repetition], "initial_state": before,
                   "final_state": rng.bit_generator.state}


def folds(count):
    """Interlaced interior holdouts; the two endpoint quotes stay in training."""
    if not isinstance(count, int) or count < 5:
        raise ValueError("At least five ordered quotes are required.")
    interior = np.arange(1, count-1)
    return [(np.setdiff1d(np.arange(count), interior[f::3]), interior[f::3])
            for f in range(3)]


def pooled_score(fold_sums, fold_counts):
    sums, counts = np.asarray(fold_sums, float), np.asarray(fold_counts, int)
    if (sums.shape != counts.shape or sums.size == 0 or np.any(counts <= 0)
            or np.any(sums < 0) or not np.all(np.isfinite(sums))):
        raise ValueError("Finite nonnegative sums and matching positive counts required.")
    return float(sums.sum()/counts.sum())


def choose_penalty(scores):
    """Exact ties choose the larger penalty; no data-dependent tie tolerance."""
    if not scores or any(not np.isfinite(s) or s < 0 or p <= 0 for p,s in scores):
        raise ValueError("Positive penalties and finite nonnegative scores required.")
    return float(min(scores, key=lambda item: (item[1], -item[0]))[0])


def fit_quotes(strikes, quotes, forwards, discounts, maturities, penalty):
    return fit_maturities(strikes, quotes, forwards, discounts, maturities, EDGES,
                          penalty=penalty, max_solver_iterations=200,
                          residual_form=True, solver_backend="clarabel")


def fit_record(joint):
    return {"weights": joint.weights.tolist(), "solver": joint.solver,
            "calendar": joint.continuous_check}


def select_penalty(strikes, quotes, forwards, discounts, maturities,
                   candidates=CANDIDATES, fitter=fit_quotes):
    """Selection has no access to clean prices, benchmark densities or risk targets."""
    counts = {len(k) for k in strikes}
    if len(counts) != 1 or len(strikes) != len(quotes):
        raise ValueError("Equal quote counts across maturities are required.")
    partition = folds(counts.pop())
    rows = []
    for penalty in candidates:
        saved = []
        for fold, (train, held) in enumerate(partition):
            joint = fitter([k[train] for k in strikes], [y[train] for y in quotes],
                           forwards, discounts, maturities, penalty)
            errors = np.array([(f.prices(k[held])-y[held])/forward
                              for f,k,y,forward in zip(joint.fits,strikes,quotes,forwards)])
            saved.append({"fold": fold, "train_indices": train.tolist(),
                          "held_indices": held.tolist(), "count": int(errors.size),
                          "squared_error_sum": float(np.sum(errors**2)),
                          "normalised_residuals": errors.tolist(), **fit_record(joint)})
        score = pooled_score([f["squared_error_sum"] for f in saved], [f["count"] for f in saved])
        rows.append({"penalty": penalty, "score": score, "folds": saved})
    selected = choose_penalty([(r["penalty"],r["score"]) for r in rows])
    return {"selected_penalty": selected, "candidates": rows,
            "boundary_selected": selected in (min(candidates),max(candidates))}


def reference_fit(fit, reference_forward):
    """Evaluation metadata only: never shift physical edges, masses or prices."""
    if not np.isfinite(reference_forward) or reference_forward <= 0:
        raise ValueError("A positive finite reference forward is required.")
    return replace(fit, forward=float(reference_forward))


def lower_bound_violations(strikes, quotes, forwards, discounts):
    deficits = np.concatenate([np.maximum(d*np.maximum(f-k,0)-y,0)
                               for k,y,f,d in zip(strikes,quotes,forwards,discounts)])
    return {"count": int(np.sum(deficits > 1e-10)), "quote_count": int(deficits.size),
            "maximum_shortfall": float(deficits.max()),
            "rms_shortfall": float(np.sqrt(np.mean(deficits**2))),
            "count_tolerance_points": 1e-10}


def observations(key, coverage, repetition):
    benchmark, ps = BENCHMARKS[key], parameters()
    indices = COVERAGES[coverage]["indices"]
    master = [master_strikes(p) for p in ps]
    clean = [benchmark.prices(k,p) for k,p in zip(master,ps)]
    draws, _ = random_draws(repetition)
    generated = [bounded_quotes(c,AMPLITUDE,u) for c,u in zip(clean,draws)]
    return ([k[indices] for k in master], [q[0][indices] for q in generated],
            [p.forward for p in ps], [np.exp(-p.rate*p.maturity) for p in ps],
            [p.maturity for p in ps])


def evaluate(joint, key, strikes, quotes, supplied_forwards):
    """Truth is accessed only after selection/refitting; events use reference F."""
    benchmark, ps = BENCHMARKS[key], parameters()
    marginals, errors = [], []
    for day,p,fit in zip(DAYS,ps,joint.fits):
        grid = master_strikes(p)
        test_strikes = (grid[:-1]+grid[1:])/2
        residual = fit.prices(test_strikes)-benchmark.prices(test_strikes,p)
        errors.extend(residual.tolist())
        fixed = reference_fit(fit,p.forward)
        marginals.append({"days":day, "reference_forward":p.forward,
            "supplied_forward":fit.forward, "discount":fit.discount,
            "physical_support":[float(fit.edges[0]),float(fit.edges[-1])],
            "validation_rmse":float(np.sqrt(np.mean(residual**2))),
            "density_error":full_density_error(fixed,benchmark,p.maturity),
            "risk":histogram_risk(fixed),"known_risk":true_risk(benchmark,p.maturity)})
    last=marginals[-1]
    return {**fit_record(joint), "penalty":joint.fits[0].penalty, "marginals":marginals,
        "lower_bound":lower_bound_violations(strikes,quotes,supplied_forwards,[f.discount for f in joint.fits]),
        "metrics":{"validation_rmse":float(np.sqrt(np.mean(np.asarray(errors)**2))),
            "mean_full_density_l1":float(np.mean([m["density_error"]["full_domain"] for m in marginals])),
            "tail_absolute_error_pp":100*abs(last["risk"]["above_1_8_forward"]-last["known_risk"]["above_1_8_forward"]),
            "tail_error_pp":100*(last["risk"]["above_1_8_forward"]-last["known_risk"]["above_1_8_forward"])}}


def selection_case(spec):
    args = observations(spec["benchmark"],spec["coverage"],spec["repetition"])
    cv = select_penalty(*args)
    selected = fit_quotes(*args,cv["selected_penalty"])
    fixed = None if cv["selected_penalty"] == PENALTY else fit_quotes(*args,PENALTY)
    # Evaluation starts only after both full-data fits have been determined.
    return {"spec":spec,"status":"accepted","selection":cv,
            "selected":evaluate(selected,spec["benchmark"],args[0],args[1],args[2]),
            "fixed":None if fixed is None else evaluate(fixed,spec["benchmark"],args[0],args[1],args[2]),
            "fixed_reuses_selected":fixed is None,"fit_count":9+1+int(fixed is not None)}


def forward_case(spec, selected_penalty):
    args=list(observations(spec["benchmark"],"extended",spec["repetition"]))
    args[2]=[f*(1+spec["shift"]) for f in args[2]]
    joint=fit_quotes(*args,selected_penalty)
    return {"spec":spec,"status":"accepted","fit_count":1,
            "fit":evaluate(joint,spec["benchmark"],args[0],args[1],args[2])}


def selection_specs():
    return [{"id":f'{key}_{coverage}_r{r:02}',"benchmark":key,"coverage":coverage,"repetition":r}
            for key in BENCHMARKS for coverage in PATTERNS for r in range(REPETITIONS)]


def forward_specs():
    return [{"id":f'{key}_extended_r{r:02}_f{int(round(s*10000)):+d}',
             "benchmark":key,"coverage":"extended","repetition":r,"shift":s,
             "parent":f'{key}_extended_r{r:02}'}
            for key in BENCHMARKS for r in range(REPETITIONS) for s in SHIFTS if s != 0]


def protocol():
    ps=parameters()
    return {"stage":8,"status":"synthetic_only","repetitions":REPETITIONS,
        "seed":list(SEED),"rng":"PCG64, SeedSequence((20260921,8), spawn_key=(repetition,))",
        "amplitude":AMPLITUDE,"days":list(DAYS),"edges":EDGES.tolist(),
        "reference_forwards":[p.forward for p in ps],
        "discounts":[float(np.exp(-p.rate*p.maturity)) for p in ps],
        "master_strikes":[master_strikes(p).tolist() for p in ps],
        "benchmark":{key:{"weights":b.weights,"volatilities":b.volatilities} for key,b in BENCHMARKS.items()},
        "coverage":{k:COVERAGES[k]["indices"].tolist() for k in PATTERNS},
        "candidates":list(CANDIDATES),"baseline_penalty":PENALTY,
        "folds":"Three interlaced interior holdouts; both endpoints always in training",
        "selection_loss":"Sum of squared held-out noisy residuals / F^2 divided by total held-out count",
        "tie_rule":"Larger lambda among exact minimum-score ties",
        "selection_scope":"One common lambda for all eight maturities; selection rerun for every noise realisation",
        "evaluation":"120 clean master-strike midpoints per maturity, full-domain L1 and fixed physical risk thresholds; never used in selection",
        "forward_shifts":list(SHIFTS),"forward_scope":"Extended 121 only; selected lambda held fixed at the zero-shift choice",
        "reference_events":"S_T < 0.8 F_true, S_T > 1.2 F_true, S_T > 1.8 F_true",
        "solver":{"backend":"clarabel","residual_form":True,"max_solver_iterations":200,
                  "calendar_tolerance":1e-8,"refinement_target":1e-9,"max_rounds":15},
        "planned_selection_experiments":80,"planned_cv_fits":720,
        "planned_full_selected_fits":80,"maximum_additional_fixed_fits":80,"planned_nonzero_forward_fits":160,
        "limits":["Fixed-design interior interpolation selector, not temporal market cross-validation",
                  "Three candidates only; boundary choices do not establish an optimum beyond the grid",
                  "Forward shocks are declared stresses, not measured market-input error probabilities",
                  "Changing supplied F changes the mean, physical support, normalisation and penalty coordinates together",
                  "Twenty independent repetitions; MCSE reported; no post-result enlargement of candidate set"]}


def signature(root):
    names=["src/density.py","src/constrained.py","src/surface.py","src/joint.py",
           "src/robustness.py","src/repeated.py","src/selection.py","run_selection.py"]
    hashes={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in names}
    payload={"protocol":protocol(),"code_sha256":hashes}
    return hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest(),hashes
