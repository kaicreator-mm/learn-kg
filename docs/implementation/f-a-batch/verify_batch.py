"""Cumulative closure and historical process fixture regression, not full CQ/LC."""
import json,hashlib,sys,collections,importlib.util,tempfile,multiprocessing
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];B=ROOT/'knowledge/v0.1.0'
sys.path[:0]=[str(ROOT),str(HERE.parent/'db03')]
from tools.knowledge_import.importer import Importer,ManifestPin
from tools.knowledge_import.v00_prototype import load_record
from process_pointer import read_pointer,switch,resolve
from tools.knowledge_import.importer import Reject
from semantic_rules import evaluate,_old
from public_views import current_catalog
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dig(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
def main():
 old=B/'learning-process-cumulative-r3';new=B/'learning-process-cumulative-r4';h=B/'chinese-cumulative-r2'
 om=load(old/'learning-process.manifest.json');nm=load(new/'learning-process.manifest.json');hm=load(h/'chinese.manifest.json');ov=om['version'];nv=nm['version'];hv=hm['version']
 def read(m,p):
  out={}
  for f in m['files']:
   fp=p/f['path'];assert sha(fp)==f['sha256']
   for l in fp.read_text().splitlines():
    r=json.loads(l);assert r['stable_id'] not in out;out[r['stable_id']]=r
  return out
 o=read(om,old);n=read(nm,new);hr=read(hm,h)
 def remap(x):
  if isinstance(x,list):return [remap(v) for v in x]
  if isinstance(x,dict):
   y={k:remap(v) for k,v in x.items()}
   if set(y)=={'package_id','version','kind','owner','stable_id'} and y['package_id']=='learning-process' and y['version']==ov:y['version']=nv
   return y
  return x
 mig=load(HERE/'migration.json');assert len(o)==len(mig['records'])==1725
 for r in mig['records']:
  id=r['id'];assert n[id]==remap(o[id]) and dig(o[id])==r['old_sha256'] and dig(n[id])==r['new_sha256']
 # Explicit old event fixture migration at execution boundary. Only re-seal a digest if it was valid
 # for the old object; negative tests with deliberately invalid digests remain invalid.
 def rebind_event(x):
  if isinstance(x,list):return [rebind_event(v) for v in x]
  if not isinstance(x,dict):return x
  y={k:rebind_event(v) for k,v in x.items()}
  if set(y)=={'package_id','version','kind','owner','stable_id'} and y['package_id']=='learning-process' and y['version']==ov:y['version']=nv
  if y!=x and 'event_record_sha256' in x and x['event_record_sha256']==dig({k:v for k,v in x.items() if k!='event_record_sha256'}):
   y['event_record_sha256']=dig({k:v for k,v in y.items() if k!='event_record_sha256'})
  return y
 roots,catalog,bindings,extension,oldh=current_catalog()
 # Current historical helper treats previous H root as a preparation extension. Explicitly replace
 # both old roots with current H and process preparation; avoid duplicate version snapshots.
 for k in list(roots):
  if k[0] in ('chinese','learning-process'):del roots[k]
 pkey=('learning-process',nv);hkey=('chinese',hv)
 assert pkey in catalog and hkey in catalog
 roots[pkey]=catalog[pkey];roots[hkey]=catalog[hkey]
 im=Importer(ROOT,mode='research',catalog=catalog,extension=extension)
 def rf(id):
  z=n[id];return dict(package_id='learning-process',version=nv,kind=z['kind'],owner=z['owner'],stable_id=id)
 try:
  for k in roots:im._load(k,set())
  links={k:im._validate_refs(k) for k in im.packages}
  for k,rr in links.items():im._materialize(k,rr)
  assert ('learning-process',ov) not in im.packages and len([k for k in im.packages if k[0]=='chinese'])==1
  counts=[]
  for k,c in im.connections.items():
   assert c.execute('PRAGMA query_only').fetchone()==(1,) and not c.execute('PRAGMA foreign_key_check').fetchall() and all(not r[2] for r in c.execute('PRAGMA database_list'))
   counts.append(dict(package=list(k),records=c.execute('SELECT count(*) FROM local_registry').fetchone()[0],typed_refs=c.execute('SELECT count(*) FROM typed_refs').fetchone()[0],manifest_sha256=catalog[k].sha256))
  previous=load(HERE.parent/'f-composition-preparation/fixtures.json');replayed=[];changed=[]
  for f in previous:
   id=f['owner']+'.'+f['name'];z=load_record(im,rf(id));x=json.loads(z['input_spec']);assert x==f['input']
   expected=json.loads(z['expected_spec']) if isinstance(f['expected'],dict) else z['expected_spec']
   assert expected==f['expected']
   # Prior fixture is unchanged as historical input. Execute original oracle contract, then
   # separately execute explicit candidate-4 typed reference transformation and compare.
   assert _old.FUN[f['owner']](x)==expected,id
   y=rebind_event(x)
   oldver=_old._PROCESS_VERSION
   try:
    _old._PROCESS_VERSION=nv
    actual=_old.FUN[f['owner']](y)
   finally:_old._PROCESS_VERSION=oldver
   assert actual==expected,(id,actual,expected)
   if y!=x:changed.append(dict(id=id,old_input_sha256=dig(x),rebound_input_sha256=dig(y)))
   replayed.append(dict(id=id,actual=actual))
  assert len(replayed)==121
  design=load(HERE/'design.json');cases=[]
  for f in design['cases']:
   z=load_record(im,rf(f['id']));x=json.loads(z['input_spec']);expected=json.loads(z['expected_spec']) if isinstance(f['expected'],dict) else z['expected_spec']
   assert evaluate(f['owner'],x)==expected==f['expected'];cases.append(f['id'])
  # Actual H semantic cases in same integrated closure, not only prior H receipt.
  spec=importlib.util.spec_from_file_location('h_rules',HERE.parent/'h05-h07-batch/semantic_rules.py');hs=importlib.util.module_from_spec(spec);spec.loader.exec_module(hs)
  hcases=load(HERE.parent/'h01-h04-batch/validation-results.json')['tests']+load(HERE.parent/'h05-h07-batch/validation-results.json')['tests']
  for f in hcases:
   row=im.connections[hkey].execute('SELECT input_spec,expected_spec FROM record_case WHERE stable_id=?',(f['id'],)).fetchone()
   assert row and hs.evaluate(f['rule'],json.loads(row[0]))==json.loads(row[1])==f['actual']
  # Old and new process reader actual pointer switch and rollback.
  oldkey=('learning-process',ov);oi=Importer(ROOT,mode='research',catalog=catalog,extension=extension);oi.run(oldkey)
  try:
   oc=oi.connections[oldkey];initial=oc.execute('SELECT count(*) FROM local_registry').fetchone()[0];assert initial==1725
   pins=[[*k,v.path,v.sha256] for k,v in sorted(catalog.items())]
   a=dict(mode='CANDIDATE_RESEARCH_ONLY',select=list(oldkey),catalog=pins,extension=[extension.path,extension.sha256]);b=dict(mode='CANDIDATE_RESEARCH_ONLY',select=list(pkey),catalog=pins,extension=[extension.path,extension.sha256])
   with tempfile.TemporaryDirectory(prefix='learn-fa-pointer-') as td:
    p=Path(td);switch(p,ROOT,a,None)
    for phase,code,want in [('before_replace',71,a),('after_replace',72,b)]:
     child=multiprocessing.get_context('fork').Process(target=switch,args=(p,ROOT,b,a),kwargs={'_crash':phase});child.start();child.join(90)
     if child.is_alive():child.terminate();child.join();raise RuntimeError('POINTER_TIMEOUT')
     assert child.exitcode==code and read_pointer(p)==want
    assert oc.execute('SELECT count(*) FROM local_registry').fetchone()[0]==initial
    assert oc.execute('PRAGMA query_only').fetchone()==(1,)
    # Extension pin and snapshot CAS fail closed before mutation.
    bad=dict(b,extension=[extension.path,'0'*64])
    try:switch(p,ROOT,bad,b);raise AssertionError('BAD_EXTENSION_ACCEPTED')
    except Reject:pass
    assert read_pointer(p)==b
    try:switch(p,ROOT,a,a);raise AssertionError('STALE_CAS_ACCEPTED')
    except Reject:pass
    switch(p,ROOT,a,b);assert read_pointer(p)==a
  finally:oi.close()
 finally:im.close()
 totals=dict(packages=len(counts),records=sum(x['records'] for x in counts),typed_refs=sum(x['typed_refs'] for x in counts))
 report=dict(status='CUMULATIVE_AUTHOR_REBIND_NOT_QUALIFICATION',old_manifest_sha256=sha(old/'learning-process.manifest.json'),new_manifest_sha256=sha(new/'learning-process.manifest.json'),chinese_manifest_sha256=sha(h/'chinese.manifest.json'),migration_records=len(o),migration_counts=mig['counts'],closure=totals,package_counts=counts,prior_F_E_A07_cases=len(replayed),prior_case_results=replayed,embedded_event_rebinds=changed,new_FA_cases=len(cases),H_cases=len(hcases),pointer_recovery=dict(before_replace=True,after_replace=True,old_live_reader=True,rollback=True,bad_extension_rejected=True,stale_cas_rejected=True,physical_power_loss='HOLD'),private_adapter='EXACT_PRIOR_SCOPE_ONLY',persistent_sqlite=False)
 write(HERE/'cumulative-evidence.json',report)
 print('CUMULATIVE',totals,'F_E_A07',len(replayed),'event_rebinds',len(changed),'H',len(hcases),'new',len(cases))
if __name__=='__main__':main()
