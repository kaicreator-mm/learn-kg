"""Bounded synthetic decisions for F03/F04/F05/F07/E01. No external effects."""
import json,hashlib
def dig(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def f03(x):
 if not isinstance(x,dict):return 'HOLD'
 if x.get('permission') is not True or x.get('rights') not in ('PRIVATE_ONLY','PUBLIC_AUTHORIZED'):return 'HOLD'
 if x.get('accessible') is not True:return 'HOLD'
 if x.get('publication') is True and x['rights']!='PUBLIC_AUTHORIZED':return 'REFUSE_PUBLICATION'
 if x.get('required_construct')=='LISTENING' and x.get('modality')!='AUDIO':return 'REJECT_CONSTRUCT_SUBSTITUTION'
 if x.get('required_construct')=='READING' and x.get('modality')!='TEXT':return 'REJECT_CONSTRUCT_SUBSTITUTION'
 return 'PRIVATE_RESOURCE_CANDIDATE' if x['rights']=='PRIVATE_ONLY' else 'PUBLIC_RESOURCE_CANDIDATE_WITH_SEPARATE_RIGHTS_CHECK'
def f04(x):
 if not isinstance(x,dict) or x.get('role_authorized') is not True:return 'HOLD'
 if x.get('task_version')!=x.get('expected_task_version') or x.get('scoring_version')!=x.get('expected_scoring_version'):return 'HOLD'
 events=x.get('hint_events')
 if not isinstance(events,list):return 'HOLD'
 seen={}
 for e in events:
  if not isinstance(e,dict) or not isinstance(e.get('id'),str) or not e['id'] or e.get('task_version')!=x['task_version'] or e.get('type')!='HINT':return 'HOLD'
  if type(e.get('event_time')) is not int or type(e.get('recorded_at')) is not int or e['event_time']<0 or e['recorded_at']<0:return 'HOLD'
  h=dig(e)
  if e['id'] in seen and seen[e['id']]!=h:return 'HOLD'
  seen[e['id']]=h
 if x.get('generated_answer') is True:return 'NOT_LEARNER_EVIDENCE'
 if not isinstance(x.get('initial_response'),str) or not x['initial_response'] or not isinstance(x.get('final_response'),str) or not x['final_response']:return 'UNKNOWN'
 if seen:return 'ASSISTED_NOT_INDEPENDENT'
 if x.get('independent_retest') is not True:return 'OBSERVED_NOT_INDEPENDENT'
 return 'INDEPENDENT_OBSERVATION'

def f05(x):
 if not isinstance(x,dict):return 'HOLD'
 out={}
 for name in ('response','self_report','score','estimate'):
  z=x.get(name)
  if not isinstance(z,dict):return 'HOLD'
  status=z.get('status')
  if status in ('MISSING','INVALID','NOT_ADMINISTERED'):out[name]={'status':'UNKNOWN','reason':status};continue
  if name=='response':
   if status!='OBSERVED' or not isinstance(z.get('value'),str) or not z['value'] or not z.get('task_version'):return 'HOLD'
   out[name]={'status':'OBSERVED','value':z['value'],'task_version':z['task_version']}
  elif name=='self_report':
   if status!='OBSERVED' or not isinstance(z.get('value'),str) or not z['value'] or z.get('respondent')!='LEARNER':return 'HOLD'
   out[name]={'status':'SELF_REPORTED','value':z['value']}
  elif name=='score':
   if status!='OBSERVED' or type(z.get('value')) not in (int,float) or not z.get('scoring_version') or type(z.get('denominator')) is not int or z['denominator']<=0:return 'HOLD'
   out[name]={'status':'SCORED','value':z['value'],'scoring_version':z['scoring_version'],'denominator':z['denominator']}
  else:
   if status=='NOT_RUN':out[name]={'status':'NOT_ESTIMATED'};continue
   return 'HOLD'
 return {'channels':out,'combined_mastery':'NOT_INFERRED'}
def f07(x):
 if not isinstance(x,dict):return 'HOLD'
 if x.get('exit') is True:return 'STOP'
 if x.get('identity_verified') is not True or x.get('role') not in ('LEARNER','FACILITATOR','REVIEWER'):return 'CLARIFY'
 if type(x.get('permission')) is not bool:return 'CLARIFY'
 if x['permission'] is False:return 'REFUSE'
 if type(x.get('accessible')) is not bool:return 'CLARIFY'
 if x['accessible'] is False:return 'DEFER'
 if type(x.get('capability_match')) is not bool:return 'CLARIFY'
 if x['capability_match'] is False:return 'DEFER'
 if x.get('learner_selected') is not True:return 'CLARIFY'
 return 'SUGGEST_ONLY_NO_EXECUTION'
def e01(x):
 if not isinstance(x,dict):return 'HOLD'
 if x.get('direct_knowledge_write') is True:return 'REFUSE'
 required=('approved','protocol_frozen','population_defined','outcome_defined','comparator_pinned','followup_complete','independent_review')
 if any(x.get(k) is not True for k in required):return 'HOLD'
 for k in ('protocol_id','protocol_version','assignment_unit','assignment_method','intervention_version','comparator_version','current_policy_version','candidate_policy_version','primary_outcome_id','analysis_plan_sha256'):
  if not isinstance(x.get(k),str) or not x[k]:return 'HOLD'
 if x['protocol_id']!='E01.PROTOCOL' or x['protocol_version']!='V1' or x['primary_outcome_id']!='E01.OBS.PRIMARY_OUTCOME' or x['current_policy_version']!='CURRENT_V1' or x['candidate_policy_version']!='CANDIDATE_V1':return 'HOLD'
 if x['intervention_version']!=x['candidate_policy_version'] or x['comparator_version']!=x['current_policy_version'] or x['intervention_version']==x['comparator_version'] or type(x.get('followup_days')) is not int or x['followup_days']!=28:return 'HOLD'
 if x.get('assignment_unit') not in ('LEARNER','CLASSROOM'):return 'HOLD'
 h=x['analysis_plan_sha256']
 if len(h)!=64 or any(c not in '0123456789abcdef' for c in h):return 'HOLD'
 if x.get('data_kind')=='SIMULATED':return 'SIMULATION_ONLY_NOT_EFFECT'
 if x.get('assignment_method') not in ('RANDOMIZED','CLUSTER_RANDOMIZED') or x.get('assignment_verified') is not True:return 'DESCRIPTIVE_ONLY_NO_CAUSAL_ESTIMATE'
 if x.get('data_kind')!='OBSERVED':return 'HOLD'
 return 'CANDIDATE_ANALYSIS_ONLY_NO_RELEASE'


def a07(x):
 def d(action,scope='NONE',assessment='UNKNOWN',basis='NO_AUTOMATIC_INFERENCE'):
  return {'action':action,'support_scope':scope,'assessment_disposition':assessment,'evidence_basis':basis,'effect':'ADVICE_ONLY'}
 if not isinstance(x,dict):return d('CLARIFY',basis='INVALID_INPUT')
 if x.get('exit') is True:return d('STOP',basis='LEARNER_EXIT')
 if x.get('identity_verified') is not True:return d('CLARIFY',basis='IDENTITY_NOT_VERIFIED')
 role=x.get('actor_role')
 if role=='REVIEWER':return d('REFUSE',basis='REVIEW_ONLY_ROLE')
 if role=='FACILITATOR':return d('CLARIFY',basis='LEARNER_SELECTION_REQUIRED')
 if role!='LEARNER':return d('CLARIFY',basis='ROLE_UNKNOWN')
 if type(x.get('permission')) is not bool:return d('CLARIFY',basis='PERMISSION_UNKNOWN')
 if x['permission'] is False:return d('REFUSE',basis='PERMISSION_DENIED')
 if x.get('support_requested_by')!='LEARNER' or x.get('learner_selected') is not True:return d('CLARIFY',basis='EXPLICIT_LEARNER_SELECTION_REQUIRED')
 if x.get('support_request_verified') is not True or not isinstance(x.get('support_request_id'),str) or not x['support_request_id']:return d('CLARIFY',basis='REQUEST_ID_NOT_VERIFIED')
 if x.get('environment_profile_verified') is not True:return d('REQUEST_OBSERVATION',basis='ENVIRONMENT_PROFILE_NOT_VERIFIED')
 for field in ('environment_profile_id','environment_profile_version'):
  if not isinstance(x.get(field),str) or not x[field]:return d('REQUEST_OBSERVATION',basis='ENVIRONMENT_PROFILE_PIN_REQUIRED')
 eh=x.get('environment_profile_sha256')
 if not isinstance(eh,str) or len(eh)!=64 or any(c not in '0123456789abcdef' for c in eh):return d('REQUEST_OBSERVATION',basis='ENVIRONMENT_PROFILE_HASH_REQUIRED')
 if type(x.get('accessible')) is not bool or type(x.get('capability_match')) is not bool:return d('CLARIFY',basis='ACCESSIBILITY_UNKNOWN')
 if x['accessible'] is False or x['capability_match'] is False:return d('DEFER',basis='ENVIRONMENT_OR_CAPABILITY_BLOCK')
 if x.get('estimate_status')!='NOT_ESTIMATED':return d('CLARIFY',basis='UNBOUND_ESTIMATE_NOT_USED')
 sr=x.get('self_report',{'status':'MISSING'})
 if not isinstance(sr,dict) or sr.get('status') not in ('MISSING','NOT_ADMINISTERED','OBSERVED'):return d('CLARIFY',basis='SELF_REPORT_INVALID')
 if sr.get('status')=='OBSERVED' and (sr.get('respondent')!='LEARNER' or not isinstance(sr.get('value'),str) or not sr['value']):return d('CLARIFY',basis='SELF_REPORT_NOT_LEARNER_AUTHORED')
 for field in ('response','score'):
  z=x.get(field,{'status':'MISSING'})
  if not isinstance(z,dict) or z.get('status') not in ('MISSING','NOT_ADMINISTERED','INVALID','OBSERVED'):return d('CLARIFY',basis='OBSERVATION_STATUS_INVALID')
 if type(x.get('assessment')) is not bool:return d('CLARIFY',basis='ASSESSMENT_SCOPE_UNKNOWN')
 if x.get('construct_review_verified') is not True:return d('REQUEST_OBSERVATION',basis='TASK_LEVEL_CONSTRUCT_REVIEW_REQUIRED')
 if not isinstance(x.get('construct_review_id'),str) or not x['construct_review_id'] or not isinstance(x.get('construct_review_version'),str) or not x['construct_review_version']:return d('REQUEST_OBSERVATION',basis='CONSTRUCT_REVIEW_PIN_REQUIRED')
 h=x.get('construct_review_sha256')
 if not isinstance(h,str) or len(h)!=64 or any(c not in '0123456789abcdef' for c in h):return d('REQUEST_OBSERVATION',basis='CONSTRUCT_REVIEW_HASH_REQUIRED')
 relation=x.get('construct_relation')
 if relation not in ('PRESERVED','CHANGED'):return d('REQUEST_OBSERVATION',basis='CONSTRUCT_RELATION_UNKNOWN')
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
 base=dict(role_authorized=True,task_version='T1',expected_task_version='T1',scoring_version='S1',expected_scoring_version='S1',hint_events=[],initial_response='A',final_response='A',generated_answer=False,independent_retest=True)
 hint=[dict(id='H1',task_version='T1',type='HINT',event_time=10,recorded_at=25)]
 a('F04','UNASSISTED_INDEPENDENT',base,'INDEPENDENT_OBSERVATION')
 a('F04','HINTED_NOT_INDEPENDENT',base|dict(hint_events=hint,independent_retest=False),'ASSISTED_NOT_INDEPENDENT')
 a('F04','IDENTICAL_DUPLICATE_HINT_IDEMPOTENT',base|dict(hint_events=hint+[hint[0]]),'ASSISTED_NOT_INDEPENDENT')
 a('F04','EVENT_AND_STORAGE_TIMES_SEPARATE',base|dict(hint_events=[hint[0]|dict(event_time=100,recorded_at=20)]),'ASSISTED_NOT_INDEPENDENT')
 a('F04','GENERATED_ANSWER_NOT_EVIDENCE',base|dict(generated_answer=True),'NOT_LEARNER_EVIDENCE')
 a('F04','MISSING_INITIAL_UNKNOWN',base|dict(initial_response=None),'UNKNOWN')
 a('F04','ROLE_DENIED_HOLD',base|dict(role_authorized=False),'HOLD')
 a('F04','VERSION_MISMATCH_HOLD',base|dict(scoring_version='S2'),'HOLD')
 a('F04','CONFLICTING_DUPLICATE_HINT_HOLD',base|dict(hint_events=hint+[hint[0]|dict(event_time=11)]),'HOLD')
 obs=dict(response=dict(status='OBSERVED',value='response',task_version='T1'),self_report=dict(status='MISSING'),score=dict(status='OBSERVED',value=0.75,scoring_version='S1',denominator=4),estimate=dict(status='NOT_RUN'))
 expected={'channels':{'response':{'status':'OBSERVED','value':'response','task_version':'T1'},'self_report':{'status':'UNKNOWN','reason':'MISSING'},'score':{'status':'SCORED','value':0.75,'scoring_version':'S1','denominator':4},'estimate':{'status':'NOT_ESTIMATED'}},'combined_mastery':'NOT_INFERRED'}
 a('F05','SEPARATE_CHANNELS',obs,expected)
 a('F05','MISSING_SELF_REPORT_UNKNOWN',obs|dict(self_report={'status':'NOT_ADMINISTERED'}),expected|{'channels':expected['channels']|{'self_report':{'status':'UNKNOWN','reason':'NOT_ADMINISTERED'}}})
 a('F05','MISSING_SCORE_UNKNOWN',obs|dict(score={'status':'MISSING'}),expected|{'channels':expected['channels']|{'score':{'status':'UNKNOWN','reason':'MISSING'}}})
 a('F05','UNPINNED_MODEL_HOLD',obs|dict(estimate={'status':'OBSERVED','model_id':'M1','model_version':'V1','model_pin_verified':False}),'HOLD')
 a('F05','SCORING_VERSION_MISMATCH_HOLD',obs|dict(score={'status':'OBSERVED','value':0.75,'scoring_version':None,'denominator':4}),'HOLD')
 for status in ('MISSING','INVALID','NOT_ADMINISTERED'):
  a('F05','RESPONSE_'+status+'_UNKNOWN',obs|dict(response={'status':status}),expected|{'channels':expected['channels']|{'response':{'status':'UNKNOWN','reason':status}}})
 a('F05','MODEL_OUTPUT_UNBOUND_HOLD',obs|dict(estimate={'status':'OBSERVED','model_id':'M1','model_version':'V1','model_pin_verified':True}),'HOLD')
 base=dict(identity_verified=True,role='LEARNER',permission=True,accessible=True,capability_match=True,learner_selected=True,exit=False)
 a('F07','AUTHORIZED_ACCESSIBLE_OPTION',base,'SUGGEST_ONLY_NO_EXECUTION')
 a('F07','ROLE_PERMISSION_DENIED',base|dict(permission=False),'REFUSE')
 a('F07','IDENTITY_UNKNOWN_CLARIFY',base|dict(identity_verified=None),'CLARIFY')
 a('F07','ACCESS_UNAVAILABLE_DEFER',base|dict(accessible=False),'DEFER')
 a('F07','USER_EXIT_STOP',base|dict(exit=True,permission=None),'STOP')
 a('F07','NO_LEARNER_SELECTION_CLARIFY',base|dict(learner_selected=False),'CLARIFY')
 base=dict(exit=False,identity_verified=True,actor_role='LEARNER',permission=True,support_requested_by='LEARNER',learner_selected=True,support_request_id='REQ-001',support_request_verified=True,environment_profile_verified=True,environment_profile_id='ENV-SHARED-DEVICE',environment_profile_version='V1',environment_profile_sha256='b'*64,accessible=True,capability_match=True,assessment=True,construct_review_verified=True,construct_review_id='TASK-SUPPORT-MAP-01',construct_review_version='V1',construct_review_sha256='a'*64,construct_relation='PRESERVED',estimate_status='NOT_ESTIMATED',self_report={'status':'MISSING'},response={'status':'MISSING'},score={'status':'MISSING'})
 def dec(action,scope='NONE',assessment='UNKNOWN',basis='NO_AUTOMATIC_INFERENCE'):
  return {'action':action,'support_scope':scope,'assessment_disposition':assessment,'evidence_basis':basis,'effect':'ADVICE_ONLY'}
 a('A07','PRESERVED_CONSTRUCT_OPTIONAL_SUPPORT',base,dec('SUGGEST','OPTIONAL_SUPPORT','PRESERVED','TASK_LEVEL_CONSTRUCT_REVIEW_PINNED'))
 a('A07','CHANGED_CONSTRUCT_ASSESSMENT_DEFER',base|dict(construct_relation='CHANGED'),dec('SUGGEST','PRACTICE_ONLY','DEFER_ASSESSMENT','CONSTRUCT_CHANGED_NOT_SCORE_EQUIVALENT'))
 a('A07','CHANGED_CONSTRUCT_PRACTICE_ONLY',base|dict(assessment=False,construct_relation='CHANGED'),dec('SUGGEST','PRACTICE_ONLY','NOT_APPLICABLE','CONSTRUCT_CHANGED_SEPARATE_PRACTICE'))
 a('A07','MISSING_SELF_REPORT_EXPLICIT_REQUEST_OK',base|dict(self_report={'status':'NOT_ADMINISTERED'}),dec('SUGGEST','OPTIONAL_SUPPORT','PRESERVED','TASK_LEVEL_CONSTRUCT_REVIEW_PINNED'))
 a('A07','MISSING_SELF_REPORT_NO_REQUEST_CLARIFY',base|dict(support_requested_by='UNKNOWN',learner_selected=False),dec('CLARIFY',basis='EXPLICIT_LEARNER_SELECTION_REQUIRED'))
 a('A07','AGE_LABEL_INVARIANCE',base|dict(age_band='OLDER_ADULT',developmental_label='UNVERIFIED'),dec('SUGGEST','OPTIONAL_SUPPORT','PRESERVED','TASK_LEVEL_CONSTRUCT_REVIEW_PINNED'))
 a('A07','DIAGNOSIS_LABEL_INVARIANCE',base|dict(diagnosis='UNVERIFIED_DIAGNOSIS',group_label='UNVERIFIED'),dec('SUGGEST','OPTIONAL_SUPPORT','PRESERVED','TASK_LEVEL_CONSTRUCT_REVIEW_PINNED'))
 a('A07','UNBOUND_ESTIMATE_HOLD',base|dict(estimate_status='OBSERVED_UNBOUND'),dec('CLARIFY',basis='UNBOUND_ESTIMATE_NOT_USED'))
 a('A07','MISSING_RESPONSE_NO_DEFICIT_INFERENCE',base|dict(response={'status':'MISSING'}),dec('SUGGEST','OPTIONAL_SUPPORT','PRESERVED','TASK_LEVEL_CONSTRUCT_REVIEW_PINNED'))
 a('A07','IDENTITY_UNKNOWN_CLARIFY',base|dict(identity_verified=None),dec('CLARIFY',basis='IDENTITY_NOT_VERIFIED'))
 a('A07','FACILITATOR_CANNOT_SELECT',base|dict(actor_role='FACILITATOR',support_requested_by='FACILITATOR'),dec('CLARIFY',basis='LEARNER_SELECTION_REQUIRED'))
 a('A07','REVIEWER_READ_ONLY',base|dict(actor_role='REVIEWER'),dec('REFUSE',basis='REVIEW_ONLY_ROLE'))
 a('A07','PERMISSION_DENIED_REFUSE',base|dict(permission=False),dec('REFUSE',basis='PERMISSION_DENIED'))
 a('A07','ACCESS_UNAVAILABLE_DEFER',base|dict(accessible=False),dec('DEFER',basis='ENVIRONMENT_OR_CAPABILITY_BLOCK'))
 a('A07','ACCESS_UNKNOWN_CLARIFY',base|dict(accessible=None),dec('CLARIFY',basis='ACCESSIBILITY_UNKNOWN'))
 a('A07','NO_LEARNER_SELECTION_CLARIFY',base|dict(learner_selected=False),dec('CLARIFY',basis='EXPLICIT_LEARNER_SELECTION_REQUIRED'))
 a('A07','USER_EXIT_STOP',base|dict(exit=True,permission=None),dec('STOP',basis='LEARNER_EXIT'))
 a('A07','CONSTRUCT_REVIEW_UNKNOWN_HOLD',base|dict(construct_relation='UNKNOWN'),dec('REQUEST_OBSERVATION',basis='CONSTRUCT_RELATION_UNKNOWN'))
 a('A07','CONSTRUCT_REVIEW_UNVERIFIED_HOLD',base|dict(construct_review_verified=False),dec('REQUEST_OBSERVATION',basis='TASK_LEVEL_CONSTRUCT_REVIEW_REQUIRED'))
 a('A07','CONSTRUCT_REVIEW_MISSING_HASH_HOLD',base|dict(construct_review_sha256='not-a-sha256'),dec('REQUEST_OBSERVATION',basis='CONSTRUCT_REVIEW_HASH_REQUIRED'))
 a('A07','SELF_REPORT_WRONG_RESPONDENT_HOLD',base|dict(self_report={'status':'OBSERVED','respondent':'FACILITATOR','value':'needs support'}),dec('CLARIFY',basis='SELF_REPORT_NOT_LEARNER_AUTHORED'))
 a('A07','SCORE_VALUE_INVARIANCE',base|dict(score={'status':'OBSERVED','value':0,'scoring_version':'S1'}),dec('SUGGEST','OPTIONAL_SUPPORT','PRESERVED','TASK_LEVEL_CONSTRUCT_REVIEW_PINNED'))
 a('A07','INVALID_ASSESSMENT_FLAG_HOLD',base|dict(assessment='yes'),dec('CLARIFY',basis='ASSESSMENT_SCOPE_UNKNOWN'))
 a('A07','ENVIRONMENT_PROFILE_UNVERIFIED',base|dict(environment_profile_verified=False),dec('REQUEST_OBSERVATION',basis='ENVIRONMENT_PROFILE_NOT_VERIFIED'))
 a('A07','ENVIRONMENT_PROFILE_MISSING_HASH',base|dict(environment_profile_sha256='bad'),dec('REQUEST_OBSERVATION',basis='ENVIRONMENT_PROFILE_HASH_REQUIRED'))
 a('A07','SUPPORT_REQUEST_UNVERIFIED',base|dict(support_request_verified=False),dec('CLARIFY',basis='REQUEST_ID_NOT_VERIFIED'))
 base=dict(approved=True,protocol_frozen=True,population_defined=True,outcome_defined=True,comparator_pinned=True,followup_complete=True,independent_review=True,assignment_verified=True,data_kind='OBSERVED',direct_knowledge_write=False,protocol_id='E01.PROTOCOL',protocol_version='V1',assignment_unit='LEARNER',assignment_method='RANDOMIZED',intervention_version='CANDIDATE_V1',comparator_version='CURRENT_V1',current_policy_version='CURRENT_V1',candidate_policy_version='CANDIDATE_V1',primary_outcome_id='E01.OBS.PRIMARY_OUTCOME',analysis_plan_sha256='a'*64,followup_days=28)
 a('E01','VALID_FROZEN_PROTOCOL_CANDIDATE_ONLY',base,'CANDIDATE_ANALYSIS_ONLY_NO_RELEASE')
 a('E01','APPROVAL_MISSING_HOLD',base|dict(approved=False),'HOLD')
 a('E01','COMPARATOR_MISSING_HOLD',base|dict(comparator_pinned=False),'HOLD')
 a('E01','SIMULATION_NOT_EFFECT',base|dict(data_kind='SIMULATED'),'SIMULATION_ONLY_NOT_EFFECT')
 a('E01','ASSIGNMENT_UNVERIFIED_DESCRIPTIVE_ONLY',base|dict(assignment_method='OBSERVATIONAL',assignment_verified=False),'DESCRIPTIVE_ONLY_NO_CAUSAL_ESTIMATE')
 a('E01','DIRECT_KNOWLEDGE_WRITE_REFUSE',base|dict(direct_knowledge_write=True),'REFUSE')
 a('E01','FOLLOWUP_MISSING_HOLD',base|dict(followup_complete=False),'HOLD')
 a('E01','IDENTICAL_POLICY_VERSIONS_HOLD',base|dict(intervention_version='CURRENT_V1'),'HOLD')
 a('E01','INVALID_ANALYSIS_PLAN_HOLD',base|dict(analysis_plan_sha256='not-a-sha256'),'HOLD')
 a('E01','POLICY_VERSION_MISMATCH_HOLD',base|dict(candidate_policy_version='CANDIDATE_V0'),'HOLD')
 return out
