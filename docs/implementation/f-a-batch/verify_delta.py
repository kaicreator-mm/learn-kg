"""R2 exact normalized delta proof against reviewed candidate-4 R1."""
import hashlib,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
P=ROOT/'knowledge/v0.1.0/learning-process-cumulative-r4'
BASE='8e9ec9c2dc5e87da1b132e5239c265628fe775f1'
def old(p):return subprocess.check_output(['git','show',BASE+':'+p.relative_to(ROOT).as_posix()],cwd=ROOT)
def sha(b):return hashlib.sha256(b).hexdigest()
def dig(x):return sha(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
def load(b):return json.loads(b)
def ptr(d,p):
 for s in p.split('/')[1:]:
  s=s.replace('~1','/').replace('~0','~');d=d[int(s)] if isinstance(d,list) else d[s]
 return d
def rows(b):return {r['stable_id']:r for r in map(json.loads,b.splitlines())}
def main():
 design=HERE/'design.json';od=load(old(design));nd=load(design.read_bytes())
 oh,nh=sha(old(design)),sha(design.read_bytes())
 assert od['modules']==nd['modules'] and nd['cases'][:77]==od['cases'] and len(nd['cases'])==107
 affected={'F08','A05','A08'};assert {z['owner'] for z in nd['cases'][77:]}==affected
 report={}
 for p in sorted(P.glob('*.jsonl')):
  a,b=rows(old(p)),rows(p.read_bytes());unchanged=0;checksum=0;changed=[];added=sorted(set(b)-set(a))
  assert set(a)<=set(b)
  for i,x in a.items():
   y=b[i]
   if x==y:unchanged+=1;continue
   for u,v in zip(x['provenance'],y['provenance']):
    if u!=v:
     assert u['source_path']==design.relative_to(ROOT).as_posix() and u['source_sha256']==oh and v['source_sha256']==nh
     assert u['json_pointer']==v['json_pointer'] and ptr(od,u['json_pointer'])==ptr(nd,v['json_pointer'])
     u['source_sha256']=nh
   if x==y:checksum+=1;continue
   assert p.stem in affected and i==p.stem+'.COMPOSITION',i
   assert y['evidence_refs'][:len(x['evidence_refs'])]==x['evidence_refs']
   extra=y['evidence_refs'][len(x['evidence_refs']):];assert len(extra)==20 and {v['stable_id'] for v in extra}==set(added)
   x['evidence_refs']=y['evidence_refs'];assert x==y
   changed.append(i)
  if p.stem in affected:
   assert len(added)==20 and len(changed)==1
   for z in added:assert z.startswith(p.stem+'.R4.CASE.')
  else:assert not added and not changed
  report[p.stem]=dict(old_records=len(a),new_records=len(b),unchanged=unchanged,provenance_hash_only=checksum,affected_compositions=changed,added_case_validation_ids=added)
 # Frozen old dependency inputs, all direct qualified claims, old object bindings;
 # new owner-set digests propagate only through explicitly consumed preparation refs.
 ob=load(old(HERE/'bindings.json'));nb=load((HERE/'bindings.json').read_bytes())
 assert ob['claim_bindings']==nb['claim_bindings']
 for owner,refs in ob['input_receipts'].items():
  assert len(refs)==len(nb['input_receipts'][owner])
  for x,y in zip(refs,nb['input_receipts'][owner]):
   if x!=y:
    assert x.get('state')==y.get('state')=='PREPARATION_ONLY_NO_RECEIPT'
    dep=x['task_id'];assert x['owner_record_set_sha256']==ob['owner_preparation_sets'][dep] and y['owner_record_set_sha256']==nb['owner_preparation_sets'][dep]
    assert {k:v for k,v in x.items() if k!='owner_record_set_sha256'}=={k:v for k,v in y.items() if k!='owner_record_set_sha256'}
 for owner,rs in ob['object_bindings'].items():
  for id,x in rs.items():
   y=nb['object_bindings'][owner][id]
   if x!=y:
    assert x['source']==y['source']=='PREPARATION'
    assert {k:v for k,v in x.items() if k!='record_sha256'}=={k:v for k,v in y.items() if k!='record_sha256'}
    shard=P/(x['ref']['owner']+'.jsonl')
    assert x['record_sha256']==dig(rows(old(shard))[id]) and y['record_sha256']==dig(rows(shard.read_bytes())[id])
 assert old(HERE/'migration.json')!= (HERE/'migration.json').read_bytes()
 om=load(old(HERE/'migration.json'));nm=load((HERE/'migration.json').read_bytes())
 assert om['records']==nm['records'] and om['counts']==nm['counts']
 # Old private pins untouched: hash actual private manifests/shards and descriptor closure.
 for path,pin in [
 ('/root/.local/share/learn-kg-private/h01-h04-source-index-20261128-r1','8f4f7ae3757537c6229ca019d33808216b34fd02ac3e7246d6f3bcdce2ef079b'),
 ('/root/.local/share/learn-kg-private/h05-h07-source-index-20261128-r1','93c9ceaf3d697274f31880566ec59ccff16a559492fea632378a1b277804cb97')]:
  r=Path(path);raw=(r/'manifest.json').read_bytes();assert sha(raw)==pin
  for n,v in load(raw)['files'].items():assert sha((r/n).read_bytes())==v['sha256']
 r=Path('/root/.local/share/learn-kg-private/db03-private-canonical-20261128-r2')
 raw=(r/'adapter-manifest.json').read_bytes();assert sha(raw)=='0c8f69deaae06766f685eec40ed14978a2db06451821ca4d1bc2e26dee60aff2'
 m=load(raw)
 for n,v in m['documents'].items():assert sha((r/n).read_bytes())==v['sha256']
 for n,h in m['pins'].items():assert sha((r/n).read_bytes())==h
 for k in ('evidence','chinese'):
  for f in load((r/(k+'.manifest.json')).read_bytes())['files']:assert sha((r/f['path']).read_bytes())==f['sha256']
 result=dict(status='AUTHOR_DELTA_PROOF_NOT_QUALIFICATION',review_base=BASE,review_comment=7243959073,old_design_sha256=oh,new_design_sha256=nh,prior_cases_unchanged=77,added_cases=30,record_delta=report,prior_migration_records_unchanged=1725,prior_qualified_claim_bindings_unchanged=True,preparation_and_object_binding_deltas_exact=True,private_pins_verified=True)
 (HERE/'delta-invariance.json').write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
 print('DELTA',sum(v['unchanged'] for v in report.values()),sum(v['provenance_hash_only'] for v in report.values()),sum(len(v['affected_compositions']) for v in report.values()),sum(len(v['added_case_validation_ids']) for v in report.values()))
if __name__=='__main__':main()
