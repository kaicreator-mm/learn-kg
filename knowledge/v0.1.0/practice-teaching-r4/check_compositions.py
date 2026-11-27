"""Limited policy advice examples, not real learner or workflow execution."""
from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=json.loads((P/'compositions.json').read_text())
out=[]
for c in rows:
 assert c['condition']['op']=='EQ' and c['condition']['value'] is True
 for j,x in enumerate(c['cases']):
  v=x['input'].get(c['condition']['field'])
  actual=c['action'] if v is True else c['unknown_action']
  assert actual==x['expected'],(c['id'],j,actual)
  out.append({'id':c['id']+'.CASE.'+str(j),'actual':actual,'status':'PASS_BUILDER_FINITE_ONLY'})
(P/'composition-results.json').write_text(json.dumps({'fixture_sha256':sha(P/'compositions.json'),'results':out},indent=2)+'\n')
print(len(out),'PASS_BUILDER_FINITE_ONLY')
