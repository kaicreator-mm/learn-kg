"""Adversarial unit tests for the finite F/E composition guards.

These tests assert the contract directly. They are not independent professional
oracles, learner evidence, CQ/LC acceptance, or runtime authorization.
"""
import hashlib
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from copy import deepcopy
from semantic_checks import FUN, fixtures, dig, _evidence_pair_valid, VISUAL_ACCESSIBILITY_EVIDENCE, F04_CLOCK_CONTRACT


def case(owner, name):
    return deepcopy(next(x for x in fixtures() if x[0] == owner and x[1] == name)[2])


def seal(obj, key):
    obj[key] = dig({k: v for k, v in obj.items() if k != key})
    return obj


class F03Tests(unittest.TestCase):
    def test_visual_route_requires_construct_and_accessibility(self):
        x = case('F03', 'VISUAL_RECOGNITION_SYNTHETIC')
        self.assertEqual(FUN['F03'](x), 'PUBLIC_RESOURCE_CANDIDATE_WITH_SEPARATE_RIGHTS_CHECK')
        x.pop('visual_accessibility_evidence')
        self.assertEqual(FUN['F03'](x), 'HOLD')
        for name in ('VISUAL_ACCESSIBILITY_RESOURCE_MISMATCH_HOLD','VISUAL_ACCESSIBILITY_DIGEST_MISMATCH_HOLD','VISUAL_ACCESSIBILITY_SCOPE_MISMATCH_HOLD'):
            self.assertEqual(FUN['F03'](case('F03', name)), 'HOLD')

    def test_unknown_modality_and_construct_fail_closed(self):
        x = case('F03', 'UNSUPPORTED_VIDEO_MODALITY_HOLD')
        self.assertEqual(FUN['F03'](x), 'HOLD')
        x = case('F03', 'UNSUPPORTED_CONSTRUCT_HOLD')
        self.assertEqual(FUN['F03'](x), 'HOLD')
        x = case('F03', 'MISSING_MODALITY_HOLD')
        self.assertEqual(FUN['F03'](x), 'HOLD')

    def test_only_declared_mapping_is_accepted(self):
        x = case('F03', 'AUDIO_FOR_READING_REJECT')
        self.assertEqual(FUN['F03'](x), 'REJECT_CONSTRUCT_SUBSTITUTION')
        x = case('F03', 'TEXT_READING_SYNTHETIC')
        self.assertEqual(FUN['F03'](x), 'PUBLIC_RESOURCE_CANDIDATE_WITH_SEPARATE_RIGHTS_CHECK')


class F04Tests(unittest.TestCase):
    def test_missing_generated_answer_and_retest_do_not_promote(self):
        x = case('F04', 'UNASSISTED_INDEPENDENT')
        x.pop('generated_answer')
        self.assertEqual(FUN['F04'](x), 'UNKNOWN')
        x = case('F04', 'UNASSISTED_INDEPENDENT')
        x['retest_event'] = None
        self.assertEqual(FUN['F04'](x), 'UNKNOWN')

    def test_retest_must_bind_the_same_learner_identity(self):
        x = case('F04', 'UNASSISTED_INDEPENDENT')
        x['retest_event']['learner_id'] = 'OTHER-LEARNER'
        seal(x['retest_event'], 'event_record_sha256')
        self.assertEqual(FUN['F04'](x), 'HOLD')

    def test_new_variant_and_event_hash_are_mandatory(self):
        x = case('F04', 'UNASSISTED_INDEPENDENT')
        x['retest_event']['variant_id'] = x['initial_response_event']['variant_id']
        seal(x['retest_event'], 'event_record_sha256')
        self.assertEqual(FUN['F04'](x), 'HOLD')
        x = case('F04', 'UNASSISTED_INDEPENDENT')
        x['retest_event']['event_record_sha256'] = '0' * 64
        self.assertEqual(FUN['F04'](x), 'HOLD')

    def test_retest_requires_exact_construct_scoring_and_unassisted_status(self):
        x = case('F04', 'UNASSISTED_INDEPENDENT')
        x['retest_event']['assistance_status'] = 'ASSISTED'
        seal(x['retest_event'], 'event_record_sha256')
        self.assertEqual(FUN['F04'](x), 'ASSISTED_NOT_INDEPENDENT')
        x = case('F04', 'UNASSISTED_INDEPENDENT')
        x['retest_event']['scoring_binding']['scoring_version'] = 'S2'
        seal(x['retest_event'], 'event_record_sha256')
        self.assertEqual(FUN['F04'](x), 'HOLD')

    def test_empty_task_and_scoring_versions_never_promote(self):
        for name in ('EMPTY_TASK_VERSION_TOP_AND_EVENTS_HOLD','EMPTY_SCORING_VERSION_TOP_AND_EVENTS_HOLD',
                     'EMPTY_RETEST_TASK_VERSION_HOLD','EMPTY_RETEST_SCORING_VERSION_HOLD'):
            self.assertEqual(FUN['F04'](case('F04', name)), 'HOLD')

    def test_clock_domains_skew_and_recording_order_are_pinned(self):
        x = case('F04', 'UNASSISTED_INDEPENDENT')
        self.assertEqual(x['clock_contract'], F04_CLOCK_CONTRACT)
        for name in ('UNKNOWN_CLOCK_DOMAIN_HOLD','CLOCK_SKEW_EXCEEDED_HOLD','RECORDED_AT_ORDER_INVALID_HOLD'):
            self.assertEqual(FUN['F04'](case('F04', name)), 'HOLD')
        x['clock_contract']['event_clock_domain'] = 'LOCAL'
        self.assertEqual(FUN['F04'](x), 'HOLD')

    def test_hints_do_not_contaminate_a_separate_independent_retest(self):
        x = case('F04', 'HINTED_THEN_INDEPENDENT_RETEST')
        self.assertEqual(FUN['F04'](x), 'INDEPENDENT_RETEST_OBSERVATION')
        x = case('F04', 'IDENTICAL_DUPLICATE_HINT_IDEMPOTENT')
        self.assertEqual(FUN['F04'](x), 'ASSISTED_NOT_INDEPENDENT')
        x = case('F04', 'CONFLICTING_DUPLICATE_HINT_HOLD')
        self.assertEqual(FUN['F04'](x), 'HOLD')


