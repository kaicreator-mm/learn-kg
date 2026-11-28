"""Finite actual SQL-backed event join; no execution authority or independent oracle."""
import sys,json,copy,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path[:0]=[str(HERE),str(ROOT),str(HERE.parent/'process-cumulative'),str(HERE.parent/'v01-second-subject')]
from replay import subject_eval,ref,H,P,MATH_KEY,load,sha,dig,SubjectImporter
from tools.knowledge_import.importer import ManifestPin,Reject
from tools.knowledge_import.v00_prototype import load_record
from semantic_checks import evaluate as pe
import importlib.util
spec=importlib.util.spec_from_file_location('f_rules',HERE.parent/'f-composition-preparation/semantic_checks.py')
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
def event_digest(e):return dig({k:v for k,v in e.items() if k!='sha256'})
def seal(e):e['sha256']=event_digest(e);return e
def ident(s):return type(s)is str and bool(s) and s==s.strip() and not any(ord(c)<32 for c in s)
def int0(x):return type(x)is int and x>=0
def route(im,domain,events,expected_event_pins,budget):
 if type(domain)is not str or domain not in ('ZH','MATH') or not int0(budget):return 'HOLD'
 key,owner,id=(H,'H06','H06.CONFIRM.TASK') if domain=='ZH' else (MATH_KEY,'M01','M01.TASK.COMPARE')
 taskref=ref(key,owner,'TaskSpec',id);task=load_record(im,taskref)
 obsref=task['observation_refs'][0];cref=task['construct_ref']
 load_record(im,obsref);load_record(im,cref)
 fc=load_record(im,ref(P,'F05','CompositionSpec','F05.COMPOSITION'))
 if fc['effect']!='CANDIDATE_DECISION_ONLY':return 'HOLD'
 for rr in fc['input_refs']+fc['output_refs']+fc['claim_refs']+fc['condition_refs']+fc['evidence_refs']:load_record(im,rr)
 if not isinstance(events,list) or len(events)!=4 or not isinstance(expected_event_pins,dict):return 'HOLD'
 if len(expected_event_pins)!=4:return 'HOLD'
 byid={};results=[];prior=None
 for phase,e in zip(('INITIAL','IMMEDIATE','DELAYED','VARIANT'),events):
  if not isinstance(e,dict) or not ident(e.get('id')) or e['id'] in byid or e.get('phase')!=phase:return 'HOLD'
  try:
   if e.get('sha256')!=event_digest(e) or expected_event_pins.get(e['id'])!=e['sha256']:return 'HOLD'
  except (TypeError,ValueError):return 'HOLD'
  if e.get('domain')!=domain or e.get('task_ref')!=taskref or e.get('construct_ref')!=cref or e.get('observation_ref')!=obsref:return 'HOLD'
  if e.get('subject')!='SYNTHETIC-'+domain or e.get('session')!='FIXTURE-'+domain or e.get('generated') is not False or e.get('actor')!=e['subject'] or e.get('hint_used') is not False:return 'HOLD'
  if e.get('clock')!='FIXTURE-UTC' or not int0(e.get('observed_at')) or not int0(e.get('recorded_at')) or not 0<=e['recorded_at']-e['observed_at']<=300:return 'HOLD'
  if prior and (e['observed_at']<=prior['observed_at'] or e['recorded_at']<=prior['recorded_at']):return 'HOLD'
  if e.get('family')!=('VARIANT_FIXTURE' if phase=='VARIANT' else 'TRAINED_FIXTURE'):return 'HOLD'
  if e.get('problem') in [z['problem'] for z in byid.values()]:return 'HOLD'
  x=dict(task_ref=taskref,problem=e.get('problem'),task_version=e.get('task_version'),observed_task_version=e.get('task_version'),scoring_version=e.get('scoring_version'),expected_scoring_version='S1',exit=False,permission=True,response_status=e.get('response_status'),response=e.get('response'),hint_used=e['hint_used'],hypotheses=['RULE','INSTRUCTION'])
  y=subject_eval(im,domain,x)
  if not isinstance(y,dict) or y['result']['category'] not in ('ERROR','INDEPENDENT_TASK_ONLY'):return 'HOLD'
  score=y['result']['score']
  chans=f.f05(dict(expected_scoring_version='S1',response=dict(status='OBSERVED',value=e['response'],task_version=e['task_version']),self_report=dict(status='MISSING'),score=dict(status='OBSERVED',value=score,scoring_version='S1',denominator=1),estimate=dict(status='NOT_RUN')))
  if not isinstance(chans,dict) or chans['combined_mastery']!='NOT_INFERRED':return 'HOLD'
  results.append(dict(event_id=e['id'],event_sha256=e['sha256'],score=score,feedback_route=y['result']['update'],channels=chans))
  byid[e['id']]=e;prior=e
 if set(byid)!=set(expected_event_pins):return 'HOLD'
 if results[0]['score']!=0 or results[0]['feedback_route']!='REQUEST_DISCRIMINATING_OBSERVATION':return 'HOLD'
 # Candidate feedback addresses the task, not an inferred cause or a real intervention.
 # P09 uses actual scored event identities and timestamps, not caller criteria booleans.
 observations=[]
 for e,r,stage in zip(events[1:],results[1:],('IMMEDIATE','DELAYED','TRANSFER')):
  observations.append(dict(stage=stage,id=e['id'],learner_identity=dict(kind='LEARNER_SUBJECT',subject_id=e['subject'],identity_version='V1'),time_basis='UTC_EPOCH_SECONDS',time_unit='SECOND',recording_time_basis='UTC_EPOCH_SECONDS',recording_time_unit='SECOND',clock_source_id=e['clock'],recording_clock_source_id=e['clock'],observed_at=e['observed_at'],recorded_at=e['recorded_at'],goal=id,scoring_version='S1',independent=True,construct_match=True,scoring_version_match=True,family=e['family'],criteria_met=r['score']==1,dimension='FIXTURE_VARIANT',new_task_family=stage=='TRANSFER',transfer_dimension_declared=stage=='TRANSFER'))
 def proc(o,x):
  return pe(im,load_record(im,ref(P,o,'FlowSpec',o+'.FLOW')),x,o,load_record)
 p09=proc('P09',dict(goal=id,scoring_version='S1',trained_family='TRAINED_FIXTURE',transfer_dimension='FIXTURE_VARIANT',observations=observations))
 if not isinstance(p09,dict):return p09
 # The exact checkpoint is reconstructed only from successfully validated event pins.
 def cp_input(cp,ev):
  return dict(exit=False,checkpoint=cp,checkpoint_sha256=dig(cp),resume_requested=True,authorized=True,session=cp['session'],version=cp['version'],events=ev)
 ce=[dict(id=e['id'],version=P[1],session=e['session'],type='OBSERVATION',cost=1,evidence_id=e['sha256']) for e in events]
 cp=dict(session=events[0]['session'],version=P[1],remaining=budget,seen={})
 first=proc('P10',cp_input(cp,ce[:1]))
 if not isinstance(first,dict):return first
 cp1=dict(cp,remaining=first['remaining'],seen={ce[0]['id']:dig(ce[0])})
 cp1=json.loads(json.dumps(cp1,sort_keys=True,separators=(',',':')))
 resume=proc('P10',cp_input(cp1,ce)) # repeat first then process remaining
 if not isinstance(resume,dict):return resume
 cp2=dict(cp1,remaining=resume['remaining'],seen={e['id']:dig(e) for e in ce})
 cp2=json.loads(json.dumps(cp2,sort_keys=True,separators=(',',':')))
 repeat=proc('P10',cp_input(cp2,ce))
 if not isinstance(repeat,dict):return repeat
 # Actual P10 gate must reject altered checkpoint and replay collision.
 checkpoint_probes=[]
 for name,payload,expect in [
  ('tampered_checkpoint',dict(cp_input(dict(cp1,remaining=99),ce),checkpoint_sha256=dig(cp1)),'HOLD'),
  ('conflicting_event',cp_input(cp2,[dict(ce[0],evidence_id='0'*64)]),'HOLD_CONFLICT'),
  ('wrong_session',dict(cp_input(cp2,ce),session='OTHER'),'HOLD'),
  ('wrong_version',dict(cp_input(cp2,ce),version='OTHER'),'HOLD'),
  ('exit',dict(cp_input(cp2,ce),exit=True),'STOP')]:
  got=proc('P10',payload);assert got==expect,(name,got,expect)
  checkpoint_probes.append(dict(id=name,expected=expect,actual=got,input_sha256=dig(payload)))
 return dict(status='SYNTHETIC_CHAIN_ONLY',events=results,p09=p09,first=first,resume=resume,repeat=repeat,checkpoint=cp2,checkpoint_sha256=dig(cp2),checkpoint_probes=checkpoint_probes,F05_composition_sha256=dig(fc),mastery='UNKNOWN',real_transfer='UNKNOWN')
