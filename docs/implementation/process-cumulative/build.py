"""Build a single cumulative process snapshot; no same-package cross-version refs."""
import json,hashlib,sys,copy,importlib.util,math
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[2];sys.path.insert(0,str(ROOT))
from tools.knowledge_import.importer import Importer,ManifestPin
from tools.knowledge_import.v00_prototype import load_record
from semantic_checks import fixture_rows,evaluate,p09
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
 d=load(P/'design.json');p09_contract=load(P/'p09-remediation.json');d['P09']['stages']=p09_contract['stages'];d['P09']['requirements'].update(p09_contract['requirements']);v=d['version'];dag=load(ROOT/'docs/implementation/task-dag.json');ts={t['id']:t for t in dag['tasks']}
 preserved_shards={o:(PKG/(o+'.jsonl')).read_bytes() for o in [f'P{i:02}' for i in range(1,11) if i!=9] if (PKG/(o+'.jsonl')).is_file()}
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
  source=P/'p09-remediation.json' if o=='P09' else P/'design.json'
  pointer='/protocol_id' if o=='P09' else '/'+o
  z=dict(owner=o,kind=k,stable_id=id,status='CANDIDATE',conditions=['当前版本、本人认可目标、明确条件与预算；未知保持HOLD。'],negative_boundary='受限项目模板；不证明真实学习效果、能力、因果或执行授权。',provenance=[dict(source_path=source.relative_to(ROOT).as_posix(),source_sha256=sha(source),json_pointer=pointer,source_status='PROJECT_AUTHORED_TEMPLATE')])
  if cr is not None:z['claim_refs']=cr
  return z
 def add(o,k,id,cr=None,**kw):
  assert id not in records,id;records[id]=base(o,k,id,cr)|kw;return local(id)
 def cond(o,id,cr,flags):
  return add(o,'ConditionSpec',id,cr,clauses=[dict(field=f,op='EQ',value=y) for f,y in flags.items()],combination='ALL',unknown='HOLD')
 def activity(o,id,cr,label):
  sk=add(o,'SkillType',id+'.SKILL',cr,label=label,performance_boundary='模板步骤记录，不是独立能力结论。')
  unit='STEP_RECORD';method=label;independence='本人操作、帮助和实际证据分离。';conditions=['本人操作、帮助和实际证据分离。']
  if o=='P09':
   is_summary=id.endswith('.SUMMARY')
   unit='SUMMARY_RECORD' if is_summary else 'UTC_EPOCH_SECONDS'
   method=label+'；'+('保存阶段摘要且不覆盖原始观测。' if is_summary else '每条观测携带typed LEARNER_SUBJECT identity/version、UTC epoch-second observed_at及独立recorded_at。')
   independence='身份对象精确绑定；event time仅与event time比较，recorded_at仅与recorded_at比较；不跨时钟比较。'
   conditions=(['summary保留即时/延迟/迁移结果分离','goal_reviewed必须明确'] if is_summary else
    ['learner_identity.kind=LEARNER_SUBJECT','learner_identity.subject_id非空且identity_version=V1',
     'time_basis=UTC_EPOCH_SECONDS','time_unit=SECOND',
     'recording_time_basis=UTC_EPOCH_SECONDS','recording_time_unit=SECOND',
     'observed_at与recorded_at分别记录且不跨时钟比较'])
  ob=add(o,'ObservationSpec',id+'.OBS',cr,construct_ref=sk,method=method,unit=unit,independence_requirement=independence,missing='UNKNOWN_NOT_ZERO',conditions=conditions)
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
 def case(o,target,x,y,view='FORWARD',evaluation_kind=None):
  id=o+'.C'+str(1+sum(f['owner']==o for f in fixtures)).zfill(3)
  vr=ref(o,'Validation',id+'.VAL',v);c=ref(o,'Case',id,v)
  add(o,'Case',id,target_refs=[target],view=view,input_spec=json.dumps(x,ensure_ascii=False,sort_keys=True),expected_spec=json.dumps(y,ensure_ascii=False,sort_keys=True,separators=(',',':')) if isinstance(y,dict) else y,oracle_ref=vr,actual_status='RECORDED_BUILDER_ONLY')
  add(o,'Validation',id+'.VAL',target_refs=[target],case_refs=[c],method='Exact SQL-read finite contract replay; author expectation',oracle_identity='AUTHOR_FROZEN_CONTRACT_EXPECTATION',input_digest=dig(x),result_digest=dig(y),run_status='BUILDER_RUN')
  fixture=dict(owner=o,case_id=id,target=target,input=x,expected=y)
  if evaluation_kind is not None:fixture['evaluation_kind']=evaluation_kind
  fixtures.append(fixture);return c
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
  if o=='P09':
   common=[
    dict(field='learner_identity.kind',op='EQ',value='LEARNER_SUBJECT'),
    dict(field='learner_identity.identity_version',op='EQ',value='V1'),
    dict(field='learner_identity.subject_id',op='NE',value=''),
    dict(field='time_basis',op='EQ',value='UTC_EPOCH_SECONDS'),
    dict(field='time_unit',op='EQ',value='SECOND'),
    dict(field='recording_time_basis',op='EQ',value='UTC_EPOCH_SECONDS'),
    dict(field='recording_time_unit',op='EQ',value='SECOND'),
    dict(field='observed_at',op='GT',value=0),
    dict(field='recorded_at',op='GT',value=0),
    dict(field='clock_source_id',op='NE',value=''),
    dict(field='recording_clock_source_id',op='NE',value='')
   ]
   for guard_ref in guards[:3]:
    guard_record=records[guard_ref['stable_id']]
    guard_record['clauses'].extend(copy.deepcopy(common))
    guard_record['conditions'].extend(['每条观测均须绑定非空subject_id、固定identity_version和显式UTC秒时基/单位。'])
    guard_record['negative_boundary']='缺失/错配身份、时基、单位、时钟来源或非正时间戳均HOLD。'
   same=add(o,'ConditionSpec','P09.GUARD.SAME_LEARNER',cr,
    conditions=['即时、延迟和陌生任务迁移观察的subject_id与identity_version必须由语义校验器逐对象比较后得到相同身份结论。'],
    negative_boundary='此守卫只消费语义校验器派生结果；caller boolean或caller复制的subject字段不构成证据。',
    clauses=[dict(field='computed_same_learner_identity',op='EQ',value=True),
             dict(field='immediate_subject_id',op='NE',value=''),
             dict(field='delayed_subject_id',op='NE',value=''),
             dict(field='transfer_subject_id',op='NE',value='')],
    combination='ALL',unknown='HOLD')
   time=add(o,'ConditionSpec','P09.GUARD.TIME_BASIS',cr,
    conditions=['三个event time统一为UTC epoch seconds/SECOND；recorded_at单独记录并只在recording clock stream内验证顺序。'],
    negative_boundary='缺失/混用时基或单位、无有效时钟来源、event chronology或recording chronology错误均HOLD；不跨时钟比较。',
    clauses=[dict(field='time_basis',op='EQ',value='UTC_EPOCH_SECONDS'),
             dict(field='time_unit',op='EQ',value='SECOND'),
             dict(field='recording_time_basis',op='EQ',value='UTC_EPOCH_SECONDS'),
             dict(field='recording_time_unit',op='EQ',value='SECOND'),
             dict(field='clock_source_id',op='NE',value=''),
             dict(field='recording_clock_source_id',op='NE',value=''),
             dict(field='computed_timestamp_order_valid',op='EQ',value=True),
             dict(field='computed_recording_order_valid',op='EQ',value=True)],
    combination='ALL',unknown='HOLD')
   delay=add(o,'ConditionSpec','P09.GUARD.MIN_DELAY',cr,
    conditions=['延迟间隔由delayed.observed_at减immediate.observed_at计算，至少86400秒；novel transfer event time严格晚于delayed。'],
    negative_boundary='86400秒仅为本候选有限协议阈值，不是普遍或最优学习间隔；caller delay_positive/minimum_delay_seconds不构成证据。',
    clauses=[dict(field='computed_delay_seconds',op='GE',value=86400),
             dict(field='minimum_delay_seconds',op='EQ',value=86400),
             dict(field='computed_timestamp_order_valid',op='EQ',value=True)],
    combination='ALL',unknown='HOLD')
   composite=add(o,'ConditionSpec','P09.GUARD.COMPOSITE_VALID',cr,
    conditions=['同一typed learner identity、统一UTC秒时基、至少86400秒派生延迟、严格event/recording顺序和完整summary全部通过才可完成。'],
    negative_boundary='仅由P09语义校验器派生结果驱动；任何身份/时基/间隔/顺序/summary缺失或不匹配均HOLD。',
    clauses=[dict(field='computed_same_learner_identity',op='EQ',value=True),
             dict(field='immediate_subject_id',op='NE',value=''),
             dict(field='delayed_subject_id',op='NE',value=''),
             dict(field='transfer_subject_id',op='NE',value=''),
             dict(field='time_basis',op='EQ',value='UTC_EPOCH_SECONDS'),
             dict(field='time_unit',op='EQ',value='SECOND'),
             dict(field='recording_time_basis',op='EQ',value='UTC_EPOCH_SECONDS'),
             dict(field='recording_time_unit',op='EQ',value='SECOND'),
             dict(field='clock_source_id',op='NE',value=''),
             dict(field='recording_clock_source_id',op='NE',value=''),
             dict(field='computed_delay_seconds',op='GE',value=86400),
             dict(field='minimum_delay_seconds',op='EQ',value=86400),
             dict(field='computed_timestamp_order_valid',op='EQ',value=True),
             dict(field='computed_recording_order_valid',op='EQ',value=True),
             dict(field='evidence_separated',op='EQ',value=True),
             dict(field='goal_reviewed',op='EQ',value=True)],
    combination='ALL',unknown='HOLD')
   guards.extend([same,time,delay,composite])
   policy_gate=p09_contract['policy_gate']
   assert policy_gate['status']=='SUGGEST_DISABLED_UNTIL_SUPPORTED_NONFORGEABLE_FLOW_COMPLETION_BINDING'
   policy=add(o,'PolicySpec','P09.POLICY',cr,
    conditions=[
     '当前DB01 PolicySpec/CompositionSpec与IF01 typed reference合同不能表达绑定精确FlowSpec身份/版本、flow instance、input digest和COMPLETE结果的不可伪造依赖，因此明确移除SUGGEST路由。',
     '仅当内部wrapper以同一package version加载精确P09.FLOW并对同一input对象重新求值为COMPLETE时，才允许REQUEST_OBSERVATION；wrapper不接受caller提供的flow_result、flow_ref、flow_instance_id或input_digest。',
     'HOLD/STOP/PAUSE/FAILED/缺失/未知/格式错误/身份或时间不匹配均不得进入建议路径。'
    ],
    negative_boundary=policy_gate['negative_boundary'],
    policy_type='ASSESSMENT',
    rules=[dict(condition_ref=composite,action='REQUEST_OBSERVATION',reason='FlowSpec精确同输入求值COMPLETE后，仅请求记录有限观察；不产生建议或学习效果结论',priority=1)],
    unknown_action='CLARIFY',effect='ADVICE_ONLY')
   trans[-1]['condition_ref']=composite
   for i,e in enumerate(events[:3]):
    stage=('IMMEDIATE','DELAYED','TRANSFER')[i]
    observed=1800000000+i*86400
    e.update(dict(stage=stage,
                 learner_identity={'kind':'LEARNER_SUBJECT','subject_id':'SUBJECT-01','identity_version':'V1'},
                 time_basis='UTC_EPOCH_SECONDS',time_unit='SECOND',
                 recording_time_basis='UTC_EPOCH_SECONDS',recording_time_unit='SECOND',
                 clock_source_id='SYNTHETIC-UTC-CLOCK-01',
                 recording_clock_source_id='SYNTHETIC-SERVER-UTC-01',
                 observed_at=observed,recorded_at=observed+1,
                 goal='G',scoring_version='S1',
                 family='F2' if stage=='TRANSFER' else 'F1',
                 criteria_met=i!=1,dimension='CONTEXT',construct_match=True,scoring_version_match=True,
                 new_task_family=stage=='TRANSFER',
                 transfer_dimension_declared=stage=='TRANSFER'))
   events[3].update(dict(stage='SUMMARY',evidence_separated=True,goal_reviewed=True))
  target=flow(o,cr,steps,trans,[],len(steps)*2+3)
  x=dict(budget=len(steps),version='V1',authorized=True,goal_confirmed=True,events=events)
  if o=='P09':
   x.update(dict(goal='G',scoring_version='S1',trained_family='F1',transfer_dimension='CONTEXT'))
   records['P09.FLOW']['conditions']=[
    'IMMEDIATE、DELAYED、TRANSFER三条ObservationSpec必须携带完全一致的typed LEARNER_SUBJECT identity对象。',
    '三个observed_at使用UTC_EPOCH_SECONDS/SECOND；recorded_at单独记录，仅在其recording clock stream内检查追加顺序。',
    'DELAYED-IMMEDIATE间隔由时间戳计算且至少86400秒；TRANSFER时间严格晚于DELAYED；不读取caller delay_positive。',
    '86400秒是本候选协议边界，不是普遍或最优学习间隔；所有缺失/冲突/未知保持HOLD。']
   records['P09.FLOW']['negative_boundary']='身份一致性、event time和recording time分别由有限语义校验器验证；不跨时钟比较，不认证真实学习者身份或时钟准确性。'
  evs=[case(o,target,x,'COMPLETE')]
  for i,(_,_,_,flags) in enumerate(d[o]['stages']):
   for f in flags:
    for bad in (False,None,1):
     y=copy.deepcopy(x);y['events'][i][f]=bad;evs.append(case(o,target,y,'HOLD','COUNTEREXAMPLE'))
  for y,out in [(x|{'budget':len(steps)-1},'HOLD'),(x|{'budget':True},'HOLD'),(x|{'authorized':False},'HOLD'),(x|{'events':events[:-1]},'HOLD'),(x|{'events':events[:1]+[{'type':'STOP'}]},'STOP'),(x|{'events':events[:1]+[{'type':'PAUSE','id':'PAUSE','version':'V1'}]},'PAUSE'),(x|{'events':events[:1]+events},'COMPLETE')]:evs.append(case(o,target,y,out,'COUNTEREXAMPLE'))
  y=copy.deepcopy(x);y['events'][1]['version']='V2';evs.append(case(o,target,y,'HOLD','COUNTEREXAMPLE'))
  y=copy.deepcopy(x);y['events'].insert(1,events[0]|{'cost':0});evs.append(case(o,target,y,'HOLD','COUNTEREXAMPLE'))
  composition(o,cr,target,guards,evs[:2])
  if o=='P09':
   records['P09.COMPOSITION']['output_refs'].append(policy)
   records['P09.COMPOSITION']['conditions']=[
    '每条即时/延迟/迁移ObservationSpec必须携带相同typed learner_identity，subject_id与identity_version精确一致。',
    '延迟间隔只从UTC epoch-second observed_at相减计算，阈值86400秒仅为本候选有限协议边界。',
    'recorded_at使用独立recording time basis/unit，只验证其自身顺序；绝不与observed_at跨时钟比较。',
    'caller delay_positive与caller minimum_delay_seconds均不作为证据；缺失、冲突和未知保持HOLD。',
    '当前DB01/IF01无法表达不可伪造FlowSpec完成结果绑定，因此移除PolicySpec的SUGGEST规则。',
    '仅内部wrapper加载与PolicySpec同package version的精确P09.FLOW并使用同一input重新求值COMPLETE后，才允许REQUEST_OBSERVATION。']
   records['P09.COMPOSITION']['failure_policy']='任何身份不一致、时间单位/时基混用、延迟不足、时间顺序错误、recording顺序错误或summary缺失均HOLD；STOP/PAUSE原样传播。当前canonical contract无法表达不可伪造FlowSpec完成依赖，故PolicySpec无SUGGEST规则；仅精确P09.FLOW同版本/同输入内部求值COMPLETE后可REQUEST_OBSERVATION。'
   p09_policy_ref=policy
   p09_policy_base_input=copy.deepcopy(x)
 for o,x,y in fixture_rows():case(o,local(o+'.FLOW'),x,y,'COMPOSITION')
 # P09 policy-gate cases are separate from FlowSpec cases. They exercise the
 # only supported ADVICE_ONLY route after an internally re-evaluated exact flow.
 def p09_policy_case(x,expected):
  case('P09',p09_policy_ref,copy.deepcopy(x),expected,'COMPOSITION','P09_POLICY_GATE')
 policy_base=copy.deepcopy(p09_policy_base_input)
 p09_policy_case(policy_base,'REQUEST_OBSERVATION')
 x=copy.deepcopy(policy_base);x['events'][1]['learner_identity']['subject_id']='SUBJECT-OTHER'
 x.update(dict(computed_same_learner_identity=True,immediate_subject_id='SUBJECT-01',delayed_subject_id='SUBJECT-01',transfer_subject_id='SUBJECT-01',computed_delay_seconds=86400,minimum_delay_seconds=86400,computed_timestamp_order_valid=True,computed_recording_order_valid=True,evidence_separated=True,goal_reviewed=True))
 x['flow_result']=dict(status='COMPLETE',flow_instance_id='OTHER-FLOW',input_sha256='0'*64,version='V0')
 p09_policy_case(x,'HOLD')
 x=copy.deepcopy(policy_base);x['events'][1]['observed_at']=x['events'][0]['observed_at']+86399;x['events'][2]['observed_at']=x['events'][1]['observed_at']+86400
 x.update(dict(computed_delay_seconds=86400,minimum_delay_seconds=86400,computed_timestamp_order_valid=True,computed_recording_order_valid=True))
 p09_policy_case(x,'HOLD')
 x=copy.deepcopy(policy_base);x['events'][2]['learner_identity']['subject_id']='SUBJECT-OTHER'
 x.update(dict(computed_same_learner_identity=True,immediate_subject_id='SUBJECT-01',delayed_subject_id='SUBJECT-01',transfer_subject_id='SUBJECT-01',computed_delay_seconds=86400,minimum_delay_seconds=86400,computed_timestamp_order_valid=True,computed_recording_order_valid=True))
 p09_policy_case(x,'HOLD')
 x=copy.deepcopy(policy_base);x['events'][1]['learner_identity']['subject_id']='SUBJECT-OTHER'
 x['events'][3].update(dict(evidence_separated=True,goal_reviewed=True))
 x.update(dict(computed_same_learner_identity=True,computed_delay_seconds=86400,computed_timestamp_order_valid=True,computed_recording_order_valid=True))
 p09_policy_case(x,'HOLD')
 x=copy.deepcopy(policy_base);x['events']=None;x['flow_result']=dict(status='COMPLETE',flow_ref=dict(owner='P09',kind='FlowSpec',stable_id='P09.FLOW',version='0.1.0-process-candidate-1',package_id='learning-process'))
 p09_policy_case(x,'HOLD')
 x=copy.deepcopy(policy_base);x['flow_result']=dict(status='COMPLETE',flow_instance_id='OTHER-FLOW',input_sha256=dig(policy_base),version=v)
 p09_policy_case(x,'REQUEST_OBSERVATION')
 x=copy.deepcopy(policy_base);x['flow_result']=dict(status='COMPLETE',flow_instance_id='P09:'+dig(policy_base),input_sha256='f'*64,version=v)
 p09_policy_case(x,'REQUEST_OBSERVATION')
 x=copy.deepcopy(policy_base);x['flow_result']=dict(status='COMPLETE',flow_instance_id='P09:'+dig(policy_base),input_sha256=dig(policy_base),version='0.1.0-process-candidate-1',flow_ref=dict(owner='P09',kind='FlowSpec',stable_id='P09.FLOW',version='0.1.0-process-candidate-1',package_id='learning-process'))
 p09_policy_case(x,'REQUEST_OBSERVATION')
 x=copy.deepcopy(policy_base);x['events']=[dict(type='STOP')]
 p09_policy_case(x,'STOP')
 x=copy.deepcopy(policy_base);x['events']=[dict(type='PAUSE')]
 p09_policy_case(x,'PAUSE')
 x=copy.deepcopy(policy_base);x['events']=[dict(type='UNKNOWN')]
 p09_policy_case(x,'HOLD')
 # Write one version with local references only.
 PKG.mkdir(exist_ok=True);files=[]
 for o in [f'P{i:02}' for i in range(1,11)]:
  f=PKG/(o+'.jsonl')
  if o=='P09':
   rows=[r for r in records.values() if r['owner']==o]
   f.write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for r in rows))
  else:
   assert o in preserved_shards and f.read_bytes()==preserved_shards[o],(o,'CANONICAL_SHARD_MUST_REMAIN_BYTE_IDENTICAL')
  on_disk=[json.loads(line) for line in f.read_text().splitlines()]
  files.append(dict(path=f.name,sha256=sha(f),format='JSONL_RECORDS',record_count=len(on_disk)))
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
   if f.get('evaluation_kind')=='P09_POLICY_GATE':
    y=p09_policy_eval(im,t,x)
   elif x.get('scenario')=='CONCRETE_FINITE':
    y=evaluate(im,a,x,f['owner'],load_record)
   elif f['owner']=='P07':
    y=policy_eval(im,a,x)
   else:
    y=flow_eval(im,a,x,f['owner'])
   assert y==f['expected'],(f['case_id'],y,f['expected'],x);results.append(dict(owner=f['owner'],case_id=f['case_id'],actual=y))
  write(P/'import-receipt.json',receipt);write(P/'results.json',dict(status='SQL_BOUND_BUILDER_ONLY',cases=len(results),results=results,manifest_sha256=sha(mf),fixture_sha256=sha(P/'fixtures.json'),migration_count=len(migration),limits='Finite contract replay only. No generic engine, real state, empirical effect, rights, CQ/LC or independent verdict.'))
  print('MIGRATED',len(migration),'NEW',len(records)-len(migration),'SQL CASES',len(results),'PACKAGE',len(records))
 finally:im.close()
