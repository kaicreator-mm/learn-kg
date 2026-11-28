"""Author bounded cases and fresh denial probes; not independent qualification."""
import json,unittest
from pathlib import Path
from semantic_rules import evaluate
HERE=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
 def test_all_finite(self):
  d=json.loads((HERE/'professional-design.json').read_text());rules={c['id']:c['rule'] for c in d['claims']}
  self.assertEqual(len(d['cases']),74)
  for z in d['cases']:self.assertEqual(evaluate(rules[z['claim']],z['input']),z['expected'],z['id'])
 def test_unknown_shape(self):
  for c in json.loads((HERE/'professional-design.json').read_text())['claims']:
   for x in ({},None,False,[]):self.assertEqual(evaluate(c['rule'],x),'HOLD')
 def test_confirm_stipulated_function(self):
  x=dict(framework='RFC_2024',prior_proposition=True,form='DECLARATIVE',response='CONFIRM')
  for v in (None,False,'true',1):self.assertEqual(evaluate('confirm',dict(x,verified_confirmation_request=v)),'HOLD')
  self.assertEqual(evaluate('confirm',x),'HOLD')
  self.assertEqual(evaluate('confirm',dict(x,verified_confirmation_request=True)),'CONFIRMATION_SEQUENCE')
 def test_mediation_no_language_inference(self):
  x=dict(framework='CEFR',query='MEDIATION_TASK',meaning_access_goal=True,recipient_and_purpose_explicit=True)
  for v in (None,False,'UNKNOWN'):self.assertEqual(evaluate('mediation',dict(x,language_relation=v)),'HOLD')
 def test_modalities(self):
  for s,a,o in [('LISTENING','AUDIO','MEANING_RESPONSE'),('READING','TEXT','MEANING_RESPONSE'),('SPEAKING','AUDIO_OUTPUT','PRODUCTION'),('WRITING','TEXT_OUTPUT','PRODUCTION')]:
   x=dict(framework='ACTFL_2024',query='MODALITY_EVIDENCE',skill=s,artifact=a,observed_operation=o)
   self.assertEqual(evaluate('task_modality',x),'MODALITY_MATCH_ONLY')
   for v in ('UNKNOWN',None):self.assertEqual(evaluate('task_modality',dict(x,artifact=v)),'HOLD')
 def test_can_do_no_mastery(self):
  x=dict(framework='ACTFL_CAN_DO',query='EVIDENCE_SUFFICIENCY_SCREEN',independent=True,distinct_situations=2,distinct_occasions=2)
  self.assertEqual(evaluate('can_do',x),'MULTIPLE_CONTEXT_EVIDENCE_REVIEW_REQUIRED')
  for v in (0,-1,True,1.5,'2',None):self.assertEqual(evaluate('can_do',dict(x,distinct_situations=v)),'HOLD')
 def test_announcement_not_occurrence(self):
  x=dict(source='CTI_51336724',edition='HSK_3.0',query='ACTUAL_OCCURRED')
  self.assertEqual(evaluate('exam_launch',x),'HOLD')
 def test_link_guard(self):
  x=dict(framework='PROJECT_EVIDENCE_GATE',query='CROSS_STANDARD_MAPPING',source_standard='HSK',target_standard='CEFR',source_version='3.0',target_version='2020',empirical_link_evidence=True,mapping_conditions_verified=True)
  self.assertEqual(evaluate('standard_mapping',x),'UNKNOWN_HOLD')
  for v in (True,1,None,'false'):self.assertEqual(evaluate('standard_mapping',dict(x,same_label_only=v)),'UNKNOWN_HOLD')
  self.assertEqual(evaluate('standard_mapping',dict(x,same_label_only=False)),'LINK_EVIDENCE_REVIEW_REQUIRED')
 def test_cross_standard_identity(self):
  x=dict(framework='PROJECT_EVIDENCE_GATE',query='CROSS_STANDARD_MAPPING',source_standard='HSK',source_version='3.0',target_standard='HSK',target_version='3.0',same_label_only=False,empirical_link_evidence=True,mapping_conditions_verified=True)
  for v in ('3.0','2.0','unknown',None):self.assertEqual(evaluate('standard_mapping',dict(x,target_version=v)),'HOLD')
  for v in ('hsk',' HSK','HSK 3.0','UNKNOWN',None,True):self.assertEqual(evaluate('standard_mapping',dict(x,target_standard=v)),'HOLD')
  self.assertEqual(evaluate('standard_mapping',dict(x,target_standard='CEFR',target_version='2020')),'LINK_EVIDENCE_REVIEW_REQUIRED')
 def test_scope_counts(self):
  x=dict(source='MOE_2021_04_02',standard='GF0025-2021',query='COVERAGE_FROM_COUNTS',source_counts_equal=True)
  self.assertEqual(evaluate('gf_totals',x),'HOLD')
  self.assertEqual(evaluate('gf_totals',dict(x,query='REPORTED_TOTALS'))['grammar_points'],572)
if __name__=='__main__':unittest.main(verbosity=2)
