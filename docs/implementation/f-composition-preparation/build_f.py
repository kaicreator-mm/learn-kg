"""Build the next cumulative learning-process snapshot on a preparation branch.

The current P01-P10 package is copied as a single new snapshot because DB01
intentionally rejects cross-version references within one package. No current
version-branch receipt is modified here.
"""
import json,hashlib,sys,copy
from pathlib import Path
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[3]
DOC=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from tools.knowledge_import.importer import Importer,ManifestPin
from tools.knowledge_import.v00_prototype import load_record
from semantic_checks import FUN,fixtures,dig,VISUAL_ACCESSIBILITY_EVIDENCE,F04_CLOCK_CONTRACT,F05_SCORING_VERSION_PIN

B=ROOT/'knowledge/v0.1.0'
OLD=B/'learning-process-cumulative-r2'
PKG=B/'learning-process-cumulative-r3'
VERSION='0.1.0-process-candidate-3'
OWNERS=['P01','P02','P03','P04','P05','P06','P07','P08','P09','P10','F03','F04','F05','F07','A07','E01']
ACCEPTED_TYPES={'PROJECT_RULE','ENGINEERING_POLICY','ORIGINAL_METHOD_DERIVATION','METHOD','MATHEMATICAL_DERIVATION'}
ANALYSIS_PLAN_REF='docs/implementation/f-composition-preparation/analysis-plan.json'
ANALYSIS_PLAN={
 'artifact_id':'E01.ANALYSIS_PLAN',
 'version':'V2',
 'protocol_id':'E01.PROTOCOL',
 'population':{
  'population_id':'LEARN_KG_SYNTHETIC_CANDIDATE_SCOPE_V2',
  'inclusion':'仅限未来经单独批准、明确同意并满足纳入条件的目标学习者群体；当前无实际招募或研究人群。',
  'exclusion':'未同意、身份/授权不明、无法按协议安全参与或超出本协议适用边界的对象。',
  'scope':'候选研究设计模板；不得外推到未定义总体。'
 },
 'allocation':{'unit':'LEARNER','method':'RANDOMIZED','assignment_verified_required':True},
 'intervention':{'policy_id':'E01.POLICY.CANDIDATE','version':'CANDIDATE_V1'},
 'comparator':{'policy_id':'E01.POLICY.CURRENT','version':'CURRENT_V1'},
 'primary_outcome':{'id':'E01.OBS.PRIMARY_OUTCOME','definition':'预先固定的任务版本、评分版本、分母和28日主要结果；当前未采集任何真实结果。'},
 'followup':{'days':28,'window':'从预先登记的分配时点起算28日','incomplete':'未完成随访记为缺失/未观测，不插补为成功或失败。'},
 'analysis_plan_summary':'预先定义学习者层随机分配、候选与当前策略版本、主要结果、28日随访、ITT estimand、缺失数据与安全事件分开报告；在真实批准和独立复核证据缺失时不执行效果分析。',
 'estimand':'仅在分配方法经独立核验、处理版本固定、主要结果有效且识别条件满足时，描述分配至候选可拒绝支持建议相对当前流程的28日ITT差；不估计依从者效应，不从模拟或非随机观察推断因果。',
 'analysis_rules':{
  'primary':'ITT；按预先登记的学习者分配单位分析。',
  'missing':'报告缺失模式和分母；不将缺失设为零，不把未完成随访当作成功。',
  'safety':'退出、拒绝及不利事件独立报告；不以完成率抵消。',
  'multiplicity':'当前无次要结果的推断性检验。',
  'release':'分析结果不自动写入正式知识；须另行授权、独立复核和版本化发布。'
 },
 'required_evidence':{
  'approval':'RESEARCH_PROTOCOL_APPROVAL_RECEIPT with repository, issue/comment identity, artifact path/hash, subject E01.PROTOCOL@V2 and this plan SHA256.',
  'independent_review':'INDEPENDENT_NON_WRITER_REVIEW_RECEIPT with repository, issue/comment identity, artifact path/hash, subject E01.PROTOCOL@V2 and this plan SHA256.'
 },
 'authority_status':'NO_TRUSTED_APPROVAL_OR_REVIEW_RESOLVER_BOUND',
 'data_status':'NO_REAL_COMPLIANT_RESEARCH_DATA',
 'release_status':'NOT_AUTHORIZED'
}
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def ref(owner,kind,id,version=VERSION,package='learning-process'):
 return {'package_id':package,'version':version,'kind':kind,'stable_id':id,'owner':owner}
def remap(x):
 if isinstance(x,list):return [remap(z) for z in x]
 if isinstance(x,dict):
  y={k:remap(z) for k,z in x.items()}
  if y.get('package_id')=='learning-process' and y.get('version')=='0.1.0-process-candidate-2':y['version']=VERSION
  return y
 return x