def check(im,c,e):
 if c is None:return True
 z=load_record(im,c);assert z['combination'] in ('ALL','ANY') and z['unknown']=='HOLD'
 def value(path):
  if path in e:return True,e[path]
  cur=e
  for part in path.split('.'):
   if not isinstance(cur,dict) or part not in cur:return False,None
   cur=cur[part]
  return True,cur
 def clause(q):
  exists,actual=value(q['field'])
  if not exists:return False
  expected=q['value'];op=q['op']
  if op=='EQ':return type(actual) is type(expected) and actual==expected
  if op=='NE':return type(actual) is type(expected) and actual!=expected
  if op in ('LT','LE','GT','GE'):
   if type(actual) not in (int,float) or type(expected) not in (int,float):return False
   return {'LT':actual<expected,'LE':actual<=expected,'GT':actual>expected,'GE':actual>=expected}[op]
  return False
 values=[clause(q) for q in z['clauses']]
 return all(values) if z['combination']=='ALL' else any(values)
def p09_flow_eval(im,f,x):
 events=x.get('events')
 if not isinstance(events,list) or any(not isinstance(e,dict) for e in events):return 'HOLD'
 if any(e.get('type')=='STOP' for e in events):return 'STOP'
 if any(e.get('type')=='PAUSE' for e in events):return 'PAUSE'
 if (not int0(x.get('budget')) or not isinstance(x.get('version'),str) or not x['version']
     or x.get('authorized') is not True or x.get('goal_confirmed') is not True
     or not all(isinstance(x.get(k),str) and x[k] for k in ('goal','scoring_version','trained_family','transfer_dimension'))):return 'HOLD'
 unique=[];seen={}
 for event in events:
  event_id=event.get('id')
  if not isinstance(event_id,str) or not event_id.strip():return 'HOLD'
  if event_id in seen:
   if event!=seen[event_id]:return 'HOLD'
   continue
  seen[event_id]=event;unique.append(event)
 if len(unique)!=4 or len(unique)>f['max_events']:return 'HOLD'
 if any(e.get('version')!=x['version'] or not int0(e.get('cost')) for e in unique):return 'HOLD'
 if sum(e['cost'] for e in unique)>x['budget']:return 'HOLD'
 expected=[('IMMEDIATE','IMMEDIATE_RECORDED'),('DELAYED','DELAYED_RECORDED'),
           ('TRANSFER','TRANSFER_RECORDED'),('SUMMARY','SUMMARY_RECORDED')]
 if any(e.get('stage')!=stage or e.get('type')!=event_type for e,(stage,event_type) in zip(unique,expected)):return 'HOLD'
 observations=[{k:v for k,v in e.items() if k not in ('type','version','cost')} for e in unique[:3]]
 result=p09(dict(goal=x['goal'],scoring_version=x['scoring_version'],trained_family=x['trained_family'],
                 transfer_dimension=x['transfer_dimension'],observations=observations))
 if result=='HOLD':return 'HOLD'
 # Check each stage's SQL-read guard against the raw event object.
 for step_id,event_type,event in [('IMMEDIATE','IMMEDIATE_RECORDED',unique[0]),
                                  ('DELAYED','DELAYED_RECORDED',unique[1]),
                                  ('NOVEL','TRANSFER_RECORDED',unique[2])]:
  transition=next((t for t in f['transitions'] if t['from_step']==step_id and t['event']==event_type),None)
  if transition is None or not check(im,transition['condition_ref'],event):return 'HOLD'
 summary=unique[3]
 # The SUMMARY step's own event contract is represented by its declared activity observation.
 # The composite completion guard consumes only values derived here, never caller booleans.
 derived=dict(computed_same_learner_identity=result['computed_same_learner_identity'],
              immediate_subject_id=result['immediate_subject_id'],
              delayed_subject_id=result['delayed_subject_id'],
              transfer_subject_id=result['transfer_subject_id'],
              time_basis=result['time_basis'],time_unit=result['time_unit'],
              recording_time_basis=result['recording_time_basis'],recording_time_unit=result['recording_time_unit'],
              clock_source_id=result['clock_source_id'],recording_clock_source_id=result['recording_clock_source_id'],
              computed_delay_seconds=result['computed_delay_seconds'],
              minimum_delay_seconds=result['minimum_delay_seconds'],
              computed_timestamp_order_valid=result['computed_timestamp_order_valid'],
              computed_recording_order_valid=result['computed_recording_order_valid'])
 # Summary fields must be checked separately before the final composite condition.
 summary_spec=next((t for t in f['transitions'] if t['from_step']=='SUMMARY' and t['to_step']=='COMPLETE'),None)
 if summary_spec is None:return 'HOLD'
 # A dedicated summary guard is in the FlowSpec's claim-linked condition refs.
 # The final composite condition also includes both summary fields.
 if not check(im,summary_spec['condition_ref'],summary|derived):return 'HOLD'
 return 'COMPLETE'

