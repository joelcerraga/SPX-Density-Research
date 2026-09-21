"""Joint histogram fits and continuous-strike calendar verification.

All slices share bins in x=S/F. Constraints are added at offending quadratic
minima until the stated tolerance is satisfied. No mass clipping is performed.
"""
from dataclasses import dataclass

import numpy as np
import osqp
from scipy import sparse

from src.constrained import DensityFit, payoff_matrix


def validate_edges(edges):
    edges = np.asarray(edges, dtype=float)
    if (edges.ndim != 1 or len(edges) < 4 or not np.all(np.isfinite(edges))
            or edges[0] < 0 or np.any(np.diff(edges) <= 0)):
        raise ValueError("At least three finite increasing nonnegative bins required.")
    centres = (edges[1:] + edges[:-1]) / 2
    if not centres[0] < 1 < centres[-1]:
        raise ValueError("Normalised bin centres must bracket one.")
    return edges


def continuous_calendar_check(edges, weights, tolerance=1e-8):
    """Check all kappa>=0 for the supplied common-bin histogram calls.

    A gap is quadratic in each bin, linear below support and zero above it.
    Endpoints and every interior local minimum exhaust its possible minima.
    This is an analytical-location check in floating-point arithmetic, not a
    formal interval-arithmetic certificate or a check of unmodelled maturities.
    """
    edges = validate_edges(edges)
    weights = np.asarray(weights, dtype=float)
    if (weights.ndim != 2 or weights.shape[0] < 2 or weights.shape[1] != len(edges) - 1
            or not np.all(np.isfinite(weights))):
        raise ValueError("Finite matrix of at least two common-bin slices required.")
    if not np.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("Positive finite tolerance required.")
    widths = np.diff(edges)
    nodes = np.unique(np.r_[0., edges])
    B = payoff_matrix(nodes, edges, 1.)
    edge_B = payoff_matrix(edges[:-1], edges, 1.)
    pairs, cuts = [], []
    for i, delta in enumerate(np.diff(weights, axis=0)):
        gaps = B @ delta
        minimum_index = int(np.argmin(gaps))
        minimum, where = float(gaps[minimum_index]), float(nodes[minimum_index])
        left_values = edge_B @ delta
        slopes = -np.cumsum(delta[::-1])[::-1]
        curvature = delta / widths
        interior_count = 0
        offending = []
        for j in np.flatnonzero(curvature > 0):
            offset = -slopes[j] / curvature[j]
            if 0 < offset < widths[j]:
                interior_count += 1
                kappa = float(edges[j] + offset)
                value = float(left_values[j] + slopes[j] * offset + .5 * curvature[j] * offset ** 2)
                if value < minimum:
                    minimum, where = value, kappa
                if value < -tolerance:
                    offending.append(kappa)
        offending.extend(float(k) for k, value in zip(nodes, gaps) if value < -tolerance)
        pairs.append({"earlier_index": i, "later_index": i + 1,
                      "minimum_gap": minimum, "minimum_moneyness": where,
                      "endpoint_checks": len(nodes), "interior_minimum_checks": interior_count,
                      "passes": minimum >= -tolerance})
        cuts.append(sorted(set(offending)))
    minimum = min(p["minimum_gap"] for p in pairs)
    return ({"scope": "All nonnegative strikes for each adjacent pair of supplied discrete maturities under the common-bin model",
             "method": "Endpoints and quadratic interior minima; floating-point arithmetic",
             "tolerance": tolerance, "minimum_gap": minimum,
             "passes": all(p["passes"] for p in pairs), "pairs": pairs}, cuts)


@dataclass
class JointResult:
    fits: list
    weights: np.ndarray
    solver: dict
    continuous_check: dict


