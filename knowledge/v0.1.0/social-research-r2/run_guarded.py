"""New guard for actual defined two-period synthetic DiD; not an identification engine."""
import json,pathlib,hashlib
from fractions import Fraction as F
P=pathlib.Path(__file__).resolve().parent
def number(v):
 if type(v) not in (int,float,str):raise ValueError('number')
 return F(str(v))
def evaluate(x):
 try:
  a,b,t=x['treatment'],x['control'],x['periods']
  if not all(isinstance(v,list) and len(v)==2 for v in (a,b,t)):return 'HOLD'
  if not number(t[0])<number(t[1]) or x.get('matched_periods') is not True or x.get('same_measurement_scale') is not True:return 'HOLD'
  y=[number(v) for v in a+b]
  d=y[1]-y[0]-y[3]+y[2]
  flags=('parallel_trends','no_other_differential_changes','no_anticipation','no_spillover','stable_measurement','stable_composition')
  ok=x.get('estimand')=='TREATED_GROUP_POST_PERIOD_EFFECT' and all(x.get(k) is True for k in flags)
  return {'difference_in_differences':str(d),'causal':'CANDIDATE_UNDER_DECLARED_ASSUMPTIONS' if ok else 'HOLD'}
 except (ValueError,KeyError,TypeError,ZeroDivisionError,IndexError,OverflowError):return 'HOLD'
def main():
 f=P/'guarded-fixtures.json';a=json.loads(f.read_text());out=[]
 for r in a:
  v=evaluate(r['input']);assert v==r['expected'],(r['id'],v,r['expected'])
  out.append({'id':r['id'],'actual':v,'expected':r['expected'],'status':'PASS_BUILDER_FINITE_ONLY'})
 (P/'guarded-results.json').write_text(json.dumps({'fixture_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'results':out,'limits':'Specified two-period arithmetic and declared assumptions only; not evidence that assumptions hold.'},ensure_ascii=False,indent=2)+'\n')
 print(len(out),'GUARDED_BUILDER_PASS')
if __name__=='__main__':main()
