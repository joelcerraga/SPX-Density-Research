"""Run or resume the fixed paired simulation, retaining every attempted case."""
import os
# Explicit settings keep process-level parallelism from oversubscribing BLAS.
for _thread_variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_thread_variable] = "1"

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from src.repeated import (AMPLITUDES, BENCHMARKS, COVERAGES, DAYS, EDGES,
    REPETITIONS, RISK_FIELDS, bounded_quotes, case_specs, fit_case, master_strikes,
    paired_summary, parameters, protocol, random_draws, scalar_summary, signature)

ROOT = Path(__file__).resolve().parent
CASE_DIR = ROOT / "results/repeated_cases"


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def result_hash(result):
    return hashlib.sha256(json.dumps(result,sort_keys=True,allow_nan=False).encode()).hexdigest()


def worker(spec, fingerprint):
    start = time.monotonic()
    try:
        result = fit_case(spec)
    except Exception as exc:
        result = {"spec":spec,"status":"failed","error_type":type(exc).__name__,"error":str(exc)}
    result["runtime_seconds"] = time.monotonic()-start
    result["completed_utc"] = datetime.now(timezone.utc).isoformat()
    record = {"signature":fingerprint,"result_sha256":result_hash(result),"result":result}
    write_json(CASE_DIR / (spec["id"] + ".json"),record)
    return result


def write_inputs():
    ps = parameters()
    states, draws = [], []
    for repetition in range(REPETITIONS):
        u,state = random_draws(repetition)
        states.append(state); draws.append(u)
    write_json(ROOT / "results/repeated_random_states.json", states)
    path = ROOT / "results/repeated_quotes.csv"
    with path.open("w",newline="") as f:
        out=csv.writer(f)
        out.writerow(["benchmark","amplitude","repetition","days","master_index","strike",
                      "clean_call","unit_draw","error_half_width","added_error","observed_call"])
        for key,bench in BENCHMARKS.items():
            for amplitude,reps in [(0.,[-1]), *[(a,range(REPETITIONS)) for a in AMPLITUDES]]:
                for repetition in reps:
                    for m,(d,p) in enumerate(zip(DAYS,ps)):
                        strikes=master_strikes(p);clean=bench.prices(strikes,p)
                        u=np.zeros(121) if repetition < 0 else draws[repetition][m]
                        y,e,b=bounded_quotes(clean,amplitude,u)
                        for j in range(121):
                            out.writerow([key,amplitude,repetition,d,j,strikes[j],clean[j],u[j],b[j],e[j],y[j]])


def aggregate(results):
    groups, clean, paired = [], [], []
    for key in BENCHMARKS:
        for coverage in COVERAGES:
            control=next(c for c in results if c["spec"]["benchmark"]==key
                         and c["spec"]["coverage"]==coverage and c["spec"]["amplitude"]==0)
            clean.append({k:v for k,v in control.items() if k not in ("weights","solver")})
            for amplitude in AMPLITUDES:
                cases=sorted([c for c in results if c["spec"]["benchmark"]==key
                              and c["spec"]["coverage"]==coverage and c["spec"]["amplitude"]==amplitude],
                             key=lambda c:c["spec"]["repetition"])
                accepted=[c for c in cases if c["status"]=="accepted"]
                row={"benchmark":key,"coverage":coverage,"amplitude":amplitude,
                     "attempted":len(cases),"accepted":len(accepted),"complete":len(accepted)==REPETITIONS}
                if row["complete"]:
                    row["metrics"]={field:scalar_summary([c["metrics"][field] for c in cases])
                        for field in cases[0]["metrics"] if cases[0]["metrics"][field] is not None}
                    row["risk_by_day"]=[]
                    for m,d in enumerate(DAYS):
                        row["risk_by_day"].append({"days":d,**{field:scalar_summary(
                            [c["marginals"][m]["risk"][field] for c in cases],
                            cases[0]["marginals"][m]["known_risk"][field]) for field in RISK_FIELDS}})
                groups.append(row)
        for amplitude in AMPLITUDES:
            for left,right in [("sparse","original"),("central","original"),("extended","original"),("central","sparse")]:
                a=sorted([c for c in results if c["spec"]["benchmark"]==key and c["spec"]["coverage"]==left
                          and c["spec"]["amplitude"]==amplitude],key=lambda c:c["spec"]["repetition"])
                b=sorted([c for c in results if c["spec"]["benchmark"]==key and c["spec"]["coverage"]==right
                          and c["spec"]["amplitude"]==amplitude],key=lambda c:c["spec"]["repetition"])
                row={"benchmark":key,"amplitude":amplitude,"left":left,"right":right,
                     "complete":all(c["status"]=="accepted" for c in a+b) and len(a)==len(b)==REPETITIONS}
                if row["complete"]:
                    row["metrics"]={field:paired_summary([c["metrics"][field] for c in a],
                        [c["metrics"][field] for c in b]) for field in ("mean_full_density_l1","validation_rmse")}
                    def tail_error(c):
                        m=c["marginals"][-1]
                        return 100*abs(m["risk"]["above_1_8_forward"]-m["known_risk"]["above_1_8_forward"])
                    row["tail_absolute_error_pp"]=paired_summary([tail_error(c) for c in a],[tail_error(c) for c in b])
                paired.append(row)
    return groups,clean,paired