class F05Tests(unittest.TestCase):
    def test_nonempty_wrong_scoring_version_is_rejected(self):
        x = case('F05', 'SEPARATE_CHANNELS')
        x['score']['scoring_version'] = 'S2'
        self.assertEqual(FUN['F05'](x), 'HOLD')

    def test_caller_cannot_rebind_the_composition_scoring_version(self):
        self.assertEqual(FUN['F05'](case('F05', 'EXPECTED_SCORING_VERSION_REBOUND_HOLD')), 'HOLD')

    def test_missing_expected_version_is_rejected(self):
        x = case('F05', 'SEPARATE_CHANNELS')
        x.pop('expected_scoring_version')
        self.assertEqual(FUN['F05'](x), 'HOLD')

    def test_missing_score_remains_unknown(self):
        x = case('F05', 'SEPARATE_CHANNELS')
        x['score'] = {'status': 'MISSING'}
        result = FUN['F05'](x)
        self.assertEqual(result['channels']['score'], {'status': 'UNKNOWN', 'reason': 'MISSING'})
        self.assertEqual(result['combined_mastery'], 'NOT_INFERRED')


class F07Tests(unittest.TestCase):
    def test_reviewer_and_unknown_exit_never_suggest(self):
        self.assertEqual(FUN['F07'](case('F07', 'REVIEWER_READ_ONLY_REFUSE')), 'REFUSE')
        self.assertEqual(FUN['F07'](case('F07', 'EXIT_UNKNOWN_CLARIFY')), 'CLARIFY')
        self.assertEqual(FUN['F07'](case('F07', 'USER_EXIT_STOP')), 'STOP')

    def test_facilitator_requires_scoped_time_bound_assignment(self):
        self.assertEqual(FUN['F07'](case('F07', 'FACILITATOR_ASSIGNED_SCOPE_OPTION')), 'HOLD')
        self.assertEqual(FUN['F07'](case('F07', 'FACILITATOR_SCOPE_MISMATCH_REFUSE')), 'REFUSE')
        self.assertEqual(FUN['F07'](case('F07', 'EXPIRED_FACILITATOR_AUTHORITY_REFUSE')), 'REFUSE')

    def test_environment_profile_is_task_bound_current_and_digest_checked(self):
        for name in ('ENVIRONMENT_PROFILE_HASH_TAMPER_HOLD','STALE_ENVIRONMENT_PROFILE_HOLD','ENVIRONMENT_TASK_VERSION_MISMATCH_HOLD'):
            self.assertEqual(FUN['F07'](case('F07', name)), 'HOLD')

    def test_canonical_f07_policy_has_no_suggest_route_until_resolver_exists(self):
        root = Path(__file__).resolve().parents[3]
        records = [json.loads(line) for line in (root/'knowledge/v0.1.0/learning-process-cumulative-r3/F07.jsonl').read_text().splitlines()]
        policy = next(x for x in records if x['stable_id']=='F07.POLICY')
        self.assertFalse(any(rule['action']=='SUGGEST' for rule in policy['rules']))
        guard = next(x for x in records if x['stable_id']=='F07.GUARD.OFFER_LEARNER')
        fields = {x['field'] for x in guard['clauses']}
        self.assertTrue({'role_authority.resolver_status','role_authority.resolver_id','support_request.event_sha256','environment_profile.profile_sha256'} <= fields)
        unavailable = next(x for x in records if x['stable_id']=='F07.GUARD.UNAVAILABLE')
        self.assertEqual(unavailable['combination'],'ANY')

    def test_authority_and_support_request_digests_are_checked(self):
        self.assertEqual(FUN['F07'](case('F07', 'AUTHORITY_HASH_MISMATCH_HOLD')), 'HOLD')
        x = case('F07', 'LEARNER_SELF_SESSION_RESOLVER_UNBOUND_HOLD')
        x['support_request']['event_sha256'] = '0' * 64
        self.assertEqual(FUN['F07'](x), 'HOLD')
        self.assertEqual(FUN['F07'](case('F07', 'GENERIC_PERMISSION_BOOLEAN_NOT_AUTHORITY_CLARIFY')), 'CLARIFY')


