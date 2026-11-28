import copy,unittest,sys
from pathlib import Path
from build_hsk01 import *
def literal(v):return {'kind':'literal','value':v,'datatype':'http://www.w3.org/2001/XMLSchema#string','language':None}
def iri(v):return {'kind':'iri','value':v}
def row(k,id,p):return {'graph':'urn:synthetic:graph','stable_id':id,'kind':k,'type_iri':'urn:synthetic:type:'+k,'properties':{'urn:synthetic:'+n:[t] for n,t in p.items()}}
class Tests(unittest.TestCase):
 def setUp(self):
  self.han=row('HanCharacter','urn:synthetic:han',{'glyph':literal('一')})
  self.src=row('SourceRecord','urn:synthetic:source',{'status':literal('STAGING'),'textSha256':literal('0'*64)})
  self.band=row('LevelBand','urn:synthetic:band',{'label':literal('1'),'version':iri('urn:synthetic:standard')})
  self.topic=row('TaxonomyTopic','urn:synthetic:topic',{'depth':literal('1'),'label':literal('synthetic'),'status':literal('STAGING')})
  self.lex=row('LexicalRecord','urn:synthetic:lex',{'headwordRaw':literal('一'),'levelBand':iri(self.band['stable_id']),'levelRaw':literal('3（4）（7-9）'),'ordinal':literal('1'),'printedPage':literal('7'),'readingPosRaw':literal('synthetic unparsed'),'scopeTopic':iri(self.topic['stable_id']),'source':iri(self.src['stable_id']),'status':literal('STAGING')})
  self.registry={r['stable_id']:r for r in (self.han,self.src,self.band,self.topic,self.lex)}
  self.hsmap={'sources':{self.src['stable_id']:{}},'blocks':{},'bands':{},'standard':{}}
 def build(self,r):
  return build_record(r,line_bytes(r),r['kind']+'.jsonl',1,self.registry,'urn:synthetic:standard',self.hsmap)
 def test_01_explicit_kind_same_surface(self):
  h=self.build(self.han);l=self.build(self.lex)
  self.assertEqual(h['candidate']['record_kind'],'CHARACTER_ITEM')
  self.assertEqual(l['candidate']['record_kind'],'VOCABULARY_ITEM')
  self.assertNotEqual(h['candidate']['candidate_id'],l['candidate']['candidate_id'])
  self.assertIsNone(l['candidate']['normalized_knowledge_id'])
 def test_02_level_raw(self):
  z=self.build(self.lex)['candidate']['level_label']
  self.assertEqual(z['raw'],'3（4）（7-9）');self.assertEqual(z['normalized_member_levels'],[3,4,7,8,9])
  self.assertEqual(z['semantics_status'],'UNKNOWN_HOLD')
 def test_03_unknown_label_preserved(self):
  r=copy.deepcopy(self.lex);r['properties']['urn:synthetic:levelRaw']=[literal(' 9（10） ')]
  z=self.build(r)['candidate']['level_label'];self.assertEqual(z['raw'],' 9（10） ');self.assertEqual(z['parse_status'],'HOLD_UNPARSED');self.assertIsNone(z['normalized_member_levels'])
 def test_04_unknown_multivalue(self):
  r=copy.deepcopy(self.lex);r['properties']['urn:synthetic:vendor']=[literal(''),literal('Ω'),iri('urn:unknown:target')]
  z=self.build(r);self.assertEqual(z['raw_rdf'],r)
  self.assertEqual(next(x for x in z['candidate']['raw_field_index'] if x['field_name']=='vendor')['parse_status'],'UNKNOWN_PRESERVED')
 def test_05_wrong_type_link(self):
  r=copy.deepcopy(self.lex);r['properties']['urn:synthetic:source']=[iri(self.han['stable_id'])]
  with self.assertRaisesRegex(ValueError,'TYPED_LINK_MISMATCH'):self.build(r)
 def test_06_unbound_link(self):
  r=copy.deepcopy(self.lex);r['properties']['urn:synthetic:scopeTopic']=[iri('urn:absent')]
  with self.assertRaisesRegex(ValueError,'TYPED_LINK_MISMATCH'):self.build(r)
 def test_07_conflicting_required_field(self):
  r=copy.deepcopy(self.lex);r['properties']['urn:synthetic:levelRaw'].append(literal('8'))
  with self.assertRaisesRegex(ValueError,'AMBIGUOUS_REQUIRED_FIELD'):self.build(r)
 def test_08_missing_required_field(self):
  r=copy.deepcopy(self.lex);del r['properties']['urn:synthetic:source']
  with self.assertRaisesRegex(ValueError,'REQUIRED_FIELD_MISSING'):self.build(r)
 def test_09_predicate_collision(self):
  r=copy.deepcopy(self.lex);r['properties']['urn:other:source']=[iri(self.src['stable_id'])]
  with self.assertRaisesRegex(ValueError,'PREDICATE_COLLISION'):self.build(r)
 def test_10_page_hold(self):
  r=copy.deepcopy(self.lex);r['properties']['urn:synthetic:printedPage']=[literal('unknown')]
  z=self.build(r)['candidate']['source_locator'];self.assertEqual(z['printed_page_label_recorded_raw'],'unknown');self.assertIsNone(z['printed_page_numeric_candidate']);self.assertIsNone(z['pdf_page_index_zero_based']);self.assertIsNone(z['pdf_page_number_one_based'])
 def test_11_rights_and_raw_replay(self):
  x=self.build(self.lex);self.assertEqual(x['rights_scope'],RIGHTS_SCOPE);self.assertEqual(x['provenance']['raw_line_sha256'],sha(line_bytes(x['raw_rdf'])))
  Draft202012Validator(read_json(HERE/'stage.schema.json')).validate(x)
 def test_12_sql_wrong_kind(self):
  l=self.build(self.lex);h=self.build(self.han);l['candidate']['typed_links']={'source':{'graph':h['provenance']['graph'],'source_entity_id':h['provenance']['source_entity_id'],'source_rdf_kind':'SourceRecord'}}
  with self.assertRaises(sqlite3.IntegrityError):verify_sql([l,h])
 def test_13_wrong_required_term_kind(self):
  r=copy.deepcopy(self.lex);r['properties']['urn:synthetic:levelRaw']=[iri('urn:wrong')]
  with self.assertRaisesRegex(ValueError,'WRONG_REQUIRED_TERM_KIND'):self.build(r)
 def test_14_scope_not_pedagogical(self):
  c=self.build(self.lex)['candidate'];self.assertEqual(c['scope_topic_semantics'],'SOURCE_SCOPE_ONLY_NOT_PEDAGOGICAL_RELATION');self.assertEqual(c['semantic_refs'],[])
if __name__=='__main__':unittest.main(verbosity=2)
