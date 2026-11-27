"""Bounded synthetic input guards; no certification, clinical inference or execution."""
import pathlib,json,hashlib
from fractions import Fraction as F
P=pathlib.Path(__file__).resolve().parent
def number(v):
 if type(v) not in (int,float,str):raise ValueError('number')
 return F(str(v))
def evaluate(m,x):
 try:
  if m=='model':
   if x.get('constant_speed') is not True or x.get('units')!='METER_SECOND':return 'HOLD'
   s,t=number(x['speed']),number(x['time'])
   return str(s*t) if s>=0 and t>=0 else 'HOLD'
  if m=='operation':
   if x.get('unit')!='MM' or type(x.get('safety_checked')) is not bool:return 'HOLD'
   e,t=number(x['error']),number(x['tolerance'])
   if t<0:return 'HOLD'
   return 'TASK_CRITERIA_MET_ONLY' if abs(e)<=t and x['safety_checked'] else 'NOT_ALL_CRITERIA_MET'
  if m=='support':
   if x.get('function_request') not in ('larger_text','lower_stimulation','pause'):return 'HOLD'
   if x.get('learner_confirmed') is not True:return 'REQUEST_CONFIRMATION_OR_DEFER'
   return 'SUGGEST_REVERSIBLE_SUPPORT_ONLY'
 except (ValueError,KeyError,TypeError,ZeroDivisionError,IndexError,OverflowError):return 'HOLD'
 raise ValueError(m)
def main():
 f=P/'guarded-fixtures.json';a=json.loads(f.read_text());out=[]
 for r in a:
  v=evaluate(r['mode'],r['input']);assert v==r['expected'],(r['id'],v,r['expected'])
  out.append({'id':r['id'],'actual':v,'expected':r['expected'],'status':'PASS_BUILDER_FINITE_ONLY'})
 (P/'guarded-results.json').write_text(json.dumps({'fixture_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'results':out,'limits':'Finite synthetic guards only; no general task, clinical, or credential authority.'},ensure_ascii=False,indent=2)+'\n')
 print(len(out),'GUARDED_BUILDER_PASS')
if __name__=='__main__':main()
