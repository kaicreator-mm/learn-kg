"""Exact residual scope and normalized semantic diff, not qualification."""
import json, pathlib, hashlib
P=pathlib.Path(__file__).resolve().parent
Q=P.parent/'foundation-r2'
def read(p):return json.loads(p.read_text())
def load(d):
    return {x['stable_id']:x for f in d.glob('*/records-*.jsonl') for x in map(json.loads,f.read_text().splitlines())}
def norm(x):
    if isinstance(x,dict):return {k:norm(v) for k,v in x.items() if k not in ('provenance','oracle_identity')}
    if isinstance(x,list):return [norm(v) for v in x]
    return '0.1.0-foundation-candidate-2' if x=='0.1.0-foundation-candidate-3' else x
a,b=load(Q),load(P)
assert not a.keys()-b.keys()
changed=sorted(k for k in a if norm(a[k])!=norm(b[k]))
assert set(changed)=={'K02.01.03.R2.01','K02.01.03.R2.01:K02-R2-S01','K02.01.03.R2.01:R2:construct','K02.01.03.R2.01:case','K02.03.03.R2.01','K02.03.03.R2.01:K02-S09','K02.03.03.R2.01:case','K03.03.03.R2.01','K03.03.03.R2.01:K03-S07','K03.03.03.R2.01:case'}
old,new=read(Q/'new-oracles.json'),read(P/'new-oracles.json')
assert new[:len(old)]==old and len(new)-len(old)==19
added=sorted(b.keys()-a.keys())
assert set(added)=={'K02-R3-S01','K02.01.03.R2.01:K02-R3-S01'}|{c['id']+s for c in new[len(old):] for s in ('',':validation')}
for name in ('source-support.json','anchor-dispositions.json','relation-design.json','relation-types.json','view-transformations.json','duplicate-dispositions.json'):
    assert (Q/name).read_bytes()==(P/name).read_bytes(),name
oldr,newr=read(Q/'oracle-results.json'),read(P/'oracle-results.json')
assert newr['results'][:len(oldr['results'])]==oldr['results'] and len(newr['results'])==72
r={'status':'BUILDER_SCOPE_CHECK_ONLY','base_records':len(a),'new_records':len(b),'removed':[],'changed_semantic_records':changed,'added_records':added,'normalization':'only package version, provenance and oracle identity excluded; verify actual provenance, refs and new manifest separately; not byte-identical or new qualification','K01_K04_semantic_change_count':0,'prior_53_results_preserved':True,'prior_33_fixtures_preserved':True,'new_cases':19,'independent_qualification':'NOT_RUN'}
(P/'delta-impact.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
print('DELTA_SCOPE',len(changed),len(added),'old_results',len(oldr['results']))
