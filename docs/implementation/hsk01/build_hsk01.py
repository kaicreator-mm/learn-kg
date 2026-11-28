#!/usr/bin/env python3
"""Lossless private HSK01 text candidate; no publication or semantic qualification."""
from __future__ import annotations
import argparse,collections,hashlib,json,os,re,sqlite3,sys
from pathlib import Path
from typing import Any
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent/'hs00'))
from build_hs00 import RIGHTS_SCOPE,parse_level_label,merged_identity
from hs00_semantic import HS00Validator
from jsonschema import Draft202012Validator
EXPECTED={'AbilityRecord':9,'CharacterMembership':4288,'HanCharacter':3088,'LevelBand':11,'LexicalRecord':11000,'SourceBlock':94,'SourceRecord':3,'SyllabusVersion':1,'TaxonomyTopic':823}
TYPES={'AbilityRecord':'CAPABILITY_SOURCE','CharacterMembership':'CHARACTER_MEMBERSHIP','HanCharacter':'CHARACTER_ITEM','LevelBand':'LEVEL_BAND','LexicalRecord':'VOCABULARY_ITEM','SourceBlock':'SOURCE_BLOCK','SourceRecord':'SOURCE_RECORD','SyllabusVersion':'STANDARD_IDENTITY','TaxonomyTopic':'CATEGORY'}
LINKS={'source':'SourceRecord','levelBand':'LevelBand','scopeTopic':'TaxonomyTopic','character':'HanCharacter','version':'SyllabusVersion','parent':'TaxonomyTopic'}
REQUIRED={
'AbilityRecord':{'levelBand','rawText','scopeTopic','source','status'},
'CharacterMembership':{'character','levelBand','mode','ordinal','printedPage','scopeTopic','source','status'},
'HanCharacter':{'glyph'},'LevelBand':{'label','version'},
'LexicalRecord':{'headwordRaw','levelBand','levelRaw','ordinal','printedPage','readingPosRaw','scopeTopic','source','status'},
'SourceBlock':{'blockKind','levelBand','printedPage','rawText','scopeTopic','source','status'},
'SourceRecord':{'status','textSha256'},'SyllabusVersion':{'releaseLabel','status'},
'TaxonomyTopic':{'depth','label','status'}}
DB_MAP={'AbilityRecord':('Competency','HOLD_REQUIRES_H06_CLAIMS_EVIDENCE'),
'CharacterMembership':('SourceMembership','HOLD_SOURCE_MEMBERSHIP_ONLY'),
'HanCharacter':('HanCharacter','HOLD_REQUIRES_H02_CLAIMS'),
'LevelBand':('StandardBand','HOLD_STANDARD_AUTHORITY'),
'LexicalRecord':('SourceMembership','HOLD_REQUIRES_H03_LEXEME_READING_SENSE'),
'SourceBlock':('Locator','HOLD_LAYOUT_AND_H04_H05_SEMANTICS'),
'SourceRecord':('Source','HOLD_RIGHTS'),'SyllabusVersion':('Standard','HOLD_AUTHORITY'),
'TaxonomyTopic':('Topic','HOLD_SCOPE_NOT_PEDAGOGICAL_RELATION')}
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha(b):return hashlib.sha256(b).hexdigest()
def file_sha(p):return sha(p.read_bytes())
def need(v,code):
 if not v:raise ValueError(code)
def read_json(p):return json.loads(p.read_text(encoding='utf-8'))
def line_bytes(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,allow_nan=False)+'\n').encode('utf-8')
def typed_ref(row):
 return {'graph':row['graph'],'source_entity_id':row['stable_id'],'source_rdf_kind':row['kind']}
