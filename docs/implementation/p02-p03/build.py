"""P02/P03 text-first process candidates; SQL-consumed finite contract fixtures."""
import json,hashlib,sys,copy
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[2];sys.path.insert(0,str(ROOT))
from tools.knowledge_import.importer import Importer,ManifestPin
from tools.knowledge_import.v00_prototype import load_record
B=ROOT/'knowledge/v0.1.0';PKG=B/'learning-process-p02-p03';V='0.1.0-p02-p03-candidate-1'
PACK={'K03':'foundation-r3','K04':'foundation-r3','K05':'practice-teaching-r10','K06':'practice-teaching-r10','K07':'practice-teaching-r10','K08':'practice-teaching-r10','K09':'measurement-r4','K10':'trace-adaptation-resources-r1','K11':'trace-adaptation-resources-r1','K12':'trace-adaptation-resources-r1'}
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dig(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def ref(o,kind,id,package='learning-process',v=V):return dict(owner=o,kind=kind,stable_id=id,package_id=package,version=v)
PREP=[
 ('GOAL','目标协商',['K07.01.01.PT.01','K08.04.01.PT.01','K09.01.01.ME.01'],'本人确认目标、任务条件、表现标准；保留目标版本。','GOAL_CONFIRMED'),
 ('BASELINE','现状与先备核查',['K07.03.01.PT.01','K10.01.05.TR.01','K09.01.03.ME.01'],'仅采纳匹配目标及观测条件的先备证据；缺失保留UNKNOWN，另提补测。','BASELINE_RECORDED'),
 ('RESOURCE','资源与时间',['K07.05.02.PT.01','K11.01.04.TR.01','K08.04.02.PT.01'],'核对时间单位、全部动作成本、可访问资源及明确授权。','RESOURCES_CONFIRMED'),
 ('PLAN','有限计划',['K07.05.01.PT.01','K08.04.02.PT.01','K11.01.03.TR.01'],'给出保留综合目标的候选计划，须本人选择；计划不是已完成行为。','PLAN_SELECTED')]
ACT=[
 ('EXPOSITION','讲解','FACILITATOR','EXPOSITION_DELIVERED','讲解记录：目标、实际呈现与条件，不记录为学习者表现。',['K03.06.02.D4.02','K06.02.01.PT.01','K12.01.01.TR.01']),
 ('DEMONSTRATION','示范','FACILITATOR','DEMONSTRATION_DELIVERED','示范记录：步骤、选择、理由和检查；后续独立操作另测。',['K06.02.02.PT.01','K04.02.01.D4.02','K12.04.01.TR.01']),
 ('DISCRIMINATION','辨别','LEARNER','CLASSIFICATION_RESPONSE','类别、近邻反例、判断依据和规则；表面相似不等于正确归类。',['K03.02.04.D4.02','K05.03.02.PT.01','K12.03.01.TR.01']),
 ('RECALL','回忆','LEARNER','GENERATED_RECALL','无候选生成与有线索回忆分开，记录遗漏和侵入，不用再认替代。',['K05.01.02.PT.01','K05.01.03.PT.01','K12.02.02.TR.01']),
 ('IMITATION','模仿','LEARNER','ASSISTED_OPERATION','记录所用示范、提示和实际操作；模仿不是无辅助掌握。',['K04.02.01.D4.02','K06.03.01.PT.01','K12.02.05.TR.01']),
 ('EXPLANATION','解释','LEARNER','REASONED_EXPLANATION','结论、理由、条件和反例分别观察；篇幅不作理解代理。',['K03.04.03.D4.02','K05.04.01.PT.01','K12.02.03.TR.01']),
 ('PRODUCTION','产出','LEARNER','CONSTRUCTED_PRODUCT','作品、允许工具、版本、本人贡献及评分规则分别绑定。',['K04.06.01.D4.02','K06.04.02.PT.01','K12.02.04.TR.01']),
 ('PROBLEM_SOLVING','问题解决','LEARNER','STRATEGY_AND_EXECUTION','新约束下策略选择、执行、结果和提示分开；同题重做不当迁移。',['K04.01.04.D4.02','K05.03.02.PT.01','K12.04.05.TR.01']),
 ('REFLECTION','反思','LEARNER','SELF_REPORT','学习者自愿重述目标、策略、结果和后续建议；自述不替代任务证据。',['K03.04.03.D4.02','K06.02.04.PT.01','K12.06.01.TR.01'])]
def main():
 dag=load(ROOT/'docs/implementation/task-dag.json');tasks={t['id']:t for t in dag['tasks']}
 idx={};deps=[];cat={}
 for n in sorted(set(PACK.values())):
  b=B/n;m=load(b/'learning-core.manifest.json');v=m['version']
  deps.append(dict(package_id='learning-core',version=v,manifest_sha256=sha(b/'learning-core.manifest.json')))
  for pkg in ('learning-core','evidence'):
   f=b/(pkg+'.manifest.json');cat[pkg,v]=ManifestPin(f.relative_to(ROOT).as_posix(),sha(f))
  for f in m['files']:
   fp=b/f['path'];assert sha(fp)==f['sha256']
   for line in fp.read_text().splitlines():
    r=json.loads(line)
    if r['kind']=='Claim':idx[r['stable_id']]=(r,v,fp)
 design={'P02':PREP,'P03':ACT,'limits':'Authored candidate process templates; no empirical effect, actual learner state, source promotion or runtime permission.'}
 write(P/'design.json',design)
 recs=[];bindings={};used={'P02':{},'P03':{}};fixtures=[]
 def claims(o,ids):
  refs=[]
  for id in ids:
   r,v,fp=idx[id];k=r['owner'];assert k in tasks[o]['depends_on'] and r['status']=='CANDIDATE'
   assert r['claim_type'] in ('PROJECT_RULE','ENGINEERING_POLICY','ORIGINAL_METHOD_DERIVATION','METHOD','MATHEMATICAL_DERIVATION'),(id,r['claim_type'])
   rr=load(ROOT/tasks[k]['current_receipt']);assert any(x['path']==fp.relative_to(ROOT).as_posix() and x['sha256']==sha(fp) for x in rr['output'])
   allowed=rr.get('scope_restriction',{}).get('candidate_claim_ids')
   if allowed is not None:assert id in allowed,id
   used[o][id]={'ref':ref(k,'Claim',id,'learning-core',v),'file':fp.relative_to(ROOT).as_posix(),'file_sha256':sha(fp),'record_sha256':dig(r),'scope':'NONEMPIRICAL_PROJECT_METHOD_ONLY'}
   refs.append(used[o][id]['ref'])
  return refs
 def base(o,k,id,pointer,cr=None):
  r=dict(owner=o,kind=k,stable_id=id,status='CANDIDATE',conditions=['明确目标、版本及适用条件；未知保持HOLD。'],negative_boundary='仅合成项目契约；不证明学习效果、能力或执行授权。',provenance=[dict(source_path=(P/'design.json').relative_to(ROOT).as_posix(),source_sha256=sha(P/'design.json'),json_pointer=pointer,source_status='PROJECT_AUTHORED_TEMPLATE')])
  if cr is not None:r['claim_refs']=cr
  return r
 def add(o,k,id,pointer,cr,**kw):
  recs.append(base(o,k,id,pointer,cr)|kw);return ref(o,k,id)
 def cond(o,id,ptr,cr,flags):
  return add(o,'ConditionSpec',id,ptr,cr,clauses=[dict(field=f,op='EQ',value=v) for f,v in flags.items()],combination='ALL',unknown='HOLD')
 def activity(o,id,label,ptr,ids,method,actor,unit):
  cr=claims(o,ids)
  sk=add(o,'SkillType',id+'.SKILL',ptr,cr,label=label,performance_boundary='仅当前任务与条件；教师呈现、自述、辅助表现和独立表现不合并。')
  ob=add(o,'ObservationSpec',id+'.OBS',ptr,cr,construct_ref=sk,method=method,unit=unit,independence_requirement=('教师呈现仅为实施记录。' if actor=='FACILITATOR' else '本人实际作答及提示状态分别保留；自述不等于表现。'),missing='UNKNOWN_NOT_ZERO')
  goal=add(o,'Goal',id+'.GOAL',ptr,cr,construct_ref=sk,success_evidence_refs=[ob],scope=label+'：'+method)
  obj=add(o,'LearningObject',id+'.OBJECT',ptr,cr,target_refs=[sk],component_refs=[],granularity='当前任务的类型占位；由学科包或本人提供实际内容。')
  role=add(o,'Role',id+'.ROLE',ptr,cr,label=actor,capability_requirements=['明确角色与目标、可用资源'],permission_requirements=['仅明确授权的任务；允许停止'])
  a=add(o,'Activity',id,ptr,cr,goal_refs=[goal],object_refs=[obj],resource_refs=[],role_refs=[role],observation_refs=[ob],budget=1,stop_condition='缺失条件、目标/版本不匹配、退出或预算耗尽时停止。')
  return a,cr
 o='P02';steps=[];trans=[];allcr={}
 for i,(id,label,ids,method,event) in enumerate(PREP):
  ptr=f'/P02/{i}';a,cr=activity(o,'P02.'+id,label,ptr,ids,method,'LEARNER',id+'_RECORD')
  allcr.update({x['stable_id']:x for x in cr});steps.append(dict(id=id,activity_ref=a,max_attempts=1,checkpoint=True))
  fields={'GOAL':{'goal_confirmed':True,'goal_version_match':True},'BASELINE':{'baseline_observed':True,'goal_version_match':True},'RESOURCE':{'resource_ready':True,'authorized':True,'within_budget':True},'PLAN':{'plan_selected':True,'goal_version_match':True,'within_budget':True}}[id]
  c=cond(o,'P02.'+id+'.GUARD',ptr,cr,fields)
  trans.append(dict(from_step=id,to_step=PREP[i+1][0] if i<3 else 'COMPLETE',event=event,condition_ref=c,priority=0,consumes_budget=False))
  trans.extend([dict(from_step=id,to_step='STOP',event='STOP',condition_ref=None,priority=0,consumes_budget=False),dict(from_step=id,to_step='PAUSE',event='PAUSE',condition_ref=None,priority=0,consumes_budget=False)])
  if id=='BASELINE':trans.append(dict(from_step=id,to_step='PAUSE',event='REQUEST_OBSERVATION',condition_ref=cond(o,'P02.BASELINE.UNKNOWN',ptr,cr,{'baseline_observed':False}),priority=0,consumes_budget=False))
  if id=='RESOURCE':trans.append(dict(from_step=id,to_step='PAUSE',event='BUDGET_CONFLICT',condition_ref=cond(o,'P02.RESOURCE.INSUFFICIENT',ptr,cr,{'within_budget':False}),priority=0,consumes_budget=False))
 flow=add(o,'FlowSpec','P02.PREPARATION','/P02',list(allcr.values()),entry='GOAL',steps=steps,transitions=trans,terminals=[dict(id=t,outcome=t) for t in ('COMPLETE','STOP','PAUSE','HOLD','FAILED')],max_events=8,unknown_terminal='HOLD',stop_terminal='STOP',parallel_joins=[],effect='TEMPLATE_ONLY')
 ev=[dict(event='GOAL_CONFIRMED',goal_confirmed=True,goal_version_match=True),dict(event='BASELINE_RECORDED',baseline_observed=True,goal_version_match=True),dict(event='RESOURCES_CONFIRMED',resource_ready=True,authorized=True,cost=3,budget=5),dict(event='PLAN_SELECTED',plan_selected=True,goal_version_match=True,cost=3,budget=5)]
 def case(o,id,target,x,y,view,ptr):
  cr=ref(o,'Case',id);vr=ref(o,'Validation',id+'.VAL')
  recs.append(base(o,'Case',id,ptr)|dict(target_refs=[target],view=view,input_spec=json.dumps(x,ensure_ascii=False,sort_keys=True),expected_spec=y,oracle_ref=vr,actual_status='RECORDED_BUILDER_ONLY'))
  recs.append(base(o,'Validation',id+'.VAL',ptr)|dict(target_refs=[target],case_refs=[cr],method='Exact SQL-loaded finite contract replay',oracle_identity='AUTHOR_FROZEN_CONTRACT_EXPECTATION',input_digest=dig(x),result_digest=dig(y),run_status='BUILDER_RUN'))
  fixtures.append(dict(owner=o,case_id=id,target=target,input=x,expected=y))
 case(o,'P02.F01',flow,ev,'COMPLETE','FORWARD','/P02')
 for i,(step,field,value) in enumerate([(0,'goal_confirmed',False),(0,'goal_version_match',None),(1,'baseline_observed',None),(2,'budget',-1),(2,'budget',2),(2,'authorized',False),(3,'plan_selected',False),(3,'cost',True)],2):
  x=copy.deepcopy(ev);x[step][field]=value;case(o,f'P02.F{i:02}',flow,x,'HOLD','COUNTEREXAMPLE','/P02')
 case(o,'P02.F10',flow,ev[:1]+[dict(event='REQUEST_OBSERVATION',baseline_observed=False)],'PAUSE','REVERSE','/P02')
 case(o,'P02.F11',flow,ev[:2]+[dict(event='BUDGET_CONFLICT',cost=3,budget=2)],'PAUSE','INTERVENTION','/P02')
 case(o,'P02.F12',flow,ev[:2]+[dict(event='STOP')],'STOP','COUNTEREXAMPLE','/P02')
 case(o,'P02.F13',flow,ev[:2],'HOLD','COMPOSITION','/P02')
 x=copy.deepcopy(ev);x[2].pop('cost');x[2].pop('budget');x[2]['within_budget']=True;case(o,'P02.F14',flow,x,'HOLD','COUNTEREXAMPLE','/P02')
 x=copy.deepcopy(ev);x[3]['cost']=4;case(o,'P02.F15',flow,x,'HOLD','COUNTEREXAMPLE','/P02')
 x=copy.deepcopy(ev);x[3]['budget']=6;case(o,'P02.F16',flow,x,'HOLD','COUNTEREXAMPLE','/P02')
 case(o,'P02.F17',flow,ev[:2]+[dict(event='STOP',cost=True)],'STOP','COUNTEREXAMPLE','/P02')
 o='P03'
 for i,(id,label,actor,unit,method,ids) in enumerate(ACT):
  ptr=f'/P03/{i}';id='P03.'+id;a,cr=activity(o,id,label,ptr,ids,method,actor,unit)
  guard=cond(o,id+'.GUARD',ptr,cr,{'authorized':True,'target_match':True,'resource_ready':True,'actor':actor,'observation_kind':unit,'scoring_version_match':True,'support_recorded':True})
  bindings[id]={'activity':a,'guard':guard,'evidence_class':'IMPLEMENTATION_ONLY' if actor=='FACILITATOR' else 'SELF_REPORT_ONLY' if unit=='SELF_REPORT' else 'ASSISTED_ONLY' if unit=='ASSISTED_OPERATION' else 'TASK_OBSERVATION_ONLY'}
  x={'authorized':True,'target_match':True,'resource_ready':True,'actor':actor,'observation_kind':unit,'scoring_version_match':True,'support_recorded':True,'budget':1,'exit':False}
  case(o,id+'.F01',a,x,bindings[id]['evidence_class'],'FORWARD',ptr)
  for j,(k,v) in enumerate([('target_match',False),('actor','FACILITATOR' if actor=='LEARNER' else 'LEARNER'),('observation_kind','UNRELATED'),('support_recorded',None),('resource_ready',False),('scoring_version_match',False),('budget',0),('budget',True)],2):
   y=x|{k:v};case(o,id+f'.F{j:02}',a,y,'HOLD','COUNTEREXAMPLE',ptr)
  case(o,id+'.F10',a,x|{'exit':True},'STOP','INTERVENTION',ptr)
 write(P/'activity-bindings.json',bindings);write(P/'fixtures.json',fixtures)
 PKG.mkdir(parents=True,exist_ok=True)
 files=[]
 for owner in ('P02','P03'):
  rows=[r for r in recs if r['owner']==owner];f=PKG/(owner+'.jsonl');f.write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for r in rows))
  files.append(dict(path=f.name,sha256=sha(f),format='JSONL_RECORDS',record_count=len(rows)))
 m=dict(schema_version='learn-kg-canonical-candidate-1',package_id='learning-process',version=V,status='CANDIDATE',rights='HOLD',owners=['P02','P03'],dependencies=deps,files=files,qualification_receipt_refs=[])
 write(PKG/'learning-process.manifest.json',m);mf=PKG/'learning-process.manifest.json';cat['learning-process',V]=ManifestPin(mf.relative_to(ROOT).as_posix(),sha(mf))
 ext=B/'foundation-r3'/'relation-types.json'
 im=Importer(mode='research',catalog=cat,extension=ManifestPin(ext.relative_to(ROOT).as_posix(),sha(ext)))
 def check(c,x):
  if c is None:return True
  z=load_record(im,c);assert z['combination']=='ALL' and z['unknown']=='HOLD'
  return all(f['op']=='EQ' and type(x.get(f['field'])) is type(f['value']) and x[f['field']]==f['value'] for f in z['clauses'])
 def flow_eval(f,x):
  f=load_record(im,f);s=f['entry'];terms={t['id']:t['outcome'] for t in f['terminals']};seen=set();frozen_cost_budget=None
  for i,event in enumerate(x):
   if s in terms:return terms[s]
   if i>=f['max_events'] or s in seen:return 'HOLD'
   seen.add(s);e=dict(event)
   if e.get('event')=='STOP':return f['stop_terminal']
   if e.get('event') in ('RESOURCES_CONFIRMED','PLAN_SELECTED','BUDGET_CONFLICT'):
    if 'cost' not in e or 'budget' not in e:return 'HOLD'
    a,b=e.get('cost'),e.get('budget')
    if type(a) is not int or type(b) is not int or min(a,b)<0:return 'HOLD'
    e['within_budget']=a<=b
    if e.get('event')=='RESOURCES_CONFIRMED':frozen_cost_budget=(a,b)
    if e.get('event')=='PLAN_SELECTED' and (a,b)!=frozen_cost_budget:return 'HOLD'
   step=next(z for z in f['steps'] if z['id']==s)
   a=load_record(im,step['activity_ref']);assert a['budget']==step['max_attempts']==1
   candidates=[t for t in f['transitions'] if t['from_step']==s and t['event']==e.get('event')]
   if len(candidates)!=1 or not check(candidates[0]['condition_ref'],e):return 'HOLD'
   s=candidates[0]['to_step']
  return terms.get(s,'HOLD')
 def activity_eval(a,x):
  if x.get('exit') is True:return 'STOP'
  if x.get('exit') is not False:return 'HOLD'
  act=load_record(im,a)
  if type(x.get('budget')) is not int or x['budget']<act['budget']:return 'HOLD'
  b=bindings[a['stable_id']]
  return b['evidence_class'] if check(b['guard'],x) else 'HOLD'
 try:
  receipt=im.run(('learning-process',V));results=[]
  for f in fixtures:
   c=load_record(im,ref(f['owner'],'Case',f['case_id']));x=json.loads(c['input_spec']);assert x==f['input'] and c['expected_spec']==f['expected']
   t=c['target_refs'][0];y=flow_eval(t,x) if f['owner']=='P02' else activity_eval(t,x)
   assert y==f['expected'],(f['case_id'],y,f['expected'])
   results.append({'case_id':f['case_id'],'owner':f['owner'],'actual':y,'status':'BUILDER_ONLY'})
  write(P/'results.json',{'status':'SQL_BOUND_FINITE_CONTRACT_CHECK_BUILDER_ONLY','case_count':len(results),'results':results,'manifest_sha256':sha(mf),'fixture_sha256':sha(P/'fixtures.json'),'records':len(recs),'limits':'Finite declared transitions and condition checks only. No real execution, general inference, learning outcomes or independent acceptance.'})
  write(P/'import-receipt.json',receipt)
  write(P/'input-bindings.json',used)
  print('P02',sum(r['owner']=='P02' for r in recs),'P03',sum(r['owner']=='P03' for r in recs),'SQL cases',len(results))
 finally:im.close()
if __name__=='__main__':main()
