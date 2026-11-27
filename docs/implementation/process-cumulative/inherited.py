"""Replay previously authored P01–P03 cases on the cumulative SQL snapshot.

No independent result is inferred. P01 uses the original finite evaluator;
P02/P03 use the original declared transition/guard semantics, with references
resolved from the current cumulative SQL snapshot.
"""
import json,sys
def replay(im,local,old,remap,version,root,load_record,check,dig):
 p=root/'docs/implementation/p01-learning-modes'
 sys.path.insert(0,str(p))
 from build_p01 import evaluate
 old_bind=json.loads((root/'docs/implementation/p02-p03/activity-bindings.json').read_text())
 bindings=remap(old_bind,version)
 results=[]
 def p02(f,x):
  s=f['entry'];terms={t['id']:t['outcome'] for t in f['terminals']};seen=set();frozen=None
  for i,event in enumerate(x):
   if s in terms:return terms[s]
   if i>=f['max_events'] or s in seen:return 'HOLD'
   seen.add(s);e=dict(event)
   if e.get('event')=='STOP':return f['stop_terminal']
   if e.get('event') in ('RESOURCES_CONFIRMED','PLAN_SELECTED','BUDGET_CONFLICT'):
    a,b=e.get('cost'),e.get('budget')
    if type(a) is not int or type(b) is not int or min(a,b)<0:return 'HOLD'
    e['within_budget']=a<=b
    if e.get('event')=='RESOURCES_CONFIRMED':frozen=(a,b)
    if e.get('event')=='PLAN_SELECTED' and (a,b)!=frozen:return 'HOLD'
   step=next(z for z in f['steps'] if z['id']==s);a=load_record(im,step['activity_ref']);assert a['budget']==step['max_attempts']==1
   ts=[t for t in f['transitions'] if t['from_step']==s and t['event']==e.get('event')]
   if len(ts)!=1 or not check(im,ts[0]['condition_ref'],e):return 'HOLD'
   s=ts[0]['to_step']
  return terms.get(s,'HOLD')
 def p03(ref,a,x):
  if x.get('exit') is True:return 'STOP'
  if x.get('exit') is not False:return 'HOLD'
  if type(x.get('budget')) is not int or x['budget']<a['budget']:return 'HOLD'
  b=bindings[ref['stable_id']]
  return b['evidence_class'] if check(im,b['guard'],x) else 'HOLD'
 for id,r in old.items():
  if r['kind']!='Case':continue
  c=load_record(im,local(id));x=json.loads(c['input_spec']);assert c['expected_spec']==r['expected_spec']
  target=c['target_refs'][0];a=load_record(im,target);o=r['owner']
  if o=='P01':y=evaluate(c['view'],x)
  elif o=='P02':y=p02(a,x)
  else:y=p03(target,a,x)
  assert y==c['expected_spec'],(id,y,c['expected_spec'])
  results.append(dict(owner=o,case_id=id,actual=y,status='BUILDER_REGRESSION_ONLY'))
 counts={o:sum(r['owner']==o for r in results) for o in ('P01','P02','P03')};assert counts=={'P01':36,'P02':17,'P03':90},counts
 return dict(status='MIGRATED_BUILDER_REGRESSION_ONLY',counts=counts,results=results,limits='143 inherited authored cases; no new independent oracles; P01 is original finite author evaluator with current SQL target read.')
