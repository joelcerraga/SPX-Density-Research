"""Build and validate Notebook 9's explicitly synthetic input fixture."""
import copy
import csv
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import platform

import clarabel
import numpy as np
import scipy

from src.density import Parameters
from src.empirical import (DISCOUNT_FIELDS, QUOTE_FIELDS, calibrate, parity_interval,
                           prepare_groups, read_bundle, sha256, year_fraction)
from src.robustness import BENCHMARKS, full_density_error
from src.selection import reference_fit

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT/"data/fixtures/empirical"
SEED = (20260921, 9)


def write_csv(path, fields, rows):
    with Path(path).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fields)
        writer.writeheader()
        writer.writerows(rows)


def json_write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+"\n")


def generate_fixture():
    """Invented dates identify test rows; they are not exchange calendar assertions."""
    FIXTURE.mkdir(parents=True, exist_ok=True)
    observed = "2026-01-15T15:45:00-05:00"
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(SEED)))
    initial_state = copy.deepcopy(rng.bit_generator.state)
    rows, discounts, truth = [], [], []
    for days, count in ((60,41), (120,47), (240,53)):
        expiry = (datetime(2026,1,15)+timedelta(days=days)).date().isoformat()
        settlement = expiry+"T16:00:00-04:00"
        T = year_fraction(observed,settlement)
        p = Parameters(maturity=T)
        discount = float(np.exp(-p.rate*T))
        strikes = p.forward*np.linspace(.65,1.55,count)
        calls = BENCHMARKS["mixture"].prices(strikes,p)
        puts = calls-discount*(p.forward-strikes)
        assert np.min(puts)>0 and np.min(calls)>0
        for i,(strike,call,put) in enumerate(zip(strikes,calls,puts)):
            for typ, value in (("C",call),("P",put)):
                width = min(.75,.08*value)
                midpoint = value+.2*width*rng.uniform(-1,1)
                rows.append({"quote_id":f"FIXTURE-{days}-{i:03}-{typ}",
                    "snapshot_id":"SYNTHETIC-ONLY-01", "observed_at":observed,
                    "root":"SPXW", "expiry":expiry, "settlement_at":settlement,
                    "exercise":"European", "settlement_style":"PM", "option_type":typ,
                    "strike":float(strike), "bid":float(midpoint-width), "ask":float(midpoint+width),
                    "bid_size":5, "ask_size":7})
        discounts.append({"snapshot_id":"SYNTHETIC-ONLY-01", "root":"SPXW", "settlement_at":settlement,
            "discount":discount, "observed_at":observed, "available_at":observed,
            "source_reference":"Synthetic constant rate r=0.04; not a market yield curve."})
        truth.append({"nominal_days":days,"expiry":expiry,"maturity":T,
            "forward":float(p.forward),"discount":discount,"strikes":strikes.tolist(),"pair_count":count})
    write_csv(FIXTURE/"quotes.csv",QUOTE_FIELDS,rows)
    write_csv(FIXTURE/"discounts.csv",DISCOUNT_FIELDS,discounts)
    manifest = {"schema_version":1,"data_kind":"synthetic_fixture","underlying":"SPX",
        "quote_units":"index_points", "settlement_type":"cash", "timestamp_semantics":"contemporaneous_nbbo_snapshot",
        "size_semantics":"positive_displayed_contracts",
        "calendar_model":"deterministic_carry_proportional_dividends",
        "source_evidence":{key:"Synthetic fixture generated in run_empirical_preparation.py; no observed market information."
                           for key in ("quotes","observation_time","sizes","settlement","discounts","research_use")},
        "screening":{"max_relative_spread":.25,"max_curve_age_seconds":86400},
        "input_sha256":{name:sha256(FIXTURE/name) for name in ("quotes.csv","discounts.csv")},
        "notes":"All prices, sizes, discounts and dates are test inputs. Dates do not assert real listed contracts or exchange sessions."}
    json_write(FIXTURE/"manifest.json",manifest)
    json_write(FIXTURE/"truth.json",{"data_kind":"synthetic_fixture", "benchmark":"mixture", "seed":list(SEED),
        "initial_rng_state":initial_state,"final_rng_state":rng.bit_generator.state,
        "groups":truth,"half_spread":"min(0.75, 0.08 * analytical price)",
        "midpoint":"analytical price + 0.2 * half_spread * Uniform[-1,1]",
        "evaluation":"Analytical prices at midpoints between input strikes; not used for selection."})
    return truth


