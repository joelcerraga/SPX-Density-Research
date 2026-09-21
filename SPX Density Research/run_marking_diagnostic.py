"""Explicitly post-hoc lower-penalty check, preserving the primary result."""
import json
from pathlib import Path

from run_marking_calibration import marginal, write
from src.empirical import sha256
from src.marking import audit_file, fit_market, select_market
from src.selection import fit_record

ROOT=Path(__file__).resolve().parent
CANDIDATES=(1e-10,1e-9,1e-8)


def main():
    parent=ROOT/"results/marking_calibration.json"
    primary=json.loads(parent.read_text())
    if not primary["selection"]["boundary_selected"]:
        raise ValueError("This diagnostic was motivated by a boundary choice in the recorded primary run.")
    groups,_=audit_file(ROOT/"data/raw/marking_prices/eod_marking_prices_list.csv")
    result={"label":"Post-hoc diagnostic, not a replacement for the declared primary selection",
        "reason":"Primary minimum candidate chosen and 650/1938 selected-fit prices outside bid/ask ranges",
        "parent_sha256":sha256(parent),"candidates":list(CANDIDATES),
        "limitation":"Reuses the primary folds and observations after seeing results; no independent performance claim or density truth",
        "selection":select_market(groups,candidates=CANDIDATES),"full_sample_fits":[]}
    for penalty in CANDIDATES:
        joint,carry=fit_market(groups,[g.pairs for g in groups],penalty)
        records=[marginal(g,f,c) for g,f,c in zip(groups,joint.fits,carry)]
        result["full_sample_fits"].append({"penalty":penalty,**fit_record(joint),"marginals":records})
        print(f'Post-hoc lambda={penalty:g}: {sum(m["outside_spread_count"] for m in records)} outside spreads.',flush=True)
    result["code_sha256"]={"run_marking_diagnostic.py":sha256(Path(__file__))}
    write(ROOT/"results/marking_range_diagnostic.json",result)
    print('Lower-grid scores:',[(c["penalty"],c["score"]) for c in result["selection"]["candidates"]],flush=True)
    return result


if __name__=="__main__":main()