def main():
 d=load(HERE.parent/'v01-lifecycle-witness/fixture_contract.json');cat={}
 for z in load(HERE/'catalog.json')['entries']:cat[z['package_id'],z['version']]=ManifestPin(z['path'],z['sha256'])
 ext=ROOT/'knowledge/v0.1.0/foundation-r3/relation-types.json';pin=ManifestPin(ext.relative_to(ROOT).as_posix(),sha(ext))
 ts={t['id']:t for t in load(ROOT/'docs/implementation/task-dag.json')['tasks']}
 receipt_pins={}
 for o in ('P06','P09','P10','F05','H06'):
  t=ts[o];p=ROOT/t['current_receipt'];r=load(p)
  for out in r['output']:assert sha(ROOT/out['path'])==out['sha256']
  q=t.get('qualification_receipt')
  if q:assert load(ROOT/q)['reviewed_content_digest']==r['content_digest']
  receipt_pins[o]=dict(receipt_sha256=sha(p),content_digest=r['content_digest'],qualification_sha256=sha(ROOT/q) if q else None)
 report=[]
 for domain in ('ZH','MATH'):
  key,owner,id=(H,'H06','H06.CONFIRM.TASK') if domain=='ZH' else (MATH_KEY,'M01','M01.TASK.COMPARE')
  im=SubjectImporter(ROOT,mode='research',catalog=cat,extension=pin)
  try:
   for k in (P,key):im._load(k,set())
   links={k:im._validate_refs(k) for k in im.packages}
   for k,v in links.items():im._materialize(k,v)
   taskref=ref(key,owner,'TaskSpec',id);task=load_record(im,taskref)
   cfg=d['domains'][domain];ev=[]
   for i,(phase,problem,response) in enumerate(zip(d['phases'],[cfg[x] for x in ('initial','immediate','delayed','variant')],cfg['responses'])):
    ev.append(seal(dict(id=domain+'-E'+str(i),phase=phase,domain=domain,task_ref=taskref,construct_ref=task['construct_ref'],observation_ref=task['observation_refs'][0],task_version='T1',scoring_version='S1',subject='SYNTHETIC-'+domain,actor='SYNTHETIC-'+domain,session='FIXTURE-'+domain,generated=False,hint_used=False,clock='FIXTURE-UTC',observed_at=d['observed_at'][i],recorded_at=d['observed_at'][i]+d['record_lag_seconds'],family='VARIANT_FIXTURE' if i==3 else 'TRAINED_FIXTURE',problem=problem,response_status='OBSERVED',response=response)))
   pins={e['id']:e['sha256'] for e in ev};actual=route(im,domain,ev,pins,d['initial_budget']);ex=d['expected']
   assert isinstance(actual,dict),actual
   assert actual['events'][0]['score']==ex['initial_score'] and actual['events'][0]['feedback_route']==ex['initial_route']
   assert [x['score'] for x in actual['events'][1:]]==ex['post_feedback_scores']
   assert actual['p09']['computed_delay_seconds']==ex['delay_seconds'] and all(actual['p09']['criteria'].values())
   assert actual['first']['new_events']==ex['new_events_first'] and actual['resume']['new_events']==ex['new_events_resume'] and actual['resume']['remaining']==0 and actual['resume']['total_event_ids']==4 and actual['repeat']['new_events']==0
   assert actual['mastery']==ex['mastery'] and actual['real_transfer']==ex['real_transfer']
   negative=[]
   def probe(name,index,patch,expected='HOLD',reseal=True):
    events=copy.deepcopy(ev);events[index].update(patch)
    if reseal:seal(events[index])
    # Pins may be refreshed by synthetic fixture author to test actual semantic guards,
    # rather than merely tripping the original digest guard.
    p={e['id']:e['sha256'] for e in events} if reseal else pins
    got=route(im,domain,events,p,4);assert got==expected,(name,got);negative.append(dict(id=name,expected=expected,actual=got,input=events,pins=p))
   for name,index,patch in [('wrong_actor',0,{'actor':'OTHER'}),('generated',0,{'generated':True}),('assisted',1,{'hint_used':True}),('wrong_construct',1,{'construct_ref':{}}),('wrong_observation',1,{'observation_ref':{}}),('wrong_scoring',1,{'scoring_version':'S2'}),('duplicate_id',1,{'id':ev[0]['id']}),('blank_id',1,{'id':' '}),('clock',2,{'clock':'OTHER'}),('wrong_subject',2,{'subject':'OTHER'}),('wrong_session',2,{'session':'OTHER'}),('short_delay',2,{'observed_at':ev[1]['observed_at']+30,'recorded_at':ev[1]['recorded_at']+30}),('same_problem',3,{'problem':ev[1]['problem']}),('same_family',3,{'family':'TRAINED_FIXTURE'}),('record_order',2,{'recorded_at':0}),('invalid_response',2,{'response':'INVALID'})]:
    probe(name,index,patch)
   probe('tampered_response',0,{'response':'FORGED'},reseal=False)
   assert route(im,domain,ev,pins,3)=='HOLD_BUDGET';negative.append(dict(id='budget',expected='HOLD_BUDGET',actual='HOLD_BUDGET'))
   bad=dict(pins);bad[ev[0]['id']]='0'*64;assert route(im,domain,ev,bad,4)=='HOLD';negative.append(dict(id='wrong_event_pin',expected='HOLD',actual='HOLD'))
   assert route(im,'UNKNOWN',ev,pins,4)=='HOLD';negative.append(dict(id='unknown_domain',expected='HOLD',actual='HOLD'))
   assert all(c.execute('PRAGMA query_only').fetchone()==(1,) and not c.execute('PRAGMA foreign_key_check').fetchall() and all(not v[2] for v in c.execute('PRAGMA database_list')) for c in im.connections.values())
   assert (MATH_KEY if domain=='ZH' else H) not in im.connections
   report.append(dict(domain=domain,events=ev,event_pins=pins,feedback_candidate_text=cfg['feedback'],actual=actual,negative_cases=negative,opened_packages=[list(k) for k in im.connections],persistent_sqlite=False))
  finally:im.close()
 out=dict(status='AUTHOR_SYNTHETIC_EVENT_CHAIN_NOT_INDEPENDENT_OR_FULL_CQ_LC',source_registered_manifest_sha256=load(HERE/'projection-evidence.json')['source_manifest_sha256'],fixture_sha256=sha(HERE.parent/'v01-lifecycle-witness/fixture_contract.json'),process_manifest_sha256=cat[P].sha256,receipt_pins=receipt_pins,routes=report,positive_chains=len(report),negative_cases=sum(len(r['negative_cases']) for r in report),checkpoint_guard_probes=sum(len(r['actual']['checkpoint_probes']) for r in report),full_CQ_LC='NOT_RUN',real_authority='UNBOUND',mastery='UNKNOWN',persistent_sqlite=False)
 (HERE/'lifecycle-results.json').write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
 print('LIFECYCLE',out['positive_chains'],out['negative_cases'],[(r['domain'],len(r['opened_packages'])) for r in report])
if __name__=='__main__':main()