def short(p):return p.rsplit(':',1)[-1]
def parse_record(row):
 need(set(row)=={'graph','stable_id','kind','type_iri','properties'},'ROW_SHAPE')
 need(row['kind'] in EXPECTED,'RDF_KIND')
 need(all(isinstance(row[k],str) and row[k] for k in ('graph','stable_id','type_iri')),'RDF_ID')
 fields={}
 for iri,terms in row['properties'].items():
  name=short(iri);need(name not in fields,'PREDICATE_COLLISION')
  need(isinstance(terms,list) and terms,'TERM_ARRAY')
  for t in terms:
   need(isinstance(t,dict) and t.get('kind') in ('iri','literal') and isinstance(t.get('value'),str),'RDF_TERM')
   need(set(t)==({'kind','value'} if t['kind']=='iri' else {'kind','value','datatype','language'}),'TERM_SHAPE')
   if t['kind']=='literal':need(all(t[k] is None or isinstance(t[k],str) for k in ('datatype','language')),'LITERAL_METADATA')
  fields[name]=(iri,terms)
 need(REQUIRED[row['kind']]<=fields.keys(),'REQUIRED_FIELD_MISSING')
 for n in REQUIRED[row['kind']]|({'parent'} if 'parent' in fields and row['kind']=='TaxonomyTopic' else set()):
  need(len(fields[n][1])==1,'AMBIGUOUS_REQUIRED_FIELD')
  need(fields[n][1][0]['kind']==('iri' if n in LINKS else 'literal'),'WRONG_REQUIRED_TERM_KIND')
 return fields
def field(fields,n):return fields[n][1][0]['value']
def ptr(iri,index=0):return '/raw_rdf/properties/'+iri.replace('~','~0').replace('/','~1')+'/'+str(index)
def integer(value):
 return int(value) if isinstance(value,str) and re.fullmatch(r'[1-9][0-9]*',value) else None
def candidate_id(row):
 return 'HSK01.'+TYPES[row['kind']]+'.'+sha(canonical([row['graph'],row['stable_id'],row['kind']]).encode())[:32]
