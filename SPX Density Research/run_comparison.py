"""Notebook 10: spread-constrained fits, conditional risk ranges and dated views."""
from dataclasses import replace
import json
from pathlib import Path
import platform
import time

import clarabel
import numpy as np
import scipy

from run_marking_calibration import marginal,write
from src.comparison import (EDGES,PRICE_TOL,LP_PRICE_TOL,make_problem,fit_spreads,
    linear_extreme,tail_coefficients,common_horizon,interpolation_weights)
from src.empirical import sha256
from src.marking import audit_file,residuals
from src.selection import folds

ROOT=Path(__file__).resolve().parent
SNAPSHOTS=[('aug31','eom_marking_prices_list.csv','31 August · 15:00 CT'),
    ('sep18','eod_marking_prices_list.csv','18 September · 15:00 CT'),
    ('sep18_late','eod_marking_prices_late_list.csv','18 September · 15:15 CT')]
EVENTS=[('below_0_8_forward',.8,False),('above_1_2_forward',1.2,True),('above_1_8_forward',1.8,True)]
CASES=ROOT/'results/comparison_cases'


def solve_case(groups,edges,case_id,role):
    p=make_problem(groups,edges)
    feas=linear_extreme(p,allow_widening=True)
    case={'case_id':case_id,'role':role,'pair_counts':[len(g.pairs) for g in groups],
          'edges_normalised':edges.tolist(),'carry':p.carry,'feasibility':feas}
    if feas['status']!='solved' or feas['value']>PRICE_TOL:
        case.update(status='blocked_by_spread_feasibility',reason='Original quote bounds cannot be met on this grid at the declared point tolerance.')
        write(CASES/(case_id+'.json'),case);return case,p
    attempts=[]
    for row_scale in (1.,10.,100.):
        fit=fit_spreads(p,quote_row_multiplier=row_scale)
        attempts.append({'quote_row_multiplier':row_scale,**{k:v for k,v in fit.items() if k not in ('_fits','weights','carry','edges_normalised')}})
        if fit['status']=='solved':break
    objects=fit.pop('_fits',None);case.update(fit)
    case['numerical_attempts']=attempts
    if case['status']=='solved':
        case['marginals']=[marginal(g,f,c) for g,f,c in zip(groups,objects,p.carry)]
        case['common_60_days']=common_horizon(groups,case['weights'],edges)
    write(CASES/(case_id+'.json'),case)
    return case,p


def holdout_case(groups,index,case_id):
    partitions=[folds(len(g.pairs))[index] for g in groups]
    train=[replace(g,pairs=tuple(g.pairs[i] for i in parts[0])) for g,parts in zip(groups,partitions)]
    case,p=solve_case(train,EDGES,case_id,'Descriptive paired-strike holdout; not smoothing selection or temporal prediction')
    case['membership']=[{'expiry':g.expiry,'train_indices':tr.tolist(),'held_indices':held.tolist()} for g,(tr,held) in zip(groups,partitions)]
    if case['status']=='solved':
        from src.constrained import DensityFit
        evaluation=[]
        for g,m,(tr,held) in zip(groups,case['marginals'],partitions):
            held_group=replace(g,pairs=tuple(g.pairs[i] for i in held))
            fit=DensityFit(np.array(m['edges']),np.array(m['mass']),m['discount'],m['forward'],0,0,0.)
            rows=residuals(held_group,fit)
            evaluation.append({'expiry':g.expiry,'quote_residuals':rows,
                'squared_normalised_error_sum':sum((r['midpoint_residual']/fit.forward)**2 for r in rows),
                'quote_count':len(rows),'outside_count':sum(r['distance_outside_spread']>PRICE_TOL for r in rows),
                'maximum_spread_distance':max(r['distance_outside_spread'] for r in rows)})
        case['held_out']=evaluation
    write(CASES/(case_id+'.json'),case);return case


def risk_ranges(p,point_case,snapshot_id):
    result=[]
    coefficients=[]
    for m,g in enumerate(p.groups):
        mix=np.zeros(p.M);mix[m]=1;coefficients.append((g.expiry,mix,np.array(point_case['weights'])[m]))
    coefficients.append(('common_60_days',interpolation_weights(p.groups),np.array(point_case['common_60_days']['mass'])))
    for horizon,mix,mass in coefficients:
        for event,threshold,upper in EVENTS:
            a=tail_coefficients(p.edges,threshold,upper);objective=np.outer(mix,a)
            lower=linear_extreme(p,objective);higher=linear_extreme(p,objective,maximise=True)
            if lower['status']!='solved' or higher['status']!='solved':
                raise RuntimeError(f'Unsolved risk bound: {snapshot_id}, {horizon}, {event}')
            point=float(mass@a)
            if lower['value']>point+1e-8 or higher['value']<point-1e-8 or lower['value']>higher['value']+1e-8:
                raise RuntimeError('Point estimate does not belong to its numerical feasible risk range.')
            result.append({'horizon':horizon,'event':event,'threshold':threshold,'upper_event':upper,
                'maturity_weights':mix.tolist(),'point':point,'lower':lower['value'],'upper':higher['value'],
                'minimisation':lower,'maximisation':higher})
        print(f'{snapshot_id}: risk ranges completed for {horizon}.',flush=True)
        write(CASES/(snapshot_id+'_risk_ranges.json'),{'scope':'Conditional feasible ranges, not confidence intervals',
            'point_fit_case':point_case['case_id'],'rows':result})
    return result


