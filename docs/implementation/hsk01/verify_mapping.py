#!/usr/bin/env python3
"""DB01 field recipe verifier; only private property-level views, never canonical emission."""
from __future__ import annotations
import argparse,collections,copy,hashlib,json,re,sys
from pathlib import Path
from jsonschema import Draft202012Validator,ValidationError
HERE=Path(__file__).resolve().parent
from build_hsk01 import EXPECTED,DB_MAP,parse_record,field,need,sha,file_sha,read_json
ROOT=HERE.parents[2]
SCHEMA=read_json(ROOT/'docs/implementation/db01/canonical.schema.json')
CONTRACT=read_json(HERE/'mapping-contract.json')
def pointer(obj,p):
 if not isinstance(p,str) or not p.startswith('/'):raise ValueError('INVALID_POINTER')
 for token in p[1:].split('/'):
  if re.search(r'~(?![01])',token):raise ValueError('INVALID_POINTER')
  token=token.replace('~1','/').replace('~0','~')
  if isinstance(obj,list):
   if re.fullmatch(r'0|[1-9][0-9]*',token) is None:raise ValueError('INVALID_POINTER')
   obj=obj[int(token)]
  else:obj=obj[token]
 return obj
def prop_validator(kind,name):
 return Draft202012Validator({'$defs':SCHEMA['$defs'],**SCHEMA['$defs'][kind]['properties'][name]})
def validate_contract(contract):
 need(set(contract['mapping'])==set(EXPECTED),'SOURCE_KIND_COVERAGE')
 for src,entry in contract['mapping'].items():
  kind=entry['db01_kind'];need(kind==DB_MAP[src][0],'TARGET_KIND')
  target=SCHEMA['$defs'][kind]
  fields=entry['target_fields']
  need(set(fields)==set(target['properties'])==set(target['required']),'TARGET_FIELD_COVERAGE:'+src)
  need(entry['emission']=='NOT_AUTHORIZED_NO_CANONICAL_RECORD','EMISSION')
  need(isinstance(entry['staging_only_inputs'],list) and entry['staging_only_inputs'],'STAGING_INPUTS')
  for name,recipe in fields.items():
   state=recipe['state']
   if state=='HOLD_TARGET_FIELD':
    need(bool(recipe.get('reason')),'HOLD_REASON');need('value' not in recipe,'HELD_VALUE')
   elif state=='CONDITIONAL_HOLD_TARGET_FIELD':
    need(name=='parent_ref' and src=='TaxonomyTopic' and recipe['op']=='NULL_IF_RECORDED_ROOT_ELSE_HOLD','CONDITIONAL_RULE')
    prop_validator(kind,name).validate(None)
   else:
    need(state=='MAPPED_VALUE','FIELD_STATE')
    op=recipe['op'];need(op in ('LITERAL','RAW_SINGLE_LITERAL_VALUE','CANDIDATE_VALUE','DEREFERENCE_RAW_LITERAL_POINTER','BOUNDED_RAW_LITERAL_FIELDS','RECORDED_PRINTED_LABEL_AND_ENTITY'),'FIELD_OP')
    if op=='LITERAL':prop_validator(kind,name).validate(recipe['value'])
    if op=='BOUNDED_RAW_LITERAL_FIELDS':
     need(kind=='SourceMembership' and name=='raw_fields' and src in ('LexicalRecord','CharacterMembership'),'RAW_FIELD_TARGET')
     need(recipe['on_unrepresentable']=='HOLD_ENTIRE_FIELD_NO_PARTIAL_OUTPUT' and bool(recipe['predicates']) and len(set(recipe['predicates']))==len(recipe['predicates']),'RAW_FIELD_RECIPE')
     for n in recipe['predicates']:need(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]*',n) is not None,'RAW_FIELD_NAME')
  need(fields['kind']=={'state':'MAPPED_VALUE','op':'LITERAL','value':kind},'KIND_LITERAL')
  need(fields['status']=={'state':'MAPPED_VALUE','op':'LITERAL','value':'HOLD'},'STATUS_HOLD')
  for n in ('stable_id','owner','provenance'):need(fields[n]['state']=='HOLD_TARGET_FIELD','DEFERRED_CANONICAL_IDENTITY')
 return True
def raw_literal(fields,n):
 iri,terms=fields[n]
 need(len(terms)==1 and terms[0]['kind']=='literal','NOT_SINGLE_LITERAL')
 v=terms[0]['value'];need(isinstance(v,str) and bool(v.strip()),'UNREPRESENTABLE_LITERAL')
 return v
