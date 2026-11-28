"""Verify bounded cumulative H snapshot, exact old records and selected public closure."""
import collections,hashlib,json,sys,tempfile,multiprocessing
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
from tools.knowledge_import.importer import Importer,ManifestPin,Reject,need
from tools.knowledge_import.candidate_pointer import read_pointer,switch,resolve
from semantic_rules import evaluate
sys.path.append(str(HERE.parent/'db03'))
from public_views import current_catalog
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dig(r):return hashlib.sha256(json.dumps(r,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def main():
 B=ROOT/'knowledge/v0.1.0';old=B/'chinese-h01-h04-r1';new=B/'chinese-cumulative-r2'
 om=load(old/'chinese.manifest.json');nm=load(new/'chinese.manifest.json');ov=om['version'];nv=nm['version'];migration=load(HERE/'migration.json')
 def read(pkg):
  out={}
  for f in ('chinese.manifest.json','evidence.manifest.json'):
   m=load(pkg/f)
   for x in m['files']:
    p=pkg/x['path'];assert sha(p)==x['sha256']
    for l in p.read_text().splitlines():
     r=json.loads(l);assert r['stable_id'] not in out;out[r['stable_id']]=r
  return out
 o=read(old);n=read(new)
 def rebind(x):
  if isinstance(x,list):return [rebind(y) for y in x]
  if isinstance(x,dict):
   y={k:rebind(v) for k,v in x.items()}
   if set(y)=={'package_id','version','stable_id','kind','owner'} and y['package_id'] in ('evidence','chinese'):
    assert y['version']==ov;y['version']=nv
   return y
  return x
 assert len(o)==1294
 for id,r in o.items():assert n[id]==rebind(r),id
 expected={z['id']:z for z in migration['records']};assert set(expected)==set(o)
 for k,r in o.items():assert expected[k]['old_sha256']==dig(r) and expected[k]['new_sha256']==dig(n[k])
 # Match existing H01-H04 current receipt pins, owner identity and all accepted candidate IDs.
 d=load(ROOT/'docs/implementation/task-dag.json');ts={t['id']:t for t in d['tasks']};old_bindings={}
 for h in ('H01','H02','H03','H04'):
  p=ROOT/ts[h]['current_receipt'];r=load(p);assert r['validation']['independent_result']=='ACCEPT_SCOPED'
  for f in r['output']:assert sha(ROOT/f['path'])==f['sha256']
  ids=r['scope_restriction']['candidate_claim_ids'];assert len(ids)==4
  assert all(n[i]['owner']==h and n[i]['status']=='CANDIDATE' and n[i]['kind']=='Claim' for i in ids)
  old_bindings[h]={'receipt_sha256':sha(p),'content_digest':r['content_digest'],'receipt_id':r['receipt_id'],'old_manifest_sha256':sha(old/'chinese.manifest.json'),'rebound_manifest_sha256':sha(new/'chinese.manifest.json'),'candidate_claim_ids':ids}
 # Replay current registered K/P/F/A/E roots plus one cumulative Chinese preparation root.
 roots,catalog,bindings,extension,oldh=current_catalog();h=('chinese',nv)
 assert oldh in roots and h in catalog
 del roots[oldh];roots[h]=catalog[h]
 im=Importer(ROOT,mode='research',catalog=catalog,extension=extension)
 try:
  for k in roots:im._load(k,set())
  links={k:im._validate_refs(k) for k in im.packages}
  for k,rr in links.items():im._materialize(k,rr)
  assert oldh not in im.packages and h in im.packages
  counts=[]
  for k,c in im.connections.items():
   assert c.execute('PRAGMA query_only').fetchone()==(1,) and all(not x[2] for x in c.execute('PRAGMA database_list'))
   assert c.execute('PRAGMA foreign_key_check').fetchall()==[]
   a=c.execute('SELECT count(*) FROM local_registry').fetchone()[0];b=c.execute('SELECT count(*) FROM typed_refs').fetchone()[0]
   assert a==len(im.packages[k][3]) and b==len(links[k])
   counts.append(dict(package=list(k),manifest_sha256=catalog[k].sha256,records=a,typed_refs=b))
  c=im.connections[h];results=load(HERE/'validation-results.json')['tests'];prior=load(HERE.parent/'h01-h04-batch/validation-results.json')['tests']
  assert len(results)==74 and len(prior)==95
  for z in prior+results:
   row=c.execute('SELECT input_spec,expected_spec FROM record_case WHERE stable_id=?',(z['id'],)).fetchone()
   assert row and evaluate(z['rule'],json.loads(row[0]))==json.loads(row[1])==z['actual'],z['id']
  # All new canonical template refs loaded from SQL: specific task/construct/object/observation chains.
  tasks=[r for r in n.values() if r['kind']=='TaskSpec' and r['owner']=='H06']
  assert len(tasks)==5
  for t in tasks:
   assert t['construct_ref']['version']==nv and n[t['construct_ref']['stable_id']]['kind']=='SkillType'
   for r in t['object_refs']:assert n[r['stable_id']]['kind']=='LearningObject'
   for r in t['observation_refs']:assert n[r['stable_id']]['construct_ref']==t['construct_ref']
  comp=n['H06.CONFIRM.COMPETENCY'];assert {r['kind'] for r in comp['evidence_refs']}=={'TaskSpec','ObservationSpec'}
  assert any(r['owner']=='H05' for r in comp['claim_refs'])
  assert n['H07.GF0025.2021']['effective_date']=='2021-07-01' and n['H07.HSK3.ANNOUNCEMENT']['effective_date'] is None
  assert all(r['standard_ref']['stable_id']=='H07.GF0025.2021' for r in n.values() if r['kind']=='StandardBand' and r['owner']=='H07')
  totals=dict(records=sum(x['records'] for x in counts),typed_refs=sum(x['typed_refs'] for x in counts),packages=len(counts))
  # Actual old reader kept open while candidate pointer switches to cumulative preparation.
  oldcatalog={k:catalog[k] for k in [oldh,('evidence',ov)]}
  oldim=Importer(ROOT,mode='research',catalog=oldcatalog);oldim.run(oldh)
  try:
   oldcon=oldim.connections[oldh];initial=oldcon.execute('SELECT count(*) FROM local_registry').fetchone()[0]
   pins=[[*k,catalog[k].path,catalog[k].sha256] for k in [oldh,('evidence',ov),h,('evidence',nv)]]
   a=dict(mode='CANDIDATE_RESEARCH_ONLY',select=list(oldh),catalog=pins);b=dict(mode='CANDIDATE_RESEARCH_ONLY',select=list(h),catalog=pins)
   with tempfile.TemporaryDirectory(prefix='h567-pointer-') as td:
    p=Path(td);switch(p,ROOT,a,None)
    for phase,code,want in [('before_replace',71,a),('after_replace',72,b)]:
     child=multiprocessing.get_context('fork').Process(target=switch,args=(p,ROOT,b,a),kwargs={'_crash':phase});child.start();child.join(60)
     if child.is_alive():child.terminate();child.join();raise RuntimeError('POINTER_TIMEOUT')
     assert child.exitcode==code and read_pointer(p)==want
    assert oldcon.execute('SELECT count(*) FROM local_registry').fetchone()[0]==initial
    assert oldcon.execute('PRAGMA query_only').fetchone()==(1,)
    assert len(resolve(read_pointer(p),ROOT)['packages'])==2
    switch(p,ROOT,a,b);assert read_pointer(p)==a
    assert not list(p.rglob('*.sqlite*'))
  finally:oldim.close()
 finally:im.close()
 report=dict(status='PREPARATION_ONLY_CUMULATIVE_REBIND_NOT_REGISTERED',old_H_bindings=old_bindings,old_records_invariant=len(o),migration_counts=migration['counts'],new_manifest_sha256=sha(new/'chinese.manifest.json'),current_registered_public_bindings=bindings,public_closure=totals,package_counts=counts,actual_SQL_cases=len(prior)+len(results),new_cases=len(results),inherited_cases=len(prior),canonical_task_chains=len(tasks),pointer_recovery=dict(before_replace=True,after_replace=True,live_old_reader=True,rollback=True,physical_power_loss='HOLD_NOT_TESTED'),private_adapter='EXACT_PREVIOUS_SCOPE_ONLY',persistent_sqlite=False)
 (HERE/'cumulative-evidence.json').write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('old_records_invariant','migration_counts','new_manifest_sha256','public_closure','actual_SQL_cases','canonical_task_chains','pointer_recovery')},ensure_ascii=False))
if __name__=='__main__':main()
