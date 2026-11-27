#!/usr/bin/env python3
"""Build DB01 candidate canonical record schemas and deterministic table mapping."""
import json
from pathlib import Path
P=Path(__file__).resolve().parent
def save(n,d):(P/n).write_text(json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
def obj(fields,optional=()):
 return {'type':'object','additionalProperties':False,'required':[k for k in fields if k not in optional],'properties':fields}
def arr(s,min=0):return {'type':'array','items':s,'minItems':min,'uniqueItems':True}
def enum(*v):return {'enum':list(v)}
def ref(name):return {'$ref':'#/$defs/'+name}
S={'type':'string','minLength':1,'pattern':'\\S'}; ID={'type':'string','pattern':'^[A-Za-z0-9][A-Za-z0-9._:-]*$'}
I={'type':'integer','minimum':0}; POS={'type':'integer','minimum':1}; B={'type':'boolean'}; H={'type':'string','pattern':'^[a-f0-9]{64}$'}
N={'type':'number'}; NULL={'type':'null'}
def nullable(s):return {'oneOf':[s,NULL]}
T=arr(S,1); TS=arr(S)
defs={'ref':obj({'package_id':ID,'version':ID,'kind':ID,'stable_id':ID,'owner':ID}),
 'provenance':obj({'source_path':S,'source_sha256':H,'json_pointer':S,'source_status':S}),
 'scalar':{'type':['string','number','boolean','null']}}
R=ref('ref'); RS=arr(R); R1=arr(R,1)
def record(k,fields,optional=()):
 base={'kind':{'const':k},'stable_id':ID,'owner':ID,'status':enum('CANDIDATE','HOLD','HISTORICAL','QUALIFIED'),'conditions':T,'negative_boundary':S,'provenance':arr(ref('provenance'),1)}
 defs[k]=obj(base|fields,optional)
# Distinct claim, source, locator, case, validation, and element records.
record('Source',{'title':S,'identifier':S,'access':S,'rights':enum('HOLD','PRIVATE_ONLY','PUBLIC_AUTHORIZED'),'qualification':enum('NOT_RUN','QUALIFIED','HOLD'),'bibliography':S,'recorded_locator':nullable(S),'recorded_rights':S})
record('Locator',{'source_ref':R,'location':nullable(S),'attribution':enum('RECORDED_NOT_REVERIFIED','MISSING','MULTI_SOURCE_HOLD','VERIFIED'),'verification':S})
record('Claim',{'topic_id':ID,'requirement_id':ID,'claim_type':S,'statement':S,'source_status':S,'locator_refs':RS,'case_refs':RS,'validation_refs':RS,'supersedes_refs':RS,'refinement_of':nullable(R)})
record('Element',{'topic_id':ID,'element_type':S,'label':S,'definition':S,'claim_refs':R1})
record('Relation',{'relation_type':ID,'from_ref':R,'to_ref':R,'claim_refs':R1,'condition_refs':RS,'direction':{'const':'DIRECTED'},'automatic_transitive':{'const':False},'automatic_inverse':{'const':False}})
record('Case',{'target_refs':R1,'view':enum('FORWARD','REVERSE','INTERVENTION','COUNTEREXAMPLE','COMPOSITION'),'input_spec':S,'expected_spec':S,'oracle_ref':nullable(R),'actual_status':enum('NOT_RUN','RECORDED_BUILDER_ONLY','HOLD','INDEPENDENTLY_CHECKED')})
record('Validation',{'target_refs':R1,'case_refs':R1,'method':S,'oracle_identity':nullable(S),'input_digest':nullable(H),'result_digest':nullable(H),'run_status':enum('NOT_RUN','HOLD','BUILDER_RUN','INDEPENDENT_RUN')})
record('Topic',{'label':S,'depth':{'type':'integer','minimum':1,'maximum':3},'parent_ref':nullable(R)})
record('Requirement',{'topic_ref':R,'scope':S,'source_leads':TS,'coverage_status':S})
# Professional models, evidence and assessment: no freeform executable expressions.
defs['expr']={'oneOf':[obj({'constant':N}),obj({'variable':ID}),obj({'op':enum('add','sub','mul','div','min','max','pow','exp','log','neg'),'args':{'type':'array','items':ref('expr'),'minItems':1}})]}
defs['param']=obj({'name':ID,'unit':S,'meaning':S,'lower':nullable(N),'upper':nullable(N)})
record('ModelSpec',{'claim_refs':R1,'parameters':arr(ref('param'),1),'formulas':arr(obj({'name':ID,'expr':ref('expr')}),1),'numeric_domain':enum('RATIONAL','BINARY64'),'missing_policy':{'const':'HOLD'},'applicability':T})
record('ConditionSpec',{'claim_refs':R1,'clauses':arr(obj({'field':ID,'op':enum('EQ','NE','LT','LE','GT','GE'),'value':ref('scalar')}),1),'combination':enum('ALL','ANY'),'unknown':{'const':'HOLD'}})
record('PolicySpec',{'claim_refs':R1,'policy_type':enum('PRACTICE','FEEDBACK','MOTIVATION','ASSESSMENT','ADAPTATION','REMEDIATION','GOVERNANCE'),'rules':arr(obj({'condition_ref':R,'action':enum('SUGGEST','DEFER','CLARIFY','PAUSE','STOP','REFUSE','REQUEST_OBSERVATION'),'reason':S,'priority':I}),1),'unknown_action':enum('CLARIFY','STOP','REFUSE'),'effect':{'const':'ADVICE_ONLY'}})
# Chinese professional entities remain distinct from syllabus source membership.
record('HanCharacter',{'character':{'type':'string','minLength':1,'maxLength':1},'codepoint':{'type':'string','pattern':'^U\\+[0-9A-F]{4,6}$'},'script':S,'claim_refs':R1})
record('Reading',{'notation':S,'system':S,'tone':nullable(S),'reading_scope':S,'claim_refs':R1})
record('Lexeme',{'lemma':S,'form_refs':RS,'reading_refs':RS,'claim_refs':R1})
record('Sense',{'lexeme_ref':R,'gloss':S,'part_of_speech':S,'domain':S,'claim_refs':R1})
record('Construction',{'pattern':S,'slot_constraints':T,'meaning':S,'claim_refs':R1,'condition_refs':RS})
record('Standard',{'edition':S,'standard_name':S,'source_refs':R1,'effective_date':nullable(S)})
record('StandardBand',{'standard_ref':R,'raw_band':S,'band_scope':S})
record('SourceMembership',{'standard_ref':R,'band_ref':R,'source_ref':R,'section':S,'ordinal':POS,'printed_page':nullable(POS),'raw_fields':arr(obj({'name':ID,'value':nullable(S)}),1),'mapping_status':enum('UNMAPPED','HOLD','CANDIDATE_MAPPED'),'semantic_refs':RS})
# Shared IF01 objects. Domain-specific facts reside in claims/typed entities, not duplicate descriptions.
def shared(k,fields):
 record(k,{'claim_refs':R1}|fields)
shared('Goal',{'construct_ref':R,'success_evidence_refs':R1,'scope':S})
shared('Competency',{'dimensions':T,'evidence_refs':R1})
shared('KnowledgeType',{'label':S,'definition':S})
shared('SkillType',{'label':S,'performance_boundary':S})
shared('LearningObject',{'target_refs':R1,'component_refs':RS,'granularity':S})
shared('Resource',{'modality_refs':R1,'rights':enum('HOLD','PRIVATE_ONLY','PUBLIC_AUTHORIZED'),'accessibility':T,'resource_identity':S})
shared('Modality',{'label':S,'capability_requirements':T,'not_equivalent_to':TS})
shared('Role',{'label':S,'capability_requirements':T,'permission_requirements':T})
shared('Environment',{'constraints':T,'capabilities':TS})
shared('ObservationSpec',{'construct_ref':R,'method':S,'unit':S,'independence_requirement':S,'missing':{'const':'UNKNOWN_NOT_ZERO'}})
shared('StateDimension',{'construct_ref':R,'observation_refs':R1,'estimator_ref':nullable(R),'uncertainty':S,'effect':{'const':'DEFINITION_ONLY'}})
shared('Activity',{'goal_refs':R1,'object_refs':R1,'resource_refs':RS,'role_refs':R1,'observation_refs':R1,'budget':POS,'stop_condition':S})
shared('Interaction',{'activity_ref':R,'role_refs':R1,'input_contract':S,'output_contract':S,'observation_refs':R1,'assistance_policy':S})
shared('TaskSpec',{'construct_ref':R,'object_refs':R1,'prompt':S,'scoring_spec':S,'observation_refs':R1,'independence_requirement':S})
shared('Mode',{'goal_refs':R1,'activity_refs':R1,'role_refs':R1,'selection_condition_refs':R1,'learner_choice':{'const':True},'switch_condition':S})
defs['step']=obj({'id':ID,'activity_ref':R,'max_attempts':POS,'checkpoint':B})
defs['transition']=obj({'from_step':ID,'to_step':ID,'event':ID,'condition_ref':nullable(R),'priority':I,'consumes_budget':B})
shared('FlowSpec',{'entry':ID,'steps':arr(ref('step'),1),'transitions':arr(ref('transition'),1),'terminals':arr(obj({'id':ID,'outcome':enum('COMPLETE','STOP','PAUSE','HOLD','FAILED')}),1),'max_events':POS,'unknown_terminal':ID,'stop_terminal':ID,'parallel_joins':arr(obj({'id':ID,'members':arr(ID,2),'mode':enum('ALL','ANY'),'resume_policy':S})),'effect':{'const':'TEMPLATE_ONLY'}})
shared('CompositionSpec',{'view_id':ID,'input_refs':R1,'output_refs':R1,'condition_refs':RS,'alternative_refs':RS,'failure_policy':S,'evidence_refs':R1,'effect':{'const':'CANDIDATE_DECISION_ONLY'}})
shared('EvaluationProtocol',{'goal_ref':R,'intervention_ref':R,'comparator_ref':R,'measurement_refs':R1,'estimand':S,'population_scope':S,'followup':S,'uncertainty':S,'approval_required':{'const':True},'effect':{'const':'NO_DIRECT_KNOWLEDGE_WRITE'}})
# Package manifest and record envelope. Package digest is pinned by dependency manifests, not self-reference.
kinds=[k for k in defs if 'kind' in defs[k].get('properties',{})]
defs['record']={'oneOf':[ref(k) for k in kinds]}
defs['file']=obj({'path':{'type':'string','pattern':'^(?!/)(?!.*(?:^|/)\\.\\.(?:/|$))[^\\\\]+\\.(json|jsonl|md)$'},'sha256':H,'format':enum('JSON_RECORDS','JSONL_RECORDS','MARKDOWN'),'record_count':I})
defs['dependency']=obj({'package_id':ID,'version':ID,'manifest_sha256':H})
defs['manifest']=obj({'schema_version':{'const':'learn-kg-canonical-candidate-1'},'package_id':ID,'version':ID,'status':enum('CANDIDATE','HOLD','APPROVED'),'rights':enum('HOLD','PRIVATE_ONLY','PUBLIC_AUTHORIZED'),'owners':arr(ID,1),'dependencies':arr(ref('dependency')),'files':arr(ref('file'),1),'qualification_receipt_refs':TS})
schema={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:learn-kg:canonical-candidate:1','title':'DB01 canonical candidate record schema','oneOf':[ref('record'),ref('manifest')],'$defs':defs}
save('canonical.schema.json',schema)
# Deterministic column mapping: scalar columns; structured fields stored as canonical JSON, typed references also normalized into registry/reference index.
tables={}
for k in kinds:
 v=defs[k];columns={}
 for f,s in v['properties'].items():
  if f in ('kind','stable_id','owner','status'):continue
  t=s.get('type')
  sql='INTEGER' if t in ('integer','boolean') else 'REAL' if t=='number' else 'TEXT'
  encoding='SCALAR' if t in ('string','integer','boolean','number') or 'const' in s or 'enum' in s else 'CANONICAL_JSON'
  columns[f]={'sqlite_type':sql,'encoding':encoding,'required':f in v['required']}
 tables[k]={'table':'record_'+k.lower(),'primary_key':['package_id','version','stable_id'],'foreign_key':'local_registry(package_id,version,stable_id,kind,owner)','fields':columns}
packages={'evidence':{'owners':'explicit claim owner','depends_on':[],'kinds':['Source']},'learning-core':{'owners':'K01–K19','depends_on':['evidence'],'kinds':'common + theory/model/assessment/shared types'},'chinese':{'owners':'H01–H07','depends_on':['evidence','learning-core'],'kinds':'common + Chinese professional/source membership'},'other-subject':{'owners':'future explicit subject owner','depends_on':['evidence','learning-core'],'kinds':'common + explicitly versioned subject extension'},'learning-process':{'owners':'P01–P10/F01–F08/A01–A08/E01','depends_on':['evidence','learning-core','chinese','other-subject'],'kinds':'common + shared lifecycle/mode/flow/policy/composition/protocol; actual manifest declares only needed direct packages'},'research-overlay':{'owners':'explicit owner','depends_on':['evidence','learning-core','chinese','other-subject','learning-process'],'kinds':'research candidate relations, not release by default'}}
matrix={'defined_by_model':[['Element','ModelSpec']],'informs_decision':[['ModelSpec','PolicySpec'],['Claim','PolicySpec']],'script_variant':[['HanCharacter','HanCharacter']],'converse_in_context':[['Sense','Sense']],'taxonomy_parent':[['Topic','Topic']],'necessary_prerequisite':[['Element','Element'],['SkillType','SkillType']],'recommended_sequence':[['Element','Element'],['SkillType','SkillType']],'component_of':[['LearningObject','LearningObject']],'scope_topic':[['SourceMembership','Topic']],'standard_member':[['SourceMembership','StandardBand']],'evidence_for':[['Locator','Claim']],'example_of':[['Case','Claim']]}
save('mapping-contract.json',{'status':'DB01_CANDIDATE_SCHEMA_NOT_G04_FREEZE','schema_version':'learn-kg-canonical-candidate-1','package_roles':packages,'identity':['package_id','version','kind','stable_id','owner'],'dependency_identity':['package_id','version','manifest_sha256'],'reference_resolution':'Exact package version and manifest hash, declared direct dependency only; same-package local lookup; kind and owner match; no bare ID or transitive fallback. Research read separate from approved consumption; unknown rights or qualification HOLD. Private staging/learner never in public manifest.','record_tables':tables,'common_tables':{'local_registry':['package_id','version','stable_id','kind','owner','status'],'typed_refs':['origin_package','origin_version','origin_id','field_pointer','target_package','target_version','target_id','expected_kind','expected_owner'],'package_meta':['package_id','version','manifest_sha256','status','rights'],'dependency_manifest':['target_package','target_version','manifest_sha256']},'relations':matrix,'indices':['local_registry(kind,owner,stable_id)','typed_refs(origin_package,origin_version,origin_id,field_pointer)','typed_refs(target_package,target_version,target_id)','record_claim(topic_id,requirement_id)','record_hancharacter(character)','record_lexeme(lemma)','record_sourcemembership(section,ordinal)'],'import':'DB02 validates schema, rejects duplicate keys/IDs, path escape, digest mismatch; map every declared field, use UTF-8 canonical sorted-key JSON for nested structures, preserve null vs missing; typed refs extracted by schema path into explicit index; exact roundtrip and counts; FK per connection, cross-package resolver not native FK. No runtime evaluation from arbitrary scripts.','publication':'Immutable UTF-8 text manifests, one writer, verify bytes/rights/current qualification/dependencies, same-filesystem atomic text pointer, retain old versions; DB02 tests actual interruptions and recovery. Persistent SQLite not generated, physical multi-file database guarantees HOLD.','limits':['This is versioned authoring baseline, not all professional field adapters or DB02 implementation. IF01 further defines semantic endpoint constraints, owners and finite cases. New kinds/fields require explicit schema revision and affected receipt invalidation.','Six logical role classes including future other-subject; no mandatory physical DB count or unrelated load. No inferred equivalence from standards or scope.','Actual knowledge sources remain in original candidate files until module-specific deterministic adapters and qualification; do not promote by schema validation.']})
print('SCHEMA_RECORD_KINDS',len(kinds),'TABLE_MAPPINGS',len(tables),'RELATION_TYPES',len(matrix))
