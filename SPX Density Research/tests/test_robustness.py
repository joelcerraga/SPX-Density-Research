"""Independent benchmark integrals, grid scaling and reported risk quantities."""
import base64
import csv
import hashlib
import json
from pathlib import Path
import re
import unittest

import numpy as np
from scipy.integrate import quad

from src.constrained import DensityFit, payoff_matrix
from src.density import Parameters, call_price, exact_density
from src.joint import continuous_calendar_check, fit_maturities
from src.robustness import (BASE_ALPHA, BENCHMARKS, MixtureBenchmark, equivalent_penalty,
                            full_density_error, histogram_risk, study_settings)

ROOT = Path(__file__).resolve().parents[1]


class RobustnessTests(unittest.TestCase):
    def test_explicit_residual_form_matches_expanded_quadratic(self):
        edges=np.linspace(0,2,9)
        first=np.full(8,.125)
        second=first+np.array([.1,-.125,-.125,.3,-.125,-.0125,-.125,.1125])
        forward=[100.,110.];discount=[.99,.97];ratios=np.linspace(0,2,33)
        k=[F*ratios for F in forward]
        y=[D*F*(payoff_matrix(ratios,edges,1.)@w) for D,F,w in zip(discount,forward,[first,second])]
        args=(k,y,forward,discount,[.1,.2],edges)
        expanded=fit_maturities(*args,penalty=1e-6)
        residual=fit_maturities(*args,penalty=1e-6,residual_form=True,solver_backend="clarabel",max_solver_iterations=200)
        self.assertTrue(expanded.continuous_check["passes"])
        self.assertTrue(residual.continuous_check["passes"])
        np.testing.assert_allclose(expanded.weights,residual.weights,atol=2e-7,rtol=1e-6)
        self.assertAlmostEqual(expanded.solver["objective_sum"],residual.solver["objective_sum"],places=10)

    def test_single_component_reproduces_existing_benchmark(self):
        p = Parameters(maturity=1.)
        k = np.linspace(.5*p.forward,2*p.forward,31)
        b = BENCHMARKS["lognormal"]
        np.testing.assert_allclose(b.prices(k,p),call_price(k,p),rtol=1e-13)
        np.testing.assert_allclose(b.density(k/p.forward,p.maturity)/p.forward,exact_density(k,p),rtol=1e-13)

    def test_mixture_mass_mean_variance_and_tails_by_quadrature(self):
        b = BENCHMARKS["mixture"]
        density = lambda x: float(b.density(x,1.))
        mass = quad(density,0,np.inf,epsabs=1e-10)[0]
        mean = quad(lambda x:x*density(x),0,np.inf,epsabs=1e-10)[0]
        variance = quad(lambda x:(x-1)**2*density(x),0,np.inf,epsabs=1e-10)[0]
        self.assertAlmostEqual(mass,1.,places=9)
        self.assertAlmostEqual(mean,1.,places=9)
        self.assertAlmostEqual(variance,b.variance(1.),places=9)
        self.assertAlmostEqual(quad(density,0,.8,epsabs=1e-10)[0],float(b.cdf(.8,1.)),places=9)
        self.assertAlmostEqual(quad(density,1.8,np.inf,epsabs=1e-10)[0],float(b.upper_tail(1.8,1.)),places=9)

    def test_mixture_call_prices_by_payoff_integration(self):
        p = Parameters(spot=100.,maturity=1.)
        b = BENCHMARKS["mixture"]
        for ratio in (.7,1.,1.6):
            integral = quad(lambda x:(x-ratio)*float(b.density(x,1.)),ratio,np.inf,epsabs=1e-10)[0]
            price = np.exp(-p.rate)*p.forward*integral
            self.assertAlmostEqual(price,float(b.prices(np.array([ratio*p.forward]),p)[0]),places=7)

    def test_penalty_matches_quadratic_curvature_on_every_grid(self):
        for s in study_settings():
            edges=s["edges"];h=edges[1]-edges[0];J=len(edges)-1
            centres=(edges[1:]+edges[:-1])/2
            g=centres**2  # Smooth function with constant second derivative 2.
            actual=s["penalty"]*np.mean(np.diff(g,n=2)**2)
            expected=s["alpha"]*4*(J-2)*h
            self.assertAlmostEqual(actual/expected,1.,places=9)
        base=study_settings()[0]
        self.assertAlmostEqual(base["penalty"],1e-6,places=17)
        np.testing.assert_allclose(study_settings()[5]["edges"],base["edges"][10:101],atol=1e-14)

    def test_exact_uniform_histogram_risk(self):
        fit=DensityFit(np.array([0.,100.,200.]),np.array([.5,.5]),1.,100.,0.,0,0.)
        risk=histogram_risk(fit)
        self.assertAlmostEqual(risk["below_0_8_forward"],.4)
        self.assertAlmostEqual(risk["above_1_2_forward"],.4)
        self.assertAlmostEqual(risk["above_1_8_forward"],.1)
        self.assertAlmostEqual(risk["normalised_mean"],1.)
        self.assertAlmostEqual(risk["normalised_variance"],1/3)

    def test_full_domain_error_includes_omitted_probability(self):
        fit=DensityFit(np.array([0.,1.,2.]),np.array([.5,.5]),1.,1.,0.,0,0.)
        b=BENCHMARKS["mixture"]
        error=full_density_error(fit,b,1.)
        inside=quad(lambda x:abs(.5-float(b.density(x,1.))),0,2,epsabs=1e-9,points=[.7,1.,1.3])[0]
        outside=quad(lambda x:float(b.density(x,1.)),2,np.inf,epsabs=1e-10)[0]
        self.assertAlmostEqual(error["full_domain"],inside+outside,places=6)
        self.assertGreater(error["full_domain"],error["on_support"])

    def test_invalid_benchmarks_and_grid_scaling_rejected(self):
        for weights,vols in [((.5,.4),(.2,.3)),((1.,),(-.2,)),((1.,),(np.nan,)),((.5,.5),(.2,))]:
            with self.assertRaises(ValueError): MixtureBenchmark(weights,vols)
        for edges in ([0,1,1,2],[0,1,2],[0,.2,.5,1],[0,1,2,np.nan]):
            with self.assertRaises(ValueError): equivalent_penalty(edges)
        with self.assertRaises(ValueError): equivalent_penalty([0,1,2,3],-BASE_ALPHA)

    def test_saved_results_reproduce_calendar_and_risk_summaries(self):
        report=json.loads((ROOT/"results/robustness_validation.json").read_text())
        with (ROOT/"results/robustness_bin_masses.csv").open() as f: rows=list(csv.DictReader(f))
        self.assertEqual(report["case_count"],14)
        self.assertEqual(report["marginal_count"],112)
        for key,b in report["benchmarks"].items():
            for s in report["settings"]:
                case=b["cases"][s["id"]];weights=[]
                for m in case["marginals"]:
                    part=[r for r in rows if r["benchmark"]==key and r["setting"]==s["id"] and int(r["horizon_days"])==m["days"]]
                    mass=np.array([float(r["mass"]) for r in part]);weights.append(mass)
                    edges=np.r_[[float(r["left_edge"]) for r in part],float(part[-1]["right_edge"])]
                    fit=DensityFit(edges,mass,m["discount"],m["forward"],s["penalty"],0,0.)
                    for field,value in histogram_risk(fit).items(): self.assertAlmostEqual(value,m["risk"][field],places=12)
                    self.assertGreaterEqual(m["density_error"]["full_domain"],m["density_error"]["outside_support_probability"])
                checked,_=continuous_calendar_check(s["edges"],weights)
                self.assertTrue(checked["passes"])
                self.assertAlmostEqual(checked["minimum_gap"],case["calendar"]["minimum_gap"],places=12)

    def test_inputs_are_preserved_and_noise_is_paired(self):
        report=json.loads((ROOT/"results/robustness_validation.json").read_text())
        for name,digest in report["input_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/"results"/name).read_bytes()).hexdigest(),digest)
        with (ROOT/"results/robustness_quotes.csv").open() as f: rows=list(csv.DictReader(f))
        a=[r for r in rows if r["benchmark"]=="lognormal"]
        b=[r for r in rows if r["benchmark"]=="mixture"]
        self.assertEqual(len(a),648)
        self.assertEqual(len(a),len(b))
        for x,y in zip(a,b):
            self.assertEqual(x["strike"],y["strike"])
            self.assertEqual(x["noise"],y["noise"])
            self.assertEqual(x["horizon_days"],y["horizon_days"])

    def test_notebook_has_numbered_equations_and_captions_below_figures(self):
        notebook=json.loads((ROOT/"06_density_robustness.ipynb").read_text())
        cells=notebook["cells"];numbers=[]
        for i,c in enumerate(cells):
            for name,a in c.get("attachments",{}).items():
                number=int(re.search(r"figure_(\d+)_",name)[1]);numbers.append(number)
                self.assertEqual(base64.b64decode(a["image/png"]),(ROOT/"figures"/name).read_bytes())
                self.assertTrue("".join(cells[i+1]["source"]).lstrip().startswith(f"Figure {number}."))
        self.assertEqual(numbers,[15,16,17])
        source="\n".join("".join(c["source"]) for c in cells if c["cell_type"]=="markdown")
        self.assertEqual(re.findall(r"\\tag\{(\d+)\}",source),["20","21","22","23","24","25"])
        self.assertNotRegex(source,r"\{\{[A-Z_]+\}\}")
