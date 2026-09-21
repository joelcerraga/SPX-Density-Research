"""Independent checks for spread feasibility, curvature fitting and dated comparisons."""
import json
from pathlib import Path
from dataclasses import replace
import unittest
import numpy as np

from src.constrained import DensityFit,payoff_matrix
from src.comparison import (make_problem,fit_spreads,linear_extreme,tail_coefficients,
    interpolation_weights,common_horizon,PRICE_TOL)
from src.empirical import Pair,sha256
from src.marking import MarketGroup,audit_file,infer_carry
from src.joint import continuous_calendar_check

ROOT=Path(__file__).resolve().parents[1]


def uniform_groups(width=.1):
    edges=np.linspace(.5,1.5,7);mass=np.full(6,1/6);groups=[]
    for d,t in ((.98,.1),(.95,.3)):
        strikes=np.array([70.,85.,100.,115.,130.]);calls=payoff_matrix(strikes,edges*100,d)@mass
        puts=calls-d*(100-strikes)
        pairs=tuple(Pair(float(k),{'bid':float(c-width),'ask':float(c+width)},
            {'bid':float(p-width),'ask':float(p+width)}) for k,c,p in zip(strikes,calls,puts))
        groups.append(MarketGroup(str(t),'2026-09-18T16:00:00-04:00','2026-12-18T16:00:00-05:00',t,pairs))
    return groups,edges,mass


class ComparisonMathTests(unittest.TestCase):
    def test_effective_call_bounds_enforce_both_option_types(self):
        groups,edges,_=uniform_groups();p=make_problem(groups,edges)
        pos=0
        for g,c in zip(groups,p.carry):
            for pair in g.pairs:
                pv=c['discount']*(c['forward']-pair.strike)
                expected=(max(pair.call['bid'],pair.put['bid']+pv),min(pair.call['ask'],pair.put['ask']+pv))
                np.testing.assert_allclose([p.lower[pos],p.upper[pos]],expected,rtol=0,atol=1e-12);pos+=1

    def test_known_uniform_solution_has_zero_curvature_and_preserves_prices(self):
        groups,edges,mass=uniform_groups();p=make_problem(groups,edges);fit=fit_spreads(p)
        self.assertEqual(fit['status'],'solved')
        np.testing.assert_allclose(fit['weights'],np.tile(mass,(2,1)),atol=2e-6,rtol=0)
        self.assertLess(fit['roughness_objective'],1e-9)
        self.assertLess(fit['constraint_summary']['maximum_spread_distance_points'],PRICE_TOL)

    def test_parity_compatible_but_nonconvex_prices_need_positive_widening(self):
        groups,edges,_=uniform_groups();pairs=list(groups[0].pairs);x=pairs[2]
        pairs[2]=Pair(x.strike,{k:v+10 for k,v in x.call.items()},{k:v+10 for k,v in x.put.items()})
        changed=[replace(groups[0],pairs=tuple(pairs)),groups[1]];p=make_problem(changed,edges)
        self.assertAlmostEqual(p.carry[0]['forward'],100.,places=10)
        r=linear_extreme(p,allow_widening=True)
        self.assertEqual(r['status'],'solved');self.assertGreater(r['value'],1.)
        self.assertEqual(linear_extreme(p)['status'],'infeasible')

    def test_feasible_tail_ranges_contain_truth_and_narrow_with_tighter_quotes(self):
        wide,edges,mass=uniform_groups(2.)
        tight,_,_=uniform_groups(.05)
        coeff=np.zeros((2,6));coeff[0]=tail_coefficients(edges,.8)
        answers=[]
        for groups in (wide,tight):
            p=make_problem(groups,edges);lo=linear_extreme(p,coeff);hi=linear_extreme(p,coeff,maximise=True)
            self.assertEqual(lo['status'],'solved');self.assertEqual(hi['status'],'solved')
            self.assertLessEqual(lo['value'],.3+1e-8);self.assertGreaterEqual(hi['value'],.3-1e-8)
            answers.append((lo['value'],hi['value']))
        self.assertGreaterEqual(answers[1][0],answers[0][0]-1e-8)
        self.assertLessEqual(answers[1][1],answers[0][1]+1e-8)
        np.testing.assert_allclose(tail_coefficients(edges,.8)+tail_coefficients(edges,.8,True),1)

    def test_common_horizon_mixes_distributions_and_prices_without_extrapolating(self):
        groups,edges,mass=uniform_groups();groups=[replace(groups[0],maturity=20/365),replace(groups[1],maturity=100/365)]
        endpoints=np.zeros(6);endpoints[[0,-1]]=.5;w=np.vstack([mass,endpoints])
        r=common_horizon(groups,w,edges,60)
        np.testing.assert_allclose(r['maturity_weights'],[.5,.5],atol=1e-14)
        np.testing.assert_allclose(r['mass'],w.mean(axis=0),atol=1e-14)
        self.assertAlmostEqual(r['risk']['normalised_mean'],1.,places=14)
        B=payoff_matrix(np.linspace(.1,2,51),edges,1.)
        np.testing.assert_allclose(B@np.asarray(r['mass']),.5*(B@w[0]+B@w[1]),atol=1e-14)
        np.testing.assert_allclose(interpolation_weights(groups,20),[1,0])
        with self.assertRaises(ValueError):interpolation_weights(groups,10)
        with self.assertRaises(ValueError):interpolation_weights(groups,120)


class SavedComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((ROOT/'results/comparison_summary.json').read_text())
        cls.cases={n:json.loads((ROOT/'results/comparison_cases'/(n+'.json')).read_text()) for n in cls.report['case_ids']}
        cls.inputs={s['id']:audit_file(ROOT/'data/raw/marking_prices'/s['file'])[0] for s in cls.report['snapshots']}

    def test_all_reported_constraints_and_original_spread_residuals_reconstruct(self):
        for case in self.cases.values():
            if case['status']!='solved':continue
            w=np.array(case['weights']);edges=np.array(case['edges_normalised'])
            np.testing.assert_allclose(w.sum(axis=1),1,atol=1e-8,rtol=0)
            np.testing.assert_allclose(w@((edges[:-1]+edges[1:])/2),1,atol=1e-8,rtol=0)
            self.assertGreaterEqual(w.min(),-1e-9);self.assertTrue(continuous_calendar_check(edges,w)[0]['passes'])
            self.assertTrue(all(h['status']=='Solved' for h in case['history']))
            for m in case['marginals']:
                f=DensityFit(np.array(m['edges']),np.array(m['mass']),m['discount'],m['forward'],0,0,0.)
                for r in m['quote_residuals']:
                    c=f.prices(np.array([r['strike']]))[0];v=c if r['option_type']=='C' else c-f.discount*(f.forward-r['strike'])
                    self.assertAlmostEqual(v,r['fitted'],places=8)
                    self.assertLessEqual(max(r['bid']-v,v-r['ask'],0.),PRICE_TOL)

    def test_all_held_pairs_are_excluded_from_carry_estimation_and_training(self):
        for snapshot in self.report['snapshots']:
            groups=self.inputs[snapshot['id']];count=0;sse=0.;outside=0
            for name in snapshot['holdout_cases']:
                case=self.cases[name]
                for g,mem,saved_c in zip(groups,case['membership'],case['carry']):
                    train,held=mem['train_indices'],mem['held_indices']
                    self.assertFalse(set(train)&set(held));self.assertIn(0,train);self.assertIn(len(g.pairs)-1,train)
                    c=infer_carry(tuple(g.pairs[i] for i in train))
                    for key in ('discount','forward'):self.assertAlmostEqual(c[key],saved_c[key],places=9)
                if case['status']!='solved':continue
                for e,m in zip(case['held_out'],case['marginals']):
                    for r in e['quote_residuals']:
                        sse+=(r['midpoint_residual']/m['forward'])**2;count+=1;outside+=r['distance_outside_spread']>PRICE_TOL
            self.assertEqual(count,snapshot['holdout_summary']['held_quote_count'])
            self.assertEqual(outside,snapshot['holdout_summary']['outside_count'])
            self.assertAlmostEqual(sse/count,snapshot['holdout_summary']['pooled_normalised_mse'],places=18)

    def test_common_contracts_and_common_horizon_weights_reconstruct(self):
        for mi,ks in enumerate(self.report['common_strikes']):
            expected=set.intersection(*[{p.strike for p in g[mi].pairs} for g in self.inputs.values()])
            self.assertEqual(ks,sorted(expected))
        for s in self.report['snapshots']:
            c=self.cases[s['primary_case']];r=common_horizon(self.inputs[s['id']],c['weights'],np.array(c['edges_normalised']))
            np.testing.assert_allclose(r['mass'],s['common_60_days']['mass'],rtol=0,atol=1e-14)
            self.assertAlmostEqual(sum(r['maturity_weights']),1,places=14)
            self.assertEqual(sum(v>0 for v in r['maturity_weights']),2)

    def test_risk_extremisers_meet_constraints_and_reproduce_bounds(self):
        for s in self.report['snapshots']:
            p=make_problem(self.inputs[s['id']]);rows=json.loads((ROOT/'results/comparison_cases'/(s['id']+'_risk_ranges.json')).read_text())['rows']
            self.assertEqual(len(rows),12)
            for r in rows:
                coeff=np.outer(r['maturity_weights'],tail_coefficients(p.edges,r['threshold'],r['upper_event']))
                for key,endpoint in [('minimisation','lower'),('maximisation','upper')]:
                    rec=r[key];w=np.array(rec['weights']);prices=p.price_map@w.ravel()
                    self.assertAlmostEqual(float(np.sum(coeff*w)),r[endpoint],places=12)
                    self.assertLessEqual(max(0,np.max(p.lower-prices),np.max(prices-p.upper)),rec['price_tolerance_points'])
                    self.assertTrue(continuous_calendar_check(p.edges,w)[0]['passes'])
                    self.assertLessEqual(rec['primal_dual_objective_gap'],1e-7)
                self.assertLessEqual(r['lower'],r['point']+1e-8);self.assertGreaterEqual(r['upper'],r['point']-1e-8)

    def test_code_inputs_and_all_earlier_notebooks_remain_identical(self):
        for n,h in self.report['code_sha256'].items():self.assertEqual(sha256(ROOT/n),h,n)
        for n,h in self.report['input_sha256'].items():self.assertEqual(sha256(ROOT/'data/raw/marking_prices'/n),h,n)
        for n,h in json.loads((ROOT/'results/milestone10_preserved_sha256.json').read_text()).items():self.assertEqual(sha256(ROOT/n),h,n)
        self.assertEqual(sha256(ROOT/'results/marking_calibration.json'),self.report['parent_milestone9_sha256'])


if __name__=='__main__':unittest.main()
