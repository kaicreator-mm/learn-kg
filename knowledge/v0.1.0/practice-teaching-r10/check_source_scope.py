import pathlib,hashlib,json,sys
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
sys.path.insert(0,str(ROOT))
from tools.knowledge_import.importer import Importer,ManifestPin
V='0.1.0-practice-teaching-candidate-10'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 scope=load(P/'source-consumer-dispositions.json')
 assert scope['selected_manifest_sha256']==sha(P/'learning-core.manifest.json')
 catalog={(pkg,V):ManifestPin((P/(pkg+'.manifest.json')).relative_to(ROOT).as_posix(),sha(P/(pkg+'.manifest.json'))) for pkg in ('learning-core','evidence')}
 im=Importer(mode='research',catalog=catalog)
 try:
  im.run(('learning-core',V));c=im.connections[('learning-core',V)]
  statuses=dict(c.execute("SELECT stable_id,status FROM local_registry WHERE kind='Claim'"))
  assert len(statuses)==354 and sum(s=='HOLD' for s in statuses.values())==121
  excluded={x['id'] for x in scope['rows'] if x['disposition'].startswith('EXCLUDED')}
  restored={x['id'] for x in scope['rows'] if x['disposition'].startswith('REVALIDATED')}
  assert len(excluded)==47 and len(restored)==21 and all(statuses[x]=='HOLD' for x in excluded) and all(statuses[x]=='CANDIDATE' for x in restored)
  for sid,s,cr,fr,tr in c.execute("SELECT r.stable_id,g.status,r.claim_refs,r.from_ref,r.to_ref FROM record_relation r JOIN local_registry g USING(package_id,version,stable_id)"):
   if s=='CANDIDATE':assert not excluded.intersection([v['stable_id'] for v in json.loads(cr)]+[json.loads(fr)['stable_id'],json.loads(tr)['stable_id']]),sid
  dag=load(ROOT/'docs/implementation/task-dag.json');tasks={t['id']:t for t in dag['tasks']}
  for o in ('K05','K06','K07','K08','KR02'):
   assert not tasks[o].get('current_receipt') and not tasks[o].get('qualification_receipt')
  print('68 exact claim status checks; 47 exclusions; 21 builder revalidated; no active relation to excluded; five old current receipt pointers absent')
 finally:im.close()
if __name__=='__main__':main()
