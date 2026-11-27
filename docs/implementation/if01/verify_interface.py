#!/usr/bin/env python3
"""IF01 finite shared object / typed reference contract witness, not a runtime engine."""
import json,copy,hashlib,pathlib,collections
import jsonschema
P=pathlib.Path(__file__).resolve().parent
ROOT=P.parents[2];DB=P.parent/'db01'
def load(p):return json.loads(p.read_text())
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(o):return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def digest(o):return hashlib.sha256(canon(o)).hexdigest()
S=load(DB/'canonical.schema.json');M=load(DB/'mapping-contract.json');D=S['$defs'];K=set(M['record_tables'])
# Every record reference field is assigned a finite set of allowed target kinds.
all_targets=sorted(K-{'Source','Locator','Case','Validation','Relation'})
construct=['Competency','KnowledgeType','SkillType']
obs=['ObservationSpec','TaskSpec','Validation']
entities=['Element','HanCharacter','Reading','Lexeme','Sense','Construction','Standard','StandardBand','SourceMembership','KnowledgeType','SkillType','Competency']
common=['Goal','Competency','KnowledgeType','SkillType','LearningObject','Resource','Modality','Activity','Interaction','Role','Environment','ObservationSpec','StateDimension','ConditionSpec','PolicySpec','TaskSpec','Mode','FlowSpec','CompositionSpec','EvaluationProtocol']
rules={
 'Locator':{'source_ref':['Source']},
 'Claim':{'locator_refs/*':['Locator'],'case_refs/*':['Case'],'validation_refs/*':['Validation'],'supersedes_refs/*':['Claim'],'refinement_of':['Claim']},
 'Relation':{'from_ref':all_targets+['Locator','Case'],'to_ref':all_targets+['Claim'],'claim_refs/*':['Claim'],'condition_refs/*':['ConditionSpec']},
 'Case':{'target_refs/*':all_targets+['Claim','Locator','Relation'],'oracle_ref':['Validation']},
 'Validation':{'target_refs/*':all_targets+['Claim','Locator','Relation'],'case_refs/*':['Case']},
 'Topic':{'parent_ref':['Topic']},'Requirement':{'topic_ref':['Topic']},
 'Lexeme':{'form_refs/*':['HanCharacter','Element'],'reading_refs/*':['Reading']},
 'Sense':{'lexeme_ref':['Lexeme']},'Construction':{'condition_refs/*':['ConditionSpec']},
 'Standard':{'source_refs/*':['Source']},'StandardBand':{'standard_ref':['Standard']},
 'SourceMembership':{'standard_ref':['Standard'],'band_ref':['StandardBand'],'source_ref':['Source'],'semantic_refs/*':entities},
 'Goal':{'construct_ref':construct,'success_evidence_refs/*':obs},
 'Competency':{'evidence_refs/*':obs+['Claim']},
 'LearningObject':{'target_refs/*':entities,'component_refs/*':['LearningObject']},
 'Resource':{'modality_refs/*':['Modality']},
 'ObservationSpec':{'construct_ref':construct},
 'StateDimension':{'construct_ref':construct,'observation_refs/*':['ObservationSpec'],'estimator_ref':['ModelSpec']},
 'Activity':{'goal_refs/*':['Goal'],'object_refs/*':['LearningObject'],'resource_refs/*':['Resource'],'role_refs/*':['Role'],'observation_refs/*':['ObservationSpec']},
 'Interaction':{'activity_ref':['Activity'],'role_refs/*':['Role'],'observation_refs/*':['ObservationSpec']},
 'TaskSpec':{'construct_ref':construct,'object_refs/*':['LearningObject'],'observation_refs/*':['ObservationSpec']},
 'Mode':{'goal_refs/*':['Goal'],'activity_refs/*':['Activity'],'role_refs/*':['Role'],'selection_condition_refs/*':['ConditionSpec']},
 'PolicySpec':{'rules/*/condition_ref':['ConditionSpec']},
 'FlowSpec':{'steps/*/activity_ref':['Activity'],'transitions/*/condition_ref':['ConditionSpec']},
 'CompositionSpec':{'input_refs/*':all_targets,'output_refs/*':all_targets,'condition_refs/*':['ConditionSpec'],'alternative_refs/*':all_targets,'evidence_refs/*':['Claim','Case','Validation','ObservationSpec']},
 'EvaluationProtocol':{'goal_ref':['Goal'],'intervention_ref':['Activity','FlowSpec','PolicySpec'],'comparator_ref':['Activity','FlowSpec','PolicySpec'],'measurement_refs/*':obs}}
