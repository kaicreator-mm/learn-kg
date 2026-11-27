"""Build a single cumulative process snapshot; no same-package cross-version refs."""
import json,hashlib,sys,copy,importlib.util,math
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[2];sys.path.insert(0,str(ROOT))
from tools.knowledge_import.importer import Importer,ManifestPin
from tools.knowledge_import.v00_prototype import load_record
from semantic_checks import fixture_rows,evaluate
from inherited import replay as replay_inherited
B=ROOT/'knowledge/v0.1.0';PKG=B/'learning-process-cumulative-r2'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dig(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def ref(o,k,id,v,package='learning-process'):return dict(owner=o,kind=k,stable_id=id,version=v,package_id=package)
def int0(x):return type(x) is int and x>=0
def remap(x,v):
 if isinstance(x,list):return [remap(z,v) for z in x]
 if isinstance(x,dict):
  y={k:remap(z,v) for k,z in x.items()}
  if y.get('package_id')=='learning-process' and y.get('version') in ('0.1.0-p01-candidate-1','0.1.0-p02-p03-candidate-1'):y['version']=v
  return y
 return x
def main():
 d=load(P/'design.json');v=d['version'];dag=load(ROOT/'docs/implementation/task-dag.json');ts={t['id']:t for t in dag['tasks']}
 catalog={};manifest_for={};records={};deps={};binding={};fixtures=[];migration=[];old={}
 for m in sorted(B.glob('*/*manifest.json')):
  z=load(m)
  if 'package_id' not in z or 'version' not in z:continue
  k=(z['package_id'],z['version'])
  if m.parent==PKG:continue
  if k in catalog:assert catalog[k].sha256==sha(m),(k,m)
  catalog[k]=ManifestPin(m.relative_to(ROOT).as_posix(),sha(m));manifest_for[k]=m
 def adddep(k):
  assert k[0]!='learning-process';deps[k]={'package_id':k[0],'version':k[1],'manifest_sha256':catalog[k].sha256}
 for folder in ('learning-process-p01','learning-process-p02-p03'):
  m=B/folder/'learning-process.manifest.json';z=load(m)
  for a in z['dependencies']:adddep((a['package_id'],a['version']))
  for f in z['files']:
   p=m.parent/f['path'];assert sha(p)==f['sha256']
   for l in p.read_text().splitlines():
    r=json.loads(l);id=r['stable_id'];assert id not in records
    new=remap(r,v);records[id]=new;old[id]=r
    migration.append(dict(owner=r['owner'],id=id,source_path=p.relative_to(ROOT).as_posix(),source_sha256=sha(p),old_record_sha256=dig(r),new_record_sha256=dig(new),change='INTERNAL_PROCESS_REF_VERSION_ONLY' if r!=new else 'UNCHANGED'))
 assert len(migration)==490
 def local(id):
  r=records[id];return ref(r['owner'],r['kind'],id,v)
 def claims(o):
  result=[];binding[o]={}
  for id in d[o]['claims']:
   k=id.split('.')[0];assert k in ts[o]['depends_on'];rp=ts[k]['current_receipt'];rr=load(ROOT/rp);allowed=rr.get('scope_restriction',{}).get('candidate_claim_ids')
   if allowed is not None:assert id in allowed
   hits=[]
   for f in rr['output']:
    p=ROOT/f['path']
    if p.suffix!='.jsonl' or k not in p.parts:continue
    assert sha(p)==f['sha256']
    for l in p.read_text().splitlines():
     r=json.loads(l)
     if r['stable_id']==id and r['owner']==k:
      assert r['kind']=='Claim' and r['status']=='CANDIDATE' and r['claim_type'] in ('PROJECT_RULE','ENGINEERING_POLICY','ORIGINAL_METHOD_DERIVATION','METHOD','MATHEMATICAL_DERIVATION')
      hits.append((p,r))
   assert len(hits)==1,(o,id,len(hits));p,r=hits[0]
   mp=p.parent.parent/'learning-core.manifest.json';m=load(mp);key=('learning-core',m['version']);adddep(key)
   assert any((mp.parent/f['path']).resolve()==p.resolve() and f['sha256']==sha(p) for f in m['files'])
   q=ts[k]['qualification_receipt'];assert load(ROOT/q)['reviewed_content_digest']==rr['content_digest']
   z=ref(k,'Claim',id,m['version'],'learning-core');result.append(z)
   binding[o][id]=dict(ref=z,path=p.relative_to(ROOT).as_posix(),sha256=sha(p),record_sha256=dig(r),receipt=rp,receipt_sha256=sha(ROOT/rp),qualification=q,qualification_sha256=sha(ROOT/q))
  return result
 def base(o,k,id,cr=None):
  z=dict(owner=o,kind=k,stable_id=id,status='CANDIDATE',conditions=['当前版本、本人认可目标、明确条件与预算；未知保持HOLD。'],negative_boundary='受限项目模板；不证明真实学习效果、能力、因果或执行授权。',provenance=[dict(source_path=(P/'design.json').relative_to(ROOT).as_posix(),source_sha256=sha(P/'design.json'),json_pointer='/'+o,source_status='PROJECT_AUTHORED_TEMPLATE')])
  if cr is not None:z['claim_refs']=cr
  return z
 def add(o,k,id,cr=None,**kw):
  assert id not in records,id;records[id]=base(o,k,id,cr)|kw;return local(id)
 def cond(o,id,cr,flags):
  return add(o,'ConditionSpec',id,cr,clauses=[dict(field=f,op='EQ',value=y) for f,y in flags.items()],combination='ALL',unknown='HOLD')
 def activity(o,id,cr,label):
  sk=add(o,'SkillType',id+'.SKILL',cr,label=label,performance_boundary='模板步骤记录，不是独立能力结论。')
  ob=add(o,'ObservationSpec',id+'.OBS',cr,construct_ref=sk,method=label,unit='STEP_RECORD',independence_requirement='本人操作、帮助和实际证据分离。',missing='UNKNOWN_NOT_ZERO')
  g=add(o,'Goal',id+'.GOAL',cr,construct_ref=sk,success_evidence_refs=[ob],scope=label)
  obj=add(o,'LearningObject',id+'.OBJECT',cr,target_refs=[sk],component_refs=[],granularity='当前任务类型，须实例化具体对象')
  role=add(o,'Role',id+'.ROLE',cr,label='LEARNER',capability_requirements=['明确目标、角色及资源'],permission_requirements=['本人选择及明确授权；可退出'])
  return add(o,'Activity',id,cr,goal_refs=[g],object_refs=[obj],resource_refs=[],role_refs=[role],observation_refs=[ob],budget=1,stop_condition='未知、退出、版本冲突及预算不足停止')
 def tr(a,b,event,c=None,consume=True,priority=1):return dict(from_step=a,to_step=b,event=event,condition_ref=c,priority=priority,consumes_budget=consume)
 def flow(o,cr,steps,trans,joins,max_events):
  for s in steps:
   trans.extend([tr(s['id'],'STOP','STOP',None,False,0),tr(s['id'],'PAUSE','PAUSE',None,False,0)])
  return add(o,'FlowSpec',o+'.FLOW',cr,entry=steps[0]['id'],steps=steps,transitions=trans,terminals=[dict(id=x,outcome=x) for x in ('COMPLETE','STOP','PAUSE','HOLD','FAILED')],max_events=max_events,unknown_terminal='HOLD',stop_terminal='STOP',parallel_joins=joins,effect='TEMPLATE_ONLY')
 def step(id,ar,n=1):return dict(id=id,activity_ref=ar,max_attempts=n,checkpoint=True)
 def case(o,target,x,y,view='FORWARD'):
  id=o+'.C'+str(1+sum(f['owner']==o for f in fixtures)).zfill(3)
  vr=ref(o,'Validation',id+'.VAL',v);c=ref(o,'Case',id,v)
  add(o,'Case',id,target_refs=[target],view=view,input_spec=json.dumps(x,ensure_ascii=False,sort_keys=True),expected_spec=json.dumps(y,ensure_ascii=False,sort_keys=True,separators=(',',':')) if isinstance(y,dict) else y,oracle_ref=vr,actual_status='RECORDED_BUILDER_ONLY')
  add(o,'Validation',id+'.VAL',target_refs=[target],case_refs=[c],method='Exact SQL-read finite contract replay; author expectation',oracle_identity='AUTHOR_FROZEN_CONTRACT_EXPECTATION',input_digest=dig(x),result_digest=dig(y),run_status='BUILDER_RUN')
  fixtures.append(dict(owner=o,case_id=id,target=target,input=x,expected=y));return c
 def composition(o,cr,target,guards,evidence):
  inp=[local(id) for id in d[o]['inputs']]
  for a in inp:assert a['owner'] in ts[o]['depends_on']
  return add(o,'CompositionSpec',o+'.COMPOSITION',cr,view_id=o,input_refs=inp,output_refs=[target],condition_refs=guards,alternative_refs=[],failure_policy='HOLD/PAUSE/STOP; do not infer missing facts or authorize external actions',evidence_refs=evidence,effect='CANDIDATE_DECISION_ONLY')
 # P04: explicit order-independent two-member join, guarded subflow return, retry and fade.
 o='P04';cr=claims(o);g=[]
 def gc(id,flags):
  z=cond(o,o+'.GUARD.'+id,cr,flags);g.append(z);return z
 steps=[step('START',local('P03.EXPLANATION')),step('A',local('P03.EXPLANATION')),step('B',local('P03.PRODUCTION')),step('SUBFLOW',local('P03.PROBLEM_SOLVING')),step('ASSESS',local('P03.PROBLEM_SOLVING'),2),step('RETRY',local('P03.REFLECTION'))]
 member=gc('MEMBER',{'valid_observation':True})
 transitions=[tr('START','A','START',gc('START',{'mode_match':True,'resource_ready':True})),tr('A','SUBFLOW','MEMBER',member),tr('B','SUBFLOW','MEMBER',member)]
 for result,to in [('COMPLETE','ASSESS'),('PAUSE','PAUSE'),('HOLD','HOLD'),('FAILED','FAILED')]:transitions.append(tr('SUBFLOW',to,'SUBFLOW',gc('SUBFLOW.'+result,{'result':result})))
 transitions.extend([tr('ASSESS','COMPLETE','ASSESS',gc('PASS',{'independent':True,'task_criteria_met':True})),tr('ASSESS','RETRY','ASSESS',gc('FAIL',{'independent':True,'task_criteria_met':False})),tr('RETRY','ASSESS','RETRY',gc('RETRY',{'target_match':True,'learner_opt_in':True}))])
 fade=gc('FADE',{'independent_evidence':True,'risk_acceptable':True,'reversible':True,'learner_opt_in':True})
 for s in ('A','B','ASSESS'):transitions.append(tr(s,s,'FADE',fade))
 alt=gc('ALTERNATIVE',{'same_goal':True,'same_evaluation':True,'learner_opt_in':True})
 transitions.append(tr('START','A','ALTERNATIVE',alt))
 target=flow(o,cr,steps,transitions,[dict(id='ALL_JOIN',members=['A','B'],mode='ALL',resume_policy='Persist member identities; do not pass until both independently recorded; either order only')],12)
 prior=load(ROOT/'docs/implementation/p04-p07-preparation/fixtures.json')
 evs=[case(o,target,f['input'],f['expected'],'FORWARD' if f['expected']=='COMPLETE' else 'COUNTEREXAMPLE') for f in prior if f['owner']==o]
 good=copy.deepcopy(prior[0]['input'])
 for flags,y in [({'same_goal':True,'same_evaluation':True,'learner_opt_in':True},'COMPLETE'),({'same_goal':True,'same_evaluation':False,'learner_opt_in':True},'HOLD')]:
  x=copy.deepcopy(good);x['events'][0]={'id':'s','type':'ALTERNATIVE','version':'V1','cost':1}|flags;evs.append(case(o,target,x,y,'INTERVENTION'))
 x=copy.deepcopy(good);x['events']=[{'type':'STOP'}];x['budget']=None;evs.append(case(o,target,x,'STOP','COUNTEREXAMPLE'))
 x=copy.deepcopy(good);x['events']=None;evs.append(case(o,target,x,'HOLD','COUNTEREXAMPLE'))
 x=copy.deepcopy(good);fa={'type':'FADE','version':'V1','cost':0,'independent_evidence':True,'risk_acceptable':True,'reversible':True,'learner_opt_in':True};x['events'][1:1]=[fa|{'id':'FADE'+str(i)} for i in range(3)];evs.append(case(o,target,x,'HOLD','COUNTEREXAMPLE'))
 composition(o,cr,target,g,evs[:2])
 # P07 advice-only policy. Policy and conditions are SQL-read; derived progress evidence stays bounded.
 o='P07';cr=claims(o);g=[];rules=[]
 def rule(id,flags,action,priority,reason):
  c=cond(o,o+'.GUARD.'+id,cr,flags);g.append(c);rules.append(dict(condition_ref=c,action=action,priority=priority,reason=reason))
 rule('EXIT',{'exit':True},'STOP',0,'明确退出')
 rule('DECLINE',{'declined':True},'DEFER',1,'本人拒绝')
 rule('PAUSE',{'pause_without_resume':True},'PAUSE',2,'没有主动恢复')
 for i,(opt,flags) in enumerate(d[o]['options'].items(),3):
  rule(opt,{'exit':False,'declined':False,'authorized':True,'goal_confirmed':True,'accessible':True,'budget_valid':True,'selected':opt}|flags,'SUGGEST',i,opt)
 target=add(o,'PolicySpec',o+'.POLICY',cr,policy_type='MOTIVATION',rules=rules,unknown_action='CLARIFY',effect='ADVICE_ONLY')
 evs=[case(o,target,f['input'],f['expected'],'INTERVENTION' if f['expected'].startswith('SUGGEST') else 'COUNTEREXAMPLE') for f in prior if f['owner']==o]
 x=copy.deepcopy(next(f['input'] for f in prior if f['owner']==o));x['progress_requested']=1;evs.append(case(o,target,x,'HOLD','COUNTEREXAMPLE'))
 composition(o,cr,target,g,evs[:2])
 # Distinct sequential process witnesses; stage guards and activities are real canonical records.
 for o in ('P05','P06','P08','P09','P10'):
  cr=claims(o);steps=[];trans=[];guards=[];events=[]
  for i,(id,aid,event,flags) in enumerate(d[o]['stages']):
   a=activity(o,aid,cr,d[o]['requirements'][o+'.RQ0'+str(min(i+1,4))]);steps.append(step(id,a))
   c=cond(o,o+'.GUARD.'+id,cr,flags);guards.append(c)
   nxt=d[o]['stages'][i+1][0] if i+1<len(d[o]['stages']) else 'COMPLETE'
   trans.append(tr(id,nxt,event,c));events.append(dict(id='E'+str(i+1),type=event,version='V1',cost=1)|flags)
  target=flow(o,cr,steps,trans,[],len(steps)*2+3)
  x=dict(budget=len(steps),version='V1',authorized=True,goal_confirmed=True,events=events)
  evs=[case(o,target,x,'COMPLETE')]
  for i,(_,_,_,flags) in enumerate(d[o]['stages']):
   for f in flags:
    for bad in (False,None,1):
     y=copy.deepcopy(x);y['events'][i][f]=bad;evs.append(case(o,target,y,'HOLD','COUNTEREXAMPLE'))
  for y,out in [(x|{'budget':len(steps)-1},'HOLD'),(x|{'budget':True},'HOLD'),(x|{'authorized':False},'HOLD'),(x|{'events':events[:-1]},'HOLD'),(x|{'events':events[:1]+[{'type':'STOP'}]},'STOP'),(x|{'events':events[:1]+[{'type':'PAUSE','id':'PAUSE','version':'V1'}]},'PAUSE'),(x|{'events':events[:1]+events},'COMPLETE')]:evs.append(case(o,target,y,out,'COUNTEREXAMPLE'))
  y=copy.deepcopy(x);y['events'][1]['version']='V2';evs.append(case(o,target,y,'HOLD','COUNTEREXAMPLE'))
  y=copy.deepcopy(x);y['events'].insert(1,events[0]|{'cost':0});evs.append(case(o,target,y,'HOLD','COUNTEREXAMPLE'))
  composition(o,cr,target,guards,evs[:2])
 for o,x,y in fixture_rows():case(o,local(o+'.FLOW'),x,y,'COMPOSITION')
 # Write one version with local references only.
 PKG.mkdir(exist_ok=True);files=[]
 for o in [f'P{i:02}' for i in range(1,11)]:
  rows=[r for r in records.values() if r['owner']==o];f=PKG/(o+'.jsonl');f.write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for r in rows))
  files.append(dict(path=f.name,sha256=sha(f),format='JSONL_RECORDS',record_count=len(rows)))
 m=dict(schema_version='learn-kg-canonical-candidate-1',package_id='learning-process',version=v,status='CANDIDATE',rights='HOLD',owners=[f'P{i:02}' for i in range(1,11)],dependencies=list(deps.values()),files=files,qualification_receipt_refs=[])
 mf=PKG/'learning-process.manifest.json';write(mf,m);catalog['learning-process',v]=ManifestPin(mf.relative_to(ROOT).as_posix(),sha(mf))
 write(P/'migration.json',dict(count=len(migration),records=migration,old_versions_preserved=True,limits='Internal process ref version only; no changed professional claims. Prior receipts not current for cumulative snapshot.'))
 write(P/'bindings.json',binding);write(P/'fixtures.json',fixtures)
 write(P/'mode-flow-bindings-current.json',remap(load(ROOT/'docs/implementation/p01-learning-modes/mode-flow-bindings.json'),v))
 write(P/'activity-bindings-current.json',remap(load(ROOT/'docs/implementation/p02-p03/activity-bindings.json'),v))
 ext=B/'foundation-r3'/'relation-types.json';im=Importer(mode='research',catalog=catalog,extension=ManifestPin(ext.relative_to(ROOT).as_posix(),sha(ext)))
 try:
  receipt=im.run(('learning-process',v))
  # Check complete SQL field fidelity of migrated records (old fields all represented).
  for id,r in old.items():
   z=load_record(im,local(id));diffs={k:(z[k],val) for k,val in remap(r,v).items() if k in z and z[k]!=val and not (type(val) is bool and z[k]==str(val).lower())};assert not diffs,(id,'SQL_MIGRATION',diffs)
  for row in load(P/'mode-flow-bindings-current.json')['bindings']:
   m0=load_record(im,row['mode_ref']);f0=load_record(im,row['flow_ref']);assert {r['stable_id'] for r in m0['activity_refs']}=={s['activity_ref']['stable_id'] for s in f0['steps']}
  write(P/'inherited-results.json',replay_inherited(im,local,old,remap,v,ROOT,load_record,check,dig))
  results=[]
  for f in fixtures:
   c=load_record(im,local(f['case_id']));x=json.loads(c['input_spec']);assert x==f['input'] and c['expected_spec']==(json.dumps(f['expected'],ensure_ascii=False,sort_keys=True,separators=(',',':')) if isinstance(f['expected'],dict) else f['expected'])
   t=c['target_refs'][0];a=load_record(im,t)
   y=evaluate(im,a,x,f['owner'],load_record) if x.get('scenario')=='CONCRETE_FINITE' else policy_eval(im,a,x) if f['owner']=='P07' else flow_eval(im,a,x)
   assert y==f['expected'],(f['case_id'],y,f['expected']);results.append(dict(owner=f['owner'],case_id=f['case_id'],actual=y))
  write(P/'import-receipt.json',receipt);write(P/'results.json',dict(status='SQL_BOUND_BUILDER_ONLY',cases=len(results),results=results,manifest_sha256=sha(mf),fixture_sha256=sha(P/'fixtures.json'),migration_count=len(migration),limits='Finite contract replay only. No generic engine, real state, empirical effect, rights, CQ/LC or independent verdict.'))
  print('MIGRATED',len(migration),'NEW',len(records)-len(migration),'SQL CASES',len(results),'PACKAGE',len(records))
 finally:im.close()
