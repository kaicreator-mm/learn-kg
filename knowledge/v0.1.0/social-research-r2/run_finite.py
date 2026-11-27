import json,pathlib,hashlib
from fractions import Fraction as F
P=pathlib.Path(__file__).resolve().parent
def nat(x):return type(x) is int and x>=0
def eval_(mode,x):
 try:
  if mode=='weighted':
   y=x['effect'];se=x['se'];tau=F(str(x['tau2']))
   if len(y)!=len(se) or not y or tau<0 or x.get('same_scale') is not True or x.get('independent') is not True or any(F(str(v))<=0 for v in se):return 'HOLD'
   w=[1/(F(str(v))**2+tau) for v in se]
   return {'weights':[str(z) for z in w],'mean':str(sum(F(str(a))*b for a,b in zip(y,w))/sum(w))}
  if mode=='did':
   a,b=x['treatment'],x['control']
   return {'difference_in_differences':str(F(str(a[1]))-F(str(a[0]))-F(str(b[1]))+F(str(b[0]))),'causal':'CANDIDATE_UNDER_DECLARED_ASSUMPTIONS' if x.get('parallel_trends') is True and x.get('no_other_differential_changes') is True else 'HOLD'}
  if mode=='ate':
   ys=x['potential_mean_diffs'];w=[F(str(v)) for v in x['weights']]
   if x.get('synthetic_potential_means_known') is not True or len(ys)!=len(w) or not w or any(v<0 for v in w) or sum(w)!=1 or any(v is None for v in ys):return 'HOLD'
   return str(sum(F(str(v))*k for v,k in zip(ys,w)))
  if mode=='sampling':
   n,N=x['sample'],x['population'];r=x['responded']
   if not(nat(n) and nat(N) and nat(r) and 0<=r<=n<=N and n>0 and x.get('equal_probability') is True):return 'HOLD'
   return {'weight':str(F(N,n)),'nonresponse':'UNRESOLVED' if r!=n else 'NO_OBSERVED_NONRESPONSE'}
  if mode=='agreement':
   a,n=x['agree'],x['paired'];return str(F(a,n)) if nat(a) and nat(n) and 0<n and a<=n else 'HOLD'
  if mode=='budget':
   b=x['budget'];v=x['planned']
   if not nat(b) or not v or any(not nat(z) for z in v):return 'HOLD'
   return {'cost':sum(v),'feasible':sum(v)<=b,'excess':max(0,sum(v)-b)}
  if mode=='tech':
   if x.get('submitted') is False and x.get('network_failure') is True:return 'UNOBSERVED_TECHNICAL_FAILURE'
   if x.get('submitted') is True and x.get('independent') is True and type(x.get('correct')) is bool:return 'INDEPENDENT_CORRECT' if x['correct'] else 'OBSERVED_INCORRECT'
   return 'HOLD'
  if mode=='source_count':
   v=x['source_ids']
   if not v or any(not isinstance(z,str) or not z.strip() for z in v):return 'HOLD'
   return {'reports':len(v),'distinct_origin_ids':len(set(v)),'independence':'NOT_ESTABLISHED'}
 except (ValueError,TypeError,KeyError,ZeroDivisionError,IndexError):return 'HOLD'
 raise ValueError(mode)
def main():
 f=P/'finite-fixtures.json';xs=json.loads(f.read_text());out=[]
 for x in xs:
  v=eval_(x['mode'],x['input']);assert v==x['expected'],(x['id'],v,x['expected'])
  out.append({'id':x['id'],'actual':v,'expected':x['expected'],'status':'PASS_BUILDER_FINITE_ONLY'})
 (P/'finite-results.json').write_text(json.dumps({'fixture_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'results':out,'limits':'No independent oracle, causal identification, actual learner, or generalized policy runtime.'},ensure_ascii=False,indent=2)+'\n')
 print(len(out),'PASS_BUILDER_FINITE_ONLY')
if __name__=='__main__':main()
