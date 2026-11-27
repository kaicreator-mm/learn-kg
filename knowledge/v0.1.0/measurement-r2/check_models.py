"""Read canonical ModelSpec from actual in-memory SQL; compare bounded representation to frozen finite oracles."""
import json,pathlib,math,hashlib,sys,functools
from fractions import Fraction
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
sys.path.insert(0,str(ROOT))
from tools.knowledge_import.importer import Importer,ManifestPin
from tools.knowledge_import.v00_prototype import load_record
PREP=ROOT/'docs/implementation/k09-preparation'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(x):
 if not x:raise ValueError('model domain')
def num(x):
 need(type(x) in (int,float,str));return Fraction(str(x))
def nat(x):need(type(x) is int and x>=0);return x
def countpair(a,b):need(nat(a)<=nat(b) and b>0)
def eval_ast(expr,values,domain):
 cast=float if domain=='BINARY64' else Fraction
 if 'variable' in expr:return values[expr['variable']]
 if 'constant' in expr:return cast(str(expr['constant']))
 a=[eval_ast(v,values,domain) for v in expr['args']];op=expr['op']
 if op=='add':return sum(a)
 if op=='mul':return math.prod(a)
 if op=='sub':need(len(a)==2);return a[0]-a[1]
 if op=='div':need(len(a)==2 and a[1]!=0);return a[0]/a[1]
 if op=='neg':need(len(a)==1);return -a[0]
 if op=='exp':need(domain=='BINARY64' and len(a)==1);return math.exp(a[0])
 if op=='pow':need(domain=='BINARY64' and len(a)==2 and a[0]>=0);return a[0]**a[1]
 raise ValueError('unsupported AST')
def calc(model,values):
 need(model['missing_policy']=='HOLD' and set(values)=={x['name'] for x in model['parameters']})
 domain=model['numeric_domain'];q={}
 for p in model['parameters']:
  v=num(values[p['name']])
  if p['unit']=='count':need(v.denominator==1)
  need(p['lower'] is None or v>=num(p['lower']));need(p['upper'] is None or v<=num(p['upper']))
  q[p['name']]=float(v) if domain=='BINARY64' else v
 out={f['name']:eval_ast(f['expr'],q,domain) for f in model['formulas']}
 need(all(math.isfinite(float(v)) for v in out.values()))
 return out
def actual(m,op,x):
 try:
  if op=='reliability':need(x['assumptions_met'] is True);return str(calc(m,{k:x[k] for k in ('true_var','error_var')})['reliability'])
  if op=='difficulty':return {k:str(v) for k,v in calc(m,{k:nat(x[k]) for k in ('correct','incorrect','missing')}).items()}
  if op=='discrimination':
   a,b=x['hi'];c,d=x['lo'];countpair(a,b);countpair(c,d)
   return str(calc(m,dict(hi_correct=a,hi_total=b,lo_correct=c,lo_total=d))['difference'])
  if op=='sem':need(x['matched'] is True);return calc(m,dict(sd=x['sd'],r=x['r']))['sem']
  if op=='irt':
   if len(m['parameters'])==2:
    need(x['a']==1 and x['c']==0);return calc(m,{k:x[k] for k in ('theta','b')})['p']
   need(num(x['a'])>0 and 0<=num(x['c'])<1);return calc(m,{k:x[k] for k in ('theta','b','a','c')})['p']
  if op=='multidim':
   a,b=x['a'],x['theta'];need(len(a)==len(b)==2)
   return calc(m,dict(a1=a[0],a2=a[1],theta1=b[0],theta2=b[1],d=x['d']))['p']
  if op=='information':
   a,p=x['a2'],x['p'];need(x['local_independent'] is True and len(a)==len(p)>0 and all(num(v)>0 for v in a) and all(0<num(v)<1 for v in p))
   return str(sum(calc(m,dict(a_squared=k,p=v))['information'] for k,v in zip(a,p)))
  if op=='dina':
   q,a=x['q'],x['alpha'];need(len(q)==len(a)==2 and all(type(v) is int and v in (0,1) for v in q+a) and any(q) and 1-num(x['s'])>num(x['g']))
   return str(calc(m,dict(q1=q[0],q2=q[1],alpha1=a[0],alpha2=a[1],s=x['s'],g=x['g']))['p'])
  if op=='screen':
   need(x['reference_valid'] is True);return {k:str(v) for k,v in calc(m,{k:nat(x[k]) for k in ('tp','fn','tn','fp')}).items()}
  if op=='link':
   need(x['matched'] is True and num(x['sx'])>0 and num(x['sy'])>0)
   return str(calc(m,{k:x[k] for k in ('mux','sx','muy','sy','x')})['linked'])
  raise RuntimeError(op)
 except (ValueError,KeyError,TypeError,ZeroDivisionError,OverflowError):return 'HOLD'
def main():
 version='0.1.0-measurement-candidate-2';cat={}
 for pkg in ['learning-core','evidence']:
  f=P/(pkg+'.manifest.json');cat[pkg,version]=ManifestPin(f.relative_to(ROOT).as_posix(),sha(f))
 review=ROOT/'evidence/validation/KR02-R6-K09-FINITE-01.json';rr=load(review)
 g=next(x for x in rr['groups'] if x['fixture']==(PREP/'finite-fixtures.json').relative_to(ROOT).as_posix())
 assert g['fixture_sha256']==sha(PREP/'finite-fixtures.json') and g['result_sha256']==sha(PREP/'finite-results.json')
 im=Importer(mode='research',catalog=cat)
 try:
  report=im.run(('learning-core',version))
  design=load(P/'model-design.json');models={}
  for m in design:
   x=load_record(im,{'package_id':'learning-core','version':version,'stable_id':m['id'],'kind':'ModelSpec','owner':'K09'})
   assert x['formulas']==m['formulas'] and x['parameters']==m['parameters'] and x['applicability']==m['applicability']
   models[m['topic']]=(m['id'],x)
  results=[]
  for i,x in enumerate(load(PREP/'finite-fixtures.json')):
   if x['topic'] not in models or x['op']=='rasch_mle':continue
   mid,m=models[x['topic']];v=actual(m,x['op'],x['input']);e=x['expected']
   match=math.isclose(v,e,rel_tol=0,abs_tol=1e-12) if type(v) in (float,int) and type(e) in (float,int) else v==e
   assert match,(i,v,e)
   results.append({'ordinal':i,'model_id':mid,'input':x['input'],'actual':v,'expected':e,'status':'PASS_BUILDER_MODEL_REPRESENTATION_ONLY'})
  assert len(results)==22
  (P/'model-representation-results.json').write_text(json.dumps({'status':'FINITE_ACTUAL_SQL_MODEL_REPRESENTATION_WITNESS','import_manifests':{k[0]:v.sha256 for k,v in cat.items()},'review_receipt_sha256':sha(review),'source_fixture_sha256':g['fixture_sha256'],'models':len(models),'results':results,'limit':'New representation implementation checked against independently accepted unchanged expectations. Does not independently qualify AST implementation, calibrate/fit models or validate learner inference. Only scalar bounded formulas; applicability guards applied by explicit finite adapter, not general engine.'},ensure_ascii=False,indent=2)+'\n')
  (P/'import-receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
  print(len(models),'models;',len(results),'SQL AST finite checks')
 finally:im.close()
if __name__=='__main__':main()
