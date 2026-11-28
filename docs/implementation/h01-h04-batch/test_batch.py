import copy,json,sys,unittest
from pathlib import Path
from semantic_rules import evaluate
from private_subject_index import split_reading_pos,latin_surface
HERE=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
 def test_01_all_finite_rules(self):
  d=json.loads((HERE/'professional-design.json').read_text());c={z['id']:z for z in d['claims']}
  self.assertEqual(len(d['cases']),95)
  for z in d['cases']:
   self.assertEqual(evaluate(c[z['claim']]['rule'],z['input']),z['expected'],z['id'])
 def test_02_missing_all_rules(self):
  for c in json.loads((HERE/'professional-design.json').read_text())['claims']:
   for x in ({},[],None,False):self.assertEqual(evaluate(c['rule'],x),'HOLD',c['id'])
 def test_03_malformed_tones(self):
  for t in ([True,3],[3,3,3],[3,0],None):
   self.assertEqual(evaluate('tone_pair',{'unit':'TONE_CATEGORY','same_domain':True,'citation_tones':t,'rule_scope':'THIRD_TONE_PAIR_ONLY'}),'HOLD')
 def test_04_malformed_context_no_exception(self):
  self.assertEqual(evaluate('variant_context',{'mapping_version':'UAX38_41_EXAMPLE_CONTEXT','source':'脏','direction':'SC_TO_TC','sense':[]}), 'HOLD')
  self.assertEqual(evaluate('de_marker',{'framework':'UD_ZH_V2','query':'PARTICLE_ANNOTATION','marker':'的','function':{}}),'HOLD')
 def test_05_exact_pos_split(self):
  for raw in ('mǎ 名','shǎo 形、动','xiāng-jī 名',"xi'an 名"):
   x=split_reading_pos(raw);self.assertEqual(x['status'],'RECORDED_SURFACE_SPLIT_CANDIDATE');self.assertEqual(x['reading_surface_raw']+x['separator_raw']+x['pos_label_raw'],raw)
 def test_06_unknown_suffix_hold(self):
  for raw in ('mǎ 未知','mǎ 名、名','mǎ 名、','mǎ  名','汉字 名','mǎ 名 extra','mǎ 名\n'):
   self.assertEqual(split_reading_pos(raw)['status'],'HOLD_UNSPLIT_RAW')
 def test_07_reading_only_hold_pos(self):
  for raw in ('mǎ','lüè','a','Xi’an'):
   x=split_reading_pos(raw);self.assertEqual(x['status'],'READING_SURFACE_ONLY_POS_UNKNOWN_HOLD');self.assertIsNone(x['pos_labels_raw']);self.assertEqual(x['reading_surface_raw'],raw)
 def test_08_surface_not_phonotactics(self):
  self.assertTrue(latin_surface('zzzz')) # syntactic envelope, not legal pinyin
  for raw in ('-mǎ','mǎ-','ma--ma','1ma','汉','\u0301a','ma '):self.assertFalse(latin_surface(raw))
 def test_09_claim_scope_and_coverage(self):
  d=json.loads((HERE/'coverage.json').read_text());self.assertEqual(sum(x['topics'] for x in d['stats'].values()),102)
  self.assertEqual(sum(x['candidate_claims'] for x in d['stats'].values()),16)
  self.assertEqual(sum(x['held_only_topics'] for x in d['stats'].values()),86)
  for rows in d['modules'].values():
   for r in rows:self.assertEqual(r['full_depth'],'NOT_ESTABLISHED');self.assertEqual(r['qualification'],'NOT_RUN')
if __name__=='__main__':unittest.main(verbosity=2)
