"""Finite-support histogram density fitted by a convex quadratic programme.

Theory: research/constrained_methodology.md, Equations (9)–(12).
This is a project-specific estimator, not the Ait-Sahalia–Duarte algorithm.
"""
from dataclasses import dataclass
import numpy as np
from scipy.optimize import minimize


def payoff_matrix(strikes, edges, discount):
    k=np.asarray(strikes,dtype=float)
    edges=np.asarray(edges,dtype=float)
    if k.ndim!=1 or edges.ndim!=1 or len(edges)<3 or not np.all(np.isfinite(k)) or not np.all(np.isfinite(edges)):
        raise ValueError('Finite one-dimensional strikes and at least three edges required.')
    if np.any(k<0) or np.any(edges<0) or np.any(np.diff(edges)<=0) or not np.isfinite(discount) or discount<=0:
        raise ValueError('Nonnegative levels, increasing edges and positive discount required.')
    a,b=edges[:-1][None,:],edges[1:][None,:]
    # Integrate (s-K)+ exactly under a uniform density in each bin.
    return discount*(np.maximum(b-k[:,None],0)**2-np.maximum(a-k[:,None],0)**2)/(2*(b-a))

@dataclass
class DensityFit:
    edges: np.ndarray
    mass: np.ndarray
    discount: float
    forward: float
    penalty: float
    iterations: int
    objective: float

    def prices(self,strikes):return payoff_matrix(strikes,self.edges,self.discount)@self.mass
    def density(self,levels):
        x=np.asarray(levels,dtype=float)
        if not np.all(np.isfinite(x)):
            raise ValueError('Finite evaluation levels required.')
        i=np.searchsorted(self.edges,x,side='right')-1
        valid=(i>=0)&(i<len(self.mass))
        y=np.zeros_like(x)
        y[valid]=(self.mass/np.diff(self.edges))[i[valid]]
        return y


def fit_density(strikes, prices, forward, discount, edges, penalty=1e-6):
    """Fit price/F residuals plus penalty times squared second density differences.

    Bins must be equal-width. Constraints enforce mass and first moment analytically.
    Tail support, smoothing penalty and forward are explicit input assumptions.
    """
    edges=np.asarray(edges,dtype=float);k=np.asarray(strikes,dtype=float);y=np.asarray(prices,dtype=float)
    if not np.isfinite(forward) or forward<=0 or not np.isfinite(penalty) or penalty<0:
        raise ValueError('Positive forward and nonnegative penalty required.')
    A=payoff_matrix(k,edges,discount)/forward
    if len(edges)<4:
        raise ValueError('At least three density bins are required for the smoothing penalty.')
    widths=np.diff(edges);centres=(edges[1:]+edges[:-1])/2
    if y.shape!=k.shape or len(k)<3 or not np.all(np.isfinite(y)) or np.any(y<0) or np.any(np.diff(k)<=0):
        raise ValueError('At least three sorted distinct strikes and finite nonnegative matching prices required.')
    if not np.allclose(widths,widths[0]) or not centres[0]<forward<centres[-1]:
        raise ValueError('Equal-width bins must bracket the forward with their centres.')
    L=np.diff(np.eye(len(centres)),n=2,axis=0)/(widths[0]/forward)
    H=A.T@A/len(k)+penalty*(L.T@L)/len(L)
    g=A.T@(y/forward)/len(k)
    E=np.vstack([np.ones(len(centres)),centres/forward]);target=np.ones(2)
    # Feasible initial mass on the two centres surrounding the forward.
    i=np.searchsorted(centres,forward)-1;w=np.zeros(len(centres))
    w[i]=(centres[i+1]-forward)/(centres[i+1]-centres[i]);w[i+1]=1-w[i]
    scale=1e6
    result=minimize(lambda w:scale*(w@H@w-2*g@w),w,
        jac=lambda w:2*scale*(H@w-g),method='SLSQP',bounds=[(0,1)]*len(w),
        constraints={'type':'eq','fun':lambda w:E@w-target,'jac':lambda w:E},
        options={'ftol':1e-10,'maxiter':1500})
    if not result.success or np.max(np.abs(E@result.x-target))>1e-8 or np.min(result.x)<-1e-10:
        raise RuntimeError('Constrained optimisation failed: '+result.message)
    residual=A@result.x-y/forward
    objective=float(np.mean(residual**2)+penalty*np.mean((L@result.x)**2))
    return DensityFit(edges,result.x,discount,forward,penalty,result.nit,objective)