for k in K:
 if 'claim_refs' in D[k]['properties']:rules.setdefault(k,{})['claim_refs/*']=['Claim']
def refpaths(s,path=''):
 if s.get('$ref')=='#/$defs/ref':return {path}
 if '$ref' in s:return refpaths(D[s['$ref'].split('/')[-1]],path)
 out=set()
 for k,v in s.get('properties',{}).items():out|=refpaths(v,path+'/'+k if path else k)
 if 'items' in s:out|=refpaths(s['items'],path+'/*')
 for v in s.get('oneOf',[]):out|=refpaths(v,path)
 return out
# expr is recursive but contains no typed references; avoid recursion in refpath scanner.
def safe_refpaths(s,path='',seen=frozenset()):
 if s.get('$ref')=='#/$defs/ref':return {path}
 if '$ref' in s:
  k=s['$ref'].split('/')[-1]
  return set() if k in seen else safe_refpaths(D[k],path,seen|{k})
 out=set()
 for k,v in s.get('properties',{}).items():out|=safe_refpaths(v,path+'/'+k if path else k,seen)
 if 'items' in s:out|=safe_refpaths(s['items'],path+'/*',seen)
 for v in s.get('oneOf',[]):out|=safe_refpaths(v,path,seen)
 return out
for k in K:
 expected=safe_refpaths(D[k]);actual=set(rules.get(k,{}))
 assert expected==actual,(k,expected-actual,actual-expected)
 assert all(set(v)<=K for v in rules.get(k,{}).values())
receipt_paths={'S01':'evidence/tasks/S01/S01-FORMAL-01.json','DB01':'evidence/tasks/DB01/DB01-FORMAL-01.json','G01':'evidence/tasks/G01/G01-FORMAL-01.json'}
inputs={}
for k,p in receipt_paths.items():
 x=load(ROOT/p);assert x['state'] in ('CANDIDATE_READY','GATE_ACCEPTED') and x['task_id']==k
 for o in x['output']:assert sha(ROOT/o['path'])==o['sha256']
 assert digest({'input':x['input'],'output':x['output']})==x['content_digest']
 inputs[k]={'receipt_id':x['receipt_id'],'content_digest':x['content_digest'],'version':x['version'],'path':p,'sha256':sha(ROOT/p)}