def main():
    started=time.monotonic();CASES.mkdir(exist_ok=True)
    for name,digest in json.loads((ROOT/'results/milestone10_preserved_sha256.json').read_text()).items():
        if sha256(ROOT/name)!=digest:raise RuntimeError(f'Preservation mismatch: {name}')
    verified=json.loads((ROOT/'data/raw/marking_prices/source_verification.json').read_text())
    for v in verified:
        if sha256(ROOT/'data/raw/marking_prices'/v['filename'])!=v['uploaded_sha256']:raise RuntimeError('Input checksum mismatch')
    protocol={'status':'Fixed after the documented feasibility and numerical-formulation pilots',
        'snapshots':[{'id':a,'file':b,'label':c} for a,b,c in SNAPSHOTS],
        'density_grid':{'bins':240,'support':[.3,2.2]},'coarse_control_bins':120,
        'carry':'Unchanged Equation (39), separately inferred per snapshot, scope and training fold',
        'estimator':'Minimum discrete curvature inside original matched call/put bounds; nonnegative mass, unit mean and mass; analytical calendar refinement',
        'smoothing_parameter':'None: curvature is minimised subject to hard quote constraints',
        'numerical_formulation':'Explicit roughness residuals, price inequality rows divided by each inferred forward; strict Clarabel Solved status',
        'stopping_tolerance':1e-11,'price_count_tolerance_points':PRICE_TOL,'lp_price_residual_tolerance_points':LP_PRICE_TOL,
        'numerical_retry_rule':'Try equivalent positive quote-row multipliers 1, 10, 100 only if strict solver or independent post-solve checks fail; retain all attempts, never widen quotes',
        'calendar_tolerance':1e-8,'common_horizon_days':60.,
        'common_horizon_rule':'Linear mixture in elapsed time of adjacent normalised maturity densities; never extrapolate',
        'common_contract_control':'Within each expiry, intersection of retained strikes across all three snapshots; re-estimate carry and refit',
        'holdouts':'Three interlaced interior-pair folds per snapshot; endpoints always retained; D and F estimated only on training pairs',
        'tail_ranges':'Linear extrema over the 240-bin, original-spread-feasible family with the full-sample fixed carry; no roughness restriction',
        'events':[{'name':x,'threshold':y,'upper':z} for x,y,z in EVENTS],
        'limits':['All snapshots were inspected during feasibility design; no blind or temporal performance claim.',
            'Common-horizon values require interpolation, and normalised tail events are relative to the relevant forward.',
            'No true market density, external curve, actual depth, carry-uncertainty band or executable-arbitrage conclusion.',
            'No cross-observation-date calendar constraint. The within-snapshot maturity constraints remain conditional on deterministic carry/proportional dividends.'],
        'pilot_files':{n:sha256(ROOT/'results'/n) for n in ['comparison_feasibility_pilot.json','comparison_qp_pilot.json','comparison_qp_scaling_pilot.json','comparison_normalised_qp_pilot.json']}}
    write(ROOT/'results/comparison_protocol.json',protocol)
    inputs={};audits=[]
    for key,name,label in SNAPSHOTS:
        groups,audit=audit_file(ROOT/'data/raw/marking_prices'/name)
        if audit['metadata_failure_rows']:raise RuntimeError('Input metadata failure')
        inputs[key]=groups;audits.append({k:v for k,v in audit.items() if k!='row_audit'})
    common=[set.intersection(*[{pair.strike for pair in inputs[key][i].pairs} for key,_,_ in SNAPSHOTS]) for i in range(3)]
    result={'snapshots':[],'common_strike_counts':[len(v) for v in common],
        'common_strikes':[sorted(v) for v in common],'audit_summary':audits,'case_ids':[],
        'parent_milestone9_sha256':sha256(ROOT/'results/marking_calibration.json')}
    write(ROOT/'results/comparison_inputs.json',{'audit_summary':audits,'common_strikes':result['common_strikes']})
    for key,name,label in SNAPSHOTS:
        groups=inputs[key]
        point,p=solve_case(groups,EDGES,key+'_full','Primary all-retained-pair constrained fit')
        result['case_ids'].append(point['case_id'])
        if point['status']!='solved':raise RuntimeError(f'Primary fit blocked: {key}: {point}')
        print(f'{key}: full fit, {sum(len(g.pairs) for g in groups)} pairs; max spread miss {point["constraint_summary"]["maximum_spread_distance_points"]:.3g}.',flush=True)
        coarse,_=solve_case(groups,np.linspace(.3,2.2,121),key+'_coarse','120-bin representation control')
        result['case_ids'].append(coarse['case_id'])
        matched_groups=[replace(g,pairs=tuple(pair for pair in g.pairs if pair.strike in common[i])) for i,g in enumerate(groups)]
        matched,_=solve_case(matched_groups,EDGES,key+'_matched','Common-contract sensitivity control')
        result['case_ids'].append(matched['case_id'])
        print(f'{key}: coarse={coarse["status"]}; common-contract fit={matched["status"]}.',flush=True)
        holdouts=[]
        for fi in range(3):
            case=holdout_case(groups,fi,f'{key}_fold{fi}');result['case_ids'].append(case['case_id']);holdouts.append(case)
            print(f'{key}: paired holdout {fi+1}: {case["status"]}.',flush=True)
        ranges=risk_ranges(p,point,key)
        usable=[h for h in holdouts if h['status']=='solved']
        evaluated=[e for h in usable for e in h['held_out']]
        held_summary={'successful_folds':len(usable),'attempted_folds':3,
            'held_quote_count':sum(e['quote_count'] for e in evaluated),'outside_count':sum(e['outside_count'] for e in evaluated),
            'maximum_spread_distance':max((e['maximum_spread_distance'] for e in evaluated),default=None),
            'pooled_normalised_mse':sum(e['squared_normalised_error_sum'] for e in evaluated)/sum(e['quote_count'] for e in evaluated) if evaluated else None}
        snapshot={'id':key,'file':name,'label':label,'observed_at':groups[0].observed_at,
            'primary_case':point['case_id'],'coarse_case':coarse['case_id'],'matched_case':matched['case_id'],
            'holdout_cases':[h['case_id'] for h in holdouts],'holdout_summary':held_summary,
            'marginals':point['marginals'],'common_60_days':point['common_60_days'],
            'matched_common_60_days':matched.get('common_60_days'),
            'risk_ranges':[{k:v for k,v in r.items() if k not in ('minimisation','maximisation')} for r in ranges]}
        result['snapshots'].append(snapshot)
        write(ROOT/'results/comparison_summary.json',result)
    cases=[json.loads((CASES/(name+'.json')).read_text()) for name in result['case_ids']]
    solved=[c for c in cases if c['status']=='solved'];histories=[h for c in solved for h in c['history']]
    result['case_accounting']={'attempted_cases':len(cases),'solved_qp_cases':len(solved),
        'marginal_fits':3*len(solved),'blocked_cases':[{'case_id':c['case_id'],'status':c['status'],'reason':c.get('reason',c.get('solver_status'))} for c in cases if c['status']!='solved'],
        'risk_extreme_lp_count':sum(2*len(s['risk_ranges']) for s in result['snapshots'])}
    result['validation']={'all_accepted_qp_statuses_solved':all(h['status']=='Solved' for h in histories),
        'all_accepted_calendar_checks_pass':all(c['calendar']['passes'] for c in solved),
        'minimum_final_calendar_gap':min(c['calendar']['minimum_gap'] for c in solved),
        'maximum_mass_error':max(h['maximum_mass_error'] for h in histories),
        'maximum_mean_error':max(h['maximum_mean_error'] for h in histories),
        'minimum_mass':min(h['minimum_mass'] for h in histories),
        'maximum_accepted_training_spread_miss':max(h['maximum_spread_distance_points'] for h in histories),
        'maximum_auxiliary_residual':max(h['maximum_residual_equation_error'] for h in histories)}
    result['elapsed_seconds']=time.monotonic()-started
    result['protocol_sha256']=sha256(ROOT/'results/comparison_protocol.json')
    result['input_sha256']={name:sha256(ROOT/'data/raw/marking_prices'/name) for _,name,_ in SNAPSHOTS}
    result['code_sha256']={name:sha256(ROOT/name) for name in ['src/comparison.py','src/marking.py','src/joint.py','src/constrained.py','run_comparison.py']}
    result['environment']={'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'clarabel':clarabel.__version__}
    write(ROOT/'results/comparison_summary.json',result)
    print('Completed:',result['case_accounting'],flush=True)
    return result


if __name__=='__main__':main()