def build_record(row,raw,archive_file,row_number,registry,standard_id,hsmap):
 fields=parse_record(row);kind=row['kind'];c={'record_kind':TYPES[kind],'candidate_id':candidate_id(row),'candidate_status':'HOLD','source_record_id':None,'source_locator':None,'scope_topic_semantics':'SOURCE_SCOPE_ONLY_NOT_PEDAGOGICAL_RELATION','semantic_qualification':'NOT_RUN','normalized_knowledge_id':None,'typed_links':{},'level_label':None,'raw_field_index':[],'db01_target_kind':DB_MAP[kind][0],'db01_mapping_status':DB_MAP[kind][1]}
 for name,(iri,terms) in sorted(fields.items()):
  known=name in REQUIRED[kind] or (kind=='TaxonomyTopic' and name=='parent')
  c['raw_field_index'].append({'predicate_iri':iri,'field_name':name,'term_count':len(terms),'raw_term_sha256':sha(canonical(terms).encode()),'raw_pointer':ptr(iri)[:-2],'parse_status':'RECORDED_RAW_ONLY' if known else 'UNKNOWN_PRESERVED'})
  if known and name in LINKS:
   target=registry.get(field(fields,name));need(target is not None and target['kind']==LINKS[name],'TYPED_LINK_MISMATCH:'+name)
   c['typed_links'][name]=typed_ref(target)
 if 'source' in c['typed_links']:
  c['source_record_id']=field(fields,'source');need(c['source_record_id'] in hsmap['sources'],'UNKNOWN_HS00_SOURCE')
 if 'printedPage' in fields:
  rawpage=field(fields,'printedPage');n=integer(rawpage)
  c['source_locator']={'printed_page_label_recorded_raw':rawpage,'printed_page_source_datatype':fields['printedPage'][1][0]['datatype'],'printed_page_numeric_candidate':n,'pdf_page_index_zero_based':None,'pdf_page_number_one_based':None,'visual_layout':'HOLD_LAYOUT_REVIEW_PENDING','ordinal_raw':field(fields,'ordinal') if 'ordinal' in fields else None,'ordinal_candidate':integer(field(fields,'ordinal')) if 'ordinal' in fields else None,'source_entity_id':row['stable_id']}
 if kind=='LexicalRecord':
  rawlabel=field(fields,'levelRaw');status,members=parse_level_label(rawlabel)
  c['level_label']={'raw':rawlabel,'parse_status':status,'normalized_member_levels':members,'merged_level_identity':merged_identity(rawlabel,standard_id) if members is not None else None,'semantics_status':'UNKNOWN_HOLD','parser':'hs00-level-label-parser@0.1.0','raw_sha256':sha(rawlabel.encode())}
  c['surface_pointer']=ptr(fields['headwordRaw'][0]);c['reading_pos_pointer']=ptr(fields['readingPosRaw'][0])
  c['reading_pos_parse_status']='NOT_ATTEMPTED_H03';c['semantic_refs']=[]
 elif kind=='HanCharacter':
  glyph=field(fields,'glyph');need(len(glyph)==1,'GLYPH_SCALAR')
  c['glyph_pointer']=ptr(fields['glyph'][0]);c['codepoint']='U+'+format(ord(glyph),'04X');c['reading_component_status']='HOLD_NOT_INFERRED'
 elif kind=='CharacterMembership':
  c['mode_raw']=field(fields,'mode');c['semantic_refs']=[]
 elif kind=='SourceBlock':
  original=hsmap['blocks'].get(row['stable_id']);need(original is not None,'HS00_BLOCK_MISSING')
  need(original['source_record_id']==c['source_record_id'] and original['scope_topic_ref']==field(fields,'scopeTopic') and original['level_band_ref']==field(fields,'levelBand') and original['printed_page_label_recorded_raw']==field(fields,'printedPage') and original['block_kind_raw']==field(fields,'blockKind') and original['raw_text_sha256']==sha(field(fields,'rawText').encode()) and original['source_block_jsonl_line_sha256']==sha(raw),'HS00_BLOCK_MISMATCH')
  c['block_kind_raw']=field(fields,'blockKind');c['raw_text_pointer']=ptr(fields['rawText'][0]);c['raw_text_sha256']=original['raw_text_sha256']
 elif kind=='AbilityRecord':
  c['raw_text_pointer']=ptr(fields['rawText'][0]);c['ability_mapping_status']='HOLD_H06_H07'
 elif kind=='TaxonomyTopic':
  c['depth_raw']=field(fields,'depth');c['depth_candidate']=integer(c['depth_raw']);c['label_pointer']=ptr(fields['label'][0]);c['category_relation']='RECORDED_TAXONOMY_PARENT_ONLY'
 elif kind=='LevelBand':
  original=hsmap['bands'].get(row['stable_id']);need(original is not None and original['raw_label_term']==fields['label'][1][0] and original['source_record_line_sha256']==sha(raw),'HS00_BAND_MISMATCH')
  c['level_label']={k:original[k] for k in ('raw_level_label','parse_status','normalized_member_levels','merged_level_identity','semantics_status','evidence_origin')}
 elif kind=='SourceRecord':
  original=hsmap['sources'].get(row['stable_id']);need(original is not None and original['source_record_jsonl_line_sha256']==sha(raw) and original['canonical_connector_text_sha256']==field(fields,'textSha256'),'HS00_SOURCE_MISMATCH')
 elif kind=='SyllabusVersion':
  need(row['stable_id']==standard_id and sha(raw)==hsmap['standard']['source_version_record_sha256'],'HS00_STANDARD_MISMATCH')
  c['standard_identity']='UNKNOWN_HOLD'
 return {'schema_version':'learn-kg-hsk01-private-stage-1','rights_scope':RIGHTS_SCOPE.copy(),'provenance':{'archive_file':archive_file,'row_number_one_based':row_number,'raw_line_sha256':sha(raw),'graph':row['graph'],'source_entity_id':row['stable_id'],'source_rdf_kind':kind},'raw_rdf':row,'candidate':c}
