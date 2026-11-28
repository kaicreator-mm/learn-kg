"""Derived research-only subject-neutral projection from exact current registered process tuple."""
import json,hashlib,sys,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
from tools.knowledge_import.importer import refs,Importer,ManifestPin,Reject
from tools.knowledge_import.v00_prototype import load_record
SRC=ROOT/'knowledge/v0.1.0/learning-process-cumulative-r4';DST=ROOT/'knowledge/v0.1.0/v01-shared-process-projection'
OLD='0.1.0-process-candidate-4';NEW='0.1.0-v01-shared-projection-1'
HEAD='996356965743f70480b4bd827f15ca035f22e1c1';TREE='00e26ca6ce3ed51af11e2ecbbffcb4b1ddd542f4'
OWNERS=[f'P{i:02}' for i in range(1,11)]+['F05']
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def dig(x):return hashlib.sha256(canon(x).encode()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
def remap(x,old=OLD,new=NEW):
 if isinstance(x,list):return [remap(v,old,new) for v in x]
 if isinstance(x,dict):
  y={k:remap(v,old,new) for k,v in x.items()}
  if set(y)=={'package_id','version','kind','owner','stable_id'} and y['package_id']=='learning-process' and y['version']==old:
   assert y['owner'] in OWNERS;y['version']=new
  return y
 return x
def main():
 src=SRC/'learning-process.manifest.json';mh=sha(src);assert mh=='7e2c3cfdc29f70d715e009fdb06b987c30e2a7432b418b95efa0a04a861f51b3'
 m=load(src);assert m['version']==OLD
 assert subprocess.check_output(['git','rev-parse',HEAD+'^{tree}'],cwd=ROOT).decode().strip()==TREE
 d=ROOT/'docs/implementation/task-dag.json';assert d.read_bytes()==subprocess.check_output(['git','show',HEAD+':'+rel(d)],cwd=ROOT)
 ts={t['id']:t for t in load(d)['tasks']};bindings={};allrows={};source={};files=[];migration=[];deps=set()
 for o in OWNERS:
  t=ts[o];p=ROOT/t['current_receipt'];r=load(p);assert t['status']=='CANDIDATE_READY' and r['scope_restriction']['manifest_sha256']==mh
  assert p.read_bytes()==subprocess.check_output(['git','show',HEAD+':'+rel(p)],cwd=ROOT)
  for f in r['output']:assert sha(ROOT/f['path'])==f['sha256']
  for i in r['input']:
   dp=ROOT/ts[i['task_id']]['current_receipt'];dr=load(dp);assert dr['receipt_id']==i['receipt_id'] and dr['content_digest']==i['content_digest'] and dr.get('version',dr['exact_head'])==i['version']
   for s in i['specific_refs']:assert sha(ROOT/s['path'])==s['sha256']
  q=t.get('qualification_receipt');qr=load(ROOT/q) if q else None
  if qr:assert qr['reviewed_content_digest']==r['content_digest'] and qr['consumed_tuple']==r['input']
  sp=SRC/(o+'.jsonl');assert sha(sp)==r['scope_restriction']['module_shard_sha256']
  rows=[json.loads(l) for l in sp.read_text().splitlines()];assert dig(rows)==r['scope_restriction']['owner_record_set_sha256']
  nr=[]
  for z in rows:
   i=z['stable_id'];assert i not in allrows;assert z['owner']==o
   y=remap(z);assert remap(y,NEW,OLD)==z
   for _,rr in refs(y):
    k=(rr['package_id'],rr['version'])
    if k==('learning-process',NEW):assert rr['owner'] in OWNERS
    else:assert k[0] in ('learning-core','evidence');deps.add(k)
   source[i]=z;allrows[i]=y;nr.append(y)
   migration.append(dict(id=i,owner=o,old_sha256=dig(z),new_sha256=dig(y),change='TYPED_REF_VERSION_ONLY' if z!=y else 'UNCHANGED'))
  fp=DST/(o+'.jsonl');fp.write_text(''.join(canon(x)+'\n' for x in nr));files.append(dict(path=fp.name,sha256=sha(fp),format='JSONL_RECORDS',record_count=len(nr)))
  bindings[o]=dict(receipt_path=rel(p),receipt_sha256=sha(p),content_digest=r['content_digest'],qualification_path=q,qualification_sha256=sha(ROOT/q) if q else None,source_shard_sha256=sha(sp),source_owner_record_set_sha256=dig(rows),projected_shard_sha256=sha(fp),projected_owner_record_set_sha256=dig(nr))
 assert len(source)==1436
 olddeps={(x['package_id'],x['version']):x for x in m['dependencies']}
 assert deps<=set(olddeps)
 manifest=dict(schema_version='learn-kg-canonical-candidate-1',package_id='learning-process',version=NEW,status='CANDIDATE',rights='HOLD',owners=OWNERS,dependencies=[olddeps[k] for k in sorted(deps)],files=files,qualification_receipt_refs=[])
 mp=DST/'learning-process.manifest.json';write(mp,manifest)
 # Only exact old known catalog pins + actual projected manifest; no directory scan
 oldcat=load(HERE.parent/'v01-second-subject/catalog.json')['entries'];catalog={(z['package_id'],z['version']):z for z in oldcat if z['package_id']!='learning-process'}
 for k in deps:
  assert catalog[k]['sha256']==olddeps[k]['manifest_sha256']
 catalog['learning-process',NEW]=dict(package_id='learning-process',version=NEW,path=rel(mp),sha256=sha(mp))
 write(HERE/'catalog.json',dict(status='EXACT_PROJECTED_ROUTE_CANDIDATE_PINS',entries=[catalog[k] for k in sorted(catalog)]))
 ep=ROOT/'knowledge/v0.1.0/foundation-r3/relation-types.json'
 cat={k:ManifestPin(z['path'],z['sha256']) for k,z in catalog.items()}
 im=Importer(ROOT,mode='research',catalog=cat,extension=ManifestPin(rel(ep),sha(ep)))
 try:
  rep=im.run(('learning-process',NEW));assert ('chinese','0.1.0-chinese-cumulative-candidate-2') not in im.packages
  for i,z in allrows.items():
   rr=dict(package_id='learning-process',version=NEW,kind=z['kind'],owner=z['owner'],stable_id=i)
   p=load_record(im,rr)
   for k,v in p.items():
    # DB02 stores non-JSON-encoding bools using canonical JSON text; importer
    # already checks full canonical roundtrip including registry identity.
    if type(z[k]) is bool and isinstance(v,str):v=json.loads(v)
    assert v==z[k],(i,k,v,z[k])
  assert all(c.execute('PRAGMA query_only').fetchone()==(1,) and not c.execute('PRAGMA foreign_key_check').fetchall() and all(not r[2] for r in c.execute('PRAGMA database_list')) for c in im.connections.values())
 finally:im.close()
 write(HERE/'projection-evidence.json',dict(status='DERIVED_RESEARCH_PROJECTION_NOT_REGISTERED',source_registration_head=HEAD,source_registration_tree=TREE,source_manifest_sha256=mh,projection_manifest_sha256=sha(mp),source_owner_receipts=bindings,records=len(source),migration=migration,removed_owners=sorted(set(m['owners'])-set(OWNERS)),direct_dependencies=[olddeps[k] for k in sorted(deps)],all_projected_SQL_records_checked=len(source),import_report=rep,qualification='NOT_GRANTED',persistent_sqlite=False))
 print('PROJECT',len(source),sha(mp),len(rep['packages']))
if __name__=='__main__':main()
