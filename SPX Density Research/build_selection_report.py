"""Create Milestone 8 tables and verified scientific figure exports."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from build_repeated_report import save
from src.constrained import DensityFit
from src.repeated import (BENCHMARKS,COVERAGES,EDGES,NAMES,master_strikes,
                          paired_summary,parameters,scalar_summary)
from src.selection import CANDIDATES,PATTERNS,SHIFTS

ROOT=Path(__file__).resolve().parent
NAVY,TEAL,ORANGE,GRAY='#16364c','#218a87','#c57b3c','#73858b'


def estimate(s,scale=1,decimals=4,signed=False):
    value=f'{s["mean"]*scale:+.{decimals}f}' if signed else f'{s["mean"]*scale:.{decimals}f}'
    mcse=s['mcse']*scale
    uncertainty=f'{mcse:.{decimals}f}'
    if mcse and float(uncertainty)==0:uncertainty=f'{mcse:.2g}'
    return f'{value} ({uncertainty})'


def group(report,key,coverage):
    return next(g for g in report['groups'] if g['benchmark']==key and g['coverage']==coverage)


def stress(report,key,shift):
    return next(g for g in report['forward_groups'] if g['benchmark']==key and g['shift']==shift)


def figures(report):
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(10.2,4.0),constrained_layout=True)
    for ax,key in zip(axes,BENCHMARKS):
        for pattern,offset,color in [('original',-.035,NAVY),('extended',.035,TEAL)]:
            stats=[group(report,key,pattern)['candidate_scores'][str(p)] for p in CANDIDATES]
            ax.errorbar(np.arange(3)+offset,[s['mean']*1e9 for s in stats],
                        yerr=[2*s['mcse']*1e9 for s in stats],fmt='o-',ms=4,capsize=3,
                        color=color,label=COVERAGES[pattern]['label'])
        ax.set_xticks(range(3),[r'$10^{-7}$',r'$10^{-6}$',r'$10^{-5}$'])
        ax.set_xlabel('Smoothing coefficient, λ');ax.set_title(NAMES[key],fontsize=11)
        ax.set_ylabel('Mean noisy validation MSE × 10⁹');ax.set_yscale('log')
        ax.grid(axis='y',alpha=.18,which='both')
    fig.legend(*axes[0].get_legend_handles_labels(),loc='outside upper center',ncol=2,frameon=False)
    save(fig,21,'smoothing_selection_scores')

    fig,axes=plt.subplots(1,2,figsize=(10.8,4.8),constrained_layout=True)
    combos=[(key,c) for key in BENCHMARKS for c in PATTERNS]
    labels=[('Lognormal' if k=='lognormal' else 'Mixture')+' · '+COVERAGES[c]['label'] for k,c in combos]
    for ax,field,xlabel in zip(axes,['validation_rmse','mean_full_density_l1'],
                               ['Mean clean-price RMSE (index points)','Mean full-domain density L1']):
        for method,offset,color,label in [('fixed',-.12,GRAY,'Fixed λ = 10⁻⁶'),('selected',.12,TEAL,'Selected λ')]:
            stats=[group(report,k,c)[method]['metrics'][field] for k,c in combos]
            ax.errorbar([s['mean'] for s in stats],np.arange(4)+offset,
                        xerr=[2*s['mcse'] for s in stats],fmt='o',ms=5,capsize=3,color=color,label=label)
        ax.set_yticks(range(4),labels);ax.invert_yaxis();ax.set_xlim(left=0)
        ax.set_xlabel(xlabel);ax.grid(axis='x',alpha=.2)
    fig.legend(*axes[0].get_legend_handles_labels(),loc='outside upper center',ncol=2,frameon=False)
    save(fig,22,'selected_and_fixed_recovery')

    fig,axes=plt.subplots(2,3,figsize=(12.2,7.7),constrained_layout=True)
    x=100*np.array(SHIFTS)
    for row,key in enumerate(BENCHMARKS):
        for col,(field,label) in enumerate([('validation_rmse','Mean clean-price RMSE (points)'),
                                           ('mean_full_density_l1','Mean full-domain density L1'),
                                           ('tail_error_pp','365-day upper-tail bias (pp)')]):
            ax=axes[row,col]
            stats=[stress(report,key,s)['metrics'][field] for s in SHIFTS]
            ax.errorbar(x,[s['mean'] for s in stats],yerr=[2*s['mcse'] for s in stats],
                        fmt='o-',color=TEAL if row==0 else NAVY,capsize=3,ms=4)
            ax.axvline(0,color=GRAY,ls=':',lw=1)
            if col==2:ax.axhline(0,color=GRAY,ls='--',lw=1)
            if col==0:ax.set_yscale('log')
            ax.set_xticks(x,['−0.5','−0.1','0','+0.1','+0.5'])
            ax.set_xlabel('Supplied forward error (%)');ax.set_ylabel(label)
            ax.set_title(NAMES[key],fontsize=11);ax.grid(axis='y',alpha=.18)
    save(fig,23,'forward_input_sensitivity')


def tables(report):
    counts=['| Benchmark | Strike pattern | Selected 10⁻⁷ | Selected 10⁻⁶ | Selected 10⁻⁵ |',
            '|---|---|---:|---:|---:|']
    performance=['| Benchmark | Pattern | Rule | Clean-price RMSE (points) | Full-density L1 | 365-day upper-tail bias (pp) |',
                 '|---|---|---|---:|---:|---:|']
    contrasts=['| Benchmark | Pattern | Δ clean-price RMSE (points) | Δ full-density L1 | Δ absolute upper-tail error (pp) |',
               '|---|---|---:|---:|---:|']
    for key in BENCHMARKS:
        for pattern in PATTERNS:
            g=group(report,key,pattern);prefix=f'| {NAMES[key]} | {COVERAGES[pattern]["label"]} |'
            counts.append(prefix+' '+' | '.join(str(g['selection_counts'][str(p)]) for p in CANDIDATES)+' |')
            for method,label in [('fixed','Fixed 10⁻⁶'),('selected','Selected')]:
                m=g[method]['metrics']
                performance.append(prefix+f' {label} | '+estimate(m['validation_rmse'])+' | '+
                    estimate(m['mean_full_density_l1'])+' | '+estimate(m['tail_error_pp'],signed=True)+' |')
            p=g['paired_selected_minus_fixed']
            contrasts.append(prefix+' '+' | '.join(estimate(p[field],signed=True) for field in
                 ('validation_rmse','mean_full_density_l1','tail_absolute_error_pp'))+' |')
    forward=['| Benchmark | Forward error (%) | Clean-price RMSE (points) | Full-density L1 | Upper-tail bias (pp) | Quotes below lower bound / 968 |',
             '|---|---:|---:|---:|---:|---:|']
    for key in BENCHMARKS:
        for shift in SHIFTS:
            g=stress(report,key,shift);m=g['metrics']
            forward.append(f'| {NAMES[key]} | {100*shift:+.1f} | '+estimate(m['validation_rmse'])+' | '+
                estimate(m['mean_full_density_l1'])+' | '+estimate(m['tail_error_pp'],signed=True)+' | '+
                estimate(g['lower_bound']['count'],decimals=2)+' |')
    return {'SELECTION_TABLE':'\n'.join(counts),'PERFORMANCE_TABLE':'\n'.join(performance),
            'PAIRED_TABLE':'\n'.join(contrasts),'FORWARD_TABLE':'\n'.join(forward)}


def range_diagnostic(report):
    """Post-hoc attribution by quote range, without changing selection or fits."""
    from run_selection import fixed_fit
    cases=[json.loads((ROOT/'results'/item['file']).read_text())['result'] for item in report['cases']
           if item['id'].startswith('mixture_original_')]
    rows=[]
    for c in sorted(cases,key=lambda c:c['spec']['repetition']):
        row={'repetition':c['spec']['repetition']}
        for name,record in [('selected',c['selected']),('fixed',fixed_fit(c))]:
            inside=[];outside=[]
            for m,p in enumerate(parameters()):
                k=master_strikes(p);test=(k[:-1]+k[1:])/2
                fit=DensityFit(EDGES*p.forward,np.array(record['weights'][m]),float(np.exp(-p.rate*p.maturity)),p.forward,record['penalty'],0,0)
                error=fit.prices(test)-BENCHMARKS['mixture'].prices(test,p)
                inside.extend(error[20:100]);outside.extend(np.r_[error[:20],error[100:]])
            row[name]={'within_quote_range_rmse':float(np.sqrt(np.mean(np.array(inside)**2))),
                       'outside_quote_range_rmse':float(np.sqrt(np.mean(np.array(outside)**2)))}
        rows.append(row)
    result={'purpose':'Post-hoc diagnostic of the observed selection/evaluation discrepancy; no change to selector, grid or primary evaluation measures',
        'benchmark':'mixture','coverage':'original','inside_price_count':640,'outside_price_count':320,
        'repetitions':rows,'groups':{name:{field:scalar_summary([r[name][field] for r in rows])
                     for field in rows[0][name]} for name in ['selected','fixed']},
        'paired':{field:paired_summary([r['selected'][field] for r in rows],[r['fixed'][field] for r in rows])
                  for field in rows[0]['selected']}}
    (ROOT/'results/selection_range_diagnostic.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def commentary(report,diagnostic):
    total=sum(g['attempted'] for g in report['groups'])
    frequencies=[sum(g['selection_counts'][str(p)] for g in report['groups']) for p in CANDIDATES]
    selection=(f'Across {total} selection experiments, the three candidates were chosen '
               f'{frequencies[0]}, {frequencies[1]} and {frequencies[2]} times, respectively. '
               f'The lower candidate was selected in {frequencies[0]} experiments; those choices '
               'establish only a preference within the declared grid. The grid was not extended after '
               'examining evaluation results. Table 18 also retains cases where the rule simply confirms the baseline.')
    recovery=[]
    for pattern in PATTERNS:
        g=group(report,'mixture',pattern);a,b=g['selected']['metrics'],g['fixed']['metrics']
        delta=g['paired_selected_minus_fixed']['mean_full_density_l1']
        recovery.append(f'For the mixture under {COVERAGES[pattern]["label"]}, mean clean-price RMSE changes '
            f'from {b["validation_rmse"]["mean"]:.4f} to {a["validation_rmse"]["mean"]:.4f} points, '
            f'while mean full-density error changes from {b["mean_full_density_l1"]["mean"]:.4f} '
            f'to {a["mean_full_density_l1"]["mean"]:.4f}. The paired density-error change is '
            f'{delta["mean"]:+.4f} (MCSE {delta["mcse"]:.4f}).')
    recovery.append('These comparisons concern this selection rule and these benchmark families. '
                    'They do not establish that the smallest price-validation score minimises density or tail error. '
                    'The signed and absolute tail comparisons in Tables 19–20 must be read separately.')
    a,b=diagnostic['groups']['selected'],diagnostic['groups']['fixed']
    recovery.append('A **post-hoc range diagnostic**, added after the Original 81 mixture discrepancy was observed, '
        f'locates the price deterioration. At the 640 clean test strikes inside the observed range, mean RMSE '
        f'changes from {b["within_quote_range_rmse"]["mean"]:.4f} to {a["within_quote_range_rmse"]["mean"]:.4f} points; '
        f'at the 320 outside it, the error changes from {b["outside_quote_range_rmse"]["mean"]:.4f} '
        f'to {a["outside_quote_range_rmse"]["mean"]:.4f} points. The paired outside-range change is '
        f'{diagnostic["paired"]["outside_quote_range_rmse"]["mean"]:+.4f} '
        f'(MCSE {diagnostic["paired"]["outside_quote_range_rmse"]["mcse"]:.4f}). '
        'Thus improved interior interpolation accompanies worse extrapolation on the declared common grid. '
        'This diagnostic reuses the saved fits and changes neither the chosen coefficients nor the primary measures. '
        'It is an explanation of the observed result, not a newly tuned performance claim.')
    positive,negative,zero=[stress(report,'mixture',s) for s in (.005,-.005,0)]
    forward=(f'For the mixture, mean clean-price RMSE is {zero["metrics"]["validation_rmse"]["mean"]:.4f} points '
             f'at the correct forward, {negative["metrics"]["validation_rmse"]["mean"]:.4f} at −0.5%, '
             f'and {positive["metrics"]["validation_rmse"]["mean"]:.4f} at +0.5%. '
             f'The positive stress puts an average of {positive["lower_bound"]["count"]["mean"]:.1f} '
             'of the 968 observed quotes below the supplied-forward lower bound. This diagnostic '
             'helps explain the asymmetric price response, but does not separate every effect of changing the forward. '
             'All five stress levels retain the same physical tail event; an apparent change cannot be attributed '
             'to silently moving the threshold. A tail metric can improve at one stress level while the overall '
             'density or price fit deteriorates, so it is not used alone to validate the supplied forward.')
    c=report['checks']
    numeric=(f'The completed study records {c["recorded_experiments"]} planned experiments: 80 smoothing selections '
             'and 160 nonzero forward stresses. Zero-shift results reuse the corresponding selected fits. '
             f'There are **{c["unique_accepted_joint_fits"]:,} unique accepted joint fits and '
             f'{c["accepted_marginals"]:,} marginal densities**, including the 720 training-only CV fits; '
             f'{c["reused_fixed_fits"]} fixed-control fits are reused. There are '
             f'{c["failed_or_blocked"]} failed or blocked experiments. The worst final calendar gap is '
             f'{c["minimum_calendar_gap"]:.3e}, within the $10^{{-8}}$ acceptance tolerance. '
             f'At most {c["maximum_refinement_rounds"]} refinement rounds and '
             f'{c["maximum_solver_iterations"]} solver iterations per round were needed. '
             f'The minimum raw mass across all solver rounds is {c["minimum_raw_mass"]:.3e}; '
             'small signed numerical residuals are retained. No probability clipping or renormalisation is used. '
             f'The largest density-quadrature refinement estimate is '
             f'{c["maximum_quadrature_error_estimate"]:.3e}. Successive-rule agreement is a numerical check, '
             'not a rigorous error bound.')
    return {'SELECTION_COMMENT':selection,'RECOVERY_COMMENT':'\n\n'.join(recovery),
            'FORWARD_COMMENT':forward,'NUMERICAL_COMMENT':numeric}


def main():
    report=json.loads((ROOT/'results/selection_validation.json').read_text())
    if report['checks']['failed_or_blocked'] or not all(g['complete'] for g in report['groups']+report['forward_groups']):
        raise RuntimeError('The planned study is incomplete; no success-only report will be produced.')
    figures(report)
    diagnostic=range_diagnostic(report)
    (ROOT/'results/selection_tables.json').write_text(json.dumps({**tables(report),**commentary(report,diagnostic)},indent=2)+'\n')
    print('Generated Figures 21–23 and Tables 18–21 from the complete saved study.')


if __name__=='__main__':main()