dag=load(ROOT/'docs/implementation/task-dag.json');owners={k['id']:k for k in dag['tasks'] if len(k['id'])==3 and k['id'][0] in 'KHPAFE' and k['id'][1:].isdigit()}
assert len(owners)==53
view=load(ROOT/'docs/drafts/s01/process-view-requirements.json')['views']
# View object routes are candidate design, not a replacement for original 108 requirements.
routes={'P01':['Mode','Goal','Role','ConditionSpec'],'P02':['Goal','Competency','ObservationSpec','Activity'],'P03':['Activity','TaskSpec','LearningObject','Interaction'],'P04':['FlowSpec','Activity','ConditionSpec'],'P05':['FlowSpec','PolicySpec','TaskSpec','ObservationSpec'],'P06':['ObservationSpec','PolicySpec','TaskSpec','Interaction'],'P07':['Mode','PolicySpec','Role','ConditionSpec'],'P08':['StateDimension','PolicySpec','Activity','ConditionSpec'],'P09':['TaskSpec','ObservationSpec','Validation','Goal'],'P10':['FlowSpec','Role','Environment','StateDimension'],'F01':['Goal','Competency','ObservationSpec'],'F02':['LearningObject','KnowledgeType','SkillType'],'F03':['Resource','Modality','ConditionSpec'],'F04':['Interaction','Activity','Role','ObservationSpec'],'F05':['ObservationSpec','StateDimension','ModelSpec'],'F06':['StateDimension','PolicySpec','TaskSpec'],'F07':['Role','Environment','Modality'],'F08':['TaskSpec','Goal','ObservationSpec'],'A01':['CompositionSpec','Goal','Competency','LearningObject'],'A02':['CompositionSpec','LearningObject','TaskSpec','ObservationSpec'],'A03':['CompositionSpec','ObservationSpec','StateDimension'],'A04':['CompositionSpec','StateDimension','PolicySpec','Activity'],'A05':['CompositionSpec','TaskSpec','ObservationSpec'],'A06':['CompositionSpec','Resource','TaskSpec','Validation'],'A07':['CompositionSpec','Environment','Role','PolicySpec'],'A08':['CompositionSpec','EvaluationProtocol','Validation'],'E01':['EvaluationProtocol','Goal','ObservationSpec','Validation']}
assert set(routes)=={v['id'] for v in view}
contract={'status':'IF01_SHARED_CANDIDATE_NOT_G04_FREEZE','schema_version':M['schema_version'],'interface_version':'learn-kg-if01-1','inputs':inputs,'schema_sha256':sha(DB/'canonical.schema.json'),'mapping_sha256':sha(DB/'mapping-contract.json'),'shared_objects':common,'endpoint_rules':rules,'relation_endpoints':M['relations'],'view_routes':[{'owner':v['id'],'required_scope_ids':[r['id'] for r in v['requirements']],'candidate_object_kinds':routes[v['id']],'professional_topic_refs':v['professional_topic_refs'],'task_dependencies':owners[v['id']]['depends_on'],'status':'CANDIDATE_INTERFACE_ONLY'} for v in view],
 'owner_policy':{'professional_owners':sorted(k for k in owners if k[0] in 'KH'),'view_owners':sorted(routes),'evidence_custodian':'EVIDENCE','future_subject':'explicit separate domain/version; no invented qualification','stable_identity':'package_id, version, stable_id unique within a package; expected kind and owner checked separately. Reference version and direct dependency manifest digest must match current manifest. No inference from name or bare ID. Preserve original D3 owner.'},
 'semantic_boundaries':{'goal':'construct and success evidence required; standard membership not proof of capability','knowledge_skill':'knowledge content and observable skill distinct; type-level reuse, not copy subject facts','object':'part membership does not imply prerequisite; granularity and conditions explicit','resource':'modality not equivalence, rights and capability applicability checked; descriptions not content authority','observation':'observation specification distinct from actual event, score, estimate, self-report; missing not zero, prompt/assistance and version matter','state':'state dimension is definition only; estimates require specific model/evidence/time/uncertainty; no individual data in package','roles':'permission requirement is not actual permission; only downstream authorized execution may use it','policy':'advice only, no implicit state writes; distinct priority and bounded unknown fallback; budget/learner refusal cannot be overridden','flow':'entry, explicit event transition, guard, priority, unknown/stop/pause terminal, bounded event/attempt budgets, checkpoints; parallel joins have explicit member IDs/mode/resume policy; definition only, runtime implementation/independent CQ later','composition':'specific versioned inputs and output types, assumptions/alternatives/negative boundaries, never infer qualification from input type alone; scope/subject/construct/measurement bindings checked','evaluation':'comparison/intervention and estimand, followup, uncertainty, independent approval; no automatic training/promotion or actual learner data','publication':'candidate research use only, rights HOLD and no release; immutable text manifest and typed receipt; no persistent SQLite'},
 'limits':['Interface baseline gives required record shapes and reference endpoints; owner modules refine domain-specific knowledge and versioned semantic extensions. Not final ontology or runtime engine.','Finite fixtures are original synthetic demonstrations, not actual HSK evidence or second-subject qualification/CQ25. No real observations or authorization.']}
save(P/'interface-contract.json',contract)
# Finite authored fixture: one core shared vocabulary, two domain-specific object contexts, process definition in separate package.
version='if01-synthetic-1'
def rr(pkg,k,id,owner):return {'package_id':pkg,'version':version,'kind':k,'stable_id':id,'owner':owner}
def key(r):return (r['package_id'],r['version'],r['stable_id'])
def rbase(k,id,o):
 return {'kind':k,'stable_id':id,'owner':o,'status':'CANDIDATE','conditions':['SYNTHETIC_INTERFACE_FIXTURE_ONLY'],'negative_boundary':'No empirical result, qualification or learner identity is asserted.','provenance':[{'source_path':'docs/implementation/if01/interface-contract.json','source_sha256':sha(P/'interface-contract.json'),'json_pointer':'/semantic_boundaries','source_status':'ORIGINAL_SYNTHETIC_FIXTURE'}]}