def verify_sql(rows):
 con=sqlite3.connect(':memory:')
 try:
  con.execute('PRAGMA foreign_keys=ON')
  con.executescript("""
  CREATE TABLE registry(graph TEXT NOT NULL,id TEXT NOT NULL,kind TEXT NOT NULL,candidate_id TEXT UNIQUE NOT NULL,PRIMARY KEY(graph,id,kind));
  CREATE TABLE edges(origin_graph TEXT NOT NULL,origin_id TEXT NOT NULL,origin_kind TEXT NOT NULL,predicate TEXT NOT NULL,target_graph TEXT NOT NULL,target_id TEXT NOT NULL,target_kind TEXT NOT NULL,PRIMARY KEY(origin_graph,origin_id,origin_kind,predicate),FOREIGN KEY(origin_graph,origin_id,origin_kind) REFERENCES registry(graph,id,kind),FOREIGN KEY(target_graph,target_id,target_kind) REFERENCES registry(graph,id,kind));
  """)
  con.executemany('INSERT INTO registry VALUES(?,?,?,?)',[(r['provenance']['graph'],r['provenance']['source_entity_id'],r['provenance']['source_rdf_kind'],r['candidate']['candidate_id']) for r in rows])
  edges=[]
  for r in rows:
   p=r['provenance']
   for name,t in r['candidate']['typed_links'].items():edges.append((p['graph'],p['source_entity_id'],p['source_rdf_kind'],name,t['graph'],t['source_entity_id'],t['source_rdf_kind']))
  con.executemany('INSERT INTO edges VALUES(?,?,?,?,?,?,?)',edges)
  need(con.execute('PRAGMA foreign_key_check').fetchall()==[],'SQL_FK')
  need(all(not x[2] for x in con.execute('PRAGMA database_list')),'PERSISTENT_SQLITE')
  result=dict(registry=con.execute('SELECT count(*) FROM registry').fetchone()[0],typed_edges=con.execute('SELECT count(*) FROM edges').fetchone()[0],edge_counts=dict(con.execute('SELECT predicate,count(*) FROM edges GROUP BY predicate')),foreign_key_violations=0,mode='MEMORY_PRIVATE_STAGING_ONLY')
  return result
 finally:con.close()
