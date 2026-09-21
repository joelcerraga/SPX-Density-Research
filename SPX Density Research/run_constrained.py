"""Synthetic validation of constrained density fitting. No market calibration."""
import json
from pathlib import Path
import numpy as np
from scipy.integrate import trapezoid
from scipy.special import ndtr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from src.density import Parameters,call_price,exact_density,recover_density
from src.constrained import fit_density
ROOT=Path(__file__).resolve().parent

def main():
    p=Parameters();F=p.forward;D=np.exp(-p.rate*p.maturity)
    k=np.linspace(.65*F,1.45*F,81);truth=call_price(k,p)
    noisy=truth+np.random.default_rng(2026).normal(0,.5,len(k))
    edges=np.linspace(.3*F,2.2*F,121)
    x=np.linspace(.3*F,2.2*F,20001)
    test_k=(k[:-1]+k[1:])/2
    records=[];fits=[]
    for penalty in [1e-8,1e-6,1e-4]:
        fit=fit_density(k,noisy,F,D,edges,penalty);fits.append(fit)
        c=fit.prices(k);slopes=np.diff(c)/np.diff(k)
        records.append(dict(penalty=penalty,iterations=fit.iterations,
            mass=float(fit.mass.sum()),mean=float(fit.mass@((edges[1:]+edges[:-1])/2)),
            minimum_bin_mass=float(fit.mass.min()),
            noisy_quote_rmse=float(np.sqrt(np.mean((c-noisy)**2))),
            withheld_clean_price_rmse=float(np.sqrt(np.mean((fit.prices(test_k)-call_price(test_k,p))**2))),
            integrated_density_absolute_error=float(trapezoid(np.abs(fit.density(x)-exact_density(x,p)),x)),
            monotonicity_violations=int(np.sum(slopes>1e-8)),convexity_violations=int(np.sum(np.diff(slopes)<-1e-8))))
    fitted=fits[1]
    raw_x,raw_f=recover_density(k,noisy,p.rate,p.maturity)
    v=p.volatility*np.sqrt(p.maturity);mu=np.log(p.spot)+(p.rate-p.dividend-.5*p.volatility**2)*p.maturity
    tail_mass=float(ndtr((np.log(edges[0])-mu)/v)+ndtr(-(np.log(edges[-1])-mu)/v))
    report={'status':'synthetic_only','noise_standard_deviation':.5,'seed':2026,'quote_count':len(k),'bins':120,
      'forward':F,'discount_factor':D,'support':[float(edges[0]),float(edges[-1])],
      'known_density_mass_outside_support':tail_mass,'raw_negative_density_points':int(np.sum(raw_f<0)),
      'baseline_penalty':1e-6,'penalty_selection':'Predeclared illustrative middle setting; not selected by minimising benchmark error',
      'results':records}
    assert all(abs(r['mass']-1)<1e-8 and abs(r['mean']/F-1)<1e-8 and r['minimum_bin_mass']>=-1e-10 and r['monotonicity_violations']==0 and r['convexity_violations']==0 for r in records)
    np.savetxt(ROOT/'results/constrained_density.csv',np.c_[x,exact_density(x,p),fitted.density(x)],delimiter=',',header='terminal_level,known_density,fitted_density',comments='')
    np.savetxt(ROOT/'results/constrained_bin_masses.csv',np.c_[edges[:-1],edges[1:],fitted.mass],delimiter=',',header='left_edge,right_edge,probability_mass',comments='')
    (ROOT/'results/constrained_validation.json').write_text(json.dumps(report,indent=2))
    plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(2,1,figsize=(9,7),constrained_layout=True,sharex=True)
    axes[0].plot(k,truth,label='Known theoretical price',color='#16364c');axes[0].scatter(k,noisy,s=10,label='Synthetic noisy quote',color='#cf8b51');axes[0].plot(k,fitted.prices(k),'--',label='Constrained fit',color='#218a87');axes[0].set_ylabel('Call price (index points)');axes[0].legend()
    axes[1].scatter(k,noisy-truth,s=12,label='Noise added',color='#cf8b51');axes[1].plot(k,fitted.prices(k)-truth,label='Fit minus known price',color='#218a87');axes[1].axhline(0,color='black',lw=.6);axes[1].set_ylabel('Price difference (index points)');axes[1].set_xlabel('Strike (index points)');axes[1].legend()
    save(fig,7,'constrained_prices')
    fig,ax=plt.subplots(figsize=(9,5),constrained_layout=True)
    ax.plot(raw_x,raw_f,color='#cf8b51',alpha=.65,label='Raw second differences of noisy prices');ax.plot(x,exact_density(x,p),color='#16364c',lw=2,label='Known lognormal density');ax.stairs(fitted.mass/np.diff(edges),edges,color='#218a87',label='Constrained histogram density');ax.set_xlim(.6*F,1.6*F);ax.axhline(0,color='black',lw=.6);ax.set_xlabel('Terminal index level (index points)');ax.set_ylabel('Density (per index point)');ax.legend();save(fig,8,'constrained_density')
    fig,ax=plt.subplots(figsize=(9,5),constrained_layout=True)
    ax.plot(x,exact_density(x,p),color='black',ls='--',label='Known lognormal density')
    for fit in fits:ax.stairs(fit.mass/np.diff(edges),edges,label=f'Penalty = {fit.penalty:g}')
    ax.set_xlim(.6*F,1.6*F);ax.set_xlabel('Terminal index level (index points)');ax.set_ylabel('Density (per index point)');ax.legend();save(fig,9,'smoothing_sensitivity')
    print(json.dumps(report,indent=2));return report

def save(fig,n,name):
    for ext in ['png','svg']:fig.savefig(ROOT/f'figures/figure_{n:02}_{name}.{ext}',dpi=180)
    plt.close(fig)

if __name__=='__main__':main()
