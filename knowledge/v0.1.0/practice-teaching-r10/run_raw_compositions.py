"""Execute four finite raw-observation contracts. No external learning state or execution."""
import copy,hashlib,json,pathlib
from fractions import Fraction
P=pathlib.Path(__file__).resolve().parent
def need(x):
 if not x: raise ValueError('invalid')
def nat(x): return type(x) is int and x>=0
def txt(x): return isinstance(x,str) and bool(x.strip())
def decision(action,reason,**kw):return {'action':action,'reason':reason,**kw}
def observation(x):
 need(all(txt(x.get(k)) for k in ('target','observed_target')) and x['target']==x['observed_target'])
 need(x.get('independent') is True and ('tools_allowed' not in x or x['tools_allowed'] is True))
 c,n,m=x.get('correct'),x.get('total'),x.get('min_samples')
 need(nat(c) and nat(n) and nat(m) and 0<m<=n and c<=n)
 need(type(x.get('criterion')) is str)
 t=Fraction(x['criterion']);need(0<=t<=1)
 return Fraction(c,n),t
def evaluate(mode,x):
 if mode=='compare':
  try:
   a,b=x['a'],x['b']
   for y in (a,b):
    need(all(txt(y.get(k)) for k in ('target','material','format','strategy')))
    need(all(nat(y.get(k)) for k in ('opportunities','delay_days','correct','total')) and y['total']>0 and y['opportunities']>0 and y['correct']<=y['total'])
    need(type(y.get('independent')) is bool)
  except (KeyError,TypeError,ValueError):return decision('CLARIFY','INVALID_OBSERVATION')
  keys=('target','material','opportunities','delay_days','format','total')
  if any(a[k]!=b[k] for k in keys) or not (a['independent'] and b['independent']) or a['strategy']==b['strategy']:
   return decision('CLARIFY','UNMATCHED')
  if a['correct']==b['correct']:return decision('CLARIFY','NO_OBSERVED_ADVANTAGE')
  return decision('SUGGEST','MATCHED_DESCRIPTIVE_COMPARISON',preferred=(a if a['correct']>b['correct'] else b)['strategy'])
 if mode in ('remediate','progress'):
  try:score,criterion=observation(x)
  except (KeyError,TypeError,ValueError,ZeroDivisionError):return decision('CLARIFY','INVALID_OBSERVATION')
  if mode=='remediate':
   if x.get('tools_allowed') is not True:return decision('CLARIFY','INVALID_OBSERVATION')
   if score>=criterion:return decision('CLARIFY','NO_CONFIRMED_GAP')
   if x.get('consent') is not True:return decision('STOP' if x.get('consent') is False else 'CLARIFY','NO_PERMISSION')
   if not all(nat(x.get(k)) for k in ('budget_min','support_min','retest_min')) or x['support_min']<=0 or x['retest_min']<=0:return decision('CLARIFY','INVALID_PLAN')
   if x['support_min']+x['retest_min']>x['budget_min']:return decision('CLARIFY','INSUFFICIENT_BUDGET')
   return decision('SUGGEST','BOUNDED_REMEDIATION')
  if score<criterion:return decision('CLARIFY','BELOW_RULE')
  a=x.get('necessary'); e=x.get('evidence')
  if x.get('prerequisite_scope_confirmed') is not True or not isinstance(a,list) or not all(txt(k) for k in a) or len(set(a))!=len(a) or not isinstance(e,dict) or any(e.get(k) is not True for k in a):
   return decision('CLARIFY','PREREQUISITE_UNCONFIRMED')
  return decision('SUGGEST','DECLARED_RULE_MET')
 if mode=='revise':
  if x.get('consent') is not True or not txt(x.get('plan_id')) or x['plan_id']!=x.get('confirmed_plan_id') or not nat(x.get('revision')) or not nat(x.get('confirmed_revision')) or x['revision']!=x['confirmed_revision']:
   return decision('STOP','NO_EXACT_PERMISSION')
  a=x.get('costs_min')
  if not nat(x.get('budget_min')) or not isinstance(a,list) or not a or not all(nat(k) for k in a) or not txt(x.get('observation_id')) or not txt(x.get('attribution_id')):
   return decision('CLARIFY','INVALID_PLAN')
  if sum(a)>x['budget_min']:return decision('CLARIFY','INSUFFICIENT_BUDGET')
  return decision('SUGGEST','CONFIRMED_FEASIBLE_PLAN')
 raise ValueError('unknown contract')
def patch(base,d):
 x=copy.deepcopy(base)
 for k,v in d.items():
  z=x;path=k.split('.')
  for part in path[:-1]:z=z[part]
  z[path[-1]]=v
 return x
if __name__=='__main__':
 f=P/'raw-composition-design.json';d=json.loads(f.read_text());out=[]
 for c in d['contracts']:
  for j,t in enumerate(c['cases']):
   x=patch(c['base'],t['patch']);actual=evaluate(c['mode'],x)
   assert actual==t['expected'],(c['id'],t['name'],actual,t['expected'])
   out.append({'id':c['id']+'.RAW.'+str(j),'name':t['name'],'input':x,'expected':t['expected'],'actual':actual,'status':'PASS_BUILDER_FINITE_ONLY'})
 (P/'raw-composition-results.json').write_text(json.dumps({'fixture_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'results':out},ensure_ascii=False,indent=2)+'\n')
 print(len(out),'PASS_RAW_OBSERVATION_ADVICE')
