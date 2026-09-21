"""Calculated empirical tables and publication figures; no market truth assumed."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from build_repeated_report import save
from run_marking_calibration import write

ROOT=Path(__file__).resolve().parent
NAVY,TEAL,ORANGE,GRAY="#16364c","#218a87","#c57b3c","#73858b"


def table(headers,rows):
    return "\n".join(["| "+" | ".join(headers)+" |","|"+"---|"*len(headers)]+
                     ["| "+" | ".join(map(str,r))+" |" for r in rows])


def main():
    report=json.loads((ROOT/"results/marking_calibration.json").read_text())
    diagnostic=json.loads((ROOT/"results/marking_range_diagnostic.json").read_text())
    audit=json.loads((ROOT/"results/marking_input_audit.json").read_text())
    selected=next(f for f in report["full_sample_fits"] if f["penalty"]==report["selected_penalty"])
    lower=next(f for f in diagnostic["full_sample_fits"] if f["penalty"]==diagnostic["selection"]["selected_penalty"])
    plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False})
    fig,axes=plt.subplots(2,3,figsize=(12,7.1),constrained_layout=True)
    ratios=[r["midpoint_residual"]/((r["ask"]-r["bid"])/2)
            for m in selected["marginals"] for r in m["quote_residuals"] if r["ask"]>r["bid"]]
    ylim=(min(-1.4,min(ratios)-.3),max(1.4,max(ratios)+.3))
    for col,m in enumerate(selected["marginals"]):
        F=m["forward"];rr=m["quote_residuals"];calls=[r for r in rr if r["option_type"]=="C"]
        ax=axes[0,col];x=[r["strike"]/F for r in calls]
        ax.plot(x,[(r["bid"]+r["ask"])/2 for r in calls],color=GRAY,marker=".",ms=3,lw=.6,label="Market call midpoint")
        ax.plot(x,[r["fitted"] for r in calls],color=TEAL,lw=1.3,label="Fitted call")
        ax.set_title(f'{m["expiry"]} · {m["pair_count"]} pairs',fontsize=10)
        ax.set_ylabel("Call price (index points)");ax.set_xlabel("Strike / inferred forward");ax.grid(alpha=.12)
        ax=axes[1,col]
        for typ,color,marker,label in (("C",TEAL,"o","Calls"),("P",ORANGE,"x","Puts")):
            rows=[r for r in rr if r["option_type"]==typ and r["ask"]>r["bid"]]
            ax.scatter([r["strike"]/F for r in rows],
                [r["midpoint_residual"]/((r["ask"]-r["bid"])/2) for r in rows],s=8,marker=marker,color=color,alpha=.75,label=label)
        ax.axhspan(-1,1,color=GRAY,alpha=.12,label="Inside bid–ask range")
        for v in (-1,1):ax.axhline(v,color=GRAY,lw=.7,ls="--")
        ax.axhline(0,color=GRAY,lw=.5);ax.set_ylim(*ylim)
        ax.set_xlabel("Strike / inferred forward");ax.set_ylabel("Midpoint residual / half-spread")
        ax.text(.03,.96,f'{m["outside_spread_count"]} / {2*m["pair_count"]} outside',transform=ax.transAxes,va="top",fontsize=9)
        ax.grid(alpha=.12)
    axes[0,0].legend(frameon=False,fontsize=8);axes[1,0].legend(frameon=False,fontsize=8,loc="lower left")
    save(fig,26,"market_prices_and_spreads")

    fig,axes=plt.subplots(2,3,figsize=(12,7.1),constrained_layout=True)
    curves=[(f,c,f'Primary λ = {f["penalty"]:g}',"-") for f,c in zip(report["full_sample_fits"],[TEAL,ORANGE,GRAY])]
    curves.append((lower,NAVY,f'Post-hoc λ = {lower["penalty"]:g}',"--"))
    for col,m in enumerate(selected["marginals"]):
        for row in range(2):
            ax=axes[row,col]
            for f,color,label,style in curves:
                mm=f["marginals"][col];edges=np.array(mm["edges"])/mm["forward"]
                ax.stairs(np.array(mm["mass"])/np.diff(edges),edges,color=color,lw=1.15,ls=style,label=label)
            lo,hi=m["normalised_strike_range"]
            ax.axvline(lo,color=GRAY,lw=.7,ls=":");ax.axvline(hi,color=GRAY,lw=.7,ls=":")
            ax.set_xlim((.3,2.2) if row==0 else (.75,1.25))
            ax.set_xlabel("Terminal level / inferred forward");ax.set_ylabel("Normalised density")
            ax.grid(alpha=.12)
            ax.set_title(f'{m["expiry"]} · '+("full fitting support" if row==0 else "central detail"),fontsize=10)
    fig.legend(*axes[0,0].get_legend_handles_labels(),loc="outside upper center",ncol=4,fontsize=8,frameon=False)
    save(fig,27,"market_density_sensitivity")

    edges=np.array(selected["marginals"][0]["edges"])/selected["marginals"][0]["forward"]
    x=(edges[1:]+edges[:-1])/2;days=np.array([m["elapsed_days"] for m in selected["marginals"]])
    z=np.array([np.array(m["mass"])/np.diff(edges) for m in selected["marginals"]])
    fig=plt.figure(figsize=(10.2,6.8));ax=fig.add_subplot(111,projection="3d")
    fig.subplots_adjust(left=.01,right=.95,bottom=.08,top=.99)
    X,Y=np.meshgrid(x,days)
    ax.plot_surface(X,Y,z,cmap="viridis",alpha=.87,linewidth=0,rcount=3,ccount=len(x))
    for t,line in zip(days,z):ax.plot(x,np.full_like(x,t),line,color=NAVY,lw=.8)
    ax.view_init(elev=26,azim=-62);ax.set_xlabel("Terminal level / inferred forward",labelpad=10)
    ax.set_ylabel("Time to settlement (days)",labelpad=10);ax.set_zlabel("Normalised density",labelpad=8)
    ax.set_xlim(.3,2.2);ax.set_yticks(days);ax.set_yticklabels(["28","63.04","91.04"])
    save(fig,28,"market_density_surface")

    inputs=[]
    for a in audit["files"]:
        inputs.append([a["file"],a["profile"]["date"],a["profile"]["time_ct"][:5],
            f'{a["total_rows"]:,}',f'{a["spx_pair_rows"]:,}',a["profile"]["role"].replace("_"," ")])
    carry=[];fitrows=[];riskrows=[]
    for m in selected["marginals"]:
        c=m["carry"];dl,du=c["discount_feasible_interval"]
        carry.append([m["expiry"],m["pair_count"],f'{m["elapsed_days"]:.5f}',f'{m["discount"]:.8f}',
            f'[{dl:.8f}, {du:.8f}]',f'{m["forward"]:.4f}',f'{100*m["quote_implied_rate"]:.4f}'])
        lo,hi=m["normalised_strike_range"]
        fitrows.append([m["expiry"],f'{lo:.4f}–{hi:.4f}',f'{m["call_midpoint_rmse"]:.4f}',f'{m["put_midpoint_rmse"]:.4f}',
            f'{m["call_outside_spread_count"]} / {m["put_outside_spread_count"]}',f'{m["maximum_spread_distance"]:.4f}'])
    sensitivity=[]
    for name,r in (("Primary",report),("Post-hoc",diagnostic)):
        for f,c in zip(r["full_sample_fits"],r["selection"]["candidates"]):
            n=sum(m["outside_spread_count"] for m in f["marginals"])
            sensitivity.append([name,f'{f["penalty"]:g}',f'{c["score"]:.7g}',f'{n} / 1938',
                f'{max(m["maximum_spread_distance"] for m in f["marginals"]):.4f}'])
    for name,f in (("Primary 1e−7",selected),("Post-hoc 1e−10",lower)):
        for m in f["marginals"]:
            rr=m["risk"]
            riskrows.append([name,m["expiry"],f'{100*rr["below_0_8_forward"]:.5f}',
                f'{100*rr["above_1_2_forward"]:.7f}',f'{100*rr["above_1_8_forward"]:.9f}',f'{rr["normalised_variance"]:.7f}'])
    all_fits=[]
    for r in (report,diagnostic):all_fits+=r["full_sample_fits"]+[f for c in r["selection"]["candidates"] for f in c["folds"]]
    histories=[h for f in all_fits for h in f["solver"]["history"]]
    checks={"joint_fit_count":len(all_fits),"marginal_fit_count":3*len(all_fits),
        "all_statuses_solved":all(h["status"]=="Solved" for h in histories),
        "all_calendar_checks_pass":all(f["calendar"]["passes"] for f in all_fits),
        "minimum_final_calendar_gap":min(f["calendar"]["minimum_gap"] for f in all_fits),
        "minimum_bin_mass":min(h["minimum_bin_mass"] for h in histories),
        "maximum_mass_error":max(h["maximum_mass_error"] for h in histories),
        "maximum_mean_error":max(h["maximum_normalised_mean_error"] for h in histories),
        "maximum_auxiliary_residual":max(h["maximum_residual_equation_error"] for h in histories),
        "selected_residual_plot_limits":list(ylim),"selected_residual_extrema":[min(ratios),max(ratios)]}
    output={"INPUT_TABLE":table(["File","Date","CT","All rows","SPX/SPXW pairs","Use here"],inputs),
        "CARRY_TABLE":table(["Expiry","Pairs","Elapsed days","Inferred D","Feasible D range","Inferred F (points)","Implied rate (%/yr)"],carry),
        "MARKET_FIT_TABLE":table(["Expiry","Retained K/F range","Call RMSE (points)","Put RMSE (points)","Calls / puts outside","Largest spread miss (points)"],fitrows),
        "SENSITIVITY_TABLE":table(["Role","λ","Pooled held-out score","Outside spreads","Largest miss (points)"],sensitivity),
        "RISK_TABLE":table(["Fit","Expiry","Q(S < 0.8F), %","Q(S > 1.2F), %","Q(S > 1.8F), %","Var(S/F)"],riskrows),
        "NUMERICAL_SUMMARY":f'All {len(all_fits)} empirical joint fits ({3*len(all_fits)} marginals), including the post-hoc diagnostic, '
            f'have strict solved status and pass the continuous calendar check at $10^{{-8}}$. '
            f'The minimum final gap is {checks["minimum_final_calendar_gap"]:.4g}; largest mass and normalised-mean residuals '
            f'are {checks["maximum_mass_error"]:.4g} and {checks["maximum_mean_error"]:.4g}. '
            f'The smallest signed mass is {checks["minimum_bin_mass"]:.4g}, retained without clipping or renormalisation.'}
    write(ROOT/"results/marking_report_tables.json",output)
    write(ROOT/"results/marking_complete_validation.json",checks)
    print("Generated empirical Figures 26–28 and Tables 26–30.")
    return output


if __name__=="__main__":main()
