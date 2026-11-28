import copy,unittest
from verify_mapping import *
from test_hsk01 import Tests as FixtureTests,row,literal,iri
class MappingTests(unittest.TestCase):
 def setUp(self):
  fixture=FixtureTests();fixture.setUp();self.lex=fixture.build(fixture.lex);self.han=fixture.build(fixture.han)
  self.fields=parse_record(self.lex['raw_rdf'])
  self.recipe=CONTRACT['mapping']['LexicalRecord']['target_fields']['raw_fields']
 def raw_projection(self,fields,recipe=None):
  return project_property(self.lex,'SourceMembership','raw_fields',recipe or self.recipe,fields)
 def test_01_all_nine_exact_target_field_sets(self):
  self.assertTrue(validate_contract(CONTRACT))
  for e in CONTRACT['mapping'].values():
   self.assertEqual(set(e['target_fields']),set(SCHEMA['$defs'][e['db01_kind']]['required']))
 def test_02_extra_ability_field_rejected(self):
  c=copy.deepcopy(CONTRACT);c['mapping']['AbilityRecord']['target_fields']['source']={'state':'HOLD_TARGET_FIELD','reason':'not a target'}
  with self.assertRaisesRegex(ValueError,'TARGET_FIELD_COVERAGE'):validate_contract(c)
 def test_03_missing_required_rejected(self):
  for source in ('LexicalRecord','CharacterMembership','SourceRecord','LevelBand','SyllabusVersion','SourceBlock','TaxonomyTopic','AbilityRecord','HanCharacter'):
   c=copy.deepcopy(CONTRACT);del c['mapping'][source]['target_fields']['provenance']
   with self.assertRaisesRegex(ValueError,'TARGET_FIELD_COVERAGE'):validate_contract(c)
 def test_04_literal_bad_shape_rejected(self):
  c=copy.deepcopy(CONTRACT);c['mapping']['LexicalRecord']['target_fields']['raw_fields']={'state':'MAPPED_VALUE','op':'LITERAL','value':{'urn:raw:headwordRaw':[literal('示例')]}}
  with self.assertRaises(ValidationError):validate_contract(c)
 def test_05_held_value_rejected(self):
  c=copy.deepcopy(CONTRACT);c['mapping']['AbilityRecord']['target_fields']['claim_refs']['value']=[]
  with self.assertRaisesRegex(ValueError,'HELD_VALUE'):validate_contract(c)
 def test_06_source_rights_exact(self):
  x=CONTRACT['mapping']['SourceRecord']['target_fields'];self.assertEqual(x['rights']['value'],'HOLD');self.assertEqual(x['access']['value'],'PRIVATE_ONLY');self.assertIsNone(x['recorded_locator']['value'])
 def test_07_membership_raw_array_exact(self):
  original=copy.deepcopy(self.lex);r=self.raw_projection(self.fields)
  self.assertEqual(r['state'],'MAPPED_VALUE')
  self.assertEqual(r['value'],[{'name':k,'value':self.fields[k][1][0]['value']} for k in sorted(self.recipe['predicates'])])
  prop_validator('SourceMembership','raw_fields').validate(r['value'])
  self.assertEqual(original,self.lex)
 def test_08_preserve_whitespace_nonblank(self):
  f=copy.deepcopy(self.fields);f['headwordRaw'][1][0]['value']='  synthetic  '
  r=self.raw_projection(f);self.assertEqual(next(i['value'] for i in r['value'] if i['name']=='headwordRaw'),'  synthetic  ')
 def test_09_empty_and_whitespace_hold_entire_field(self):
  for val in ('',' ','\t\n'):
   f=copy.deepcopy(self.fields);f['headwordRaw'][1][0]['value']=val;self.assertEqual(self.raw_projection(f),{'state':'HOLD_TARGET_FIELD'})
 def test_10_multi_term_hold_entire_field(self):
  f=copy.deepcopy(self.fields);f['headwordRaw'][1].append(literal('second'));self.assertEqual(self.raw_projection(f),{'state':'HOLD_TARGET_FIELD'})
 def test_11_iri_hold_entire_field(self):
  f=copy.deepcopy(self.fields);f['headwordRaw'][1][0]=iri('urn:synthetic:wrong');self.assertEqual(self.raw_projection(f),{'state':'HOLD_TARGET_FIELD'})
 def test_12_missing_field_hold_entire_field(self):
  f=copy.deepcopy(self.fields);del f['headwordRaw'];self.assertEqual(self.raw_projection(f),{'state':'HOLD_TARGET_FIELD'})
 def test_13_unknown_metadata_retained(self):
  r=copy.deepcopy(self.lex);r['raw_rdf']['properties']['urn:synthetic:unknown']=[{'kind':'literal','value':'x','datatype':None,'language':'en'},iri('urn:synthetic:target')]
  original=copy.deepcopy(r);projected=project_fields(r);self.assertEqual(projected['raw_fields']['state'],'MAPPED_VALUE')
  self.assertEqual(r,original);self.assertNotIn('unknown',[x['name'] for x in projected['raw_fields']['value']])
 def test_14_duplicate_predicate_rejected(self):
  r=copy.deepcopy(self.lex);r['raw_rdf']['properties']['urn:other:headwordRaw']=[literal('x')]
  with self.assertRaisesRegex(ValueError,'PREDICATE_COLLISION'):project_fields(r)
 def test_15_dereference_glyph_not_pointer_literal(self):
  z=project_fields(self.han);self.assertEqual(z['character']['value'],'一');self.assertEqual(z['codepoint']['value'],'U+4E00')
  self.assertEqual(z['script']['state'],'HOLD_TARGET_FIELD');self.assertEqual(z['claim_refs']['state'],'HOLD_TARGET_FIELD')
 def test_16_source_refs_and_provenance_held(self):
  z=project_fields(self.lex)
  for k in ('source_ref','standard_ref','band_ref','stable_id','owner','provenance'):self.assertEqual(z[k],{'state':'HOLD_TARGET_FIELD'})
  self.assertEqual(z['semantic_refs']['value'],[]);self.assertEqual(z['mapping_status']['value'],'HOLD');self.assertEqual(z['section']['value'],'LEXICAL_SOURCE_RECORD')
 def test_17_locator_and_page_never_invented(self):
  r=copy.deepcopy(self.lex);r['candidate']['source_locator']['ordinal_candidate']=None;r['candidate']['source_locator']['printed_page_numeric_candidate']=None
  z=project_fields(r);self.assertEqual(z['ordinal'],{'state':'HOLD_TARGET_FIELD'});self.assertEqual(z['printed_page'],{'state':'MAPPED_VALUE','value':None})
 def test_18_root_only_null(self):
  e=CONTRACT['mapping']['TaxonomyTopic']['target_fields']['parent_ref']
  for depth,parent,expected in [('1',None,'MAPPED_VALUE'),('2',None,'HOLD_TARGET_FIELD'),('1','urn:parent','HOLD_TARGET_FIELD'),('2','urn:parent','HOLD_TARGET_FIELD')]:
   p={'depth':literal(depth),'label':literal('example'),'status':literal('STAGING')}
   if parent:p['parent']=iri(parent)
   raw=row('TaxonomyTopic','urn:synthetic:topic',p)
   z=project_property({},'Topic','parent_ref',e,parse_record(raw));self.assertEqual(z['state'],expected)
   if expected=='MAPPED_VALUE':self.assertIsNone(z['value'])
 def test_19_private_stage_boundary(self):
  for key,val in [('publication','AUTHORIZED'),('visibility','PUBLIC')]:
   r=copy.deepcopy(self.lex);r['rights_scope'][key]=val
   with self.assertRaisesRegex(ValueError,'PRIVATE_STAGE_BOUNDARY'):project_fields(r)
  r=copy.deepcopy(self.lex);r['candidate']['normalized_knowledge_id']='made-up'
  with self.assertRaisesRegex(ValueError,'PRIVATE_STAGE_BOUNDARY'):project_fields(r)
 def test_20_no_competency_source_or_raw_text_target(self):
  e=CONTRACT['mapping']['AbilityRecord'];self.assertNotIn('source',e['target_fields']);self.assertNotIn('raw_text',e['target_fields'])
  self.assertIn('typed_links.source',e['staging_only_inputs']);self.assertIn('candidate.raw_text_pointer',e['staging_only_inputs'])
  for k in ('claim_refs','dimensions','evidence_refs'):self.assertEqual(e['target_fields'][k]['state'],'HOLD_TARGET_FIELD')
if __name__=='__main__':unittest.main(verbosity=2)
