"""Exact-SHA, schema, migration-scope and P09-only preservation verifier."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOC = Path(__file__).resolve().parent
PKG = ROOT / 'knowledge/v0.1.0/learning-process-cumulative-r2'
BASE = '4a8cd2b6aef68d5a574842325ef9fddaa0559c16'
P09_PATH = 'knowledge/v0.1.0/learning-process-cumulative-r2/P09.jsonl'
MANIFEST_PATH = 'knowledge/v0.1.0/learning-process-cumulative-r2/learning-process.manifest.json'


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha(path):
    return sha_bytes(Path(path).read_bytes())


def git_bytes(path):
    return subprocess.check_output(['git', '-C', str(ROOT), 'show', f'{BASE}:{path}'])


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def main():
    base_manifest = json.loads(git_bytes(MANIFEST_PATH))
    manifest = load(PKG / 'learning-process.manifest.json')
    assert manifest['package_id'] == 'learning-process'
    assert manifest['version'] == '0.1.0-process-candidate-2'
    assert manifest['status'] == 'CANDIDATE' and manifest['rights'] == 'HOLD'
    assert manifest['qualification_receipt_refs'] == []

    base_files = {x['path']: x for x in base_manifest['files']}
    files = {x['path']: x for x in manifest['files']}
    assert set(base_files) == set(files)
    changed_shards = []
    for owner in [f'P{i:02}' for i in range(1, 11) if i != 9]:
        rel = f'knowledge/v0.1.0/learning-process-cumulative-r2/{owner}.jsonl'
        actual = (PKG / f'{owner}.jsonl').read_bytes()
        expected = git_bytes(rel)
        assert actual == expected, f'{owner} canonical shard changed'
        assert files[f'{owner}.jsonl']['sha256'] == base_files[f'{owner}.jsonl']['sha256']
    assert (DOC / 'design.json').read_bytes() == git_bytes('docs/implementation/process-cumulative/design.json')
    assert (DOC / 'migration.json').read_bytes() == git_bytes('docs/implementation/process-cumulative/migration.json')
    assert (ROOT / 'docs/implementation/task-dag.json').read_bytes() == git_bytes('docs/implementation/task-dag.json')

    records = [json.loads(line) for line in (PKG / 'P09.jsonl').read_text(encoding='utf-8').splitlines()]
    by_id = {x['stable_id']: x for x in records}
    assert len(records) == len(by_id) == 197
    assert sum(x['kind'] == 'Case' for x in records) == 81
    assert sum(x['kind'] == 'Validation' for x in records) == 81
    assert sum(x['kind'] == 'PolicySpec' for x in records) == 1
    assert sum(x['kind'] == 'ObservationSpec' for x in records) == 4
    p09_contract_sha = sha(DOC / 'p09-remediation.json')
    for item in records:
        assert item['provenance'][0]['source_path'] == 'docs/implementation/process-cumulative/p09-remediation.json'
        assert item['provenance'][0]['source_sha256'] == p09_contract_sha
    for stage in ('IMMEDIATE', 'DELAYED', 'NOVEL'):
        obs = by_id[f'P09.ACT.{stage}.OBS']
        assert obs['unit'] == 'UTC_EPOCH_SECONDS'
        assert 'learner_identity.kind=LEARNER_SUBJECT' in obs['conditions']
        assert 'time_unit=SECOND' in obs['conditions']
        assert 'recording_time_unit=SECOND' in obs['conditions']
    assert by_id['P09.ACT.SUMMARY.OBS']['unit'] == 'SUMMARY_RECORD'

    flow = by_id['P09.FLOW']
    assert flow['effect'] == 'TEMPLATE_ONLY' and flow['unknown_terminal'] == 'HOLD'
    assert any('至少86400秒' in x for x in flow['conditions'])
    transitions = flow['transitions']
    for step, event, guard in (
        ('IMMEDIATE', 'IMMEDIATE_RECORDED', 'P09.GUARD.IMMEDIATE'),
        ('DELAYED', 'DELAYED_RECORDED', 'P09.GUARD.DELAYED'),
        ('NOVEL', 'TRANSFER_RECORDED', 'P09.GUARD.NOVEL'),
        ('SUMMARY', 'SUMMARY_RECORDED', 'P09.GUARD.COMPOSITE_VALID')
    ):
        t = next(x for x in transitions if x['from_step'] == step and x['event'] == event)
        assert t['condition_ref']['stable_id'] == guard
    same = by_id['P09.GUARD.SAME_LEARNER']
    assert {'computed_same_learner_identity','immediate_subject_id','delayed_subject_id','transfer_subject_id'} <= {x['field'] for x in same['clauses']}
    time = by_id['P09.GUARD.TIME_BASIS']
    assert {'time_basis','time_unit','recording_time_basis','recording_time_unit',
            'computed_timestamp_order_valid','computed_recording_order_valid'} <= {x['field'] for x in time['clauses']}
    delay = by_id['P09.GUARD.MIN_DELAY']
    delay_fields = {x['field']: x for x in delay['clauses']}
    assert delay_fields['computed_delay_seconds']['op'] == 'GE'
    assert delay_fields['computed_delay_seconds']['value'] == 86400
    composite_fields = {x['field'] for x in by_id['P09.GUARD.COMPOSITE_VALID']['clauses']}
    assert {'computed_same_learner_identity','computed_delay_seconds','evidence_separated','goal_reviewed'} <= composite_fields
    assert not any(x['field'] == 'delay_positive' for x in records if x['kind'] == 'ConditionSpec' for x in x.get('clauses', []))

    policy = by_id['P09.POLICY']
    assert policy['policy_type'] == 'ASSESSMENT' and policy['effect'] == 'ADVICE_ONLY'
    assert policy['rules'][0]['condition_ref']['stable_id'] == 'P09.GUARD.COMPOSITE_VALID'
    assert '不推断真实保持、迁移、掌握或因果效果' in ''.join(policy['conditions'])
    composition = by_id['P09.COMPOSITION']
    assert {'P09.FLOW','P09.POLICY'} <= {x['stable_id'] for x in composition['output_refs']}
    assert {'P09.GUARD.SAME_LEARNER','P09.GUARD.TIME_BASIS','P09.GUARD.MIN_DELAY',
            'P09.GUARD.COMPOSITE_VALID'} <= {x['stable_id'] for x in composition['condition_refs']}

    fixture_rows = load(DOC / 'fixtures.json')
    p09_fixtures = [x for x in fixture_rows if x['owner'] == 'P09']
    assert len(fixture_rows) == 348 and len(p09_fixtures) == 81
    concrete = [x for x in p09_fixtures if x['input'].get('scenario') == 'CONCRETE_FINITE']
    assert len(concrete) == 38
    results = load(DOC / 'results.json')
    assert results['cases'] == 348
    assert results['manifest_sha256'] == sha(PKG / 'learning-process.manifest.json')
    assert results['fixture_sha256'] == sha(DOC / 'fixtures.json')
    assert sum(x['owner'] == 'P09' for x in results['results']) == 81
    assert manifest['files'] == [
        {'path': f'{owner}.jsonl', 'sha256': sha(PKG / f'{owner}.jsonl'),
         'format': 'JSONL_RECORDS',
         'record_count': sum(1 for _ in (PKG / f'{owner}.jsonl').open(encoding='utf-8'))}
        for owner in [f'P{i:02}' for i in range(1, 11)]
    ]
    assert sum(x['record_count'] for x in manifest['files']) == 1377
    assert sum(x['record_count'] for x in manifest['files'] if x['path'] != 'P09.jsonl') == 1180
    assert files['P09.jsonl']['sha256'] != base_files['P09.jsonl']['sha256']

    coverage = load(DOC / 'coverage.json')
    p09_coverage = next(x for x in coverage['modules'] if x['owner'] == 'P09')
    assert p09_coverage['records'] == 197
    assert p09_coverage['finite_cases'] == 81 and p09_coverage['concrete_cases'] == 38
    assert p09_coverage.get('independent_delta_review') in (None, 'PENDING')
    hashes = coverage['p09_remediation']['artifact_hashes']
    expected_hashes = {
        'p09_jsonl_sha256': sha(PKG / 'P09.jsonl'),
        'manifest_sha256': sha(PKG / 'learning-process.manifest.json'),
        'contract_sha256': sha(DOC / 'p09-remediation.json'),
        'fixtures_sha256': sha(DOC / 'fixtures.json'),
        'results_sha256': sha(DOC / 'results.json'),
        'import_receipt_sha256': sha(DOC / 'import-receipt.json'),
        'migration_sha256': sha(DOC / 'migration.json'),
        'bindings_sha256': sha(DOC / 'bindings.json')
    }
    for key, value in expected_hashes.items():
        assert hashes[key] == value, key
    assert coverage['p09_remediation']['independent_delta_review'] == 'PENDING'
    print(json.dumps({
        'status': 'P09_REMEDIATION_INVARIANTS_PASS',
        'base_head': BASE,
        'package_version': manifest['version'],
        'manifest_sha256': sha(PKG / 'learning-process.manifest.json'),
        'p09_contract_sha256': p09_contract_sha,
        'p09_records': len(records),
        'p09_cases': len(p09_fixtures),
        'p09_concrete_identity_time_cases': len(concrete),
        'package_records': sum(x['record_count'] for x in manifest['files']),
        'builder_cases': len(fixture_rows),
        'preserved_canonical_shards': [f'P{i:02}' for i in range(1, 11) if i != 9],
        'changed_canonical_shards': ['P09'],
        'independent_delta_review': 'PENDING',
        'qualification': 'NOT_GRANTED'
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
