#!/usr/bin/env python3
"""Private source-oriented H01-H04 candidate indices; never infer semantic identities."""
from pathlib import Path
import argparse,collections,hashlib,json,os,re,sys,unicodedata,sqlite3
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent/'hsk01'))
from build_hsk01 import EXPECTED,parse_record,field,canonical,sha,file_sha,need,read_json,ptr,RIGHTS_SCOPE
POS={'名','动','形','数','量','代','副','介','连','助','叹','拟声','区别','语气','方位','时间','处所','专名','前缀','后缀','词缀','成语','惯用语','短语','象声','代词','名词','动词','形容词','量词','数词','副词','连词','介词','助词','叹词','拟声词'}
def latin_surface(s):
 # Structural envelope only, not pinyin phonotactics/orthography.
 if not isinstance(s,str) or not s or s.strip()!=s:return False
 z=unicodedata.normalize('NFD',s)
 if not z or not z[0].isascii() or not z[0].isalpha():return False
 marks={'\u0300','\u0301','\u0304','\u030c','\u0308','\u0302'}
 prev=False;letters=0
 for c in z:
  if c.isascii() and c.isalpha():prev=True;letters+=1
  elif c in marks and prev:pass
  elif c in ("'",'’','-') and prev:prev=False
  else:return False
 return prev and letters>0
def split_reading_pos(raw):
 # Exactly one ASCII space and recognized literal suffix labels, no repair.
 if raw.count(' ')==1:
  reading,tags=raw.split(' ');parts=tags.split('、')
  if latin_surface(reading) and parts and all(p in POS for p in parts) and len(set(parts))==len(parts):
   return {'status':'RECORDED_SURFACE_SPLIT_CANDIDATE','reading_surface_raw':reading,'pos_label_raw':tags,'pos_labels_raw':parts,'separator_raw':' '}
 if latin_surface(raw):
  return {'status':'READING_SURFACE_ONLY_POS_UNKNOWN_HOLD','reading_surface_raw':raw,'pos_label_raw':None,'pos_labels_raw':None,'separator_raw':None}
 return {'status':'HOLD_UNSPLIT_RAW','reading_surface_raw':None,'pos_label_raw':None,'pos_labels_raw':None,'separator_raw':None}
def source_ref(r):return {'graph':r['provenance']['graph'],'source_entity_id':r['provenance']['source_entity_id'],'source_rdf_kind':r['provenance']['source_rdf_kind'],'stage_candidate_id':r['candidate']['candidate_id'],'stage_record_sha256':sha(canonical(r).encode()),'source_line_sha256':r['provenance']['raw_line_sha256'],'source_file':r['provenance']['archive_file'],'source_row':r['provenance']['row_number_one_based']}
def load_stage(root,pin,receipt_pin):
 rp=ROOT/'evidence/tasks/HSK01/HSK01-FORMAL-01.json';need(file_sha(rp)==receipt_pin,'RECEIPT_PIN');r=read_json(rp)
 need(r['validation']['independent_result']=='ACCEPT_SCOPED' and r['scope_restriction']['private_manifest_sha256']==pin,'PRIVATE_CANDIDATE_PIN')
 for f in r['output']:need(file_sha(ROOT/f['path'])==f['sha256'],'RECEIPT_ARTIFACT_PIN')
 m=read_json(root/'manifest.json');need(file_sha(root/'manifest.json')==pin and m['private_outputs']==r['scope_restriction']['private_outputs'],'MANIFEST_PIN')
 data={}
 for k,n in EXPECTED.items():
  f=root/(k+'.candidate.jsonl');need(file_sha(f)==m['private_outputs'][f.name]['sha256'],'SHARD_PIN')
  rows=[json.loads(l) for l in f.open(encoding='utf-8')];need(len(rows)==n,'COUNT')
  need(all(row['raw_rdf']['kind']==k and row['rights_scope']==RIGHTS_SCOPE and row['candidate']['normalized_knowledge_id'] is None for row in rows),'SCOPE')
  data[k]=rows
 return data
