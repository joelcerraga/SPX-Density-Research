"""Cboe exchange-BBO snapshots and quote-implied carry estimation.

This explicitly separate profile does not label marking sizes as live depth,
exchange BBO as NBBO, or inferred discounts as an independently observed curve.
The external-discount profile in src/empirical.py is unchanged.
"""
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
import csv
import re
from zoneinfo import ZoneInfo

import clarabel
import numpy as np
from scipy import sparse
from scipy.optimize import linprog

from src.empirical import Pair, parity_interval, sha256, timestamp, year_fraction
from src.joint import fit_maturities
from src.repeated import EDGES
from src.selection import CANDIDATES, choose_penalty, fit_record, folds, pooled_score

PROFILES = {
    "eom_marking_prices_list.csv": {"date":"2026-08-31","time_ct":"15:00:00","role":"reserved_date_comparison"},
    "eod_marking_prices_list.csv": {"date":"2026-09-18","time_ct":"15:00:00","role":"primary_calibration"},
    "eod_marking_prices_late_list.csv": {"date":"2026-09-18","time_ct":"15:15:00","role":"reserved_intraday_comparison"},
}
EXPIRIES = ("2026-10-16", "2026-11-20", "2026-12-18")
MAX_SPREAD = .25
MAX_AGE_SECONDS = 60.
MARKING_SOURCE = "https://www.cboe.com/markets/us/options/market-statistics/product-data/proprietary-index-marking-prices"
OSI = re.compile(r"^(SPXW?)\s+(\d{6})([CP])(\d{8})$")


@dataclass(frozen=True)
class MarketGroup:
    expiry: str
    observed_at: str
    settlement_at: str
    maturity: float
    pairs: tuple


def snapshot_time(profile):
    return datetime.fromisoformat(profile["date"]+"T"+profile["time_ct"]).replace(
        tzinfo=ZoneInfo("America/Chicago")).isoformat()


def audit_file(path, max_age_seconds=MAX_AGE_SECONDS):
    profile=PROFILES[path.name]
    snapshot=snapshot_time(profile);asof=timestamp(snapshot)
    with path.open(newline="") as stream:raw=list(csv.DictReader(stream))
    target=[(i,r) for i,r in enumerate(raw,2) if r["root"] in ("SPX","SPXW")]
    keys=Counter((r["root"],r["expiry"],r["strike"]) for _,r in target)
    audit=[];groups=defaultdict(list);changed=Counter();size_values=Counter();zero_sequence=Counter()
    time_ages=[];date_counts=Counter();price_counts=Counter();recent_counts=Counter()
    for line,row in target:
        reasons=[];sides={};ages=[];metadata_errors=[]
        if keys[(row["root"],row["expiry"],row["strike"])]!=1:reasons.append("duplicate_pair")
        try:
            strike=float(row["strike"])
            if not np.isfinite(strike) or strike<=0:raise ValueError("invalid strike")
            datetime.strptime(row["expiry"],"%Y-%m-%d")
            if row["underlying_symbol"]!="^SPX":raise ValueError("unexpected underlying")
            for side,typ in (("call","C"),("put","P")):
                ident=OSI.fullmatch(row[f"{side}_osi_identifier"].strip())
                if (ident is None or ident[1]!=row["root"] or ident[2]!=row["expiry"].replace("-","")[2:]
                        or ident[3]!=typ or abs(int(ident[4])/1000-strike)>1e-9):
                    raise ValueError("OSI identifier disagrees with contract columns")
                t=timestamp(row[f"{side}_message_time"].replace(" ","T",1))
                if t>asof or t.astimezone(ZoneInfo("America/New_York")).date().isoformat()!=profile["date"]:
                    raise ValueError("message outside declared snapshot day or after snapshot")
                age=(asof-t).total_seconds();ages.append(age);time_ages.append(age)
                date_counts[row[f"{side}_message_time"][:10]]+=1
                b,a=[float(row[f"{side}_last_disseminated_market_{s}"]) for s in ("bid","ask")]
                ib,ia=[float(row[f"{side}_final_indicative_{s}"]) for s in ("bid","ask")]
                changed[side]+=int(b!=ib or a!=ia)
                for s in ("bid","ask"):size_values[row[f"{side}_final_indicative_{s}_size"]]+=1
                zero_sequence[side]+=int(row[f"{side}_sequence_number"]=="0")
                if not np.isfinite(b) or not np.isfinite(a):reasons.append(f"{side}_nonfinite_price")
                elif b<=0 or a<=0:reasons.append(f"{side}_nonpositive_price")
                elif b>a:reasons.append(f"{side}_crossed_quote")
                elif (a-b)/((a+b)/2)>MAX_SPREAD:reasons.append(f"{side}_wide_spread")
                sides[typ]={"quote_id":f"{path.name}:{line}:{typ}","osi":row[f"{side}_osi_identifier"],
                    "bid":b,"ask":a,"bid_size":None,"ask_size":None,
                    "message_at":t.isoformat(),"message_age_seconds":age,
                    "indicative_bid":ib,"indicative_ask":ia}
        except (ValueError,KeyError,TypeError) as error:
            reasons.append("invalid_metadata");metadata_errors.append(str(error))
        price_pass=not reasons
        if price_pass:price_counts[row["root"]]+=1
        if ages and max(ages)>max_age_seconds:reasons.append("message_age_exceeds_limit")
        recent_pass=not reasons
        if recent_pass:recent_counts[row["root"]]+=1
        selected=row["root"]=="SPXW" and row["expiry"] in EXPIRIES
        if not selected:reasons.append("outside_primary_contract_scope")
        audit.append({"csv_row":line,"root":row["root"],"expiry":row["expiry"],"strike":row["strike"],
            "price_screen_pass":price_pass,"price_and_age_pass":recent_pass,"selected_contract":selected,
            "retained_for_primary_scope":not reasons,"reasons":reasons,"metadata_errors":metadata_errors,
            "maximum_message_age_seconds":max(ages) if ages else None})
        if not reasons:groups[row["expiry"]].append(Pair(strike,sides["C"],sides["P"]))
    market_groups=[]
    for expiry in EXPIRIES:
        # Only these explicitly reviewed, full-session 2026 dates are supported.
        settlement=datetime.fromisoformat(expiry+"T16:00:00").replace(tzinfo=ZoneInfo("America/New_York")).isoformat()
        pairs=tuple(sorted(groups[expiry],key=lambda p:p.strike))
        market_groups.append(MarketGroup(expiry,snapshot,settlement,year_fraction(snapshot,settlement),pairs))
    report={"file":path.name,"sha256":sha256(path),"profile":profile,"snapshot_at":snapshot,
        "source_page":MARKING_SOURCE,"total_rows":len(raw),"spx_pair_rows":len(target),
        "spx_root_counts":dict(Counter(r["root"] for _,r in target)),
        "root_expiry_groups":len({(r["root"],r["expiry"]) for _,r in target}),
        "price_screen_pairs_by_root":dict(price_counts),"price_and_age_pairs_by_root":dict(recent_counts),
        "indicative_different_from_market":dict(changed),"indicative_size_values":dict(size_values),
        "zero_sequence_counts":dict(zero_sequence),"message_date_counts":dict(date_counts),
        "message_age_seconds":{"minimum":min(time_ages) if time_ages else None,
                               "maximum":max(time_ages) if time_ages else None},
        "retained_pairs":sum(len(g.pairs) for g in market_groups),
        "selected_expiries":list(EXPIRIES),"maximum_relative_spread":MAX_SPREAD,
        "maximum_message_age_seconds":max_age_seconds,"row_audit":audit,
        "metadata_failure_rows":sum("invalid_metadata" in a["reasons"] for a in audit),
        "quote_basis":"Actual Cboe exchange BBO at the documented snapshot, not indicative marks or an asserted consolidated NBBO",
        "size_policy":"Actual market depth unavailable. Indicative size fields are not reused or used as liquidity evidence."}
    return market_groups,report