def main():
 write(DOC/'analysis-plan.json',ANALYSIS_PLAN)
 design=load(DOC/'design.json');design['modules'].update(load(DOC/'remediation-design.json')['modules']);tasks={x['id']:x for x in load(ROOT/'docs/implementation/task-dag.json')['tasks']}
 old_manifest=load(OLD/'learning-process.manifest.json')
 records={};old_records={};bindings={};deps={}
 schema_defs=load(ROOT/'docs/implementation/db01/canonical.schema.json')['$defs']
 for f in old_manifest['files']:
  p=OLD/f['path'];assert sha(p)==f['sha256'],p
  for line in p.read_text(encoding='utf-8').splitlines():
   r=json.loads(line);assert r['stable_id'] not in records
   records[r['stable_id']]=remap(r);old_records[r['stable_id']]=r
 assert len(records)==1312
 # Load all package manifests, preserving exact source manifest pins.
 catalog={}
 for m in B.glob('*/*manifest.json'):
  z=load(m)
  if not {'package_id','version'}<=z.keys():continue
  k=(z['package_id'],z['version']);pin=ManifestPin(m.relative_to(ROOT).as_posix(),sha(m))
  if k in catalog:assert catalog[k].sha256==pin.sha256,(k,m)
  catalog[k]=pin
 def adddep(key):
  assert key in catalog,key
  deps[key]={'package_id':key[0],'version':key[1],'manifest_sha256':catalog[key].sha256}
 for x in old_manifest['dependencies']:adddep((x['package_id'],x['version']))
 def local(id):
  r=records[id];return ref(r['owner'],r['kind'],id)
 def claims(owner,ids):
  assert owner not in bindings;bindings[owner]={};out=[]
  for id in ids:
   k=id.split('.')[0];assert k in tasks[owner]['depends_on'],(owner,k)
   t=tasks[k];rp=ROOT/t['current_receipt'];rr=load(rp);qp=ROOT/t['qualification_receipt'];qr=load(qp)
   assert qr['reviewed_content_digest']==rr['content_digest'],(owner,id,'qualification_digest')
   s=rr['scope_restriction'];allowed=set(s.get('candidate_claim_ids',[]))
   assert id in allowed,(owner,id,'not_in_restricted_allowlist')
   assert id not in set(s.get('source_limited_candidate_claim_ids',[])),(owner,id,'source_limited')
   assert id not in set(s.get('model_claim_ids',[])),(owner,id,'model_claim_not_allowed')
   hits=[]
   for o in rr['output']:
    p=ROOT/o['path']
    if p.suffix!='.jsonl':continue
    assert sha(p)==o['sha256'],(k,p)
    for line in p.read_text(encoding='utf-8').splitlines():
     r=json.loads(line)
     if r['stable_id']==id and r['owner']==k:hits.append((p,r))
   assert len(hits)==1,(owner,id,len(hits))
   p,r=hits[0]
   assert r['kind']=='Claim' and r['status']=='CANDIDATE' and r['claim_type'] in ACCEPTED_TYPES,(owner,id,r.get('claim_type'),r.get('status'))
   assert r['source_status'] not in ('HOLD','UNVERIFIED_SOURCE','SOURCE_UNVERIFIED'),(owner,id,r['source_status'])
   mp=None
   for parent in p.parents:
    candidate=parent/'learning-core.manifest.json'
    if candidate.exists():mp=candidate;break
   assert mp is not None,(id,p)
   lm=load(mp);key=('learning-core',lm['version']);adddep(key)
   assert any((mp.parent/f['path']).resolve()==p.resolve() and f['sha256']==sha(p) for f in lm['files'])
   z=ref(k,'Claim',id,lm['version'],'learning-core');out.append(z)
   bindings[owner][id]={'ref':z,'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'record_sha256':dig(r),'candidate_receipt':t['current_receipt'],'candidate_receipt_sha256':sha(rp),'candidate_content_digest':rr['content_digest'],'qualification_receipt':t['qualification_receipt'],'qualification_receipt_sha256':sha(qp),'qualification_content_digest':qr['content_digest']}
  return out
 def base(owner,kind,id,cr,conditions,negative):
  design_source=DOC/('remediation-design.json' if owner in {'F03','F04','F05','F07','A07','E01'} else 'design.json')
  z={'owner':owner,'kind':kind,'stable_id':id,'status':'CANDIDATE','conditions':conditions,'negative_boundary':negative,'provenance':[{'source_path':design_source.relative_to(ROOT).as_posix(),'source_sha256':sha(design_source),'json_pointer':'/modules/'+owner,'source_status':'PROJECT_AUTHORED_CANDIDATE_DESIGN'}]}
  if 'claim_refs' in schema_defs[kind]['properties']:z['claim_refs']=cr
  return z
 def add(owner,kind,id,cr,conditions,negative,**kw):
  assert id not in records,id
  records[id]=base(owner,kind,id,cr,conditions,negative)|kw
  return local(id)
 def cond(owner,id,cr,clauses,conditions):
  return add(owner,'ConditionSpec',id,cr,conditions,'仅为有限合成判别；缺失/未知不构成肯定条件。',clauses=clauses,combination='ALL',unknown='HOLD')
 def case(owner,name,target,x,y,view='FORWARD'):
  cid=owner+'.'+name
  assert cid not in records
  inp=json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
  exp=json.dumps(y,ensure_ascii=False,sort_keys=True,separators=(',',':')) if isinstance(y,(dict,list)) else str(y)
  c=add(owner,'Case',cid,owner_claims[owner],['仅合成输入；按冻结的本模块有限守卫执行。'],'本例不代表真实学习者、实证效果、许可或授权。',target_refs=[target],view=view,input_spec=inp,expected_spec=exp,oracle_ref=None,actual_status='RECORDED_BUILDER_ONLY')
  vid=cid+'.VAL'
  v=add(owner,'Validation',vid,owner_claims[owner],['只回放本项目声明的有限合同。'],'Builder结果不是独立oracle、CQ/LC通过或专业资格。',target_refs=[target],case_refs=[c],method='DETERMINISTIC_FINITE_BUILDER_REPLAY',oracle_identity='PROJECT_AUTHORED_EXPECTATION_NOT_INDEPENDENT',input_digest=dig(x),result_digest=dig(y),run_status='BUILDER_RUN')
  records[cid]['oracle_ref']=v
  return c,v
 def composition(owner,cr,inputs,outputs,guards,negative):
  return add(owner,'CompositionSpec',owner+'.COMPOSITION',cr,['受限视图；只定义输入、候选输出和失败边界。'],negative,view_id=owner,input_refs=inputs,output_refs=outputs,condition_refs=guards,alternative_refs=[],evidence_refs=[],effect='CANDIDATE_DECISION_ONLY',failure_policy='未知/无效/冲突HOLD；退出STOP；未授权REFUSE；不得自动执行或写正式知识。')
 def obs(owner,id,cr,construct,method,unit,independence):
  return add(owner,'ObservationSpec',id,cr,['观测目标、任务版本、时间及支持条件明确。'],'观测不等于潜在能力或稳定人格。',construct_ref=construct,method=method,unit=unit,independence_requirement=independence,missing='UNKNOWN_NOT_ZERO')
 # F03 resource and modality
 o='F03';cr=claims(o,design['modules'][o]['claims']);owner_claims={o:cr}
 mods={}
 for suffix,label,cap,not_eq in [
  ('TEXT','TEXT',['text rendering','language metadata'],['AUDIO_LISTENING','SPEECH_PRODUCTION']),
  ('AUDIO','AUDIO',['playback','volume control','audio access'],['TEXT_READING','VISUAL_RECOGNITION']),
  ('VISUAL','VISUAL',['visual rendering','alternative description'],['AUDIO_LISTENING'])]:
  mods[suffix]=add(o,'Modality',o+'.MOD.'+suffix,cr,['目标构念和实际可用通道明确。'],'通道标签不证明可及性或等价性。',label=label,capability_requirements=cap,not_equivalent_to=not_eq)
 resources={}
 for suffix,rights,mod,access in [('TEXT','PUBLIC_AUTHORIZED','TEXT',['private test only','text reader support']),('AUDIO','PUBLIC_AUTHORIZED','AUDIO',['private test only','playback required']),('UNVERIFIED','HOLD','AUDIO',['source and access not verified']),('VISUAL','PUBLIC_AUTHORIZED','VISUAL',['visual rendering tested','alternative description tested'])]:
  resources[suffix]=add(o,'Resource',o+'.RES.'+suffix,cr,['资源身份和版本已声明；内容未嵌入此候选。'],'PRIVATE_ONLY不可公开；HOLD不得消费；下载可用不等于再发布许可。',resource_identity='urn:learn-kg:synthetic:'+suffix.lower()+':v1',rights=rights,modality_refs=[mods[mod]],accessibility=access)
 g={}
 g['AUDIO']=cond(o,o+'.GUARD.AUDIO',cr,[{'field':'permission','op':'EQ','value':True},{'field':'rights','op':'EQ','value':'PUBLIC_AUTHORIZED'},{'field':'accessible','op':'EQ','value':True},{'field':'modality','op':'EQ','value':'AUDIO'},{'field':'required_construct','op':'EQ','value':'LISTENING'}],['权限、权利、可及性、模态和构念全部明确。'])
 g['TEXT_READING']=cond(o,o+'.GUARD.TEXT_READING',cr,[{'field':'permission','op':'EQ','value':True},{'field':'rights','op':'EQ','value':'PUBLIC_AUTHORIZED'},{'field':'accessible','op':'EQ','value':True},{'field':'modality','op':'EQ','value':'TEXT'},{'field':'required_construct','op':'EQ','value':'READING'}],['文本资源只用于阅读构念，权利和可及性仍需单独核验。'])
 g['TEXT']=cond(o,o+'.GUARD.TEXT',cr,[{'field':'modality','op':'EQ','value':'TEXT'},{'field':'required_construct','op':'EQ','value':'LISTENING'}],['仅用于反例判别。'])
 visual_fields=['evidence_id','evidence_version','resource_identity','resource_version','modality','required_construct','test_scope','test_result','source_status','evidence_sha256']
 visual_clauses=[{'field':'visual_accessibility_evidence.'+k,'op':'EQ','value':VISUAL_ACCESSIBILITY_EVIDENCE[k]} for k in visual_fields]
 g['VISUAL_ACCESSIBILITY']=cond(o,o+'.GUARD.VISUAL_ACCESSIBILITY',cr,visual_clauses,['视觉可及性对象须绑定资源身份/版本、视觉模态、目标构念、测试范围/结果及重算摘要；当前仅为项目合成候选对象，不是实际媒体/真实无障碍认证。'])
 g['VISUAL']=cond(o,o+'.GUARD.VISUAL',cr,[{'field':'permission','op':'EQ','value':True},{'field':'rights','op':'EQ','value':'PUBLIC_AUTHORIZED'},{'field':'accessible','op':'EQ','value':True},{'field':'modality','op':'EQ','value':'VISUAL'},{'field':'required_construct','op':'EQ','value':'VISUAL_RECOGNITION'}],['视觉构念、权限/权利与可及性对象必须分别通过。'])
 g['RIGHTS']=cond(o,o+'.GUARD.RIGHTS',cr,[{'field':'rights','op':'EQ','value':'HOLD'}],['来源权利未知。'])
 g['ACCESS']=cond(o,o+'.GUARD.ACCESS',cr,[{'field':'accessible','op':'EQ','value':False}],['通道不可用。'])
 target=composition(o,cr,[local('P03.PRODUCTION'),local('P04.FLOW'),*mods.values(),*resources.values()],[resources['AUDIO'],resources['TEXT'],resources['VISUAL']],[g['AUDIO'],g['TEXT_READING'],g['TEXT'],g['VISUAL'],g['VISUAL_ACCESSIBILITY'],g['RIGHTS'],g['ACCESS']],'文本不能替代听辨；私人权利不能升级公开；无障碍/授权未知时HOLD。')
 owner_claims[o]=cr
 # F04 interaction
 o='F04';cr=claims(o,design['modules'][o]['claims']);owner_claims[o]=cr
 pgoal=records['P03.PRODUCTION.GOAL']['construct_ref'];pactivity=local('P03.PRODUCTION');prole=local('P03.PRODUCTION.ROLE')
 observations={}
 for suffix,method,unit,ind in [
  ('INITIAL','原始首次响应','RESPONSE_EVENT','首次响应需保留时间/任务版本，提示前独立性另核'),
  ('HINT','提示及辅助事件','ASSISTANCE_EVENT','提示发生和提示后响应不得折叠'),
  ('FINAL','最终提交响应','RESPONSE_EVENT','最终响应不能覆盖首次响应'),
  ('RETEST','新变式无提示独立复测','INDEPENDENT_RETEST','独立复测需新任务变式及明确无提示')]:
  observations[suffix]=obs(o,o+'.OBS.'+suffix,cr,pgoal,method,unit,ind)
 interaction=add(o,'Interaction',o+'.INTERACTION',cr,['任务、评分、角色、帮助、时间和响应版本可追溯。'],'生成答案不属于学习者响应；提示后正确不自动等于独立掌握。',activity_ref=pactivity,role_refs=[prole],observation_refs=[*observations.values(),local('P06.ACT.OBSERVE.OBS')],input_contract='InitialResponseEvent, HintEvent, FinalResponseEvent and IndependentRetestEvent are distinct append-only events. Task/scoring versions must be nonempty and pinned; event_time and recorded_at are UTC epoch seconds with explicit client/server clock IDs, BOUNDED synchronization and maximum 300-second skew. recorded_at is nondecreasing in append order; event_time retains its own event chronology. Every event digest is recomputed. IndependentRetestEvent binds F04.OBS.RETEST and P06.ACT.OBSERVE.OBS; a bare independent_retest boolean is never evidence.',output_contract='Append-only observations; no overwrite; assisted and independent channels remain distinct.',assistance_policy='Record hint before/after and resubmission separately; no answer substitution; ambiguous or missing evidence UNKNOWN.')
 g={}
 g['INDEPENDENT']=cond(o,o+'.GUARD.INDEPENDENT',cr,[{'field':'role_authorized','op':'EQ','value':True},{'field':'generated_answer','op':'EQ','value':False},{'field':'expected_task_version','op':'NE','value':''},{'field':'task_version','op':'NE','value':''},{'field':'expected_scoring_version','op':'EQ','value':F05_SCORING_VERSION_PIN},{'field':'scoring_version','op':'EQ','value':F05_SCORING_VERSION_PIN},{'field':'retest_event.task_version','op':'NE','value':''},{'field':'retest_event.scoring_binding.scoring_version','op':'EQ','value':F05_SCORING_VERSION_PIN},{'field':'clock_contract.event_clock_domain','op':'EQ','value':F04_CLOCK_CONTRACT['event_clock_domain']},{'field':'clock_contract.recording_clock_domain','op':'EQ','value':F04_CLOCK_CONTRACT['recording_clock_domain']},{'field':'clock_contract.clock_sync_status','op':'EQ','value':'BOUNDED'},{'field':'clock_contract.max_clock_skew_seconds','op':'EQ','value':300},{'field':'retest_event.event_type','op':'EQ','value':'INDEPENDENT_RETEST'},{'field':'retest_event.observation_ref.stable_id','op':'EQ','value':'F04.OBS.RETEST'},{'field':'retest_event.assistance_status','op':'EQ','value':'NONE'},{'field':'retest_event.generated_answer','op':'EQ','value':False}],['复测版本非空且精确固定；事件时钟域/时钟身份/最大偏差明确，记录时间顺序与事件时间顺序分开验证。'])
 g['ASSISTED']=cond(o,o+'.GUARD.ASSISTED',cr,[{'field':'retest_event.assistance_status','op':'NE','value':'NONE'}],['复测受到提示/辅助，不得作为独立复测。'])
 g['GENERATED']=cond(o,o+'.GUARD.GENERATED',cr,[{'field':'generated_answer','op':'EQ','value':True}],['响应不是学习者生成；缺失/未知也不得晋升。'])
 target=composition(o,cr,[interaction,pactivity,local('P06.FLOW'),*observations.values()],[interaction,*observations.values()],[g['INDEPENDENT'],g['ASSISTED'],g['GENERATED']],'提示、生成答案、无效/缺失响应及版本错配均不能晋升为独立学习证据。')
 # F05 learner state
 o='F05';cr=claims(o,design['modules'][o]['claims']);owner_claims[o]=cr
 sk=add(o,'SkillType',o+'.SKILL.OBSERVATION_INTEGRITY',cr,['只描述被声明任务中的证据通道。'],'不等于一般能力或掌握。',label='OBSERVATION_INTEGRITY',performance_boundary='区分原始响应、自述、评分和模型估计；不合并成单一能力标签。')
 observations={}
 for suffix,method,unit,ind in [
  ('RESPONSE','原始响应事件','RESPONSE','记录任务版本、时点及是否提示'),
  ('SELF_REPORT','学习者自述','SELF_REPORT','记录本人身份、时点和拒答/缺失'),
  ('SCORE','版本化评分结果','SCORE','记录评分版本、分母、缺答/无效类别'),
  ('ESTIMATE','模型估计输出','MODEL_OUTPUT','记录模型ID、版本、适用条件和不确定性')]:
  observations[suffix]=obs(o,o+'.OBS.'+suffix,cr,sk,method,unit,ind)
 states={}
 for suffix,obsids,unc in [
  ('RESPONSE',[observations['RESPONSE']],'只描述已观测响应；不推断潜在掌握。'),
  ('SELF_REPORT',[observations['SELF_REPORT']],'自述为本人报告；缺失不视为否定。'),
  ('SCORE',[observations['SCORE']],'评分依赖评分规则/版本/分母；分数不是能力本体。'),
  ('ESTIMATE',[observations['ESTIMATE']],'无当前已核验估计器绑定；保持未估计，禁止自动推断掌握。')]:
  states[suffix]=add(o,'StateDimension',o+'.STATE.'+suffix,cr,['各通道保留原始身份、版本、时间及条件。'],'不得把不同来源、尺度或缺失值合并。',construct_ref=sk,estimator_ref=None,observation_refs=obsids,uncertainty=unc,effect='DEFINITION_ONLY')
 g['VERSION']=cond(o,o+'.GUARD.VERSION',cr,[{'field':'expected_scoring_version','op':'EQ','value':F05_SCORING_VERSION_PIN},{'field':'score.scoring_version','op':'EQ','value':F05_SCORING_VERSION_PIN}],['任务预期评分版本与实际评分版本必须相同；缺失/不匹配HOLD。'])
 target=composition(o,cr,[local('P08.FLOW'),local('P10.FLOW'),*observations.values()],[*states.values()],[g['VERSION']],'没有已核验模型时不估计；缺失UNKNOWN；不输出综合掌握标签。')
 # F07 environment/role/governance
 o='F07';cr=claims(o,design['modules'][o]['claims']);owner_claims[o]=cr
 envs={}
 for suffix,caps,constraints in [
  ('LOW_BANDWIDTH',['text access','offline checkpoint'],['audio stream may be unavailable','connectivity unknown is HOLD']),
  ('SHARED_DEVICE',['keyboard','screen reader when tested'],['session ownership must be verified','no persistence without permission']),
  ('PRIVATE_DEVICE',['local rendering'],['device capability must be tested','local access is not role authorization'])]:
  envs[suffix]=add(o,'Environment',o+'.ENV.'+suffix,cr,['只记录实际测试能力和限制。'],'环境标签不证明个体身份、无障碍合规或授权。',capabilities=caps,constraints=constraints)
 roles={}
 for suffix,label,caps,perms in [
  ('LEARNER','LEARNER',['choose goal','submit own response','decline support'],['session-bound self selection','purpose-bound optional support','exit']),
  ('FACILITATOR','FACILITATOR',['explain task','offer optional support'],['explicit learner request','assigned learner and scope','session and expiry bound authority']),
  ('REVIEWER','REVIEWER',['inspect candidate evidence'],['read-only review scope; no learner-support suggestion authority'])]:
  roles[suffix]=add(o,'Role',o+'.ROLE.'+suffix,cr,['角色身份和当前授权需逐次验证。'],'角色标签不自动授予数据访问或执行权限。',label=label,capability_requirements=caps,permission_requirements=perms)
 guards={}
 guards['EXIT']=cond(o,o+'.GUARD.EXIT',cr,[{'field':'exit','op':'EQ','value':True}],['本人退出。'])
 guards['EXIT_UNKNOWN']=cond(o,o+'.GUARD.EXIT_UNKNOWN',cr,[{'field':'exit','op':'NE','value':False}],['退出状态不是明确false时澄清；STOP优先。'])
 guards['DENY']=cond(o,o+'.GUARD.DENY',cr,[{'field':'role_authority.permission','op':'EQ','value':False}],['角色授权证据中的实际权限明确为否。'])
 guards['REVIEWER']=cond(o,o+'.GUARD.REVIEWER',cr,[{'field':'role','op':'EQ','value':'REVIEWER'}],['审核者只读，不能提出学习者支持建议。'])
 guards['UNAVAILABLE']=cond(o,o+'.GUARD.UNAVAILABLE',cr,[{'field':'environment_profile.accessible','op':'EQ','value':False},{'field':'environment_profile.capability_match','op':'EQ','value':False}],['当前环境不可及或任务能力不匹配。'])
 records[o+'.GUARD.UNAVAILABLE']['combination']='ANY'
 offer_common=[{'field':'identity_verified','op':'EQ','value':True},{'field':'actor_id','op':'NE','value':''},{'field':'learner_id','op':'NE','value':''},{'field':'session_id','op':'NE','value':''},{'field':'exit','op':'EQ','value':False},{'field':'now','op':'GT','value':0},{'field':'task_id','op':'NE','value':''},{'field':'task_version','op':'NE','value':''},{'field':'role_authority.authority_id','op':'NE','value':''},{'field':'role_authority.authority_version','op':'EQ','value':'V1'},{'field':'role_authority.actor_id','op':'NE','value':''},{'field':'role_authority.learner_id','op':'NE','value':''},{'field':'role_authority.role','op':'EQ','value':'LEARNER'},{'field':'role_authority.purpose','op':'EQ','value':'OFFER_LEARNER_SUPPORT'},{'field':'role_authority.scope','op':'EQ','value':'LEARNER_SUPPORT_ADVICE_ONLY'},{'field':'role_authority.session_id','op':'NE','value':''},{'field':'role_authority.permission','op':'EQ','value':True},{'field':'role_authority.issued_at','op':'GT','value':0},{'field':'role_authority.not_before','op':'GT','value':0},{'field':'role_authority.expires_at','op':'GT','value':0},{'field':'role_authority.resolver_status','op':'EQ','value':'VERIFIED'},{'field':'role_authority.resolver_id','op':'NE','value':''},{'field':'support_request.event_id','op':'NE','value':''},{'field':'support_request.learner_id','op':'NE','value':''},{'field':'support_request.session_id','op':'NE','value':''},{'field':'support_request.selected_option_id','op':'NE','value':''},{'field':'support_request.selected_by','op':'EQ','value':'LEARNER'},{'field':'support_request.task_id','op':'NE','value':''},{'field':'support_request.task_version','op':'NE','value':''},{'field':'support_request.event_time','op':'GT','value':0},{'field':'support_request.recorded_at','op':'GT','value':0},{'field':'support_request.event_sha256','op':'NE','value':''},{'field':'environment_profile.profile_id','op':'NE','value':''},{'field':'environment_profile.profile_version','op':'EQ','value':'V1'},{'field':'environment_profile.task_id','op':'NE','value':''},{'field':'environment_profile.task_version','op':'NE','value':''},{'field':'environment_profile.tested_at','op':'GT','value':0},{'field':'environment_profile.valid_until','op':'GT','value':0},{'field':'environment_profile.profile_sha256','op':'NE','value':''},{'field':'environment_profile.accessible','op':'EQ','value':True},{'field':'environment_profile.capability_match','op':'EQ','value':True}]
 guards['OFFER_LEARNER']=cond(o,o+'.GUARD.OFFER_LEARNER',cr,offer_common+[{'field':'role','op':'EQ','value':'LEARNER'}],['学习者本人会话身份、本人选择、目的、范围、期限、会话和环境证据匹配。'])
 guards['LEARNER_AUTH_UNBOUND']=cond(o,o+'.GUARD.LEARNER_AUTH_UNBOUND',cr,[{'field':'role','op':'EQ','value':'LEARNER'},{'field':'role_authority.resolver_status','op':'EQ','value':'UNBOUND'}],['当前可信学习者身份/会话授权解析器未绑定；学习者路径保持HOLD，不产生SUGGEST。'])
 guards['FACILITATOR_UNBOUND']=cond(o,o+'.GUARD.FACILITATOR_UNBOUND',cr,[{'field':'role','op':'EQ','value':'FACILITATOR'}],['当前可信促进者授权解析器未绑定；即使有结构化范围/期限对象，促进者路径也必须HOLD。'])
 rules=[{'condition_ref':guards['EXIT'],'action':'STOP','reason':'本人退出，停止后续非授权动作','priority':0},{'condition_ref':guards['REVIEWER'],'action':'REFUSE','reason':'审核者只读，不提供学习者支持建议','priority':1},{'condition_ref':guards['DENY'],'action':'REFUSE','reason':'角色授权证据中的权限明确为否','priority':2},{'condition_ref':guards['EXIT_UNKNOWN'],'action':'CLARIFY','reason':'退出状态未知，不提供支持建议','priority':3},{'condition_ref':guards['UNAVAILABLE'],'action':'DEFER','reason':'当前环境不可及或任务能力不匹配','priority':4},{'condition_ref':guards['LEARNER_AUTH_UNBOUND'],'action':'REQUEST_OBSERVATION','reason':'可信学习者身份/会话授权解析器未绑定；不产生支持建议','priority':5},{'condition_ref':guards['FACILITATOR_UNBOUND'],'action':'REQUEST_OBSERVATION','reason':'可信促进者授权解析器未绑定；不产生支持建议','priority':6}]
 policy=add(o,'PolicySpec',o+'.POLICY',cr,['权限必须由角色/目的/范围/期限/会话绑定的证据对象表达；支持请求和环境配置均需精确事件摘要。'],'审核者只读；促进者必须有明确分配范围/期限/会话并由可信解析器核验；当前解析器未绑定，促进者路径HOLD；未知退出/权限/身份澄清；不自动执行。',policy_type='GOVERNANCE',rules=rules,unknown_action='CLARIFY',effect='ADVICE_ONLY')
 target=composition(o,cr,[local('P10.FLOW'),*envs.values(),*roles.values()],[policy],[*guards.values()],'未授权拒绝、未知澄清、退出停止；不从行为推断健康/身份或固定偏好。')
 # A07 environment/development/difference-to-support integration
 o='A07';claims(o,design['modules'][o]['claims'])
 needed={'K10.01.04.TR.01','K09.01.01.ME.01','K16.01.04.TG.01','K09.02.05.ME.01','K13.04.02.SR.01','K16.04.03.TG.01','K19.03.02.TG.01','K19.02.03.TG.01'}
 cr=[]
 for upstream in ('F05.COMPOSITION','F07.COMPOSITION'):
  for z in records[upstream]['claim_refs']:
   if z['stable_id'] in needed and z not in cr:cr.append(z)
 assert {z['stable_id'] for z in cr}==needed,({z['stable_id'] for z in cr},needed)
 upstream_task_deps=set(tasks['F05']['depends_on'])|set(tasks['F07']['depends_on'])
 assert all(z['owner'] in upstream_task_deps for z in cr),[(z['owner'],z['stable_id']) for z in cr if z['owner'] not in upstream_task_deps]
 assert set(tasks['A07']['depends_on'])=={'F05','F07','IF01'}
 owner_claims[o]=cr
 a07_claims=list(cr)
 g={}
 g['EXIT']=cond(o,o+'.GUARD.EXIT',cr,[{'field':'exit','op':'EQ','value':True}],['本人退出优先于其他支持判断。'])
 g['EXIT_UNKNOWN']=cond(o,o+'.GUARD.EXIT_UNKNOWN',cr,[{'field':'exit','op':'NE','value':False}],['只有exit精确为false才可继续；缺失/null/未知必须澄清。'])
 g['IDENTITY']=cond(o,o+'.GUARD.IDENTITY',cr,[{'field':'identity_verified','op':'EQ','value':False}],['身份未知或未核验时澄清；未知属性由unknown_action处理。'])
 g['REVIEWER']=cond(o,o+'.GUARD.REVIEWER',cr,[{'field':'actor_role','op':'EQ','value':'REVIEWER'}],['审核者只读，不作学习者支持决策。'])
 g['PERMISSION']=cond(o,o+'.GUARD.PERMISSION',cr,[{'field':'permission','op':'EQ','value':False}],['权限明确为否时拒绝。'])
 g['LEARNER_SELECTION']=cond(o,o+'.GUARD.LEARNER_SELECTION',cr,[{'field':'actor_role','op':'NE','value':'LEARNER'},{'field':'support_requested_by','op':'NE','value':'LEARNER'},{'field':'learner_selected','op':'EQ','value':False}],['促进者不能代替学习者选择；缺少本人选择时澄清。'])
 records[o+'.GUARD.LEARNER_SELECTION']['combination']='ANY'
 g['ACCESS_UNAVAILABLE']=cond(o,o+'.GUARD.ACCESS_UNAVAILABLE',cr,[{'field':'accessible','op':'EQ','value':False},{'field':'capability_match','op':'EQ','value':False}],['当前环境不可及或能力不匹配时延后。'])
 records[o+'.GUARD.ACCESS_UNAVAILABLE']['combination']='ANY'
 g['REQUEST_UNVERIFIED']=cond(o,o+'.GUARD.REQUEST_UNVERIFIED',cr,[{'field':'f07_input.support_request.event_sha256','op':'EQ','value':''}],['学习者请求必须来自F07结构化、可重算摘要的事件对象；caller boolean不构成证据。'])
 g['ENVIRONMENT_UNVERIFIED']=cond(o,o+'.GUARD.ENVIRONMENT_UNVERIFIED',cr,[{'field':'f07_input.environment_profile.profile_sha256','op':'EQ','value':''}],['环境配置必须由任务/版本/测试时间/有效期和对象摘要绑定。'])
 g['ESTIMATE_UNBOUND']=cond(o,o+'.GUARD.ESTIMATE_UNBOUND',cr,[{'field':'estimate_status','op':'NE','value':'NOT_ESTIMATED'}],['当前没有已核验估计器；任何模型输出不作为支持依据。'])
 g['CONSTRUCT_UNVERIFIED']=cond(o,o+'.GUARD.CONSTRUCT_UNVERIFIED',cr,[{'field':'construct_review.review_result','op':'NE','value':'PASS'}],['任务级构念审查对象缺失、身份不匹配或摘要不正确时请求观察/审查。'])
 g['CONSTRUCT_UNKNOWN']=cond(o,o+'.GUARD.CONSTRUCT_UNKNOWN',cr,[{'field':'construct_review.relation','op':'EQ','value':'UNKNOWN'}],['构念关系未知时请求任务级观察/审查。'])
 common=[{'field':'actor_role','op':'EQ','value':'LEARNER'},{'field':'exit','op':'EQ','value':False},{'field':'f07_input.role','op':'EQ','value':'LEARNER'},{'field':'f07_input.role_authority.resolver_status','op':'EQ','value':'VERIFIED'},{'field':'f07_input.support_request.selected_by','op':'EQ','value':'LEARNER'},{'field':'f07_input.support_request.event_sha256','op':'NE','value':''},{'field':'f07_input.environment_profile.profile_sha256','op':'NE','value':''},{'field':'f07_input.environment_profile.task_id','op':'NE','value':''},{'field':'f07_input.environment_profile.task_version','op':'NE','value':''},{'field':'estimate_status','op':'EQ','value':'NOT_ESTIMATED'},{'field':'construct_review.review_result','op':'EQ','value':'PASS'},{'field':'construct_review.review_sha256','op':'NE','value':''}]
 g['PRESERVED']=cond(o,o+'.GUARD.PRESERVED',cr,common+[{'field':'construct_review.relation','op':'EQ','value':'PRESERVED'}],['全部授权/环境/本人选择前提成立，且任务级审查确认构念保持。'])
 g['CHANGED_ASSESSMENT']=cond(o,o+'.GUARD.CHANGED_ASSESSMENT',cr,common+[{'field':'construct_review.relation','op':'EQ','value':'CHANGED'},{'field':'assessment','op':'EQ','value':True}],['评估构念已改变，原评估延后，另列练习，不替代或并分。'])
 g['CHANGED_PRACTICE']=cond(o,o+'.GUARD.CHANGED_PRACTICE',cr,common+[{'field':'construct_review.relation','op':'EQ','value':'CHANGED'},{'field':'assessment','op':'EQ','value':False}],['仅在非评估练习中提供独立替代选项。'])
 rules=[
  {'condition_ref':g['EXIT'],'action':'STOP','reason':'本人退出，停止后续支持流程','priority':0},
  {'condition_ref':g['EXIT_UNKNOWN'],'action':'CLARIFY','reason':'退出状态缺失/未知时不得继续','priority':1},
  {'condition_ref':g['REVIEWER'],'action':'REFUSE','reason':'审核角色只读，不决定学习者支持','priority':2},
  {'condition_ref':local('F07.GUARD.DENY'),'action':'REFUSE','reason':'F07角色授权明确拒绝','priority':3},
  {'condition_ref':local('F07.GUARD.EXIT_UNKNOWN'),'action':'CLARIFY','reason':'F07退出状态不明确','priority':4},
  {'condition_ref':local('F07.GUARD.UNAVAILABLE'),'action':'DEFER','reason':'F07环境或能力不满足','priority':5},
  {'condition_ref':local('F07.GUARD.REVIEWER'),'action':'REFUSE','reason':'F07审核者只读','priority':6},
  {'condition_ref':local('F07.GUARD.LEARNER_AUTH_UNBOUND'),'action':'REQUEST_OBSERVATION','reason':'F07可信学习者身份/会话授权解析器未绑定；A07不得建议','priority':7},
  {'condition_ref':local('F07.GUARD.FACILITATOR_UNBOUND'),'action':'REQUEST_OBSERVATION','reason':'F07可信促进者授权解析器未绑定；A07不得建议','priority':8},
  {'condition_ref':g['CONSTRUCT_UNVERIFIED'],'action':'REQUEST_OBSERVATION','reason':'任务级构念审查对象不完整或未核验','priority':9},
  {'condition_ref':g['CONSTRUCT_UNKNOWN'],'action':'REQUEST_OBSERVATION','reason':'构念关系未知，需先完成任务级审查','priority':10}
 ]
 policy=add(o,'PolicySpec',o+'.POLICY',cr,['必须同时绑定F05证据通道与F07环境/角色合同；当前支持策略只作建议。'],'不以年龄、发展标签、诊断、群体或固定学习风格推断个体；缺失自述不是无需求；缺失响应/分数不是能力不足；不使用未绑定估计器；改变构念不等价评分；不自动执行或写入状态。',policy_type='GOVERNANCE',rules=rules,unknown_action='CLARIFY',effect='ADVICE_ONLY')
 inputs=[local('F05.COMPOSITION'),local('F05.STATE.RESPONSE'),local('F05.STATE.SELF_REPORT'),local('F05.STATE.SCORE'),local('F05.STATE.ESTIMATE'),local('F07.COMPOSITION'),local('F07.POLICY'),local('F07.ENV.LOW_BANDWIDTH'),local('F07.ENV.SHARED_DEVICE'),local('F07.ENV.PRIVATE_DEVICE'),local('F07.ROLE.LEARNER'),local('F07.ROLE.FACILITATOR'),local('F07.ROLE.REVIEWER')]
 a07_f07_guards=[local('F07.GUARD.EXIT'),local('F07.GUARD.EXIT_UNKNOWN'),local('F07.GUARD.REVIEWER'),local('F07.GUARD.DENY'),local('F07.GUARD.UNAVAILABLE'),local('F07.GUARD.LEARNER_AUTH_UNBOUND'),local('F07.GUARD.FACILITATOR_UNBOUND'),local('F07.GUARD.OFFER_LEARNER')]
 inputs.extend(a07_f07_guards)
 target=composition(o,cr,inputs,[policy],[*g.values(),*a07_f07_guards],'A07必须消费F07完整结构化身份/会话/请求/环境证据和决策边界；当前可信身份解析器未绑定，A07不得产生SUGGEST；明确退出STOP、拒绝REFUSE、不可及DEFER。')
 # E01 evaluation and change governance
 o='E01';cr=claims(o,design['modules'][o]['claims']);owner_claims[o]=cr
 sk=add(o,'SkillType',o+'.SKILL.PROTOCOL_INTEGRITY',cr,['评价协议完整性和版本化证据流程。'],'协议完整不代表干预有效。',label='PROTOCOL_INTEGRITY',performance_boundary='核协议、估计量、比较、结果、随访、审批和复核，不推断实证效果。')
 goal=add(o,'Goal',o+'.GOAL',cr,['目标为协议和证据完整性，而非提高分数。'],'不等于学习者能力目标。',construct_ref=sk,success_evidence_refs=[],scope='受限评价协议完整性')
 obs1=obs(o,o+'.OBS.PRIMARY_OUTCOME',cr,sk,'预先声明的主要结果观测','VERSIONED_OUTCOME','绑定人群、任务版本、评分版本、分母和固定时间点')
 obs2=obs(o,o+'.OBS.SAFETY',cr,sk,'退出/拒绝/不利事件观测','SAFETY_EVENT','保留事件身份、时点、处置和缺失状态')
 records[o+'.GOAL']['success_evidence_refs']=[obs1,obs2]
 g={}
 g['DIRECT_WRITE']=cond(o,o+'.GUARD.DIRECT_WRITE',cr,[{'field':'direct_knowledge_write','op':'EQ','value':True}],['直接写正式知识请求。'])
 approval_fields=[('kind','RESEARCH_PROTOCOL_APPROVAL'),('decision','APPROVED'),('subject_id','E01.PROTOCOL'),('subject_version','V2'),('analysis_plan_sha256',sha(DOC/'analysis-plan.json')),('repository','kaicreator-mm/learn-kg')]
 approval_clauses=[{'field':'approval_evidence_ref.'+k,'op':'EQ','value':v} for k,v in approval_fields]+[{'field':'approval_evidence_ref.issue_number','op':'GT','value':0},{'field':'approval_evidence_ref.comment_id','op':'GT','value':0},{'field':'approval_evidence_ref.artifact_path','op':'NE','value':''},{'field':'approval_evidence_ref.artifact_sha256','op':'NE','value':''},{'field':'approval_evidence_ref.authority_id','op':'NE','value':''},{'field':'approval_evidence_ref.issued_at','op':'GT','value':0},{'field':'approval_evidence_ref.expires_at','op':'GT','value':0}]
 g['APPROVED']=cond(o,o+'.GUARD.APPROVED',cr,approval_clauses,['审批证据必须绑定类型、决定、仓库、Issue/comment、artifact路径/摘要、authority和有效时间；caller boolean不构成审批。'])
 review_fields=[('kind','INDEPENDENT_NON_WRITER_REVIEW'),('decision','ACCEPT_SCOPED'),('subject_id','E01.PROTOCOL'),('subject_version','V2'),('analysis_plan_sha256',sha(DOC/'analysis-plan.json')),('repository','kaicreator-mm/learn-kg')]
 review_clauses=[{'field':'independent_review_evidence_ref.'+k,'op':'EQ','value':v} for k,v in review_fields]+[{'field':'independent_review_evidence_ref.issue_number','op':'GT','value':0},{'field':'independent_review_evidence_ref.comment_id','op':'GT','value':0},{'field':'independent_review_evidence_ref.artifact_path','op':'NE','value':''},{'field':'independent_review_evidence_ref.artifact_sha256','op':'NE','value':''},{'field':'independent_review_evidence_ref.authority_id','op':'NE','value':''},{'field':'independent_review_evidence_ref.issued_at','op':'GT','value':0},{'field':'independent_review_evidence_ref.expires_at','op':'GT','value':0}]
 g['REVIEWED']=cond(o,o+'.GUARD.REVIEWED',cr,review_clauses,['独立审核证据必须绑定不同的非作者身份、仓库、Issue/comment、artifact路径/摘要、authority和有效时间。'])
 evidence_pair_clauses=approval_clauses+review_clauses+[{'field':'direct_knowledge_write','op':'EQ','value':False}]
 g['CURRENT_VERSION']=cond(o,o+'.GUARD.CURRENT_VERSION',cr,evidence_pair_clauses+[{'field':'current_policy_version','op':'EQ','value':'CURRENT_V1'}],['对照策略仅在完整、相互独立且有效的审批/复核证据以及禁止直接写知识条件下识别。'])
 g['CANDIDATE_VERSION']=cond(o,o+'.GUARD.CANDIDATE_VERSION',cr,evidence_pair_clauses+[{'field':'candidate_policy_version','op':'EQ','value':'CANDIDATE_V1'}],['候选策略只有完整、相互独立且有效的审批/复核证据以及禁止直接写知识条件时才能进入待核验状态；无可信resolver仍不得建议。'])
 g['RESOLVER_UNBOUND']=cond(o,o+'.GUARD.RESOLVER_UNBOUND',cr,[{'field':'trusted_evidence_resolver.status','op':'EQ','value':'UNBOUND'}],['可信审批/独立审核解析器未绑定；候选建议路径保持REQUEST_OBSERVATION。'])
 current=add(o,'PolicySpec',o+'.POLICY.CURRENT',cr,['只定义当前对照建议策略。'],'不得把当前策略当作已验证有效；直接知识写入必须拒绝。',policy_type='GOVERNANCE',rules=[{'condition_ref':g['DIRECT_WRITE'],'action':'REFUSE','reason':'禁止直接写入正式知识','priority':0},{'condition_ref':g['CURRENT_VERSION'],'action':'DEFER','reason':'继续当前流程，不增加候选支持建议','priority':1}],unknown_action='CLARIFY',effect='ADVICE_ONLY')
 candidate=add(o,'PolicySpec',o+'.POLICY.CANDIDATE',cr,['只定义待评价候选建议策略。'],'当前无可信审批/复核resolver；候选策略只能请求补充可信证据，不允许直接SUGGEST。',policy_type='GOVERNANCE',rules=[{'condition_ref':g['DIRECT_WRITE'],'action':'REFUSE','reason':'禁止直接写入正式知识','priority':0},{'condition_ref':g['CANDIDATE_VERSION'],'action':'REQUEST_OBSERVATION','reason':'候选版本证据结构完整仍需可信resolver；当前不产生建议','priority':1},{'condition_ref':g['RESOLVER_UNBOUND'],'action':'REQUEST_OBSERVATION','reason':'可信审批/独立复核resolver未绑定','priority':2}],unknown_action='CLARIFY',effect='ADVICE_ONLY')
 plan=load(DOC/'analysis-plan.json');plan_hash=sha(DOC/'analysis-plan.json')
 protocol=add(o,'EvaluationProtocol',o+'.PROTOCOL',cr,['协议字段采用DB01 canonical v1现有字符串槽位中的规范JSON；分析计划作为单独只读文件按SHA256固定。','当前没有可信审批/独立审核解析器，因此不得进行观察数据效果分析。'],'模拟不是效果；观察性差异不自动因果；个体记录不直接写正式知识；审批布尔值和自述审批不构成授权。',comparator_ref=current,intervention_ref=candidate,goal_ref=goal,measurement_refs=[obs1,obs2],population_scope=json.dumps(plan['population'],ensure_ascii=False,sort_keys=True,separators=(',',':')),estimand=json.dumps({'allocation':plan['allocation'],'intervention':plan['intervention'],'comparator':plan['comparator'],'primary_outcome':plan['primary_outcome'],'analysis_plan_ref':ANALYSIS_PLAN_REF,'analysis_plan_sha256':plan_hash,'analysis_plan_summary':plan['analysis_plan_summary'],'estimand':plan['estimand']},ensure_ascii=False,sort_keys=True,separators=(',',':')),followup=json.dumps(plan['followup'],ensure_ascii=False,sort_keys=True,separators=(',',':')),uncertainty=json.dumps({'authority_status':plan['authority_status'],'data_status':plan['data_status'],'release_status':plan['release_status'],'required_evidence':plan['required_evidence'],'limits':'没有真实合规研究数据；模拟、离线测试和即时分数不构成长期效果。'},ensure_ascii=False,sort_keys=True,separators=(',',':')),approval_required=True,effect='NO_DIRECT_KNOWLEDGE_WRITE')
 records[o+'.PROTOCOL']['provenance'].append({'source_path':ANALYSIS_PLAN_REF,'source_sha256':plan_hash,'json_pointer':'/artifact_id','source_status':'PROJECT_AUTHORED_FROZEN_CANDIDATE_PLAN'})
 target=composition(o,cr,[protocol,local('P10.FLOW'),current,candidate,goal,obs1,obs2],[candidate],[g['APPROVED'],g['REVIEWED'],g['CURRENT_VERSION'],g['CANDIDATE_VERSION'],g['DIRECT_WRITE'],g['RESOLVER_UNBOUND']],'仅生成候选协议完整性结果；当前可信审批/独立审核解析器未绑定，观察数据始终HOLD；禁止效果结论、直接修改正式知识或发布。')
 # Add cases and attach exact evidence refs to each composition.
 all_fixtures=fixtures()
 for owner,mod in design['modules'].items():
  expected_names=mod.get('cases',[])
  actual_names=[name for candidate_owner,name,_,_ in all_fixtures if candidate_owner==owner]
  assert len(expected_names)==len(set(expected_names)) and len(actual_names)==len(set(actual_names)) and set(expected_names)==set(actual_names),(owner,expected_names,actual_names)
 all_results=[]
 for owner,name,x,y in all_fixtures:
  assert owner in owner_claims
  comp=local(owner+'.COMPOSITION')
  neg = (y.get('action') in ('REFUSE','STOP','DEFER','CLARIFY','REQUEST_OBSERVATION') if isinstance(y,dict) else y in ('HOLD','REFUSE','STOP','DEFER','CLARIFY','REJECT_CONSTRUCT_SUBSTITUTION','NOT_LEARNER_EVIDENCE','ASSISTED_NOT_INDEPENDENT','DESCRIPTIVE_ONLY_NO_CAUSAL_ESTIMATE','SIMULATION_ONLY_NOT_EFFECT'))
  c,v=case(owner,name,comp,x,y,'COUNTEREXAMPLE' if neg else 'FORWARD')
  records[owner+'.COMPOSITION']['evidence_refs'].extend([c,v])
  actual=FUN[owner](x)
  assert actual==y,(owner,name,actual,y)
  all_results.append({'owner':owner,'case_id':owner+'.'+name,'input':x,'expected':y,'actual':actual,'status':'BUILDER_ONLY'})
 # Validate full canonical records and prepare one cumulative manifest.
 schema=load(ROOT/'docs/implementation/db01/canonical.schema.json');validator=Draft202012Validator(schema)
 for id,r in records.items():
  validator.validate(r)
 PKG.mkdir(exist_ok=True)
 files=[]
 for owner in OWNERS:
  rows=[r for r in records.values() if r['owner']==owner]
  if not rows:continue
  fp=PKG/(owner+'.jsonl')
  fp.write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for r in rows),encoding='utf-8')
  files.append({'path':fp.name,'sha256':sha(fp),'format':'JSONL_RECORDS','record_count':len(rows)})
 manifest={'schema_version':'learn-kg-canonical-candidate-1','package_id':'learning-process','version':VERSION,'status':'CANDIDATE','rights':'HOLD','owners':OWNERS,'dependencies':sorted(deps.values(),key=lambda x:(x['package_id'],x['version'])),'files':files,'qualification_receipt_refs':[]}
 mf=PKG/'learning-process.manifest.json';write(mf,manifest)
 catalog['learning-process',VERSION]=ManifestPin(mf.relative_to(ROOT).as_posix(),sha(mf))
 # Sidecar exact tuple bindings and migration proof.
 migration=[]
 for id,r in old_records.items():
  nr=records[id]
  migration.append({'owner':r['owner'],'stable_id':id,'old_record_sha256':dig(r),'new_record_sha256':dig(nr),'change':'INTERNAL_PROCESS_VERSION_REF_ONLY' if r!=nr else 'UNCHANGED'})
 write(DOC/'migration.json',{'source_version':old_manifest['version'],'target_version':VERSION,'migrated_record_count':len(migration),'records':migration,'old_shards_unchanged':True,'historical_receipts_preserved':True,'qualification_invalidation':'All prior P01-P10 candidate/qualification receipts require explicit exact tuple rebind because package manifest/version refs changed.'})
 write(DOC/'bindings.json',bindings)
 write(DOC/'fixtures.json',[{'owner':o,'name':n,'input':x,'expected':y} for o,n,x,y in all_fixtures])
 write(DOC/'results.json',{'status':'BUILDER_ONLY','case_count':len(all_results),'counts':{o:sum(x['owner']==o for x in all_results) for o in ['F03','F04','F05','F07','A07','E01']},'results':all_results,'manifest_sha256':sha(mf),'limitations':'No independent oracle, CQ/LC, empirical effects, source/rights qualification, generic runtime or authorization.'})
 # In-memory import with exact dependencies; no persistent SQLite file.
 ext=ROOT/'knowledge/v0.1.0/foundation-r3/relation-types.json'
 im=Importer(mode='research',catalog=catalog,extension=ManifestPin(ext.relative_to(ROOT).as_posix(),sha(ext)))
 try:
  receipt=im.run(('learning-process',VERSION))
  # Roundtrip all old P record fields and references.
  for id,r in old_records.items():
   z=load_record(im,local(id));n=records[id]
   diffs={k:(z[k],val) for k,val in n.items() if k in z and z[k]!=val and not(type(val) is bool and z[k]==str(val).lower())}
   assert not diffs,(id,diffs)
  # SQL-read every new F record and replay the finite cases.
  replay=[]
  for row in all_results:
   c=load_record(im,local(row['case_id']))
   inp=json.loads(c['input_spec']);expected=json.loads(c['expected_spec']) if c['expected_spec'].startswith(('{','[')) else c['expected_spec']
   comp=load_record(im,local(row['owner']+'.COMPOSITION'))
   assert comp['effect']=='CANDIDATE_DECISION_ONLY' and comp['evidence_refs']
   actual=FUN[row['owner']](inp);assert actual==expected,(row['case_id'],actual,expected)
   for cr in comp['claim_refs']:
    q=load_record(im,cr);assert isinstance(q.get('statement'),str) and q['statement']
   replay.append({'owner':row['owner'],'case_id':row['case_id'],'sql_target':row['owner']+'.COMPOSITION','actual':actual,'status':'SQL_BUILDER_ONLY'})
  binding_results=[]
  expected_bindings={'F03':['P03.PRODUCTION','P04.FLOW'],'F04':['P03.PRODUCTION','P06.FLOW'],'F05':['P08.FLOW','P10.FLOW'],'F07':['P10.FLOW'],'A07':['F05.COMPOSITION','F05.STATE.RESPONSE','F05.STATE.SELF_REPORT','F05.STATE.SCORE','F05.STATE.ESTIMATE','F07.COMPOSITION','F07.POLICY','F07.GUARD.EXIT','F07.GUARD.EXIT_UNKNOWN','F07.GUARD.REVIEWER','F07.GUARD.DENY','F07.GUARD.UNAVAILABLE','F07.GUARD.LEARNER_AUTH_UNBOUND','F07.GUARD.FACILITATOR_UNBOUND','F07.GUARD.OFFER_LEARNER'],'E01':['P10.FLOW']}
  for owner,expected_ids in expected_bindings.items():
   comp=load_record(im,local(owner+'.COMPOSITION'));actual_ids=[x['stable_id'] for x in comp['input_refs']]
   assert all(x in actual_ids for x in expected_ids),(owner,actual_ids,expected_ids)
   for id in expected_ids:load_record(im,local(id))
   binding_results.append({'owner':owner,'expected_process_refs':expected_ids,'actual_process_refs':actual_ids,'status':'STATIC_TYPED_BINDING_ONLY_NOT_EXECUTION'})
  f04_interaction=load_record(im,local('F04.INTERACTION'))
  nested_refs=f04_interaction['observation_refs']
  assert any(x['stable_id']=='F04.OBS.RETEST' and x['owner']=='F04' and x['kind']=='ObservationSpec' for x in nested_refs)
  assert any(x['stable_id']=='P06.ACT.OBSERVE.OBS' and x['owner']=='P06' and x['kind']=='ObservationSpec' for x in nested_refs)
  nested_typed_bindings=[{'owner':'F04','interaction_ref':local('F04.INTERACTION'),'retest_observation_ref':local('F04.OBS.RETEST'),'scoring_observation_ref':local('P06.ACT.OBSERVE.OBS'),'status':'STATIC_TYPED_EVENT_AND_SCORING_BINDING_ONLY'}]
  if01_contract=ROOT/'docs/implementation/if01/interface-contract.json'
  if01_receipt=ROOT/'evidence/tasks/IF01/IF01-FORMAL-01.json'
  if01_view=next(v for v in load(if01_contract)['view_routes'] if v['owner']=='A07')
  assert set(if01_view['task_dependencies'])=={'F05','F07','IF01'}
  assert set(if01_view['required_scope_ids'])=={'A07.RQ01','A07.RQ02','A07.RQ03','A07.RQ04'}
  a07_input_records=[]
  for id in expected_bindings['A07']:
   z=records[id];a07_input_records.append({'stable_id':id,'kind':z['kind'],'owner':z['owner'],'record_sha256':dig(z)})
  inherited_claims=[]
  for z in a07_claims:
   origin='F05' if z in records['F05.COMPOSITION']['claim_refs'] else 'F07'
   inherited_claims.append({'ref':z,'inherited_from':origin})
  write(DOC/'composition-input-bindings.json',{'owner':'A07','status':'EXACT_PREPARATION_BINDING_ONLY','package_id':'learning-process','version':VERSION,'manifest_sha256':sha(mf),'task_dependencies':tasks['A07']['depends_on'],'inputs':a07_input_records,'inherited_claim_refs':inherited_claims,'if01':{'interface_version':if01_view.get('interface_version',load(if01_contract).get('interface_version')),'contract_path':'docs/implementation/if01/interface-contract.json','contract_sha256':sha(if01_contract),'receipt_path':'evidence/tasks/IF01/IF01-FORMAL-01.json','receipt_sha256':sha(if01_receipt),'content_digest':load(if01_receipt)['content_digest'],'required_scope_ids':if01_view['required_scope_ids'],'task_dependencies':if01_view['task_dependencies']},'limits':'IF01 is a file/receipt contract pin, not a synthetic canonical record; no formal A07 receipt or CQ/LC qualification.'})
  write(DOC/'import-receipt.json',receipt)
  write(DOC/'sql-results.json',{'status':'MEMORY_SQLITE_BUILDER_ONLY','cases':len(replay),'results':replay,'cross_module_bindings':binding_results,'nested_typed_bindings':nested_typed_bindings,'manifest_sha256':sha(mf),'migration_count':len(migration),'record_count':len(records),'limits':'No persistent SQLite; no independent oracle or task qualification.'})
  print('PROCESS_MIGRATED',len(migration),'F_RECORDS',len(records)-len(migration),'TOTAL',len(records),'F_CASES',len(replay),'MANIFEST',sha(mf))
 finally:im.close()
if __name__=='__main__':main()
