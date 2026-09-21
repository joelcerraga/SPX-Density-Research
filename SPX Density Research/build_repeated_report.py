"""Generate scientific figures, tables and narrative from accepted saved cases."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator
import numpy as np
from PIL import Image

from src.repeated import AMPLITUDES, BENCHMARKS, COVERAGES, NAMES, REPETITIONS, master_strikes, parameters

ROOT=Path(__file__).resolve().parent
NAVY,TEAL,ORANGE,GRAY='#16364c','#218a87','#c57b3c','#73858b'


def group(report,key,coverage,amplitude=.5):
    return next(g for g in report['groups'] if g['benchmark']==key and g['coverage']==coverage and g['amplitude']==amplitude)


def control(report,key,coverage):
    return next(c for c in report['clean_controls'] if c['spec']['benchmark']==key and c['spec']['coverage']==coverage)


def pair(report,key,left,right='original',amplitude=.5):
    return next(p for p in report['paired'] if p['benchmark']==key and p['left']==left and p['right']==right and p['amplitude']==amplitude)


def estimate(s,scale=1,decimals=4,signed=False):
    value=f'{s["mean"]*scale:+.{decimals}f}' if signed else f'{s["mean"]*scale:.{decimals}f}'
    uncertainty=f'{s["mcse"]*scale:.{decimals}f}'
    if s['mcse'] and float(uncertainty)==0:
        uncertainty=f'{s["mcse"]*scale:.2g}'
    return f'{value} ({uncertainty})'


def save(fig,number,name):
    for ext in ('png','svg'):
        destination=ROOT/f'figures/figure_{number:02}_{name}.{ext}'
        temporary=destination.with_name(destination.stem+'.tmp.'+ext)
        fig.savefig(temporary,dpi=180)
        if ext=='png':
            with Image.open(temporary) as rendered:rendered.verify()
        else:
            ET.parse(temporary)
        if temporary.stat().st_size==0:raise RuntimeError('Empty figure export.')
        temporary.replace(destination)
    plt.close(fig)


def figures(report,cases):
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    p=parameters()[-1];ratios=master_strikes(p)/p.forward
    fig,ax=plt.subplots(figsize=(10.5,4.1),constrained_layout=True)
    ax.axvspan(.3,2.2,color='#eaf0f1',label='Fixed density-fitting support')
    for y,(key,s) in enumerate(COVERAGES.items()):
        x=ratios[s['indices']]
        ax.plot([x[0],x[-1]],[y,y],color=NAVY,lw=1)
        ax.scatter(x,np.full(len(x),y),s=12,color=TEAL,zorder=3)
    for x,color,label in [(.8,NAVY,'0.8F'),(1.2,GRAY,'1.2F'),(1.8,ORANGE,'1.8F')]:
        ax.axvline(x,color=color,ls='--',lw=1,label=f'Tail threshold {label}')
    ax.set_yticks(range(4),[s['label'] for s in COVERAGES.values()]);ax.invert_yaxis()
    ax.set_xlim(.28,2.22);ax.set_xlabel('Strike / forward at 365 days (dimensionless)')
    ax.grid(axis='x',alpha=.15)
    fig.legend(*ax.get_legend_handles_labels(),loc='outside upper center',ncol=2,frameon=False,fontsize=9)
    save(fig,18,'quote_coverage_design')

    fig,axes=plt.subplots(2,2,figsize=(10.8,7.4),constrained_layout=True)
    y=np.arange(4)
    for row,key in enumerate(BENCHMARKS):
        for col,field in enumerate(['mean_full_density_l1','validation_rmse']):
            ax=axes[row,col]
            for a,offset,color in [(.1,-.12,TEAL),(.5,.12,ORANGE)]:
                stats=[group(report,key,c,a)['metrics'][field] for c in COVERAGES]
                ax.errorbar([s['mean'] for s in stats],y+offset,xerr=[2*s['mcse'] for s in stats],
                    fmt='o',ms=4.5,capsize=3,color=color,label=f'a = {a:g} points')
            ax.set_yticks(y,[s['label'] for s in COVERAGES.values()]);ax.invert_yaxis();ax.grid(axis='x',alpha=.18)
            ax.set_title(NAMES[key],fontsize=11)
            if col==0:
                ax.set_xlim(left=0);ax.set_xlabel('Mean full-domain density L1')
            else:
                ax.set_xscale('log');ax.set_xlabel('Mean validation-price RMSE (points; log scale)')
    fig.legend(*axes[0,0].get_legend_handles_labels(),loc='outside upper center',ncol=2,frameon=False)
    save(fig,19,'repeated_recovery_errors')

    fig,axes=plt.subplots(2,2,figsize=(10.8,7.6),constrained_layout=True)
    for row,key in enumerate(BENCHMARKS):
        for col,a in enumerate(AMPLITUDES):
            ax=axes[row,col]
            for y,coverage in enumerate(COVERAGES):
                selected=sorted([c for c in cases if c['spec']['benchmark']==key and c['spec']['coverage']==coverage
                                 and c['spec']['amplitude']==a],key=lambda c:c['spec']['repetition'])
                errors=np.array([100*(c['marginals'][-1]['risk']['above_1_8_forward']-
                                     c['marginals'][-1]['known_risk']['above_1_8_forward']) for c in selected])
                jitter=np.linspace(-.15,.15,len(errors))
                ax.scatter(errors,y+jitter,color=TEAL,s=9,alpha=.45,edgecolors='none')
                ax.errorbar(errors.mean(),y,xerr=errors.std(ddof=1),fmt='o',ms=4,color=NAVY,capsize=3,zorder=4)
                clean=control(report,key,coverage)['marginals'][-1]
                error=100*(clean['risk']['above_1_8_forward']-clean['known_risk']['above_1_8_forward'])
                ax.scatter([error],[y],color=ORANGE,marker='D',s=28,zorder=5)
            ax.axvline(0,color=GRAY,lw=.8);ax.set_yticks(range(4),[s['label'] for s in COVERAGES.values()])
            ax.invert_yaxis();ax.grid(axis='x',alpha=.18)
            ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
            ax.set_title(f'{NAMES[key]}; a = {a:g} points',fontsize=10)
            ax.set_xlabel('Error in P(S > 1.8F) (percentage points)')
    handles=[Line2D([],[],marker='o',color=TEAL,ls='',ms=4,label=f'Individual fit ({REPETITIONS} per row)'),
             Line2D([],[],marker='o',color=NAVY,lw=1,ms=4,label='Mean ± 1 empirical SD'),
             Line2D([],[],marker='D',color=ORANGE,ls='',ms=5,label='Clean-input control')]
    fig.legend(handles=handles,loc='outside upper center',ncol=3,frameon=False,fontsize=9)
    save(fig,20,'repeated_tail_errors')


def narrative(report):
    blocks={};p=parameters()[-1];grid=master_strikes(p)/p.forward
    lines=['Table 14. Quote patterns at 365 days. The same nested construction is used at every horizon. The fitting support remains [0.3, 2.2] in forward coordinates. Threshold entries indicate whether that strike is inside the quoted span.',
           '', '| Pattern | Quotes per horizon | Minimum K/F | Maximum K/F | 0.8F inside? | 1.2F inside? | 1.8F inside? |',
           '|---|---:|---:|---:|---|---|---|']
    for c,s in COVERAGES.items():
        k=grid[s['indices']];flags=['Yes' if k[0]<t<k[-1] else 'No' for t in [.8,1.2,1.8]]
        lines.append(f'| {s["label"]} | {len(k)} | {k[0]:.4f} | {k[-1]:.4f} | '+ ' | '.join(flags)+' |')
    blocks['DESIGN_TABLE']='\n'.join(lines)

    lines=[f'Table 15. Average recovery errors across {REPETITIONS} repetitions per scenario. Parentheses contain one Monte Carlo standard error of the mean. Each repetition aggregates eight horizons; the common validation grid contains 960 withheld clean prices. Density L1 is dimensionless and price RMSE is in index points.',
           '', '| Benchmark | Error limit a (points) | Quote pattern | Mean density L1 (MCSE) | Mean price RMSE (MCSE) |', '|---|---:|---|---:|---:|']
    for key in BENCHMARKS:
        for a in AMPLITUDES:
            for c,s in COVERAGES.items():
                g=group(report,key,c,a)['metrics']
                lines.append(f'| {NAMES[key]} | {a:g} | {s["label"]} | {estimate(g["mean_full_density_l1"])} | {estimate(g["validation_rmse"])} |')
    blocks['RESULTS_TABLE']='\n'.join(lines)

    truths=[100*group(report,k,'original')['risk_by_day'][-1]['above_1_8_forward']['truth'] for k in BENCHMARKS]
    lines=[f'Table 16. Error in the 365-day probability above 1.8F with a = 0.5 points. The known probabilities are {truths[0]:.4f}% (single lognormal) and {truths[1]:.4f}% (mixture). All errors and SDs are percentage points. The clean column uses exact input prices once, without a Monte Carlo error bar.',
           '', '| Benchmark | Pattern | Clean-input error | Mean error (MCSE) | Empirical SD | Root MSE |', '|---|---|---:|---:|---:|---:|']
    for key in BENCHMARKS:
        for c,s in COVERAGES.items():
            t=group(report,key,c)['risk_by_day'][-1]['above_1_8_forward'];z=control(report,key,c)['marginals'][-1]
            error=100*(z['risk']['above_1_8_forward']-z['known_risk']['above_1_8_forward'])
            clean_text=f'{error:+.4f}' if abs(error)>=.00005 or error==0 else f'{error:+.3g}'
            lines.append(f'| {NAMES[key]} | {s["label"]} | {clean_text} | {100*t["bias"]:+.4f} ({100*t["mcse"]:.4f}) | {100*t["sd"]:.4f} | {100*t["rmse"]:.4f} |')
    blocks['TAIL_TABLE']='\n'.join(lines)

    lines=['Table 17. Paired changes at a = 0.5 points, with one MCSE in parentheses. Each difference uses matched repetitions. Negative values mean a smaller error for the first pattern. The tail measure is mean absolute probability error at 365 days, in percentage points.',
           '', '| Benchmark | First pattern − second pattern | Change in density L1 | Change in mean absolute tail error (pp) |', '|---|---|---:|---:|']
    for key in BENCHMARKS:
        for left,right in [('sparse','original'),('central','original'),('extended','original'),('central','sparse')]:
            t=pair(report,key,left,right)
            lines.append(f'| {NAMES[key]} | {COVERAGES[left]["label"]} − {COVERAGES[right]["label"]} | {estimate(t["metrics"]["mean_full_density_l1"],signed=True)} | {estimate(t["tail_absolute_error_pp"],signed=True)} |')
    blocks['PAIRED_TABLE']='\n'.join(lines)

    parts=[]
    for key in BENCHMARKS:
        g=pair(report,key,'central','sparse')['metrics']['mean_full_density_l1']
        parts.append(f'For the {NAMES[key].lower()} benchmark at $a=0.5$, Central 41 minus Sparse 41 gives a mean density-error change '
                     f'of {g["mean"]:+.5f}, with MCSE {g["mcse"]:.5f}. Both patterns contain 41 quotes per horizon. '
                     'Their difference tests quote placement and range at a fixed count; it is not explained by deleting more observations from one than the other.')
    z=control(report,'mixture','central')['metrics']
    parts.append(f'With clean mixture prices, the Central 41 control has RMSE {z["within_quote_range_rmse"]:.4f} '
                 f'within its quoted span but {z["validation_rmse"]:.4f} over the common validation grid. '
                 'This discrepancy exists without random quote perturbations. The clean control still has finite-support, histogram and regularisation approximation errors; it is not an exact population-bias calculation.')
    blocks['RESULTS_COMMENTARY']='\n\n'.join(parts)
    parts=[]
    for key in BENCHMARKS:
        original=group(report,key,'original')['risk_by_day'][-1]['above_1_8_forward']
        extended=group(report,key,'extended')['risk_by_day'][-1]['above_1_8_forward']
        delta=pair(report,key,'extended')['tail_absolute_error_pp']
        parts.append(f'For the {NAMES[key].lower()} benchmark at $a=0.5$, the original pattern gives an average probability '
                     f'of {100*original["mean"]:.4f}% above $1.8F$, compared with the known {100*original["truth"]:.4f}%. '
                     f'The extended pattern gives {100*extended["mean"]:.4f}%. Its paired change in mean absolute error is '
                     f'{delta["mean"]:+.4f} percentage points (MCSE {delta["mcse"]:.4f}).')
    blocks['TAIL_COMMENTARY']='\n\n'.join(parts)
    c=report['checks']
    blocks['NUMERICAL_COMMENTARY']=(f'All {c["accepted"]} of {c["attempted"]} planned fits were accepted, covering '
        f'{c["accepted_marginals"]:,} marginal distributions. There were {c["failed"]} failed fits. The worst final calendar gap was '
        f'{c["minimum_calendar_gap"]:.3e}, inside the $10^{{-8}}$ acceptance tolerance. The maximum mass and normalised-mean residuals '
        f'across solver rounds were {c["maximum_mass_error"]:.3e} and {c["maximum_normalised_mean_error"]:.3e}; the minimum raw mass was '
        f'{c["minimum_raw_mass"]:.3e}. Raw signed residuals are retained. No probabilities or quotes were clipped or renormalised.\n\n'
        f'The largest residual-variable equality mismatch was {c["maximum_residual_equation_error"]:.3e}. '
        f'The most demanding solve used {c["maximum_solver_iterations"]} interior-point iterations, and at most '
        f'{c["maximum_refinement_rounds"]} calendar-refinement rounds were required. The maximum density-integration error estimate was '
        f'{c["maximum_quadrature_error_estimate"]:.3e}. These are numerical diagnostics, not exact arithmetic certificates.')
    return blocks


def main():
    report=json.loads((ROOT/'results/repeated_validation.json').read_text())
    if report['checks']['failed'] or not all(g['complete'] for g in report['groups']):
        raise RuntimeError('The planned study is incomplete; aggregate publication is withheld. Inspect the saved failures.')
    cases=[json.loads((ROOT/'results'/c['file']).read_text())['result'] for c in report['cases']]
    figures(report,cases)
    blocks=narrative(report)
    (ROOT/'results/repeated_tables.json').write_text(json.dumps(blocks,indent=2,ensure_ascii=False)+'\n')
    return report


if __name__=='__main__':main()
