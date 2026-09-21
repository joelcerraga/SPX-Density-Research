"""Run or resume the fixed smoothing-selection and forward-input experiment."""
import os
for _thread_setting in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS"):
    os.environ[_thread_setting]="1"

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from src.repeated import (BENCHMARKS, DAYS, EDGES, RISK_FIELDS, bounded_quotes,
                          master_strikes, paired_summary, parameters, scalar_summary)
from src.selection import (AMPLITUDE,CANDIDATES,PATTERNS,REPETITIONS,SHIFTS,
    forward_case,forward_specs,protocol,random_draws,selection_case,selection_specs,signature)

ROOT=Path(__file__).resolve().parent
CASE_DIR=ROOT/"results/selection_cases"


def write_json(path,value):
    temporary=path.with_suffix(path.suffix+".tmp")
    temporary.write_text(json.dumps(value,indent=2,allow_nan=False)+"\n")
    temporary.replace(path)


def result_hash(result):
    return hashlib.sha256(json.dumps(result,sort_keys=True,allow_nan=False).encode()).hexdigest()


def worker(spec,fingerprint,parent=None):
    start=time.monotonic()
    try:
        result=(selection_case(spec) if parent is None else
                forward_case(spec,parent["selection"]["selected_penalty"]))
    except Exception as exc:
        result={"spec":spec,"status":"failed","error_type":type(exc).__name__,"error":str(exc)}
    result["runtime_seconds"]=time.monotonic()-start
    result["completed_utc"]=datetime.now(timezone.utc).isoformat()
    record={"signature":fingerprint,"result_sha256":result_hash(result),"result":result,
            "parent_sha256":None if parent is None else result_hash(parent)}
    write_json(CASE_DIR/(spec["id"]+".json"),record)
    return result


def write_inputs():
    states,draws=[],[]
    for r in range(REPETITIONS):
        u,state=random_draws(r);draws.append(u);states.append(state)
    write_json(ROOT/"results/selection_random_states.json",states)
    with (ROOT/"results/selection_quotes.csv").open("w",newline="") as f:
        out=csv.writer(f)
        out.writerow(["benchmark","repetition","days","master_index","strike","clean_call",
                      "unit_draw","error_half_width","added_error","observed_call"])
        for key,bench in BENCHMARKS.items():
            for r in range(REPETITIONS):
                for m,(day,p) in enumerate(zip(DAYS,parameters())):
                    k=master_strikes(p);clean=bench.prices(k,p)
                    y,e,width=bounded_quotes(clean,AMPLITUDE,draws[r][m])
                    out.writerows(zip([key]*121,[r]*121,[day]*121,range(121),k,clean,draws[r][m],width,e,y))


def batch(specs,fingerprint,resume,workers,parents=None):
    results,pending=[],[]
    for spec in specs:
        parent=None if parents is None else parents[spec["parent"]]
        if parent is not None and parent["status"]!="accepted":
            result={"spec":spec,"status":"blocked","error":"Required selection experiment failed"}
            write_json(CASE_DIR/(spec["id"]+".json"),{"signature":fingerprint,
                "result_sha256":result_hash(result),"result":result,"parent_sha256":result_hash(parent)})
            results.append(result);continue
        path=CASE_DIR/(spec["id"]+".json")
        if resume and path.exists():
            record=json.loads(path.read_text())
            if (record["signature"]!=fingerprint or record["result_sha256"]!=result_hash(record["result"])
                    or record["result"]["spec"]!=spec
                    or record["parent_sha256"]!=(None if parent is None else result_hash(parent))):
                raise RuntimeError(f'Case provenance changed: {spec["id"]}; use --fresh for the declared study.')
            results.append(record["result"])
        else:pending.append((spec,parent))
    label="Selection" if parents is None else "Forward"
    print(f'{label}: {len(results)} saved / {len(specs)} planned experiments; {len(pending)} to run.',flush=True)
    if pending:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures=[pool.submit(worker,s,fingerprint,p) for s,p in pending]
            for future in as_completed(futures):
                result=future.result();results.append(result)
                if result["status"]!="accepted":print(f'FAILED {result["spec"]["id"]}: {result["error"]}',flush=True)
                if len(results)%10==0 or len(results)==len(specs):
                    print(f'{label}: {len(results)}/{len(specs)} recorded; {sum(c["status"]!="accepted" for c in results)} unsuccessful.',flush=True)
    return sorted(results,key=lambda c:c["spec"]["id"])