def input_checks(manifest, rows, discounts):
    evidence = []
    variants = []
    bad=copy.deepcopy(rows);bad[0]["observed_at"]="2026-01-15T15:45:00"
    variants.append(("Missing quote timezone",bad,discounts))
    bad=copy.deepcopy(rows);bad[0]["observed_at"]="2026-01-15T15:46:00-05:00"
    variants.append(("Unsynchronised quote",bad,discounts))
    bad=copy.deepcopy(rows);bad[0]["settlement_at"]="2026-03-16T09:30:00-04:00"
    variants.append(("Conflicting settlement time",bad,discounts))
    bad=copy.deepcopy(discounts);bad[0]["available_at"]="2026-01-15T16:00:00-05:00"
    variants.append(("Discount published after the snapshot",rows,bad))
    bad=copy.deepcopy(discounts);bad[0]["observed_at"]="2026-01-13T15:45:00-05:00"
    variants.append(("Discount older than the declared limit",rows,bad))
    for label,q,d in variants:
        _,audit=prepare_groups(manifest,q,d)
        if not audit["fatal_errors"]:
            raise AssertionError(f"Invalid case was not blocked: {label}")
        evidence.append({"case":label,"expected":"blocked","observed":"blocked","reasons":audit["fatal_errors"]})
    bad=copy.deepcopy(rows)
    # Preserve valid prices/sizes while breaking cross-strike put–call compatibility.
    bad[0]["bid"]=str(float(bad[0]["bid"])+5)
    bad[0]["ask"]=str(float(bad[0]["ask"])+5)
    groups,audit=prepare_groups(manifest,bad,discounts)
    assert not audit["fatal_errors"]
    interval=parity_interval(groups[0].pairs,groups[0].discount)
    assert not interval["feasible"]
    evidence.append({"case":"Call bid and ask at the first strike increased by 5 points",
        "expected":"blocked by parity","observed":"blocked by parity","interval":interval,
        "reconstruction":"Add 5 to bid and ask of the first data row in the saved fixture quotes.csv; all other fields unchanged."})
    bad=copy.deepcopy(rows)
    bad[0]["bid_size"]="0"
    bad.append(copy.deepcopy(bad[4]));bad[-1]["quote_id"]="FIXTURE-DUPLICATE"
    _,audit=prepare_groups(manifest,bad,discounts)
    assert audit["reason_counts"]=={"unusable_size":1,"unmatched_pair":2,"duplicate_quote":2}
    evidence.append({"case":"Zero size and a duplicated call quote","expected":"five rows excluded",
        "observed":f'{audit["excluded_rows"]} rows excluded',"reason_counts":audit["reason_counts"],
        "reconstruction":"Set first data row bid_size to zero; append a copy of the fifth data row with quote_id FIXTURE-DUPLICATE."})
    return evidence


def main():
    truth=generate_fixture()
    manifest, rows, discounts=read_bundle(FIXTURE)
    result,joint,groups=calibrate(FIXTURE)
    if joint is None:
        raise RuntimeError("The synthetic compatibility fixture was unexpectedly blocked.")
    evaluation=[]
    for known,g,fit in zip(truth,groups,joint.fits):
        p=Parameters(maturity=g.maturity)
        strikes=np.array([pair.strike for pair in g.pairs])
        test=(strikes[:-1]+strikes[1:])/2
        residual=fit.prices(test)-BENCHMARKS["mixture"].prices(test,p)
        evaluation.append({"expiry":g.expiry,"known_forward":known["forward"],
            "estimated_forward":fit.forward,"forward_error":fit.forward-known["forward"],
            "clean_test_strikes":test.tolist(),"clean_test_residuals":residual.tolist(),
            "clean_test_rmse":float(np.sqrt(np.mean(residual**2))),
            "density_error":full_density_error(reference_fit(fit,known["forward"]),BENCHMARKS["mixture"],g.maturity)})
    result["fixture_evaluation"]=evaluation
    result["input_checks"]=input_checks(manifest,rows,discounts)
    result["environment"]={"python":platform.python_version(),"numpy":np.__version__,
        "scipy":scipy.__version__,"clarabel":clarabel.__version__}
    result["code_sha256"]={name:sha256(ROOT/name) for name in (
        "src/density.py","src/constrained.py","src/joint.py","src/robustness.py",
        "src/repeated.py","src/selection.py","src/empirical.py","run_empirical_preparation.py")}
    result["fixture_sha256"]={name:sha256(FIXTURE/name) for name in ("quotes.csv","discounts.csv","manifest.json","truth.json")}
    result["actual_market_calibration"]={"status":"not_performed", "reason":"This synthetic fixture runner does not calibrate market data; see marking_calibration.json for the separately recorded empirical case.",
        "candidate_payload_sha256":sha256(ROOT/"data/raw/cboe_spx_candidate.json"),
        "sample_attempt":"data/raw/cboe_eod_sample/retrieval.json"}
    json_write(ROOT/"results/empirical_preparation.json",result)
    print(f'Synthetic preparation: {result["audit"]["retained_rows"]} rows, {len(groups)} horizons, '
          f'{result["fit_count"]} joint fits, selected lambda={result["selection"]["selected_penalty"]:g}.')
    print("All deliberately invalid metadata/parity cases blocked; row exclusions retain their reasons.")
    print("This acceptance exercise is synthetic; market calibration is recorded separately.")
    return result


if __name__=="__main__":
    main()