pkgs={}
def package(name,owners,deps):
 pkgs[name]={'owners':owners,'deps':deps,'records':[]}
def add(p,k,id,o,**kw):
 rec=rbase(k,id,o)|kw;pkgs[p]['records'].append(rec);return rr(p,k,id,o)
def claim(p,id,o,text):
 return add(p,'Claim',id,o,topic_id=o,requirement_id=o+':fixture',claim_type='ENGINEERING_POLICY',statement=text,source_status='ORIGINAL_SYNTHETIC_FIXTURE',locator_refs=[],case_refs=[],validation_refs=[],supersedes_refs=[],refinement_of=None)
core='learning-core';proc='learning-process'
package(core,['K03','K04','K06','K07','K09','K10','K13','K16'],[])
c=claim(core,'core:claim','K03','Synthetic object type must not be equated with a learner state.')
kt=add(core,'KnowledgeType','core:kt','K03',claim_refs=[c],label='domain object',definition='Typed domain content')
st=add(core,'SkillType','core:skill','K04',claim_refs=[c],label='independent discrimination',performance_boundary='Requires an independent specified task')
mod=add(core,'Modality','core:modality','K16',claim_refs=[c],label='written',capability_requirements=['read written prompt'],not_equivalent_to=['spoken production'])
role=add(core,'Role','core:role','K13',claim_refs=[c],label='learner',capability_requirements=['respond or refuse'],permission_requirements=['actual consent resolved externally'])
env=add(core,'Environment','core:env','K13',claim_refs=[c],constraints=['no actual learner data'],capabilities=['display text'])
cond=add(core,'ConditionSpec','core:condition','K06',claim_refs=[c],clauses=[{'field':'input_complete','op':'EQ','value':True}],combination='ALL',unknown='HOLD')
contexts={}
for p,o,tag,label in [('chinese','H03','zh','synthetic written word discrimination'),('other-subject','MATH01','ma','synthetic equal-unit fraction discrimination')]:
 package(p,[o],[core])
 cl=claim(p,tag+':claim',o,'Only synthetic typed object comparison; no domain result qualification.')
 ent=add(p,'Element',tag+':element',o,topic_id=o,element_type='SYNTHETIC_SUBJECT_OBJECT',label=label,definition='A separately scoped fixture object',claim_refs=[cl])
 cp=rr(p,'Competency',tag+':competency',o);ob=rr(p,'ObservationSpec',tag+':obs',o)
 add(p,'Competency',tag+':competency',o,claim_refs=[cl],dimensions=['independent discrimination'],evidence_refs=[ob])
 add(p,'ObservationSpec',tag+':obs',o,claim_refs=[cl],construct_ref=cp,method='Independent fixture response; assistance must be recorded separately',unit='binary response under specified rubric',independence_requirement='No prompt giving answer',missing='UNKNOWN_NOT_ZERO')
 goal=add(p,'Goal',tag+':goal',o,claim_refs=[cl],construct_ref=cp,success_evidence_refs=[ob],scope=tag+' only')
 obj=add(p,'LearningObject',tag+':object',o,claim_refs=[cl],target_refs=[ent],component_refs=[],granularity='one fixture item')
 res=add(p,'Resource',tag+':resource',o,claim_refs=[cl],modality_refs=[mod],rights='HOLD',accessibility=['written fixture only'],resource_identity=tag+':synthetic-prompt')
 task=add(p,'TaskSpec',tag+':task',o,claim_refs=[cl],construct_ref=cp,object_refs=[obj],prompt=label,scoring_spec='Expected response specified by the future fixture oracle; no score asserted',observation_refs=[ob],independence_requirement='unassisted')
 contexts[tag]={'goal':goal,'object':obj,'resource':res,'task':task,'obs':ob,'construct':cp}