def write_exports(results):
    with (ROOT/"results/repeated_metrics.csv").open("w",newline="") as f, (ROOT/"results/repeated_bin_masses.csv").open("w",newline="") as g:
        metrics=csv.writer(f);masses=csv.writer(g)
        metrics.writerow(["case_id","benchmark","coverage","amplitude","repetition","days",
            "validation_rmse","full_density_l1",*RISK_FIELDS,*["known_"+k for k in RISK_FIELDS]])
        masses.writerow(["case_id","days","left_normalised_edge","right_normalised_edge","mass"])
        for c in results:
            if c["status"]!="accepted":continue
            s=c["spec"]
            for m,w in zip(c["marginals"],c["weights"]):
                metrics.writerow([s["id"],s["benchmark"],s["coverage"],s["amplitude"],s["repetition"],m["days"],
                    m["validation_rmse"],m["density_error"]["full_domain"],*[m["risk"][k] for k in RISK_FIELDS],
                    *[m["known_risk"][k] for k in RISK_FIELDS]])
                masses.writerows(zip([s["id"]]*len(w),[m["days"]]*len(w),EDGES[:-1],EDGES[1:],w))


def main(resume=True, workers=4):
    if not isinstance(workers,int) or workers < 1:
        raise ValueError("Positive worker count required.")
    CASE_DIR.mkdir(parents=True,exist_ok=True)
    fingerprint,hashes=signature(ROOT)
    design={**protocol(),"numerical_signature":fingerprint,"code_sha256":hashes}
    write_json(ROOT/"results/repeated_protocol.json",design)
    write_inputs()
    results,pending=[],[]
    for spec in case_specs():
        path=CASE_DIR/(spec["id"]+".json")
        if resume and path.exists():
            record=json.loads(path.read_text())
            if record["signature"]!=fingerprint or record["result_sha256"]!=result_hash(record["result"]):
                raise RuntimeError(f'Case provenance changed: {spec["id"]}; use --fresh to recompute the declared study.')
            if record["result"]["spec"]!=spec:
                raise RuntimeError("Saved case specification does not match.")
            results.append(record["result"])
        else: pending.append(spec)
    print(f'Fixed study: {len(case_specs())} fits; {len(results)} matching saved cases, {len(pending)} to run.',flush=True)
    if pending:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures=[pool.submit(worker,s,fingerprint) for s in pending]
            for future in as_completed(futures):
                result=future.result();results.append(result)
                count=len(results)
                if result["status"]!="accepted":
                    print(f'FAILED {result["spec"]["id"]}: {result["error"]}',flush=True)
                if count%20==0 or count==len(case_specs()):
                    print(f'{count}/{len(case_specs())} cases recorded; failures {sum(c["status"]!="accepted" for c in results)}.',flush=True)
    results.sort(key=lambda c:c["spec"]["id"])
    groups,clean,paired=aggregate(results)
    accepted=[c for c in results if c["status"]=="accepted"]
    histories=[h for c in accepted for h in c["solver"]["history"]]
    checks={"attempted":len(results),"accepted":len(accepted),"failed":len(results)-len(accepted),
        "accepted_marginals":len(accepted)*len(DAYS),
        "all_calendar_checks_pass":len(accepted)==len(results) and all(c["calendar"]["passes"] for c in accepted),
        "minimum_calendar_gap":min(c["calendar"]["minimum_gap"] for c in accepted),
        "maximum_mass_error":max(h["maximum_mass_error"] for h in histories),
        "maximum_normalised_mean_error":max(h["maximum_normalised_mean_error"] for h in histories),
        "minimum_raw_mass":min(h["minimum_bin_mass"] for h in histories),
        "maximum_residual_equation_error":max(h["maximum_residual_equation_error"] for h in histories),
        "maximum_solver_iterations":max(h["iterations"] for h in histories),
        "maximum_refinement_rounds":max(c["solver"]["refinement_rounds"] for c in accepted),
        "maximum_quadrature_error_estimate":max(m["density_error"]["quadrature_error_estimate"] for c in accepted for m in c["marginals"])}
    report={"protocol":design,"checks":checks,"groups":groups,"clean_controls":clean,"paired":paired,
        "failures":[c for c in results if c["status"]!="accepted"],
        "cases":[{"id":c["spec"]["id"],"status":c["status"],"file":"repeated_cases/"+c["spec"]["id"]+".json"} for c in results],
        "limits":["Synthetic bounded errors, fixed known forwards and fixed regularisation",
                  "Monte Carlo standard errors concern the stated repeated experiment, not market probabilities",
                  "No model confidence intervals, penalty tuning or empirical calibration",
                  "All incomplete groups are withheld from aggregate performance summaries"]}
    write_exports(results)
    report["input_sha256"]={name:hashlib.sha256((ROOT/"results"/name).read_bytes()).hexdigest()
        for name in ("repeated_protocol.json","repeated_quotes.csv","repeated_random_states.json")}
    write_json(ROOT/"results/repeated_validation.json",report)
    print(f'Accepted {checks["accepted"]}/{checks["attempted"]}; minimum calendar gap {checks["minimum_calendar_gap"]:.3e}.',flush=True)
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fresh",action="store_true",help="Recompute every case instead of checking and reusing matching saved cases.")
    parser.add_argument("--workers",type=int,default=4)
    args=parser.parse_args()
    main(resume=not args.fresh,workers=args.workers)
