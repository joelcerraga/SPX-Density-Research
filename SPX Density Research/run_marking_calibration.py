"""First empirical case from the archived Cboe exchange-BBO marking files."""
import json
from pathlib import Path
import platform
import time

import clarabel
import numpy as np
import scipy

from src.empirical import sha256
from src.marking import (EXPIRIES, MAX_AGE_SECONDS, MAX_SPREAD, PROFILES,
                         audit_file, fit_market, residuals, select_market)
from src.repeated import EDGES
from src.robustness import histogram_risk
from src.selection import CANDIDATES, fit_record

ROOT=Path(__file__).resolve().parent
RAW=ROOT/"data/raw/marking_prices"


def write(path,value):
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+"\n")


def marginal(group,fit,carry):
    rr=residuals(group,fit)
    call=[r for r in rr if r["option_type"]=="C"]
    put=[r for r in rr if r["option_type"]=="P"]
    strikes=np.array([p.strike for p in group.pairs])
    return {"expiry":group.expiry,"observed_at":group.observed_at,
        "settlement_at":group.settlement_at,"maturity":group.maturity,
        "elapsed_days":365*group.maturity,"pair_count":len(group.pairs),
        "strike_range":strikes[[0,-1]].tolist(),"normalised_strike_range":(strikes[[0,-1]]/fit.forward).tolist(),
        "discount":fit.discount,"forward":fit.forward,"carry":carry,
        "quote_implied_rate":float(-np.log(fit.discount)/group.maturity),
        "edges":fit.edges.tolist(),"mass":fit.mass.tolist(),"risk":histogram_risk(fit),
        "call_midpoint_rmse":float(np.sqrt(np.mean([r["midpoint_residual"]**2 for r in call]))),
        "put_midpoint_rmse":float(np.sqrt(np.mean([r["midpoint_residual"]**2 for r in put]))),
        "outside_spread_count":sum(r["distance_outside_spread"]>1e-7 for r in rr),
        "call_outside_spread_count":sum(r["distance_outside_spread"]>1e-7 for r in call),
        "put_outside_spread_count":sum(r["distance_outside_spread"]>1e-7 for r in put),
        "maximum_spread_distance":max(r["distance_outside_spread"] for r in rr),
        "quote_residuals":rr}


