"""Adversarial unit tests for the finite F/E composition guards.

These tests assert the contract directly. They are not independent professional
oracles, learner evidence, CQ/LC acceptance, or runtime authorization.
"""
import hashlib
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from copy import deepcopy
from semantic_checks import FUN, fixtures, dig


def case(owner, name):
    return deepcopy(next(x for x in fixtures() if x[0] == owner and x[1] == name)[2])


def seal(obj, key):
    obj[key] = dig({k: v for k, v in obj.items() if k != key})
    return obj


class F03Tests(unittest.TestCase):
    def test_visual_route_requires_construct_and_accessibility(self):
        x = case('F03', 'VISUAL_RECOGNITION_SYNTHETIC')
        self.assertEqual(FUN['F03'](x), 'PUBLIC_RESOURCE_CANDIDATE_WITH_SEPARATE_RIGHTS_CHECK')
        x.pop('visual_accessibility_verified')
        self.assertEqual(FUN['F03'](x), 'HOLD')

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

    def test_authority_and_support_request_digests_are_checked(self):
        self.assertEqual(FUN['F07'](case('F07', 'AUTHORITY_HASH_MISMATCH_HOLD')), 'HOLD')
        x = case('F07', 'AUTHORIZED_ACCESSIBLE_OPTION')
        x['support_request']['event_sha256'] = '0' * 64
        self.assertEqual(FUN['F07'](x), 'HOLD')
        self.assertEqual(FUN['F07'](case('F07', 'GENERIC_PERMISSION_BOOLEAN_NOT_AUTHORITY_CLARIFY')), 'CLARIFY')


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

    def test_typed_receipt_pointers_still_hold_without_trusted_resolver(self):
        self.assertEqual(FUN['E01'](case('E01', 'UNRESOLVED_TYPED_APPROVAL_AND_REVIEW_HOLD')), 'HOLD')


class BuilderExpectationConsistencyTests(unittest.TestCase):
    def test_all_finite_builder_expectations_match(self):
        for owner, name, payload, expected in fixtures():
            with self.subTest(owner=owner, case=name):
                self.assertEqual(FUN[owner](payload), expected)


if __name__ == '__main__':
    unittest.main()
