"""Calculated Notebook 10 tables, comparisons and standalone scientific figures."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from build_repeated_report import save
from build_marking_report import table
from run_marking_calibration import write

ROOT=Path(__file__).resolve().parent
COLORS=['#16364c','#218a87','#c57b3c']
LABELS=['31 Aug · 15:00 CT','18 Sep · 15:00 CT','18 Sep · 15:15 CT']
EVENTS=['below_0_8_forward','above_1_2_forward','above_1_8_forward']


def main():
    r=json.loads((ROOT/'results/comparison_summary.json').read_text())
    cases={k:json.loads((ROOT/'results/comparison_cases'/(k+'.json')).read_text()) for k in r['case_ids']}
    old=json.loads((ROOT/'results/marking_calibration.json').read_text())
    oldfit=next(c for c in old['full_sample_fits'] if c['penalty']==old['selected_penalty'])
    snaps=r['snapshots'];edges=np.array(cases[snaps[0]['primary_case']]['edges_normalised']);width=np.diff(edges)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})

    fig,axes=plt.subplots(2,3,figsize=(12,7),constrained_layout=True)
    ratios=[q['midpoint_residual']/((q['ask']-q['bid'])/2) for m in oldfit['marginals'] for q in m['quote_residuals']]
    limits=(min(-1.3,min(ratios)-.4),max(1.3,max(ratios)+.4))
    for row,fit in enumerate((oldfit,cases['sep18_full'])):
        for col,m in enumerate(fit['marginals']):
            ax=axes[row,col]
            ax.axhspan(-1,1,color='#73858b',alpha=.13)
            for typ,color,marker in [('C',COLORS[1],'o'),('P',COLORS[2],'x')]:
                q=[a for a in m['quote_residuals'] if a['option_type']==typ]
                ax.scatter([a['strike']/m['forward'] for a in q],
                    [a['midpoint_residual']/((a['ask']-a['bid'])/2) for a in q],
                    s=8,alpha=.8,color=color,marker=marker,label='Calls' if typ=='C' else 'Puts')
            for y in (-1,1):ax.axhline(y,color='#73858b',lw=.7,ls='--')
            ax.axhline(0,color='#73858b',lw=.5);ax.set_ylim(limits if row==0 else (-1.2,1.2))
            ax.set_title(m['expiry']+' · '+('Notebook 9 primary' if row==0 else 'Original-spread constraints'),fontsize=10)
            ax.text(.03,.96,f"{m['outside_spread_count']} / {2*m['pair_count']} outside",va='top',transform=ax.transAxes,fontsize=9)
            ax.set_xlabel('Strike / inferred forward');ax.set_ylabel('Midpoint residual / half-spread');ax.grid(alpha=.12)
    axes[0,0].legend(frameon=False,fontsize=8,loc='lower left')
    save(fig,29,'original_spread_comparison')

    fig,axes=plt.subplots(2,3,figsize=(12,7.1),constrained_layout=True)
    for j in range(3):
        for i,s in enumerate(snaps):
            m=s['marginals'][j]
            for row in range(2):
                ax=axes[row,j];ax.stairs(np.array(m['mass'])/width,edges,color=COLORS[i],lw=1.25,
                    label=f'{LABELS[i]} · {m["elapsed_days"]:.2f} d')
                ax.set_xlim((.3,2.2) if row==0 else (.75,1.25));ax.grid(alpha=.12)
                ax.set_xlabel('Terminal level / own-date forward');ax.set_ylabel('Normalised density')
                ax.set_title(m['expiry']+' · '+('full support' if row==0 else 'central detail'),fontsize=10)
        axes[0,j].legend(frameon=False,fontsize=7.5,loc='upper right')
    save(fig,30,'fixed_expiry_date_comparison')

    fig,axes=plt.subplots(1,2,figsize=(11.3,4.5),constrained_layout=True,sharey=True)
    for j,key in enumerate(('common_60_days','matched_common_60_days')):
        for i,s in enumerate(snaps):axes[j].stairs(np.array(s[key]['mass'])/width,edges,color=COLORS[i],lw=1.5,label=LABELS[i])
        axes[j].set_xlim(.7,1.3);axes[j].grid(alpha=.12);axes[j].set_xlabel('Normalised terminal level')
        axes[j].set_title('All retained pairs' if j==0 else 'Common contracts; carry re-estimated',fontsize=11)
    axes[0].set_ylabel('Normalised density');axes[0].legend(frameon=False,fontsize=8)
    save(fig,31,'common_horizon_density')

    fig,axes=plt.subplots(1,3,figsize=(12,4.3),constrained_layout=True)
    titles=['Below 0.8 × forward','Above 1.2 × forward','Above 1.8 × forward']
    for ax,event,title in zip(axes,EVENTS,titles):
        for i,s in enumerate(snaps):
            q=next(q for q in s['risk_ranges'] if q['horizon']=='common_60_days' and q['event']==event)
            ax.plot(100*np.array([q['lower'],q['upper']]),[i,i],color=COLORS[i],lw=4,solid_capstyle='butt')
            ax.plot(100*q['point'],i,'o',color=COLORS[i],ms=8,mec='white',mew=1.2)
        ax.set_yticks(range(3),LABELS if event==EVENTS[0] else ['', '', '']);ax.invert_yaxis()
        ax.set_ylim(2.5,-.5);ax.set_title(title,fontsize=11);ax.set_xlabel('Conditional probability (%)');ax.grid(axis='x',alpha=.15)
    save(fig,32,'conditional_tail_ranges')

    fig=plt.figure(figsize=(14.4,4.9));centres=(edges[:-1]+edges[1:])/2
    zmax=max(max(np.array(m['mass'])/width) for s in snaps for m in s['marginals'])
    for i,s in enumerate(snaps):
        ax=fig.add_subplot(1,3,i+1,projection='3d');days=np.array([m['elapsed_days'] for m in s['marginals']])
        z=np.array([np.array(m['mass'])/width for m in s['marginals']]);X,Y=np.meshgrid(centres,days)
        ax.plot_surface(X,Y,z,cmap='viridis',vmin=0,vmax=zmax,linewidth=0,alpha=.88,rcount=3,ccount=len(centres))
        for t,line in zip(days,z):ax.plot(centres,np.full_like(centres,t),line,color=COLORS[i],lw=.7)
        ax.set_title(LABELS[i],fontsize=11,pad=10);ax.view_init(elev=27,azim=-66)
        ax.set_xlim(.3,2.2);ax.set_ylim(20,115);ax.set_zlim(0,zmax*1.05)
        ax.set_xlabel('Level / forward',labelpad=6,fontsize=9);ax.set_ylabel('Elapsed days',labelpad=7,fontsize=9)
        ax.set_zlabel('Density',labelpad=5,fontsize=9);ax.tick_params(labelsize=8,pad=0)
    fig.subplots_adjust(left=.005,right=.96,bottom=.10,top=.91,wspace=.06)
    save(fig,33,'dated_density_surfaces')

    coverage=[];feasible=[];fits=[];hold=[];points=[];ranges=[];changes=[]
    for label,s in zip(LABELS,snaps):
        full=cases[s['primary_case']];coarse=cases[s['coarse_case']]
        for m in s['marginals']:
            coverage.append([label,m['expiry'],m['pair_count'],r['common_strike_counts'][len(coverage)%3],
                f'{m["elapsed_days"]:.5f}',f'{m["discount"]:.8f}',f'{m["forward"]:.4f}'])
            fits.append([label,'240-bin constrained',m['expiry'],f'{m["call_midpoint_rmse"]:.4f}',f'{m["put_midpoint_rmse"]:.4f}',
                f'{m["call_outside_spread_count"]} / {m["put_outside_spread_count"]}',f'{m["maximum_spread_distance"]:.3g}'])
        for c in (coarse,full):
            attempts=c.get('numerical_attempts',[])
            feasible.append([label,len(c['edges_normalised'])-1,f'{c["feasibility"]["value"]:.9g}',
                'Solved' if c['status']=='solved' else 'Blocked on this grid',
                ', '.join(f'{a["quote_row_multiplier"]:g}: {a["status"]}' for a in attempts) or 'No QP attempted'])
        h=s['holdout_summary']
        hold.append([label,f'{h["successful_folds"]} / 3',h['held_quote_count'],h['outside_count'],
            f'{100*h["outside_count"]/h["held_quote_count"]:.3f}',f'{h["maximum_spread_distance"]:.6f}',f'{h["pooled_normalised_mse"]:.7g}'])
        for kind,key in [('All pairs','common_60_days'),('Common contracts','matched_common_60_days')]:
            p=s[key]['risk'];points.append([label,kind,*[f'{100*p[e]:.7f}' for e in EVENTS],f'{p["normalised_variance"]:.8f}'])
        for q in s['risk_ranges']:
            if q['horizon']=='common_60_days':ranges.append([label,titles[EVENTS.index(q['event'])],
                f'{100*q["point"]:.7f}',f'{100*q["lower"]:.7f}',f'{100*q["upper"]:.7f}'])
    for name,c in [('Notebook 9 primary',oldfit),('120-bin constrained',cases['sep18_coarse'])]:
        for m in c['marginals']:fits.append([LABELS[1],name,m['expiry'],f'{m["call_midpoint_rmse"]:.4f}',f'{m["put_midpoint_rmse"]:.4f}',
            f'{m["call_outside_spread_count"]} / {m["put_outside_spread_count"]}',f'{m["maximum_spread_distance"]:.6f}'])
    for a,b in [(0,1),(1,2)]:
        left,right=snaps[a],snaps[b]
        changes.append({'from':left['id'],'to':right['id'],
            'fixed_expiry_l1':[float(np.sum(np.abs(np.array(x['mass'])-y['mass']))) for x,y in zip(left['marginals'],right['marginals'])],
            'common_60_l1':float(np.sum(np.abs(np.array(left['common_60_days']['mass'])-right['common_60_days']['mass']))),
            'matched_common_60_l1':float(np.sum(np.abs(np.array(left['matched_common_60_days']['mass'])-right['matched_common_60_days']['mass'])))})
    attempts=[a for c in cases.values() for a in c.get('numerical_attempts',[])]
    metrics={'date_changes':changes,'primary_spread_quote_count':sum(2*m['pair_count'] for s in snaps for m in s['marginals']),
        'primary_outside_count':sum(m['outside_spread_count'] for s in snaps for m in s['marginals']),
        'nonaccepted_numerical_attempts':sum(a['status']!='solved' for a in attempts),
        'residual_plot_old_ylim':list(limits),'residual_plot_new_ylim':[-1.2,1.2]}
    output={
        'COVERAGE_TABLE':table(['Snapshot (2026)','Expiry','Retained pairs','Common strikes','Elapsed days','Inferred D','Inferred F (points)'],coverage),
        'FEASIBILITY_TABLE':table(['Snapshot','Bins','Minimum widening (points)','Final outcome','Equivalent quote-row multiplier: status'],feasible),
        'FIT_TABLE':table(['Snapshot','Estimator','Expiry','Call RMSE (points)','Put RMSE (points)','Calls / puts outside','Largest miss (points)'],fits),
        'HOLDOUT_TABLE':table(['Snapshot','Solved folds','Evaluated quotes','Outside spreads','Outside (%)','Largest miss (points)','Pooled normalised MSE'],hold),
        'POINT_TABLE':table(['Snapshot','Pairs used','Below 0.8 (%)','Above 1.2 (%)','Above 1.8 (%)','Normalised variance'],points),
        'RANGE_TABLE':table(['Snapshot','60-day event','Chosen estimate (%)','Feasible lower (%)','Feasible upper (%)'],ranges),
        'CHANGE_SUMMARY':f'The August-to-September common-60-day density distance in Equation (46) is {changes[0]["common_60_l1"]:.6f}; '
            f'the common-contract control gives {changes[0]["matched_common_60_l1"]:.6f}. Across the two September snapshots these distances are '
            f'{changes[1]["common_60_l1"]:.6f} and {changes[1]["matched_common_60_l1"]:.6f}. '
            'They measure differences between fitted normalised distributions, not estimation errors or statistical significance.',
        'NUMERICAL_SUMMARY':f'{r["case_accounting"]["solved_qp_cases"]} of {r["case_accounting"]["attempted_cases"]} attempted QP cases were accepted '
            f'({r["case_accounting"]["marginal_fits"]} marginal fits). The late 120-bin control was blocked by the feasibility check; '
            'the first late-snapshot holdout fold failed the declared numerical acceptance rule. '
            f'All accepted fits passed the probability and full-interval calendar checks. The smallest final calendar gap was '
            f'{r["validation"]["minimum_final_calendar_gap"]:.4g}; the largest accepted training-spread miss was '
            f'{r["validation"]["maximum_accepted_training_spread_miss"]:.4g} index points, below the counting tolerance of $10^{{-7}}$. '
            f'The smallest signed mass was {r["validation"]["minimum_mass"]:.4g}, retained without clipping. '
            'Seventy-two tail-extremum LPs completed; their independent physical-price residual limit was $2\\times10^{-6}$ points.'}
    write(ROOT/'results/comparison_report_tables.json',output);write(ROOT/'results/comparison_display_metrics.json',metrics)
    print('Generated Figures 29–33, Tables 31–36 and dated comparison metrics.')
    return output


if __name__=='__main__':main()