class A07Tests(unittest.TestCase):
    def test_exit_must_be_exact_false_and_unknown_never_suggests(self):
        for name in ('EXIT_MISSING_CLARIFY','EXIT_NULL_CLARIFY'):
            self.assertEqual(FUN['A07'](case('A07', name))['action'], 'CLARIFY')
        self.assertEqual(FUN['A07'](case('A07','USER_EXIT_STOP'))['action'], 'STOP')

    def test_a07_consumes_f07_and_never_bypasses_unbound_authority(self):
        for name in ('PRESERVED_CONSTRUCT_OPTIONAL_SUPPORT','CHANGED_CONSTRUCT_ASSESSMENT_DEFER',
                     'F07_INPUT_MISSING_REQUEST_OBSERVATION','ENVIRONMENT_TASK_VERSION_MISMATCH_HOLD',
                     'STALE_ENVIRONMENT_PROFILE_HOLD'):
            self.assertEqual(FUN['A07'](case('A07', name))['action'], 'REQUEST_OBSERVATION')
        x=case('A07','PRESERVED_CONSTRUCT_OPTIONAL_SUPPORT')
        x.pop('f07_input')
        self.assertEqual(FUN['A07'](x)['action'],'REQUEST_OBSERVATION')

    def test_construct_review_digest_and_task_identity_are_bound(self):
        self.assertEqual(FUN['A07'](case('A07','CONSTRUCT_REVIEW_MISSING_HASH_HOLD'))['action'],'REQUEST_OBSERVATION')
        self.assertEqual(FUN['A07'](case('A07','CONSTRUCT_REVIEW_TASK_VERSION_MISMATCH_HOLD'))['action'],'REQUEST_OBSERVATION')
        root=Path(__file__).resolve().parents[3]
        records=[json.loads(line) for line in (root/'knowledge/v0.1.0/learning-process-cumulative-r3/A07.jsonl').read_text().splitlines()]
        policy=next(x for x in records if x['stable_id']=='A07.POLICY')
        self.assertFalse(any(rule['action']=='SUGGEST' for rule in policy['rules']))
        composition=next(x for x in records if x['stable_id']=='A07.COMPOSITION')
        refs={x['stable_id'] for x in composition['condition_refs']}
        self.assertTrue({'F07.GUARD.EXIT_UNKNOWN','F07.GUARD.LEARNER_AUTH_UNBOUND','F07.GUARD.OFFER_LEARNER'} <= refs)