def infer_carry(pairs):
    """Constrained least squares for C-P = H-D*K; D and H are quote-derived.

    Coordinates are centred/scaled for conditioning. The LP projects the same
    bid–ask feasible set onto D; it is not a statistical confidence interval.
    """
    if len(pairs)<3:raise ValueError("At least three matched pairs required.")
    k=np.array([p.strike for p in pairs]);anchor=float(np.median(k))
    if np.any(np.diff(k)<=0) or not np.all(np.isfinite(k)) or anchor<=0:
        raise ValueError("Sorted distinct positive strikes required.")
    lower=np.array([p.call["bid"]-p.put["ask"] for p in pairs])/anchor
    upper=np.array([p.call["ask"]-p.put["bid"] for p in pairs])/anchor
    if not np.all(np.isfinite(np.r_[lower,upper])) or np.any(lower>upper):
        raise ValueError("Ordered finite pair bounds required.")
    y=(lower+upper)/2
    X=np.column_stack([np.ones(len(k)),-(k-anchor)/anchor])
    # beta[0] = (H - D*anchor)/anchor; beta[1] = D.
    A=np.vstack([X,-X,[-1.,-1.]])
    b=np.r_[upper,-lower,-1e-8]
    bounds=[(None,None),(1e-8,None)]
    minimum=linprog([0.,1.],A_ub=A,b_ub=b,bounds=bounds,method="highs")
    maximum=linprog([0.,-1.],A_ub=A,b_ub=b,bounds=bounds,method="highs")
    if not minimum.success or not maximum.success:
        raise ValueError(f"Carry set is empty or unbounded: LP statuses {minimum.status}, {maximum.status}.")
    beta=np.linalg.lstsq(X,y,rcond=None)[0]
    method="Feasible unconstrained least-squares solution"
    iterations=0
    def violation(coef):
        pred=X@coef
        return max(float(np.max(lower-pred)),float(np.max(pred-upper)),1e-8-coef[1],1e-8-coef.sum(),0.)
    if violation(beta)>1e-10/anchor:
        # Two-variable convex QP; retain strict solver acceptance.
        matrix=np.vstack([A,[0.,-1.]])
        rhs=np.r_[b,-1e-8]
        scale=1e6
        P=sparse.csc_matrix(2*scale*(X.T@X)/len(k));q=-2*scale*(X.T@y)/len(k)
        settings=clarabel.DefaultSettings();settings.verbose=False;settings.max_iter=200
        settings.tol_gap_abs=1e-10;settings.tol_gap_rel=1e-10;settings.tol_feas=1e-10
        settings.max_threads=1
        solution=clarabel.DefaultSolver(P,q,sparse.csc_matrix(matrix),rhs,
            [clarabel.NonnegativeConeT(len(rhs))],settings).solve()
        if str(solution.status)!="Solved":raise RuntimeError(f"Carry QP failed: {solution.status}")
        beta=np.asarray(solution.x);iterations=solution.iterations;method="Constrained least squares, Clarabel"
    deficit=violation(beta)*anchor
    if deficit>1e-7:raise RuntimeError(f"Carry solution violates pair bounds by {deficit} points.")
    discount=float(beta[1]);forward=float(anchor*(1+beta[0]/discount));H=forward*discount
    conditional=parity_interval(pairs,discount)
    if not conditional["feasible"] or forward<conditional["lower"]-1e-7 or forward>conditional["upper"]+1e-7:
        raise RuntimeError("Inferred forward does not pass the independent pair-interval check.")
    residual=(X@beta-y)*anchor
    return {"discount":discount,"forward":forward,"discounted_forward":H,"anchor":anchor,
        "discount_feasible_interval":[float(minimum.x[1]),float(maximum.x[1])],
        "conditional_forward_interval":conditional,"method":method,"iterations":iterations,
        "parity_midpoint_rmse":float(np.sqrt(np.mean(residual**2))),
        "parity_midpoint_residuals":residual.tolist(),"maximum_interval_violation_points":deficit,
        "pair_count":len(pairs),"interpretation":"Quote-implied carry proxy; feasible intervals are not confidence intervals or an independent yield curve."}