def fixed_fit(case):
    return case["selected"] if case["fixed_reuses_selected"] else case["fixed"]


def summarise_fits(fits):
    return {"metrics":{name:scalar_summary([f["metrics"][name] for f in fits]) for name in fits[0]["metrics"]},
        "risk_by_day":[{"days":d,**{name:scalar_summary([f["marginals"][m]["risk"][name] for f in fits],
                   fits[0]["marginals"][m]["known_risk"][name]) for name in RISK_FIELDS}}
                      for m,d in enumerate(DAYS)],
        "lower_bound":{field:scalar_summary([f["lower_bound"][field] for f in fits])
                       for field in ("count","maximum_shortfall","rms_shortfall")}}


def aggregate(selection,forward):
    groups=[]
    for key in BENCHMARKS:
        for coverage in PATTERNS:
            cases=[c for c in selection if c["spec"]["benchmark"]==key and c["spec"]["coverage"]==coverage]
            complete=len(cases)==REPETITIONS and all(c["status"]=="accepted" for c in cases)
            row={"benchmark":key,"coverage":coverage,"attempted":len(cases),
                 "accepted":sum(c["status"]=="accepted" for c in cases),"complete":complete}
            if complete:
                a,b=[c["selected"] for c in cases],[fixed_fit(c) for c in cases]
                row.update(selected=summarise_fits(a),fixed=summarise_fits(b),
                    selection_counts={str(p):sum(c["selection"]["selected_penalty"]==p for c in cases) for p in CANDIDATES},
                    candidate_scores={str(p):scalar_summary([next(r["score"] for r in c["selection"]["candidates"] if r["penalty"]==p) for c in cases]) for p in CANDIDATES},
                    paired_selected_minus_fixed={name:paired_summary([f["metrics"][name] for f in a],
                      [f["metrics"][name] for f in b]) for name in a[0]["metrics"]})
            groups.append(row)
    stress=[]
    for key in BENCHMARKS:
        base=[c for c in selection if c["spec"]["benchmark"]==key and c["spec"]["coverage"]=="extended"]
        base.sort(key=lambda c:c["spec"]["repetition"])
        for shift in SHIFTS:
            cases=base if shift==0 else [c for c in forward if c["spec"]["benchmark"]==key and c["spec"]["shift"]==shift]
            cases=sorted(cases,key=lambda c:c["spec"]["repetition"])
            complete=len(cases)==REPETITIONS and all(c["status"]=="accepted" for c in cases+base)
            row={"benchmark":key,"shift":shift,"attempted":len(cases),
                 "accepted":sum(c["status"]=="accepted" for c in cases),"complete":complete}
            if complete:
                a=[c["selected" if shift==0 else "fit"] for c in cases];b=[c["selected"] for c in base]
                row.update(**summarise_fits(a),paired_minus_zero={name:paired_summary(
                    [f["metrics"][name] for f in a],[f["metrics"][name] for f in b]) for name in a[0]["metrics"]})
            stress.append(row)
    return groups,stress


def all_fits(selection,forward):
    for c in selection:
        if c["status"]!="accepted":continue
        for candidate in c["selection"]["candidates"]:yield from candidate["folds"]
        yield c["selected"]
        if not c["fixed_reuses_selected"]:yield c["fixed"]
    for c in forward:
        if c["status"]=="accepted":yield c["fit"]