def main(root,out,mp,rp):
 os.umask(0o077);need(not out.exists() and not out.resolve().is_relative_to(ROOT),'PRIVATE_NEW_DIRECTORY_ONLY')
 data=load_stage(root,mp,rp);out.mkdir(parents=True,mode=0o700)
 h={o:[] for o in ('H01','H02','H03','H04')};counts=collections.Counter()
 def record(o,r,kind,fields):
  return dict(owner=o,kind=kind,source_ref=source_ref(r),rights_scope=RIGHTS_SCOPE,candidate_status='HOLD',semantic_qualification='NOT_RUN',normalized_knowledge_id=None,**fields)
 for r in data['LexicalRecord']:
  fs=parse_record(r['raw_rdf']);raw=field(fs,'readingPosRaw');split=split_reading_pos(raw);counts[split['status']]+=1
  if split['status']=='RECORDED_SURFACE_SPLIT_CANDIDATE':need(split['reading_surface_raw']+split['separator_raw']+split['pos_label_raw']==raw,'SPLIT_LOSS')
  h['H01'].append(record('H01',r,'RECORDED_READING_SURFACE_INDEX',dict(reading_pos_raw=raw,reading_surface_raw=split['reading_surface_raw'],parse_status=split['status'],syllable_segmentation=None,phoneme_mapping=None,actual_audio=None)))
  h['H03'].append(record('H03',r,'LEXICAL_SOURCE_INDEX',dict(headword_raw=field(fs,'headwordRaw'),reading_pos_raw=raw,split=split,level_label=r['candidate']['level_label'],sense_refs=[],lexeme_id=None,collocation_evidence=None)))
 chars={r['raw_rdf']['stable_id']:r for r in data['HanCharacter']};members=collections.defaultdict(list)
 for r in data['CharacterMembership']:
  fs=parse_record(r['raw_rdf']);id=field(fs,'character');need(id in chars,'CHARACTER_REF');target=chars[id]
  need(r['candidate']['typed_links']['character']['source_entity_id']==id,'CHARACTER_LINK')
  m=record('H02',r,'CHARACTER_SOURCE_MEMBERSHIP',dict(character_source_ref=source_ref(target),mode_raw=field(fs,'mode'),level_band_ref=r['candidate']['typed_links']['levelBand'],source_locator=r['candidate']['source_locator'],mastery=None))
  h['H02'].append(m);members[id].append(source_ref(r))
 for id,r in chars.items():
  fs=parse_record(r['raw_rdf']);glyph=field(fs,'glyph');need(len(glyph)==1 and r['candidate']['codepoint']=='U+'+format(ord(glyph),'04X'),'GLYPH_IDENTITY')
  h['H02'].append(record('H02',r,'CHARACTER_IDENTITY_INDEX',dict(glyph=glyph,codepoint=r['candidate']['codepoint'],membership_source_refs=members[id],reading=None,components=None,stroke_order=None,script=None)))
 for r in data['SourceBlock']:
  fs=parse_record(r['raw_rdf'])
  if field(fs,'blockKind')!='Grammar':continue
  h['H04'].append(record('H04',r,'GRAMMAR_BLOCK_INDEX',dict(raw_text=field(fs,'rawText'),raw_text_sha256=r['candidate']['raw_text_sha256'],source_locator=r['candidate']['source_locator'],scope_topic_ref=r['candidate']['typed_links']['scopeTopic'],constructs=[],layout_review='HOLD')))
 need({o:len(v) for o,v in h.items()}=={'H01':11000,'H02':7376,'H03':11000,'H04':21},'DOMAIN_COUNTS')
 # Actual cross-record exact source identity test for all emitted indices.
 conn=sqlite3.connect(':memory:')
 try:
  conn.executescript('CREATE TABLE source(id TEXT PRIMARY KEY,digest TEXT NOT NULL);CREATE TABLE idx(owner TEXT NOT NULL,id TEXT NOT NULL,digest TEXT NOT NULL,PRIMARY KEY(owner,id),FOREIGN KEY(id) REFERENCES source(id));PRAGMA foreign_keys=ON;')
  source={r['candidate']['candidate_id']:sha(canonical(r).encode()) for rows in data.values() for r in rows}
  conn.executemany('INSERT INTO source VALUES(?,?)',source.items())
  for o,rows in h.items():
   for r in rows:
    sr=r['source_ref'];need(source[sr['stage_candidate_id']]==sr['stage_record_sha256'],'EXACT_SOURCE_DIGEST')
    conn.execute('INSERT INTO idx VALUES(?,?,?)',(o,sr['stage_candidate_id'],sr['stage_record_sha256']))
  need(conn.execute('PRAGMA foreign_key_check').fetchall()==[],'INDEX_FK')
  counts_sql=dict(conn.execute('SELECT owner,count(*) FROM idx GROUP BY owner'));need(counts_sql=={o:len(v) for o,v in h.items()},'SQL_COUNTS')
 finally:conn.close()
 files={}
 for o,rows in h.items():
  f=out/(o+'.source-index.jsonl');f.write_text(''.join(canonical(r)+'\n' for r in rows),encoding='utf-8')
  files[f.name]=dict(rows=len(rows),bytes=f.stat().st_size,sha256=file_sha(f))
 summary=dict(status='PRIVATE_SOURCE_INDEX_ONLY',stage_manifest_sha256=mp,hsk01_receipt_sha256=rp,files=files,reading_pos_split_counts=dict(counts),indexed_counts=counts_sql,grammar_layout='HOLD',phonotactics='NOT_VALIDATED',sense_and_pos_semantics='NOT_ESTABLISHED',character_readings_and_components='NOT_ESTABLISHED',rights=RIGHTS_SCOPE,professional_qualification='NOT_RUN',persistent_sqlite=False)
 (out/'manifest.json').write_text(json.dumps(summary,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
 print(json.dumps(summary,ensure_ascii=False,sort_keys=True))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--stage',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--manifest-sha256',required=True);p.add_argument('--receipt-sha256',required=True);a=p.parse_args();main(a.stage.resolve(),a.output.resolve(),a.manifest_sha256,a.receipt_sha256)
