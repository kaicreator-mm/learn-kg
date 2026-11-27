"""Actual SQL Case/ModelSpec/ConditionSpec consumption of frozen finite cases only."""
import pathlib,sys,json,hashlib,math
from fractions import Fraction as F
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
sys.path.insert(0,str(ROOT))
from tools.knowledge_import.importer import Importer,ManifestPin
from tools.knowledge_import.v00_prototype import load_record
from run_finite import evaluate,n,prob,need
from tools.knowledge_import.model_spec import load_domain_contract,validate_model_parameters,ModelParameterError
DOMAIN=load_domain_contract(P/'model-domain-constraints.json')
V='0.1.0-trace-adaptation-resources-candidate-1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def ref(k,id,o):return dict(kind=k,stable_id=id,owner=o,package_id='learning-core',version=V)
def ast(e,v,binary):
 cast=float if binary else F
 if 'variable' in e:return v[e['variable']]
 if 'constant' in e:return cast(str(e['constant']))
 a=[ast(z,v,binary) for z in e['args']]
 op=e['op']
 if op=='add':return sum(a)
 if op=='mul':return math.prod(a)
 if op=='sub':need(len(a)==2);return a[0]-a[1]
 if op=='div':need(len(a)==2 and a[1]!=0);return a[0]/a[1]
 if op=='neg':need(len(a)==1);return -a[0]
 if op=='pow':need(binary and len(a)==2 and a[0]>0);return a[0]**a[1]
 raise ValueError(op)
def model_values(im,mode,x):
 """Independently select model/guard from declared fixture domain, not expected output."""
 try:
  if mode=='bkt':
   need(type(x['correct']) is bool and x['matching_observation'] is True and x['transition']=='NO_FORGETTING_AFTER_OBSERVATION')
   v={k:prob(x[k]) for k in ('p','s','g','t')};mid='K10.BKT.'+('CORRECT' if x['correct'] else 'INCORRECT')
  elif mode=='hlr':
   v={k:n(x[k]) for k in ('half_life','lag')};need(x['matched_unit'] is True);mid='K10.HLR.FIXED'
  elif mode=='brier':
   need(len(x['p'])==len(x['y'])==2 and x['same_target'] is True)
   v={'p0':prob(x['p'][0]),'p1':prob(x['p'][1]),'y0':x['y'][0],'y1':x['y'][1]};mid='K10.BRIER.TWO'
  elif mode=='discount':
   need(len(x['rewards'])==3 and x['same_unit'] is True);v={'gamma':prob(x['gamma'])}|{k:n(z) for k,z in zip(('r0','r1','r2'),x['rewards'])};mid='K11.REWARD.THREE'
  elif mode=='rectangle':
   v={k:n(x[k]) for k in ('a','b')};need(x['unit']=='CM');mid='K12.RECT.AREA'
  else:raise RuntimeError(mode)
  m=load_record(im,ref('ModelSpec',mid,mid.split('.')[0]));need(m['missing_policy']=='HOLD')
  v=validate_model_parameters(m,v,DOMAIN,model_id=mid)
  binary=m['numeric_domain']=='BINARY64'
  if binary:v={k:float(z) for k,z in v.items()}
  r={f['name']:ast(f['expr'],v,binary) for f in m['formulas']}
  need(all(math.isfinite(float(z)) for z in r.values()))
  if mode=='bkt':return {k:str(z) for k,z in r.items()},mid,'AST_EVALUATED'
  val=next(iter(r.values()));return (round(val,12) if binary else str(val)),mid,'AST_EVALUATED'
 except (ValueError,TypeError,KeyError,ZeroDivisionError,OverflowError,IndexError):return 'HOLD',None,'GUARD_OR_DOMAIN_REJECT'
