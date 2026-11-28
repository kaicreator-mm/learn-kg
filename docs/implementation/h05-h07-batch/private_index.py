"""Restricted private source indices. No raw content enters Git."""
from pathlib import Path
import sys,os,json,collections,sqlite3,argparse
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path[:0]=[str(HERE.parent/'hsk01'),str(HERE.parent/'h01-h04-batch')]
from private_subject_index import load_stage,source_ref
from build_hsk01 import parse_record,field,canonical,file_sha,need,RIGHTS_SCOPE
def build(stage,out,mp,rp):
 os.umask(0o077);need(not out.exists() and not out.resolve().is_relative_to(ROOT),'NEW_PRIVATE_DIRECTORY')
 data=load_stage(stage,mp,rp);out.mkdir(parents=True,mode=0o700)
 def base(r,owner,kind):return dict(owner=owner,kind=kind,source_ref=source_ref(r),candidate_status='HOLD',normalized_knowledge_id=None,semantic_qualification='NOT_RUN',rights_scope=RIGHTS_SCOPE)
 h={o:[] for o in ('H05','H06','H07')}
 for r in data['SourceBlock']:
  fs=parse_record(r['raw_rdf']);k=field(fs,'blockKind')
  if k in ('Task','Topic'):
   h['H05'].append(base(r,'H05','TASK_TOPIC_BLOCK')|dict(block_kind=k,raw_text=field(fs,'rawText'),raw_text_sha256=r['candidate']['raw_text_sha256'],source_locator=r['candidate']['source_locator'],scope_topic_ref=r['candidate']['typed_links']['scopeTopic'],semantic_intent=None,layout='HOLD'))
 for r in data['AbilityRecord']:
  fs=parse_record(r['raw_rdf'])
  h['H06'].append(base(r,'H06','ABILITY_SOURCE_RECORD')|dict(raw_text=field(fs,'rawText'),typed_links=r['candidate']['typed_links'],competency_id=None,skill_mapping='HOLD',mastery=None))
 for kind,rows in data.items():
  for r in rows:
   # Keep exact stage identity, raw RDF remains in the pinned archive, no normalization.
   h['H07'].append(base(r,'H07','SOURCE_SCOPE_RECONCILIATION')|dict(source_kind=kind,raw_links=r['candidate']['typed_links'],level_label=r['candidate'].get('level_label'),official_standard_id=None,official_member_status='UNKNOWN_HOLD',semantic_refs=[],prerequisite=None,mastery=None))
 need({k:len(v) for k,v in h.items()}=={'H05':73,'H06':9,'H07':19317},'COUNTS')
 con=sqlite3.connect(':memory:')
 try:
  con.executescript('PRAGMA foreign_keys=ON;CREATE TABLE stage(id TEXT PRIMARY KEY, digest TEXT NOT NULL);CREATE TABLE idx(owner TEXT,id TEXT,digest TEXT NOT NULL,PRIMARY KEY(owner,id),FOREIGN KEY(id) REFERENCES stage(id));')
  index={r['candidate']['candidate_id']:source_ref(r)['stage_record_sha256'] for rows in data.values() for r in rows}
  con.executemany('INSERT INTO stage VALUES(?,?)',index.items())
  for o,rows in h.items():
   for r in rows:
    sr=r['source_ref'];need(sr['stage_record_sha256']==index[sr['stage_candidate_id']],'STAGE_BIND')
    con.execute('INSERT INTO idx VALUES(?,?,?)',(o,sr['stage_candidate_id'],sr['stage_record_sha256']))
  need(not con.execute('PRAGMA foreign_key_check').fetchall(),'FK')
  need(con.execute("SELECT count(*) FROM stage WHERE id NOT IN (SELECT id FROM idx WHERE owner='H07')").fetchone()==(0,),'H07_CLOSURE')
  counts=dict(con.execute('SELECT owner,count(*) FROM idx GROUP BY owner'))
 finally:con.close()
 files={}
 for o,rows in h.items():
  f=out/(o+'.source-index.jsonl');f.write_text(''.join(canonical(r)+'\n' for r in rows),encoding='utf-8')
  files[f.name]=dict(rows=len(rows),bytes=f.stat().st_size,sha256=file_sha(f))
 m=dict(status='PRIVATE_RESTRICTED_SOURCE_INDICES_ONLY',stage_manifest_sha256=mp,hsk01_receipt_sha256=rp,files=files,counts=counts,source_kind_counts={k:len(v) for k,v in data.items()},official_authority='UNKNOWN_HOLD',rights=RIGHTS_SCOPE,professional_qualification='NOT_RUN',persistent_sqlite=False)
 (out/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
 print(json.dumps(m,ensure_ascii=False,sort_keys=True))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--manifest-sha256',required=True);p.add_argument('--receipt-sha256',required=True);a=p.parse_args();build(a.stage.resolve(),a.out.resolve(),a.manifest_sha256,a.receipt_sha256)