def check(im,c,e):
 if c is None:return True
 z=load_record(im,c);assert z['combination']=='ALL' and z['unknown']=='HOLD'
 return all(q['op']=='EQ' and type(e.get(q['field'])) is type(q['value']) and e[q['field']]==q['value'] for q in z['clauses'])
def flow_eval(im,f,x):
 events=x.get('events')
 if not isinstance(events,list) or any(not isinstance(e,dict) for e in events):return 'HOLD'
 if events and events[0].get('type')=='STOP':return f['stop_terminal']
 b=x.get('budget');v=x.get('version')
 if not int0(b) or not isinstance(v,str) or not v or x.get('authorized') is not True or x.get('goal_confirmed') is not True:return 'HOLD'
 state=f['entry'];terms={t['id']:t['outcome'] for t in f['terminals']};steps={s['id']:s for s in f['steps']};seen={};members=set();attempt={};checkpoint=None;support=2
 joins=f['parallel_joins'];join=set(joins[0]['members']) if joins else set()
 for e in events:
  if state in terms:return terms[state]
  if e.get('type')=='STOP':return f['stop_terminal']
  id=e.get('id')
  if not isinstance(id,str) or not id:return 'HOLD'
  if id in seen:
   if e!=seen[id]:return 'HOLD'
   continue
  if len(seen)>=f['max_events'] or e.get('version')!=v:return 'HOLD'
  seen[id]=e;t=e.get('type')
  if checkpoint:
   if t!='RESUME' or e.get('learner_resume') is not True or e.get('checkpoint')!=checkpoint[0]:return 'HOLD'
   checkpoint=None;continue
  if t=='PAUSE':
   ps=[z for z in f['transitions'] if z['from_step']==state and z['event']=='PAUSE' and not z['consumes_budget']]
   if len(ps)!=1:return 'HOLD'
   checkpoint=(id,state);continue
  if state in join and t=='MEMBER':
   member=e.get('member')
   if member not in join or member in members:return 'HOLD'
   state=member
  c=e.get('cost')
  if not int0(c) or c>b:return 'HOLD'
  matches=[z for z in f['transitions'] if z['from_step']==state and z['event']==t and check(im,z['condition_ref'],e)]
  if len(matches)!=1:return 'HOLD'
  z=matches[0];a=load_record(im,steps[state]['activity_ref']);assert steps[state]['activity_ref']['kind']=='Activity'
  if t=='FADE':
   if support<=0:return 'HOLD'
   support-=1
  else:
   attempt[state]=attempt.get(state,0)+1
   if attempt[state]>steps[state]['max_attempts']:return 'HOLD'
  if z['consumes_budget']:b-=c
  if state in join and t=='MEMBER':
   members.add(state)
   if members!=join:
    state=sorted(join-members)[0];continue
  state=z['to_step']
 return 'PAUSE' if checkpoint else terms.get(state,'HOLD')
