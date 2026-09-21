"""Checks of pairing, sampling summaries, held-out evaluation and saved evidence."""
import base64
import csv
import hashlib
import json
from pathlib import Path
import re
import unittest

import numpy as np
from scipy.integrate import quad

from src.constrained import DensityFit
from src.joint import continuous_calendar_check
from src.repeated import (COVERAGES,DAYS,EDGES,REPETITIONS,bounded_quotes,
                          master_strikes,paired_summary,parameters,random_draws,scalar_summary)

ROOT=Path(__file__).resolve().parents[1]


class RepeatedTests(unittest.TestCase):
    def test_original_strikes_match_the_archived_inputs(self):
        data=np.loadtxt(ROOT/'results/maturity_quotes.csv',delimiter=',',skiprows=1)
        for d,p in zip(DAYS,parameters()):
            np.testing.assert_array_equal(master_strikes(p)[20:101],data[data[:,0]==d,1])

    def test_equal_count_comparison_and_no_validation_leakage(self):
        sparse,central=COVERAGES['sparse']['indices'],COVERAGES['central']['indices']
        self.assertEqual(len(sparse),len(central))
        self.assertEqual(len(sparse),41)
        self.assertLess(sparse[0],central[0]);self.assertGreater(sparse[-1],central[-1])
        for p in parameters():
            grid=master_strikes(p);validation=(grid[1:]+grid[:-1])/2
            self.assertGreater(grid[0]/p.forward,EDGES[0])
            self.assertLess(grid[-1]/p.forward,EDGES[-1])
            for s in COVERAGES.values():
                distances=np.abs(validation[:,None]-grid[s['indices']][None,:])
                self.assertGreater(float(distances.min()),1e-6)

    def test_bounded_errors_have_zero_mean_and_declared_variance(self):
        for clean,width in [(.1,.05),(4.,.5)]:
            def error(u): return float(bounded_quotes([clean],.5,[u])[1][0])
            self.assertAlmostEqual(quad(lambda u:error(u)/2,-1,1)[0],0,places=14)
            self.assertAlmostEqual(quad(lambda u:error(u)**2/2,-1,1)[0],width**2/3,places=14)
            y,_,_=bounded_quotes(np.array([clean,clean]),.5,[-1,1])
            self.assertGreaterEqual(y.min(),clean/2)
        with self.assertRaises(ValueError):bounded_quotes([1],-.1,[0])
        with self.assertRaises(ValueError):bounded_quotes([0],.1,[0])
        with self.assertRaises(ValueError):bounded_quotes([1],.1,[2])

    def test_random_streams_replay_independently_of_run_order(self):
        fingerprints=set()
        for r in [7,0,REPETITIONS-1,2]:
            draws,state=random_draws(r)
            bit=np.random.PCG64();bit.state=state['initial_state']
            np.testing.assert_array_equal(np.random.Generator(bit).uniform(-1,1,draws.shape),draws)
            np.testing.assert_array_equal(random_draws(r)[0],draws)
            fingerprints.add(hashlib.sha256(draws.tobytes()).hexdigest())
        self.assertEqual(len(fingerprints),4)

    def test_sampling_summaries_against_hand_calculation(self):
        s=scalar_summary([1,2,4],3)
        self.assertAlmostEqual(s['mean'],7/3)
        self.assertAlmostEqual(s['bias'],-2/3)
        self.assertAlmostEqual(s['sd']**2,7/3)
        self.assertAlmostEqual(s['mcse'],np.sqrt(7)/3)
        self.assertAlmostEqual(s['rmse'],np.sqrt(2))
        self.assertAlmostEqual(s['mse'],s['bias']**2+(s['n']-1)/s['n']*s['sd']**2)
        with self.assertRaises(ValueError):scalar_summary([1])

    def test_paired_uncertainty_uses_within_repetition_differences(self):
        s=paired_summary([1,2,3],[1,1,2])
        self.assertAlmostEqual(s['mean'],2/3)
        self.assertAlmostEqual(s['mcse'],1/3)
        with self.assertRaises(ValueError):paired_summary([1,2],[1,2,3])

    def test_saved_inputs_reproduce_all_quotes(self):
        report=json.loads((ROOT/'results/repeated_validation.json').read_text())
        for name,digest in report['input_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/'results'/name).read_bytes()).hexdigest(),digest)
        cache={r:random_draws(r)[0] for r in range(REPETITIONS)}
        count=0
        with (ROOT/'results/repeated_quotes.csv').open() as f:
            for row in csv.DictReader(f):
                r,j,d=int(row['repetition']),int(row['master_index']),int(row['days'])
                u=0. if r < 0 else cache[r][DAYS.index(d),j]
                self.assertEqual(float(row['unit_draw']),u)
                c,a=float(row['clean_call']),float(row['amplitude'])
                expected=min(a,c/2)*u
                self.assertAlmostEqual(float(row['added_error']),expected,places=13)
                self.assertAlmostEqual(float(row['observed_call']),c+expected,places=11)
                count+=1
        self.assertEqual(count,2*(1+2*REPETITIONS)*len(DAYS)*121)

    def test_saved_fits_and_reported_statistics_reconstruct(self):
        report=json.loads((ROOT/'results/repeated_validation.json').read_text())
        self.assertEqual(report['checks']['attempted'],8*(1+2*REPETITIONS))
        self.assertEqual(report['checks']['failed'],0)
        cases=[]
        for item in report['cases']:
            record=json.loads((ROOT/'results'/item['file']).read_text());c=record['result'];cases.append(c)
            digest=hashlib.sha256(json.dumps(c,sort_keys=True,allow_nan=False).encode()).hexdigest()
            self.assertEqual(record['result_sha256'],digest)
            w=np.array(c['weights']);check,_=continuous_calendar_check(EDGES,w)
            self.assertTrue(check['passes'])
            np.testing.assert_allclose(w.sum(axis=1),1,rtol=0,atol=1e-8)
            np.testing.assert_allclose(w@((EDGES[1:]+EDGES[:-1])/2),1,rtol=0,atol=1e-8)
            fraction=np.clip((EDGES[1:]-1.8)/np.diff(EDGES),0,1)
            self.assertAlmostEqual(float(w[-1]@fraction),c['marginals'][-1]['risk']['above_1_8_forward'],places=12)
        for group in report['groups']:
            selected=[c for c in cases if all(c['spec'][k]==group[k] for k in ['benchmark','coverage','amplitude'])]
            self.assertEqual(len(selected),REPETITIONS)
            values=np.array([c['metrics']['mean_full_density_l1'] for c in selected])
            target=group['metrics']['mean_full_density_l1']
            self.assertAlmostEqual(float(values.mean()),target['mean'],places=13)
            se=np.sqrt(np.sum((values-values.mean())**2)/(REPETITIONS*(REPETITIONS-1)))
            self.assertAlmostEqual(float(se),target['mcse'],places=13)
        for pair in report['paired']:
            def values(coverage):
                selected=sorted([c for c in cases if c['spec']['benchmark']==pair['benchmark']
                    and c['spec']['amplitude']==pair['amplitude'] and c['spec']['coverage']==coverage],
                    key=lambda c:c['spec']['repetition'])
                return np.array([c['metrics']['mean_full_density_l1'] for c in selected])
            delta=values(pair['left'])-values(pair['right'])
            self.assertAlmostEqual(delta.mean(),pair['metrics']['mean_full_density_l1']['mean'],places=13)
            self.assertAlmostEqual(delta.std(ddof=1)/np.sqrt(REPETITIONS),pair['metrics']['mean_full_density_l1']['mcse'],places=13)

    def test_previous_notebooks_and_interactive_files_are_preserved(self):
        manifest=json.loads((ROOT/'results/milestone7_preserved_sha256.json').read_text())
        self.assertEqual(len(manifest),8)
        for name,digest in manifest.items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),digest)

    def test_notebook_equations_figures_and_captions(self):
        notebook=json.loads((ROOT/'07_noise_and_coverage.ipynb').read_text());numbers=[]
        for i,c in enumerate(notebook['cells']):
            for name,a in c.get('attachments',{}).items():
                number=int(re.search(r'figure_(\d+)_',name)[1]);numbers.append(number)
                self.assertEqual(base64.b64decode(a['image/png']),(ROOT/'figures'/name).read_bytes())
                self.assertTrue(''.join(notebook['cells'][i+1]['source']).lstrip().startswith(f'Figure {number}.'))
        self.assertEqual(numbers,[18,19,20])
        source='\n'.join(''.join(c['source']) for c in notebook['cells'] if c['cell_type']=='markdown')
        self.assertEqual(re.findall(r'\\tag\{(\d+)\}',source),['26','27','28','29'])
        self.assertNotRegex(source,r'\{\{[A-Z_]+\}\}')
