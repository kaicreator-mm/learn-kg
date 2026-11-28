"""Two independent subject routes, actual SQL reads and shared registered P06 finite evaluator."""
import hashlib,json,sys,itertools
from pathlib import Path
from fractions import Fraction
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path[:0]=[str(ROOT),str(HERE.parent/'process-cumulative')]
from tools.knowledge_import.importer import Importer,ManifestPin,Reject
from tools.knowledge_import.v00_prototype import load_record
from subject_importer import SubjectImporter,MATH_KEY,MATH_PATH,MATH_PIN
from semantic_checks import evaluate as p06_evaluate
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def dig(x):return hashlib.sha256(canonical(x).encode()).hexdigest()
P=('learning-process','0.1.0-process-candidate-3')
H=('chinese','0.1.0-chinese-cumulative-candidate-2')
def ref(key,owner,kind,id):return dict(package_id=key[0],version=key[1],owner=owner,kind=kind,stable_id=id)
def math_key(x):
 if not isinstance(x,list) or len(x)!=4 or any(type(v)is not int or not 0<=v<=100 for v in x):return None
 a,b,c,d=x
 if b==0 or d==0:return None
 return 'LESS' if a*d<c*b else 'GREATER' if a*d>c*b else 'EQUAL'
def zh_key(x):
 if not isinstance(x,dict) or set(x)!={'request_function_verified','prior_proposition','requested_hour','actual_hour'}:return None
 if x['request_function_verified'] is not True or x['prior_proposition'] is not True:return None
 if any(type(x[k])is not int or not 0<=x[k]<=23 for k in ('requested_hour','actual_hour')):return None
 return 'CONFIRM' if x['requested_hour']==x['actual_hour'] else 'DISCONFIRM'
def subject_eval(im,domain,x):
 if not isinstance(x,dict):return 'HOLD'
 if x.get('exit') is True:return 'STOP'
 if x.get('permission') is False:return 'REFUSE'
 if x.get('exit') is not False or x.get('permission') is not True:return 'HOLD'
 if type(domain) is not str or domain not in ('ZH','MATH'):return 'HOLD'
 key=H if domain=='ZH' else MATH_KEY
 owner='H06' if domain=='ZH' else 'M01'
 taskid='H06.CONFIRM.TASK' if domain=='ZH' else 'M01.TASK.COMPARE'
 taskref=ref(key,owner,'TaskSpec',taskid)
 if x.get('task_ref')!=taskref or x.get('task_version')!='T1' or x.get('observed_task_version')!='T1' or x.get('scoring_version')!='S1' or x.get('expected_scoring_version')!='S1':return 'HOLD'
 task=load_record(im,taskref);construct=task['construct_ref'];load_record(im,construct)
 for r in task['object_refs']+task['observation_refs']+task['claim_refs']:load_record(im,r)
 fn=zh_key if domain=='ZH' else math_key
 answer=fn(x.get('problem'))
 if answer is None:return 'HOLD'
 if x.get('response_status')=='OBSERVED':
  allowed=('CONFIRM','DISCONFIRM') if domain=='ZH' else ('LESS','EQUAL','GREATER')
  if x.get('response') not in allowed:return 'HOLD'
 flowref=ref(P,'P06','FlowSpec','P06.FLOW');flow=load_record(im,flowref)
 for step in flow['steps']:
  a=load_record(im,step['activity_ref'])
  for r in a['goal_refs']+a['observation_refs']+a['role_refs']+a['object_refs']:load_record(im,r)
 inp={k:x.get(k) for k in ('task_version','observed_task_version','scoring_version','expected_scoring_version','response_status','response','hint_used','hypotheses','discrimination')}
 inp['key']=answer
 actual=p06_evaluate(im,flow,inp,'P06',load_record)
 return dict(task=taskref,derived_key=answer,process=flowref,result=actual,mastery='UNKNOWN') if isinstance(actual,dict) else actual
