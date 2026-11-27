"""Independent structural and migration invariants for the F/E remediation candidate."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOC = Path(__file__).resolve().parent
PKG = ROOT / 'knowledge/v0.1.0/learning-process-cumulative-r3'
OLD = ROOT / 'knowledge/v0.1.0/learning-process-cumulative-r2'
BASE = 'b08f0ccd5fce03093871d5020bd674134c8e530a'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dig(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def remap(value):
    if isinstance(value, list):
        return [remap(x) for x in value]
    if isinstance(value, dict):
        result = {k: remap(v) for k, v in value.items()}
        if result.get('package_id') == 'learning-process' and result.get('version') == '0.1.0-process-candidate-2':
            result['version'] = '0.1.0-process-candidate-3'
        return result
    return value


def records(manifest_dir, manifest):
    result = {}
    for f in manifest['files']:
        p = manifest_dir / f['path']
        assert sha(p) == f['sha256'], p
        for line in p.read_text(encoding='utf-8').splitlines():
            obj = json.loads(line)
            assert obj['stable_id'] not in result
            result[obj['stable_id']] = obj
    return result


def git_bytes(path):
    return subprocess.check_output(['git', '-C', str(ROOT), 'show', f'{BASE}:{path}'])


def main():
    old_manifest = load(OLD / 'learning-process.manifest.json')
    new_manifest = load(PKG / 'learning-process.manifest.json')
    old = records(OLD, old_manifest)
    new = records(PKG, new_manifest)
    migration = load(DOC / 'migration.json')
    assert len(old) == len(new) - 272 == 1312
    assert migration['migrated_record_count'] == 1312
    entries = {x['stable_id']: x for x in migration['records']}
    assert len(entries) == 1312 and set(entries) == set(old)
    changed = unchanged = 0
    for stable_id, old_record in old.items():
        expected = remap(old_record)
        actual = new[stable_id]
        assert actual == expected, stable_id
        entry = entries[stable_id]
        assert entry['old_record_sha256'] == dig(old_record), stable_id
        assert entry['new_record_sha256'] == dig(actual), stable_id
        assert entry['change'] == ('INTERNAL_PROCESS_VERSION_REF_ONLY' if old_record != actual else 'UNCHANGED')
        if old_record != actual:
            changed += 1
        else:
            unchanged += 1
    assert (changed, unchanged) == (1147, 165)
    assert all('0.1.0-process-candidate-2' not in json.dumps(x, ensure_ascii=False) for x in new.values())

    manifest_hash = sha(PKG / 'learning-process.manifest.json')
    result = load(DOC / 'results.json')
    sql = load(DOC / 'sql-results.json')
    coverage = load(DOC / 'coverage.json')
    assert result['manifest_sha256'] == sql['manifest_sha256'] == coverage['manifest_sha256'] == manifest_hash
    assert sum(x['record_count'] for x in new_manifest['files']) == 1584
    assert sum(x['record_count'] for x in new_manifest['files'] if not x['path'].startswith('P')) == 272
    assert result['case_count'] == sql['cases'] == 97
    assert result['counts'] == {'F03': 12, 'F04': 18, 'F05': 11, 'F07': 14, 'A07': 26, 'E01': 16}
    assert len(sql['cross_module_bindings']) == 6 and len(sql['nested_typed_bindings']) == 1

    design = load(DOC / 'design.json')
    design['modules'].update(load(DOC / 'remediation-design.json')['modules'])
    fixture_names = {}
    for f in load(DOC / 'fixtures.json'):
        fixture_names.setdefault(f['owner'], set()).add(f['name'])
    for owner, module in design['modules'].items():
        assert len(module['cases']) == len(set(module['cases']))
        assert set(module['cases']) == fixture_names[owner]

    # P01-P10 and A07 are byte-stable relative to the reviewed candidate base.
    for owner in [f'P{i:02d}' for i in range(1, 11)] + ['A07']:
        path = f'knowledge/v0.1.0/learning-process-cumulative-r3/{owner}.jsonl'
        assert git_bytes(path) == (PKG / f'{owner}.jsonl').read_bytes(), owner
    assert git_bytes('docs/implementation/f-composition-preparation/migration.json') == (DOC / 'migration.json').read_bytes()

    # F03: all three explicit modality/construct routes are represented.
    f03 = [x for x in new.values() if x['owner'] == 'F03']
    assert {x['label'] for x in f03 if x['kind'] == 'Modality'} == {'TEXT', 'AUDIO', 'VISUAL'}
    f03_comp = new['F03.COMPOSITION']
    f03_guard_ids = {x['stable_id'] for x in f03_comp['condition_refs']}
    assert {'F03.GUARD.AUDIO', 'F03.GUARD.TEXT_READING', 'F03.GUARD.VISUAL'} <= f03_guard_ids

    # F04: the interaction binds both the independent-retest observation and scoring observation.
    interaction = new['F04.INTERACTION']
    obs_ids = {x['stable_id'] for x in interaction['observation_refs']}
    assert {'F04.OBS.INITIAL', 'F04.OBS.HINT', 'F04.OBS.FINAL', 'F04.OBS.RETEST', 'P06.ACT.OBSERVE.OBS'} <= obs_ids
    assert 'bare independent_retest boolean is never evidence' in interaction['input_contract']

    # F05: exact expected/observed scoring-version comparison is part of the guard.
    version_guard = new['F05.GUARD.VERSION']
    assert {'expected_scoring_version', 'score.scoring_version'} == {x['field'] for x in version_guard['clauses']}

    # F07: reviewer refusal, exit fail-close, role scope, and time/session-bound authority.
    f07_guard_ids = {x['stable_id'] for x in new['F07.COMPOSITION']['condition_refs']}
    assert {'F07.GUARD.REVIEWER', 'F07.GUARD.EXIT_UNKNOWN', 'F07.GUARD.OFFER_LEARNER', 'F07.GUARD.FACILITATOR_UNBOUND'} <= f07_guard_ids

    # E01: protocol's canonical strings reproduce the separately pinned analysis plan.
    plan_path = DOC / 'analysis-plan.json'
    plan = load(plan_path)
    plan_hash = sha(plan_path)
    protocol = new['E01.PROTOCOL']
    population = json.loads(protocol['population_scope'])
    estimand = json.loads(protocol['estimand'])
    followup = json.loads(protocol['followup'])
    uncertainty = json.loads(protocol['uncertainty'])
    assert population == plan['population']
    assert estimand['allocation'] == plan['allocation']
    assert estimand['analysis_plan_ref'] == 'docs/implementation/f-composition-preparation/analysis-plan.json'
    assert estimand['analysis_plan_sha256'] == plan_hash
    assert estimand['analysis_plan_summary'] == plan['analysis_plan_summary']
    assert followup == plan['followup']
    assert uncertainty['authority_status'] == 'NO_TRUSTED_APPROVAL_OR_REVIEW_RESOLVER_BOUND'
    assert any(p['source_path'].endswith('/analysis-plan.json') and p['source_sha256'] == plan_hash for p in protocol['provenance'])
    assert coverage['analysis_plan']['sha256'] == plan_hash
    assert coverage['analysis_plan']['observed_data_analysis'] == 'HOLD'

    # Candidate/release boundaries remain closed.
    assert new_manifest['status'] == 'CANDIDATE' and new_manifest['rights'] == 'HOLD'
    assert new_manifest['qualification_receipt_refs'] == []
    assert coverage['independent_review']['result'] == 'REWORK_REQUIRED'
    assert coverage['independent_review_delta'] == 'NOT_RUN'
    assert coverage['a07_independent_review'] == 'NOT_RUN'
    assert coverage['p_candidate3_exact_rebind'] == 'PENDING_FOR_P01_P10'
    assert coverage['release'] == 'NOT_ELIGIBLE'

    print(json.dumps({
        'status': 'REMEDIATION_STRUCTURAL_INVARIANTS_PASS',
        'manifest_sha256': manifest_hash,
        'migrated_p_records': len(old),
        'migration_changed': changed,
        'migration_unchanged': unchanged,
        'new_records': 272,
        'total_records': 1584,
        'builder_cases': 97,
        'f_e_cases': 71,
        'a07_cases_out_of_review_scope': 26,
        'cross_module_bindings': 6,
        'nested_typed_bindings': 1,
        'analysis_plan_sha256': plan_hash,
        'release': 'NOT_ELIGIBLE'
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