def policy_eval(im,p,x):
 if x.get('exit') is not True and x.get('exit') is not False:return 'HOLD'
 if x.get('exit') is not True and type(x.get('declined')) is not bool:return 'HOLD'
 y=dict(x);y['pause_without_resume']=x.get('paused') is True and x.get('resume_requested') is not True
 y['budget_valid']=int0(x.get('budget')) and int0(x.get('cost')) and x['cost']<=x['budget']
 early=[r for r in p['rules'] if r['priority']<3 and check(im,r['condition_ref'],y)]
 if early:return min(early,key=lambda r:r['priority'])['action']
 if type(x.get('paused')) is not bool or not y['budget_valid'] or x.get('goal_confirmed') is not True or x.get('authorized') is not True:return 'HOLD'
 options={r['reason'] for r in p['rules'] if r['action']=='SUGGEST'}
 if x.get('selected') not in options:return 'CLARIFY'
 matches=[r for r in p['rules'] if r['action']=='SUGGEST' and check(im,r['condition_ref'],y)]
 if len(matches)!=1:return 'HOLD'
 if 'progress_requested' in x and type(x['progress_requested']) is not bool:return 'HOLD'
 if x.get('progress_requested') is True:
  a,b=x.get('previous'),x.get('current')
  if not isinstance(a,dict) or not isinstance(b,dict) or any(not isinstance(a.get(k),str) or not a[k] or a[k]!=b.get(k) for k in ('goal','scoring_version','support','unit')) or not int0(a.get('score')) or not int0(b.get('score')):return 'REQUEST_OBSERVATION'
  return 'DESCRIBE_TASK_CHANGE_ONLY'
 return 'SUGGEST_'+matches[0]['reason']
if __name__=='__main__':main()
