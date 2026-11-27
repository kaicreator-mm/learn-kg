"""V00 finite synthetic import/flow witness; not a general flow engine."""
import json
import math
import pathlib
import sys
import tempfile

from tools.knowledge_import.importer import Importer, canonical, digest, parse, need
from tools.knowledge_import.test_importer import Fixture, ref
from tools.knowledge_import.test_mapping_witness import packages

ROOT = pathlib.Path(__file__).resolve().parents[2]
FIXTURES = ROOT / 'docs/implementation/v00/fixtures.json'

def load_record(im, reference):
    """Fetch exact typed identity from the selected in-memory package only."""
    key = reference['package_id'], reference['version']
    spec = im.mapping['record_tables'][reference['kind']]
    c = im.connections[key]
    fields = spec['fields']
    names = list(fields)
    columns = ','.join('"' + k + '"' for k in names)
    row = c.execute(
        'SELECT ' + columns + ' FROM "' + spec['table'] + '" WHERE package_id=? AND version=? AND stable_id=? AND kind=? AND owner=?',
        (*key, reference['stable_id'], reference['kind'], reference['owner'])
    ).fetchone()
    need(row is not None, 'V00_UNRESOLVED_IDENTITY', str(reference))
    return {k: parse(v.encode()) if fields[k]['encoding'] == 'CANONICAL_JSON' else v for k, v in zip(names, row)}

def setup(f, budget):
    def mutate(e, c, h, p):
        flow = next(x for x in p if x['kind'] == 'FlowSpec')
        activity = ref('learning-process','P01','Activity','Activity')
        cond = ref('learning-core','K09','ConditionSpec','ConditionSpec')
        flow['steps'] = [{'id':s,'activity_ref':activity,'max_attempts':1,'checkpoint':True} for s in ('start','check')]
        flow['transitions'] = [
            {'from_step':s,'to_step':t,'event':'complete','condition_ref':cond,'priority':1,'consumes_budget':True}
            for s,t in [('start','check'),('check','done')]
        ] + [
            {'from_step':s,'to_step':'stop','event':'stop','condition_ref':None,'priority':0,'consumes_budget':False}
            for s in ('start','check')
        ]
        flow['max_events'] = budget
    return packages(f, mutate)[0]

def condition(im, reference, event):
    if reference is None:
        return True
    need(reference['kind'] == 'ConditionSpec', 'V00_UNSUPPORTED_KIND')
    r = load_record(im, reference)
    need(r['combination']=='ALL' and r['unknown']=='HOLD','V00_UNSUPPORTED_CONDITION')
    values = []
    for c in r['clauses']:
        v, expected = event.get(c['field']), c['value']
        if c['op']=='EQ' and type(expected) is bool:
            values.append(v == expected if type(v) is bool else None)
        elif c['op']=='GE' and type(expected) in (int,float):
            values.append(v >= expected if type(v) in (int,float) and math.isfinite(v) else None)
        else:
            need(False,'V00_UNSUPPORTED_CLAUSE')
    return None if None in values else all(values)

def execute(im, events):
    flow = load_record(im, ref('learning-process','P01','FlowSpec','FlowSpec'))
    need(flow['effect']=='TEMPLATE_ONLY' and not flow['parallel_joins'],'V00_UNSUPPORTED_FLOW')
    steps = {s['id']:s for s in flow['steps']}
    terminals = {t['id']:t['outcome'] for t in flow['terminals']}
    node = flow['entry']
    visited = [node]
    consumed = 0
    def result(reason):
        return {'outcome':terminals.get(node,'HOLD'),'visited':visited,'consumed':consumed,'reason':reason}
    def hold(reason):
        nonlocal node
        node = flow['unknown_terminal']
        visited.append(node)
        return result(reason)
    for ev in events:
        if node in terminals:
            return result('TERMINAL')
        step = steps[node]
        activity = load_record(im, step['activity_ref'])
        # Only this acyclic fixture is supported; no arbitrary retry or learner action.
        need(step['max_attempts']==1 and activity['budget']==2,'V00_UNSUPPORTED_STEP')
        candidates = [t for t in flow['transitions'] if t['from_step']==node and t['event']==ev.get('event')]
        if len(candidates)!=1:
            return hold('UNKNOWN_EVENT')
        t = candidates[0]
        if t['consumes_budget'] and consumed >= flow['max_events']:
            return hold('BUDGET_EXHAUSTED')
        v = condition(im,t['condition_ref'],ev)
        if v is not True:
            return hold('CONDITION_UNKNOWN' if v is None else 'CONDITION_FALSE')
        consumed += int(t['consumes_budget'])
        node = t['to_step']
        need(node not in visited,'V00_UNSUPPORTED_CYCLE')
        visited.append(node)
    return result('TERMINAL' if node in terminals else 'EVENTS_EXHAUSTED')

def run():
    spec = parse(FIXTURES.read_bytes())
    rows = []
    for c in spec['cases']:
        with tempfile.TemporaryDirectory() as d:
            f = Fixture(d)
            key = setup(f,c['event_budget'])
            im = Importer(f.root, mode='research', catalog=f.catalog)
            try:
                report = im.run(key)
                actual = execute(im,c['events'])
                need(actual == c['expect'],'V00_EXPECTATION_MISMATCH',c['id'])
                need(all(path=='' for conn in im.connections.values() for _,_,path in conn.execute('PRAGMA database_list')),'V00_PERSISTENCE')
                rows.append({'id':c['id'],'input_digest':digest(canonical(c).encode()),'manifest_pins':[{ 'package':list(k),'sha256':v.sha256} for k,v in sorted(f.catalog.items())],'import_report_digest':digest(canonical(report).encode()),'actual':actual,'expected':c['expect'],'result':'PASS_BUILDER_ONLY'})
            finally:
                im.close()
    return {'scope':'V00_FINITE_SYNTHETIC_NOT_QUALIFICATION','fixture_sha256':digest(FIXTURES.read_bytes()),'cases':rows,'passed':len(rows),'persistent_sqlite':False,'release_authority':'NOT_GRANTED','independent_oracle':'NOT_RUN'}

if __name__=='__main__':
    print(json.dumps(run(),ensure_ascii=False,indent=2))
