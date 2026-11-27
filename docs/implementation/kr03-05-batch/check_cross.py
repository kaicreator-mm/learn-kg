"""Bounded research composition; no qualification, empirical inference or generic execution."""
import sys,json,pathlib,hashlib,importlib.util
from fractions import Fraction as F
P=pathlib.Path(__file__).resolve().parent; ROOT=P.parents[2]; sys.path.insert(0,str(ROOT))
from tools.knowledge_import.importer import Importer,ManifestPin
from tools.knowledge_import.v00_prototype import load_record
from tools.knowledge_import.model_spec import load_domain_contract,validate_model_parameters,ModelParameterError
B=ROOT/'knowledge/v0.1.0'
DOMAIN=load_domain_contract(B/'trace-adaptation-resources-r1'/'model-domain-constraints.json')
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
names=['foundation-r3','practice-teaching-r10','measurement-r4','trace-adaptation-resources-r1','social-research-r2','domain-development-r2','technology-inclusion-governance-r1']
owners={**{f'K{i:02}':names[0] for i in range(1,5)},**{f'K{i:02}':names[1] for i in range(5,9)},'K09':names[2],**{f'K{i:02}':names[3] for i in range(10,13)},'K13':names[4],'K17':names[4],'K14':names[5],'K18':names[5],'K15':names[6],'K16':names[6],'K19':names[6]}
groups={
'observation':['K09.01.03.ME.01','K09.01.04.ME.01','K10.01.02.TR.01','K10.01.05.TR.01','K10.02.01.TR.01','K10.BKT.CORRECT','K02.06.04.D4.03'],
'schedule':['K10.03.01.TR.01','K10.HLR.FIXED','K11.02.04.TR.01','K11.05.04.TR.01','K05.02.04.PT.01','K08.05.04.PT.01'],
'task':['K03.06.02.D4.02','K06.03.01.PT.01','K09.01.03.ME.01','K12.02.02.TR.01','K12.06.01.TR.01'],
'transfer':['K04.01.03.D4.01','K06.01.02.D4.01','K14.04.03.DD.01','K14.05.03.DD.01','K14.05.04.DD.01'],
'event':['K06.03.01.PT.01','K09.01.04.ME.01','K15.06.02.TG.01','K15.06.04.TG.01','K10.04.04.TR.01'],
'inclusion':['K02.05.04.D4.02','K13.02.03.SR.01','K16.03.04.TG.01','K16.05.01.TG.01'],
'development':['K02.05.04.D4.02','K18.01.01.DD.01','K18.04.01.DD.01'],
'governance':['K13.04.04.SR.01','K17.02.02.SR.01','K19.02.05.TG.01','K19.03.02.TG.01','K19.04.05.TG.01']}
def ast(e,v):
 if 'variable'in e:return v[e['variable']]
 if 'constant'in e:return F(str(e['constant']))
 a=[ast(z,v) for z in e['args']];op=e['op']
 if op=='add':return sum(a)
 if op=='mul':
  r=F(1)
  for z in a:r*=z
  return r
 if op=='sub':return a[0]-a[1]
 if op=='div':return a[0]/a[1]
 if op=='neg':return -a[0]
 if op=='pow':return a[0]**a[1]
 raise ValueError(op)
def strict_number(value):
 if type(value) not in (int,float):raise ValueError('strict non-bool numeric value required')
 return F(str(value))
