#!/usr/bin/env python3
"""Selected exact candidate-package closure, memory-only; no release activation."""
from pathlib import Path
import collections,hashlib,json,sys,tempfile,multiprocessing
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];sys.path.insert(0,str(ROOT))
from tools.knowledge_import.importer import Importer,ManifestPin,Reject,need
from tools.knowledge_import.candidate_pointer import switch,read_pointer,resolve
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def key(m):return m['package_id'],m['version']
def current_catalog():
 d=load(ROOT/'docs/implementation/task-dag.json');tasks={t['id']:t for t in d['tasks']};catalog={};roots={};bindings={}
 for path in sorted((ROOT/'knowledge/v0.1.0').glob('*/*manifest.json')):
  m=load(path)
  if not {'package_id','version'}<=m.keys():continue
  k=key(m);pin=ManifestPin(path.relative_to(ROOT).as_posix(),sha(path))
  need(k not in catalog or catalog[k].sha256==pin.sha256,'DUPLICATE_PACKAGE_IDENTITY')
  catalog[k]=pin
 for o in [f'K{i:02}' for i in range(1,20)]+[f'P{i:02}' for i in range(1,11)]+['F03','F04','F05','F07','E01','A07']:
  t=tasks[o];p=ROOT/t['current_receipt'];r=load(p);matches=[]
  for f in r['output']:
   path=ROOT/f['path']
   if not path.name.endswith('manifest.json'):continue
   m=load(path)
   if m.get('package_id') not in ('learning-core','learning-process') or o not in m.get('owners',[]):continue
   need(sha(path)==f['sha256'],'CURRENT_RECEIPT_MANIFEST_PIN',o);matches.append(key(m))
  need(len(matches)==1,'CURRENT_OWNER_MANIFEST',o)
  k=matches[0];roots[k]=catalog[k];bindings[o]=dict(receipt_path=p.relative_to(ROOT).as_posix(),receipt_sha256=sha(p),receipt_id=r['receipt_id'],content_digest=r['content_digest'],version=r['version'],package=list(k),manifest_sha256=catalog[k].sha256)
  if o.startswith(('K','P')):
   qp=ROOT/t['qualification_receipt'];qr=load(qp);need(qr['reviewed_content_digest']==r['content_digest'],'CURRENT_QUALIFICATION_TUPLE',o)
   bindings[o]['qualification_receipt_sha256']=sha(qp)
 # First H batch is preparation-only, not a current registered task. Include separately.
 h=('chinese','0.1.0-chinese-h01-h04-candidate-1');roots[h]=catalog[h]
 ext=ROOT/'knowledge/v0.1.0/foundation-r3/relation-types.json'
 return roots,catalog,bindings,ManifestPin(ext.relative_to(ROOT).as_posix(),sha(ext)),h
