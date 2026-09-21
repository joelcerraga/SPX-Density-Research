"""Synthetic mixture benchmarks and exact histogram risk summaries.

The mixture generates test data; it is not the fitted estimator. All components
share the same forward, and mixture weights are fixed across maturity.
"""
from dataclasses import dataclass, replace
from functools import lru_cache

import numpy as np
from scipy.integrate import quad
from scipy.special import ndtr, roots_legendre

from src.density import call_price
from src.surface import interval_probability

BASE_WIDTH = 1.9 / 120
BASE_ALPHA = 1e-6 * BASE_WIDTH ** 3 / 118


@dataclass(frozen=True)
class MixtureBenchmark:
    weights: tuple
    volatilities: tuple

    def __post_init__(self):
        w, v = np.asarray(self.weights, float), np.asarray(self.volatilities, float)
        if (w.ndim != 1 or not len(w) or w.shape != v.shape
                or not np.all(np.isfinite(w)) or not np.all(np.isfinite(v))
                or np.any(w <= 0) or np.any(v <= 0) or abs(w.sum() - 1) > 1e-12):
            raise ValueError("Positive finite component weights summing to one and matching volatilities required.")

    def prices(self, strikes, p):
        return sum(w * call_price(strikes, replace(p, volatility=v))
                   for w, v in zip(self.weights, self.volatilities))

    def density(self, x, maturity):
        x = np.asarray(x, float)
        if not np.all(np.isfinite(x)) or not np.isfinite(maturity) or maturity <= 0:
            raise ValueError("Finite normalised levels and positive maturity required.")
        safe = np.where(x > 0, x, 1.)
        result = np.zeros_like(safe)
        for weight, sigma in zip(self.weights, self.volatilities):
            v = sigma * np.sqrt(maturity)
            z = (np.log(safe) + .5 * v * v) / v
            result += weight * np.exp(-.5 * z * z) / (safe * v * np.sqrt(2 * np.pi))
        return np.where(x > 0, result, 0.)

    def cdf(self, x, maturity):
        x = np.asarray(x, float)
        if np.any(np.isnan(x)) or not np.isfinite(maturity) or maturity <= 0:
            raise ValueError("Non-NaN levels and positive maturity required.")
        safe = np.where(x > 0, x, 1.)
        result = sum(w * ndtr((np.log(safe) + .5 * s * s * maturity) / (s * np.sqrt(maturity)))
                     for w, s in zip(self.weights, self.volatilities))
        return np.where(x > 0, result, 0.)

    def upper_tail(self, x, maturity):
        # Evaluate the survival function directly, avoiding 1-CDF cancellation.
        x = np.asarray(x, float)
        if np.any(np.isnan(x)) or not np.isfinite(maturity) or maturity <= 0:
            raise ValueError("Non-NaN levels and positive maturity required.")
        safe = np.where(x > 0, x, 1.)
        result = sum(w * ndtr(-(np.log(safe) + .5 * s * s * maturity) / (s * np.sqrt(maturity)))
                     for w, s in zip(self.weights, self.volatilities))
        return np.where(x > 0, result, 1.)

    def variance(self, maturity):
        if not np.isfinite(maturity) or maturity <= 0:
            raise ValueError("Positive maturity required.")
        return float(sum(w * np.expm1(s * s * maturity)
                         for w, s in zip(self.weights, self.volatilities)))


BENCHMARKS = {"lognormal": MixtureBenchmark((1.,), (.2,)),
              "mixture": MixtureBenchmark((.75, .25), (.14, .40))}


def equivalent_penalty(edges, alpha=BASE_ALPHA):
    edges = np.asarray(edges, float)
    if (edges.ndim != 1 or len(edges) < 4 or not np.all(np.isfinite(edges))
            or np.any(np.diff(edges) <= 0) or not np.isfinite(alpha) or alpha < 0):
        raise ValueError("Increasing finite edges, at least three bins and nonnegative roughness coefficient required.")
    width = np.diff(edges)
    if not np.allclose(width, width[0], rtol=1e-10, atol=1e-14):
        raise ValueError("Equal-width bins required.")
    return float(alpha * (len(edges) - 3) / width[0] ** 3)


