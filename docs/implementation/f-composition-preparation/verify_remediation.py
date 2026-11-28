"""Independent structural, projection and migration invariants for the F/E/A07 remediation candidate."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOC = Path(__file__).resolve().parent
PKG = ROOT / 'knowledge/v0.1.0/learning-process-cumulative-r3'
OLD = ROOT / 'knowledge/v0.1.0/learning-process-cumulative-r2'
BASE = 'd1ce8647b29f896849e14a9d7314b9b51c338fdf'
EXPECTED_CASES = {'F03': 15, 'F04': 25, 'F05': 12, 'F07': 17, 'A07': 32, 'E01': 20}
EXPECTED_NEW_RECORDS = 324
EXPECTED_TOTAL_RECORDS = 1725


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


def verify_e01_projection(protocol, plan, plan_hash):
    population = json.loads(protocol['population_scope'])
    estimand = json.loads(protocol['estimand'])
    followup = json.loads(protocol['followup'])
    uncertainty = json.loads(protocol['uncertainty'])
    assert population == plan['population']
    expected_estimand = {
        'allocation': plan['allocation'],
        'intervention': plan['intervention'],
        'comparator': plan['comparator'],
        'primary_outcome': plan['primary_outcome'],
        'analysis_plan_ref': 'docs/implementation/f-composition-preparation/analysis-plan.json',
        'analysis_plan_sha256': plan_hash,
        'analysis_plan_summary': plan['analysis_plan_summary'],
        'estimand': plan['estimand']
    }
    assert estimand == expected_estimand
    assert followup == plan['followup']
    expected_uncertainty = {
        'authority_status': plan['authority_status'],
        'data_status': plan['data_status'],
        'release_status': plan['release_status'],
        'required_evidence': plan['required_evidence'],
        'limits': '没有真实合规研究数据；模拟、离线测试和即时分数不构成长期效果。'
    }
    assert uncertainty == expected_uncertainty
    matches = [p for p in protocol['provenance']
               if p.get('source_path') == 'docs/implementation/f-composition-preparation/analysis-plan.json']
    assert len(matches) == 1
    assert matches[0] == {
        'source_path': 'docs/implementation/f-composition-preparation/analysis-plan.json',
        'source_sha256': plan_hash,
        'json_pointer': '/artifact_id',
        'source_status': 'PROJECT_AUTHORED_FROZEN_CANDIDATE_PLAN'
    }


def main():
    old_manifest = load(OLD / 'learning-process.manifest.json')
    new_manifest = load(PKG / 'learning-process.manifest.json')
    old = records(OLD, old_manifest)
    new = records(PKG, new_manifest)
    migration = load(DOC / 'migration.json')
    assert len(old) == len(new) - EXPECTED_NEW_RECORDS == 1401
    assert migration['migrated_record_count'] == 1401
    entries = {x['stable_id']: x for x in migration['records']}
    assert len(entries) == 1401 and set(entries) == set(old)
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
    assert (changed, unchanged) == (1232, 169)
    def check_refs(value):
        if isinstance(value, dict):
            if value.get('package_id') == 'learning-process' and {'version','owner','kind','stable_id'} <= value.keys():
                assert value['version'] == '0.1.0-process-candidate-3', value
            for child in value.values(): check_refs(child)
        elif isinstance(value, list):
            for child in value: check_refs(child)
    for record in new.values(): check_refs(record)
    # Serialized input_spec strings intentionally preserve adversarial foreign-version inputs.

    manifest_hash = sha(PKG / 'learning-process.manifest.json')
    result = load(DOC / 'results.json')
    sql = load(DOC / 'sql-results.json')
    coverage = load(DOC / 'coverage.json')
    assert result['manifest_sha256'] == sql['manifest_sha256'] == coverage['manifest_sha256'] == manifest_hash
    assert sum(x['record_count'] for x in new_manifest['files']) == EXPECTED_TOTAL_RECORDS
    assert sum(x['record_count'] for x in new_manifest['files'] if not x['path'].startswith('P')) == EXPECTED_NEW_RECORDS
    assert result['case_count'] == sql['cases'] == sum(EXPECTED_CASES.values()) == 121
    assert result['counts'] == EXPECTED_CASES
    assert len(sql['cross_module_bindings']) == 6 and len(sql['nested_typed_bindings']) == 1

    design = load(DOC / 'design.json')
    remediation_design = load(DOC / 'remediation-design.json')
    design['modules'].update(remediation_design['modules'])
    fixture_names = {}
    for f in load(DOC / 'fixtures.json'):
        fixture_names.setdefault(f['owner'], set()).add(f['name'])
    for owner, module in design['modules'].items():
        assert len(module['cases']) == len(set(module['cases']))
        assert set(module['cases']) == fixture_names[owner]

    # Previously independently reviewed candidate-3 professional/composition shards:
    # only P09 changes; other nine P shards and all six F/E/A07 shards are byte-identical.
    for owner in [f'P{i:02d}' for i in range(1, 11) if i != 9] + ['F03','F04','F05','F07','A07','E01']:
        path = f'knowledge/v0.1.0/learning-process-cumulative-r3/{owner}.jsonl'
        assert git_bytes(path) == (PKG / f'{owner}.jsonl').read_bytes(), owner
    assert git_bytes('knowledge/v0.1.0/learning-process-cumulative-r3/P09.jsonl') != (PKG / 'P09.jsonl').read_bytes()
    for name in ('design.json','remediation-design.json','analysis-plan.json','fixtures.json','bindings.json'):
        assert git_bytes('docs/implementation/f-composition-preparation/'+name) == (DOC / name).read_bytes()
    for owner in [f'P{i:02d}' for i in range(1,11)]:
        path=f'knowledge/v0.1.0/learning-process-cumulative-r2/{owner}.jsonl'
        assert subprocess.check_output(['git','-C',str(ROOT),'show','589cd14a042501ce468b9976edefdba2c537e657:'+path]) == (ROOT/path).read_bytes()
    p_rebind=load(DOC/'p-rebind-regression.json')
    assert p_rebind['target_manifest_sha256']==manifest_hash
    assert p_rebind['source_manifest_sha256']==sha(OLD/'learning-process.manifest.json')
    assert (p_rebind['current_cases'],p_rebind['inherited_cases'],p_rebind['total_cases'])==(360,143,503)
    assert p_rebind['qualification']=='NOT_GRANTED' and p_rebind['persistent_sqlite'] is False

    # F03: exact visual-accessibility evidence identity/version/scope/result/digest is pinned.
    f03_comp = new['F03.COMPOSITION']
    f03_guard_ids = {x['stable_id'] for x in f03_comp['condition_refs']}
    assert {'F03.GUARD.AUDIO', 'F03.GUARD.TEXT_READING', 'F03.GUARD.VISUAL',
            'F03.GUARD.VISUAL_ACCESSIBILITY'} <= f03_guard_ids
    visual_guard = new['F03.GUARD.VISUAL_ACCESSIBILITY']
    visual_fields = {x['field'] for x in visual_guard['clauses']}
    assert {'visual_accessibility_evidence.evidence_id','visual_accessibility_evidence.evidence_version',
            'visual_accessibility_evidence.resource_identity','visual_accessibility_evidence.resource_version',
            'visual_accessibility_evidence.modality','visual_accessibility_evidence.required_construct',
            'visual_accessibility_evidence.test_scope','visual_accessibility_evidence.test_result',
            'visual_accessibility_evidence.evidence_sha256'} <= visual_fields

    # F04: nonempty pinned task/scoring versions and explicit clock contract.
    interaction = new['F04.INTERACTION']
    obs_ids = {x['stable_id'] for x in interaction['observation_refs']}
    assert {'F04.OBS.INITIAL', 'F04.OBS.HINT', 'F04.OBS.FINAL', 'F04.OBS.RETEST', 'P06.ACT.OBSERVE.OBS'} <= obs_ids
    assert 'bare independent_retest boolean is never evidence' in interaction['input_contract']
    assert 'maximum 300-second skew' in interaction['input_contract']
    f04_guard_fields = {x['field'] for x in new['F04.GUARD.INDEPENDENT']['clauses']}
    assert {'expected_task_version','task_version','expected_scoring_version','scoring_version',
            'retest_event.task_version','retest_event.scoring_binding.scoring_version',
            'clock_contract.event_clock_domain','clock_contract.recording_clock_domain',
            'clock_contract.clock_sync_status','clock_contract.max_clock_skew_seconds'} <= f04_guard_fields

    # F05: the expected version itself is pinned to the composition's S1 contract.
    version_clauses = {x['field']: x['value'] for x in new['F05.GUARD.VERSION']['clauses']}
    assert version_clauses['expected_scoring_version'] == 'S1'
    assert version_clauses['score.scoring_version'] == 'S1'

    # F07: no policy SUGGEST route exists until a trusted resolver is bound.
    f07_guard_ids = {x['stable_id'] for x in new['F07.COMPOSITION']['condition_refs']}
    assert {'F07.GUARD.REVIEWER','F07.GUARD.EXIT_UNKNOWN','F07.GUARD.OFFER_LEARNER',
            'F07.GUARD.LEARNER_AUTH_UNBOUND','F07.GUARD.FACILITATOR_UNBOUND'} <= f07_guard_ids
    assert not any(x['action'] == 'SUGGEST' for x in new['F07.POLICY']['rules'])
    unavailable = new['F07.GUARD.UNAVAILABLE']
    assert unavailable['combination'] == 'ANY'
    unavailable_fields = {x['field'] for x in unavailable['clauses']}
    assert {'environment_profile.accessible','environment_profile.capability_match'} <= unavailable_fields

    # A07 consumes the exact F07 decision guards and cannot bypass the resolver boundary.
    a07_comp = new['A07.COMPOSITION']
    a07_condition_ids = {x['stable_id'] for x in a07_comp['condition_refs']}
    a07_input_ids = {x['stable_id'] for x in a07_comp['input_refs']}
    required_f07 = {'F07.GUARD.EXIT_UNKNOWN','F07.GUARD.REVIEWER','F07.GUARD.DENY',
                    'F07.GUARD.UNAVAILABLE','F07.GUARD.LEARNER_AUTH_UNBOUND',
                    'F07.GUARD.FACILITATOR_UNBOUND','F07.GUARD.OFFER_LEARNER'}
    assert required_f07 <= a07_condition_ids and required_f07 <= a07_input_ids
    assert not any(x['action'] == 'SUGGEST' for x in new['A07.POLICY']['rules'])
    assert 'construct_review.review_sha256' in {x['field'] for x in new['A07.GUARD.PRESERVED']['clauses']}

    # E01: all four canonical string slots exactly reproduce the frozen plan.
    plan_path = DOC / 'analysis-plan.json'
    plan = load(plan_path)
    plan_hash = sha(plan_path)
    protocol = new['E01.PROTOCOL']
    verify_e01_projection(protocol, plan, plan_hash)
    assert coverage['analysis_plan']['sha256'] == plan_hash
    assert coverage['analysis_plan']['observed_data_analysis'] == 'HOLD'
    assert not any(x['action'] == 'SUGGEST' for x in new['E01.POLICY.CANDIDATE']['rules'])
    e01_gate_fields = {x['field'] for x in new['E01.GUARD.CANDIDATE_VERSION']['clauses']}
    assert {'approval_evidence_ref.kind','approval_evidence_ref.comment_id','approval_evidence_ref.artifact_sha256',
            'approval_evidence_ref.authority_id','independent_review_evidence_ref.kind',
            'independent_review_evidence_ref.comment_id','independent_review_evidence_ref.artifact_sha256',
            'independent_review_evidence_ref.authority_id','direct_knowledge_write'} <= e01_gate_fields

    # Candidate/release boundaries remain closed.
    assert new_manifest['status'] == 'CANDIDATE' and new_manifest['rights'] == 'HOLD'
    assert new_manifest['qualification_receipt_refs'] == []
    assert coverage['independent_review']['result'] == 'REWORK_REQUIRED'
    assert coverage['independent_review_delta'] == 'NOT_RUN'
    assert coverage['a07_independent_review'].startswith('REWORK_REQUIRED_PREVIOUS_SNAPSHOT')
    assert coverage['p_candidate3_exact_rebind'] == 'PENDING_FOR_P01_P10'
    assert coverage['release'] == 'NOT_ELIGIBLE'

    print(json.dumps({
        'status': 'REMEDIATION_STRUCTURAL_INVARIANTS_PASS',
        'manifest_sha256': manifest_hash,
        'migrated_p_records': len(old),
        'migration_changed': changed,
        'migration_unchanged': unchanged,
        'new_records': EXPECTED_NEW_RECORDS,
        'total_records': EXPECTED_TOTAL_RECORDS,
        'builder_cases': 121,
        'f_e_cases': 89,
        'a07_cases': 32,
        'cross_module_bindings': len(sql['cross_module_bindings']),
        'nested_typed_bindings': len(sql['nested_typed_bindings']),
        'analysis_plan_sha256': plan_hash,
        'release': 'NOT_ELIGIBLE'
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
