"""Finite synthetic logical/arithmetic discrimination, not diagnosis or certification."""
import pathlib,json,hashlib
from fractions import Fraction as F
P=pathlib.Path(__file__).resolve().parent
def ev(m,x):
 if m=='proof':
  n=x.get('n');need=x.get('domain')=='INTEGER' and type(n) is int
  if not need:return 'HOLD'
  return 'REFUTES_DECLARED_ODD_UNIVERSAL' if (n*n+n)%2==0 else 'NO_COUNTEREXAMPLE'
 if m=='estimate':
  a,b,e=x['a'],x['b'],x['estimate'];v=a*b
  return {'exact':v,'absolute_error':abs(v-e)}
 if m=='model':
  if x.get('constant_speed') is not True:return 'HOLD'
  return str(F(str(x['speed']))*F(str(x['time'])))
 if m=='operation':
  err=x.get('error');tol=x.get('tolerance');safe=x.get('safety_checked')
  if err is None or tol is None or type(safe) is not bool:return 'HOLD'
  return 'TASK_CRITERIA_MET_ONLY' if abs(F(str(err)))<=F(str(tol)) and safe else 'NOT_ALL_CRITERIA_MET'
 if m=='change':
  if x.get('same_person') is not True or x.get('same_scale') is not True or x.get('matched_conditions') is not True:return 'HOLD'
  return {'observed_difference':str(F(str(x['after']))-F(str(x['before']))),'causal':'NOT_ESTABLISHED'}
 if m=='support':
  if x.get('learner_confirmed') is not True:return 'REQUEST_CONFIRMATION_OR_DEFER'
  if x.get('function_request') in ('larger_text','lower_stimulation','pause'):return 'SUGGEST_REVERSIBLE_SUPPORT_ONLY'
  return 'HOLD'
 raise ValueError(m)
def main():
 f=P/'finite-fixtures.json';a=json.loads(f.read_text());out=[]
 for r in a:
  v=ev(r['mode'],r['input']);assert v==r['expected'],(r['id'],v,r['expected']);out.append({'id':r['id'],'actual':v,'expected':r['expected'],'status':'PASS_BUILDER_FINITE_ONLY'})
 (P/'finite-results.json').write_text(json.dumps({'fixture_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'results':out,'limits':'Author finite cases; no general evaluator, empirical learning, medical or certification verdict.'},ensure_ascii=False,indent=2)+'\n')
 print(len(out),'PASS_BUILDER_FINITE_ONLY')
if __name__=='__main__':main()