def evaluate(mode,x,recs):
 if mode=='observation':
  if not(x.get('kind')=='RESPONSE' and type(x.get('hint')) is bool and x['hint'] is False and type(x.get('correct')) is bool and x['correct'] is True and type(x.get('same_contract')) is bool and x['same_contract'] is True):return 'HOLD'
  params=x.get('model_parameters')
  if not isinstance(params,dict) or set(params)!={'p','s','g','t'}:return 'HOLD'
  try:
   v={k:strict_number(params[k]) for k in ('p','s','g','t')}
   m=recs['K10.BKT.CORRECT']
   validate_model_parameters(m,v,DOMAIN,model_id='K10.BKT.CORRECT')
   calculated={f['name']:ast(f['expr'],v) for f in m['formulas']}
   return str(calculated['next_prior'])
  except (ValueError,TypeError,KeyError,ZeroDivisionError,OverflowError):return 'HOLD'
 if mode=='schedule':
  if type(x.get('exit')) is not bool:return 'HOLD'
  if x['exit'] is True:return 'STOP'
  if type(x.get('matched_unit')) is not bool or x['matched_unit'] is not True or type(x.get('authorized')) is not bool or x['authorized'] is not True:return 'HOLD'
  try:
   v={k:strict_number(x[k]) for k in ('half_life','lag')}
   target=strict_number(x['target']);budget=strict_number(x['budget']);cost=strict_number(x['cost'])
   if target<0 or target>1 or budget<0 or cost<0:return 'HOLD'
   m=recs['K10.HLR.FIXED']
   validate_model_parameters(m,v,DOMAIN,model_id='K10.HLR.FIXED')
   p=ast(m['formulas'][0]['expr'],v)
   if p>=target:return 'DEFER'
   return 'SUGGEST' if cost<=budget else 'DEFER'
  except (ValueError,TypeError,KeyError,ZeroDivisionError,OverflowError):return 'HOLD'
 if mode=='task':
  if not x['rule'] or x['response_rule']!=x['rule']:return 'HOLD'
  if x['target']!=x['task']:return 'SEPARATE_CONSTRUCT'
  return 'ASSISTED_OBSERVATION' if x['hint'] is True else 'INDEPENDENT_OBSERVATION' if x['hint'] is False else 'HOLD'
 if mode=='transfer':
  if type(x.get('days')) is not int or x['days']<=0:return 'HOLD'
  if type(x.get('new_task')) is not bool or type(x.get('own_performance')) is not bool or type(x.get('assistance')) is not bool:return 'HOLD'
  if not isinstance(x.get('target'),str) or not x['target'] or not isinstance(x.get('prior_target'),str) or not x['prior_target']:return 'HOLD'
  if x['own_performance'] is not True or x['prior_target']!=x['target'] or x['new_task'] is not True:return 'HOLD'
  return 'ASSISTED_NOT_INDEPENDENT' if x['assistance'] is True else 'TRANSFER_OBSERVATION_ONLY'
 if mode=='event':
  if x['authorized'] is not True or x['same_clock'] is not True or any(type(x[k]) is not int for k in ('event_time','available_at','prediction_time')):return 'HOLD'
  if x['available_at']<x['event_time']:return 'HOLD'
  if max(x['event_time'],x['available_at'])>x['prediction_time']:return 'EXCLUDE_FUTURE_OR_UNAVAILABLE'
  if x['event_id']==x['old_id']:return 'DUPLICATE_NO_UPDATE' if x['payload']==x['old_payload'] else 'CONFLICT_HOLD'
  return 'NEW_EVENT_CANDIDATE'
 if mode=='inclusion':
  if x['observed_access'] is not True or x['individual_evidence'] is not True:return 'HOLD'
  return 'CANDIDATE_SUPPORT' if x['target']==x['adapted_target'] else 'SEPARATE_CONSTRUCT'
 if mode=='development':
  if x['observed_target']!=x['target'] or x['response'] not in ('CORRECT','INCORRECT'):return 'HOLD'
  return 'TASK_EVIDENCE_ONLY' if x['independent'] is True else 'ASSISTED_NOT_INDEPENDENT' if x['independent'] is False else 'HOLD'
 if mode=='governance':
  if x['withdrawn'] is True:return 'STOP'
  if x['withdrawn'] is not False or x['purpose']!=x['granted_purpose']:return 'HOLD_PURPOSE'
  if x['risk']=='HIGH' and x['assignment_random'] is not True:return 'HOLD_HIGH_RISK_CAUSAL_CLAIM'
  if x['risk']=='LOW' and x['human_review'] is True:return 'DESIGN_REVIEW_ONLY'
  return 'HOLD'
 raise ValueError(mode)

