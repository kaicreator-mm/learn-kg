"""Finite composition of stipulated evidence. No learner data, authority resolver or action."""
import importlib.util
from pathlib import Path
_p=Path(__file__).resolve().parent.parent/"f-composition-preparation"/"semantic_checks.py"
_spec=importlib.util.spec_from_file_location("accepted_f_rules",_p);_old=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_old)
def goodint(v):return type(v)is int and v>=0
def yes(x,*keys):return all(x.get(k) is True for k in keys)
def evaluate(owner,x):
 try:
  if not isinstance(x,dict):return 'HOLD'
  if x.get('exit') is True:return 'STOP'
  if x.get('permission') is False:return 'REFUSE'
  if x.get('exit') is not False or x.get('permission') is not True:return 'HOLD'
  if owner=='F01':
   # Exact H06 task templates, not a score, course level or actual ability.
   goal=x.get('goal');task=x.get('task');match={'LISTENING':'H06.TASK.LISTENING','READING':'H06.TASK.READING','SPEAKING':'H06.TASK.SPEAKING','WRITING':'H06.TASK.WRITING','CONFIRMATION':'H06.CONFIRM.TASK'}
   if goal not in match or task!=match[goal] or not yes(x,'target_explicit','conditions_verified'):return 'HOLD'
   return dict(task=task,goal=goal,level='UNKNOWN',mastery='UNKNOWN',necessary_prerequisites=[])
  if owner=='F02':
   task=x.get('task');skill=x.get('skill');obj=x.get('object')
   m={k:('H06.TASK.'+k,'H06.TASK.'+k+'.OBJECT') for k in ('LISTENING','READING','SPEAKING','WRITING')};m['CONFIRMATION']=('H06.CONFIRM.TASK','H06.CONFIRM.OBJECT')
   if skill not in m or (task,obj)!=m[skill] or not yes(x,'object_identity_verified','target_match'):return 'HOLD'
   if x.get('basis')!='ACTUAL_TASK_OBJECT':return 'HOLD'
   return dict(task=task,object=obj,granularity='TASK_OBJECT_ONLY',necessary_prerequisites=[],mastery='UNKNOWN')
  if owner=='F06':
   # Competing explanations are not diagnoses. Require stipulated distinguishing observation.
   if x.get('task')!='H06.CONFIRM.TASK' or x.get('observation') not in ('INCORRECT','NO_RESPONSE','ASSISTED'):return 'HOLD'
   hypotheses=['PROPOSITION_UNDERSTANDING','RESPONSE_FORM','TASK_INSTRUCTION']
   if not yes(x,'independent','same_construct','conditions_verified') or x.get('observation')!='INCORRECT':return dict(hypotheses=hypotheses,decision='REQUEST_OBSERVATION',mastery='UNKNOWN')
   h=x.get('distinguished_gap')
   if h not in hypotheses or not yes(x,'competing_explanations_checked'):return dict(hypotheses=hypotheses,decision='REQUEST_OBSERVATION',mastery='UNKNOWN')
   return dict(hypotheses=hypotheses,decision='REMEDIATION_REVIEW_REQUIRED',target=h,mastery='UNKNOWN')
  if owner=='F08':
   # Independent events with different task instances, same construct, exact template, increasing times.
   rows=x.get('events')
   if not isinstance(rows,list) or len(rows)>3:return 'HOLD'
   out={k:'UNKNOWN' for k in ('IMMEDIATE','DELAYED','NOVEL')};seen=set();times={}
   for e in rows:
    if not isinstance(e,dict) or e.get('phase') not in out or e['phase'] in seen:return 'HOLD'
    p=e['phase'];seen.add(p)
    if not isinstance(e.get('task_instance'),str) or not e['task_instance'] or not goodint(e.get('time')) or e.get('template')!='H06.CONFIRM.TASK':return 'HOLD'
    if e.get('outcome') not in ('CORRECT','INCORRECT') or not yes(e,'independent','construct_match','conditions_verified'):return 'HOLD'
    if p=='NOVEL' and e.get('structural_novelty_verified') is not True:return 'HOLD'
    times[p]=e['time'];out[p]=e['outcome']
   if len({e['task_instance'] for e in rows})!=len(rows):return 'HOLD'
   if ('DELAYED' in seen or 'NOVEL' in seen) and 'IMMEDIATE' not in seen:return 'HOLD'
   if any(times[p]<=times['IMMEDIATE'] for p in ('DELAYED','NOVEL') if p in seen):return 'HOLD'
   return dict(observations=out,mastery='UNKNOWN',general_transfer='UNKNOWN')
  def run(o,k):return evaluate(o,x.get(k))
  if owner=='A01':
   g=run('F01','goal');b=run('F02','object')
   if not isinstance(g,dict) or not isinstance(b,dict):return 'HOLD'
   if g['task']!=b['task'] or g['goal']!=x['object']['skill']:return 'HOLD'
   return dict(goal=g['goal'],task=g['task'],object=b['object'],necessary_prerequisites=[],level='UNKNOWN')
  if owner=='A02':
   b=run('F02','object')
   if not isinstance(b,dict):return 'HOLD'
   if b['task']!='H06.TASK.LISTENING':return 'HOLD'
   rg=x.get('resource_gate')
   if not isinstance(rg,dict) or rg.get('modality')!=x.get('artifact') or rg.get('required_construct')!='LISTENING':return 'HOLD'
   resource=_old.f03(rg)
   if resource=='REJECT_CONSTRUCT_SUBSTITUTION':return resource
   if resource not in ('PRIVATE_RESOURCE_CANDIDATE','PUBLIC_RESOURCE_CANDIDATE_WITH_SEPARATE_RIGHTS_CHECK') or x.get('artifact')!='AUDIO':return 'HOLD'
   if not yes(x,'resource_accessible','resource_rights_verified','response_is_learner','independent','task_version_verified'):return 'HOLD'
   return dict(task=b['task'],observation='H06.TASK.LISTENING.OBS',effect='REVIEW_OBSERVATION_ONLY')
  if owner=='A03':
   d=run('F06','diagnosis')
   if not isinstance(d,dict):return 'HOLD'
   channels=_old.f05(x.get('state_channels'))
   if not isinstance(channels,dict) or channels.get('combined_mastery')!='NOT_INFERRED':return 'HOLD'
   if x.get('observation_channel') not in ('RESPONSE','SELF_REPORT','SCORE','ESTIMATE'):return 'HOLD'
   if x.get('observation_channel')!='RESPONSE':return dict(state='UNKNOWN',decision='REQUEST_OBSERVATION')
   return dict(state='UNKNOWN',diagnosis=d)
  if owner=='A04':
   d=run('F06','diagnosis')
   if not isinstance(d,dict) or d['decision']!='REMEDIATION_REVIEW_REQUIRED':return 'HOLD'
   channels=_old.f05(x.get('state_channels'))
   if not isinstance(channels,dict) or channels.get('combined_mastery')!='NOT_INFERRED':return 'HOLD'
   budget=x.get('budget');choices=x.get('choices')
   if not goodint(budget) or not isinstance(choices,list) or not choices or len(choices)>8:return 'HOLD'
   eligible=[]
   for c in choices:
    if not isinstance(c,dict) or c.get('id') not in ('CHECK_PROPOSITION','CHECK_FORM','CHECK_INSTRUCTION') or not goodint(c.get('cost')):return 'HOLD'
    target={'CHECK_PROPOSITION':'PROPOSITION_UNDERSTANDING','CHECK_FORM':'RESPONSE_FORM','CHECK_INSTRUCTION':'TASK_INSTRUCTION'}[c['id']]
    if target==d['target'] and c['cost']<=budget and yes(c,'conditions_verified','resources_verified'):eligible.append((c['cost'],c['id']))
   if len({c['id'] for c in choices})!=len(choices):return 'HOLD'
   if not eligible:return 'DEFER'
   cost,id=min(eligible);return dict(candidate=id,cost=cost,remaining=budget-cost,effect='PLAN_REVIEW_ONLY')
  if owner=='A05':
   g=run('F01','goal');r=run('F08','retention')
   if not isinstance(g,dict) or g['task']!='H06.CONFIRM.TASK' or not isinstance(r,dict):return 'HOLD'
   return dict(task=g['task'],**r)
  if owner=='A06':
   if x.get('publication') is True:return 'REFUSE_PUBLICATION'
   if x.get('publication') is not False:return 'HOLD'
   if x.get('generated_as_learner_response') is True:return 'NOT_LEARNER_EVIDENCE'
   if x.get('generated_as_learner_response') is not False:return 'HOLD'
   if x.get('content_kind')!='ORIGINAL_CONFIRMATION_TEMPLATE' or not yes(x,'source_scope_verified','facts_checked','conditions_checked','independent_content_review','resource_rights_verified'):return 'HOLD'
   return 'PRIVATE_DRAFT_REVIEW_ONLY'
  if owner=='A08':
   r=run('F08','retention')
   if not isinstance(r,dict):return 'HOLD'
   if x.get('direct_knowledge_write') is True:return 'REFUSE'
   if x.get('direct_knowledge_write') is not False:return 'HOLD'
   result=_old.e01(x.get('protocol_gate'))
   if x.get('data_kind')=='SYNTHETIC' and result=='SIMULATION_ONLY_NOT_EFFECT':return result
   if x.get('data_kind')=='REAL' and result in ('HOLD','DESCRIPTIVE_ONLY_NO_CAUSAL_ESTIMATE'):return 'HOLD_NO_TRUSTED_APPROVAL_OR_REAL_DATA'
   return 'HOLD'
  return 'HOLD'
 except (TypeError,ValueError,KeyError):return 'HOLD'
