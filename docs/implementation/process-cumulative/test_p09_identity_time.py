import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / 'knowledge/v0.1.0/learning-process-cumulative-r2'
sys.path.insert(0, str(Path(__file__).resolve().parent))
from semantic_checks import fixture_rows, p09, MIN_DELAYED_INTERVAL_SECONDS, MAX_UTC_EPOCH_SECONDS


def independent_oracle(x):
    """Test-only reference calculation; never reads builder expected_spec or p09()."""
    if not isinstance(x, dict):
        return 'HOLD'
    if not all(isinstance(x.get(k), str) and x[k].strip()
               for k in ('goal', 'scoring_version', 'trained_family', 'transfer_dimension')):
        return 'HOLD'
    observations = x.get('observations')
    if not isinstance(observations, list) or len(observations) != 3:
        return 'HOLD'
    stages = ('IMMEDIATE', 'DELAYED', 'TRANSFER')
    identity = None
    clock = None
    event_times = []
    record_times = []
    event_ids = set()
    criteria = {}
    for index, (item, stage) in enumerate(zip(observations, stages)):
        if not isinstance(item, dict) or item.get('stage') != stage:
            return 'HOLD'
        event_id = item.get('id')
        if not isinstance(event_id, str) or not event_id or event_id.strip() != event_id or event_id in event_ids:
            return 'HOLD'
        event_ids.add(event_id)
        current_identity = item.get('learner_identity')
        if (not isinstance(current_identity, dict)
            or set(current_identity) != {'kind', 'subject_id', 'identity_version'}
            or current_identity.get('kind') != 'LEARNER_SUBJECT'
            or not isinstance(current_identity.get('subject_id'), str)
            or not current_identity['subject_id']
            or current_identity['subject_id'].strip() != current_identity['subject_id']
            or len(current_identity['subject_id']) > 128
            or current_identity.get('identity_version') != 'V1'):
            return 'HOLD'
        if identity is None:
            identity = copy.deepcopy(current_identity)
        elif current_identity != identity:
            return 'HOLD'
        current_clock = (
            item.get('time_basis'), item.get('time_unit'),
            item.get('recording_time_basis'), item.get('recording_time_unit'),
            item.get('clock_source_id'), item.get('recording_clock_source_id')
        )
        if (current_clock[:4] != ('UTC_EPOCH_SECONDS', 'SECOND', 'UTC_EPOCH_SECONDS', 'SECOND')
            or not isinstance(current_clock[4], str) or not current_clock[4].strip()
            or not isinstance(current_clock[5], str) or not current_clock[5].strip()):
            return 'HOLD'
        if clock is None:
            clock = current_clock
        elif current_clock != clock:
            return 'HOLD'
        event_time = item.get('observed_at')
        record_time = item.get('recorded_at')
        if (type(event_time) is not int or type(record_time) is not int
            or event_time <= 0 or record_time <= 0
            or event_time > MAX_UTC_EPOCH_SECONDS or record_time > MAX_UTC_EPOCH_SECONDS):
            return 'HOLD'
        event_times.append(event_time)
        record_times.append(record_time)
        if (item.get('goal') != x['goal']
            or item.get('scoring_version') != x['scoring_version']
            or item.get('independent') is not True
            or item.get('construct_match') is not True
            or item.get('scoring_version_match') is not True
            or not isinstance(item.get('family'), str) or not item['family'].strip()
            or type(item.get('criteria_met')) is not bool):
            return 'HOLD'
        if stage == 'TRANSFER':
            if (item['family'] == x['trained_family']
                or item.get('dimension') != x['transfer_dimension']
                or item.get('new_task_family') is not True
                or item.get('transfer_dimension_declared') is not True):
                return 'HOLD'
        elif item['family'] != x['trained_family']:
            return 'HOLD'
        criteria[stage] = item['criteria_met']
    if any(b <= a for a, b in zip(event_times, event_times[1:])):
        return 'HOLD'
    if any(b < a for a, b in zip(record_times, record_times[1:])):
        return 'HOLD'
    delay = event_times[1] - event_times[0]
    if delay < MIN_DELAYED_INTERVAL_SECONDS:
        return 'HOLD'
    return {
        'status': 'THREE_TASK_OBSERVATIONS_ONLY',
        'criteria': criteria,
        'learner_identity_binding': identity,
        'computed_same_learner_identity': True,
        'immediate_subject_id': identity['subject_id'],
        'delayed_subject_id': identity['subject_id'],
        'transfer_subject_id': identity['subject_id'],
        'time_basis': 'UTC_EPOCH_SECONDS',
        'time_unit': 'SECOND',
        'recording_time_basis': 'UTC_EPOCH_SECONDS',
        'recording_time_unit': 'SECOND',
        'clock_source_id': clock[4],
        'recording_clock_source_id': clock[5],
        'computed_delay_seconds': delay,
        'minimum_delay_seconds': MIN_DELAYED_INTERVAL_SECONDS,
        'computed_timestamp_order_valid': True,
        'computed_recording_order_valid': True
    }