def main():
 d=load(ROOT/'docs/implementation/task-dag.json');tasks={t['id']:t for t in d['tasks']}
 recs={};bindings={};ims={};indexes={};manifests={}
 try:
  for n in names:
   p=B/n; m=load(p/'learning-core.manifest.json');v=m['version']; manifests[n]=sha(p/'learning-core.manifest.json')
   cat={(k,v):ManifestPin((p/(k+'.manifest.json')).relative_to(ROOT).as_posix(),sha(p/(k+'.manifest.json'))) for k in ('learning-core','evidence')}
   im=Importer(mode='research',catalog=cat,extension=ManifestPin((p/'relation-types.json').relative_to(ROOT).as_posix(),sha(p/'relation-types.json')) if n==names[0] else None);ims[n]=im;im.run(('learning-core',v))
   indexes[n]={}
   for f in m['files']:
    path=p/f['path'];assert sha(path)==f['sha256']
    for line in path.read_text().splitlines():
     r=json.loads(line);indexes[n][r['stable_id']]=(r,path,v)
  for id in sorted(set(sum(groups.values(),[]))):
   o=id.split('.')[0];n=owners[o];r,path,v=indexes[n][id];assert r['status']=='CANDIDATE',(id,r['status'])
   ref={k:r[k] for k in ('kind','stable_id','owner')};ref.update(package_id='learning-core',version=v)
   sql=load_record(ims[n],ref);recs[id]=sql
   if r['kind']=='Claim':assert sql['statement']==r['statement']
   task=tasks[o]; receipt=task.get('current_receipt');q=task.get('qualification_receipt')
   bound={'ref':ref,'record_sha256':digest(r),'file':str(path.relative_to(ROOT)),'file_sha256':sha(path),'manifest_sha256':manifests[n],'formal_status':task['status']}
   if receipt:
    rr=load(ROOT/receipt);assert any(x.get('path')==str(path.relative_to(ROOT)) and x.get('sha256')==sha(path) for x in rr['output'])
    bound.update(receipt=receipt,receipt_sha256=sha(ROOT/receipt),content_digest=rr['content_digest'])
   if q:
    qr=load(ROOT/q);assert qr['reviewed_content_digest']==rr['content_digest']
    bound.update(qualification=q,qualification_sha256=sha(ROOT/q),qualification_scope=task.get('qualification_scope','LOCAL'))
    if task.get('qualification_scope')=='RESTRICTED':bound['scope_note']='Only bounded nonempirical method or allowlisted source statement; no restored excluded-source inference.'
   bindings[id]=bound
  results=[]
  for x in load(P/'cross-fixtures.json'):
   if x['id']=='X01':assert x.get('model_parameter_digest')==digest(x['input'].get('model_parameters')),'X01 model parameter preset digest'
   y=evaluate(x['mode'],x['input'],recs);assert y==x['expected'],(x['id'],y,x['expected'])
   results.append({'id':x['id'],'actual':y,'refs':groups[x['mode']]})
  result={'status':'RESEARCH_CROSS_SNAPSHOT_WITNESS_BUILDER_ONLY','fixture_sha256':sha(P/'cross-fixtures.json'),'case_count':len(results),'x01_model_parameter_digest':load(P/'cross-fixtures.json')[0]['model_parameter_digest'],'bindings':bindings,'results':results,'limits':'Separate in-memory imports; finite hard-coded composition, not canonical cross-version edges, formal dependency consumption, CQ/LC, learner or qualification result.'}
  (P/'cross-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('cross',len(results),'bindings',len(bindings))
 finally:
  for im in ims.values():im.close()
if __name__=='__main__':main()
