"""Independent checks of selection, unchanged events and saved study evidence."""
import base64
import hashlib
import json
from pathlib import Path
import re
from types import SimpleNamespace
import unittest

import numpy as np
from scipy.integrate import quad

from run_selection import all_fits, fixed_fit, result_hash
from src.constrained import DensityFit
from src.joint import continuous_calendar_check
from src.repeated import DAYS, EDGES, master_strikes, parameters
from src.repeated import random_draws as earlier_draws
from src.robustness import BENCHMARKS, full_density_error, histogram_risk
from src.selection import (CANDIDATES, REPETITIONS, choose_penalty, folds,
    lower_bound_violations, observations, pooled_score, random_draws,
    reference_fit, select_penalty)

ROOT=Path(__file__).resolve().parents[1]


class SelectionTests(unittest.TestCase):
    def test_endpoints_retained_each_interior_quote_held_once(self):
        for n in (81,121):
            seen=[]
            for train,held in folds(n):
                self.assertIn(0,train);self.assertIn(n-1,train)
                self.assertEqual(len(np.intersect1d(train,held)),0)
                np.testing.assert_array_equal(np.sort(np.r_[train,held]),np.arange(n))
                seen.extend(held)
            np.testing.assert_array_equal(np.sort(seen),np.arange(1,n-1))
        self.assertEqual([len(h) for _,h in folds(81)],[27,26,26])
        self.assertEqual([len(h) for _,h in folds(121)],[40,40,39])

    def test_score_weights_observations_and_exact_ties_are_declared(self):
        self.assertEqual(pooled_score([12,4],[3,1]),4.)
        self.assertAlmostEqual(pooled_score([12,2],[3,1]),3.5)
        self.assertNotEqual(pooled_score([12,2],[3,1]),3.)
        self.assertEqual(choose_penalty([(1e-7,2),(1e-6,2),(1e-5,3)]),1e-6)
        self.assertEqual(choose_penalty([(1e-7,2),(1e-6,2+1e-14)]),1e-7)

    def test_selector_receives_only_training_quotes_and_scores_held_noisy_quotes(self):
        strikes=[np.arange(9.)+100,np.arange(9.)+200]
        quotes=[np.arange(9.)**2,np.arange(9.)**2+3]
        calls=[]
        def fitter(k,y,f,d,t,penalty):
            calls.append((k,y,penalty))
            fits=[SimpleNamespace(prices=lambda x,mean=float(v.mean()):np.full(len(x),mean+penalty)) for v in y]
            return SimpleNamespace(fits=fits,weights=np.ones((2,1)),solver={},continuous_check={})
        selected=select_penalty(strikes,quotes,[100,200],[1,1],[.5,1],candidates=(1.,2.),fitter=fitter)
        self.assertEqual(len(calls),6)
        for ci,candidate in enumerate(selected['candidates']):
            total=0;count=0
            for fi,(train,held) in enumerate(folds(9)):
                k,y,penalty=calls[3*ci+fi]
                for m,forward in enumerate([100,200]):
                    np.testing.assert_array_equal(k[m],strikes[m][train])
                    np.testing.assert_array_equal(y[m],quotes[m][train])
                    err=(float(quotes[m][train].mean())+penalty-quotes[m][held])/forward
                    total+=float(err@err);count+=len(err)
            self.assertAlmostEqual(candidate['score'],total/count,places=15)

    def test_new_streams_replay_and_differ_from_previous_study(self):
        for r in (0,3,REPETITIONS-1):
            u,state=random_draws(r)
            bit=np.random.PCG64();bit.state=state['initial_state']
            np.testing.assert_array_equal(np.random.Generator(bit).uniform(-1,1,u.shape),u)
            self.assertFalse(np.array_equal(u,earlier_draws(r)[0]))

    def test_reference_coordinates_keep_physical_prices_and_events_unchanged(self):
        fit=DensityFit(np.array([0.,110.,220.]),np.array([.5,.5]),.95,110.,1e-6,1,0.)
        fixed=reference_fit(fit,100.)
        np.testing.assert_array_equal(fixed.edges,fit.edges)
        np.testing.assert_array_equal(fixed.mass,fit.mass)
        np.testing.assert_array_equal(fixed.prices(np.array([50.,100.,180.])),fit.prices(np.array([50.,100.,180.])))
        risk=histogram_risk(fixed)
        self.assertAlmostEqual(risk['above_1_8_forward'],40/220)
        self.assertAlmostEqual(risk['below_0_8_forward'],80/220)
        self.assertAlmostEqual(risk['normalised_mean'],1.1)
        self.assertAlmostEqual(risk['normalised_variance'],220**2/(12*100**2))
        self.assertNotEqual(risk['above_1_8_forward'],histogram_risk(fit)['above_1_8_forward'])
        self.assertEqual(fit.forward,110.)

    def test_full_density_error_reference_change_matches_physical_integration(self):
        fit=DensityFit(np.array([40.,100.,180.]),np.array([.4,.6]),.97,112.,1e-6,1,0.)
        benchmark=BENCHMARKS['lognormal'];ref=100.;T=1.
        fixed=reference_fit(fit,ref)
        direct=sum(quad(lambda s:abs(w/(b-a)-float(benchmark.density(s/ref,T))/ref),a,b,
                        epsabs=1e-10,points=[ref] if a<ref<b else None)[0]
                   for a,b,w in zip(fit.edges[:-1],fit.edges[1:],fit.mass))
        direct+=float(benchmark.cdf(40/ref,T)+benchmark.upper_tail(180/ref,T))
        self.assertAlmostEqual(full_density_error(fixed,benchmark,T)['full_domain'],direct,delta=5e-7)

    def test_forward_lower_bound_against_hand_calculation(self):
        strikes=[np.array([80.,100.,120.])];quotes=[np.array([15.,1.,0.])]
        r=lower_bound_violations(strikes,quotes,[110.],[.9])
        self.assertEqual(r['count'],2)
        self.assertEqual(r['maximum_shortfall'],12.)
        self.assertAlmostEqual(r['rms_shortfall'],np.sqrt((12**2+8**2)/3))
        self.assertEqual(lower_bound_violations(strikes,quotes,[90.],[.9])['count'],0)

    def test_saved_selection_and_forward_results_reconstruct(self):
        report=json.loads((ROOT/'results/selection_validation.json').read_text())
        self.assertEqual(report['checks']['failed_or_blocked'],0)
        self.assertEqual(report['checks']['recorded_experiments'],240)
        selection,forward=[],[]
        for entry in report['cases']:
            wrapper=json.loads((ROOT/'results'/entry['file']).read_text());c=wrapper['result']
            self.assertEqual(wrapper['result_sha256'],result_hash(c))
            self.assertEqual(wrapper['signature'],report['protocol']['numerical_signature'])
            (forward if 'shift' in c['spec'] else selection).append(c)
        for fit in all_fits(selection,forward):
            w=np.array(fit['weights']);cal,_=continuous_calendar_check(EDGES,w)
            self.assertTrue(cal['passes'])
            np.testing.assert_allclose(w.sum(axis=1),1,atol=1e-8,rtol=0)
            np.testing.assert_allclose(w@((EDGES[:-1]+EDGES[1:])/2),1,atol=1e-8,rtol=0)
        self.assertEqual(len(list(all_fits(selection,forward))),report['checks']['unique_accepted_joint_fits'])
        for c in selection:
            cv=c['selection']
            scored=[]
            args=observations(c['spec']['benchmark'],c['spec']['coverage'],c['spec']['repetition'])
            for candidate in cv['candidates']:
                sums=[];counts=[]
                for fold in candidate['folds']:
                    held=np.array(fold['held_indices'])
                    reconstructed=[]
                    for m,(k,y,f,d) in enumerate(zip(args[0],args[1],args[2],args[3])):
                        fitted=DensityFit(EDGES*f,np.array(fold['weights'][m]),d,f,candidate['penalty'],0,0)
                        reconstructed.append((fitted.prices(k[held])-y[held])/f)
                    np.testing.assert_allclose(reconstructed,fold['normalised_residuals'],rtol=0,atol=1e-13)
                    sums.append(float(np.sum(np.asarray(reconstructed)**2)));counts.append(np.asarray(reconstructed).size)
                score=sum(sums)/sum(counts)
                self.assertAlmostEqual(score,candidate['score'],delta=1e-15)
                scored.append((candidate['penalty'],score))
            self.assertEqual(choose_penalty(scored),cv['selected_penalty'])
        parents={c['spec']['id']:c for c in selection}
        diagnostic=json.loads((ROOT/'results/selection_range_diagnostic.json').read_text())
        self.assertEqual(len(diagnostic['repetitions']),REPETITIONS)
        for row in diagnostic['repetitions']:
            parent=parents[f'mixture_original_r{row["repetition"]:02}']
            for method,fit in [('selected',parent['selected']),('fixed',fixed_fit(parent))]:
                partitioned=(2*row[method]['within_quote_range_rmse']**2+row[method]['outside_quote_range_rmse']**2)/3
                self.assertAlmostEqual(partitioned,fit['metrics']['validation_rmse']**2,places=11)
        for c in forward:
            spec,fit=c['spec'],c['fit'];parent=parents[spec['parent']]
            self.assertEqual(fit['penalty'],parent['selection']['selected_penalty'])
            wrapper=json.loads((ROOT/'results/selection_cases'/(spec['id']+'.json')).read_text())
            self.assertEqual(wrapper['parent_sha256'],result_hash(parent))
            for m,p in enumerate(parameters()):
                physical=EDGES*p.forward*(1+spec['shift'])
                fraction=np.clip((physical[1:]-1.8*p.forward)/np.diff(physical),0,1)
                probability=float(np.array(fit['weights'][m])@fraction)
                self.assertAlmostEqual(probability,fit['marginals'][m]['risk']['above_1_8_forward'],places=11)
                self.assertAlmostEqual(fit['marginals'][m]['risk']['normalised_mean'],1+spec['shift'],places=8)
        for group in report['groups']:
            cases=[c for c in selection if c['spec']['benchmark']==group['benchmark'] and c['spec']['coverage']==group['coverage']]
            values=np.array([c['selected']['metrics']['mean_full_density_l1']-fixed_fit(c)['metrics']['mean_full_density_l1'] for c in cases])
            s=group['paired_selected_minus_fixed']['mean_full_density_l1']
            self.assertAlmostEqual(s['mean'],values.mean(),places=13)
            self.assertAlmostEqual(s['mcse'],values.std(ddof=1)/np.sqrt(REPETITIONS),places=13)

    def test_inputs_and_evaluation_strikes_are_distinct_and_traceable(self):
        report=json.loads((ROOT/'results/selection_validation.json').read_text())
        for name,digest in report['input_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/'results'/name).read_bytes()).hexdigest(),digest)
        for name,digest in report['protocol']['code_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),digest)
        for p in parameters():
            k=master_strikes(p);held=(k[:-1]+k[1:])/2
            self.assertGreater(np.abs(held[:,None]-k[None,:]).min(),1e-6)

    def test_prior_notebooks_companions_and_new_captions(self):
        manifest=json.loads((ROOT/'results/milestone8_preserved_sha256.json').read_text())
        self.assertEqual(len(manifest),9)
        for name,digest in manifest.items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),digest)
        notebook=json.loads((ROOT/'08_smoothing_and_forwards.ipynb').read_text());numbers=[]
        for i,c in enumerate(notebook['cells']):
            for name,attachment in c.get('attachments',{}).items():
                number=int(re.search(r'figure_(\d+)_',name)[1]);numbers.append(number)
                self.assertEqual(base64.b64decode(attachment['image/png']),(ROOT/'figures'/name).read_bytes())
                self.assertTrue(''.join(notebook['cells'][i+1]['source']).lstrip().startswith(f'Figure {number}.'))
        self.assertEqual(numbers,[21,22,23])
        source='\n'.join(''.join(c['source']) for c in notebook['cells'] if c['cell_type']=='markdown')
        self.assertEqual(re.findall(r'\\tag\{(\d+)\}',source),['30','31','32','33'])
        self.assertNotRegex(source,r'\{\{[A-Z_]+\}\}')