def run():
 roots,catalog,bindings,extension,h=current_catalog()
 im=Importer(ROOT,mode='research',catalog=catalog,extension=extension)
 try:
  # Same DB02 load, validate, materialize operations as single-root run; only
  # explicit registered roots plus separately labeled H preparation root.
  for k in roots:im._load(k,set())
  all_links={k:im._validate_refs(k) for k in im.packages}
  for k,links in all_links.items():im._materialize(k,links)
  by_owner=collections.Counter();counts=[];plans={};total=0
  for k,c in im.connections.items():
   need(c.execute('PRAGMA query_only').fetchone()==(1,) and all(not x[2] for x in c.execute('PRAGMA database_list')),'MEMORY_QUERY_ONLY')
   n=c.execute('SELECT count(*) FROM local_registry').fetchone()[0];nr=c.execute('SELECT count(*) FROM typed_refs').fetchone()[0]
   need(n==len(im.packages[k][3]) and nr==len(all_links[k]) and c.execute('PRAGMA foreign_key_check').fetchall()==[],'SQL_RECONCILIATION')
   total+=n
   counts.append(dict(package=list(k),manifest_sha256=catalog[k].sha256,records=n,typed_refs=nr,owners=dict(c.execute('SELECT owner,count(*) FROM local_registry GROUP BY owner'))))
  for o,b in bindings.items():
   k=tuple(b['package']);c=im.connections[k];n=c.execute('SELECT count(*) FROM local_registry WHERE owner=?',(o,)).fetchone()[0]
   need(n>0,'OWNER_ROUTE_EMPTY',o);by_owner[o]=n
  for k in ('H01','H02','H03','H04'):
   c=im.connections[h];n=c.execute('SELECT count(*) FROM local_registry WHERE owner=?',(k,)).fetchone()[0];need(n>0,'H_PREP_ROUTE_EMPTY');by_owner[k]=n
  for k in (('learning-process','0.1.0-process-candidate-3'),h):
   c=im.connections[k];plan=c.execute('EXPLAIN QUERY PLAN SELECT * FROM local_registry WHERE kind=? AND owner=?',('Claim','H01' if k==h else 'P04')).fetchall();plans[k[0]]=[x[3] for x in plan]
  # Physical package-specific routing witness: no unopened catalog records were materialized.
  need(set(im.connections)==set(im.packages),'ROUTING_CLOSURE')
  result=dict(status='REGISTERED_CURRENT_ROOTS_PLUS_H_PREPARATION_ONLY',roots=[list(k) for k in roots],packages=counts,total_records=total,total_typed_refs=sum(x['typed_refs'] for x in counts),owner_routes=dict(by_owner),input_bindings=bindings,query_plans=plans,unselected_catalog_packages=len(set(catalog)-set(im.packages)),persistent_sqlite=False,full_future_views='HOLD_REMAINING_H_F_A_AND_V01')
 finally:im.close()
 # Real candidate text-pointer interruption/restore witness for current new
 # H candidate (no extension needed). Never activate any released package.
 h_catalog=[[*k,catalog[k].path,catalog[k].sha256] for k in [h,('evidence',h[1])]]
 old=dict(mode='CANDIDATE_RESEARCH_ONLY',select=['evidence',h[1]],catalog=h_catalog)
 new=dict(mode='CANDIDATE_RESEARCH_ONLY',select=list(h),catalog=h_catalog)
 with tempfile.TemporaryDirectory(prefix='db03-pointer-') as td:
  d=Path(td);switch(d,ROOT,old,None)
  before=read_pointer(d);need(before==old and len(resolve(before,ROOT)['packages'])==1,'POINTER_INITIAL')
  for phase,code,expected in [('before_replace',71,old),('after_replace',72,new)]:
   child=multiprocessing.get_context('fork').Process(target=switch,args=(d,ROOT,new,old),kwargs={'_crash':phase});child.start();child.join(60)
   if child.is_alive():child.terminate();child.join();raise RuntimeError('POINTER_CHILD_TIMEOUT')
   need(child.exitcode==code and read_pointer(d)==expected,'POINTER_INTERRUPTION',phase)
   need(len(resolve(read_pointer(d),ROOT)['packages'])==(1 if expected==old else 2),'POINTER_REOPEN')
  need(len(resolve(before,ROOT)['packages'])==1,'READER_OLD_SNAPSHOT')
  bad={**new,'catalog':[[*v[:3],'0'*64] if v[:2]==list(h) else v for v in h_catalog]}
  try:switch(d,ROOT,bad,new);raise RuntimeError('BAD_PIN_ACCEPTED')
  except Reject:pass
  need(read_pointer(d)==new,'FAILED_SWITCH_MUTATED')
  try:switch(d,ROOT,old,old);raise RuntimeError('STALE_CAS_ACCEPTED')
  except Reject:pass
  switch(d,ROOT,old,new);need(read_pointer(d)==old,'ROLLBACK')
  need(not list(d.rglob('*.sqlite*')),'POINTER_PERSISTENT_DB')
 result['text_activation_recovery']=dict(initial=True,before_replace=True,after_replace=True,old_reader=True,wrong_pin_rejected=True,stale_cas_rejected=True,rollback=True,physical_power_loss='HOLD_NOT_TESTED',scope='ACTUAL_H_CANDIDATE_TEXT_POINTER_ONLY')
 print(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2))
if __name__=='__main__':run()
