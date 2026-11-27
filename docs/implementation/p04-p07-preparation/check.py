"""Restricted preparation, not canonical FlowSpec or general runtime."""
import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent; ROOT=P.parents[2]
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dig(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def integer(x):return type(x) is int and x>=0
def p04(x,spec):
 b=x.get('budget');v=x.get('version')
 if not integer(b) or not isinstance(v,str) or not v or x.get('authorized') is not True or x.get('goal_confirmed') is not True:return 'HOLD'
 state='READY'; seen={}; members=set(); retries=0; checkpoint=None; support=spec['max_support_level']
 for e in x['events']:
  if state in ('STOP','COMPLETE','HOLD','FAILED'):return state
  if e.get('type')=='STOP':return 'STOP'
  id=e.get('id')
  if not isinstance(id,str) or not id:return 'HOLD'
  if id in seen:
   if e!=seen[id]:return 'HOLD'
   continue
  if len(seen)>=spec['max_events']:return 'HOLD'
  seen[id]=e
  if e.get('version')!=v:return 'HOLD'
  t=e.get('type')
  if t=='PAUSE' and state in ('ACTIVE','JOINED','REMEDIATION','EVALUATE'):
   checkpoint=(id,state);state='PAUSED';continue
  if state=='PAUSED':
   if t!='RESUME' or e.get('learner_resume') is not True or e.get('checkpoint')!=checkpoint[0]:return 'HOLD'
   state=checkpoint[1];continue
  c=e.get('cost')
  if not integer(c) or c>b:return 'HOLD'
  if t=='START' and state=='READY':
   if e.get('mode_match') is not True or e.get('resource_ready') is not True:return 'HOLD'
   state='ACTIVE'
  elif t=='MEMBER' and state=='ACTIVE':
   m=e.get('member')
   if m not in ('A','B') or m in members or e.get('valid_observation') is not True:return 'HOLD'
   members.add(m)
   if len(members)==2:state='JOINED'
  elif t=='SUBFLOW' and state=='JOINED':
   z=e.get('result')
   if z=='COMPLETE':state='EVALUATE'
   elif z in ('PAUSE','HOLD','FAILED'):return z
   else:return 'HOLD'
  elif t=='ASSESS' and state=='EVALUATE':
   if e.get('independent') is not True:return 'HOLD'
   if e.get('task_criteria_met') is True:state='COMPLETE'
   elif e.get('task_criteria_met') is False and retries<spec['max_retries']:state='REMEDIATION'
   else:return 'HOLD'
  elif t=='RETRY' and state=='REMEDIATION':
   if retries>=spec['max_retries'] or e.get('target_match') is not True or e.get('learner_opt_in') is not True:return 'HOLD'
   retries+=1;state='EVALUATE'
  elif t=='FADE' and state in ('ACTIVE','EVALUATE'):
   if support<=0 or any(e.get(k) is not True for k in ('independent_evidence','risk_acceptable','reversible','learner_opt_in')):return 'HOLD'
   support-=1
  else:return 'HOLD'
  b-=c
 return state if state in ('COMPLETE','STOP') else 'PAUSE' if state=='PAUSED' else 'HOLD'
def p07(x,options):
 if x.get('exit') is True:return 'STOP'
 if x.get('exit') is not False:return 'HOLD'
 if x.get('declined') is True:return 'DEFER'
 if x.get('declined') is not False:return 'HOLD'
 if x.get('paused') is True and x.get('resume_requested') is not True:return 'PAUSE'
 if x.get('paused') not in (True,False) or type(x.get('paused')) is not bool:return 'HOLD'
 if x.get('goal_confirmed') is not True or x.get('authorized') is not True:return 'HOLD'
 if not integer(x.get('budget')) or not integer(x.get('cost')) or x['cost']>x['budget']:return 'HOLD'
 if x.get('selected') not in options:return 'CLARIFY'
 if x.get('accessible') is not True:return 'HOLD'
 if x['selected']=='ADJUST_CHALLENGE' and x.get('target_match') is not True:return 'HOLD'
 if x['selected']=='REQUEST_SUPPORT' and x.get('no_answer_substitution') is not True:return 'HOLD'
 if x.get('progress_requested') is True:
  a,b=x.get('previous'),x.get('current')
  if not isinstance(a,dict) or not isinstance(b,dict):return 'REQUEST_OBSERVATION'
  if any(not isinstance(a.get(k),str) or not a[k] or a[k]!=b.get(k) for k in ('goal','scoring_version','support','unit')):return 'REQUEST_OBSERVATION'
  if not integer(a.get('score')) or not integer(b.get('score')):return 'REQUEST_OBSERVATION'
  return 'DESCRIBE_TASK_CHANGE_ONLY'
 return 'SUGGEST_'+x['selected']
def main():
 design=load(P/'design.json');dag=load(ROOT/'docs/implementation/task-dag.json');ts={t['id']:t for t in dag['tasks']};bindings={}
 for owner in ('P04','P07'):
  t=ts[owner];assert t['status']=='READY'
  ids=set(design[owner]['claims']+design[owner]['process_refs']);found={}
  for dep in t['depends_on']:
   rp=ts[dep]['current_receipt'];r=load(ROOT/rp);assert r['state']==ts[dep]['status']
   q=ts[dep].get('qualification_receipt')
   if q: assert load(ROOT/q)['reviewed_content_digest']==r['content_digest']
   for f in r['output']:
    fp=ROOT/f['path']
    if fp.suffix!='.jsonl':continue
    assert sha(fp)==f['sha256']
    for l in fp.read_text().splitlines():
     z=json.loads(l);id=z['stable_id']
     if z['owner']!=dep or id not in ids:continue
     assert id not in found and z['status']=='CANDIDATE'
     if z['kind']=='Claim':
      assert z['claim_type'] in ('PROJECT_RULE','ENGINEERING_POLICY','ORIGINAL_METHOD_DERIVATION','METHOD','MATHEMATICAL_DERIVATION')
      allowed=r.get('scope_restriction',{}).get('candidate_claim_ids')
      if allowed is not None:assert id in allowed
     found[id]=dict(owner=dep,kind=z['kind'],path=f['path'],sha256=f['sha256'],record_sha256=dig(z),receipt=rp,receipt_sha256=sha(ROOT/rp),qualification=q,qualification_sha256=sha(ROOT/q) if q else None)
  assert set(found)==ids,(owner,ids-set(found));bindings[owner]=found
 write(P/'bindings.json',bindings)
 fs=load(P/'fixtures.json');results=[]
 for f in fs:
  owner=f['owner'];y=p04(f['input'],design[owner]['limits']) if owner=='P04' else p07(f['input'],design[owner]['options'])
  assert y==f['expected'],(f['id'],y,f['expected']);results.append(dict(id=f['id'],owner=owner,actual=y))
 write(P/'results.json',dict(status='BUILDER_PREPARATION_ONLY',case_count=len(results),design_sha256=sha(P/'design.json'),bindings_sha256=sha(P/'bindings.json'),fixtures_sha256=sha(P/'fixtures.json'),results=results,limits='Synthetic adapter, no canonical FlowSpec import, empirical effect, runtime authorization or qualification.'))
 print('PREPARATION',len(results),'finite cases',sum(len(x) for x in bindings.values()),'exact bindings')
if __name__=='__main__':main()
