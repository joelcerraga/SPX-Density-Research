"""Initial Notebook 10 feasibility diagnostic, prior to final fit design."""
import json,time
from pathlib import Path
import numpy as np
from scipy import sparse
from scipy.optimize import linprog
from src.marking import audit_file,infer_carry
from src.constrained import payoff_matrix
from src.joint import continuous_calendar_check
P=Path(__file__).resolve().parent

def solve(groups,edges,calendar=True):
 carry=[infer_carry(g.pairs) for g in groups];M=len(groups);J=len(edges)-1
 mats=[];lo=[];hi=[]
 for g,c in zip(groups,carry):
  k=np.array([p.strike for p in g.pairs]);D,F=c['discount'],c['forward'];parity=D*(F-k)
  mats.append(sparse.csc_matrix(D*F*payoff_matrix(k/F,edges,1.)))
  lo.extend(np.maximum([p.call['bid'] for p in g.pairs],np.array([p.put['bid'] for p in g.pairs])+parity))
  hi.extend(np.minimum([p.call['ask'] for p in g.pairs],np.array([p.put['ask'] for p in g.pairs])+parity))
 A=sparse.block_diag(mats,format='csc');ones=sparse.csc_matrix(np.ones((len(lo),1)))
 C=sparse.vstack([sparse.hstack([A,-ones]),sparse.hstack([-A,-ones])],format='csc');rhs=np.r_[hi,-np.array(lo)]
 E=sparse.hstack([sparse.kron(sparse.eye(M),np.vstack([np.ones(J),(edges[:-1]+edges[1:])/2])),sparse.csc_matrix((2*M,1))],format='csc')
 grids=[list(edges[1:-1]) for _ in range(M-1)];history=[]
 for run in range(25):
  blocks=[C]
  if calendar:
   for i,grid in enumerate(grids):
    B=sparse.csc_matrix(payoff_matrix(np.array(grid),edges,1.))
    blocks.append(sparse.hstack([sparse.csc_matrix((len(grid),i*J)),B,-B,sparse.csc_matrix((len(grid),(M-i-2)*J+1))]))
  AA=sparse.vstack(blocks,format='csc');b=np.r_[rhs,np.zeros(AA.shape[0]-len(rhs))]
  result=linprog(np.r_[np.zeros(M*J),1.],A_ub=AA,b_ub=b,A_eq=E,b_eq=np.ones(2*M),bounds=(0,None),method='highs',options={'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9})
  if not result.success:raise RuntimeError(result.message)
  w=result.x[:-1].reshape(M,J);gap,cuts=continuous_calendar_check(edges,w,1e-9)
  history.append({'round':run+1,'minimum_widening_points':result.fun,'calendar_gap':gap['minimum_gap']})
  if not calendar or gap['passes']:break
  added=0
  for grid,new in zip(grids,cuts):
   for v in new:
    if min(abs(v-x) for x in grid)>1e-12:grid.append(v);added+=1
  if not added:raise RuntimeError('No new cuts')
 else:raise RuntimeError('Refinement limit')
 return {'minimum_widening_points':result.fun,'weights':w.tolist(),'carry':carry,'history':history,'calendar':gap,'maximum_lp_inequality_error':float(max(0,np.max(AA@result.x-b)))}

def main():
 out=[];start=time.monotonic()
 for name in ['eom_marking_prices_list.csv','eod_marking_prices_list.csv','eod_marking_prices_late_list.csv']:
  groups,audit=audit_file(P/'data/raw/marking_prices'/name)
  for bins,calendar in [(120,False),(120,True),(240,True)]:
   t=time.monotonic();rec={'file':name,'bins':bins,'enforce_calendar':calendar}
   try:rec.update(solve(groups,np.linspace(.3,2.2,bins+1),calendar));rec['status']='solved'
   except Exception as e:rec['status']='failed';rec['error']=str(e)
   rec['elapsed_seconds']=time.monotonic()-t;out.append(rec)
   print({k:v for k,v in rec.items() if k not in ['weights','carry','history','calendar']},flush=True)
   (P/'results/comparison_feasibility_pilot.json').write_text(json.dumps({'purpose':'Initial feasibility pilot; not final study protocol','cases':out,'elapsed_seconds':time.monotonic()-start},indent=2)+'\n')
 return out
if __name__=='__main__':main()