def project_property(record,kind,name,recipe,fields):
 state=recipe['state']
 if state=='HOLD_TARGET_FIELD':return {'state':'HOLD_TARGET_FIELD'}
 if state=='CONDITIONAL_HOLD_TARGET_FIELD':
  # Explicit root means no parent predicate and recorded depth 1. Missing parent at
  # any other depth is not a root and must remain held.
  if 'parent' not in fields and field(fields,'depth')=='1':value=None
  else:return {'state':'HOLD_TARGET_FIELD'}
 else:
  try:
   op=recipe['op']
   if op=='LITERAL':value=copy.deepcopy(recipe['value'])
   elif op=='RAW_SINGLE_LITERAL_VALUE':value=raw_literal(fields,recipe['predicate'])
   elif op=='CANDIDATE_VALUE':value=pointer(record,recipe['pointer'])
   elif op=='DEREFERENCE_RAW_LITERAL_POINTER':
    p=pointer(record,recipe['pointer']);need(p.startswith('/raw_rdf/properties/'),'NON_RAW_POINTER')
    term=pointer(record,p);need(term.get('kind')=='literal','NOT_LITERAL')
    value=term['value']
   elif op=='BOUNDED_RAW_LITERAL_FIELDS':
    value=[{'name':n,'value':raw_literal(fields,n)} for n in sorted(recipe['predicates'])]
   elif op=='RECORDED_PRINTED_LABEL_AND_ENTITY':
    loc=pointer(record,recipe['pointer']);value='Recorded source entity '+loc['source_entity_id']+'; printed page label '+loc['printed_page_label_recorded_raw']
   else:raise ValueError('UNKNOWN_OP')
   prop_validator(kind,name).validate(value)
  except (KeyError,IndexError,TypeError,AttributeError,ValueError,ValidationError):
   return {'state':'HOLD_TARGET_FIELD'}
 # Conditional mapped null is checked as well.
 prop_validator(kind,name).validate(value)
 return {'state':'MAPPED_VALUE','value':value}
def project_fields(record,contract=CONTRACT):
 src=record['raw_rdf']['kind'];entry=contract['mapping'][src];kind=entry['db01_kind']
 need(record['rights_scope']['publication']=='NOT_AUTHORIZED' and record['rights_scope']['visibility']=='PRIVATE_ONLY' and record['candidate']['candidate_status']=='HOLD' and record['candidate']['normalized_knowledge_id'] is None,'PRIVATE_STAGE_BOUNDARY')
 fields=parse_record(record['raw_rdf'])
 return {name:project_property(record,kind,name,recipe,fields) for name,recipe in entry['target_fields'].items()}
def verify_private_stage(root,expected_manifest):
 root=root.resolve();need(not root.is_relative_to(ROOT.resolve()),'PRIVATE_ROOT_OUTSIDE_REPO')
 manifest=root/'manifest.json';need(file_sha(manifest)==expected_manifest,'MANIFEST_PIN')
 evidence=read_json(HERE/'conversion-evidence.json');need(expected_manifest==evidence['private_manifest_sha256'],'REVIEWED_MANIFEST_PIN')
 m=read_json(manifest);need(m['private_outputs']==evidence['private_outputs'],'OUTPUT_PIN_SET')
 counts={};hold_counts={};field_counts=collections.Counter();raw_fields_rows=collections.Counter();root_count=0
 for src,expected in EXPECTED.items():
  name=src+'.candidate.jsonl';p=root/name;pin=m['private_outputs'][name]
  need(file_sha(p)==pin['sha256'] and p.stat().st_size==pin['bytes'],'PRIVATE_OUTPUT_PIN')
  n=0;holds=collections.Counter()
  with p.open(encoding='utf-8') as f:
   for line in f:
    r=json.loads(line);need(r['raw_rdf']['kind']==src,'RECORD_KIND')
    projection=project_fields(r)
    for k,v in projection.items():
     field_counts[v['state']]+=1
     if v['state']=='HOLD_TARGET_FIELD':holds[k]+=1
    need(all(projection[x]['state']=='HOLD_TARGET_FIELD' for x in ('stable_id','owner','provenance')),'NO_CANONICAL_EMISSION')
    if src in ('LexicalRecord','CharacterMembership'):
     rf=projection['raw_fields'];need(rf['state']=='MAPPED_VALUE','ACTUAL_RAW_FIELD_SHAPE')
     raw_fields_rows[src]+=1
     # Verify actual raw values by exact predicate lookup, without changing raw record.
     original={k.rsplit(':',1)[-1]:v for k,v in r['raw_rdf']['properties'].items()}
     for item in rf['value']:need(original[item['name']][0]['value']==item['value'],'RAW_LITERAL_LOSS')
    if src=='TaxonomyTopic' and projection['parent_ref']['state']=='MAPPED_VALUE':root_count+=1
    n+=1
  need(n==expected,'ROW_COUNT');counts[src]=n;hold_counts[src]=dict(sorted(holds.items()))
 return {'records':sum(counts.values()),'records_by_kind':counts,'projected_property_counts':dict(field_counts),'held_fields_by_source_kind':hold_counts,'raw_field_array_rows':dict(raw_fields_rows),'recorded_taxonomy_root_nulls':root_count,'canonical_records_emitted':0,'manifest_sha256':expected_manifest,'db01_schema_sha256':file_sha(ROOT/'docs/implementation/db01/canonical.schema.json')}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--private-stage',type=Path);p.add_argument('--manifest-sha256');a=p.parse_args();validate_contract(CONTRACT)
 if a.private_stage:
  need(a.manifest_sha256,'MANIFEST_REQUIRED');print(json.dumps(verify_private_stage(a.private_stage,a.manifest_sha256),ensure_ascii=False,sort_keys=True,indent=2))
 else:print('DB01_FIELD_COVERAGE_PASS_9_SOURCE_KINDS')