package(proc,['P01','P03','P04','P06','P08','F04','F05','A02','E01'],[core,'chinese','other-subject'])
pc=claim(proc,'p:claim','P04','A bounded candidate flow must stop or hold on missing evidence.')
for tag,z in contexts.items():
 a=add(proc,'Activity',tag+':activity','P03',claim_refs=[pc],goal_refs=[z['goal']],object_refs=[z['object']],resource_refs=[z['resource']],role_refs=[role],observation_refs=[z['obs']],budget=2,stop_condition='learner STOP or budget exhausted')
 intr=add(proc,'Interaction',tag+':interaction','F04',claim_refs=[pc],activity_ref=a,role_refs=[role],input_contract='scoped task response',output_contract='observation reference or HOLD',observation_refs=[z['obs']],assistance_policy='separate assistance from independent performance')
 sd=add(proc,'StateDimension',tag+':state','F05',claim_refs=[pc],construct_ref=z['construct'],observation_refs=[z['obs']],estimator_ref=None,uncertainty='no estimate or calibration asserted',effect='DEFINITION_ONLY')
 mode=add(proc,'Mode',tag+':mode','P01',claim_refs=[pc],goal_refs=[z['goal']],activity_refs=[a],role_refs=[role],selection_condition_refs=[cond],learner_choice=True,switch_condition='learner requests switch or condition no longer holds')
 policy=add(proc,'PolicySpec',tag+':policy','P06',claim_refs=[pc],policy_type='FEEDBACK',rules=[{'condition_ref':cond,'action':'REQUEST_OBSERVATION','reason':'obtain separate evidence','priority':0}],unknown_action='CLARIFY',effect='ADVICE_ONLY')
 fl=add(proc,'FlowSpec',tag+':flow','P04',claim_refs=[pc],entry='s1',steps=[{'id':'s1','activity_ref':a,'max_attempts':2,'checkpoint':True}],transitions=[{'from_step':'s1','to_step':t,'event':e,'condition_ref':cond if e=='COMPLETE' else None,'priority':0,'consumes_budget':e=='COMPLETE'} for e,t in [('COMPLETE','done'),('UNKNOWN','hold'),('STOP','stop'),('PAUSE','pause'),('BUDGET_EXHAUSTED','stop')]],terminals=[{'id':i,'outcome':o} for i,o in [('done','COMPLETE'),('hold','HOLD'),('stop','STOP'),('pause','PAUSE')]],max_events=4,unknown_terminal='hold',stop_terminal='stop',parallel_joins=[],effect='TEMPLATE_ONLY')
 comp=add(proc,'CompositionSpec',tag+':composition','A02',claim_refs=[pc],view_id='A02',input_refs=[z['object'],z['task']],output_refs=[z['obs']],condition_refs=[cond],alternative_refs=[],failure_policy='HOLD if context or typed reference does not match',evidence_refs=[pc],effect='CANDIDATE_DECISION_ONLY')
 z['activity']=a;z['flow']=fl;z['state']=sd;z['composition']=comp
# An explicitly separate comparator on the same construct; no effect data.
z=contexts['zh']
cmp=add(proc,'Activity','zh:comparator','P03',claim_refs=[pc],goal_refs=[z['goal']],object_refs=[z['object']],resource_refs=[z['resource']],role_refs=[role],observation_refs=[z['obs']],budget=2,stop_condition='same stop contract')
add(proc,'EvaluationProtocol','zh:protocol','E01',claim_refs=[pc],goal_ref=z['goal'],intervention_ref=z['activity'],comparator_ref=cmp,measurement_refs=[z['obs']],estimand='synthetic difference in specified independent response; no estimate',population_scope='no actual learner population',followup='design only',uncertainty='not evaluated',approval_required=True,effect='NO_DIRECT_KNOWLEDGE_WRITE')
for p,q in pkgs.items():
 m={'package_id':p,'version':version,'owners':q['owners'],'status':'CANDIDATE','rights':'HOLD','record_sha256':digest(q['records']),'dependencies':[{'package_id':d,'version':version,'manifest_sha256':pkgs[d]['manifest_sha256']} for d in q['deps']]}
 q['manifest']=m;q['manifest_sha256']=digest(m)
fixture={'status':'SYNTHETIC_ONLY','packages':pkgs,'contexts':contexts}
save(P/'interface-fixtures.json',fixture)
validators={k:jsonschema.Draft202012Validator({'$defs':D,'$ref':'#/$defs/'+k}) for k in K}
def need(ok,msg):
 if not ok:raise ValueError(msg)
def values(v,path):
 if not path:return [v] if v is not None else []
 h,*rest=path
 if h=='*':return [x for a in v for x in values(a,rest)]
 return values(v.get(h),rest) if isinstance(v,dict) and h in v else []