def main():
 b=ROOT/'knowledge/v0.1.0';catalog={}
 for z in load(HERE/'catalog.json')['entries']:
  k=(z['package_id'],z['version']);assert k not in catalog
  catalog[k]=ManifestPin(z['path'],z['sha256'])
 # No manifest discovery or unrelated shard scan in the route execution scope.
 tracker={'active':None,'files':set(),'excluded':[]}
 def audit(event,args):
  if event!='open' or tracker['active'] is None or not args or not isinstance(args[0],(str,bytes)):return
  p=Path(args[0].decode() if isinstance(args[0],bytes) else args[0])
  if not p.is_absolute():p=Path.cwd()/p
  if not p.is_relative_to(ROOT):return
  rel=p.relative_to(ROOT).as_posix();tracker['files'].add(rel)
  other='other-subject-math-v01' if tracker['active']=='ZH' else 'chinese-'
  if any(other in part for part in Path(rel).parts):
   tracker['excluded'].append(rel);raise RuntimeError('UNRELATED_SUBJECT_FILE_OPEN')
 sys.addaudithook(audit)
 assert catalog[MATH_KEY].sha256==MATH_PIN
 ext=b/'foundation-r3/relation-types.json';ep=ManifestPin(ext.relative_to(ROOT).as_posix(),sha(ext))
 ts={t['id']:t for t in load(ROOT/'docs/implementation/task-dag.json')['tasks']}
 bindings={}
 for o in ('P06','H05','H06','H07','V00'):
  t=ts[o];p=ROOT/t['current_receipt'];r=load(p)
  for f in r['output']:assert sha(ROOT/f['path'])==f['sha256']
  v=dict(receipt_path=t['current_receipt'],receipt_sha256=sha(p),content_digest=r['content_digest'])
  if t.get('qualification_receipt'):
   q=ROOT/t['qualification_receipt'];assert load(q)['reviewed_content_digest']==r['content_digest'];v['qualification_receipt_sha256']=sha(q)
  bindings[o]=v
 # Existing DB02 importer intentionally rejects the math role. The narrow adapter
 # must not override that baseline policy or provide general subject authorization.
 im=Importer(ROOT,mode='research',catalog=catalog,extension=ep)
 try:
  try:im.run(MATH_KEY);raise AssertionError('BASELINE_MUST_REJECT')
  except Reject as e:assert 'PACKAGE_ROLE_NOT_IMPLEMENTED' in str(e)
 finally:im.close()
 # 64^2 pairs of small fractions (including zero numerators); independent Fraction comparison.
 fs=[(a,b) for a in range(8) for b in range(1,9)];n=0
 for (a,b),(c,d) in itertools.product(fs,repeat=2):
  x,y=Fraction(a,b),Fraction(c,d);expect='LESS' if x<y else 'GREATER' if x>y else 'EQUAL'
  assert math_key([a,b,c,d])==expect;n+=1
 for x in ([1,0,1,2],[True,2,1,3],[1,-2,1,3],[101,2,1,3],[1.0,2,1,3],None):assert math_key(x) is None
 routes=[]
 for domain,key,owner,taskid,problem,answer,wrong in [
  ('ZH',H,'H06','H06.CONFIRM.TASK',dict(request_function_verified=True,prior_proposition=True,requested_hour=9,actual_hour=9),'CONFIRM','DISCONFIRM'),
  ('MATH',MATH_KEY,'M01','M01.TASK.COMPARE',[2,3,3,4],'LESS','GREATER')]:
  tracker.update(active=domain,files=set(),excluded=[])
  im=SubjectImporter(ROOT,mode='research',catalog=catalog,extension=ep)
  try:
   for k in (P,key):im._load(k,set())
   links={k:im._validate_refs(k) for k in im.packages}
   for k,rr in links.items():im._materialize(k,rr)
   excluded=MATH_KEY if domain=='ZH' else H
   assert excluded not in im.packages and excluded not in im.connections
   assert all((('other-subject' if domain=='ZH' else 'chinese') not in p) for p in im.opened)
   assert all(c.execute('PRAGMA query_only').fetchone()==(1,) and not c.execute('PRAGMA foreign_key_check').fetchall() and all(not t[2] for t in c.execute('PRAGMA database_list')) for c in im.connections.values())
   taskref=ref(key,owner,'TaskSpec',taskid)
   base=dict(task_ref=taskref,problem=problem,task_version='T1',observed_task_version='T1',scoring_version='S1',expected_scoring_version='S1',exit=False,permission=True,response_status='OBSERVED',response=answer,hint_used=False)
   def result(x):return dict(task=taskref,derived_key=answer,process=ref(P,'P06','FlowSpec','P06.FLOW'),result=x,mastery='UNKNOWN')
   tests=[
    ('independent',base,result(dict(score=1,category='INDEPENDENT_TASK_ONLY',update='NONE'))),
    ('assisted',dict(base,hint_used=True),result(dict(score=1,category='ASSISTED',update='REQUEST_INDEPENDENT_RETEST'))),
    ('missing',dict(base,response_status='MISSING',response=None),result(dict(score=None,category='MISSING',update='NONE'))),
    ('competing',dict(base,response=wrong,hypotheses=['RULE','INSTRUCTION'],discrimination={'RULE':True,'INSTRUCTION':True}),result(dict(score=0,category='ERROR',update='KEEP_COMPETING_HYPOTHESES'))),
    ('unknown_evidence',dict(base,response=wrong,hypotheses=['RULE','INSTRUCTION']),result(dict(score=0,category='ERROR',update='REQUEST_DISCRIMINATING_OBSERVATION'))),
    ('stipulated_discriminator',dict(base,response=wrong,hypotheses=['RULE','INSTRUCTION'],discrimination={'RULE':True,'INSTRUCTION':False}),result(dict(score=0,category='ERROR',update='SUGGEST_TARGETED_FEEDBACK_ONLY',hypothesis='RULE'))),
    ('wrong_task',dict(base,task_ref=dict(taskref,version='wrong')),'HOLD'),
    ('wrong_scoring',dict(base,expected_scoring_version='S2'),'HOLD'),
    ('wrong_subject',dict(base,task_ref=ref(excluded,'M01' if domain=='ZH' else 'H06','TaskSpec','M01.TASK.COMPARE' if domain=='ZH' else 'H06.CONFIRM.TASK')),'HOLD'),
    ('invalid_problem',dict(base,problem=None),'HOLD'),
    ('invalid_response',dict(base,response='unrecognized'),'HOLD'),
    ('exit',dict(base,exit=True),'STOP'),('denied',dict(base,permission=False),'REFUSE'),('unknown_permission',dict(base,permission=None),'HOLD')]
   # Retest is a new finite task example, independent result only, not a proven learning effect.
   alt=dict(request_function_verified=True,prior_proposition=True,requested_hour=10,actual_hour=11) if domain=='ZH' else [3,5,2,4]
   a='DISCONFIRM' if domain=='ZH' else 'GREATER'
   ret=dict(base,problem=alt,response=a)
   tests.append(('novel_variant',ret,dict(result(dict(score=1,category='INDEPENDENT_TASK_ONLY',update='NONE')),derived_key=a)))
   cases=[]
   for id,x,expect in tests:
    y=subject_eval(im,domain,x);assert y==expect,(domain,id,y,expect)
    cases.append(dict(id=domain+'.'+id,input=x,input_sha256=dig(x),expected=expect,actual=y,status='AUTHOR_FINITE_ONLY'))
   # Exact domain guard probes run while the legitimate subject SQL is loaded.
   domain_probes=[]
   for bad in (None,'UNKNOWN','math','zh',' MATH','ZH ','',False,1,[],{},'EN'):
    for input_,expect in ((base,'HOLD'),(dict(base,exit=True),'STOP'),(dict(base,permission=False),'REFUSE')):
     actual=subject_eval(im,bad,input_);assert actual==expect,(domain,bad,actual,expect)
     domain_probes.append(dict(domain=bad,input_sha256=dig(input_),expected=expect,actual=actual))
   flow=load_record(im,ref(P,'P06','FlowSpec','P06.FLOW'))
   routes.append(dict(domain=domain,root=list(key),process=list(P),flow_sha256=dig(flow),opened_manifest_and_records=im.opened,opened_packages=[list(k) for k in im.connections],excluded_subject_open_count=len(tracker['excluded']),audited_repo_file_opens=sorted(tracker['files']),records=sum(len(z[3]) for z in im.packages.values()),typed_refs=sum(len(z) for z in links.values()),cases=cases,domain_probes=domain_probes))
  finally:
   im.close();tracker['active']=None
 assert routes[0]['flow_sha256']==routes[1]['flow_sha256']
 # Explicit new math tuple and pin rejection.
 for bad in [ManifestPin(MATH_PATH,'0'*64),ManifestPin('docs/implementation/v01-second-subject/design.json',MATH_PIN)]:
  im=SubjectImporter(ROOT,mode='research',catalog=catalog|{MATH_KEY:bad},extension=ep)
  try:
   try:im.run(MATH_KEY);raise AssertionError('BAD_PIN_ACCEPTED')
   except Reject as e:assert 'SUBJECT_MANIFEST_PIN' in str(e)
  finally:im.close()
 report=dict(status='V01_PREPARATION_ONLY_NOT_LC11_ACCEPTANCE',math_manifest_sha256=MATH_PIN,source_bindings=bindings,math_fraction_reference_cases=n,invalid_math_probes=6,baseline_math_role_rejected=True,bad_pin_probes=2,shared_process_manifest_sha256=catalog[P].sha256,shared_process_same_sql_payload=True,route_file_open_audit='PYTHON_AUDIT_OPEN_EVENTS_IN_ROUTE_SCOPE_ONLY',route_cases=sum(len(r['cases']) for r in routes),domain_guard_probes=sum(len(r['domain_probes']) for r in routes),routes=routes,persistent_sqlite=False,independent_oracle='NOT_RUN',scope='Shared P06 finite discriminator/feedback gate, stipulated diagnostic flags; no complete lifecycle or full CQ25/LC11.')
 (HERE/'results.json').write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
 print('TWO_SUBJECTS',[(r['domain'],len(r['cases']),len(r['opened_packages']),r['records'],r['typed_refs'],r['excluded_subject_open_count']) for r in routes],'MATH_REFERENCE',n)
if __name__=='__main__':main()
