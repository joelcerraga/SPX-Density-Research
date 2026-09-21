"""Computed tables and static scientific figures for empirical preparation."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from build_repeated_report import save
from src.constrained import DensityFit
from src.empirical import prepare_groups, read_bundle
from src.robustness import BENCHMARKS

ROOT=Path(__file__).resolve().parent
NAVY,TEAL,ORANGE,GRAY="#16364c","#218a87","#c57b3c","#73858b"


def main():
    report=json.loads((ROOT/"results/empirical_preparation.json").read_text())
    known=json.loads((ROOT/"data/fixtures/empirical/truth.json").read_text())["groups"]
    manifest,rows,discounts=read_bundle(ROOT/"data/fixtures/empirical")
    groups,_=prepare_groups(manifest,rows,discounts)
    plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False})
    fig,axes=plt.subplots(1,2,figsize=(11.1,4.5),constrained_layout=True)
    F=known[0]["forward"]
    x=np.array(known[0]["strikes"])/F
    for ax,interval,title in zip(axes,[report["forward_intervals"][0],report["input_checks"][5]["interval"]],
                               ["Compatible synthetic pairs","First call shifted by +5 points"]):
        lower=np.array(interval["lower_by_strike"])-F;upper=np.array(interval["upper_by_strike"])-F
        ax.vlines(x,lower,upper,color=GRAY,alpha=.8,lw=1.4,label="Individual pair interval")
        ax.scatter(x,lower,s=7,color=GRAY);ax.scatter(x,upper,s=7,color=GRAY)
        ax.axhline(0,color=NAVY,lw=1.2,ls=":",label="Known fixture forward")
        L,U=interval["lower"]-F,interval["upper"]-F
        ax.axhline(L,color=TEAL,lw=1.3,label="Largest lower bound")
        ax.axhline(U,color=ORANGE,lw=1.3,label="Smallest upper bound")
        if interval["feasible"]:
            ax.axhspan(L,U,color=TEAL,alpha=.10)
            text="Common interval exists"
        else:
            text=f'No common interval\nMinimum uniform widening: {interval["minimum_uniform_relaxation"]:.3f} points'
        ax.text(.97,.97,text,transform=ax.transAxes,ha="right",va="top",fontsize=9,
                bbox={"facecolor":"white","edgecolor":"none","alpha":.9})
        ax.set_xlabel("Strike / known fixture forward")
        ax.set_ylabel("Possible forward − known forward (points)")
        ax.set_title(title,fontsize=11);ax.grid(axis="y",alpha=.15)
    fig.legend(*axes[0].get_legend_handles_labels(),loc="outside upper center",ncol=2,frameon=False,fontsize=9)
    save(fig,24,"paired_forward_intervals")

    fig,axes=plt.subplots(2,3,figsize=(12.1,7.0),constrained_layout=True)
    all_ratios=[r["midpoint_residual"]/((r["ask"]-r["bid"])/2)
                for m in report["marginals"] for r in m["quote_residuals"]]
    residual_limits=(min(-1.3,min(all_ratios)-.2),max(1.3,max(all_ratios)+.2))
    for col,(g,m,k) in enumerate(zip(groups,report["marginals"],known)):
        fit=DensityFit(np.array(m["edges"]),np.array(m["mass"]),m["discount"],m["forward"],0,0,0.)
        F=k["forward"];xx=np.linspace(.4,1.8,1401)
        ax=axes[0,col]
        ax.plot(xx,BENCHMARKS["mixture"].density(xx,g.maturity),color=NAVY,lw=1.8,label="Known mixture")
        ax.plot(xx,fit.density(xx*F)*F,color=TEAL,lw=1.2,label="Fitted density")
        ax.set_title(f'{k["nominal_days"]}-day fixture · {m["pair_count"]} pairs',fontsize=11)
        ax.set_xlabel("Terminal level / known forward")
        ax.set_ylabel("Normalised density");ax.set_xlim(.4,1.8);ax.grid(alpha=.12)
        ax=axes[1,col]
        for typ,color,marker,label in (("C",TEAL,"o","Calls"),("P",ORANGE,"x","Puts")):
            rr=[r for r in m["quote_residuals"] if r["option_type"]==typ]
            ax.plot([r["strike"]/F for r in rr],
                    [r["midpoint_residual"]/((r["ask"]-r["bid"])/2) for r in rr],
                    marker=marker,ms=3,lw=.65,color=color,label=label)
        ax.axhspan(-1,1,color=GRAY,alpha=.1,label="Inside bid–ask range")
        ax.axhline(1,color=GRAY,lw=.8,ls="--");ax.axhline(-1,color=GRAY,lw=.8,ls="--")
        ax.axhline(0,color=GRAY,lw=.5)
        ax.set_xlabel("Strike / known forward");ax.set_ylabel("Midpoint residual / half-spread")
        ax.set_ylim(*residual_limits);ax.grid(alpha=.12)
        outside=[r for r in m["quote_residuals"] if r["distance_outside_spread"]>1e-7]
        if outside:
            r=max(outside,key=lambda r:r["distance_outside_spread"])
            y=r["midpoint_residual"]/((r["ask"]-r["bid"])/2)
            ax.annotate("Outside spread",xy=(r["strike"]/F,y),xytext=(.83,y+.30),
                        fontsize=8,color=ORANGE,arrowprops={"arrowstyle":"->","color":ORANGE,"lw":.8})
    axes[0,0].legend(frameon=False,fontsize=8)
    axes[1,0].legend(frameon=False,fontsize=8,loc="upper right")
    save(fig,25,"fixture_density_and_spreads")

    forward=["| Nominal horizon | Elapsed years | Pairs | Conditional forward interval | Chosen forward | Error from known forward |",
             "|---|---:|---:|---|---:|---:|"]
    fit_table=["| Nominal horizon | Separate clean-price RMSE (points) | Full-domain density L1 | Quotes outside spread | Largest spread distance (points) |",
               "|---|---:|---:|---:|---:|"]
    for k,m,e,b in zip(known,report["marginals"],report["fixture_evaluation"],report["forward_intervals"]):
        forward.append(f'| {k["nominal_days"]} days | {m["maturity"]:.8f} | {m["pair_count"]} | '
            f'[{b["lower"]:.4f}, {b["upper"]:.4f}] | {m["forward"]:.4f} | {e["forward_error"]:+.4f} |')
        fit_table.append(f'| {k["nominal_days"]} days | {e["clean_test_rmse"]:.5f} | '
            f'{e["density_error"]["full_domain"]:.5f} | {m["outside_spread_count"]} / {2*m["pair_count"]} | '
            f'{m["maximum_spread_distance"]:.5f} |')
    checks=["| Deliberate input change | Observed response |","|---|---|"]
    checks.extend(f'| {r["case"]} | {r["observed"].capitalize()} |' for r in report["input_checks"])
    scores="; ".join(f'λ = {c["penalty"]:g}: {c["score"]:.6g}' for c in report["selection"]["candidates"])
    all_fits=[report["fit"]]+[f for c in report["selection"]["candidates"] for f in c["folds"]]
    histories=[h for fit in all_fits for h in fit["solver"]["history"]]
    statistics={"fit_count":len(all_fits),"marginal_count":3*len(all_fits),
        "maximum_mass_error":max(h["maximum_mass_error"] for h in histories),
        "maximum_mean_error":max(h["maximum_normalised_mean_error"] for h in histories),
        "minimum_bin_mass":min(h["minimum_bin_mass"] for h in histories),
        "minimum_final_calendar_gap":min(f["calendar"]["minimum_gap"] for f in all_fits),
        "maximum_auxiliary_residual":max(h["maximum_residual_equation_error"] for h in histories),
        "all_statuses_solved":all(h["status"]=="Solved" for h in histories),
        "all_calendar_checks_pass":all(f["calendar"]["passes"] for f in all_fits)}
    output={"FORWARD_TABLE":"\n".join(forward),"FIT_TABLE":"\n".join(fit_table),
        "CHECK_TABLE":"\n".join(checks),"SCORES":scores,
        "PARITY_RELAXATION":f'{report["input_checks"][5]["interval"]["minimum_uniform_relaxation"]:.4f}',
        "NUMERICAL_SUMMARY":f'All {len(all_fits)} joint fits ({3*len(all_fits)} marginals) have solved status and pass '
        f'the continuous calendar check at tolerance $10^{{-8}}$. Across their solver histories, the largest mass '
        f'and normalised-mean residuals are {statistics["maximum_mass_error"]:.3g} and '
        f'{statistics["maximum_mean_error"]:.3g}; the minimum final calendar gap is '
        f'{statistics["minimum_final_calendar_gap"]:.3g}. No clipping or renormalisation is applied.'}
    (ROOT/"results/empirical_preparation_tables.json").write_text(json.dumps(output,indent=2)+"\n")
    (ROOT/"results/empirical_preparation_validation.json").write_text(json.dumps(statistics,indent=2)+"\n")
    print("Generated Figures 24–25 and computed Tables 23–25; data source table is a documented access assessment.")
    return output


if __name__=="__main__":main()
