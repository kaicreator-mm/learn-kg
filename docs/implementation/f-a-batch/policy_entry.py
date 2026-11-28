"""Explicit candidate-4 P07 entry; reviewed previous algorithm, version gate only changed."""
from build import ref,load_record,int0,check

def policy_eval(im,policy_ref,x,*,expected_version=None):
 # Bounded P07-only entry point. Never infer policy ownership from mutable
 # rule payloads. Resolve the canonical policy using the complete typed tuple
 # from the already validated, read-only SQL import. No caller policy object.
 if expected_version!='0.1.0-process-candidate-4':return 'HOLD'
 expected=ref('P07','PolicySpec','P07.POLICY',expected_version)
 if type(policy_ref) is not dict or policy_ref!=expected or type(x) is not dict:return 'HOLD'
 try:
  p=load_record(im,expected)
  if type(p) is not dict or p.get('effect')!='ADVICE_ONLY' or p.get('policy_type')!='MOTIVATION':return 'HOLD'
  rules=p.get('rules')
  if type(rules) is not list or not rules:return 'HOLD'
  priorities=set()
  early_actions={0:'STOP',1:'DEFER',2:'PAUSE'}
  for r in rules:
   if type(r) is not dict or type(r.get('priority')) is not int:return 'HOLD'
   priority=r['priority'];condition=r.get('condition_ref')
   if priority<0 or priority in priorities:return 'HOLD'
   priorities.add(priority)
   if type(condition) is not dict:return 'HOLD'
   guard_id=condition.get('stable_id')
   if type(guard_id) is not str or not guard_id.startswith('P07.GUARD.'):return 'HOLD'
   if condition!=ref('P07','ConditionSpec',guard_id,expected['version']):return 'HOLD'
   if r.get('action')!=early_actions.get(priority,'SUGGEST'):return 'HOLD'
 except Exception:
  return 'HOLD'
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
