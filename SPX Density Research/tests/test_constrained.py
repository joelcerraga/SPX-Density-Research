"""Independent pricing and shape tests, plus notebook-layout regression checks."""
import json
from pathlib import Path
import unittest
import numpy as np
from scipy.integrate import quad
from src.constrained import DensityFit, fit_density, payoff_matrix
from src.density import Parameters, call_price


class ConstrainedTests(unittest.TestCase):
    def setUp(self):
        self.edges = np.array([1., 2., 3., 4.])
        self.mass = np.array([.2, .5, .3])
        self.fit = DensityFit(self.edges, self.mass, .97, 2.6, 0., 0, 0.)

    def test_payoff_against_independent_quadrature(self):
        for strike in (0., .8, 1., 1.7, 2.6, 3.9, 4., 5.):
            value = sum(.97 * w * quad(lambda s: max(s-strike, 0.) / (b-a), a, b,
                                      points=[strike] if a < strike < b else None)[0]
                        for a, b, w in zip(self.edges[:-1], self.edges[1:], self.mass))
            self.assertAlmostEqual(self.fit.prices([strike])[0], value, places=10)

    def test_distribution_mass_mean_and_boundaries(self):
        self.assertAlmostEqual(self.mass.sum(), 1.)
        self.assertAlmostEqual(self.mass @ ((self.edges[:-1]+self.edges[1:])/2), 2.6)
        np.testing.assert_allclose(self.fit.density([0., 1., 2., 3., 4., 5.]), [0., .2, .5, .3, 0., 0.])
        self.assertAlmostEqual(float(self.fit.density(2.5)), .5)
        self.assertAlmostEqual(self.fit.prices([0.])[0], .97*2.6)
        self.assertEqual(self.fit.prices([5.])[0], 0.)

    def test_price_derivatives_recover_bin_densities(self):
        # Away from edges, the price is quadratic and the centred stencil is exact.
        x=np.array([1.5, 2.5, 3.5]); h=.01
        second=(self.fit.prices(x+h)-2*self.fit.prices(x)+self.fit.prices(x-h))/h**2
        np.testing.assert_allclose(second/.97, self.fit.density(x), rtol=1e-8, atol=1e-9)

    def test_clean_fit_reprices_and_satisfies_constraints(self):
        k=np.linspace(.5, 4.5, 17)
        recovered=fit_density(k, self.fit.prices(k), 2.6, .97, self.edges, penalty=0.)
        np.testing.assert_allclose(recovered.mass, self.mass, atol=1e-6)
        np.testing.assert_allclose(recovered.prices(k), self.fit.prices(k), atol=1e-6)

    def test_invalid_inputs_rejected(self):
        k=np.array([1.,2.,3.]); y=self.fit.prices(k)
        for edges in ([1,2,4,5], [3,4,5,6], [1,2,3], [1,1,2,3]):
            with self.assertRaises(ValueError):
                fit_density(k,y,2.6,.97,edges)
        for prices in ([1,2], [1,float('nan'),3], [1,-1,3]):
            with self.assertRaises(ValueError):
                fit_density(k,prices,2.6,.97,self.edges)
        for discount in (0., -1., float('nan')):
            with self.assertRaises(ValueError):
                payoff_matrix(k,self.edges,discount)
        for penalty in (-1., float('inf')):
            with self.assertRaises(ValueError):
                fit_density(k,y,2.6,.97,self.edges,penalty)
        with self.assertRaises(ValueError):
            fit_density(k[::-1],y[::-1],2.6,.97,self.edges)
        with self.assertRaises(ValueError):
            self.fit.density([float('nan')])

    def test_saved_benchmark_shape_and_error(self):
        root=Path(__file__).resolve().parents[1]
        result=json.loads((root/'results/constrained_validation.json').read_text())
        baseline=next(r for r in result['results'] if r['penalty']==result['baseline_penalty'])
        self.assertAlmostEqual(baseline['mass'],1.,places=8)
        self.assertAlmostEqual(baseline['mean'],result['forward'],places=6)
        self.assertGreaterEqual(baseline['minimum_bin_mass'],0.)
        self.assertEqual(baseline['monotonicity_violations'],0)
        self.assertEqual(baseline['convexity_violations'],0)
        self.assertLess(baseline['withheld_clean_price_rmse'],.5)
        self.assertLess(baseline['integrated_density_absolute_error'],.05)

    def test_figure_four_explanation_stays_below_caption(self):
        root=Path(__file__).resolve().parents[1]
        cells=json.loads((root/'01_synthetic_density.ipynb').read_text())['cells']
        texts=[''.join(c['source']) for c in cells]
        caption=next(i for i,t in enumerate(texts) if t.startswith('Figure 4.'))
        explanation=next(i for i,t in enumerate(texts) if t.startswith('Figure 4 introduces'))
        self.assertEqual(explanation,caption+1)
        self.assertEqual(cells[caption-1]['cell_type'],'code')


if __name__=='__main__':
    unittest.main()
