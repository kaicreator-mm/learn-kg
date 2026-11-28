"""Bounded synthetic decisions for F03/F04/F05/F07/E01. No external effects."""
import json,hashlib
from pathlib import Path
def dig(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def _sealed_digest(x,key):
 return dig({k:v for k,v in x.items() if k!=key})

VISUAL_ACCESSIBILITY_EVIDENCE={
 'evidence_id':'F03.ACCESSIBILITY.VISUAL.V1',
 'evidence_version':'V1',
 'resource_identity':'urn:learn-kg:synthetic:visual:v1',
 'resource_version':'V1',
 'modality':'VISUAL',
 'required_construct':'VISUAL_RECOGNITION',
 'test_scope':'VISUAL_RENDERING_AND_ALTERNATIVE_DESCRIPTION',
 'test_result':'PASS',
 'source_status':'PROJECT_AUTHORED_SYNTHETIC_CANDIDATE'
}
VISUAL_ACCESSIBILITY_EVIDENCE['evidence_sha256']=dig(VISUAL_ACCESSIBILITY_EVIDENCE)

F04_CLOCK_CONTRACT={
 'event_clock_domain':'UTC_EPOCH_SECONDS',
 'recording_clock_domain':'UTC_EPOCH_SECONDS',
 'event_clock_id':'CLIENT-CLOCK-01',
 'recording_clock_id':'SERVER-CLOCK-01',
 'clock_sync_status':'BOUNDED',
 'max_clock_skew_seconds':300
}
F05_SCORING_VERSION_PIN='S1'
_PROCESS_VERSION='0.1.0-process-candidate-3'

def _valid_version(value):
 import re
 return isinstance(value,str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,63}',value) is not None

def f03(x):
 if not isinstance(x,dict):return 'HOLD'
 if x.get('permission') is not True or x.get('rights') not in ('PRIVATE_ONLY','PUBLIC_AUTHORIZED'):return 'HOLD'
 if x.get('accessible') is not True:return 'HOLD'
 if type(x.get('publication')) is not bool:return 'HOLD'
 if x['publication'] is True and x['rights']!='PUBLIC_AUTHORIZED':return 'REFUSE_PUBLICATION'
 mapping={'TEXT':'READING','AUDIO':'LISTENING','VISUAL':'VISUAL_RECOGNITION'}
 modality=x.get('modality');construct=x.get('required_construct')
 if modality not in mapping or construct not in ('READING','LISTENING','VISUAL_RECOGNITION'):return 'HOLD'
 if mapping[modality]!=construct:return 'REJECT_CONSTRUCT_SUBSTITUTION'
 if modality=='VISUAL':
  evidence=x.get('visual_accessibility_evidence')
  if not isinstance(evidence,dict) or evidence!=VISUAL_ACCESSIBILITY_EVIDENCE:return 'HOLD'
 return 'PRIVATE_RESOURCE_CANDIDATE' if x['rights']=='PRIVATE_ONLY' else 'PUBLIC_RESOURCE_CANDIDATE_WITH_SEPARATE_RIGHTS_CHECK'

def _ref(kind,owner,stable_id):
 return {'package_id':'learning-process','version':_PROCESS_VERSION,'kind':kind,'stable_id':stable_id,'owner':owner}

def _event_digest(e):
 return _sealed_digest(e,'event_record_sha256')

def _valid_clocked_event_time(e,clock):
 if type(e.get('event_time')) is not int or type(e.get('recorded_at')) is not int:return False
 if min(e['event_time'],e['recorded_at'])<0:return False
 if e.get('event_clock_domain')!=clock['event_clock_domain'] or e.get('recording_clock_domain')!=clock['recording_clock_domain']:return False
 if e.get('event_clock_id')!=clock['event_clock_id'] or e.get('recording_clock_id')!=clock['recording_clock_id']:return False
 return abs(e['recorded_at']-e['event_time'])<=clock['max_clock_skew_seconds']

def _valid_event(e,event_type,task,version,variant,learner_id,construct_ref,scoring_ref,scoring_version,clock):
 if not isinstance(e,dict):return False
 if e.get('event_type')!=event_type or not isinstance(e.get('event_id'),str) or not e['event_id']:return False
 if e.get('task_id')!=task or e.get('task_version')!=version or not _valid_version(e.get('task_version')) or e.get('variant_id')!=variant:return False
 if e.get('learner_id')!=learner_id or e.get('actor_id')!=learner_id:return False
 if not _valid_clocked_event_time(e,clock):return False
 if e.get('actor_role')!='LEARNER' or e.get('generated_answer') is not False:return False
 if not isinstance(e.get('response'),str) or not e['response']:return False
 if e.get('assistance_status') not in ('NONE','ASSISTED'):return False
 if e.get('construct_ref')!=construct_ref:return False
 sb=e.get('scoring_binding')
 if not isinstance(sb,dict) or sb.get('observation_ref')!=scoring_ref or sb.get('scoring_version')!=scoring_version or not _valid_version(sb.get('scoring_version')):return False
 h=e.get('event_record_sha256')
 return isinstance(h,str) and len(h)==64 and h==_event_digest(e)

def f04(x):
 if not isinstance(x,dict) or x.get('role_authorized') is not True:return 'HOLD'
 if x.get('generated_answer') is True:return 'NOT_LEARNER_EVIDENCE'
 if x.get('generated_answer') is not False:return 'UNKNOWN'
 task_version=x.get('expected_task_version');scoring_version=x.get('expected_scoring_version')
 if not _valid_version(task_version) or not _valid_version(scoring_version):return 'HOLD'
 if x.get('task_version')!=task_version or x.get('scoring_version')!=scoring_version:return 'HOLD'
 if scoring_version!='S1':return 'HOLD'
 clock=x.get('clock_contract')
 if not isinstance(clock,dict) or clock!=F04_CLOCK_CONTRACT:return 'HOLD'
 construct_ref=_ref('Goal','P03','P03.PRODUCTION.GOAL')
 scoring_ref=_ref('ObservationSpec','P06','P06.ACT.OBSERVE.OBS')
 retest_ref=_ref('ObservationSpec','F04','F04.OBS.RETEST')
 task=x.get('task_id');learner_id=x.get('learner_id')
 if not isinstance(task,str) or not task or not isinstance(learner_id,str) or not learner_id:return 'HOLD'
 initial=x.get('initial_response_event');final=x.get('final_response_event')
 if not isinstance(initial,dict) or not isinstance(final,dict):return 'UNKNOWN'
 variant=initial.get('variant_id')
 if not isinstance(variant,str) or not variant:return 'HOLD'
 if not _valid_event(initial,'INITIAL_RESPONSE',task,task_version,variant,learner_id,construct_ref,scoring_ref,scoring_version,clock):return 'HOLD'
 if not _valid_event(final,'FINAL_RESPONSE',task,task_version,variant,learner_id,construct_ref,scoring_ref,scoring_version,clock):return 'HOLD'
 if final['event_time']<initial['event_time'] or final['recorded_at']<initial['recorded_at'] or initial.get('assistance_status')!='NONE':return 'HOLD'
 if x.get('hint_events') and final.get('assistance_status')!='ASSISTED':return 'HOLD'
 if not x.get('hint_events') and final.get('assistance_status')!='NONE':return 'HOLD'
 events=[initial,final]
 hints=x.get('hint_events')
 if not isinstance(hints,list):return 'HOLD'
 seen={};last_recorded=initial['recorded_at']
 for e in hints:
  if not isinstance(e,dict) or not isinstance(e.get('event_id'),str) or not e['event_id']:return 'HOLD'
  if e.get('event_type')!='HINT' or e.get('task_id')!=task or e.get('task_version')!=task_version or not _valid_version(e.get('task_version')) or e.get('variant_id')!=variant or e.get('learner_id')!=learner_id or not isinstance(e.get('actor_id'),str) or not e['actor_id']:return 'HOLD'
  if not _valid_clocked_event_time(e,clock):return 'HOLD'
  if e.get('assistance_status')!='HINT':return 'HOLD'
  h=e.get('event_record_sha256')
  if not isinstance(h,str) or len(h)!=64 or h!=_event_digest(e):return 'HOLD'
  old=seen.get(e['event_id'])
  if old is not None and old!=h:return 'HOLD'
  seen[e['event_id']]=h
  if e['event_time']<initial['event_time'] or e['event_time']>final['event_time']:return 'HOLD'
  if e['recorded_at']<last_recorded or e['recorded_at']>final['recorded_at']:return 'HOLD'
  last_recorded=e['recorded_at']
  if old is None:events.append(e)
 ids=[e['event_id'] for e in events]
 if len(ids)!=len(set(ids)):return 'HOLD'
 retest=x.get('retest_event')
 if retest is None:return 'ASSISTED_NOT_INDEPENDENT' if seen or final.get('assistance_status')=='ASSISTED' else 'UNKNOWN'
 if not isinstance(retest,dict):return 'HOLD'
 if retest.get('generated_answer') is True:return 'NOT_LEARNER_EVIDENCE'
 if retest.get('generated_answer') is not False:return 'UNKNOWN'
 if retest.get('assistance_status')!='NONE':return 'ASSISTED_NOT_INDEPENDENT'
 rv=retest.get('variant_id')
 if not isinstance(rv,str) or not rv or rv==variant:return 'HOLD'
 if not _valid_event(retest,'INDEPENDENT_RETEST',task,task_version,rv,learner_id,construct_ref,scoring_ref,scoring_version,clock):return 'HOLD'
 if retest.get('observation_ref')!=retest_ref:return 'HOLD'
 if retest['event_time']<final['event_time'] or retest['recorded_at']<final['recorded_at']:return 'HOLD'
 if retest['event_id'] in set(ids):return 'HOLD'
 return 'INDEPENDENT_RETEST_OBSERVATION'

def f05(x):
 if not isinstance(x,dict):return 'HOLD'
 expected=x.get('expected_scoring_version')
 if expected!=F05_SCORING_VERSION_PIN:return 'HOLD'
 out={}
 for name in ('response','self_report','score','estimate'):
  z=x.get(name)
  if not isinstance(z,dict):return 'HOLD'
  status=z.get('status')
  if status in ('MISSING','INVALID','NOT_ADMINISTERED'):out[name]={'status':'UNKNOWN','reason':status};continue
  if name=='response':
   if status!='OBSERVED' or not isinstance(z.get('value'),str) or not z['value'] or not _valid_version(z.get('task_version')):return 'HOLD'
   out[name]={'status':'OBSERVED','value':z['value'],'task_version':z['task_version']}
  elif name=='self_report':
   if status!='OBSERVED' or not isinstance(z.get('value'),str) or not z['value'] or z.get('respondent')!='LEARNER':return 'HOLD'
   out[name]={'status':'SELF_REPORTED','value':z['value']}
  elif name=='score':
   if status!='OBSERVED' or type(z.get('value')) not in (int,float) or not _valid_version(z.get('scoring_version')) or type(z.get('denominator')) is not int or z['denominator']<=0:return 'HOLD'
   if z['scoring_version']!=expected:return 'HOLD'
   out[name]={'status':'SCORED','value':z['value'],'scoring_version':z['scoring_version'],'denominator':z['denominator']}
  else:
   if status=='NOT_RUN':out[name]={'status':'NOT_ESTIMATED'};continue
   return 'HOLD'
 return {'channels':out,'combined_mastery':'NOT_INFERRED'}

TRUSTED_FACILITATOR_AUTHORITY_RESOLVER_BOUND=False
TRUSTED_LEARNER_AUTHORITY_RESOLVER_BOUND=False
def f07(x):
 if not isinstance(x,dict):return 'HOLD'
 if x.get('exit') is True:return 'STOP'
 if x.get('exit') is not False:return 'CLARIFY'
 if x.get('identity_verified') is not True:return 'CLARIFY'
 role=x.get('role')
 if role=='REVIEWER':return 'REFUSE'
 if role not in ('LEARNER','FACILITATOR'):return 'CLARIFY'
 if not isinstance(x.get('actor_id'),str) or not x['actor_id'] or not isinstance(x.get('learner_id'),str) or not x['learner_id']:return 'CLARIFY'
 if not isinstance(x.get('session_id'),str) or not x['session_id'] or type(x.get('now')) is not int:return 'CLARIFY'
 if not _valid_version(x.get('task_version')) or not isinstance(x.get('task_id'),str) or not x['task_id']:return 'CLARIFY'
 req=x.get('support_request')
 if not isinstance(req,dict):return 'CLARIFY'
 for k in ('event_id','learner_id','session_id','selected_option_id','selected_by'):
  if not isinstance(req.get(k),str) or not req[k]:return 'CLARIFY'
 if req['selected_by']!='LEARNER' or req['learner_id']!=x['learner_id'] or req['session_id']!=x['session_id']:return 'CLARIFY'
 if req.get('task_id')!=x['task_id'] or req.get('task_version')!=x['task_version']:return 'CLARIFY'
 if type(req.get('event_time')) is not int or type(req.get('recorded_at')) is not int or min(req['event_time'],req['recorded_at'])<0 or max(req['event_time'],req['recorded_at'])>x['now']:return 'CLARIFY'
 rh=req.get('event_sha256')
 if not isinstance(rh,str) or len(rh)!=64 or rh!=_sealed_digest(req,'event_sha256'):return 'HOLD'
 authority=x.get('role_authority')
 if not isinstance(authority,dict):return 'CLARIFY'
 for k in ('authority_id','authority_version','actor_id','learner_id','role','purpose','scope','session_id','authority_kind','grantor_id'):
  if not isinstance(authority.get(k),str) or not authority[k]:return 'CLARIFY'
 if authority.get('actor_id')!=x['actor_id'] or authority.get('learner_id')!=x['learner_id'] or authority.get('role')!=role or authority.get('session_id')!=x['session_id'] or authority.get('authority_version')!='V1':return 'HOLD'
 if authority.get('purpose')!='OFFER_LEARNER_SUPPORT' or authority.get('scope')!='LEARNER_SUPPORT_ADVICE_ONLY':return 'REFUSE'
 if type(authority.get('permission')) is not bool:return 'CLARIFY'
 if authority['permission'] is False:return 'REFUSE'
 if type(authority.get('not_before')) is not int or type(authority.get('issued_at')) is not int or type(authority.get('expires_at')) is not int:return 'CLARIFY'
 if not 0<=authority['issued_at']<=authority['not_before']<=x['now']<authority['expires_at']:return 'REFUSE'
 ah=authority.get('evidence_sha256')
 if not isinstance(ah,str) or len(ah)!=64 or ah!=_sealed_digest(authority,'evidence_sha256'):return 'HOLD'
 if role=='LEARNER':
  if x['actor_id']!=x['learner_id'] or authority['authority_kind']!='LEARNER_SESSION_SELF' or authority['grantor_id']!=x['learner_id'] or authority.get('assignment_id') is not None:return 'REFUSE'
 elif role=='FACILITATOR':
  if authority['authority_kind']!='ASSIGNED_FACILITATOR' or authority['grantor_id']==x['actor_id'] or not isinstance(authority.get('assignment_id'),str) or not authority['assignment_id'] or authority.get('assigned_learner_id')!=x['learner_id']:return 'REFUSE'
 env=x.get('environment_profile')
 if not isinstance(env,dict) or not isinstance(env.get('profile_id'),str) or not env['profile_id'] or not isinstance(env.get('profile_version'),str) or not env['profile_version']:return 'CLARIFY'
 if env.get('profile_version')!='V1' or type(env.get('tested_at')) is not int or type(env.get('valid_until')) is not int or env['tested_at']<0 or env['tested_at']>x['now']:return 'HOLD'
 if env.get('task_id')!=x['task_id'] or env.get('task_version')!=x['task_version']:return 'HOLD'
 if not env['tested_at']<=x['now']<env['valid_until'] or x['now']-env['tested_at']>3600:return 'HOLD'
 eh=env.get('profile_sha256')
 if not isinstance(eh,str) or len(eh)!=64 or eh!=_sealed_digest(env,'profile_sha256'):return 'HOLD'
 if type(env.get('accessible')) is not bool or type(env.get('capability_match')) is not bool:return 'CLARIFY'
 if env['accessible'] is False or env['capability_match'] is False:return 'DEFER'
 if role=='LEARNER' and (not TRUSTED_LEARNER_AUTHORITY_RESOLVER_BOUND or authority.get('resolver_status')!='VERIFIED' or not isinstance(authority.get('resolver_id'),str) or not authority['resolver_id']):return 'HOLD'
 if role=='FACILITATOR' and (not TRUSTED_FACILITATOR_AUTHORITY_RESOLVER_BOUND or authority.get('resolver_status')!='VERIFIED' or not isinstance(authority.get('resolver_id'),str) or not authority['resolver_id']):return 'HOLD'
 return 'SUGGEST_ONLY_NO_EXECUTION'

def _analysis_plan():
 p=Path(__file__).with_name('analysis-plan.json')
 if not p.is_file():return None,None,None
 raw=p.read_bytes()
 try:plan=json.loads(raw)
 except Exception:return None,None,None
 return plan,hashlib.sha256(raw).hexdigest(),p
def _evidence_object_valid(evidence,kind,decision,plan_hash,now,root):
 if not isinstance(evidence,dict) or evidence.get('kind')!=kind:return False
 if evidence.get('subject_id')!='E01.PROTOCOL' or evidence.get('subject_version')!='V2' or evidence.get('analysis_plan_sha256')!=plan_hash or evidence.get('decision')!=decision:return False
 for key in ('authority_id','artifact_path','repository'):
  if not isinstance(evidence.get(key),str) or not evidence[key]:return False
 if evidence['repository']!='kaicreator-mm/learn-kg' or type(evidence.get('issue_number')) is not int or evidence['issue_number']<=0 or type(evidence.get('comment_id')) is not int or evidence['comment_id']<=0:return False
 if type(evidence.get('issued_at')) is not int or type(evidence.get('expires_at')) is not int:return False
 if not evidence['issued_at']<=now<evidence['expires_at']:return False
 h=evidence.get('artifact_sha256')
 if not isinstance(h,str) or len(h)!=64 or any(c not in '0123456789abcdef' for c in h):return False
 artifact=Path(evidence['artifact_path'])
 if artifact.is_absolute() or '..' in artifact.parts:return False
 root=root.resolve();target=(root/artifact).resolve()
 if root not in target.parents or not target.is_file():return False
 return hashlib.sha256(target.read_bytes()).hexdigest()==h

def _evidence_pair_valid(approval,review,plan_hash,now,root):
 if not _evidence_object_valid(approval,'RESEARCH_PROTOCOL_APPROVAL','APPROVED',plan_hash,now,root):return False
 if not _evidence_object_valid(review,'INDEPENDENT_NON_WRITER_REVIEW','ACCEPT_SCOPED',plan_hash,now,root):return False
 # Approval and independent review must be distinct records and authorities.
 if (approval['repository'],approval['issue_number'],approval['comment_id'])==(review['repository'],review['issue_number'],review['comment_id']):return False
 for key in ('artifact_path','artifact_sha256','authority_id'):
  if approval[key]==review[key]:return False
 return True

def e01(x):
 if not isinstance(x,dict):return 'HOLD'
 if x.get('direct_knowledge_write') is True:return 'REFUSE'
 if x.get('direct_knowledge_write') is not False:return 'HOLD'
 plan,plan_hash,plan_path=_analysis_plan()
 if plan is None:return 'HOLD'
 plan_ref='docs/implementation/f-composition-preparation/analysis-plan.json'
 if x.get('analysis_plan_ref')!=plan_ref or x.get('analysis_plan_sha256')!=plan_hash:return 'HOLD'
 if x.get('analysis_plan_version')!=plan.get('version') or x.get('analysis_plan_summary')!=plan.get('analysis_plan_summary'):return 'HOLD'
 if x.get('protocol_id')!='E01.PROTOCOL' or x.get('protocol_version')!='V2':return 'HOLD'
 if x.get('population_id')!=plan['population']['population_id']:return 'HOLD'
 if x.get('assignment_unit')!=plan['allocation']['unit'] or x.get('assignment_method')!=plan['allocation']['method']:return 'HOLD'
 unit=x.get('assignment_unit');method=x.get('assignment_method')
 compatible={'LEARNER':('RANDOMIZED','OBSERVATIONAL'),'CLASSROOM':('CLUSTER_RANDOMIZED','OBSERVATIONAL')}
 if unit not in compatible or method not in compatible[unit]:return 'HOLD'
 if x.get('intervention_version')!=plan['intervention']['version'] or x.get('comparator_version')!=plan['comparator']['version']:return 'HOLD'
 if x.get('primary_outcome_id')!=plan['primary_outcome']['id']:return 'HOLD'
 if type(x.get('followup_days')) is not int or x['followup_days']!=plan['followup']['days']:return 'HOLD'
 if type(x.get('assignment_verified')) is not bool:return 'HOLD'
 if x.get('data_kind')=='SIMULATED':return 'SIMULATION_ONLY_NOT_EFFECT'
 if method=='OBSERVATIONAL' or x['assignment_verified'] is False:return 'DESCRIPTIVE_ONLY_NO_CAUSAL_ESTIMATE'
 if x.get('data_kind')!='OBSERVED':return 'HOLD'
 if 'approved' in x or 'protocol_frozen' in x or 'independent_review' in x:return 'HOLD'
 now=x.get('evaluation_time')
 if type(now) is not int or now<0:return 'HOLD'
 root=Path(__file__).resolve().parents[3]
 if not _evidence_pair_valid(x.get('approval_evidence_ref'),x.get('independent_review_evidence_ref'),plan_hash,now,root):return 'HOLD'
 # No trusted authority/signature resolver is currently bound. Even independently
 # distinct, time-valid and hash-matching evidence objects cannot authorize analysis.
 return 'HOLD'

def a07(x):
 def d(action,scope='NONE',assessment='UNKNOWN',basis='NO_AUTOMATIC_INFERENCE'):
  return {'action':action,'support_scope':scope,'assessment_disposition':assessment,'evidence_basis':basis,'effect':'ADVICE_ONLY'}
 if not isinstance(x,dict):return d('CLARIFY',basis='INVALID_INPUT')
 if x.get('exit') is True:return d('STOP',basis='LEARNER_EXIT')
 if x.get('exit') is not False:return d('CLARIFY',basis='EXIT_STATE_UNKNOWN')
 role=x.get('actor_role')
 if role=='REVIEWER':return d('REFUSE',basis='REVIEW_ONLY_ROLE')
 if role not in ('LEARNER','FACILITATOR'):return d('CLARIFY',basis='ROLE_UNKNOWN')
 f07_input=x.get('f07_input')
 if not isinstance(f07_input,dict):return d('REQUEST_OBSERVATION',basis='F07_TYPED_EVIDENCE_REQUIRED')
 if f07_input.get('role')!=role:return d('CLARIFY',basis='F07_ROLE_BINDING_MISMATCH')
 if f07_input.get('task_id')!=x.get('task_id') or f07_input.get('task_version')!=x.get('task_version'):return d('REQUEST_OBSERVATION',basis='F07_TASK_BINDING_MISMATCH')
 f07_decision=f07(f07_input)
 if f07_decision=='STOP':return d('STOP',basis='LEARNER_EXIT')
 if f07_decision=='REFUSE':return d('REFUSE',basis='F07_AUTHORITY_REFUSED')
 if f07_decision=='CLARIFY':return d('CLARIFY',basis='F07_EVIDENCE_INCOMPLETE')
 if f07_decision=='DEFER':return d('DEFER',basis='ENVIRONMENT_OR_CAPABILITY_BLOCK')
 if f07_decision not in ('HOLD','SUGGEST_ONLY_NO_EXECUTION'):return d('REQUEST_OBSERVATION',basis='F07_VALIDATED_DECISION_REQUIRED')
 if type(x.get('assessment')) is not bool:return d('CLARIFY',basis='ASSESSMENT_SCOPE_UNKNOWN')
 if x.get('estimate_status')!='NOT_ESTIMATED':return d('CLARIFY',basis='UNBOUND_ESTIMATE_NOT_USED')
 sr=x.get('self_report',{'status':'MISSING'})
 if not isinstance(sr,dict) or sr.get('status') not in ('MISSING','NOT_ADMINISTERED','OBSERVED'):return d('CLARIFY',basis='SELF_REPORT_INVALID')
 if sr.get('status')=='OBSERVED' and (sr.get('respondent')!='LEARNER' or not isinstance(sr.get('value'),str) or not sr['value']):return d('CLARIFY',basis='SELF_REPORT_NOT_LEARNER_AUTHORED')
 for field in ('response','score'):
  z=x.get(field,{'status':'MISSING'})
  if not isinstance(z,dict) or z.get('status') not in ('MISSING','NOT_ADMINISTERED','INVALID','OBSERVED'):return d('CLARIFY',basis='OBSERVATION_STATUS_INVALID')
 review=x.get('construct_review')
 if not isinstance(review,dict):return d('REQUEST_OBSERVATION',basis='TASK_LEVEL_CONSTRUCT_REVIEW_REQUIRED')
 for field in ('review_id','review_version','task_id','task_version','assessment_id','assessment_version','construct_id','relation','review_result','source_status'):
  if not isinstance(review.get(field),str) or not review[field]:return d('REQUEST_OBSERVATION',basis='CONSTRUCT_REVIEW_PIN_REQUIRED')
 if review['task_id']!=x.get('task_id') or review['task_version']!=x.get('task_version') or review['assessment_id']!=x.get('assessment_id') or review['assessment_version']!=x.get('assessment_version'):return d('REQUEST_OBSERVATION',basis='CONSTRUCT_REVIEW_IDENTITY_MISMATCH')
 if review['source_status']!='PROJECT_AUTHORED_SYNTHETIC_CANDIDATE' or review['review_result']!='PASS':return d('REQUEST_OBSERVATION',basis='CONSTRUCT_REVIEW_NOT_VERIFIED')
 if type(review.get('reviewed_at')) is not int or type(review.get('valid_until')) is not int:return d('REQUEST_OBSERVATION',basis='CONSTRUCT_REVIEW_TIME_REQUIRED')
 now=f07_input.get('now')
 if type(now) is not int or not review['reviewed_at']<=now<review['valid_until'] or now-review['reviewed_at']>2592000:return d('REQUEST_OBSERVATION',basis='CONSTRUCT_REVIEW_STALE_OR_INVALID')
 h=review.get('review_sha256')
 if not isinstance(h,str) or len(h)!=64 or h!=_sealed_digest(review,'review_sha256'):return d('REQUEST_OBSERVATION',basis='CONSTRUCT_REVIEW_DIGEST_INVALID')
 relation=review['relation']
 if relation not in ('PRESERVED','CHANGED'):return d('REQUEST_OBSERVATION',basis='CONSTRUCT_RELATION_UNKNOWN')
 if f07_decision!='SUGGEST_ONLY_NO_EXECUTION':
  return d('REQUEST_OBSERVATION',basis='F07_TRUSTED_AUTHORITY_RESOLVER_UNBOUND')
 if relation=='CHANGED' and x['assessment'] is True:return d('SUGGEST','PRACTICE_ONLY','DEFER_ASSESSMENT','CONSTRUCT_CHANGED_NOT_SCORE_EQUIVALENT')
 if relation=='CHANGED':return d('SUGGEST','PRACTICE_ONLY','NOT_APPLICABLE','CONSTRUCT_CHANGED_SEPARATE_PRACTICE')
 return d('SUGGEST','OPTIONAL_SUPPORT','PRESERVED','TASK_LEVEL_CONSTRUCT_REVIEW_PINNED')

FUN={'A07':a07,'F03':f03,'F04':f04,'F05':f05,'F07':f07,'E01':e01}
def fixtures():
 out=[]
 def a(o,name,x,y):out.append((o,name,x,y))

 a('F03','AUDIO_LISTENING_SYNTHETIC',dict(permission=True,rights='PUBLIC_AUTHORIZED',accessible=True,publication=False,modality='AUDIO',required_construct='LISTENING'),'PUBLIC_RESOURCE_CANDIDATE_WITH_SEPARATE_RIGHTS_CHECK')
 a('F03','TEXT_READING_SYNTHETIC',dict(permission=True,rights='PUBLIC_AUTHORIZED',accessible=True,publication=False,modality='TEXT',required_construct='READING'),'PUBLIC_RESOURCE_CANDIDATE_WITH_SEPARATE_RIGHTS_CHECK')
 a('F03','TEXT_FOR_LISTENING_REJECT',dict(permission=True,rights='PUBLIC_AUTHORIZED',accessible=True,publication=False,modality='TEXT',required_construct='LISTENING'),'REJECT_CONSTRUCT_SUBSTITUTION')
 a('F03','RIGHTS_UNKNOWN_HOLD',dict(permission=True,rights='HOLD',accessible=True,publication=False,modality='AUDIO',required_construct='LISTENING'),'HOLD')
 a('F03','ACCESS_UNAVAILABLE_HOLD',dict(permission=True,rights='PRIVATE_ONLY',accessible=False,publication=False,modality='AUDIO',required_construct='LISTENING'),'HOLD')
 a('F03','PRIVATE_TO_PUBLIC_REFUSE',dict(permission=True,rights='PRIVATE_ONLY',accessible=True,publication=True,modality='AUDIO',required_construct='LISTENING'),'REFUSE_PUBLICATION')
 a('F03','VISUAL_RECOGNITION_SYNTHETIC',dict(permission=True,rights='PUBLIC_AUTHORIZED',accessible=True,publication=False,modality='VISUAL',required_construct='VISUAL_RECOGNITION',visual_accessibility_evidence=dict(VISUAL_ACCESSIBILITY_EVIDENCE)),'PUBLIC_RESOURCE_CANDIDATE_WITH_SEPARATE_RIGHTS_CHECK')
 a('F03','VISUAL_ACCESSIBILITY_UNKNOWN_HOLD',dict(permission=True,rights='PUBLIC_AUTHORIZED',accessible=True,publication=False,modality='VISUAL',required_construct='VISUAL_RECOGNITION'),'HOLD')
 visual_bad_id=dict(VISUAL_ACCESSIBILITY_EVIDENCE);visual_bad_id['evidence_id']='F03.ACCESSIBILITY.OTHER.V1';visual_bad_id['evidence_sha256']=dig({k:v for k,v in visual_bad_id.items() if k!='evidence_sha256'})
 a('F03','VISUAL_ACCESSIBILITY_RESOURCE_MISMATCH_HOLD',dict(permission=True,rights='PUBLIC_AUTHORIZED',accessible=True,publication=False,modality='VISUAL',required_construct='VISUAL_RECOGNITION',visual_accessibility_evidence=visual_bad_id),'HOLD')
 visual_bad_hash=dict(VISUAL_ACCESSIBILITY_EVIDENCE);visual_bad_hash['evidence_sha256']='0'*64
 a('F03','VISUAL_ACCESSIBILITY_DIGEST_MISMATCH_HOLD',dict(permission=True,rights='PUBLIC_AUTHORIZED',accessible=True,publication=False,modality='VISUAL',required_construct='VISUAL_RECOGNITION',visual_accessibility_evidence=visual_bad_hash),'HOLD')
 visual_bad_scope=dict(VISUAL_ACCESSIBILITY_EVIDENCE);visual_bad_scope['test_scope']='UNRELATED_SCOPE';visual_bad_scope['evidence_sha256']=dig({k:v for k,v in visual_bad_scope.items() if k!='evidence_sha256'})
 a('F03','VISUAL_ACCESSIBILITY_SCOPE_MISMATCH_HOLD',dict(permission=True,rights='PUBLIC_AUTHORIZED',accessible=True,publication=False,modality='VISUAL',required_construct='VISUAL_RECOGNITION',visual_accessibility_evidence=visual_bad_scope),'HOLD')
 a('F03','UNSUPPORTED_VIDEO_MODALITY_HOLD',dict(permission=True,rights='PUBLIC_AUTHORIZED',accessible=True,publication=False,modality='VIDEO',required_construct='VISUAL_RECOGNITION'),'HOLD')
 a('F03','MISSING_MODALITY_HOLD',dict(permission=True,rights='PUBLIC_AUTHORIZED',accessible=True,publication=False,required_construct='READING'),'HOLD')
 a('F03','UNSUPPORTED_CONSTRUCT_HOLD',dict(permission=True,rights='PUBLIC_AUTHORIZED',accessible=True,publication=False,modality='TEXT',required_construct='COMPREHENSION'),'HOLD')
 a('F03','AUDIO_FOR_READING_REJECT',dict(permission=True,rights='PUBLIC_AUTHORIZED',accessible=True,publication=False,modality='AUDIO',required_construct='READING'),'REJECT_CONSTRUCT_SUBSTITUTION')
 def ref(kind,owner,stable_id):
  return {'package_id':'learning-process','version':'0.1.0-process-candidate-3','kind':kind,'stable_id':stable_id,'owner':owner}
 construct_ref=ref('Goal','P03','P03.PRODUCTION.GOAL')
 scoring_ref=ref('ObservationSpec','P06','P06.ACT.OBSERVE.OBS')
 retest_ref=ref('ObservationSpec','F04','F04.OBS.RETEST')
 def seal_event(e):
  e['event_record_sha256']=dig(e);return e
 def response_event(event_id,event_type,variant,event_time,recorded_at,response,assistance='NONE'):
  return seal_event({'event_id':event_id,'event_type':event_type,'task_id':'TASK-01','task_version':'T1','variant_id':variant,'learner_id':'LEARNER-01','actor_id':'LEARNER-01','event_time':event_time,'recorded_at':recorded_at,'event_clock_domain':F04_CLOCK_CONTRACT['event_clock_domain'],'recording_clock_domain':F04_CLOCK_CONTRACT['recording_clock_domain'],'event_clock_id':F04_CLOCK_CONTRACT['event_clock_id'],'recording_clock_id':F04_CLOCK_CONTRACT['recording_clock_id'],'actor_role':'LEARNER','response':response,'generated_answer':False,'assistance_status':assistance,'construct_ref':construct_ref,'scoring_binding':{'observation_ref':scoring_ref,'scoring_version':'S1'}})
 def hint_event(event_id='H1',event_time=20,recorded_at=22):
  return seal_event({'event_id':event_id,'event_type':'HINT','task_id':'TASK-01','task_version':'T1','variant_id':'V1','learner_id':'LEARNER-01','actor_id':'SYSTEM-01','event_time':event_time,'recorded_at':recorded_at,'event_clock_domain':F04_CLOCK_CONTRACT['event_clock_domain'],'recording_clock_domain':F04_CLOCK_CONTRACT['recording_clock_domain'],'event_clock_id':F04_CLOCK_CONTRACT['event_clock_id'],'recording_clock_id':F04_CLOCK_CONTRACT['recording_clock_id'],'actor_role':'SYSTEM','assistance_status':'HINT'})
 def retest_event(variant='V2',event_id='RT1',event_time=40,recorded_at=42,assistance='NONE',task_version='T1',construct=construct_ref,scoring=scoring_ref,observation=retest_ref,generated=False):
  return seal_event({'event_id':event_id,'event_type':'INDEPENDENT_RETEST','task_id':'TASK-01','task_version':task_version,'variant_id':variant,'learner_id':'LEARNER-01','actor_id':'LEARNER-01','event_time':event_time,'recorded_at':recorded_at,'event_clock_domain':F04_CLOCK_CONTRACT['event_clock_domain'],'recording_clock_domain':F04_CLOCK_CONTRACT['recording_clock_domain'],'event_clock_id':F04_CLOCK_CONTRACT['event_clock_id'],'recording_clock_id':F04_CLOCK_CONTRACT['recording_clock_id'],'actor_role':'LEARNER','response':'B','generated_answer':generated,'assistance_status':assistance,'construct_ref':construct,'scoring_binding':{'observation_ref':scoring,'scoring_version':'S1'},'observation_ref':observation})
 base=dict(clock_contract=dict(F04_CLOCK_CONTRACT),role_authorized=True,learner_id='LEARNER-01',task_id='TASK-01',task_version='T1',expected_task_version='T1',scoring_version='S1',expected_scoring_version='S1',generated_answer=False,initial_response_event=response_event('R1','INITIAL_RESPONSE','V1',10,11,'A'),final_response_event=response_event('R2','FINAL_RESPONSE','V1',30,31,'A'),hint_events=[],retest_event=retest_event())
 a('F04','UNASSISTED_INDEPENDENT',base,'INDEPENDENT_RETEST_OBSERVATION')
 hint=hint_event()
 assisted=base|dict(hint_events=[hint],final_response_event=response_event('R2','FINAL_RESPONSE','V1',30,31,'A','ASSISTED'),retest_event=None)
 a('F04','HINTED_NOT_INDEPENDENT',assisted,'ASSISTED_NOT_INDEPENDENT')
 a('F04','IDENTICAL_DUPLICATE_HINT_IDEMPOTENT',assisted|dict(hint_events=[hint,hint]),'ASSISTED_NOT_INDEPENDENT')
 a('F04','EVENT_AND_STORAGE_TIMES_SEPARATE',base|dict(hint_events=[hint_event(event_time=25,recorded_at=12)],final_response_event=response_event('R2','FINAL_RESPONSE','V1',30,31,'A','ASSISTED'),retest_event=None),'ASSISTED_NOT_INDEPENDENT')
 a('F04','GENERATED_ANSWER_NOT_EVIDENCE',base|dict(generated_answer=True),'NOT_LEARNER_EVIDENCE')
 a('F04','MISSING_INITIAL_UNKNOWN',base|dict(initial_response_event=None),'UNKNOWN')
 a('F04','ROLE_DENIED_HOLD',base|dict(role_authorized=False),'HOLD')
 a('F04','VERSION_MISMATCH_HOLD',base|dict(scoring_version='S2'),'HOLD')
 a('F04','CONFLICTING_DUPLICATE_HINT_HOLD',assisted|dict(hint_events=[hint,hint_event(event_time=21)]),'HOLD')
 a('F04','GENERATED_ANSWER_UNKNOWN',base|dict(generated_answer=None),'UNKNOWN')
 a('F04','MISSING_RETEST_UNKNOWN',base|dict(retest_event=None),'UNKNOWN')
 a('F04','SAME_VARIANT_REPLAY_HOLD',base|dict(retest_event=retest_event(variant='V1')),'HOLD')
 a('F04','RETEST_VERSION_MISMATCH_HOLD',base|dict(retest_event=retest_event(task_version='T2')),'HOLD')
 a('F04','ASSISTED_RETEST_NOT_INDEPENDENT',base|dict(retest_event=retest_event(assistance='ASSISTED')),'ASSISTED_NOT_INDEPENDENT')
 a('F04','RETEST_CONSTRUCT_MISMATCH_HOLD',base|dict(retest_event=retest_event(construct=ref('Goal','P03','P03.EXPOSITION.GOAL'))),'HOLD')
 a('F04','RETEST_SCORING_BINDING_MISMATCH_HOLD',base|dict(retest_event=retest_event(scoring=ref('ObservationSpec','P06','P06.ACT.SCORE.OBS'))),'HOLD')
 bad_hash=retest_event();bad_hash['event_record_sha256']='0'*64
 a('F04','RETEST_EVENT_HASH_MISMATCH_HOLD',base|dict(retest_event=bad_hash),'HOLD')
 a('F04','HINTED_THEN_INDEPENDENT_RETEST',assisted|dict(retest_event=retest_event()),'INDEPENDENT_RETEST_OBSERVATION')
 empty_task=json.loads(json.dumps(base));empty_task.update(task_version='',expected_task_version='')
 for e in (empty_task['initial_response_event'],empty_task['final_response_event'],empty_task['retest_event']):
  e['task_version']='';seal_event(e)
 a('F04','EMPTY_TASK_VERSION_TOP_AND_EVENTS_HOLD',empty_task,'HOLD')
 empty_scoring=json.loads(json.dumps(base));empty_scoring.update(scoring_version='',expected_scoring_version='')
 for e in (empty_scoring['initial_response_event'],empty_scoring['final_response_event'],empty_scoring['retest_event']):
  e['scoring_binding']['scoring_version']='';seal_event(e)
 a('F04','EMPTY_SCORING_VERSION_TOP_AND_EVENTS_HOLD',empty_scoring,'HOLD')
 nested_task=base|dict(retest_event=retest_event(task_version=''))
 a('F04','EMPTY_RETEST_TASK_VERSION_HOLD',nested_task,'HOLD')
 nested_scoring=base|dict(retest_event=retest_event(scoring='BAD-SCORING-REF'))
 nested_scoring['retest_event']['scoring_binding']['scoring_version']='';seal_event(nested_scoring['retest_event'])
 a('F04','EMPTY_RETEST_SCORING_VERSION_HOLD',nested_scoring,'HOLD')
 bad_clock=base|dict(retest_event=retest_event())
 bad_clock['retest_event']['event_clock_domain']='LOCAL_UNKNOWN';seal_event(bad_clock['retest_event'])
 a('F04','UNKNOWN_CLOCK_DOMAIN_HOLD',bad_clock,'HOLD')
 bad_skew=base|dict(retest_event=retest_event(recorded_at=1000))
 a('F04','CLOCK_SKEW_EXCEEDED_HOLD',bad_skew,'HOLD')
 bad_record_order=base|dict(hint_events=[hint_event(event_time=20,recorded_at=10)],final_response_event=response_event('R2','FINAL_RESPONSE','V1',30,31,'A','ASSISTED'),retest_event=None)
 a('F04','RECORDED_AT_ORDER_INVALID_HOLD',bad_record_order,'HOLD')
 obs=dict(expected_scoring_version='S1',response=dict(status='OBSERVED',value='response',task_version='T1'),self_report=dict(status='MISSING'),score=dict(status='OBSERVED',value=0.75,scoring_version='S1',denominator=4),estimate=dict(status='NOT_RUN'))
 expected={'channels':{'response':{'status':'OBSERVED','value':'response','task_version':'T1'},'self_report':{'status':'UNKNOWN','reason':'MISSING'},'score':{'status':'SCORED','value':0.75,'scoring_version':'S1','denominator':4},'estimate':{'status':'NOT_ESTIMATED'}},'combined_mastery':'NOT_INFERRED'}
 a('F05','SEPARATE_CHANNELS',obs,expected)
 a('F05','MISSING_SELF_REPORT_UNKNOWN',obs|dict(self_report={'status':'NOT_ADMINISTERED'}),expected|{'channels':expected['channels']|{'self_report':{'status':'UNKNOWN','reason':'NOT_ADMINISTERED'}}})
 a('F05','MISSING_SCORE_UNKNOWN',obs|dict(score={'status':'MISSING'}),expected|{'channels':expected['channels']|{'score':{'status':'UNKNOWN','reason':'MISSING'}}})
 a('F05','UNPINNED_MODEL_HOLD',obs|dict(estimate={'status':'OBSERVED','model_id':'M1','model_version':'V1','model_pin_verified':False}),'HOLD')
 a('F05','SCORING_VERSION_MISMATCH_HOLD',obs|dict(score={'status':'OBSERVED','value':0.75,'scoring_version':'S2','denominator':4}),'HOLD')
 a('F05','EXPECTED_SCORING_VERSION_REBOUND_HOLD',obs|dict(expected_scoring_version='S2',score={'status':'OBSERVED','value':0.75,'scoring_version':'S2','denominator':4}),'HOLD')
 a('F05','SCORING_VERSION_EXPECTATION_MISSING_HOLD',obs|dict(expected_scoring_version=None),'HOLD')
 a('F05','SCORING_VERSION_EMPTY_HOLD',obs|dict(score={'status':'OBSERVED','value':0.75,'scoring_version':'','denominator':4}),'HOLD')
 for status in ('MISSING','INVALID','NOT_ADMINISTERED'):
  a('F05','RESPONSE_'+status+'_UNKNOWN',obs|dict(response={'status':status}),expected|{'channels':expected['channels']|{'response':{'status':'UNKNOWN','reason':status}}})
 a('F05','MODEL_OUTPUT_UNBOUND_HOLD',obs|dict(estimate={'status':'OBSERVED','model_id':'M1','model_version':'V1','model_pin_verified':True}),'HOLD')

 def seal(obj,key):
  obj[key]=_sealed_digest(obj,key);return obj
 def f07_base(role='LEARNER',now=100):
  actor='LEARNER-01' if role=='LEARNER' else 'FACILITATOR-01'
  learner='LEARNER-01';session='SESSION-01'
  req=seal({'event_id':'SUPPORT-REQ-01','learner_id':learner,'session_id':session,'selected_option_id':'OPTION-01','selected_by':'LEARNER','task_id':'TASK-01','task_version':'T1','event_time':90,'recorded_at':91},'event_sha256')
  authority={'authority_id':'AUTH-01','authority_version':'V1','actor_id':actor,'learner_id':learner,'role':role,'purpose':'OFFER_LEARNER_SUPPORT','scope':'LEARNER_SUPPORT_ADVICE_ONLY','session_id':session,'authority_kind':'LEARNER_SESSION_SELF' if role=='LEARNER' else 'ASSIGNED_FACILITATOR','grantor_id':learner if role=='LEARNER' else 'ORG-01','resolver_status':'UNBOUND','resolver_id':'NONE_BOUND','not_before':80,'issued_at':80,'expires_at':120,'permission':True,'assignment_id':None if role=='LEARNER' else 'ASSIGN-01','assigned_learner_id':learner}
  seal(authority,'evidence_sha256')
  env=seal({'profile_id':'ENV-SHARED-01','profile_version':'V1','task_id':'TASK-01','task_version':'T1','accessible':True,'capability_match':True,'tested_at':85,'valid_until':200},'profile_sha256')
  return dict(identity_verified=True,role=role,actor_id=actor,learner_id=learner,session_id=session,task_id='TASK-01',task_version='T1',now=now,exit=False,support_request=req,role_authority=authority,environment_profile=env)
 fbase=f07_base()
 a('F07','LEARNER_SELF_SESSION_RESOLVER_UNBOUND_HOLD',fbase,'HOLD')
 denied=f07_base();denied['role_authority']['permission']=False;seal(denied['role_authority'],'evidence_sha256')
 a('F07','ROLE_PERMISSION_DENIED',denied,'REFUSE')
 a('F07','IDENTITY_UNKNOWN_CLARIFY',fbase|dict(identity_verified=None),'CLARIFY')
 env_unavailable=f07_base();env_unavailable['environment_profile']['accessible']=False;seal(env_unavailable['environment_profile'],'profile_sha256')
 a('F07','ACCESS_UNAVAILABLE_DEFER',env_unavailable,'DEFER')
 a('F07','USER_EXIT_STOP',fbase|dict(exit=True),'STOP')
 no_selection=f07_base();no_selection['support_request']['selected_by']='FACILITATOR';seal(no_selection['support_request'],'event_sha256')
 a('F07','NO_LEARNER_SELECTION_CLARIFY',no_selection,'CLARIFY')
 a('F07','REVIEWER_READ_ONLY_REFUSE',f07_base('REVIEWER'),'REFUSE')
 a('F07','EXIT_UNKNOWN_CLARIFY',fbase|dict(exit=None),'CLARIFY')
 facilitator=f07_base('FACILITATOR')
 a('F07','FACILITATOR_ASSIGNED_SCOPE_OPTION',facilitator,'HOLD')
 bad_scope=f07_base('FACILITATOR');bad_scope['role_authority']['scope']='GENERAL_ADMIN';seal(bad_scope['role_authority'],'evidence_sha256')
 a('F07','FACILITATOR_SCOPE_MISMATCH_REFUSE',bad_scope,'REFUSE')
 expired=f07_base('FACILITATOR');expired['role_authority']['expires_at']=99;seal(expired['role_authority'],'evidence_sha256')
 a('F07','EXPIRED_FACILITATOR_AUTHORITY_REFUSE',expired,'REFUSE')
 bad_hash=f07_base();bad_hash['role_authority']['evidence_sha256']='0'*64
 a('F07','AUTHORITY_HASH_MISMATCH_HOLD',bad_hash,'HOLD')
 wrong_session=f07_base();wrong_session['role_authority']['session_id']='OTHER-SESSION';seal(wrong_session['role_authority'],'evidence_sha256')
 a('F07','SESSION_MISMATCH_HOLD',wrong_session,'HOLD')
 a('F07','GENERIC_PERMISSION_BOOLEAN_NOT_AUTHORITY_CLARIFY',dict(identity_verified=True,role='LEARNER',permission=True,accessible=True,capability_match=True,learner_selected=True,exit=False),'CLARIFY')
 bad_env_hash=f07_base();bad_env_hash['environment_profile']['profile_sha256']='0'*64
 a('F07','ENVIRONMENT_PROFILE_HASH_TAMPER_HOLD',bad_env_hash,'HOLD')
 stale_env=f07_base();stale_env['environment_profile']['tested_at']=1;seal(stale_env['environment_profile'],'profile_sha256')
 a('F07','STALE_ENVIRONMENT_PROFILE_HOLD',stale_env,'HOLD')
 wrong_env_task=f07_base();wrong_env_task['environment_profile']['task_version']='T2';seal(wrong_env_task['environment_profile'],'profile_sha256')
 a('F07','ENVIRONMENT_TASK_VERSION_MISMATCH_HOLD',wrong_env_task,'HOLD')
 def clone(x):return json.loads(json.dumps(x))
 def construct_review(relation='PRESERVED',task_id='TASK-01',task_version='T1',assessment_id='ASSESSMENT-01',assessment_version='A1'):
  obj={'review_id':'TASK-CONSTRUCT-REVIEW-01','review_version':'V1','task_id':task_id,'task_version':task_version,'assessment_id':assessment_id,'assessment_version':assessment_version,'construct_id':'CONSTRUCT-01','relation':relation,'review_result':'PASS','reviewed_at':80,'valid_until':1000,'source_status':'PROJECT_AUTHORED_SYNTHETIC_CANDIDATE'}
  obj['review_sha256']=dig(obj);return obj
 a07_f07=f07_base()
 base=dict(exit=False,actor_role='LEARNER',task_id='TASK-01',task_version='T1',assessment_id='ASSESSMENT-01',assessment_version='A1',f07_input=a07_f07,assessment=True,construct_review=construct_review(),estimate_status='NOT_ESTIMATED',self_report={'status':'MISSING'},response={'status':'MISSING'},score={'status':'MISSING'})
 def dec(action,scope='NONE',assessment='UNKNOWN',basis='NO_AUTOMATIC_INFERENCE'):
  return {'action':action,'support_scope':scope,'assessment_disposition':assessment,'evidence_basis':basis,'effect':'ADVICE_ONLY'}
 a('A07','PRESERVED_CONSTRUCT_OPTIONAL_SUPPORT',base,dec('REQUEST_OBSERVATION',basis='F07_TRUSTED_AUTHORITY_RESOLVER_UNBOUND'))
 changed_review=construct_review('CHANGED')
 a('A07','CHANGED_CONSTRUCT_ASSESSMENT_DEFER',base|dict(construct_review=changed_review),dec('REQUEST_OBSERVATION',basis='F07_TRUSTED_AUTHORITY_RESOLVER_UNBOUND'))
 a('A07','CHANGED_CONSTRUCT_PRACTICE_ONLY',base|dict(assessment=False,construct_review=changed_review),dec('REQUEST_OBSERVATION',basis='F07_TRUSTED_AUTHORITY_RESOLVER_UNBOUND'))
 a('A07','MISSING_SELF_REPORT_EXPLICIT_REQUEST_OK',base|dict(self_report={'status':'NOT_ADMINISTERED'}),dec('REQUEST_OBSERVATION',basis='F07_TRUSTED_AUTHORITY_RESOLVER_UNBOUND'))
 a('A07','MISSING_SELF_REPORT_NO_REQUEST_CLARIFY',base|dict(f07_input=(lambda z:(z['support_request'].__setitem__('selected_by','UNKNOWN'),seal(z['support_request'],'event_sha256'),z)[2])(clone(a07_f07))),dec('CLARIFY',basis='F07_EVIDENCE_INCOMPLETE'))
 a('A07','AGE_LABEL_INVARIANCE',base|dict(age_band='OLDER_ADULT',developmental_label='UNVERIFIED'),dec('REQUEST_OBSERVATION',basis='F07_TRUSTED_AUTHORITY_RESOLVER_UNBOUND'))
 a('A07','DIAGNOSIS_LABEL_INVARIANCE',base|dict(diagnosis='UNVERIFIED_DIAGNOSIS',group_label='UNVERIFIED'),dec('REQUEST_OBSERVATION',basis='F07_TRUSTED_AUTHORITY_RESOLVER_UNBOUND'))
 a('A07','UNBOUND_ESTIMATE_HOLD',base|dict(estimate_status='OBSERVED_UNBOUND'),dec('CLARIFY',basis='UNBOUND_ESTIMATE_NOT_USED'))
 a('A07','MISSING_RESPONSE_NO_DEFICIT_INFERENCE',base|dict(response={'status':'MISSING'}),dec('REQUEST_OBSERVATION',basis='F07_TRUSTED_AUTHORITY_RESOLVER_UNBOUND'))
 a('A07','IDENTITY_UNKNOWN_CLARIFY',base|dict(f07_input=(lambda z:(z.__setitem__('identity_verified',None),z)[1])(clone(a07_f07))),dec('CLARIFY',basis='F07_EVIDENCE_INCOMPLETE'))
 facilitator_input=clone(a07_f07);facilitator_input['role']='FACILITATOR';facilitator_input['actor_id']='FACILITATOR-01';facilitator_input['role_authority']['role']='FACILITATOR';facilitator_input['role_authority']['actor_id']='FACILITATOR-01';facilitator_input['role_authority']['authority_kind']='ASSIGNED_FACILITATOR';facilitator_input['role_authority']['grantor_id']='ORG-01';facilitator_input['role_authority']['assignment_id']='ASSIGN-01';facilitator_input['role_authority']['assigned_learner_id']='LEARNER-01';seal(facilitator_input['role_authority'],'evidence_sha256');facilitator_input['support_request']['selected_by']='FACILITATOR';seal(facilitator_input['support_request'],'event_sha256')
 a('A07','FACILITATOR_CANNOT_SELECT',base|dict(actor_role='FACILITATOR',f07_input=facilitator_input),dec('CLARIFY',basis='F07_EVIDENCE_INCOMPLETE'))
 reviewer_input=clone(a07_f07);reviewer_input['role']='REVIEWER'
 a('A07','REVIEWER_READ_ONLY',base|dict(actor_role='REVIEWER',f07_input=reviewer_input),dec('REFUSE',basis='REVIEW_ONLY_ROLE'))
 denied_input=clone(a07_f07);denied_input['role_authority']['permission']=False;seal(denied_input['role_authority'],'evidence_sha256')
 a('A07','PERMISSION_DENIED_REFUSE',base|dict(f07_input=denied_input),dec('REFUSE',basis='F07_AUTHORITY_REFUSED'))
 unavailable_input=clone(a07_f07);unavailable_input['environment_profile']['accessible']=False;seal(unavailable_input['environment_profile'],'profile_sha256')
 a('A07','ACCESS_UNAVAILABLE_DEFER',base|dict(f07_input=unavailable_input),dec('DEFER',basis='ENVIRONMENT_OR_CAPABILITY_BLOCK'))
 unknown_access=clone(a07_f07);unknown_access['environment_profile']['accessible']=None;seal(unknown_access['environment_profile'],'profile_sha256')
 a('A07','ACCESS_UNKNOWN_CLARIFY',base|dict(f07_input=unknown_access),dec('CLARIFY',basis='F07_EVIDENCE_INCOMPLETE'))
 no_selection=clone(a07_f07);no_selection['support_request']['selected_by']='UNKNOWN';seal(no_selection['support_request'],'event_sha256')
 a('A07','NO_LEARNER_SELECTION_CLARIFY',base|dict(f07_input=no_selection),dec('CLARIFY',basis='F07_EVIDENCE_INCOMPLETE'))
 a('A07','USER_EXIT_STOP',base|dict(exit=True),dec('STOP',basis='LEARNER_EXIT'))
 a('A07','EXIT_MISSING_CLARIFY',{k:v for k,v in base.items() if k!='exit'},dec('CLARIFY',basis='EXIT_STATE_UNKNOWN'))
 a('A07','EXIT_NULL_CLARIFY',base|dict(exit=None),dec('CLARIFY',basis='EXIT_STATE_UNKNOWN'))
 unknown_review=construct_review('UNKNOWN')
 a('A07','CONSTRUCT_REVIEW_UNKNOWN_HOLD',base|dict(construct_review=unknown_review),dec('REQUEST_OBSERVATION',basis='CONSTRUCT_RELATION_UNKNOWN'))
 a('A07','CONSTRUCT_REVIEW_UNVERIFIED_HOLD',base|dict(construct_review=None),dec('REQUEST_OBSERVATION',basis='TASK_LEVEL_CONSTRUCT_REVIEW_REQUIRED'))
 bad_review=construct_review();bad_review['review_sha256']='0'*64
 a('A07','CONSTRUCT_REVIEW_MISSING_HASH_HOLD',base|dict(construct_review=bad_review),dec('REQUEST_OBSERVATION',basis='CONSTRUCT_REVIEW_DIGEST_INVALID'))
 wrong_review_task=construct_review(task_version='T2')
 a('A07','CONSTRUCT_REVIEW_TASK_VERSION_MISMATCH_HOLD',base|dict(construct_review=wrong_review_task),dec('REQUEST_OBSERVATION',basis='CONSTRUCT_REVIEW_IDENTITY_MISMATCH'))
 a('A07','SELF_REPORT_WRONG_RESPONDENT_HOLD',base|dict(self_report={'status':'OBSERVED','respondent':'FACILITATOR','value':'needs support'}),dec('CLARIFY',basis='SELF_REPORT_NOT_LEARNER_AUTHORED'))
 a('A07','SCORE_VALUE_INVARIANCE',base|dict(score={'status':'OBSERVED','value':0,'scoring_version':'S1'}),dec('REQUEST_OBSERVATION',basis='F07_TRUSTED_AUTHORITY_RESOLVER_UNBOUND'))
 a('A07','INVALID_ASSESSMENT_FLAG_HOLD',base|dict(assessment='yes'),dec('CLARIFY',basis='ASSESSMENT_SCOPE_UNKNOWN'))
 a('A07','ENVIRONMENT_PROFILE_UNVERIFIED',base|dict(f07_input=(lambda z:(z.__setitem__('environment_profile',None),z)[1])(clone(a07_f07))),dec('CLARIFY',basis='F07_EVIDENCE_INCOMPLETE'))
 bad_profile=clone(a07_f07);bad_profile['environment_profile']['profile_sha256']='bad'
 a('A07','ENVIRONMENT_PROFILE_MISSING_HASH',base|dict(f07_input=bad_profile),dec('REQUEST_OBSERVATION',basis='F07_TRUSTED_AUTHORITY_RESOLVER_UNBOUND'))
 bad_request=clone(a07_f07);bad_request['support_request']['event_sha256']='0'*64
 a('A07','SUPPORT_REQUEST_UNVERIFIED',base|dict(f07_input=bad_request),dec('REQUEST_OBSERVATION',basis='F07_TRUSTED_AUTHORITY_RESOLVER_UNBOUND'))
 a('A07','F07_INPUT_MISSING_REQUEST_OBSERVATION',base|dict(f07_input=None),dec('REQUEST_OBSERVATION',basis='F07_TYPED_EVIDENCE_REQUIRED'))
 bad_task_env=clone(a07_f07);bad_task_env['environment_profile']['task_version']='T2';seal(bad_task_env['environment_profile'],'profile_sha256')
 a('A07','ENVIRONMENT_TASK_VERSION_MISMATCH_HOLD',base|dict(f07_input=bad_task_env),dec('REQUEST_OBSERVATION',basis='F07_TRUSTED_AUTHORITY_RESOLVER_UNBOUND'))
 stale_env=clone(a07_f07);stale_env['environment_profile']['tested_at']=1;seal(stale_env['environment_profile'],'profile_sha256')
 a('A07','STALE_ENVIRONMENT_PROFILE_HOLD',base|dict(f07_input=stale_env),dec('REQUEST_OBSERVATION',basis='F07_TRUSTED_AUTHORITY_RESOLVER_UNBOUND'))
 plan_path=Path(__file__).with_name('analysis-plan.json')
 plan=json.loads(plan_path.read_text(encoding='utf-8'))
 plan_hash=hashlib.sha256(plan_path.read_bytes()).hexdigest()
 base=dict(evaluation_time=100,direct_knowledge_write=False,analysis_plan_ref='docs/implementation/f-composition-preparation/analysis-plan.json',analysis_plan_sha256=plan_hash,analysis_plan_version=plan['version'],analysis_plan_summary=plan['analysis_plan_summary'],protocol_id='E01.PROTOCOL',protocol_version='V2',population_id=plan['population']['population_id'],assignment_unit=plan['allocation']['unit'],assignment_method=plan['allocation']['method'],intervention_version=plan['intervention']['version'],comparator_version=plan['comparator']['version'],primary_outcome_id=plan['primary_outcome']['id'],followup_days=plan['followup']['days'],assignment_verified=True,data_kind='OBSERVED')
 a('E01','PINNED_PROTOCOL_AWAITING_APPROVAL_AND_REVIEW_HOLD',base,'HOLD')
 a('E01','APPROVAL_MISSING_HOLD',base|dict(approval_evidence_ref=None),'HOLD')
 a('E01','COMPARATOR_MISSING_HOLD',base|dict(comparator_version='UNKNOWN'),'HOLD')
 a('E01','SIMULATION_NOT_EFFECT',base|dict(data_kind='SIMULATED'),'SIMULATION_ONLY_NOT_EFFECT')
 a('E01','ASSIGNMENT_UNVERIFIED_DESCRIPTIVE_ONLY',base|dict(assignment_unit='LEARNER',assignment_method='RANDOMIZED',assignment_verified=False),'DESCRIPTIVE_ONLY_NO_CAUSAL_ESTIMATE')
 a('E01','DIRECT_KNOWLEDGE_WRITE_REFUSE',base|dict(direct_knowledge_write=True),'REFUSE')
 a('E01','DIRECT_KNOWLEDGE_WRITE_UNKNOWN_HOLD',base|dict(direct_knowledge_write=None),'HOLD')
 a('E01','FOLLOWUP_MISSING_HOLD',base|dict(followup_days=None),'HOLD')
 a('E01','IDENTICAL_POLICY_VERSIONS_HOLD',base|dict(intervention_version='CURRENT_V1'),'HOLD')
 a('E01','INVALID_ANALYSIS_PLAN_HOLD',base|dict(analysis_plan_sha256='not-a-sha256'),'HOLD')
 a('E01','POLICY_VERSION_MISMATCH_HOLD',base|dict(intervention_version='CANDIDATE_V0'),'HOLD')
 a('E01','ASSIGNMENT_UNIT_METHOD_MISMATCH_HOLD',base|dict(assignment_unit='LEARNER',assignment_method='CLUSTER_RANDOMIZED'),'HOLD')
 a('E01','LEGACY_BOOLEAN_APPROVAL_NOT_EVIDENCE_HOLD',base|dict(approved=True,protocol_frozen=True,independent_review=True),'HOLD')
 typed={'kind':'RESEARCH_PROTOCOL_APPROVAL','subject_id':'E01.PROTOCOL','subject_version':'V2','analysis_plan_sha256':plan_hash,'decision':'APPROVED','repository':'kaicreator-mm/learn-kg','issue_number':999,'comment_id':999,'artifact_path':'evidence/e01/approval.json','artifact_sha256':'a'*64,'authority_id':'AUTHORITY-PLACEHOLDER','issued_at':1,'expires_at':9999999999}
 review={'kind':'INDEPENDENT_NON_WRITER_REVIEW','subject_id':'E01.PROTOCOL','subject_version':'V2','analysis_plan_sha256':plan_hash,'decision':'ACCEPT_SCOPED','repository':'kaicreator-mm/learn-kg','issue_number':999,'comment_id':998,'artifact_path':'evidence/e01/review.json','artifact_sha256':'b'*64,'authority_id':'REVIEWER-PLACEHOLDER','issued_at':1,'expires_at':9999999999}
 a('E01','UNRESOLVED_TYPED_APPROVAL_AND_REVIEW_HOLD',base|dict(approval_evidence_ref=typed,independent_review_evidence_ref=review),'HOLD')
 duplicate_review=dict(review);duplicate_review.update(comment_id=typed['comment_id'],artifact_path=typed['artifact_path'],artifact_sha256=typed['artifact_sha256'],authority_id=typed['authority_id'])
 a('E01','DUPLICATE_APPROVAL_REVIEW_IDENTITY_HOLD',base|dict(approval_evidence_ref=typed,independent_review_evidence_ref=duplicate_review),'HOLD')
 expired_review=dict(review);expired_review['expires_at']=99
 a('E01','EXPIRED_APPROVAL_REVIEW_HOLD',base|dict(approval_evidence_ref=typed,independent_review_evidence_ref=expired_review),'HOLD')
 traversal_review=dict(review);traversal_review['artifact_path']='../../outside.json'
 a('E01','EVIDENCE_PATH_TRAVERSAL_HOLD',base|dict(approval_evidence_ref=typed,independent_review_evidence_ref=traversal_review),'HOLD')
 hash_review=dict(review);hash_review['artifact_path']='docs/implementation/f-composition-preparation/analysis-plan.json';hash_review['artifact_sha256']='0'*64
 a('E01','EVIDENCE_ARTIFACT_HASH_MISMATCH_HOLD',base|dict(approval_evidence_ref=typed,independent_review_evidence_ref=hash_review),'HOLD')
 a('E01','ANALYSIS_PLAN_REF_MISMATCH_HOLD',base|dict(analysis_plan_ref='docs/other-plan.json'),'HOLD')
 a('E01','ANALYSIS_PLAN_SUMMARY_MISMATCH_HOLD',base|dict(analysis_plan_summary='not the pinned summary'),'HOLD')
 return out
