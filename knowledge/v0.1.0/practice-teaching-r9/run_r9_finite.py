"""Finite author discrimination, not a general learner diagnosis or fitted model."""
import json, pathlib, hashlib
P=pathlib.Path(__file__).resolve().parent
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def nat(x):return type(x) is int and x>=0
def evaluate(mode,x):
 if mode=='strategy':
  l,w=x.get('length'),x.get('width');s=x.get('selected');a=x.get('answer')
  if x.get('shape')!='rectangle' or not all(nat(k) and k>0 for k in (l,w)) or x.get('target') not in ('area','perimeter') or s not in ('area','perimeter') or not nat(a):return 'UNKNOWN'
  tr=x.get('trace');formula='L*W' if s=='area' else '2*(L+W)'
  if not isinstance(tr,dict) or tr.get('formula')!=formula or tr.get('substitution')!=[l,w] or not nat(tr.get('computed')) or tr['computed']!=a:return 'UNKNOWN'
  return {(True,True):'BOTH_CORRECT_IN_FIXTURE',(True,False):'CORRECT_SELECTION_WRONG_EXECUTION',(False,True):'WRONG_SELECTION_CORRECT_SELECTED_EXECUTION',(False,False):'BOTH_WRONG'}[s==x['target'],a==(l*w if s=='area' else 2*(l+w))]
 if mode=='schedule':
  l,t,b=(x.get(k) for k in ('last','target','budget'));w=x.get('windows');cs=x.get('candidates')
  if not all(nat(k) for k in (l,t,b)) or l>=t or not isinstance(w,dict) or not isinstance(cs,dict):return 'UNKNOWN'
  out={}
  for k,a in cs.items():
   if not isinstance(a,list) or not a or any(not isinstance(z,list) or len(z)!=2 or not all(nat(v) for v in z) for z in a):out[k]={'feasible':False,'reason':'INVALID_WINDOW'};continue
   days=[z[0] for z in a]
   if days!=sorted(set(days)) or any(not l<d<t or not 0<c<=w.get(str(d),0) for d,c in a):out[k]={'feasible':False,'reason':'INVALID_WINDOW'};continue
   cost=sum(z[1] for z in a)
   if cost>b:out[k]={'feasible':False,'reason':'BUDGET_EXCEEDED'};continue
   out[k]={'feasible':True,'cost':cost,'retention':t-days[-1],'prediction':'UNKNOWN'}
  return out
 if mode=='necessity':
  if not all(x.get(k) is True for k in ('allowed_route','same_conditions','independent')) or x.get('capability') not in ('PRESENT','ABSENT') or type(x.get('target_met')) is not bool:return 'HOLD'
  return 'REFUTES_NECESSITY_IN_SCOPE' if x['capability']=='ABSENT' and x['target_met'] else 'NO_COUNTEREXAMPLE'
 raise ValueError(mode)
def main():
 f=P/'r9-finite-fixtures.json';xs=json.loads(f.read_text());out=[]
 for x in xs:
  v=evaluate(x['mode'],x['input']);assert v==x['expected'],(x['id'],v,x['expected'])
  out.append({'id':x['id'],'claim':x['claim'],'actual':v,'expected':x['expected'],'status':'PASS_BUILDER_FINITE_ONLY'})
 (P/'r9-finite-results.json').write_text(json.dumps({'fixture_sha256':sha(f),'results':out,'limit':'Finite authored cases only; no independent verdict or psychological cause, fitted retention model, learner inference.'},ensure_ascii=False,indent=2)+'\n')
 print(len(out),'PASS_R9_FINITE_BUILDER_ONLY')
if __name__=='__main__':main()
