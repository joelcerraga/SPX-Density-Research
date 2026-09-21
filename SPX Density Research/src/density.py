"""Synthetic European-call benchmark; no market data or live calibration."""
from dataclasses import dataclass
import numpy as np
from scipy.special import ndtr
from scipy.integrate import trapezoid

@dataclass(frozen=True)
class Parameters:
    spot: float = 6000.0
    rate: float = 0.04
    dividend: float = 0.015
    volatility: float = 0.20
    maturity: float = 0.5

    @property
    def forward(self):
        return self.spot * np.exp((self.rate-self.dividend)*self.maturity)

def call_price(strikes, p=Parameters()):
    k = np.asarray(strikes, dtype=float)
    if np.any(k <= 0) or min(p.spot,p.volatility,p.maturity) <= 0:
        raise ValueError('Positive strikes, spot, volatility and maturity required.')
    v = p.volatility*np.sqrt(p.maturity)
    d1 = (np.log(p.spot/k)+(p.rate-p.dividend+0.5*p.volatility**2)*p.maturity)/v
    return p.spot*np.exp(-p.dividend*p.maturity)*ndtr(d1)-k*np.exp(-p.rate*p.maturity)*ndtr(d1-v)

def exact_density(levels, p=Parameters()):
    s = np.asarray(levels, dtype=float)
    v = p.volatility*np.sqrt(p.maturity)
    z = (np.log(s/p.spot)-(p.rate-p.dividend-0.5*p.volatility**2)*p.maturity)/v
    return np.exp(-0.5*z*z)/(s*v*np.sqrt(2*np.pi))

def recover_density(strikes, calls, rate, maturity):
    k, c = np.asarray(strikes, dtype=float), np.asarray(calls, dtype=float)
    if k.ndim != 1 or c.shape != k.shape or len(k)<3:
        raise ValueError('Matching one-dimensional arrays with at least three points required.')
    h = np.diff(k)
    if np.any(h<=0) or not np.allclose(h,h[0],rtol=1e-10,atol=1e-10):
        raise ValueError('This baseline requires strictly increasing, equally spaced strikes.')
    # Endpoints are excluded: they have no centred three-point stencil.
    return k[1:-1], np.exp(rate*maturity)*np.diff(c,n=2)/h[0]**2

def diagnostics(k, recovered, p=Parameters()):
    exact = exact_density(k,p)
    checks = np.array([4800.,5400.,6000.,6600.,7200.])
    repriced = np.array([np.exp(-p.rate*p.maturity)*trapezoid(np.maximum(k-strike,0)*recovered,k) for strike in checks])
    return {
        'mass': float(trapezoid(recovered,k)),
        'minimum_density':float(recovered.min()),
        'negative_density_count':int(np.sum(recovered<0)),
        'integrated_absolute_error':float(trapezoid(np.abs(recovered-exact),k)),
        'first_moment':float(trapezoid(k*recovered,k)),
        'theoretical_forward':float(p.forward),
        'forward_relative_error':float(abs(trapezoid(k*recovered,k)-p.forward)/p.forward),
        'max_repricing_error_index_points':float(np.max(np.abs(repriced-call_price(checks,p))))
    }