def main():
    started=time.monotonic()
    protocol={"data_kind":"market_exchange_bbo","source_profile":"Cboe proprietary-index marking CSV, actual market columns",
        "primary_file":"eod_marking_prices_list.csv","observation_date":"2026-09-18",
        "primary_snapshot":"2026-09-18T15:00:00-05:00","root":"SPXW","expiries":list(EXPIRIES),
        "settlement":"16:00 America/New_York on the three reviewed full-session expiry dates; ACT/365 elapsed UTC seconds",
        "pair_screen":{"positive_ordered_bid_ask":True,"maximum_full_spread_over_midpoint":MAX_SPREAD,
            "maximum_message_age_seconds":MAX_AGE_SECONDS,"actual_market_sizes":"unavailable; indicative sizes not used"},
        "carry":"Constrained equal-weight midpoint parity regression for H=D*F and D; bid-ask pair inequalities",
        "cv":"Three interlaced interior-pair holdouts, endpoints retained, BOTH D and F estimated on training pairs",
        "candidates":list(CANDIDATES),"edges":EDGES.tolist(),"fit_count_expected":12,
        "sensitivity":"Refit all three candidate penalties on the complete retained sample; one is the selected fit",
        "objective":"Regularised call-midpoint squared errors, not spread-constrained prices",
        "model":"Deterministic carry and proportional dividends for forward-normalised calendar ordering",
        "reserved":"EOM August date and late September snapshot audited here; no date comparison fitted in this stage",
        "scope_limit":"No external discount curve, consolidated NBBO/depth claim, independent truth, historical holdout or statistical confidence band"}
    write(ROOT/"results/marking_protocol.json",protocol)
    verification=json.loads((RAW/"source_verification.json").read_text())
    for row in verification:
        if (not row["matches_official_source"] or row["source_sha256"]!=row["uploaded_sha256"]
                or sha256(RAW/row["filename"])!=row["uploaded_sha256"]):
            raise ValueError("Archived input no longer matches its source-verification record.")
    audits=[];groups=None
    for name in PROFILES:
        candidate,audit=audit_file(RAW/name)
        if audit["metadata_failure_rows"]:raise ValueError(f"Unresolved source metadata in {name}")
        audits.append(audit)
        if name==protocol["primary_file"]:groups=candidate
    if groups is None or any(len(g.pairs)<7 for g in groups):raise ValueError("Insufficient retained matched pairs.")
    write(ROOT/"results/marking_input_audit.json",{"files":audits,"source_verification":verification})
    observations=[{"expiry":g.expiry,"pairs":[{"strike":p.strike,"call":p.call,"put":p.put} for p in g.pairs]} for g in groups]
    write(ROOT/"results/marking_retained_pairs.json",observations)
    print(f'Actual exchange BBO: {sum(len(g.pairs) for g in groups)} matched pairs; selecting across three penalties.',flush=True)
    selection=select_market(groups)
    print(f'Selection complete: lambda={selection["selected_penalty"]:g}. Refit all candidates for sensitivity.',flush=True)
    complete=[]
    for penalty in CANDIDATES:
        joint,carry=fit_market(groups,[g.pairs for g in groups],penalty)
        complete.append({"penalty":penalty,**fit_record(joint),
            "marginals":[marginal(g,f,c) for g,f,c in zip(groups,joint.fits,carry)]})
        print(f'Full sample lambda={penalty:g}: calendar minimum {joint.continuous_check["minimum_gap"]:.3g}.',flush=True)
    selected=next(c for c in complete if c["penalty"]==selection["selected_penalty"])
    all_fits=complete+[f for c in selection["candidates"] for f in c["folds"]]
    histories=[h for fit in all_fits for h in fit["solver"]["history"]]
    checks={"joint_fit_count":len(all_fits),"marginal_fit_count":3*len(all_fits),
        "all_statuses_solved":all(h["status"]=="Solved" for h in histories),
        "all_calendar_checks_pass":all(f["calendar"]["passes"] for f in all_fits),
        "minimum_final_calendar_gap":min(f["calendar"]["minimum_gap"] for f in all_fits),
        "minimum_bin_mass":min(h["minimum_bin_mass"] for h in histories),
        "maximum_mass_error":max(h["maximum_mass_error"] for h in histories),
        "maximum_mean_error":max(h["maximum_normalised_mean_error"] for h in histories),
        "maximum_auxiliary_residual":max(h["maximum_residual_equation_error"] for h in histories)}
    if not checks["all_statuses_solved"] or not checks["all_calendar_checks_pass"]:
        raise RuntimeError("Empirical run did not meet the declared numerical criteria.")
    result={"status":"complete_first_empirical_case","data_kind":"market_exchange_bbo",
        "protocol_sha256":sha256(ROOT/"results/marking_protocol.json"),
        "inputs_sha256":{n:sha256(RAW/n) for n in PROFILES},"selection":selection,
        "full_sample_fits":complete,"selected_penalty":selection["selected_penalty"],
        "validation":checks,"elapsed_seconds":time.monotonic()-started,
        "environment":{"python":platform.python_version(),"numpy":np.__version__,"scipy":scipy.__version__,"clarabel":clarabel.__version__},
        "code_sha256":{n:sha256(ROOT/n) for n in ("src/marking.py","run_marking_calibration.py","src/empirical.py",
            "src/joint.py","src/constrained.py","src/selection.py","src/robustness.py")}}
    write(ROOT/"results/marking_calibration.json",result)
    write(ROOT/"results/marking_validation.json",checks)
    print(f'Completed {len(all_fits)} joint fits. Selected fit: {sum(m["outside_spread_count"] for m in selected["marginals"])} / '
          f'{2*sum(len(g.pairs) for g in groups)} fitted call/put prices outside their spreads (tolerance 1e-7 points).',flush=True)
    return result


if __name__=="__main__":main()
