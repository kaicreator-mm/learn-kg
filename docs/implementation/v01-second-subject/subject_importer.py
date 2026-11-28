"""Explicit candidate-only M01 adapter; baseline DB01, DB02, IF01 remain unchanged."""
from pathlib import PurePosixPath
from tools.knowledge_import.importer import Importer,need,verified,parse,validate
MATH_KEY=('other-subject','0.1.0-math-v01-candidate-1')
MATH_PATH='knowledge/v0.1.0/other-subject-math-v01/other-subject.manifest.json'
MATH_PIN='deb47c6920662fa30dc64d0881f9ab0af51264a37c79dea5bb994c99271bcbe4'
KINDS={'Topic','Requirement','Claim','Element','SkillType','LearningObject','ObservationSpec','TaskSpec'}
class SubjectImporter(Importer):
 def _load(self,key,visiting):
  if key[0]!='other-subject':return super()._load(key,visiting)
  need(key==MATH_KEY and key not in visiting,'SUBJECT_TUPLE')
  if key in self.packages:return
  need(key in self.catalog,'MISSING_PACKAGE')
  pin=self.catalog[key]
  need(pin.path==MATH_PATH and pin.sha256==MATH_PIN,'SUBJECT_MANIFEST_PIN')
  m=parse(verified(self.root,pin.path,pin.sha256));validate(self.mv,m,pin.path)
  self.opened.append(pin.path)
  need((m['package_id'],m['version'])==key and m['owners']==['M01'] and m['status']=='CANDIDATE' and m['rights']=='HOLD' and m['dependencies']==[] and m['qualification_receipt_refs']==[],'SUBJECT_SCOPE')
  need(len(m['files'])==1,'SUBJECT_FILE_SCOPE');f=m['files'][0]
  need(f['path']=='M01.jsonl' and f['format']=='JSONL_RECORDS','SUBJECT_FILE_SCOPE')
  rel=str(PurePosixPath(pin.path).parent/f['path']);raw=verified(self.root,rel,f['sha256']);self.opened.append(rel)
  from tools.knowledge_import.importer import pointer
  rows=[parse(line) for line in raw.splitlines()];data={}
  need(len(rows)==f['record_count']==8,'SUBJECT_COUNT')
  for r in rows:
   need(isinstance(r,dict) and r.get('kind') in KINDS,'SUBJECT_KIND')
   validate(self.rv[r['kind']],r,r.get('stable_id',''))
   need(r['owner']=='M01' and r['status']=='CANDIDATE' and r['stable_id'].startswith('M01.') and r['stable_id'] not in data,'SUBJECT_RECORD_SCOPE')
   for p in r['provenance']:
    need(p['source_path']=='docs/implementation/v01-second-subject/design.json','SUBJECT_PROVENANCE_SCOPE')
    ck=(p['source_path'],p['source_sha256'])
    if ck not in self.source_cache:self.source_cache[ck]=parse(verified(self.root,*ck))
    pointer(self.source_cache[ck],p['json_pointer'])
   data[r['stable_id']]=r
  self.packages[key]=(m,pin.sha256,{},data)