def validate(f):
 pk=f['packages'];registry={};deps={}
 for p,q in pk.items():
  m=q['manifest'];need(digest(m)==q['manifest_sha256'] and digest(q['records'])==m['record_sha256'],'manifest digest')
  need(m['package_id']==p and m['version']==version and m['status']=='CANDIDATE' and m['rights']=='HOLD','candidate manifest scope')
  deps[p]={d['package_id'] for d in m['dependencies']};need(len(deps[p])==len(m['dependencies']),'duplicate dependency')
  for d in m['dependencies']:
   need(d['package_id'] in pk and d['version']==version and d['manifest_sha256']==pk[d['package_id']]['manifest_sha256'],'dependency digest')
  for v in q['records']:
   validators[v['kind']].validate(v);need(v['owner'] in m['owners'] and v['status']=='CANDIDATE','owner/status')
   k=(p,version,v['stable_id']);need(k not in registry,'duplicate stable id');registry[k]=v
 # Manifest dependency cycles disallowed.
 done=set()
 while len(done)<len(pk):
  ready={p for p,d in deps.items() if p not in done and d<=done};need(bool(ready),'cycle');done|=ready
 def resolve(p,r,allowed):
  need(r['version']==version and (r['package_id']==p or r['package_id'] in deps[p]),'undeclared/stale reference')
  v=registry.get(key(r));need(v is not None and v['kind']==r['kind'] and v['owner']==r['owner'] and r['kind'] in allowed,'identity/type/owner')
  return v
 count=0
 for (p,_,id),v in registry.items():
  for field,allowed in rules.get(v['kind'],{}).items():
   for r in values(v,field.split('/')):resolve(p,r,allowed);count+=1
  if v['kind']=='Relation':
   need([v['from_ref']['kind'],v['to_ref']['kind']] in M['relations'].get(v['relation_type'],[]),'relation direction')
  if v['kind']=='FlowSpec':
   steps={s['id']:s for s in v['steps']};terms={t['id']:t['outcome'] for t in v['terminals']}
   need(len(steps)==len(v['steps']) and len(terms)==len(v['terminals']) and not set(steps)&set(terms) and v['entry'] in steps,'flow identity')
   need(terms.get(v['unknown_terminal'])=='HOLD' and terms.get(v['stop_terminal'])=='STOP','flow stop/unknown')
   seen=set()
   for t in v['transitions']:
    k=(t['from_step'],t['event'],t['priority']);need(k not in seen,'ambiguous priority');seen.add(k)
    need(t['from_step'] in steps and t['to_step'] in set(steps)|set(terms),'flow endpoint')
   for id in steps:
    for ev in ('UNKNOWN','STOP','PAUSE','BUDGET_EXHAUSTED'):
     matches=[t for t in v['transitions'] if t['from_step']==id and t['event']==ev]
     need(len(matches)==1 and matches[0]['condition_ref'] is None and terms.get(matches[0]['to_step'])=={'UNKNOWN':'HOLD','STOP':'STOP','PAUSE':'PAUSE','BUDGET_EXHAUSTED':'STOP'}[ev],'mandatory unconditional terminal')
   for j in v['parallel_joins']:need(set(j['members'])<=set(steps) and j['id'] not in steps and j['resume_policy'].strip(),'join member')
  if v['kind']=='PolicySpec':need(len({r['priority'] for r in v['rules']})==len(v['rules']),'policy priority')
  if v['kind']=='EvaluationProtocol':need(key(v['intervention_ref'])!=key(v['comparator_ref']),'comparator identity')
 # Match contexts against exact construct and subject; type match alone is insufficient.
 for tag,z in f['contexts'].items():
  expected={'zh':'chinese','ma':'other-subject'}[tag]
  need(all(z[n]['package_id']==expected for n in ('goal','object','resource','task','obs','construct')),'subject context')
  goal=resolve(expected,z['goal'],['Goal']);task=resolve(expected,z['task'],['TaskSpec']);obs=resolve(expected,z['obs'],['ObservationSpec'])
  need(goal['construct_ref']==task['construct_ref']==obs['construct_ref']==z['construct'],'construct mismatch')
  need(z['obs'] in goal['success_evidence_refs'] and z['obs'] in task['observation_refs'] and z['object'] in task['object_refs'],'observation/object binding')
  act=resolve(proc,z['activity'],['Activity']);state=resolve(proc,z['state'],['StateDimension']);comp=resolve(proc,z['composition'],['CompositionSpec'])
  need(act['goal_refs']==[z['goal']] and act['object_refs']==[z['object']] and act['observation_refs']==[z['obs']] and state['construct_ref']==z['construct'] and state['observation_refs']==[z['obs']] and comp['input_refs']==[z['object'],z['task']] and comp['output_refs']==[z['obs']],'cross-context binding')
 return {'records':len(registry),'typed_refs':count,'kinds':sorted({v['kind'] for v in registry.values()}),'contexts':len(f['contexts'])}
