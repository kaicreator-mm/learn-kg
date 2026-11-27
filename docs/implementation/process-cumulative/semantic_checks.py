"""Finite concrete process decisions, separate from boolean transition fixtures.

Only supplied synthetic observations, declared units and immutable versions are
consumed. No fitted learner model, actual scheduler, external side effect or
authorization is inferred. A result is a bounded candidate decision.
"""
import copy, hashlib,json
def dig(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def int0(x):return type(x) is int and x>=0
def text(x):return isinstance(x,str) and bool(x.strip())
def p05(x):
 # Minute clock and synthetic fixed plan: last exposure, independent delayed recall,
 # next review candidate. Distinguish learning gap from retention.
 if x.get('unit')!='MINUTE' or x.get('learner_opt_in') is not True:return 'HOLD'
 a,b,t,g,budget,cost=[x.get(k) for k in ('first_exposure','last_exposure','test_time','next_gap','budget','cost')]
 if not all(int0(z) for z in (a,b,t,g,budget,cost)) or not a<b<t or g==0:return 'HOLD'
 if cost>budget:return 'DEFER_BUDGET'
 if x.get('generated') is not True or x.get('independent') is not True:return 'REQUEST_INDEPENDENT_RECALL'
 if x.get('target_version')!=x.get('test_version') or not text(x.get('target_version')):return 'HOLD'
 if x.get('arrangement') not in ('BLOCKED','MIXED') or type(x.get('category_cue')) is not bool or type(x.get('choice_required')) is not bool:return 'HOLD'
 # Arrangement does not determine cue or choice; keep explicit observations.
 return {'status':'REVIEW_WINDOW_CANDIDATE_ONLY','learning_gap':b-a,'retention_gap':t-b,'next_review_minute':t+g,'arrangement':x['arrangement'],'category_cue':x['category_cue'],'choice_required':x['choice_required']}
def p06(x):
 if not text(x.get('task_version')) or x.get('task_version')!=x.get('observed_task_version') or not text(x.get('scoring_version')) or x.get('scoring_version')!=x.get('expected_scoring_version'):return 'HOLD'
 if x.get('response_status') in ('MISSING','INVALID','NOT_ADMINISTERED'):return {'score':None,'category':x['response_status'],'update':'NONE'}
 if x.get('response_status')!='OBSERVED' or not text(x.get('key')) or not text(x.get('response')) or type(x.get('hint_used')) is not bool:return 'HOLD'
 score=int(x['key']==x['response'])
 if x['hint_used']:return {'score':score,'category':'ASSISTED','update':'REQUEST_INDEPENDENT_RETEST'}
 if score:return {'score':score,'category':'INDEPENDENT_TASK_ONLY','update':'NONE'}
 candidates=x.get('hypotheses');proof=x.get('discrimination')
 if not isinstance(candidates,list) or len(candidates)<2 or not all(text(z) for z in candidates) or len(set(candidates))!=len(candidates):return 'HOLD'
 if not isinstance(proof,dict) or set(proof)!=set(candidates) or any(type(z) is not bool for z in proof.values()):return {'score':0,'category':'ERROR','update':'REQUEST_DISCRIMINATING_OBSERVATION'}
 selected=[k for k,z in proof.items() if z]
 if len(selected)!=1:return {'score':0,'category':'ERROR','update':'KEEP_COMPETING_HYPOTHESES'}
 return {'score':0,'category':'ERROR','update':'SUGGEST_TARGETED_FEEDBACK_ONLY','hypothesis':selected[0]}
def p08(x):
 if x.get('exit') is True:return 'STOP'
 if x.get('exit') is not False or not int0(x.get('budget')) or not text(x.get('goal')) or x.get('authorized') is not True:return 'HOLD'
 if x.get('estimate_status') not in ('BOUNDED','UNKNOWN'):return 'HOLD'
 if x['estimate_status']=='UNKNOWN':return 'REQUEST_OBSERVATION'
 options=x.get('options')
 if not isinstance(options,list) or not options:return 'HOLD'
 seen=set();eligible=[];unknown=[]
 for a in options:
  if not isinstance(a,dict) or not text(a.get('id')) or a['id'] in seen or not int0(a.get('cost')) or not text(a.get('goal')):return 'HOLD'
  seen.add(a['id'])
  if a['goal']!=x['goal'] or a['cost']>x['budget'] or a.get('construct_preserved') is False or a.get('accessible') is False or a.get('authorized') is False:continue
  if any(a.get(k) is not True for k in ('construct_preserved','accessible','authorized')):unknown.append(a['id']);continue
  eligible.append(a['id'])
 if not eligible:return 'CLARIFY_UNKNOWN_FEASIBILITY' if unknown else 'DEFER_NO_FEASIBLE_ACTION'
 choice=x.get('learner_selection')
 if choice not in eligible:return {'status':'OFFER_FEASIBLE_CHOICES','eligible':eligible,'unknown':unknown}
 return {'status':'CANDIDATE_SELECTED_NOT_EXECUTED','id':choice}
MIN_DELAYED_INTERVAL_SECONDS=86400
MAX_UTC_EPOCH_SECONDS=253402300799

def _valid_subject_identity(value):
 if not isinstance(value,dict) or set(value)!={'kind','subject_id','identity_version'}:return False
 subject=value.get('subject_id')
 return (value.get('kind')=='LEARNER_SUBJECT'
         and isinstance(subject,str) and subject.strip()==subject
         and 0<len(subject)<=128 and not any(ord(c)<32 for c in subject)
         and value.get('identity_version')=='V1')

def p09(x):
 if not isinstance(x,dict) or not all(text(x.get(k)) for k in ('goal','scoring_version','trained_family','transfer_dimension')):return 'HOLD'
 obs=x.get('observations')
 if not isinstance(obs,list) or len(obs)!=3:return 'HOLD'
 expected_identity=None;clock_tuple=None;last_observed=-1;last_recorded=-1;seen=set();out={}
 for o,stage in zip(obs,('IMMEDIATE','DELAYED','TRANSFER')):
  if not isinstance(o,dict) or o.get('stage')!=stage or not text(o.get('id')) or o['id'].strip()!=o['id'] or o['id'] in seen:return 'HOLD'
  seen.add(o['id'])
  identity=o.get('learner_identity')
  if not _valid_subject_identity(identity):return 'HOLD'
  if expected_identity is None:expected_identity=copy.deepcopy(identity)
  elif identity!=expected_identity:return 'HOLD'
  clock=(o.get('time_basis'),o.get('time_unit'),o.get('recording_time_basis'),o.get('recording_time_unit'),o.get('clock_source_id'),o.get('recording_clock_source_id'))
  if (clock[0]!='UTC_EPOCH_SECONDS' or clock[1]!='SECOND'
      or clock[2]!='UTC_EPOCH_SECONDS' or clock[3]!='SECOND'
      or not text(clock[4]) or not text(clock[5])):return 'HOLD'
  if clock_tuple is None:clock_tuple=clock
  elif clock!=clock_tuple:return 'HOLD'
  observed=o.get('observed_at');recorded=o.get('recorded_at')
  if (not int0(observed) or not int0(recorded) or observed<=0 or recorded<=0
      or observed>MAX_UTC_EPOCH_SECONDS or recorded>MAX_UTC_EPOCH_SECONDS):return 'HOLD'
  # The two clocks are separate. Check event chronology only against event
  # timestamps and append/record chronology only against recording timestamps.
  if observed<=last_observed or recorded<last_recorded:return 'HOLD'
  last_observed=observed;last_recorded=recorded
  if (o.get('goal')!=x['goal'] or o.get('scoring_version')!=x['scoring_version']
      or o.get('independent') is not True or o.get('construct_match') is not True
      or o.get('scoring_version_match') is not True
      or not text(o.get('family')) or type(o.get('criteria_met')) is not bool):return 'HOLD'
  if stage=='TRANSFER':
   if (o['family']==x['trained_family'] or o.get('dimension')!=x['transfer_dimension']
       or o.get('new_task_family') is not True or o.get('transfer_dimension_declared') is not True):return 'HOLD'
  elif o['family']!=x['trained_family']:return 'HOLD'
  out[stage]=o['criteria_met']
 delay=obs[1]['observed_at']-obs[0]['observed_at']
 if delay<MIN_DELAYED_INTERVAL_SECONDS or obs[2]['observed_at']<=obs[1]['observed_at']:return 'HOLD'
 # Caller delay_positive/minimum_delay_seconds are deliberately ignored.
 subject=expected_identity['subject_id']
 return {'status':'THREE_TASK_OBSERVATIONS_ONLY','criteria':out,
         'learner_identity_binding':copy.deepcopy(expected_identity),
         'computed_same_learner_identity':True,
         'immediate_subject_id':subject,'delayed_subject_id':subject,'transfer_subject_id':subject,
         'time_basis':'UTC_EPOCH_SECONDS','time_unit':'SECOND',
         'recording_time_basis':'UTC_EPOCH_SECONDS','recording_time_unit':'SECOND',
         'clock_source_id':clock_tuple[4],'recording_clock_source_id':clock_tuple[5],
         'computed_delay_seconds':delay,'minimum_delay_seconds':MIN_DELAYED_INTERVAL_SECONDS,
         'computed_timestamp_order_valid':True,'computed_recording_order_valid':True}

def p10(x):
 # A trusted caller pins the checkpoint digest; the digest alone is not
 # authentication. This synthetic replay has no persistence/actual side effects.
 if x.get('exit') is True:return 'STOP'
 cp=x.get('checkpoint')
 if x.get('exit') is not False or not isinstance(cp,dict) or x.get('checkpoint_sha256')!=dig(cp) or x.get('resume_requested') is not True or x.get('authorized') is not True:return 'HOLD'
 if not text(cp.get('session')) or not text(cp.get('version')) or x.get('session')!=cp['session'] or x.get('version')!=cp['version'] or not int0(cp.get('remaining')) or not isinstance(cp.get('seen'),dict):return 'HOLD'
 seen=copy.deepcopy(cp['seen']);remaining=cp['remaining'];new=0
 if any(not text(k) or not isinstance(v,str) or len(v)!=64 or any(c not in '0123456789abcdef' for c in v) for k,v in seen.items()):return 'HOLD'
 events=x.get('events')
 if not isinstance(events,list) or len(events)>8:return 'HOLD'
 for e in events:
  if not isinstance(e,dict):return 'HOLD'
  if e.get('type')=='STOP':return 'STOP'
  if not text(e.get('id')) or e.get('version')!=cp['version'] or e.get('session')!=cp['session'] or e.get('type')!='OBSERVATION' or not int0(e.get('cost')) or not text(e.get('evidence_id')):return 'HOLD'
  h=dig(e)
  if e['id'] in seen:
   if seen[e['id']]!=h:return 'HOLD_CONFLICT'
   continue
  if e['cost']>remaining:return 'HOLD_BUDGET'
  remaining-=e['cost'];seen[e['id']]=h;new+=1
 return {'status':'SIMULATED_CHECKPOINT_ONLY','remaining':remaining,'new_events':new,'total_event_ids':len(seen)}
FUN={'P05':p05,'P06':p06,'P08':p08,'P09':p09,'P10':p10}
def fixture_rows():
 out=[]
 def add(o,x,y):out.append((o,{'scenario':'CONCRETE_FINITE',**copy.deepcopy(x)},copy.deepcopy(y)))
 o='P05';a=dict(unit='MINUTE',learner_opt_in=True,first_exposure=0,last_exposure=30,test_time=90,next_gap=60,budget=5,cost=3,generated=True,independent=True,target_version='V1',test_version='V1',arrangement='MIXED',category_cue=False,choice_required=True)
 y=dict(status='REVIEW_WINDOW_CANDIDATE_ONLY',learning_gap=30,retention_gap=60,next_review_minute=150,arrangement='MIXED',category_cue=False,choice_required=True)
 add(o,a,y);add(o,a|dict(arrangement='BLOCKED',category_cue=False),y|dict(arrangement='BLOCKED'))
 for k,b,z in [('test_time',20,'HOLD'),('last_exposure',True,'HOLD'),('next_gap',0,'HOLD'),('unit','DAY','HOLD'),('budget',2,'DEFER_BUDGET'),('independent',False,'REQUEST_INDEPENDENT_RECALL'),('generated',False,'REQUEST_INDEPENDENT_RECALL'),('test_version','V2','HOLD'),('category_cue',None,'HOLD')]:add(o,a|{k:b},z)
 o='P06';a=dict(task_version='T1',observed_task_version='T1',scoring_version='S1',expected_scoring_version='S1',response_status='OBSERVED',key='A',response='B',hint_used=False,hypotheses=['RULE','READING'],discrimination={'RULE':True,'READING':False})
 add(o,a,dict(score=0,category='ERROR',update='SUGGEST_TARGETED_FEEDBACK_ONLY',hypothesis='RULE'))
 add(o,a|dict(response='A'),dict(score=1,category='INDEPENDENT_TASK_ONLY',update='NONE'))
 add(o,a|dict(response='A',hint_used=True),dict(score=1,category='ASSISTED',update='REQUEST_INDEPENDENT_RETEST'))
 for status in ('MISSING','INVALID','NOT_ADMINISTERED'):add(o,a|dict(response_status=status,response=None),dict(score=None,category=status,update='NONE'))
 add(o,a|dict(discrimination={'RULE':True,'READING':True}),dict(score=0,category='ERROR',update='KEEP_COMPETING_HYPOTHESES'))
 add(o,a|dict(discrimination={'RULE':True,'READING':None}),dict(score=0,category='ERROR',update='REQUEST_DISCRIMINATING_OBSERVATION'))
 for k,b in [('observed_task_version','T2'),('expected_scoring_version','S2'),('hint_used',1),('hypotheses',['RULE','RULE'])]:add(o,a|{k:b},'HOLD')
 o='P08';a=dict(exit=False,budget=4,goal='G',authorized=True,estimate_status='BOUNDED',learner_selection='A',options=[dict(id='A',goal='G',cost=2,construct_preserved=True,accessible=True,authorized=True),dict(id='B',goal='G',cost=5,construct_preserved=True,accessible=True,authorized=True),dict(id='C',goal='G',cost=1,construct_preserved=True,accessible=None,authorized=True)])
 add(o,a,dict(status='CANDIDATE_SELECTED_NOT_EXECUTED',id='A'))
 add(o,a|dict(learner_selection='B'),dict(status='OFFER_FEASIBLE_CHOICES',eligible=['A'],unknown=['C']))
 add(o,a|dict(options=a['options'][1:]),'CLARIFY_UNKNOWN_FEASIBILITY');add(o,a|dict(options=[a['options'][1]]),'DEFER_NO_FEASIBLE_ACTION')
 add(o,a|dict(estimate_status='UNKNOWN'),'REQUEST_OBSERVATION');add(o,a|dict(exit=True,budget=None),'STOP')
 add(o,a|dict(options=a['options']+[a['options'][0]]),'HOLD');add(o,a|dict(budget=True),'HOLD')
 o='P09'
 identity={'kind':'LEARNER_SUBJECT','subject_id':'SUBJECT-01','identity_version':'V1'}
 def observation(stage,id,observed_at,family,criteria,dimension='CONTEXT',subject='SUBJECT-01',identity_version='V1',recorded_at=None):
  return dict(stage=stage,id=id,
              learner_identity={'kind':'LEARNER_SUBJECT','subject_id':subject,'identity_version':identity_version},
              time_basis='UTC_EPOCH_SECONDS',time_unit='SECOND',
              recording_time_basis='UTC_EPOCH_SECONDS',recording_time_unit='SECOND',
              clock_source_id='SYNTHETIC-UTC-CLOCK-01',recording_clock_source_id='SYNTHETIC-SERVER-UTC-01',
              observed_at=observed_at,recorded_at=observed_at+1 if recorded_at is None else recorded_at,
              goal='G',scoring_version='S1',independent=True,construct_match=True,scoring_version_match=True,
              family=family,criteria_met=criteria,dimension=dimension,
              new_task_family=stage=='TRANSFER',transfer_dimension_declared=stage=='TRANSFER')
 t0=1800000000
 base=dict(goal='G',scoring_version='S1',trained_family='F1',transfer_dimension='CONTEXT',
           observations=[observation('IMMEDIATE','OBS-I',t0,'F1',True),
                         observation('DELAYED','OBS-D',t0+86400,'F1',False),
                         observation('TRANSFER','OBS-T',t0+172800,'F2',True)])
 expected=dict(status='THREE_TASK_OBSERVATIONS_ONLY',criteria={'IMMEDIATE':True,'DELAYED':False,'TRANSFER':True},
               learner_identity_binding=identity,computed_same_learner_identity=True,
               immediate_subject_id='SUBJECT-01',delayed_subject_id='SUBJECT-01',transfer_subject_id='SUBJECT-01',
               time_basis='UTC_EPOCH_SECONDS',time_unit='SECOND',
               recording_time_basis='UTC_EPOCH_SECONDS',recording_time_unit='SECOND',
               clock_source_id='SYNTHETIC-UTC-CLOCK-01',recording_clock_source_id='SYNTHETIC-SERVER-UTC-01',
               computed_delay_seconds=86400,minimum_delay_seconds=86400,
               computed_timestamp_order_valid=True,computed_recording_order_valid=True)
 add(o,base,expected)
 # Caller delay_positive=false cannot veto an actually valid timestamp-derived interval.
 z=copy.deepcopy(base);z['delay_positive']=False;add(o,z,expected)
 for i in range(3):
  z=copy.deepcopy(base);z['observations'][i].pop('learner_identity');add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][1]['learner_identity']['subject_id']='SUBJECT-02';add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][2]['learner_identity']['subject_id']='SUBJECT-02';add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][2]['learner_identity']['identity_version']='V2';add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][0]['learner_identity']={'kind':'LEARNER_SUBJECT','subject_id':'','identity_version':'V1'};add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][1]['learner_identity']['kind']='GROUP';add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][1].pop('time_unit');add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][2]['time_unit']='MINUTE';add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][0].pop('time_basis');add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][1]['time_basis']='LOCAL_TIME';add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][1]['observed_at']=t0+86399;add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][1]['observed_at']=t0-1;add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][2]['observed_at']=z['observations'][1]['observed_at'];add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][1]['observed_at']=t0+86399;z['delay_positive']=True;add(o,z,'HOLD')
 # recorded_at is on its own clock: an epoch value below observed_at is not compared cross-clock.
 z=copy.deepcopy(base)
 z['observations'][0]['recorded_at']=t0-100
 z['observations'][1]['recorded_at']=t0+86399
 z['observations'][2]['recorded_at']=t0+172799
 add(o,z,expected)
 # Recording chronology is checked only within the recording-time stream.
 z=copy.deepcopy(base);z['observations'][2]['recorded_at']=z['observations'][1]['recorded_at']-1;add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][1]['observed_at']=True;add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][2]['clock_source_id']='OTHER-CLOCK';add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][2]['scoring_version']='S2';add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][2]['family']='F1';add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][2]['dimension']='OTHER';add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][1]['independent']=False;add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][1]['criteria_met']=1;add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][0]['observed_at']=-1;add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][0]['observed_at']=MAX_UTC_EPOCH_SECONDS+1;add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][0]['observed_at']='1800000000';add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][1]['recorded_at']=-1;add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][1]['recorded_at']=MAX_UTC_EPOCH_SECONDS+1;add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][1]['recorded_at']=1800000000.5;add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][2]['time_basis']='LOCAL_TIME';add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][1].pop('recording_time_unit');add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][1]['recording_time_unit']='MILLISECOND';add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][0].pop('recording_time_basis');add(o,z,'HOLD')
 z=copy.deepcopy(base);z['observations'][2]['recording_time_basis']='LOCAL_TIME';add(o,z,'HOLD')
 o='P10';e=dict(id='E1',version='V1',session='S1',type='OBSERVATION',cost=2,evidence_id='O1');f=e|dict(id='E2',evidence_id='O2')
 cp=dict(session='S1',version='V1',remaining=3,seen={'E1':dig(e)})
 a=dict(exit=False,checkpoint=cp,checkpoint_sha256=dig(cp),resume_requested=True,authorized=True,session='S1',version='V1',events=[e,f])
 add(o,a,dict(status='SIMULATED_CHECKPOINT_ONLY',remaining=1,new_events=1,total_event_ids=2))
 add(o,a|dict(events=[e]),dict(status='SIMULATED_CHECKPOINT_ONLY',remaining=3,new_events=0,total_event_ids=1))
 add(o,a|dict(events=[e|dict(cost=1)]),'HOLD_CONFLICT');add(o,a|dict(events=[f|dict(cost=4)]),'HOLD_BUDGET')
 add(o,a|dict(events=[f,{'type':'STOP'}]),'STOP')
 for k,b in [('version','V2'),('checkpoint_sha256','bad'),('resume_requested',False),('authorized',False),('events',[f|dict(cost=True)])]:add(o,a|{k:b},'HOLD')
 return out
def evaluate(im,flow,x,owner,load_record):
 # Verify actual SQL-read process and canonical conditions are present. The
 # concrete decision function is a restricted companion, not a flow engine.
 assert flow['effect']=='TEMPLATE_ONLY' and flow['unknown_terminal']=='HOLD'
 assert flow['claim_refs'] and flow['steps']
 for t in flow['transitions']:
  if t['condition_ref'] is not None:
   g=load_record(im,t['condition_ref']);assert g['unknown']=='HOLD' and g['clauses']
 for r in flow['claim_refs']:
  c=load_record(im,r);assert c['statement']
 return FUN[owner](x)
