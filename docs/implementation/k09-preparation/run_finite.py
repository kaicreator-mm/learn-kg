"""Exact finite synthetic measurement discriminations; not calibration or learner assessment."""
import json,math,pathlib,hashlib
from fractions import Fraction as F
P=pathlib.Path(__file__).resolve().parent
def need(x):
 if not x:raise ValueError()
def n(x):
 need(type(x) is int and x>=0);return x
def q(x):
 need(type(x) in (int,str,float));return F(str(x))
def ratio(x,y):need(y>0 and 0<=x<=y);return F(x,y)
def p(x):x=q(x);need(0<=x<=1);return x
def bits(x):need(isinstance(x,list) and x and all(type(k) is int and k in (0,1) for k in x));return x
def logistic(x):
 x=float(x)
 return 1/(1+math.exp(-x)) if x>=0 else math.exp(x)/(1+math.exp(x))
def go(op,x):
 try:
  if op=='score':
   a,b=x['scores'],x['max'];need(len(a)==len(b)>0 and x['policy'] in ('EXCLUDE_MISSING','ZERO_MISSING'))
   need(all(n(k)>0 for k in b) and all(v is None or n(v)<=m for v,m in zip(a,b)))
   d=sum(m for v,m in zip(a,b) if v is not None or x['policy']=='ZERO_MISSING');return {'score':str(ratio(sum(v for v in a if v is not None),d)),'missing':a.count(None)}
  if op=='ordinal':
   a,b=x['x'],x['y'];need(len(a)==len(b)>=3 and all(y>z for z,y in zip(a,a[1:])))
   need(all(y>z for z,y in zip(b,b[1:])))
   return {'preserves_order':True,'preserves_equal_gaps':len(set(y-z for z,y in zip(a,a[1:])))==len(set(y-z for z,y in zip(b,b[1:])))==1}
  if op=='reliability':
   a,b=q(x['true_var']),q(x['error_var']);need(x['assumptions_met'] is True and a>=0 and b>=0 and a+b>0);return str(a/(a+b))
  if op=='difficulty':
   a,b,c=(n(x[k]) for k in ('correct','incorrect','missing'));return {'p':str(ratio(a,a+b)),'missing_rate':str(ratio(c,a+b+c))}
  if op=='discrimination':
   a,b=map(n,x['hi']);c,d=map(n,x['lo']);return str(ratio(a,b)-ratio(c,d))
  if op=='total':
   a,b=bits(x['a']),bits(x['b']);need(len(a)==len(b));return {'a':sum(a),'b':sum(b),'same_pattern':a==b}
  if op=='sem':
   a,r=q(x['sd']),p(x['r']);need(a>=0 and x['matched'] is True);return float(a)*math.sqrt(float(1-r))
  if op=='irt':
   a,c=q(x['a']),p(x['c']);need(a>0 and c<1);return float(c)+(1-float(c))*logistic(a*(q(x['theta'])-q(x['b'])))
  if op=='rasch_mle':
   a,b=n(x['correct']),n(x['total']);need(0<b and a<=b);return 'NO_FINITE_UNCONSTRAINED_MLE' if a in (0,b) else 'INTERIOR_COUNT_NOT_ESTIMATED'
  if op=='multidim':
   a,b=x['a'],x['theta'];need(len(a)==len(b)>0);return logistic(sum(q(u)*q(v) for u,v in zip(a,b))+q(x['d']))
  if op=='information':
   a,b=x['a2'],x['p'];need(x['local_independent'] is True and len(a)==len(b)>0 and all(q(v)>0 for v in a));return str(sum(q(u)*p(v)*(1-p(v)) for u,v in zip(a,b)))
  if op in ('dina','q_signature'):
   def ideal(a,b):
    a,b=bits(a),bits(b);need(len(a)==len(b) and any(a));return int(all(not k or v for k,v in zip(a,b)))
   if op=='dina':
    s,g=p(x['s']),p(x['g']);need(1-s>g);return str(1-s if ideal(x['q'],x['alpha']) else g)
   a=[ideal(z,x['a']) for z in x['q']];b=[ideal(z,x['b']) for z in x['q']];need(a and b);return {'a':a,'b':b,'distinguishable':a!=b}
  if op=='cat_select':
   a=x['items'];need(isinstance(a,list) and len({z['id'] for z in a})==len(a) and all(type(z['eligible']) is bool and q(z['info'])>=0 for z in a));eligible=[z for z in a if z['eligible']]
   return min(eligible,key=lambda z:(-q(z['info']),z['id']))['id'] if eligible else 'NO_ELIGIBLE_ITEM'
  if op=='cat_stop':
   a,b=q(x['se']),q(x['target']);c,d=n(x['count']),n(x['maximum']);e=x['content_complete'];need(0<=a and b>0 and 0<d and c<=d and type(e) is bool)
   if a<=b and e:return 'STOP_CRITERIA_MET'
   if c==d:return 'STOP_LIMIT_PRECISION_NOT_MET' if a>b and e else 'STOP_LIMIT_OTHER_CRITERIA_NOT_MET'
   return 'CONTINUE_CONTENT' if not e else 'CONTINUE_PRECISION'
  if op=='kappa':
   a,b=x['table'];a,b=list(map(n,a)),list(map(n,b));need(len(a)==len(b)==2);t=sum(a+b);need(t>0)
   po=F(a[0]+b[1],t);pe=F(sum(a)*(a[0]+b[0])+sum(b)*(a[1]+b[1]),t*t)
   return {'po':str(po),'pe':str(pe),'kappa':str((po-pe)/(1-pe)) if pe!=1 else 'UNDEFINED'}
  if op=='screen':
   a,b,c,d=(n(x[k]) for k in ('tp','fn','tn','fp'));need(x['reference_valid'] is True);return {'se':str(ratio(a,a+b)),'sp':str(ratio(c,c+d)),'ppv':str(ratio(a,a+d))}
  if op=='link':
   a,b,c,d,v=(q(x[k]) for k in ('mux','sx','muy','sy','x'));need(x['matched'] is True and b>0 and d>0);return str(c+(v-a)*d/b)
  raise RuntimeError(op)
 except (ValueError,TypeError,KeyError,ZeroDivisionError,OverflowError):return 'HOLD'
def main():
 f=P/'finite-fixtures.json';rows=json.loads(f.read_text());out=[]
 for i,z in enumerate(rows):
  actual=go(z['op'],z['input']);expected=z['expected']
  ok=math.isclose(actual,expected,rel_tol=1e-12,abs_tol=1e-12) if type(actual) in (int,float) and type(expected) in (int,float) else actual==expected
  assert ok,(i,z,actual);out.append({'id':i,'topic':z['topic'],'actual':actual,'expected':expected,'status':'PASS_BUILDER_FINITE_ONLY'})
 (P/'finite-results.json').write_text(json.dumps({'fixture_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'results':out},ensure_ascii=False,indent=2)+'\n')
 print(len(out),'PASS_MEASUREMENT_FINITE_ONLY')
if __name__=='__main__':main()
