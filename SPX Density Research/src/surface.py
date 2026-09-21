"""Diagnostics for independently fitted maturities; no calendar constraint.

See research/surface_methodology.md, Equations (13)-(15).
"""
import numpy as np


def normalised_calls(fit, moneyness):
    """C(kappa F,T)/(D F), with kappa=K/F (not log-moneyness)."""
    kappa = np.asarray(moneyness, dtype=float)
    if kappa.ndim != 1 or not np.all(np.isfinite(kappa)) or np.any(kappa < 0):
        raise ValueError("Moneyness must be a finite nonnegative vector.")
    return fit.prices(kappa * fit.forward) / (fit.discount * fit.forward)


def calendar_diagnostic(maturities, moneyness, calls, tolerance=1e-8):
    """Report decreases between adjacent expiries on a stated finite grid.

    This diagnostic is not an all-strike proof and does not modify fitted values.
    It expects normalised calls, not raw prices at a fixed absolute strike.
    """
    times = np.asarray(maturities, dtype=float)
    kappa = np.asarray(moneyness, dtype=float)
    values = np.asarray(calls, dtype=float)
    if (times.ndim != 1 or len(times) < 2 or not np.all(np.isfinite(times))
            or np.any(times <= 0) or np.any(np.diff(times) <= 0)):
        raise ValueError("At least two positive, increasing maturities required.")
    if (kappa.ndim != 1 or len(kappa) < 2 or not np.all(np.isfinite(kappa))
            or np.any(kappa < 0) or np.any(np.diff(kappa) <= 0)):
        raise ValueError("At least two increasing nonnegative moneyness values required.")
    if values.shape != (len(times), len(kappa)) or not np.all(np.isfinite(values)):
        raise ValueError("Finite call matrix must match maturities and moneyness.")
    if not np.isfinite(tolerance) or tolerance < 0:
        raise ValueError("A finite nonnegative tolerance is required.")
    changes = np.diff(values, axis=0)
    pairs = []
    for i, row in enumerate(changes):
        location = int(np.argmin(row))
        pairs.append({
            "from_years": float(times[i]), "to_years": float(times[i + 1]),
            "violations": int(np.count_nonzero(row < -tolerance)),
            "minimum_change": float(row[location]),
            "minimum_change_moneyness": float(kappa[location]),
        })
    return {
        "scope": "Adjacent fitted maturities on a finite normalised-strike grid only",
        "constraint_enforced": False, "tolerance": tolerance,
        "moneyness_range": [float(kappa[0]), float(kappa[-1])],
        "moneyness_points": len(kappa), "comparisons": int(changes.size),
        "violations": int(np.count_nonzero(changes < -tolerance)),
        "maximum_decrease": float(max(0, -changes.min())), "pairs": pairs,
    }


def interval_probability(fit, lower, upper):
    """Exact histogram probability on [lower, upper]; no display-grid integral."""
    if not np.isfinite(lower) or not np.isfinite(upper) or lower > upper:
        raise ValueError("Finite ordered interval bounds required.")
    overlap = np.maximum(0, np.minimum(fit.edges[1:], upper)
                         - np.maximum(fit.edges[:-1], lower))
    return float(np.sum(fit.mass * overlap / np.diff(fit.edges)))