# Rehash deliberate mutations to distinguish semantic rejection from digest rejection.
def rehash(f):
 for p,q in f['packages'].items():
  q['manifest']['record_sha256']=digest(q['records'])
  for d in q['manifest']['dependencies']:d['manifest_sha256']=f['packages'][d['package_id']]['manifest_sha256']
  q['manifest_sha256']=digest(q['manifest'])
def rec(f,id):return next(v for q in f['packages'].values() for v in q['records'] if v['stable_id']==id)
result=validate(fixture)
negative=[]
def reject(name,fn,reh=True):
 f=copy.deepcopy(fixture);fn(f)
 if reh:rehash(f)
 try:validate(f)
 except (ValueError,KeyError,jsonschema.ValidationError) as e:negative.append({'name':name,'rejection':str(e).splitlines()[0][:160]})
 else:raise AssertionError(name)
reject('wrong_kind',lambda f:rec(f,'zh:goal')['construct_ref'].update(kind='LearningObject'))
reject('wrong_owner',lambda f:rec(f,'zh:goal')['construct_ref'].update(owner='H07'))
reject('stale_version',lambda f:rec(f,'zh:goal')['construct_ref'].update(version='old'))
reject('unknown_id',lambda f:rec(f,'zh:goal')['construct_ref'].update(stable_id='missing'))
reject('undeclared_dependency',lambda f:rec(f,'zh:goal').update(construct_ref=f['contexts']['ma']['construct']))
reject('duplicate_stable_id',lambda f:f['packages']['chinese']['records'].append(copy.deepcopy(rec(f,'zh:goal'))))
reject('mixed_subject_same_kind',lambda f:f['contexts']['zh'].update(obs=f['contexts']['ma']['obs']))
reject('mixed_observation_binding',lambda f:rec(f,'zh:activity').update(observation_refs=[f['contexts']['ma']['obs']]))
reject('missing_stop',lambda f:rec(f,'zh:flow')['transitions'].pop(2))
reject('unknown_as_success',lambda f:rec(f,'zh:flow').update(unknown_terminal='done'))
reject('ambiguous_priority',lambda f:rec(f,'zh:flow')['transitions'].append(dict(rec(f,'zh:flow')['transitions'][0],to_step='stop')))
reject('wrong_transition_target',lambda f:rec(f,'zh:flow')['transitions'][0].update(to_step='missing'))
reject('zero_budget',lambda f:rec(f,'zh:flow').update(max_events=0))
reject('missing_permission_requirement',lambda f:rec(f,'core:role').update(permission_requirements=[]))
reject('same_comparator',lambda f:rec(f,'zh:protocol').update(comparator_ref=f['contexts']['zh']['activity']))
reject('digest_tamper',lambda f:rec(f,'zh:goal').update(scope='other'),False)
reject('candidate_release',lambda f:f['packages']['chinese']['manifest'].update(status='APPROVED'))
receipt={'status':'IF01_FINITE_INTERFACE_CANDIDATE_VALIDATION','contract_sha256':sha(P/'interface-contract.json'),'fixtures_sha256':sha(P/'interface-fixtures.json'),'shared_objects':len(common),'all_reference_field_paths':sum(len(x) for x in rules.values()),'schema_kind_count':len(K),'views':len(routes),'view_requirements':sum(len(v['requirements']) for v in view),'positive':result,'negative_rejected':negative,'limits':['Static finite synthetic examples, no actual learner, authorizations, runtime flow/guard/parallel execution, source or scientific qualification.','Same author fixture; actual subject and second subject qualification/CQ/LC not run. No SQLite file, no DB02 importer.','Shared endpoint constraints cover every typed ref field path in current DB01 schema; domain-specific semantic rules, professional evidence and independently fixed oracle remain owner tasks.']}
save(P/'validation-receipt.json',receipt);print(json.dumps(receipt,ensure_ascii=False))