def policy(im,x):
 # Derive only known flags. Unknown priority guard stops rather than passing to lower action.
 flags={'exit':x['exit']} if type(x.get('exit')) is bool else {}
 if x.get('exit') is False and type(x.get('authorized')) is bool:
  flags['unauthorized']=not x['authorized']
  if x['authorized'] and x.get('applicable') is True:
   try:
    b,c=n(x['budget']),n(x['cost']);need(b>=0 and c>=0)
    flags.update(feasible=c<=b,over_budget=c>b)
   except (ValueError,TypeError,KeyError,ZeroDivisionError):pass
 comp=load_record(im,ref('CompositionSpec','K11.TR.COMP.01','K11'));p=load_record(im,comp['output_refs'][0])
 assert p['effect']=='ADVICE_ONLY'
 for rule in sorted(p['rules'],key=lambda z:z['priority']):
  c=load_record(im,rule['condition_ref']);need(c['unknown']=='HOLD' and c['combination']=='ALL')
  vals=[]
  for z in c['clauses']:
   need(z['op']=='EQ' and type(z['value']) is bool)
   if type(flags.get(z['field'])) is not bool:return p['unknown_action']
   vals.append(flags[z['field']]==z['value'])
  if all(vals):return rule['action']
 return p['unknown_action']
def main():
 cat={(p,V):ManifestPin((P/(p+'.manifest.json')).relative_to(ROOT).as_posix(),sha(P/(p+'.manifest.json'))) for p in ('learning-core','evidence')}
 im=Importer(mode='research',catalog=cat)
 try:
  im.run(('learning-core',V));out=[];fx=load(P/'finite-fixtures.json');rr=load(P/'finite-results.json');assert rr['fixture_sha256']==sha(P/'finite-fixtures.json')
  for i,f in enumerate(fx):
   o=f['topic'].split('.')[0];cid=f['topic']+'.TR.01.F'+str(i);c=load_record(im,ref('Case',cid,o));x=json.loads(c['input_spec'])
   assert x==f['input'] and json.loads(c['expected_spec'])==f['expected'] if not isinstance(f['expected'],str) else x==f['input'] and c['expected_spec']==f['expected']
   claim=load_record(im,c['target_refs'][0]);assert claim['topic_id']==f['topic'] and c['actual_status']=='RECORDED_BUILDER_ONLY'
   result=evaluate(f['mode'],x);assert result==rr['results'][i]['actual']==f['expected']
   row=dict(id=f['id'],actual=result,status='PASS_SQL_CASE_CONSUMPTION')
   if f['mode'] in ('bkt','hlr','brier','discount','rectangle'):
    value,mid,st=model_values(im,f['mode'],x);assert value==result,(f['id'],value,result);row.update(model=mid,model_result=st)
   if f['mode']=='selection':
    action=policy(im,x);assert action==('CLARIFY' if result=='HOLD' else result),(f['id'],action,result);row['policy_action']=action
   out.append(row)
  guard_fixtures=load(P/'model-spec-guard-fixtures.json');guard_results=[]
  for fixture in guard_fixtures:
   model=load_record(im,ref('ModelSpec',fixture['model'],fixture['model'].split('.')[0]))
   try:
    validate_model_parameters(model,fixture['values'],DOMAIN,model_id=fixture['model']);actual='PASS'
   except ModelParameterError:
    actual='HOLD'
   assert actual==fixture['expected'],(fixture['id'],actual,fixture['expected'])
   guard_results.append({'id':fixture['id'],'actual':actual,'expected':fixture['expected']})
  (P/'model-spec-guard-results.json').write_text(json.dumps({'status':'BUILDER_SHARED_MODEL_DOMAIN_GUARD_ONLY','fixture_sha256':sha(P/'model-spec-guard-fixtures.json'),'contract_sha256':sha(P/'model-domain-constraints.json'),'case_count':len(guard_results),'results':guard_results},ensure_ascii=False,indent=2)+'\n')
  result={'status':'BUILDER_SQL_CONSUMPTION_ONLY','case_count':len(out),'model_spec_guard_case_count':len(guard_results),'model_spec_guard_fixture_sha256':sha(P/'model-spec-guard-fixtures.json'),'model_domain_contract_sha256':sha(P/'model-domain-constraints.json'),'model_spec_guard_results':guard_results,'ast_evaluated':sum(x.get('model_result')=='AST_EVALUATED' for x in out),'model_guards':sum(x.get('model_result')=='GUARD_OR_DOMAIN_REJECT' for x in out),'policy_cases':sum('policy_action' in x for x in out),'fixture_sha256':sha(P/'finite-fixtures.json'),'manifest_sha256':sha(P/'learning-core.manifest.json'),'results':out,'limits':'Finite adapter, no generic interpreter, model fit or independent verdict.'}
  (P/'consumption-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in result.items() if k!='results'})
 finally:im.close()
if __name__=='__main__':main()
