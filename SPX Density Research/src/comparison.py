"""Quote-constrained densities and descriptive comparisons for Notebook 10.

No changes to the preceding estimators, quotes, carry rule or saved notebooks.
All-spread compatibility is conditional on inferred carry and finite support.
"""
from dataclasses import dataclass
import numpy as np
import clarabel
from scipy import sparse
from scipy.optimize import linprog

from src.constrained import DensityFit,payoff_matrix
from src.joint import continuous_calendar_check
from src.marking import infer_carry

EDGES=np.linspace(.3,2.2,241)
CALENDAR_TOL=1e-8
PRICE_TOL=1e-7
LP_PRICE_TOL=2e-6


@dataclass
class Problem:
    groups: tuple
    edges: np.ndarray
    carry: list
    price_map: object
    lower: np.ndarray
    upper: np.ndarray
    equality: object

    @property
    def M(self):return len(self.groups)
    @property
    def J(self):return len(self.edges)-1


def make_problem(groups,edges=EDGES,carry=None):
    edges=np.asarray(edges,float)
    if (len(groups)<2 or len(edges)<4 or not np.all(np.isfinite(edges))
            or np.any(np.diff(edges)<=0) or edges[0]<0
            or not np.allclose(np.diff(edges),np.diff(edges)[0],rtol=1e-10,atol=1e-14)
            or np.any(np.diff([g.maturity for g in groups])<=0)):
        raise ValueError('Increasing maturities and nonnegative equal-width bins required.')
    centres=(edges[:-1]+edges[1:])/2
    if not centres[0]<1<centres[-1]:raise ValueError('Bin centres must bracket the unit mean.')
    carry=[infer_carry(g.pairs) for g in groups] if carry is None else carry
    if len(carry)!=len(groups):raise ValueError('One carry record per horizon required.')
    matrices=[];lower=[];upper=[]
    for g,c in zip(groups,carry):
        k=np.array([p.strike for p in g.pairs]);F,D=c['forward'],c['discount']
        if len(k)<3 or np.any(np.diff(k)<=0) or not np.isfinite(F*D) or min(F,D)<=0:
            raise ValueError('Sorted distinct pairs and positive finite carry required.')
        parity=D*(F-k)
        matrices.append(sparse.csc_matrix(D*F*payoff_matrix(k/F,edges,1.)))
        lo=np.maximum([p.call['bid'] for p in g.pairs],np.array([p.put['bid'] for p in g.pairs])+parity)
        hi=np.minimum([p.call['ask'] for p in g.pairs],np.array([p.put['ask'] for p in g.pairs])+parity)
        if not np.all(np.isfinite(np.r_[lo,hi])):raise ValueError('Finite quote bounds required.')
        lower.extend(lo);upper.extend(hi)
    E=sparse.kron(sparse.eye(len(groups),format='csc'),np.vstack([np.ones(len(centres)),centres]),format='csc')
    return Problem(tuple(groups),edges.copy(),carry,sparse.block_diag(matrices,format='csc'),np.array(lower),np.array(upper),E)


def calendar_matrix(p,grids):
    blocks=[]
    for i,grid in enumerate(grids):
        B=sparse.csc_matrix(payoff_matrix(np.asarray(grid),p.edges,1.))
        blocks.append(sparse.hstack([sparse.csc_matrix((len(grid),i*p.J)),B,-B,
                                    sparse.csc_matrix((len(grid),(p.M-i-2)*p.J))],format='csc'))
    return sparse.vstack(blocks,format='csc')


def add_cuts(grids,cuts):
    added=0
    for grid,candidates in zip(grids,cuts):
        for x in candidates:
            if min(abs(x-old) for old in grid)>1e-12:grid.append(float(x));added+=1
        grid.sort()
    return added


def constraint_summary(p,w):
    flat=np.asarray(w).ravel();prices=p.price_map@flat
    return {'maximum_mass_error':float(np.max(np.abs(w.sum(axis=1)-1))),
        'maximum_mean_error':float(np.max(np.abs(w@((p.edges[:-1]+p.edges[1:])/2)-1))),
        'minimum_mass':float(w.min()),
        'maximum_spread_distance_points':float(max(0,np.max(p.lower-prices),np.max(prices-p.upper)))}


