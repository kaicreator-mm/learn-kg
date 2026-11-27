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
from semantic_checks import FUN,fixtures,dig

B=ROOT/'knowledge/v0.1.0'
OLD=B/'learning-process-cumulative-r2'
PKG=B/'learning-process-cumulative-r3'
VERSION='0.1.0-process-candidate-3'
OWNERS=['P01','P02','P03','P04','P05','P06','P07','P08','P09','P10','F03','F04','F05','F07','A07','E01']
ACCEPTED_TYPES={'PROJECT_RULE','ENGINEERING_POLICY','ORIGINAL_METHOD_DERIVATION','METHOD','MATHEMATICAL_DERIVATION'}
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
 design=load(DOC/'design.json');tasks={x['id']:x for x in load(ROOT/'docs/implementation/task-dag.json')['tasks']}
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
  z={'owner':owner,'kind':kind,'stable_id':id,'status':'CANDIDATE','conditions':conditions,'negative_boundary':negative,'provenance':[{'source_path':(DOC/'design.json').relative_to(ROOT).as_posix(),'source_sha256':sha(DOC/'design.json'),'json_pointer':'/modules/'+owner,'source_status':'PROJECT_AUTHORED_CANDIDATE_DESIGN'}]}
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
 for suffix,rights,mod,access in [('TEXT','PUBLIC_AUTHORIZED','TEXT',['private test only','text reader support']),('AUDIO','PUBLIC_AUTHORIZED','AUDIO',['private test only','playback required']),('UNVERIFIED','HOLD','AUDIO',['source and access not verified'])]:
  resources[suffix]=add(o,'Resource',o+'.RES.'+suffix,cr,['资源身份和版本已声明；内容未嵌入此候选。'],'PRIVATE_ONLY不可公开；HOLD不得消费；下载可用不等于再发布许可。',resource_identity='urn:learn-kg:synthetic:'+suffix.lower(),rights=rights,modality_refs=[mods[mod]],accessibility=access)
 g={}
 g['AUDIO']=cond(o,o+'.GUARD.AUDIO',cr,[{'field':'permission','op':'EQ','value':True},{'field':'rights','op':'EQ','value':'PRIVATE_ONLY'},{'field':'accessible','op':'EQ','value':True},{'field':'modality','op':'EQ','value':'AUDIO'},{'field':'required_construct','op':'EQ','value':'LISTENING'}],['权限、权利、可及性、模态和构念全部明确。'])
 g['TEXT']=cond(o,o+'.GUARD.TEXT',cr,[{'field':'modality','op':'EQ','value':'TEXT'},{'field':'required_construct','op':'EQ','value':'LISTENING'}],['仅用于反例判别。'])
 g['RIGHTS']=cond(o,o+'.GUARD.RIGHTS',cr,[{'field':'rights','op':'EQ','value':'HOLD'}],['来源权利未知。'])
 g['ACCESS']=cond(o,o+'.GUARD.ACCESS',cr,[{'field':'accessible','op':'EQ','value':False}],['通道不可用。'])
 target=composition(o,cr,[local('P03.PRODUCTION'),local('P04.FLOW'),*mods.values(),*resources.values()],[resources['AUDIO'],resources['TEXT']],[g['AUDIO'],g['TEXT'],g['RIGHTS'],g['ACCESS']],'文本不能替代听辨；私人权利不能升级公开；无障碍/授权未知时HOLD。')
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
 interaction=add(o,'Interaction',o+'.INTERACTION',cr,['任务、评分、角色、帮助、时间和响应版本可追溯。'],'生成答案不属于学习者响应；提示后正确不自动等于独立掌握。',activity_ref=pactivity,role_refs=[prole],observation_refs=list(observations.values()),input_contract='InitialResponse, HintEvent*(stable event ID, task version, event_time, recorded_at), FinalResponse, TaskVersion, ScoringVersion, RoleAuthorization, IndependentRetest; deduplicate identical event IDs, isolate conflicts; preserve event time separately from storage time.',output_contract='Append-only observations; no overwrite; assisted and independent channels remain distinct.',assistance_policy='Record hint before/after and resubmission separately; no answer substitution; ambiguous or missing evidence UNKNOWN.')
 g={}
 g['INDEPENDENT']=cond(o,o+'.GUARD.INDEPENDENT',cr,[{'field':'role_authorized','op':'EQ','value':True},{'field':'hint_count','op':'EQ','value':0},{'field':'independent_retest','op':'EQ','value':True}],['角色授权、无提示及独立复测均须成立。'])
 g['ASSISTED']=cond(o,o+'.GUARD.ASSISTED',cr,[{'field':'hint_count','op':'GT','value':0}],['发生提示。'])
 g['GENERATED']=cond(o,o+'.GUARD.GENERATED',cr,[{'field':'generated_answer','op':'EQ','value':True}],['响应不是学习者生成。'])
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
 g['VERSION']=cond(o,o+'.GUARD.VERSION',cr,[{'field':'scoring_version','op':'EQ','value':'S1'}],['仅示例评分版本S1。'])
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
  ('LEARNER','LEARNER',['choose goal','submit own response','decline support'],['own session','select optional support','exit']),
  ('FACILITATOR','FACILITATOR',['explain task','offer optional support'],['explicitly assigned facilitation scope']),
  ('REVIEWER','REVIEWER',['inspect candidate evidence'],['read-only review scope'])]:
  roles[suffix]=add(o,'Role',o+'.ROLE.'+suffix,cr,['角色身份和当前授权需逐次验证。'],'角色标签不自动授予数据访问或执行权限。',label=label,capability_requirements=caps,permission_requirements=perms)
 guards={}
 guards['EXIT']=cond(o,o+'.GUARD.EXIT',cr,[{'field':'exit','op':'EQ','value':True}],['本人退出。'])
 guards['DENY']=cond(o,o+'.GUARD.DENY',cr,[{'field':'permission','op':'EQ','value':False}],['明确无权限。'])
 guards['UNAVAILABLE']=cond(o,o+'.GUARD.UNAVAILABLE',cr,[{'field':'accessible','op':'EQ','value':False}],['当前通道不可及。'])
 guards['OFFER']=cond(o,o+'.GUARD.OFFER',cr,[{'field':'identity_verified','op':'EQ','value':True},{'field':'permission','op':'EQ','value':True},{'field':'accessible','op':'EQ','value':True},{'field':'capability_match','op':'EQ','value':True},{'field':'learner_selected','op':'EQ','value':True}],['身份、权限、可及性、能力和本人选择全部明确。'])
 rules=[{'condition_ref':guards['EXIT'],'action':'STOP','reason':'本人退出，停止后续非授权动作','priority':0},{'condition_ref':guards['DENY'],'action':'REFUSE','reason':'权限明确为否','priority':1},{'condition_ref':guards['UNAVAILABLE'],'action':'DEFER','reason':'当前环境不可及','priority':2},{'condition_ref':guards['OFFER'],'action':'SUGGEST','reason':'仅提供本人选择的可行支持选项，不自动执行','priority':3}]
 policy=add(o,'PolicySpec',o+'.POLICY',cr,['所有环境和角色字段均需精确绑定版本及实际状态。'],'未知身份/权限不授权；建议不执行；退出优先。',policy_type='GOVERNANCE',rules=rules,unknown_action='CLARIFY',effect='ADVICE_ONLY')
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
 g={}
 g['EXIT']=cond(o,o+'.GUARD.EXIT',cr,[{'field':'exit','op':'EQ','value':True}],['本人退出优先于其他支持判断。'])
 g['IDENTITY']=cond(o,o+'.GUARD.IDENTITY',cr,[{'field':'identity_verified','op':'EQ','value':False}],['身份未知或未核验时澄清；未知属性由unknown_action处理。'])
 g['REVIEWER']=cond(o,o+'.GUARD.REVIEWER',cr,[{'field':'actor_role','op':'EQ','value':'REVIEWER'}],['审核者只读，不作学习者支持决策。'])
 g['PERMISSION']=cond(o,o+'.GUARD.PERMISSION',cr,[{'field':'permission','op':'EQ','value':False}],['权限明确为否时拒绝。'])
 g['LEARNER_SELECTION']=cond(o,o+'.GUARD.LEARNER_SELECTION',cr,[{'field':'actor_role','op':'NE','value':'LEARNER'},{'field':'support_requested_by','op':'NE','value':'LEARNER'},{'field':'learner_selected','op':'EQ','value':False}],['促进者不能代替学习者选择；缺少本人选择时澄清。'])
 records[o+'.GUARD.LEARNER_SELECTION']['combination']='ANY'
 g['ACCESS_UNAVAILABLE']=cond(o,o+'.GUARD.ACCESS_UNAVAILABLE',cr,[{'field':'accessible','op':'EQ','value':False},{'field':'capability_match','op':'EQ','value':False}],['当前环境不可及或能力不匹配时延后。'])
 records[o+'.GUARD.ACCESS_UNAVAILABLE']['combination']='ANY'
 g['REQUEST_UNVERIFIED']=cond(o,o+'.GUARD.REQUEST_UNVERIFIED',cr,[{'field':'support_request_verified','op':'EQ','value':False}],['学习者支持请求必须有可追溯的事件身份。'])
 g['ENVIRONMENT_UNVERIFIED']=cond(o,o+'.GUARD.ENVIRONMENT_UNVERIFIED',cr,[{'field':'environment_profile_verified','op':'EQ','value':False}],['当前环境配置必须由可追溯的能力测试和版本摘要绑定。'])
 g['ESTIMATE_UNBOUND']=cond(o,o+'.GUARD.ESTIMATE_UNBOUND',cr,[{'field':'estimate_status','op':'NE','value':'NOT_ESTIMATED'}],['当前没有已核验估计器；任何模型输出不作为支持依据。'])
 g['CONSTRUCT_UNVERIFIED']=cond(o,o+'.GUARD.CONSTRUCT_UNVERIFIED',cr,[{'field':'construct_review_verified','op':'EQ','value':False}],['任务级构念审查缺失或未核验时请求观察/审查。'])
 g['CONSTRUCT_UNKNOWN']=cond(o,o+'.GUARD.CONSTRUCT_UNKNOWN',cr,[{'field':'construct_relation','op':'EQ','value':'UNKNOWN'}],['构念关系未知时请求任务级观察/审查。'])
 common=[{'field':'identity_verified','op':'EQ','value':True},{'field':'actor_role','op':'EQ','value':'LEARNER'},{'field':'permission','op':'EQ','value':True},{'field':'support_requested_by','op':'EQ','value':'LEARNER'},{'field':'learner_selected','op':'EQ','value':True},{'field':'accessible','op':'EQ','value':True},{'field':'capability_match','op':'EQ','value':True},{'field':'support_request_verified','op':'EQ','value':True},{'field':'environment_profile_verified','op':'EQ','value':True},{'field':'estimate_status','op':'EQ','value':'NOT_ESTIMATED'},{'field':'construct_review_verified','op':'EQ','value':True}]
 g['PRESERVED']=cond(o,o+'.GUARD.PRESERVED',cr,common+[{'field':'construct_relation','op':'EQ','value':'PRESERVED'}],['全部授权/环境/本人选择前提成立，且任务级审查确认构念保持。'])
 g['CHANGED_ASSESSMENT']=cond(o,o+'.GUARD.CHANGED_ASSESSMENT',cr,common+[{'field':'construct_relation','op':'EQ','value':'CHANGED'},{'field':'assessment','op':'EQ','value':True}],['评估构念已改变，原评估延后，另列练习，不替代或并分。'])
 g['CHANGED_PRACTICE']=cond(o,o+'.GUARD.CHANGED_PRACTICE',cr,common+[{'field':'construct_relation','op':'EQ','value':'CHANGED'},{'field':'assessment','op':'EQ','value':False}],['仅在非评估练习中提供独立替代选项。'])
 rules=[
  {'condition_ref':g['EXIT'],'action':'STOP','reason':'本人退出，停止后续支持流程','priority':0},
  {'condition_ref':g['IDENTITY'],'action':'CLARIFY','reason':'身份未知或未核验，不进入个体支持决策','priority':1},
  {'condition_ref':g['REVIEWER'],'action':'REFUSE','reason':'审核角色只读，不执行或决定学习者支持','priority':2},
  {'condition_ref':g['PERMISSION'],'action':'REFUSE','reason':'明确无权限时拒绝','priority':3},
  {'condition_ref':g['LEARNER_SELECTION'],'action':'CLARIFY','reason':'需由学习者本人请求并选择，不能由促进者或系统代选','priority':4},
  {'condition_ref':g['REQUEST_UNVERIFIED'],'action':'CLARIFY','reason':'学习者请求事件未核验，不进入个体支持建议','priority':5},
  {'condition_ref':g['ENVIRONMENT_UNVERIFIED'],'action':'REQUEST_OBSERVATION','reason':'环境配置/能力测试未核验，先补充环境证据','priority':6},
  {'condition_ref':g['ACCESS_UNAVAILABLE'],'action':'DEFER','reason':'可及性或能力匹配不成立时延后，不推断知识缺口','priority':7},
  {'condition_ref':g['ESTIMATE_UNBOUND'],'action':'CLARIFY','reason':'未绑定已核验估计器，不使用模型估计','priority':8},
  {'condition_ref':g['CONSTRUCT_UNVERIFIED'],'action':'REQUEST_OBSERVATION','reason':'任务级构念审查缺失或未核验','priority':9},
  {'condition_ref':g['CONSTRUCT_UNKNOWN'],'action':'REQUEST_OBSERVATION','reason':'构念关系未知，需先完成任务级观察/审查','priority':10},
  {'condition_ref':g['CHANGED_ASSESSMENT'],'action':'SUGGEST','reason':'只提供单独练习建议；原评估延后，不替代或合并评分','priority':11},
  {'condition_ref':g['CHANGED_PRACTICE'],'action':'SUGGEST','reason':'仅在非评估练习中提供独立替代选项','priority':12},
  {'condition_ref':g['PRESERVED'],'action':'SUGGEST','reason':'只提出可拒绝的可选支持，不自动执行','priority':13}
 ]
 policy=add(o,'PolicySpec',o+'.POLICY',cr,['必须同时绑定F05证据通道与F07环境/角色合同；当前支持策略只作建议。'],'不以年龄、发展标签、诊断、群体或固定学习风格推断个体；缺失自述不是无需求；缺失响应/分数不是能力不足；不使用未绑定估计器；改变构念不等价评分；不自动执行或写入状态。',policy_type='GOVERNANCE',rules=rules,unknown_action='CLARIFY',effect='ADVICE_ONLY')
 inputs=[local('F05.COMPOSITION'),local('F05.STATE.RESPONSE'),local('F05.STATE.SELF_REPORT'),local('F05.STATE.SCORE'),local('F05.STATE.ESTIMATE'),local('F07.COMPOSITION'),local('F07.POLICY'),local('F07.ENV.LOW_BANDWIDTH'),local('F07.ENV.SHARED_DEVICE'),local('F07.ENV.PRIVATE_DEVICE'),local('F07.ROLE.LEARNER'),local('F07.ROLE.FACILITATOR'),local('F07.ROLE.REVIEWER')]
 target=composition(o,cr,inputs,[policy],list(g.values()),'未知身份/权限/可及性/构念审查保持CLARIFY或HOLD；明确退出STOP；无权限REFUSE；不可及DEFER；改变构念只可独立练习；本人选择之前不提供个体化支持建议。')
 # E01 evaluation and change governance
 o='E01';cr=claims(o,design['modules'][o]['claims']);owner_claims[o]=cr
 sk=add(o,'SkillType',o+'.SKILL.PROTOCOL_INTEGRITY',cr,['评价协议完整性和版本化证据流程。'],'协议完整不代表干预有效。',label='PROTOCOL_INTEGRITY',performance_boundary='核协议、估计量、比较、结果、随访、审批和复核，不推断实证效果。')
 goal=add(o,'Goal',o+'.GOAL',cr,['目标为协议和证据完整性，而非提高分数。'],'不等于学习者能力目标。',construct_ref=sk,success_evidence_refs=[],scope='受限评价协议完整性')
 obs1=obs(o,o+'.OBS.PRIMARY_OUTCOME',cr,sk,'预先声明的主要结果观测','VERSIONED_OUTCOME','绑定人群、任务版本、评分版本、分母和固定时间点')
 obs2=obs(o,o+'.OBS.SAFETY',cr,sk,'退出/拒绝/不利事件观测','SAFETY_EVENT','保留事件身份、时点、处置和缺失状态')
 records[o+'.GOAL']['success_evidence_refs']=[obs1,obs2]
 g={}
 g['DIRECT_WRITE']=cond(o,o+'.GUARD.DIRECT_WRITE',cr,[{'field':'direct_knowledge_write','op':'EQ','value':True}],['直接写正式知识请求。'])
 g['APPROVED']=cond(o,o+'.GUARD.APPROVED',cr,[{'field':'approved','op':'EQ','value':True},{'field':'protocol_frozen','op':'EQ','value':True}],['协议已冻结且审批已完成。'])
 g['CURRENT_VERSION']=cond(o,o+'.GUARD.CURRENT_VERSION',cr,[{'field':'approved','op':'EQ','value':True},{'field':'current_policy_version','op':'EQ','value':'CURRENT_V1'}],['当前对照策略版本精确固定。'])
 g['CANDIDATE_VERSION']=cond(o,o+'.GUARD.CANDIDATE_VERSION',cr,[{'field':'approved','op':'EQ','value':True},{'field':'candidate_policy_version','op':'EQ','value':'CANDIDATE_V1'}],['候选干预策略版本精确固定。'])
 current=add(o,'PolicySpec',o+'.POLICY.CURRENT',cr,['只定义当前对照建议策略。'],'不得把当前策略当作已验证有效。',policy_type='GOVERNANCE',rules=[{'condition_ref':g['CURRENT_VERSION'],'action':'DEFER','reason':'继续当前流程，不增加候选支持建议','priority':1}],unknown_action='CLARIFY',effect='ADVICE_ONLY')
 candidate=add(o,'PolicySpec',o+'.POLICY.CANDIDATE',cr,['只定义待评价候选建议策略。'],'候选策略不执行、不发布、不写正式知识。',policy_type='GOVERNANCE',rules=[{'condition_ref':g['CANDIDATE_VERSION'],'action':'SUGGEST','reason':'仅向已批准对象提供可拒绝的候选支持建议','priority':1}],unknown_action='CLARIFY',effect='ADVICE_ONLY')
 protocol=add(o,'EvaluationProtocol',o+'.PROTOCOL',cr,['人群、处理版本、比较、结果、时间点、估计量、审批及随访均预先冻结。'],'模拟不是效果；观察性差异不自动因果；个体记录不直接写正式知识。',comparator_ref=current,intervention_ref=candidate,goal_ref=goal,measurement_refs=[obs1,obs2],population_scope='仅限预先定义、已批准的合成/研究目标人群；不推断其他总体。',estimand='若随机/班级随机分配、版本固定、完整随访和识别条件均成立，估计分配至候选可拒绝支持建议相对当前流程的28日主要结果ITT差；未满足条件不估计。',followup='固定28日随访；未完成不插补为成功。',uncertainty='没有真实合规研究数据；本协议为候选模板。模型模拟、离线测试和即时分数不构成长期效果。',approval_required=True,effect='NO_DIRECT_KNOWLEDGE_WRITE')
 target=composition(o,cr,[protocol,local('P10.FLOW'),current,candidate,goal,obs1,obs2],[candidate],[g['APPROVED'],g['CURRENT_VERSION'],g['CANDIDATE_VERSION'],g['DIRECT_WRITE']],'仅生成待审分析建议；独立复核和授权发布为后续任务，禁止直接修改正式知识。')
 # Add cases and attach exact evidence refs to each composition.
 all_results=[]
 for owner,name,x,y in fixtures():
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
 write(DOC/'fixtures.json',[{'owner':o,'name':n,'input':x,'expected':y} for o,n,x,y in fixtures()])
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
  expected_bindings={'F03':['P03.PRODUCTION','P04.FLOW'],'F04':['P03.PRODUCTION','P06.FLOW'],'F05':['P08.FLOW','P10.FLOW'],'F07':['P10.FLOW'],'A07':['F05.COMPOSITION','F05.STATE.RESPONSE','F05.STATE.SELF_REPORT','F05.STATE.SCORE','F05.STATE.ESTIMATE','F07.COMPOSITION','F07.POLICY'],'E01':['P10.FLOW']}
  for owner,expected_ids in expected_bindings.items():
   comp=load_record(im,local(owner+'.COMPOSITION'));actual_ids=[x['stable_id'] for x in comp['input_refs']]
   assert all(x in actual_ids for x in expected_ids),(owner,actual_ids,expected_ids)
   for id in expected_ids:load_record(im,local(id))
   binding_results.append({'owner':owner,'expected_process_refs':expected_ids,'actual_process_refs':actual_ids,'status':'STATIC_TYPED_BINDING_ONLY_NOT_EXECUTION'})
  if01_contract=ROOT/'docs/implementation/if01/interface-contract.json'
  if01_receipt=ROOT/'evidence/tasks/IF01/IF01-FORMAL-01.json'
  if01_view=next(v for v in load(if01_contract)['view_routes'] if v['owner']=='A07')
  assert set(if01_view['task_dependencies'])=={'F05','F07','IF01'}
  assert set(if01_view['required_scope_ids'])=={'A07.RQ01','A07.RQ02','A07.RQ03','A07.RQ04'}
  a07_input_records=[]
  for id in expected_bindings['A07']:
   z=records[id];a07_input_records.append({'stable_id':id,'kind':z['kind'],'owner':z['owner'],'record_sha256':dig(z)})
  inherited_claims=[]
  for z in cr:
   origin='F05' if z in records['F05.COMPOSITION']['claim_refs'] else 'F07'
   inherited_claims.append({'ref':z,'inherited_from':origin})
  write(DOC/'composition-input-bindings.json',{'owner':'A07','status':'EXACT_PREPARATION_BINDING_ONLY','package_id':'learning-process','version':VERSION,'manifest_sha256':sha(mf),'task_dependencies':tasks['A07']['depends_on'],'inputs':a07_input_records,'inherited_claim_refs':inherited_claims,'if01':{'interface_version':if01_view.get('interface_version',load(if01_contract).get('interface_version')),'contract_path':'docs/implementation/if01/interface-contract.json','contract_sha256':sha(if01_contract),'receipt_path':'evidence/tasks/IF01/IF01-FORMAL-01.json','receipt_sha256':sha(if01_receipt),'content_digest':load(if01_receipt)['content_digest'],'required_scope_ids':if01_view['required_scope_ids'],'task_dependencies':if01_view['task_dependencies']},'limits':'IF01 is a file/receipt contract pin, not a synthetic canonical record; no formal A07 receipt or CQ/LC qualification.'})
  write(DOC/'import-receipt.json',receipt)
  write(DOC/'sql-results.json',{'status':'MEMORY_SQLITE_BUILDER_ONLY','cases':len(replay),'results':replay,'cross_module_bindings':binding_results,'manifest_sha256':sha(mf),'migration_count':len(migration),'record_count':len(records),'limits':'No persistent SQLite; no independent oracle or task qualification.'})
  print('PROCESS_MIGRATED',len(migration),'F_RECORDS',len(records)-len(migration),'TOTAL',len(records),'F_CASES',len(replay),'MANIFEST',sha(mf))
 finally:im.close()
if __name__=='__main__':main()
