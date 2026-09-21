from pathlib import Path
import sys,json,base64,io,contextlib,html,platform
import numpy as np, scipy, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'src'))
from density import *
p=Parameters(); strikes=np.arange(2500.,14000.1,5.)
calls=call_price(strikes,p); x,f=recover_density(strikes,calls,p.rate,p.maturity)
m=diagnostics(x,f,p)
assert abs(m['mass']-1)<1e-7
assert m['negative_density_count']==0
assert m['integrated_absolute_error']<1e-5
assert m['forward_relative_error']<1e-7
assert m['max_repricing_error_index_points']<0.01
rows=[]
for h in [80,40,20,10,5]:
 k=np.arange(2500.,14000.1,h); xx,ff=recover_density(k,call_price(k,p),p.rate,p.maturity)
 rows.append({'strike_spacing':h,**diagnostics(xx,ff,p)})
assert all(rows[i+1]['integrated_absolute_error']<rows[i]['integrated_absolute_error'] for i in range(4))
(root/'results/validation.json').write_text(json.dumps({'parameters':p.__dict__,'baseline':m,'convergence':rows},indent=2))
np.savetxt(root/'results/recovered_density.csv',np.column_stack([x,f,exact_density(x,p)]),delimiter=',',header='terminal_index_level,recovered_density,exact_density',comments='')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':0.18,'figure.facecolor':'white','savefig.facecolor':'white'})
navy='#17354d'; teal='#008c95'; orange='#c36e24'
def save(fig,name):
 fig.tight_layout()
 fig.savefig(root/f'figures/{name}.png',dpi=180,bbox_inches='tight'); fig.savefig(root/f'figures/{name}.svg',bbox_inches='tight');plt.close(fig)
fig,ax=plt.subplots(figsize=(9,4.8));ax.plot(strikes,calls,color=navy,lw=2);ax.set(xlim=(3000,10000),xlabel='Strike K (index points)',ylabel='Call price (index points)');save(fig,'figure_01_call_prices')
fig,ax=plt.subplots(figsize=(9,4.8));ax.plot(x,exact_density(x,p),color=navy,lw=3,label='Analytical lognormal density');ax.plot(x,f,color=teal,ls='--',lw=1.8,label='Recovered from call-price curvature');ax.axvline(p.forward,color=orange,ls=':',label=f'Forward: {p.forward:,.2f}');ax.set(xlim=(3000,10000),xlabel='Terminal index level (index points)',ylabel='Probability density (per index point)');ax.ticklabel_format(axis='y',style='sci',scilimits=(0,0));ax.legend(frameon=False);save(fig,'figure_02_density_recovery')
fig,ax=plt.subplots(figsize=(9,4.8));hs=np.array([r['strike_spacing'] for r in rows]);es=np.array([r['integrated_absolute_error'] for r in rows]);ax.loglog(hs,es,'o-',color=teal,label='Measured integrated absolute error');ax.loglog(hs,es[-1]*(hs/hs[-1])**2,'--',color=navy,label='Second-order reference');ax.set(xlabel='Strike spacing h (index points)',ylabel='Integrated absolute density error');ax.legend(frameon=False);save(fig,'figure_03_convergence')
rng=np.random.default_rng(42);k=np.arange(3000.,10000.1,20.);c=call_price(k,p);xx,ff=recover_density(k,c+rng.normal(0,.05,len(k)),p.rate,p.maturity)
fig,ax=plt.subplots(figsize=(9,4.8));ax.plot(xx,ff,color=orange,alpha=.75,lw=.9,label='Recovered with independent quote noise');ax.plot(xx,exact_density(xx,p),color=navy,lw=2,label='Analytical density');ax.axhline(0,color='black',lw=.8);ax.set(xlabel='Terminal index level (index points)',ylabel='Density (per index point)');ax.legend(frameon=False);save(fig,'figure_04_noise_sensitivity')
(root/'results/noise_diagnostic.json').write_text(json.dumps({'seed':42,'noise_standard_deviation':.05,'negative_density_fraction':float(np.mean(ff<0))},indent=2))

print(json.dumps(m, indent=2))
print("All baseline and grid-convergence checks passed.")
