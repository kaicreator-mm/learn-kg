"""Synthetic calculations and decision guards, never empirical estimation."""
import pathlib,json,hashlib,math
from fractions import Fraction as F
P=pathlib.Path(__file__).resolve().parent
def need(x):
 if not x:raise ValueError('domain')
def n(x):
 need(type(x) in (int,float,str));return F(str(x))
def prob(x):
 p=n(x);need(0<=p<=1);return p
def dist(x):
 need(isinstance(x,list) and x);v=[prob(y) for y in x];need(sum(v)==1);return v
def ids(x):
 need(isinstance(x,list) and all(isinstance(z,str) and z.strip() for z in x));return set(x)
def evaluate(m,x):
 try:
  if m=='bkt':
   p,s,g,t=[prob(x[k]) for k in ('p','s','g','t')]
   need(x.get('matching_observation') is True and type(x.get('correct')) is bool and x.get('transition')=='NO_FORGETTING_AFTER_OBSERVATION')
   a,b=(1-s,g) if x['correct'] else (s,1-g)
   e=p*a+(1-p)*b;need(e>0);q=p*a/e
   return {'likelihood':str(e),'posterior':str(q),'next_prior':str(q+(1-q)*t)}
  if m=='hlr':
   h,lag=n(x['half_life']),n(x['lag']);need(h>0 and lag>=0 and x.get('matched_unit') is True)
   return round(2**(-float(lag/h)),12)
  if m=='threshold':
   h,p=n(x['half_life']),prob(x['target']);need(h>0 and 0<p<1 and x.get('fixed_h') is True)
   return round(-float(h)*math.log2(float(p)),12)
  if m=='brier':
   p,y=x['p'],x['y'];need(isinstance(p,list) and isinstance(y,list) and len(p)==len(y)>0 and all(type(z) is int and z in (0,1) for z in y) and x.get('same_target') is True)
   return str(sum((prob(a)-b)**2 for a,b in zip(p,y))/len(p))
  if m=='auc':
   a,b=[x[k] for k in ('positive','negative')];need(isinstance(a,list) and isinstance(b,list) and a and b and x.get('same_target') is True)
   u,v=[n(z) for z in a],[n(z) for z in b]
   return str(sum(F(int(i>j))+F(int(i==j),2) for i in u for j in v)/(len(u)*len(v)))
  if m=='discount':
   gamma=prob(x['gamma']);r=x['rewards'];need(isinstance(r,list) and r and x.get('same_unit') is True)
   return str(sum(gamma**i*n(v) for i,v in enumerate(r)))
  if m=='belief':
   b=dist(x['belief']);t=x['transition'];o=x['likelihood'];need(len(t)==len(o)==len(b) and all(len(row)==len(b) for row in t))
   t=[dist(row) for row in t];o=[prob(v) for v in o];w=[o[j]*sum(b[i]*t[i][j] for i in range(len(b))) for j in range(len(b))]
   need(sum(w)>0);return [str(v/sum(w)) for v in w]
  if m=='ips':
   rows=x['rows'];need(isinstance(rows,list) and rows and x.get('support_verified') is True and x.get('single_step') is True and x.get('same_reward') is True)
   v=[]
   for r in rows:
    pi,mu=prob(r['pi']),prob(r['mu']);need(mu>0);v.append(pi/mu*n(r['reward']))
   return str(sum(v)/len(v))
  if m=='coverage':
   return sorted((ids(x['task'])&ids(x['goal']))-ids(x['covered']))
  if m=='selection':
   if x.get('exit') is True:return 'STOP'
   need(x.get('exit') is False)
   if x.get('authorized') is False:return 'REFUSE'
   need(x.get('authorized') is True and x.get('applicable') is True)
   budget,cost=n(x['budget']),n(x['cost']);need(budget>=0 and cost>=0)
   return 'SUGGEST' if cost<=budget else 'DEFER'
  if m=='choice':
   if x.get('version_match') is not True:return 'HOLD'
   a,b,c=x['options'],x['response'],x['correct'];opt=ids(a);res=ids(b);key=ids(c)
   maxc=x['max_choices'];need(len(opt)==len(a)>0 and len(res)==len(b) and len(key)==len(c)>0 and res<=opt and key<=opt and type(maxc) is int and maxc>=0)
   if x.get('cardinality')=='single':need(maxc==1 and len(key)==1 and len(res)<=1)
   elif x.get('cardinality')=='multiple':need(maxc==0 or len(res)<=maxc and len(key)<=maxc)
   else:return 'HOLD'
   if not res:return 'MISSING'
   need(x.get('scoring')=='EXACT_SET')
   return int(res==key)
  if m=='numeric_response':
   need(x.get('rule')=='EXACT_RATIONAL' and x.get('version_match') is True)
   if x.get('response') is None:return 'MISSING'
   return int(n(x['response'])==n(x['key']))
  if m=='counterexample':
   need(x.get('claim')=='ALL_POSITIVE_INTEGERS_EVEN' and type(x['n']) is int and x['n']>0)
   return 'REFUTES' if x['n']%2 else 'NO_COUNTEREXAMPLE'
  if m=='rectangle':
   a,b=n(x['a']),n(x['b']);need(a>0 and b>0 and x.get('unit')=='CM')
   return str(a*b)
  if m=='source_gate':
   if x.get('conflict') is not False:return 'HOLD'
   return 'REVIEW_CANDIDATE' if all(x.get(k) is True for k in ('source_observed','claim_matches','rights_checked','human_review')) else 'HOLD'
  if m=='version':
   return 'HISTORICAL_SCORE_ONLY' if x.get('response_version')==x.get('scoring_version') and isinstance(x.get('response_version'),str) and bool(x['response_version'].strip()) else 'HOLD'
  if m=='info':
   b=dist(x['belief']);lik=x['likelihood'];need(x.get('static_state') is True and len(b)==len(lik) and len(b)==2)
   l=[prob(v) for v in lik]
   def H(p):return -sum(float(v)*math.log2(float(v)) for v in p if v>0)
   value=H(b)
   for o in (l,[1-v for v in l]):
    w=[a*c for a,c in zip(b,o)];z=sum(w)
    if z:value-=float(z)*H([v/z for v in w])
   return round(value,12)
 except (ValueError,TypeError,KeyError,ZeroDivisionError,OverflowError,IndexError):return 'HOLD'
 raise ValueError(m)
def main():
 f=P/'finite-fixtures.json';a=json.loads(f.read_text());out=[]
 for r in a:
  v=evaluate(r['mode'],r['input']);assert v==r['expected'],(r['id'],v,r['expected']);out.append({'id':r['id'],'actual':v,'expected':r['expected'],'status':'PASS_BUILDER_FINITE_ONLY'})
 (P/'finite-results.json').write_text(json.dumps({'fixture_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'results':out,'limits':'Author finite synthetic cases; no independent result, model fit, real learning, external action or formal professional qualification.'},ensure_ascii=False,indent=2)+'\n')
 print(len(out),'PASS_BUILDER_FINITE_ONLY')
if __name__=='__main__':main()
