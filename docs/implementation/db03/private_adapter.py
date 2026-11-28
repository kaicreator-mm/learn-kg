#!/usr/bin/env python3
"""Exact pinned private candidate adapter. Never extends public importer authority."""
from pathlib import Path
import argparse,collections,copy,hashlib,json,os,re,sqlite3,sys,functools
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path[:0]=[str(ROOT),str(HERE.parent/'hsk01'),str(HERE.parent/'h01-h04-batch')]
from tools.knowledge_import.importer import refs,ptr_escape,parse,canonical,need,q
from private_subject_index import load_stage,source_ref
import verify_mapping
# Same reviewed property validators, cached only in this adapter process.
verify_mapping.prop_validator=functools.lru_cache(maxsize=None)(verify_mapping.prop_validator)
from verify_mapping import project_fields
from build_hsk01 import parse_record,field,file_sha,sha,RIGHTS_SCOPE
from jsonschema import Draft202012Validator
DB=ROOT/'docs/implementation/db01';IF=ROOT/'docs/implementation/if01/interface-contract.json'
SCHEMA=json.loads((DB/'canonical.schema.json').read_text());MAPPING=json.loads((DB/'mapping-contract.json').read_text());INTERFACE=json.loads(IF.read_text())
VERSION='0.1.0-db03-private-source-candidate-1'
def read(p):return json.loads(p.read_text())
def write(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(canonical(x)+'\n',encoding='utf-8')
def checked_root(p):
 need(p.is_dir() and not p.is_symlink() and not p.resolve().is_relative_to(ROOT),'PRIVATE_ROOT')
 need(p.stat().st_mode & 0o077==0,'PRIVATE_DIR_MODE')
 return p.resolve()
def relative(root,name):
 p=Path(name);need(not p.is_absolute() and name and all(x not in ('','.','..') for x in name.split('/')) and '\\' not in name,'PRIVATE_PATH')
 f=root
 for part in p.parts:
  f=f/part;need(not f.is_symlink(),'PRIVATE_SYMLINK')
 need(f.is_file() and f.resolve().is_relative_to(root),'PRIVATE_FILE')
 need(f.stat().st_mode & 0o077==0,'PRIVATE_FILE_MODE')
 return f
def target_ref(r):
 return {'package_id':'evidence' if r['kind']=='Source' else 'chinese','version':VERSION,'stable_id':r['stable_id'],'kind':r['kind'],'owner':r['owner']}
@functools.lru_cache(maxsize=None)
def schema(kind):return Draft202012Validator({'$defs':SCHEMA['$defs'],'$ref':'#/$defs/'+kind})
def refs_rebind(x):
 if isinstance(x,dict):
  if set(x)=={'package_id','version','stable_id','kind','owner'}:
   need(x['package_id']=='hsk-source-interface' and x['version']=='0.1.0-hs00-candidate-1','HS00_REF_SCOPE')
   return dict(x,package_id='evidence' if x['kind']=='Source' else 'chinese',version=VERSION)
  return {k:refs_rebind(v) for k,v in x.items()}
 if isinstance(x,list):return [refs_rebind(v) for v in x]
 return x
def held_shape(orig,provenance):
 r=refs_rebind(copy.deepcopy(orig));r['provenance']=provenance
 # HS00 Locator shape used EVIDENCE owner without a registered package.
 # In actual DB01 chinese package source interface structural owner is H07;
 # evidence package admits only Source; no professional ownership assertion.
 if r['kind']=='Locator':r['owner']='H07'
 return r
def hs00_shapes():
 hs=read(ROOT/'docs/implementation/hs00/source-mapping.json')
 projections=read(ROOT/'docs/implementation/hs00/db01-projections.json')
 receipt=read(ROOT/'evidence/tasks/HS00/HS00-FORMAL-01.json')
 for p in receipt['output']:need(file_sha(ROOT/p['path'])==p['sha256'],'HS00_REVIEWED_ARTIFACT_PIN')
 need(projections['source_mapping_sha256']==file_sha(ROOT/'docs/implementation/hs00/source-mapping.json'),'HS00_MAPPING_PIN')
 ids={}
 for i,r in enumerate(hs['source_records']):ids['/source_records/'+str(i)]=('SourceRecord',r['source_record_id'])
 for i,r in enumerate(hs['level_bands']):ids['/level_bands/'+str(i)]=('LevelBand',r['source_band_id'])
 for i,r in enumerate(hs['source_blocks']):ids['/source_blocks/'+str(i)]=('SourceBlock',r['source_block_id'])
 ids['/standard_identity']=('SyllabusVersion',hs['standard_identity']['source_standard_id'])
 return hs,{ids[r['provenance'][0]['json_pointer']]:r for r in projections['records']}
def create_projection(stage_root,out,mp,rp):
 need(file_sha(DB/'canonical.schema.json')==INTERFACE['schema_sha256'] and file_sha(DB/'mapping-contract.json')==INTERFACE['mapping_sha256'],'DB01_IF01_PIN')
 data=load_stage(checked_root(stage_root),mp,rp)
 # Explicit private source document adapter: one JSON array per original type,
 # preserve whole stage record and exact line digest; never JSONL pseudo-pointer.
 need(not out.exists() and not out.resolve().is_relative_to(ROOT),'PRIVATE_NEW_ROOT');out.mkdir(parents=True,mode=0o700)
 docs={};by_id={};doc_cache={}
 for kind,rows in data.items():
  name='documents/'+kind+'.json';p=out/name;write(p,rows);h=file_sha(p);docs[name]={'sha256':h,'rows':len(rows),'bytes':p.stat().st_size};doc_cache[name]=rows
  for i,r in enumerate(rows):
   key=(r['raw_rdf']['graph'],r['raw_rdf']['stable_id'],kind);need(key not in by_id,'DUPLICATE_STAGE_TRIPLE')
   by_id[key]=(name,i,r)
 def doc_prov(r):
  key=(r['raw_rdf']['graph'],r['raw_rdf']['stable_id'],r['raw_rdf']['kind']);n,i,original=by_id[key];need(original==r,'STAGE_IDENTITY')
  return [{'source_path':n,'source_sha256':docs[n]['sha256'],'json_pointer':'/'+str(i)+'/raw_rdf','source_status':'PRIVATE_PRESERVATION_CANDIDATE'}]
 def provenance_for(r):return doc_prov(r)
 hs,shapes=hs00_shapes()
 stage_by_kind={k:{r['raw_rdf']['stable_id']:r for r in rows} for k,rows in data.items()}
 hs_ids={}
 for i,r in enumerate(hs['source_records']):hs_ids['/source_records/'+str(i)]=('SourceRecord',r['source_record_id'])
 for i,r in enumerate(hs['level_bands']):hs_ids['/level_bands/'+str(i)]=('LevelBand',r['source_band_id'])
 for i,r in enumerate(hs['source_blocks']):hs_ids['/source_blocks/'+str(i)]=('SourceBlock',r['source_block_id'])
 hs_ids['/standard_identity']=('SyllabusVersion',hs['standard_identity']['source_standard_id'])
 records={};bindings={};deferred=[];raw_shapes=0
 def bind(r,stage,recipe):
  id=r['stable_id'];need(id not in records,'DUPLICATE_CANONICAL_ID')
  need(r['status']=='HOLD','NO_SEMANTIC_PROMOTION');schema(r['kind']).validate(r)
  records[id]=r;bindings[id]={'source_ref':source_ref(stage),'canonical_ref':target_ref(r),'record_sha256':sha(canonical(r).encode()),'recipe':recipe}
  return target_ref(r)
 source_targets={};band_targets={};std=None
 for (kind,id),orig in shapes.items():
  r0=stage_by_kind[kind][id]
  r=held_shape(orig,provenance_for(r0))
  ref=bind(r,r0,'EXACT_REVIEWED_HS00_HOLD_SHAPE_REBIND')
  if kind=='SourceRecord':source_targets[id]=ref
  elif kind=='LevelBand':band_targets[id]=ref
  elif kind=='SyllabusVersion':std=ref
 need(len(records)==109 and std is not None,'HS00_PROJECTION_COUNT')
 for kind in ('LexicalRecord','CharacterMembership'):
  for r0 in data[kind]:
   rfields=project_fields(r0);fs=parse_record(r0['raw_rdf'])
   r={k:v['value'] for k,v in rfields.items() if v['state']=='MAPPED_VALUE'}
   sourceid=field(fs,'source');bandid=field(fs,'levelBand');band=stage_by_kind['LevelBand'][bandid]
   need(field(parse_record(band['raw_rdf']),'version')==hs['standard_identity']['source_standard_id'],'STANDARD_EDGE')
   id='HSK01.SOURCE.MEMBERSHIP.'+sha(canonical([r0['raw_rdf']['graph'],r0['raw_rdf']['stable_id'],kind]).encode())[:32]
   r.update(stable_id=id,owner='H07',provenance=provenance_for(r0),source_ref=source_targets[sourceid],band_ref=band_targets[bandid],standard_ref=std)
   need(r['mapping_status']=='HOLD' and r['semantic_refs']==[],'MEMBERSHIP_SCOPE')
   bind(r,r0,'EXACT_SOURCE_MEMBERSHIP_HOLD_STRUCTURAL_H07_OWNER');raw_shapes+=1
 for kind,why in [('HanCharacter','H02 actual canonical claims and script classification not established'),('TaxonomyTopic','Raw taxonomy not a canonical H-only topic ownership/semantic mapping'),('AbilityRecord','H06/H07 actual claims, dimensions and evidence not established')]:
  for r in data[kind]:deferred.append({'source_ref':source_ref(r),'status':'HOLD_NO_CANONICAL_RECORD','reason':why})
 need(raw_shapes==15288 and len(records)==15397 and len(deferred)==3920,'PROJECTION_RECONCILIATION')
 all_stage={(r['raw_rdf']['graph'],r['raw_rdf']['stable_id'],r['raw_rdf']['kind']) for rr in data.values() for r in rr}
 used=[(v['source_ref']['graph'],v['source_ref']['source_entity_id'],v['source_ref']['source_rdf_kind']) for v in bindings.values()]+[(v['source_ref']['graph'],v['source_ref']['source_entity_id'],v['source_ref']['source_rdf_kind']) for v in deferred]
 need(len(used)==len(set(used)) and set(used)==all_stage,'STAGE_TOTAL_RECONCILIATION')
 write(out/'bindings.json',bindings);write(out/'deferred.json',deferred)
 def emit(package,rows,dep):
  f=out/(package+'.records.jsonl');f.write_text(''.join(canonical(r)+'\n' for r in rows),encoding='utf-8')
  m=dict(schema_version='learn-kg-canonical-candidate-1',package_id=package,version=VERSION,status='CANDIDATE',rights='PRIVATE_ONLY',owners=sorted({r['owner'] for r in rows}),dependencies=dep,files=[dict(path=f.name,format='JSONL_RECORDS',record_count=len(rows),sha256=file_sha(f))],qualification_receipt_refs=[])
  path=out/(package+'.manifest.json');schema('manifest').validate(m);write(path,m);return file_sha(path)
 ep=emit('evidence',[r for r in records.values() if r['kind']=='Source'],[])
 cp=emit('chinese',[r for r in records.values() if r['kind']!='Source'],[dict(package_id='evidence',version=VERSION,manifest_sha256=ep)])
 pins={'evidence.manifest.json':ep,'chinese.manifest.json':cp,'bindings.json':file_sha(out/'bindings.json'),'deferred.json':file_sha(out/'deferred.json')}
 descriptor=dict(status='PRIVATE_CANDIDATE_ONLY_NO_PUBLICATION',stage_manifest_sha256=mp,hsk01_receipt_sha256=rp,version=VERSION,documents=docs,pins=pins,counts={'canonical_hold':len(records),'deferred':len(deferred),'source_memberships':raw_shapes},rights_scope=RIGHTS_SCOPE,canonical_semantic_identity='NOT_ESTABLISHED',professional_qualification='NOT_RUN')
 write(out/'adapter-manifest.json',descriptor)
 result=import_private(out,file_sha(out/'adapter-manifest.json'),stage_root,mp,rp)
 return result
def import_private(root,descriptor_pin,stage_root,mp,rp):
 root=checked_root(root)
 def pinned(n,h):
  p=relative(root,n);need(file_sha(p)==h,'PRIVATE_PIN:'+n);return p
 desc=read(pinned('adapter-manifest.json',descriptor_pin))
 need(desc['status']=='PRIVATE_CANDIDATE_ONLY_NO_PUBLICATION' and desc['rights_scope']==RIGHTS_SCOPE and desc['stage_manifest_sha256']==mp and desc['hsk01_receipt_sha256']==rp and desc['version']==VERSION,'PRIVATE_DESCRIPTOR_SCOPE')
 # Exact stage correspondence is mandatory even on re-open, not only generation.
 stage=load_stage(checked_root(stage_root),mp,rp)
 docs={}
 for name,v in desc['documents'].items():
  p=pinned(name,v['sha256']);rr=read(p);k=Path(name).stem
  need(k in stage and rr==stage[k] and len(rr)==v['rows'] and p.stat().st_size==v['bytes'],'DOCUMENT_STAGE_BINDING')
  docs[name]=rr
 need(set(docs)=={'documents/'+k+'.json' for k in stage},'PRIVATE_DOC_SET')
 binds=read(pinned('bindings.json',desc['pins']['bindings.json']));deferred=read(pinned('deferred.json',desc['pins']['deferred.json']))
 hs,shapes=hs00_shapes()
 allrows={};manifests={};seen={};validators={}
 for package in ('evidence','chinese'):
  name=package+'.manifest.json';m=read(pinned(name,desc['pins'][name]));schema('manifest').validate(m)
  need(m['package_id']==package and m['version']==VERSION and m['rights']=='PRIVATE_ONLY' and m['status']=='CANDIDATE' and not m['qualification_receipt_refs'],'PRIVATE_PACKAGE_SCOPE')
  allowed={'EVIDENCE'} if package=='evidence' else {'H07'}
  need(set(m['owners'])==allowed,'PRIVATE_OWNER_SCOPE')
  expected=[] if package=='evidence' else [dict(package_id='evidence',version=VERSION,manifest_sha256=desc['pins']['evidence.manifest.json'])]
  need(m['dependencies']==expected,'PRIVATE_DEPENDENCY_PIN')
  manifests[package]=m;rows={}
  for f in m['files']:
   need(f['format']=='JSONL_RECORDS','PRIVATE_FORMAT')
   p=pinned(f['path'],f['sha256']);rr=[parse(l) for l in p.read_bytes().splitlines()];need(len(rr)==f['record_count'],'PRIVATE_ROW_COUNT')
   for r in rr:
    k=r['kind'];validators.setdefault(k,schema(k));validators[k].validate(r);id=r['stable_id']
    need(r['status']=='HOLD' and (k=='Source')==(package=='evidence') and r['owner'] in m['owners'] and id not in rows,'PRIVATE_RECORD_SCOPE')
    if k=='Source':need(r['rights']=='HOLD' and r['access']=='PRIVATE_ONLY','SOURCE_RIGHTS')
    b=binds[id];need(b['canonical_ref']==target_ref(r) and b['record_sha256']==sha(canonical(r).encode()),'CANONICAL_BINDING_DIGEST')
    need(len(r['provenance'])==1,'PRIVATE_PROVENANCE_CARDINALITY')
    prov=r['provenance'][0];n=prov['source_path'];doc=docs[n]
    need(prov['source_sha256']==desc['documents'][n]['sha256'] and prov['source_status']=='PRIVATE_PRESERVATION_CANDIDATE','PRIVATE_PROVENANCE_PIN')
    match=re.fullmatch(r'/([0-9]+)/raw_rdf',prov['json_pointer']);need(match is not None,'PRIVATE_PROVENANCE_POINTER')
    original=doc[int(match[1])];need(b['source_ref']==source_ref(original),'PRIVATE_PROVENANCE_ROW')
    sk=(original['raw_rdf']['graph'],original['raw_rdf']['stable_id'],original['raw_rdf']['kind']);need(sk not in seen,'DUPLICATE_STAGE_BINDING');seen[sk]=id
    if k=='SourceMembership':
     need(r['semantic_refs']==[] and r['mapping_status']=='HOLD' and r['owner']=='H07' and sk[2] in ('LexicalRecord','CharacterMembership'),'MEMBERSHIP_SCOPE')
     need(r['stable_id']=='HSK01.SOURCE.MEMBERSHIP.'+sha(canonical(list(sk)).encode())[:32],'MEMBERSHIP_STABLE_ID')
     projected=project_fields(original)
     for fld,v in projected.items():
      if v['state']=='MAPPED_VALUE':need(r[fld]==v['value'],'MEMBERSHIP_FIELD_REPLAY')
    else:
     need((sk[2],sk[1]) in shapes and r==held_shape(shapes[sk[2],sk[1]],r['provenance']),'HS00_EXACT_SHAPE_BINDING')
    rows[id]=r
  allrows[package]=rows
 need(set(binds)==set(allrows['evidence'])|set(allrows['chinese']),'BINDING_SET')
 stage_index={(r['raw_rdf']['graph'],r['raw_rdf']['stable_id'],r['raw_rdf']['kind']):r for rr in stage.values() for r in rr}
 for d in deferred:
  sr=d['source_ref'];sk=(sr['graph'],sr['source_entity_id'],sr['source_rdf_kind'])
  need(sk not in seen and sr==source_ref(stage_index[sk]) and d['status']=='HOLD_NO_CANONICAL_RECORD' and sr['source_rdf_kind'] in ('HanCharacter','TaxonomyTopic','AbilityRecord'),'DEFERRED_BINDING');seen[sk]='HOLD'
 need(set(seen)==set(stage_index),'STAGE_CLOSURE')
 edges=[]
 for package,rows in allrows.items():
  deps={x['package_id'] for x in manifests[package]['dependencies']}
  for r in rows.values():
   rules=INTERFACE['endpoint_rules'].get(r['kind'],{})
   for path,ref in refs(r):
    rule='/'.join('*' if type(k)is int else k for k in path)
    need(rule in rules and ref['kind'] in rules[rule],'PRIVATE_ENDPOINT_RULE')
    dest=ref['package_id'];need(dest==package or dest in deps,'PRIVATE_DIRECT_DEPENDENCY')
    t=allrows[dest].get(ref['stable_id']);need(t is not None and target_ref(t)==ref,'PRIVATE_EXACT_TARGET')
    edges.append((package,VERSION,r['stable_id'],'/'+ '/'.join(ptr_escape(x) for x in path),dest,VERSION,t['stable_id'],t['kind'],t['owner']))
   if r['kind']=='SourceMembership':
    b=binds[r['stable_id']]['source_ref'];sk=(b['graph'],b['source_entity_id'],b['source_rdf_kind']);orig=stage_index[sk];fs=parse_record(orig['raw_rdf'])
    # Same source and band as actual stage, standard via bound band version.
    for fld,pred in [('source_ref','source'),('band_ref','levelBand')]:
     target=r[fld]['stable_id'];sr=binds[target]['source_ref'];need(sr['source_entity_id']==field(fs,pred),'MEMBERSHIP_EXACT_SOURCE_BAND')
    band=allrows['chinese'][r['band_ref']['stable_id']];need(band['standard_ref']==r['standard_ref'],'MEMBERSHIP_EXACT_STANDARD')
 con=sqlite3.connect(':memory:')
 try:
  con.executescript("""PRAGMA temp_store=MEMORY;PRAGMA foreign_keys=ON;
  CREATE TABLE package_meta(package_id TEXT,version TEXT,manifest_sha256 TEXT NOT NULL,rights TEXT NOT NULL,PRIMARY KEY(package_id,version));
  CREATE TABLE registry(package_id TEXT,version TEXT,stable_id TEXT,kind TEXT NOT NULL,owner TEXT NOT NULL,status TEXT NOT NULL,PRIMARY KEY(package_id,version,stable_id),UNIQUE(package_id,version,stable_id,kind,owner),FOREIGN KEY(package_id,version) REFERENCES package_meta);
  CREATE TABLE typed_refs(origin_package TEXT,origin_version TEXT,origin_id TEXT,field_pointer TEXT,target_package TEXT,target_version TEXT,target_id TEXT,expected_kind TEXT,expected_owner TEXT,PRIMARY KEY(origin_package,origin_version,origin_id,field_pointer),FOREIGN KEY(origin_package,origin_version,origin_id) REFERENCES registry,FOREIGN KEY(target_package,target_version,target_id,expected_kind,expected_owner) REFERENCES registry(package_id,version,stable_id,kind,owner));""")
  for pk,m in manifests.items():
   con.execute('INSERT INTO package_meta VALUES(?,?,?,?)',(pk,VERSION,desc['pins'][pk+'.manifest.json'],m['rights']))
   con.executemany('INSERT INTO registry VALUES(?,?,?,?,?,?)',[(pk,VERSION,r['stable_id'],r['kind'],r['owner'],r['status']) for r in allrows[pk].values()])
  con.executemany('INSERT INTO typed_refs VALUES(?,?,?,?,?,?,?,?,?)',edges)
  counts={};roundtrip=0
  for kind in sorted({r['kind'] for rr in allrows.values() for r in rr.values()}):
   spec=MAPPING['record_tables'][kind];fields=spec['fields'];table=q(spec['table'])
   columns=','.join(q(f)+' '+v['sqlite_type']+' NOT NULL' for f,v in fields.items())
   con.execute(f'CREATE TABLE {table}(package_id TEXT,version TEXT,stable_id TEXT,kind TEXT,owner TEXT,{columns},PRIMARY KEY(package_id,version,stable_id),FOREIGN KEY(package_id,version,stable_id,kind,owner) REFERENCES registry(package_id,version,stable_id,kind,owner))')
   names=['package_id','version','stable_id','kind','owner',*fields];rr=[(pk,r) for pk,data in allrows.items() for r in data.values() if r['kind']==kind]
   def enc(f,r):
    v=r[f];return canonical(v) if fields[f]['encoding']=='CANONICAL_JSON' or type(v)is bool else v
   con.executemany(f'INSERT INTO {table}({",".join(map(q,names))}) VALUES({",".join("?" for _ in names)})',[(pk,VERSION,r['stable_id'],kind,r['owner'],*(enc(f,r) for f in fields)) for pk,r in rr])
   for row in con.execute(f'SELECT {",".join(map(q,names))} FROM {table}'):
    x=dict(zip(names,row));pk=x.pop('package_id');x.pop('version');orig=allrows[pk][x['stable_id']];x['status']=con.execute('SELECT status FROM registry WHERE package_id=? AND version=? AND stable_id=?',(pk,VERSION,x['stable_id'])).fetchone()[0]
    for f in fields:
     if fields[f]['encoding']=='CANONICAL_JSON' or type(orig[f])is bool:x[f]=json.loads(x[f])
    need(x==orig,'PRIVATE_SQL_RECORD_ROUNDTRIP');roundtrip+=1
   counts[kind]=len(rr)
  need(con.execute('PRAGMA foreign_key_check').fetchall()==[] and con.execute('PRAGMA integrity_check').fetchone()==('ok',),'PRIVATE_SQL_INTEGRITY')
  con.execute('CREATE INDEX membership_section ON record_sourcemembership(section,ordinal)')
  sql=con.execute('SELECT section,count(*) FROM record_sourcemembership GROUP BY section').fetchall()
  query_plan=[r[3] for r in con.execute('EXPLAIN QUERY PLAN SELECT * FROM record_sourcemembership WHERE section=? AND ordinal=?',('LEXICAL_SOURCE_RECORD',1))]
  con.execute('PRAGMA query_only=ON')
  need(all(not r[2] for r in con.execute('PRAGMA database_list')),'NO_PERSISTENT_SQLITE')
  return dict(status='PRIVATE_RESTRICTED_CANONICAL_HOLD_IMPORT',adapter_manifest_sha256=descriptor_pin,manifest_pins=desc['pins'],documents=desc['documents'],canonical_counts=counts,canonical_records=sum(counts.values()),deferred_records=len(deferred),typed_refs=len(edges),roundtrip=roundtrip,foreign_key_violations=0,query_only=con.execute('PRAGMA query_only').fetchone()[0]==1,membership_sections=dict(sql),membership_query_plan=query_plan,private_scope='NO_PUBLICATION_NO_GENERAL_IMPORTER',persistent_sqlite=False,physical_cross_db_crash='HOLD_NOT_TESTED')
 finally:con.close()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--stage',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--manifest-sha256',required=True);p.add_argument('--receipt-sha256',required=True);p.add_argument('--reopen-pin');a=p.parse_args()
 os.umask(0o077);r=import_private(a.output,a.reopen_pin,a.stage,a.manifest_sha256,a.receipt_sha256) if a.reopen_pin else create_projection(a.stage,a.output,a.manifest_sha256,a.receipt_sha256);print(json.dumps(r,ensure_ascii=False,sort_keys=True,indent=2))