def fit_market(groups,pairs_by_group,penalty,fitter=fit_maturities):
    carry=[infer_carry(pairs) for pairs in pairs_by_group]
    joint=fitter([np.array([p.strike for p in pairs]) for pairs in pairs_by_group],
        [np.array([p.call_mid for p in pairs]) for pairs in pairs_by_group],
        [c["forward"] for c in carry],[c["discount"] for c in carry],[g.maturity for g in groups],EDGES,
        penalty=penalty,max_solver_iterations=200,residual_form=True,solver_backend="clarabel")
    return joint,carry


def select_market(groups,candidates=CANDIDATES,fitter=fit_maturities):
    partition=[folds(len(g.pairs)) for g in groups]
    candidates_out=[]
    for penalty in candidates:
        records=[]
        for fi in range(3):
            train=[tuple(g.pairs[i] for i in p[fi][0]) for g,p in zip(groups,partition)]
            joint,carry=fit_market(groups,train,penalty,fitter)
            errors=[];members=[]
            for g,p,fit,c in zip(groups,partition,joint.fits,carry):
                tr,held=p[fi]
                residual=(fit.prices(np.array([g.pairs[i].strike for i in held]))
                          -np.array([g.pairs[i].call_mid for i in held]))/c["forward"]
                errors.extend(residual.tolist())
                members.append({"expiry":g.expiry,"train_indices":tr.tolist(),"held_indices":held.tolist(),
                    "carry":c,"normalised_residuals":residual.tolist()})
            records.append({"fold":fi,"groups":members,"count":len(errors),
                "squared_error_sum":float(np.dot(errors,errors)),**fit_record(joint)})
        score=pooled_score([r["squared_error_sum"] for r in records],[r["count"] for r in records])
        candidates_out.append({"penalty":float(penalty),"score":score,"folds":records})
    selected=choose_penalty([(c["penalty"],c["score"]) for c in candidates_out])
    return {"selected_penalty":selected,"candidates":candidates_out,
        "boundary_selected":selected in (min(candidates),max(candidates)),
        "scope":"Three interlaced interior pair holdouts. BOTH discount and forward re-estimated exclusively from training pairs. Endpoints retained."}


def residuals(group,fit):
    records=[]
    for p,c in zip(group.pairs,fit.prices(np.array([p.strike for p in group.pairs]))):
        for typ,row,v in (("C",p.call,c),("P",p.put,c-fit.discount*(fit.forward-p.strike))):
            records.append({"quote_id":row["quote_id"],"osi":row["osi"],"option_type":typ,"strike":p.strike,
                "bid":row["bid"],"ask":row["ask"],"fitted":float(v),
                "midpoint_residual":float(v-(row["bid"]+row["ask"])/2),
                "distance_outside_spread":float(max(row["bid"]-v,v-row["ask"],0.)),
                "message_age_seconds":row["message_age_seconds"]})
    return records