class P09IdentityTimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = [(x, y) for owner, x, y in fixture_rows() if owner == 'P09']

    def test_all_finite_fixtures_match_independent_timestamp_identity_oracle(self):
        self.assertEqual(len(self.rows), 38)
        for value, expected in self.rows:
            with self.subTest(case=value):
                oracle = independent_oracle(value)
                self.assertEqual(oracle, expected)
                self.assertEqual(p09(value), oracle)

    def test_exact_minimum_interval_is_accepted(self):
        case, expected = next((x, y) for x, y in self.rows if y != 'HOLD')
        self.assertEqual(case['observations'][1]['observed_at'] - case['observations'][0]['observed_at'],
                         MIN_DELAYED_INTERVAL_SECONDS)
        self.assertEqual(independent_oracle(case), expected)
        self.assertEqual(p09(case)['computed_delay_seconds'], 86400)

    def test_delay_positive_and_caller_threshold_are_not_authoritative(self):
        insufficient = next(x for x, y in self.rows if x.get('delay_positive') is True and y == 'HOLD')
        sufficient = next(x for x, y in self.rows if x.get('delay_positive') is False and y != 'HOLD')
        self.assertEqual(p09(insufficient), 'HOLD')
        self.assertNotEqual(p09(sufficient), 'HOLD')
        valid = copy.deepcopy(sufficient)
        valid['delay_positive'] = True
        valid['minimum_delay_seconds'] = 999999999
        self.assertEqual(p09(valid)['computed_delay_seconds'], 86400)
        short = copy.deepcopy(insufficient)
        short['minimum_delay_seconds'] = 1
        self.assertEqual(p09(short), 'HOLD')

    def test_each_observation_must_bind_the_same_typed_subject(self):
        base = next(x for x, y in self.rows if y != 'HOLD')
        for index in range(3):
            altered = copy.deepcopy(base)
            altered['observations'][index]['learner_identity']['subject_id'] = 'SUBJECT-OTHER'
            self.assertEqual(p09(altered), 'HOLD')
        altered = copy.deepcopy(base)
        altered['observations'][1]['learner_identity']['identity_version'] = 'V2'
        self.assertEqual(p09(altered), 'HOLD')
        altered = copy.deepcopy(base)
        altered['observations'][2]['learner_identity'] = []
        self.assertEqual(p09(altered), 'HOLD')

    def test_time_basis_unit_order_and_delay_boundaries(self):
        base = next(x for x, y in self.rows if y != 'HOLD')
        for index, field, value in (
            (0, 'time_basis', None),
            (1, 'time_unit', 'MINUTE'),
            (2, 'recording_time_basis', 'LOCAL_TIME'),
            (2, 'recording_time_unit', 'MILLISECOND'),
            (1, 'clock_source_id', 'OTHER-CLOCK'),
            (1, 'recording_clock_source_id', 'OTHER-SERVER')
        ):
            altered = copy.deepcopy(base)
            if value is None:
                altered['observations'][index].pop(field)
            else:
                altered['observations'][index][field] = value
            self.assertEqual(p09(altered), 'HOLD')
        altered = copy.deepcopy(base)
        altered['observations'][1]['observed_at'] -= 1
        self.assertEqual(p09(altered), 'HOLD')
        altered = copy.deepcopy(base)
        altered['observations'][2]['observed_at'] = altered['observations'][1]['observed_at']
        self.assertEqual(p09(altered), 'HOLD')

    def test_recorded_at_is_not_cross_compared_with_observed_at(self):
        case = next(x for x, y in self.rows if y != 'HOLD')
        altered = copy.deepcopy(case)
        altered['observations'][0]['recorded_at'] = altered['observations'][0]['observed_at'] - 100
        self.assertEqual(p09(altered), independent_oracle(altered))
        self.assertNotEqual(p09(altered), 'HOLD')

    def test_recording_order_is_checked_within_its_own_clock(self):
        case = next(x for x, y in self.rows if y != 'HOLD')
        altered = copy.deepcopy(case)
        altered['observations'][2]['recorded_at'] = altered['observations'][1]['recorded_at'] - 1
        self.assertEqual(p09(altered), 'HOLD')

    def test_canonical_observations_flow_guards_and_policy_bind_the_protocol(self):
        records = [json.loads(line) for line in (PACKAGE / 'P09.jsonl').read_text().splitlines()]
        by_id = {item['stable_id']: item for item in records}
        for stable_id in ('P09.ACT.IMMEDIATE.OBS', 'P09.ACT.DELAYED.OBS', 'P09.ACT.NOVEL.OBS'):
            observation = by_id[stable_id]
            self.assertEqual(observation['unit'], 'UTC_EPOCH_SECONDS')
            conditions = set(observation['conditions'])
            self.assertIn('learner_identity.kind=LEARNER_SUBJECT', conditions)
            self.assertIn('time_unit=SECOND', conditions)
        flow = by_id['P09.FLOW']
        self.assertTrue(any('至少86400秒' in value for value in flow['conditions']))
        final = next(t for t in flow['transitions'] if t['from_step'] == 'SUMMARY' and t['to_step'] == 'COMPLETE')
        self.assertEqual(final['condition_ref']['stable_id'], 'P09.GUARD.COMPOSITE_VALID')
        for stable_id in ('P09.GUARD.SAME_LEARNER', 'P09.GUARD.TIME_BASIS',
                          'P09.GUARD.MIN_DELAY', 'P09.GUARD.COMPOSITE_VALID'):
            self.assertIn(stable_id, by_id)
        policy = by_id['P09.POLICY']
        self.assertEqual(policy['policy_type'], 'ASSESSMENT')
        self.assertEqual(policy['effect'], 'ADVICE_ONLY')
        self.assertEqual(policy['rules'][0]['action'], 'REQUEST_OBSERVATION')
        self.assertEqual(policy['rules'][0]['condition_ref']['stable_id'], 'P09.GUARD.COMPOSITE_VALID')
        self.assertNotIn('SUGGEST', {r['action'] for r in policy['rules']})
        self.assertIn('移除SUGGEST路由', ''.join(policy['conditions']))
        composition = by_id['P09.COMPOSITION']
        self.assertIn('P09.POLICY', {r['stable_id'] for r in composition['output_refs']})
        self.assertIn('P09.GUARD.MIN_DELAY', {r['stable_id'] for r in composition['condition_refs']})


if __name__ == '__main__':
    unittest.main()