def export_metrics(selection,forward):
    with (ROOT/"results/selection_metrics.csv").open("w",newline="") as f:
        out=csv.writer(f)
        fields=("validation_rmse","mean_full_density_l1","tail_error_pp","tail_absolute_error_pp")
        out.writerow(["case_id","benchmark","coverage","repetition","method","forward_shift","penalty",*fields])
        for c in selection:
            if c["status"]!="accepted":continue
            s=c["spec"]
            for name,fit in [("selected",c["selected"]),("fixed",fixed_fit(c))]:
                out.writerow([s["id"],s["benchmark"],s["coverage"],s["repetition"],name,0,fit["penalty"],*[fit["metrics"][v] for v in fields]])
        for c in forward:
            if c["status"]!="accepted":continue
            s,fit=c["spec"],c["fit"]
            out.writerow([s["id"],s["benchmark"],s["coverage"],s["repetition"],"forward",s["shift"],fit["penalty"],*[fit["metrics"][v] for v in fields]])


def main(resume=True,workers=4):
    if not isinstance(workers,int) or workers < 1:raise ValueError("Positive worker count required.")
    CASE_DIR.mkdir(exist_ok=True,parents=True)
    fingerprint,hashes=signature(ROOT)
    design={**protocol(),"numerical_signature":fingerprint,"code_sha256":hashes}
    write_json(ROOT/"results/selection_protocol.json",design);write_inputs()
    selection=batch(selection_specs(),fingerprint,resume,workers)
    forward=batch(forward_specs(),fingerprint,resume,workers,{c["spec"]["id"]:c for c in selection})
    groups,stress=aggregate(selection,forward)
    fits=list(all_fits(selection,forward));histories=[h for f in fits for h in f["solver"]["history"]]
    scored=[c["selected"] for c in selection if c["status"]=="accepted"]
    scored += [c["fixed"] for c in selection if c["status"]=="accepted" and not c["fixed_reuses_selected"]]
    scored += [c["fit"] for c in forward if c["status"]=="accepted"]
    failures=[c for c in selection+forward if c["status"]!="accepted"]
    checks={"planned_experiments":240,"recorded_experiments":len(selection+forward),"failed_or_blocked":len(failures),
        "unique_accepted_joint_fits":len(fits),"accepted_marginals":len(fits)*len(DAYS),
        "reused_fixed_fits":sum(c["fixed_reuses_selected"] for c in selection if c["status"]=="accepted"),
        "all_calendar_checks_pass":not failures and all(f["calendar"]["passes"] for f in fits),
        "minimum_calendar_gap":min(f["calendar"]["minimum_gap"] for f in fits),
        "maximum_mass_error":max(h["maximum_mass_error"] for h in histories),
        "maximum_normalised_mean_error":max(h["maximum_normalised_mean_error"] for h in histories),
        "minimum_raw_mass":min(h["minimum_bin_mass"] for h in histories),
        "maximum_residual_equation_error":max(h["maximum_residual_equation_error"] for h in histories),
        "maximum_solver_iterations":max(h["iterations"] for h in histories),
        "maximum_refinement_rounds":max(f["solver"]["refinement_rounds"] for f in fits),
        "maximum_quadrature_error_estimate":max(m["density_error"]["quadrature_error_estimate"] for f in scored for m in f["marginals"])}
    export_metrics(selection,forward)
    report={"protocol":design,"checks":checks,"groups":groups,"forward_groups":stress,"failures":failures,
            "cases":[{"id":c["spec"]["id"],"status":c["status"],"file":"selection_cases/"+c["spec"]["id"]+".json"} for c in selection+forward]}
    report["input_sha256"]={name:hashlib.sha256((ROOT/"results"/name).read_bytes()).hexdigest()
        for name in ("selection_protocol.json","selection_quotes.csv","selection_random_states.json")}
    write_json(ROOT/"results/selection_validation.json",report)
    print(f'{len(fits)} unique accepted joint fits; {len(failures)} failed/blocked experiments; minimum calendar gap {checks["minimum_calendar_gap"]:.3e}.',flush=True)
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fresh",action="store_true")
    parser.add_argument("--workers",type=int,default=4)
    args=parser.parse_args();main(resume=not args.fresh,workers=args.workers)