def linear_extreme(p,coefficients=None,maximise=False,allow_widening=False,max_rounds=30):
    """LP over the same full-interval calendar constraints, refined analytically.

    If allow_widening, minimise a single nonnegative point widening; never apply
    that widening to a fit. Otherwise maximise/minimise the given linear risk.
    """
    n=p.M*p.J
    c=np.zeros(n) if coefficients is None else np.asarray(coefficients,float).ravel()
    if c.shape!=(n,) or not np.all(np.isfinite(c)):raise ValueError('One finite coefficient per weight required.')
    if allow_widening and coefficients is not None:raise ValueError('Widening has its own objective.')
    if maximise:c=-c
    grids=[list(p.edges[1:-1]) for _ in range(p.M-1)];history=[]
    for iteration in range(max_rounds):
        C=calendar_matrix(p,grids)
        A=sparse.vstack([p.price_map,-p.price_map,C],format='csc')
        b=np.r_[p.upper,-p.lower,np.zeros(C.shape[0])]
        E=p.equality;cost=c
        if allow_widening:
            A=sparse.hstack([A,sparse.csc_matrix(np.r_[-np.ones(2*len(p.lower)),np.zeros(C.shape[0])][:,None])],format='csc')
            E=sparse.hstack([E,sparse.csc_matrix((E.shape[0],1))],format='csc');cost=np.r_[np.zeros(n),1.]
        result=linprog(cost,A_ub=A,b_ub=b,A_eq=E,b_eq=np.ones(2*p.M),bounds=(0,None),method='highs',
            options={'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9})
        if not result.success:
            return {'status':'infeasible' if result.status==2 else 'solver_failure','solver_status':result.status,
                    'message':result.message,'history':history}
        w=result.x[:n].reshape(p.M,p.J);check,cuts=continuous_calendar_check(p.edges,w,CALENDAR_TOL/10)
        diagnostics=constraint_summary(p,w)
        widening=float(result.x[-1]) if allow_widening else 0.
        excess=max(diagnostics['maximum_spread_distance_points']-widening,0.)
        if (excess>LP_PRICE_TOL or diagnostics['maximum_mass_error']>1e-8
                or diagnostics['maximum_mean_error']>1e-8 or diagnostics['minimum_mass']<-1e-9):
            raise RuntimeError(f'LP returned an unacceptable primal residual: {diagnostics}')
        history.append({'round':iteration+1,'status':int(result.status),'iterations':int(result.nit),
            'objective':float(result.fun),'calendar_rows':C.shape[0],'minimum_calendar_gap':check['minimum_gap'],
            'maximum_inequality_error':float(max(0,np.max(A@result.x-b))),**diagnostics})
        if check['passes']:break
        if not add_cuts(grids,cuts):raise RuntimeError('LP calendar refinement found no new location.')
    else:raise RuntimeError('LP calendar refinement limit reached.')
    value=widening if allow_widening else float(np.asarray(coefficients).ravel()@w.ravel()) if coefficients is not None else 0.
    dual_value=float(b@result.ineqlin.marginals+np.ones(2*p.M)@result.eqlin.marginals)
    return {'status':'solved','value':value,'allow_widening':allow_widening,'maximise':maximise,
        'weights':w.tolist(),'history':history,'calendar':continuous_calendar_check(p.edges,w)[0],
        'primal_dual_objective_gap':abs(float(result.fun)-dual_value),'constraint_summary':diagnostics,
        'price_tolerance_points':LP_PRICE_TOL,'interpretation':'Conditional finite-support feasible set; not a statistical interval or executable-arbitrage claim.'}


def fit_spreads(p,max_rounds=30,max_iterations=300,objective_scale=1.,normalise_quotes=True,quote_row_multiplier=1.):
    """Least discrete curvature subject to ORIGINAL call and put spread bounds."""
    n=p.M*p.J;h=p.edges[1]-p.edges[0]
    L=sparse.csc_matrix(np.diff(np.eye(p.J),n=2,axis=0)/h)
    R=sparse.kron(sparse.eye(p.M,format='csc'),L,format='csc');nr=R.shape[0]
    # Explicit residuals avoid forming a squared condition number in R.T @ R.
    P=sparse.diags(np.r_[np.zeros(n),np.full(nr,2*objective_scale/(p.J-2))],format='csc')
    q=np.zeros(n+nr)
    E=sparse.vstack([sparse.hstack([p.equality,sparse.csc_matrix((2*p.M,nr))]),
                     sparse.hstack([R,-sparse.eye(nr,format='csc')])],format='csc')
    target=np.r_[np.ones(2*p.M),np.zeros(nr)]
    grids=[list(p.edges[1:-1]) for _ in range(p.M-1)];history=[]
    if not np.isfinite(quote_row_multiplier) or quote_row_multiplier<=0:raise ValueError('Positive row scale required.')
    quote_scale=quote_row_multiplier*np.concatenate([np.full(len(g.pairs),1/c['forward'] if normalise_quotes else 1.)
                                for g,c in zip(p.groups,p.carry)])
    quote_map=sparse.diags(quote_scale,format='csc')@p.price_map
    for iteration in range(max_rounds):
        C=calendar_matrix(p,grids)
        inequalities=sparse.vstack([-sparse.eye(n,format='csc'),quote_map,-quote_map,C],format='csc')
        inequalities=sparse.hstack([inequalities,sparse.csc_matrix((inequalities.shape[0],nr))],format='csc')
        A=sparse.vstack([E,inequalities],format='csc')
        b=np.r_[target,np.zeros(n),p.upper*quote_scale,-p.lower*quote_scale,np.zeros(C.shape[0])]
        settings=clarabel.DefaultSettings();settings.verbose=False;settings.max_iter=max_iterations
        settings.max_threads=1;settings.direct_solve_method='qdldl'
        settings.tol_gap_abs=settings.tol_gap_rel=settings.tol_feas=1e-11
        solution=clarabel.DefaultSolver(P,q,A,b,[clarabel.ZeroConeT(len(target)),clarabel.NonnegativeConeT(len(b)-len(target))],settings).solve()
        status=str(solution.status)
        if status!='Solved':
            return {'status':'infeasible' if status=='PrimalInfeasible' else 'solver_failure',
                'solver_status':status,'iterations':solution.iterations,'history':history,
                'primal_residual':solution.r_prim,'dual_residual':solution.r_dual}
        x=np.asarray(solution.x);w=x[:n].reshape(p.M,p.J)
        diagnostics=constraint_summary(p,w);residual_error=float(np.max(np.abs(E@x-target)))
        check,cuts=continuous_calendar_check(p.edges,w,CALENDAR_TOL/10)
        if (diagnostics['maximum_spread_distance_points']>PRICE_TOL or diagnostics['maximum_mass_error']>1e-8
                or diagnostics['maximum_mean_error']>1e-8 or diagnostics['minimum_mass']<-1e-9 or residual_error>1e-8):
            return {'status':'postcheck_failure','solver_status':status,'history':history,
                'constraint_summary':diagnostics,'maximum_residual_equation_error':residual_error,
                'candidate_weights':w.tolist(),'reason':'Strict solver status did not pass independent physical-price or probability checks.'}
        history.append({'round':iteration+1,'status':status,'iterations':solution.iterations,
            'primal_residual':solution.r_prim,'dual_residual':solution.r_dual,'scaled_duality_gap':abs(solution.obj_val-solution.obj_val_dual),
            'calendar_rows':C.shape[0],'minimum_calendar_gap':check['minimum_gap'],
            'maximum_residual_equation_error':residual_error,**diagnostics})
        if check['passes']:break
        if not add_cuts(grids,cuts):raise RuntimeError('QP calendar refinement found no new location.')
    else:raise RuntimeError('QP calendar refinement limit reached.')
    roughness=float(np.sum((R@w.ravel())**2)/(p.J-2))
    fits=[DensityFit(p.edges*c['forward'],mass.copy(),c['discount'],c['forward'],0.,solution.iterations,roughness)
          for mass,c in zip(w,p.carry)]
    return {'status':'solved','weights':w.tolist(),'edges_normalised':p.edges.tolist(),'carry':p.carry,
        'history':history,'calendar':continuous_calendar_check(p.edges,w)[0],'constraint_summary':diagnostics,
        'roughness_objective':roughness,'solver':{'name':'Clarabel','formulation':'Explicit roughness residuals and hard original call/put spread bounds',
            'objective_scale':objective_scale,'quote_row_coordinates':'C/F' if normalise_quotes else 'Index points',
            'quote_row_multiplier':quote_row_multiplier,
            'tolerance':1e-11,'max_iterations':max_iterations,'postprocessing':'None'},'_fits':fits}


def tail_coefficients(edges,threshold,upper=False):
    edges=np.asarray(edges,float)
    if not np.isfinite(threshold):raise ValueError('Finite threshold required.')
    fraction=np.clip((threshold-edges[:-1])/np.diff(edges),0.,1.)
    return 1-fraction if upper else fraction


def interpolation_weights(groups,days=60.):
    times=np.array([g.maturity*365 for g in groups])
    if not np.isfinite(days) or days<times[0] or days>times[-1]:raise ValueError('Common horizon must be bracketed; no extrapolation.')
    weights=np.zeros(len(times))
    if days in times:weights[np.flatnonzero(times==days)[0]]=1.
    else:
        j=np.searchsorted(times,days)-1;theta=(days-times[j])/(times[j+1]-times[j])
        weights[j]=1-theta;weights[j+1]=theta
    return weights


def common_horizon(groups,weights,edges,days=60.):
    a=interpolation_weights(groups,days);mass=a@np.asarray(weights)
    centres=(edges[:-1]+edges[1:])/2
    return {'days':days,'maturity_weights':a.tolist(),'mass':mass.tolist(),'edges_normalised':np.asarray(edges).tolist(),
        'risk':{'below_0_8_forward':float(mass@tail_coefficients(edges,.8)),
            'above_1_2_forward':float(mass@tail_coefficients(edges,1.2,True)),
            'above_1_8_forward':float(mass@tail_coefficients(edges,1.8,True)),
            'normalised_mean':float(mass@centres),
            'normalised_variance':float(mass@((edges[:-1]**2+edges[:-1]*edges[1:]+edges[1:]**2)/3)-(mass@centres)**2)},
        'interpretation':'Linear interpolation of forward-normalised distributions in elapsed time; assumed, not directly observed.'}