class E01Tests(unittest.TestCase):
    def test_boolean_approval_is_not_evidence(self):
        x = case('E01', 'LEGACY_BOOLEAN_APPROVAL_NOT_EVIDENCE_HOLD')
        self.assertEqual(FUN['E01'](x), 'HOLD')
        x = case('E01', 'PINNED_PROTOCOL_AWAITING_APPROVAL_AND_REVIEW_HOLD')
        x['approved'] = True
        x['protocol_frozen'] = True
        x['independent_review'] = True
        self.assertEqual(FUN['E01'](x), 'HOLD')

    def test_plan_pin_and_assignment_compatibility_are_required(self):
        self.assertEqual(FUN['E01'](case('E01', 'ASSIGNMENT_UNIT_METHOD_MISMATCH_HOLD')), 'HOLD')
        self.assertEqual(FUN['E01'](case('E01', 'ANALYSIS_PLAN_REF_MISMATCH_HOLD')), 'HOLD')
        self.assertEqual(FUN['E01'](case('E01', 'ANALYSIS_PLAN_SUMMARY_MISMATCH_HOLD')), 'HOLD')
        self.assertEqual(FUN['E01'](case('E01', 'INVALID_ANALYSIS_PLAN_HOLD')), 'HOLD')

    def test_direct_write_and_noncausal_boundaries(self):
        self.assertEqual(FUN['E01'](case('E01', 'DIRECT_KNOWLEDGE_WRITE_REFUSE')), 'REFUSE')
        self.assertEqual(FUN['E01'](case('E01', 'DIRECT_KNOWLEDGE_WRITE_UNKNOWN_HOLD')), 'HOLD')
        self.assertEqual(FUN['E01'](case('E01', 'SIMULATION_NOT_EFFECT')), 'SIMULATION_ONLY_NOT_EFFECT')
        self.assertEqual(FUN['E01'](case('E01', 'ASSIGNMENT_UNVERIFIED_DESCRIPTIVE_ONLY')), 'DESCRIPTIVE_ONLY_NO_CAUSAL_ESTIMATE')

    def test_external_evidence_must_be_distinct_time_valid_and_hash_matching(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root/'approval.json').write_text('approval')
            (root/'review.json').write_text('review')
            approval = {'kind':'RESEARCH_PROTOCOL_APPROVAL','decision':'APPROVED','subject_id':'E01.PROTOCOL','subject_version':'V2',
                        'analysis_plan_sha256':'a'*64,'repository':'kaicreator-mm/learn-kg','issue_number':1,'comment_id':10,
                        'artifact_path':'approval.json','artifact_sha256':hashlib.sha256(b'approval').hexdigest(),
                        'authority_id':'AUTH-A','issued_at':1,'expires_at':200}
            review = {'kind':'INDEPENDENT_NON_WRITER_REVIEW','decision':'ACCEPT_SCOPED','subject_id':'E01.PROTOCOL','subject_version':'V2',
                      'analysis_plan_sha256':'a'*64,'repository':'kaicreator-mm/learn-kg','issue_number':1,'comment_id':11,
                      'artifact_path':'review.json','artifact_sha256':hashlib.sha256(b'review').hexdigest(),
                      'authority_id':'AUTH-B','issued_at':2,'expires_at':200}
            self.assertTrue(_evidence_pair_valid(approval, review, 'a'*64, 100, root))
            duplicate = dict(review, comment_id=10)
            self.assertFalse(_evidence_pair_valid(approval, duplicate, 'a'*64, 100, root))
            self.assertFalse(_evidence_pair_valid(approval, dict(review, expires_at=99), 'a'*64, 100, root))
            self.assertFalse(_evidence_pair_valid(approval, dict(review, issued_at=101), 'a'*64, 100, root))
            self.assertFalse(_evidence_pair_valid(approval, dict(review, artifact_path='../review.json'), 'a'*64, 100, root))
            self.assertFalse(_evidence_pair_valid(approval, dict(review, artifact_sha256='0'*64), 'a'*64, 100, root))

    def test_candidate_policy_never_suggests_without_trusted_evidence_resolver(self):
        root = Path(__file__).resolve().parents[3]
        records = [json.loads(line) for line in (root/'knowledge/v0.1.0/learning-process-cumulative-r3/E01.jsonl').read_text().splitlines()]
        policy = next(x for x in records if x['stable_id']=='E01.POLICY.CANDIDATE')
        self.assertFalse(any(rule['action']=='SUGGEST' for rule in policy['rules']))
        gate = next(x for x in records if x['stable_id']=='E01.GUARD.CANDIDATE_VERSION')
        fields = {x['field'] for x in gate['clauses']}
        self.assertTrue({'approval_evidence_ref.kind','approval_evidence_ref.comment_id','approval_evidence_ref.artifact_sha256',
                         'independent_review_evidence_ref.kind','independent_review_evidence_ref.comment_id',
                         'independent_review_evidence_ref.artifact_sha256','direct_knowledge_write'} <= fields)

    def test_typed_receipt_pointers_still_hold_without_trusted_resolver(self):
        self.assertEqual(FUN['E01'](case('E01', 'UNRESOLVED_TYPED_APPROVAL_AND_REVIEW_HOLD')), 'HOLD')


class BuilderExpectationConsistencyTests(unittest.TestCase):
    def test_all_finite_builder_expectations_match(self):
        for owner, name, payload, expected in fixtures():
            with self.subTest(owner=owner, case=name):
                self.assertEqual(FUN[owner](payload), expected)


if __name__ == '__main__':
    unittest.main()