def study_settings():
    """Seven declared cases; support changes use nested bins of equal width."""
    cases = [
        ("baseline", "Baseline", np.linspace(.3, 2.2, 121), 1.),
        ("coarse", "80 bins", np.linspace(.3, 2.2, 81), 1.),
        ("fine", "160 bins", np.linspace(.3, 2.2, 161), 1.),
        ("weak", "Smoothing / 10", np.linspace(.3, 2.2, 121), .1),
        ("strong", "Smoothing x 10", np.linspace(.3, 2.2, 121), 10.),
        ("narrow", "Narrow support", .3 + np.arange(10, 101) * BASE_WIDTH, 1.),
        ("wide", "Wide support", .3 + np.arange(-12, 145) * BASE_WIDTH, 1.),
    ]
    return [{"id": key, "label": label, "edges": edges, "alpha_multiple": scale,
             "alpha": BASE_ALPHA * scale, "penalty": equivalent_penalty(edges, BASE_ALPHA * scale)}
            for key, label, edges, scale in cases]


def histogram_risk(fit):
    edges = fit.edges / fit.forward
    a, b = edges[:-1], edges[1:]
    mean = float(fit.mass @ ((a + b) / 2))
    second = float(fit.mass @ ((a*a + a*b + b*b) / 3))
    return {"below_0_8_forward": interval_probability(fit, 0., .8 * fit.forward),
            "above_1_2_forward": interval_probability(fit, 1.2 * fit.forward, max(1.2 * fit.forward, fit.edges[-1])),
            "above_1_8_forward": interval_probability(fit, 1.8 * fit.forward, fit.edges[-1])
                if fit.edges[-1] >= 1.8 * fit.forward else 0.,
            "normalised_mean": mean, "normalised_variance": second - mean**2}


def true_risk(benchmark, maturity):
    return {"below_0_8_forward": float(benchmark.cdf(.8, maturity)),
            "above_1_2_forward": float(benchmark.upper_tail(1.2, maturity)),
            "above_1_8_forward": float(benchmark.upper_tail(1.8, maturity)),
            "normalised_mean": 1., "normalised_variance": benchmark.variance(maturity)}


@lru_cache(maxsize=6)
def quadrature(order):
    return roots_legendre(order)


def full_density_error(fit, benchmark, maturity, tolerance=2e-7):
    """Binwise Gaussian quadrature plus exact omitted benchmark probability.

    Successive-order agreement is a numerical convergence check, not a rigorous
    quadrature error bound. The histogram is never renormalised to a subwindow.
    """
    edges = fit.edges / fit.forward
    widths = np.diff(edges)
    centres = (edges[1:] + edges[:-1]) / 2
    heights = fit.mass / widths
    omitted = float(benchmark.cdf(edges[0], maturity) + benchmark.upper_tail(edges[-1], maturity))
    old = None
    for order in (32, 64, 128, 256, 512, 1024):
        nodes, weights = quadrature(order)
        x = centres[:, None] + widths[:, None] * nodes[None, :] / 2
        error = np.abs(heights[:, None] - benchmark.density(x, maturity))
        inside = float(np.sum((error @ weights) * widths / 2))
        if old is not None and abs(inside - old) <= tolerance:
            return {"on_support": inside, "outside_support_probability": omitted,
                    "full_domain": inside + omitted, "quadrature_order": order,
                    "quadrature_method": "Successive Gaussian rules within each bin",
                    "quadrature_change": abs(inside - old), "quadrature_error_estimate": abs(inside - old)}
        old = inside
    # Very wide bins can straddle sharp absolute-error kinks. Use independent
    # adaptive integration there instead of accepting a poorly converged rule.
    integrated = [quad(lambda x: abs(height - float(benchmark.density(x, maturity))),
                       a, b, epsabs=tolerance/(4*len(widths)), epsrel=1e-10, limit=200)
                  for a, b, height in zip(edges[:-1], edges[1:], heights)]
    inside = sum(value for value, _ in integrated)
    error_estimate = sum(error for _, error in integrated)
    if error_estimate > tolerance:
        raise RuntimeError("Density-error quadrature did not meet its refinement target.")
    return {"on_support": inside, "outside_support_probability": omitted,
            "full_domain": inside + omitted, "quadrature_order": None,
            "quadrature_method": "Adaptive binwise quadrature fallback",
            "quadrature_change": abs(inside - old), "quadrature_error_estimate": error_estimate}
