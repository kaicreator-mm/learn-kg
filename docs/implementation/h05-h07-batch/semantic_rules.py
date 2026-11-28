"""Finite candidate task rules. Inputs are stipulated observations, not live learner evidence."""
import importlib.util
from pathlib import Path
p=Path(__file__).resolve().parent.parent/'h01-h04-batch/semantic_rules.py'
spec=importlib.util.spec_from_file_location('accepted_h01_h04_rules',p);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
def finite(rule,x):
 if not isinstance(x,dict):return 'HOLD'
 if rule=='confirm':
  if x.get('framework')!='RFC_2024' or x.get('prior_proposition') is not True or x.get('verified_confirmation_request') is not True:return 'HOLD'
  if x.get('form') not in ('DECLARATIVE','TAG','NEGATIVE_RHETORICAL','A_NOT_A','NP'):return 'HOLD'
  return {'CONFIRM':'CONFIRMATION_SEQUENCE','DISCONFIRM':'DISCONFIRMATION_SEQUENCE'}.get(x.get('response'),'HOLD')
 if rule=='domain':
  if x.get('framework')!='CEFR' or x.get('context_explicit') is not True:return 'HOLD'
  return {'FAMILY':'PERSONAL','SCHOOL':'EDUCATIONAL','JOB':'OCCUPATIONAL','PUBLIC_SERVICE':'PUBLIC'}.get(x.get('purpose'),'HOLD')
 if rule=='pragmatic_context':
  if x.get('framework')!='CEFR' or x.get('query')!='TASK_SPEC':return 'HOLD'
  keys=('goal','roles','context','language_activity')
  if not all(isinstance(x.get(k),str) and x[k].strip() for k in keys):return 'HOLD'
  if x['language_activity'] not in ('RECEPTION','PRODUCTION','INTERACTION','MEDIATION'):return 'HOLD'
  return {k:x[k] for k in keys}
 if rule=='repair':
  if x.get('framework')!='CEFR' or x.get('observed_trouble') is not True:return 'HOLD'
  if x.get('query')!='REPAIR_EVIDENCE':return 'HOLD'
  if x.get('clarification') is True and x.get('confirmed_understanding') is True:return 'REPAIR_OBSERVED_IN_FIXTURE'
  if x.get('clarification') is True:return 'REQUEST_CONFIRMATION'
  return 'HOLD'
 if rule=='activity':
  if x.get('framework')!='CEFR' or x.get('task_evidence') is not True:return 'HOLD'
  return {'LISTEN_FOR_MEANING':'RECEPTION','READ_FOR_MEANING':'RECEPTION','WRITE_MONOLOGUE':'PRODUCTION','SPEAK_MONOLOGUE':'PRODUCTION','RECIPROCAL_EXCHANGE':'INTERACTION','ENABLE_UNDERSTANDING':'MEDIATION'}.get(x.get('task'),'HOLD')
 if rule=='mediation':
  if x.get('framework')!='CEFR' or x.get('query')!='MEDIATION_TASK' or x.get('meaning_access_goal') is not True:return 'HOLD'
  if x.get('language_relation') not in ('SAME_LANGUAGE','CROSS_LANGUAGE'):return 'HOLD'
  return 'MEDIATION_CANDIDATE' if x.get('recipient_and_purpose_explicit') is True else 'HOLD'
 if rule=='fact':
  if x.get('framework')!='ACTFL_2024' or x.get('query')!='DESCRIPTION_DIMENSIONS':return 'HOLD'
  if x.get('skill') not in ('LISTENING','SPEAKING','READING','WRITING'):return 'HOLD'
  keys=('functions_tasks','accuracy','context_content','text_type')
  if any(not isinstance(x.get(k),str) or not x[k].strip() for k in keys):return 'HOLD'
  return {k:x[k] for k in keys}
 if rule=='can_do':
  if x.get('framework')!='ACTFL_CAN_DO' or x.get('query')!='EVIDENCE_SUFFICIENCY_SCREEN':return 'HOLD'
  if x.get('independent') is not True:return 'HOLD'
  n=x.get('distinct_situations');t=x.get('distinct_occasions')
  if type(n)is not int or type(t)is not int or n<1 or t<1:return 'HOLD'
  return 'INSUFFICIENT_SINGLE_CONTEXT_OR_OCCASION' if n==1 or t==1 else 'MULTIPLE_CONTEXT_EVIDENCE_REVIEW_REQUIRED'
 if rule=='task_modality':
  if x.get('query')!='MODALITY_EVIDENCE' or x.get('framework')!='ACTFL_2024':return 'HOLD'
  pairs={'LISTENING':('AUDIO','MEANING_RESPONSE'),'READING':('TEXT','MEANING_RESPONSE'),'SPEAKING':('AUDIO_OUTPUT','PRODUCTION'),'WRITING':('TEXT_OUTPUT','PRODUCTION')}
  target=pairs.get(x.get('skill'))
  if target is None:return 'HOLD'
  if (x.get('artifact'),x.get('observed_operation'))!=target:return 'HOLD'
  return 'MODALITY_MATCH_ONLY'
 if rule=='gf_totals':
  if x.get('source')!='MOE_2021_04_02' or x.get('standard')!='GF0025-2021':return 'HOLD'
  return {'REPORTED_TOTALS':{'syllables':1110,'characters':3000,'lexical_items':11092,'grammar_points':572},'GROUP_STRUCTURE':{'初等':3,'中等':3,'高等':3}}.get(x.get('query'),'HOLD')
 if rule=='gf_identity':
  if x.get('source')!='MOE_2021_03_31' or x.get('standard')!='GF0025-2021':return 'HOLD'
  return {'DOCUMENT_KIND':'EDUCATION_LANGUAGE_STANDARD','EFFECTIVE_DATE':'2021-07-01','LEVEL_STRUCTURE':[3,9],'ELEMENT_DIMENSIONS':['音节','汉字','词汇','语法'],'SKILL_DIMENSIONS':['听','说','读','写','译'],'ASSESSMENT_DIMENSIONS':['言语交际能力','话题任务内容','语言量化指标']}.get(x.get('query'),'HOLD')
 if rule=='exam_launch':
  if x.get('source')!='CTI_51336724' or x.get('edition')!='HSK_3.0' or x.get('query')!='ANNOUNCED_LAUNCH':return 'HOLD'
  return {'announced_date':'2026-12-13','status':'ANNOUNCED_NOT_ACTUAL_OCCURRENCE'}
 if rule=='standard_mapping':
  if x.get('query')!='CROSS_STANDARD_MAPPING' or x.get('framework')!='PROJECT_EVIDENCE_GATE':return 'HOLD'
  if not all(isinstance(x.get(k),str) and x[k].strip() for k in ('source_standard','target_standard','source_version','target_version')):return 'HOLD'
  if x.get('same_label_only') is not False or x.get('empirical_link_evidence') is not True or x.get('mapping_conditions_verified') is not True:return 'UNKNOWN_HOLD'
  return 'LINK_EVIDENCE_REVIEW_REQUIRED'
 if rule=='membership':
  if x.get('query')!='RECORDED_SOURCE_MEMBERSHIP' or x.get('framework')!='HSK01_RESTRICTED' or x.get('exact_source_ref') is not True:return 'HOLD'
  if x.get('semantic_qualification') is not False:return 'HOLD'
  if x.get('kind') not in ('LEXICAL','CHARACTER_READ','CHARACTER_WRITE','GRAMMAR_BLOCK','TASK_BLOCK','TOPIC_BLOCK'):return 'HOLD'
  return 'RECORDED_MEMBERSHIP_ONLY'
 return old.evaluate(rule,x)
def evaluate(rule,x):
 try:return finite(rule,x)
 except (TypeError,ValueError,KeyError):return 'HOLD'