def fit_maturities(strikes, prices, forwards, discounts, maturities, edges,
                   penalty=1e-6, enforce_calendar=True, initial_weights=None,
                   calendar_tolerance=1e-8, max_rounds=15, max_solver_iterations=100000,
                   objective_scale=1e6, residual_form=False, solver_backend="osqp"):
    """Minimise the sum of the existing per-maturity objectives.

    Independent control: identical objective and solver with calendar constraints
    omitted. Joint fit: start with bin-boundary constraints, then add failing
    analytical minima. The acceptance tolerance is explicitly recorded.
    Defaults retain the Milestone 5 expanded OSQP formulation. Milestone 6
    selects Clarabel with explicit residual variables for the equivalent QP.
    """
    edges = validate_edges(edges)
    if solver_backend not in ("osqp", "clarabel"):
        raise ValueError("Supported solvers are osqp and clarabel.")
    if solver_backend == "clarabel":
        import clarabel
        if initial_weights is not None:
            raise ValueError("This Clarabel interface uses internal initialisation; supplied warm weights are unsupported.")
    widths = np.diff(edges)
    if not np.allclose(widths, widths[0], rtol=1e-10, atol=1e-14):
        raise ValueError("The current smoothing objective requires equal-width bins.")
    forwards, discounts, times = (np.asarray(v, dtype=float) for v in (forwards, discounts, maturities))
    if forwards.ndim != 1:
        raise ValueError("Forwards must be a one-dimensional array.")
    M, J = len(forwards), len(edges) - 1
    if (M < 2 or discounts.shape != (M,) or times.shape != (M,)
            or not all(np.all(np.isfinite(v)) for v in (forwards, discounts, times))
            or np.any(forwards <= 0) or np.any(discounts <= 0) or np.any(times <= 0)
            or np.any(np.diff(times) <= 0) or len(strikes) != M or len(prices) != M):
        raise ValueError("Matching arrays of positive forwards, discounts and increasing maturities required.")
    if (not np.isfinite(penalty) or penalty < 0 or not np.isfinite(calendar_tolerance)
            or calendar_tolerance <= 0 or not isinstance(max_rounds, int) or max_rounds < 1
            or not isinstance(max_solver_iterations, int) or max_solver_iterations < 1
            or not np.isfinite(objective_scale) or objective_scale <= 0):
        raise ValueError("Nonnegative penalty, positive tolerance and positive round count required.")
    L = np.diff(np.eye(J), n=2, axis=0) / widths[0]
    H, linear, matrices, observations = [], [], [], []
    for k, y, F, D in zip(strikes, prices, forwards, discounts):
        k, y = np.asarray(k, dtype=float), np.asarray(y, dtype=float)
        if (k.ndim != 1 or len(k) < 3 or y.shape != k.shape or np.any(k < 0)
                or np.any(np.diff(k) <= 0) or np.any(y < 0)
                or not np.all(np.isfinite(k)) or not np.all(np.isfinite(y))):
            raise ValueError("Each maturity needs sorted distinct strikes and finite nonnegative prices.")
        A = D * payoff_matrix(k / F, edges, 1.)  # C/F, exactly as Equation (12).
        target = y / F
        if not residual_form:
            H.append(A.T @ A / len(k) + penalty * (L.T @ L) / len(L))
            linear.append(-2 * A.T @ target / len(k))
        matrices.append(A)
        observations.append(target)
    auxiliary_count = 0
    if residual_form:
        price_map = sparse.block_diag(matrices, format="csc")
        roughness_map = sparse.kron(sparse.eye(M, format="csc"), L, format="csc")
        residual_map = sparse.vstack([price_map, roughness_map], format="csc")
        target_residual = np.r_[np.concatenate(observations), np.zeros(M * len(L))]
        auxiliary_count = len(target_residual)
        coefficients = np.r_[np.zeros(M * J),
            np.concatenate([np.full(len(y), 1/len(y)) for y in observations]),
            np.full(M * len(L), penalty / len(L))]
        P = sparse.diags(2 * objective_scale * coefficients, format="csc")
        q = np.zeros(M * J + auxiliary_count)
    else:
        P = sparse.triu(2 * objective_scale * sparse.block_diag(H, format="csc"), format="csc")
        q = objective_scale * np.concatenate(linear)
    centres = (edges[1:] + edges[:-1]) / 2
    equality = sparse.kron(sparse.eye(M, format="csc"), np.vstack([np.ones(J), centres]), format="csc")
    base = sparse.vstack([sparse.eye(M * J, format="csc"), equality], format="csc")
    lower_base = np.r_[np.zeros(M * J), np.ones(2 * M)]
    upper_base = np.ones(M * J + 2 * M)
    if residual_form:
        base = sparse.hstack([base, sparse.csc_matrix((base.shape[0], auxiliary_count))], format="csc")
        residual_equalities = sparse.hstack([residual_map, -sparse.eye(auxiliary_count, format="csc")], format="csc")
        base = sparse.vstack([base, residual_equalities], format="csc")
        lower_base = np.r_[lower_base, target_residual]
        upper_base = np.r_[upper_base, target_residual]
    grids = [list(edges[1:-1]) for _ in range(M - 1)]
    if initial_weights is None:
        start = np.zeros(J)
        j = np.searchsorted(centres, 1.) - 1
        start[j] = (centres[j + 1] - 1) / (centres[j + 1] - centres[j])
        start[j + 1] = 1 - start[j]
        warm = np.tile(start, M)
    else:
        warm = np.asarray(initial_weights, dtype=float)
        if warm.shape != (M, J) or not np.all(np.isfinite(warm)):
            raise ValueError("Warm start must have one finite mass vector per maturity.")
        warm = warm.ravel()
    if residual_form:
        warm = np.r_[warm, residual_map @ warm - target_residual]
    history = []
    for round_index in range(max_rounds if enforce_calendar else 1):
        blocks = [base]
        if enforce_calendar:
            for i, grid in enumerate(grids):
                B = sparse.csc_matrix(payoff_matrix(np.asarray(grid), edges, 1.))
                blocks.append(sparse.hstack([sparse.csc_matrix((len(grid), i * J)), -B, B,
                    sparse.csc_matrix((len(grid), (M - i - 2) * J + auxiliary_count))], format="csc"))
        A_constraint = sparse.vstack(blocks, format="csc")
        n_calendar = A_constraint.shape[0] - base.shape[0]
        lower = np.r_[lower_base, np.zeros(n_calendar)]
        upper = np.r_[upper_base, np.full(n_calendar, np.inf)]
        duality_gap = None
        if solver_backend == "osqp":
            solver = osqp.OSQP()
            solver.setup(P=P, q=q, A=A_constraint, l=lower, u=upper, verbose=False,
                         eps_abs=1e-10, eps_rel=1e-10, max_iter=max_solver_iterations, polishing=True,
                         polish_refine_iter=10, adaptive_rho_interval=50, check_termination=25)
            solver.warm_start(x=warm)
            result = solver.solve(raise_error=False)
            accepted = result.info.status_val == 1
            raw_status, iterations = result.info.status, result.info.iter
            primal, dual = result.info.prim_res, result.info.dual_res
            polish_status, solution = result.info.status_polish, result.x
        else:
            exact = lower == upper
            has_upper = np.isfinite(upper) & ~exact
            has_lower = np.isfinite(lower) & ~exact
            conic_A = sparse.vstack([A_constraint[exact], A_constraint[has_upper], -A_constraint[has_lower]], format="csc")
            conic_b = np.r_[lower[exact], upper[has_upper], -lower[has_lower]]
            cones = [clarabel.ZeroConeT(int(exact.sum())), clarabel.NonnegativeConeT(int(has_upper.sum()+has_lower.sum()))]
            settings = clarabel.DefaultSettings()
            settings.verbose = False
            settings.max_iter = max_solver_iterations
            settings.max_threads = 1
            settings.direct_solve_method = "qdldl"
            settings.tol_gap_abs = settings.tol_gap_rel = settings.tol_feas = 1e-10
            solver = clarabel.DefaultSolver(P, q, conic_A, conic_b, cones, settings)
            result = solver.solve()
            raw_status, iterations = str(result.status), result.iterations
            accepted = raw_status == "Solved"
            primal, dual = result.r_prim, result.r_dual
            polish_status, solution = None, np.asarray(result.x)
            duality_gap = abs(result.obj_val - result.obj_val_dual)
        if not accepted:
            raise RuntimeError(f"{solver_backend} did not solve round {round_index + 1}: {raw_status}; "
                               f"iterations={iterations}, primal={primal:.3g}, dual={dual:.3g}")
        weights = solution[:M * J].reshape(M, J)
        residual_equation_error = (float(np.max(np.abs(residual_equalities @ solution - target_residual)))
                                   if residual_form else 0.)
        if residual_equation_error > 1e-9:
            raise RuntimeError("The explicit residual equations failed their post-solve tolerance.")
        mass_error = float(np.max(np.abs(weights.sum(axis=1) - 1)))
        mean_error = float(np.max(np.abs(weights @ centres - 1)))
        minimum_mass = float(weights.min())
        if max(mass_error, mean_error) > 1e-8 or minimum_mass < -1e-9:
            raise RuntimeError("A marginal constraint failed the post-solve tolerance.")
        # Refine one order tighter than the published acceptance tolerance.
        check, cuts = continuous_calendar_check(edges, weights, calendar_tolerance / 10)
        objective = sum(float(np.mean((A @ w - y) ** 2) + penalty * np.mean((L @ w) ** 2))
                        for A, w, y in zip(matrices, weights, observations))
        history.append({"round": round_index + 1, "calendar_rows": n_calendar,
                        "status": raw_status, "iterations": iterations,
                        "primal_residual": primal, "dual_residual": dual,
                        "polish_status": polish_status, "objective": objective,
                        "scaled_duality_gap": duality_gap,
                        "maximum_residual_equation_error": residual_equation_error,
                        "minimum_calendar_gap": check["minimum_gap"],
                        "maximum_mass_error": mass_error, "maximum_normalised_mean_error": mean_error,
                        "minimum_bin_mass": minimum_mass})
        if not enforce_calendar or check["passes"]:
            break
        added = 0
        for grid, candidates in zip(grids, cuts):
            for point in candidates:
                if min(abs(point - old) for old in grid) > 1e-12:
                    grid.append(point)
                    added += 1
            grid.sort()
        if not added:
            raise RuntimeError("Calendar check failed without a new constraint location.")
        warm = solution
    else:
        raise RuntimeError("Calendar constraint refinement reached its round limit.")
    fits = []
    for w, F, D, A, y in zip(weights, forwards, discounts, matrices, observations):
        loss = float(np.mean((A @ w - y) ** 2) + penalty * np.mean((L @ w) ** 2))
        fits.append(DensityFit(edges * F, w.copy(), D, F, penalty, iterations, loss))
    report = {"name": "OSQP" if solver_backend == "osqp" else "Clarabel",
              "version": osqp.__version__ if solver_backend == "osqp" else clarabel.__version__, "enforce_calendar": bool(enforce_calendar),
              "objective_scale": objective_scale,
              "max_solver_iterations": max_solver_iterations,
              "formulation": "Explicit price and roughness residual variables" if residual_form else "Expanded quadratic in bin weights",
              "stopping_settings": ({"eps_abs": 1e-10, "eps_rel": 1e-10} if solver_backend == "osqp"
                                    else {"tol_gap_abs": 1e-10, "tol_gap_rel": 1e-10, "tol_feas": 1e-10,
                                          "max_threads": 1, "direct_solve_method": "qdldl"}),
              "calendar_tolerance": calendar_tolerance, "objective_sum": objective,
              "refinement_target": calendar_tolerance / 10,
              "refinement_rounds": len(history), "history": history,
              "postprocessing": "No clipping, renormalisation or quote changes"}
    if solver_backend == "osqp":
        report.update(eps_abs=1e-10, eps_rel=1e-10)
    public_check, _ = continuous_calendar_check(edges, weights, calendar_tolerance)
    return JointResult(fits, weights, report, public_check)