def main(archive,output,receipt_pin):
 os.umask(0o077)
 rp=ROOT/'evidence/tasks/HS00/HS00-FORMAL-01.json';need(file_sha(rp)==receipt_pin,'HS00_RECEIPT_PIN')
 receipt=read_json(rp);need(receipt['validation']['independent_result']=='ACCEPT_SCOPED' and receipt['scope_restriction']['rights']=='HOLD','HS00_RECEIPT_SCOPE')
 for artifact in receipt['output']:need(file_sha(ROOT/artifact['path'])==artifact['sha256'],'HS00_ARTIFACT_PIN')
 v=HS00Validator.from_pinned_files(HERE.parent/'hs00',receipt['scope_restriction']['interface_contract_sha256'])
 mapping=v.mapping;am=archive/'manifest.json';need(file_sha(am)==mapping['archive_evidence']['readable_archive_manifest_sha256'],'ARCHIVE_MANIFEST_PIN')
 man=read_json(am);need(man['scope']=='SRC01_PRIVATE_RDF_ARCHIVAL_TEXT_ONLY' and man['original_pdf_identity']=='HOLD' and man['publication_rights']=='HOLD' and man['exact_quad_set_equal'] is True,'ARCHIVE_SCOPE')
 need(set(man['files'])=={k+'.jsonl' for k in EXPECTED},'ARCHIVE_INVENTORY')
 registry={};raws={};source_files={}
 for k,count in EXPECTED.items():
  name=k+'.jsonl';data=(archive/name).read_bytes();info=man['files'][name]
  need(len(data)==info['bytes'] and sha(data)==info['sha256'],'ARCHIVE_FILE_PIN')
  lines=data.splitlines(keepends=True);need(len(lines)==info['rows']==count,'ARCHIVE_ROW_COUNT')
  raws[k]=[]
  for idx,line in enumerate(lines,1):
   row=json.loads(line);need(row['kind']==k and line_bytes(row)==line,'ARCHIVE_LINE_REPLAY')
   need(row['stable_id'] not in registry,'AMBIGUOUS_SOURCE_ENTITY_ID');registry[row['stable_id']]=row
   raws[k].append((row,line,idx))
  source_files[name]=info
 hsmap={'sources':v.sources,'blocks':v.blocks,'bands':v.bands,'standard':mapping['standard_identity']}
 standard_id=hsmap['standard']['source_standard_id']
 schema=Draft202012Validator(read_json(HERE/'stage.schema.json'))
 need(not output.exists(),'OUTPUT_MUST_BE_NEW')
 need(not output.resolve().is_relative_to(ROOT.resolve()),'PRIVATE_OUTPUT_OUTSIDE_REPO')
 output.mkdir(parents=True,mode=0o700)
 allrows=[];file_records={};levels=collections.Counter();blocks=collections.Counter();modes=collections.Counter();unknown=0;quad_count=0;field_count=0
 for k,source in raws.items():
  out=output/(k+'.candidate.jsonl');reconstructed=hashlib.sha256()
  with out.open('xb') as fp:
   for row,line,idx in source:
    rec=build_record(row,line,k+'.jsonl',idx,registry,standard_id,hsmap);schema.validate(rec)
    # Exact source row recoverability; all unknown predicates remain in raw_rdf.
    need(line_bytes(rec['raw_rdf'])==line,'SOURCE_ROW_ROUNDTRIP')
    reconstructed.update(line_bytes(rec['raw_rdf']))
    c=rec['candidate'];quad_count+=1+sum(len(x) for x in row['properties'].values());field_count+=len(c['raw_field_index'])
    unknown+=sum(x['parse_status']=='UNKNOWN_PRESERVED' for x in c['raw_field_index'])
    if k=='LexicalRecord':levels[c['level_label']['raw']]+=1
    if k=='SourceBlock':blocks[c['block_kind_raw']]+=1
    if k=='CharacterMembership':modes[c['mode_raw']]+=1
    fp.write((canonical(rec)+'\n').encode());allrows.append(rec)
  need(reconstructed.hexdigest()==source_files[k+'.jsonl']['sha256'],'FULL_FILE_ROUNDTRIP')
  file_records[out.name]={'rows':len(source),'bytes':out.stat().st_size,'sha256':file_sha(out),'reconstructed_archive_sha256':reconstructed.hexdigest()}
 observed={x['raw_level_label']:x['occurrence_count'] for x in mapping['level_label_observations']}
 need(dict(levels)==observed and sum(v for k,v in levels.items() if '（' in k)==102,'HS00_LEVEL_RECONCILIATION')
 need(dict(blocks)==mapping['source_block_summary']['block_kind_counts'],'HS00_BLOCK_COUNTS')
 need(len(allrows)==man['records']==19317 and quad_count==man['quad_count']==159708,'FULL_COUNTS')
 sql=verify_sql(allrows)
 # Output read-back, not only in-memory objects; all source bytes must reconstruct.
 for k in EXPECTED:
  p=output/(k+'.candidate.jsonl');h=hashlib.sha256();count=0
  with p.open('rb') as fp:
   for line in fp:
    row=json.loads(line);schema.validate(row);h.update(line_bytes(row['raw_rdf']));count+=1
  need(count==EXPECTED[k] and h.hexdigest()==source_files[k+'.jsonl']['sha256'],'READBACK_ROUNDTRIP')
 result={'status':'PRIVATE_CANDIDATE_CONVERSION_ONLY','schema_version':'learn-kg-hsk01-private-stage-1','rights_scope':RIGHTS_SCOPE,'hs00_receipt_sha256':receipt_pin,'hs00_interface_sha256':receipt['scope_restriction']['interface_contract_sha256'],'archive_manifest_sha256':file_sha(am),'source_quad_count':quad_count,'source_entity_count':len(allrows),'raw_predicate_count':field_count,'counts':EXPECTED,'distinct_raw_level_labels':len(levels),'parenthetical_lexical_records':102,'source_block_kind_counts':dict(sorted(blocks.items())),'character_membership_mode_counts':dict(sorted(modes.items())),'unknown_predicates_preserved':unknown,'roundtrip_archive_files':9,'readback_archive_files':9,'source_file_pins':source_files,'private_outputs':file_records,'sql':sql,'db01_mapping':'DECLARED_STAGING_TO_CANONICAL_KIND_AND_HOLD_BOUNDARY; NO_GENERAL_IMPORTER_OR_DB01_PACKAGE_REGISTRATION','professional_qualification':'NOT_RUN','publication':'NOT_AUTHORIZED','persistent_sqlite':False,'historical_pdf_identity':'HOLD','visual_layout':'HOLD','standard_authority':'UNKNOWN_HOLD'}
 (output/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--archive',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--hs00-receipt-sha256',required=True);a=p.parse_args()
 main(a.archive.resolve(),a.output,a.hs00_receipt_sha256)