def flow_eval(im,f,x,owner=None):
 if owner=='P09':return p09_flow_eval(im,f,x)
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
 # P09 PolicySpec is intentionally non-suggesting. The generic evaluator never
 # executes its observation route; only p09_policy_eval() may do so after an
 # internal same-version/same-input FlowSpec re-evaluation.
 rules=p.get('rules')
 if not isinstance(rules,list):return 'HOLD'
 p09_policy=any(
  isinstance(r,dict) and isinstance(r.get('condition_ref'),dict)
  and r['condition_ref'].get('owner')=='P09'
  for r in rules
 )
 if p09_policy:
  if any(not isinstance(r,dict) for r in rules):return 'HOLD'
  if any(r.get('action')=='SUGGEST' for r in rules):return 'HOLD'
  return 'CLARIFY'
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

def p09_policy_eval(im,policy_ref,x):
 """Fail-closed P09 policy wrapper: exact same-version FlowSpec + same input.

 The current canonical DB01/IF01 contract cannot persist a non-forgeable flow
 completion result bound to a flow instance and input digest. Therefore the
 PolicySpec has no SUGGEST rule. This wrapper re-loads the exact P09.FLOW ref
 at the PolicySpec version, evaluates that flow with this exact input object,
 and permits only the declared ADVICE_ONLY REQUEST_OBSERVATION route.
 Caller-supplied flow_result/flow_ref/flow_instance_id/input_digest are ignored.
 """
 if type(policy_ref) is not dict or type(x) is not dict:return 'HOLD'
 version=policy_ref.get('version')
 expected_policy=ref('P09','PolicySpec','P09.POLICY',version)
 if policy_ref!=expected_policy:return 'HOLD'
 flow_ref=ref('P09','FlowSpec','P09.FLOW',version)
 try:
  policy=load_record(im,policy_ref);flow_record=load_record(im,flow_ref)
 except Exception:
  return 'HOLD'
 # load_record resolves each object through its exact typed reference tuple;
 # the imported payload omits DB identity columns, so do not expect those
 # columns to be duplicated inside the canonical JSON payload.
 if policy.get('effect')!='ADVICE_ONLY' or not isinstance(flow_record,dict):
  return 'HOLD'
 rules=policy.get('rules')
 if type(rules) is not list or len(rules)!=1:return 'HOLD'
 composite_ref=ref('P09','ConditionSpec','P09.GUARD.COMPOSITE_VALID',version)
 route=rules[0]
 if (type(route) is not dict or route.get('action')!='REQUEST_OBSERVATION'
     or route.get('condition_ref')!=composite_ref
     or route.get('priority')!=1):
  return 'HOLD'
 # Snapshot only plain JSON values. The wrapper evaluates this immutable-by-
 # convention copy, not caller-owned mutable state or caller-supplied results.
 def plain_json(value):
  if value is None or type(value) in (str,int,bool):return True
  if type(value) is float:return value==value and abs(value)!=float('inf')
  if type(value) is list:return all(plain_json(v) for v in value)
  if type(value) is dict:return all(type(k) is str and plain_json(v) for k,v in value.items())
  return False
 if not plain_json(x):return 'HOLD'
 try:
  original_digest=dig(x)
  snapshot=json.loads(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False))
 except (TypeError,ValueError,OverflowError):
  return 'HOLD'
 input_digest=dig(snapshot)
 try:
  if input_digest!=original_digest or dig(x)!=original_digest:return 'HOLD'
  flow_result=p09_flow_eval(im,flow_record,snapshot)
  if dig(snapshot)!=input_digest or dig(x)!=original_digest:return 'HOLD'
 except Exception:
  return 'HOLD'
 if flow_result in ('STOP','PAUSE','HOLD','FAILED'):return flow_result
 if flow_result!='COMPLETE':return 'HOLD'
 return route['action']

if __name__=='__main__':main()
