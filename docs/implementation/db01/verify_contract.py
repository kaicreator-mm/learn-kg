#!/usr/bin/env python3
"""Actual candidate-schema adapter witness. No persistent database or qualification."""
import copy, hashlib,json,pathlib,collections
import jsonschema
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
Q=ROOT/'docs/drafts/stage-handoff/qualification-preparation'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
s=load(P/'canonical.schema.json');m=load(P/'mapping-contract.json');jsonschema.Draft202012Validator.check_schema(s)
defs=s['$defs'];validators={k:jsonschema.Draft202012Validator({'$schema':s['$schema'],'$defs':defs,'$ref':'#/$defs/'+k}) for k in m['record_tables']}
for k,table in m['record_tables'].items():
 assert set(table['fields'])==set(defs[k]['properties'])-{'kind','stable_id','owner','status'}
 assert set(defs[k]['required'])==set(defs[k]['properties'])
 assert defs[k]['additionalProperties'] is False
led=load(Q/'ledger-manifest.json');files=led['files'];inputs=[]
for f in files:
 p=ROOT/f['path'];assert sha(p)==f['sha256'];inputs.append(load(p))
def ptr(r):
 i,p=r;assert type(i) is int and 0<=i<len(files);a=inputs[i]
 for k in p[1:].split('/'):a=a[int(k)] if isinstance(a,list) else a[k.replace('~1','/').replace('~0','~')]
 return a
def prov(r,st):
 i,p=r;return {'source_path':files[i]['path'],'source_sha256':files[i]['sha256'],'json_pointer':p,'source_status':st}
version='candidate-adapter-1'
def pkg(owner):return 'learning-core' if owner.startswith('K') else 'chinese'
def ref(k,i,o,p=None):return {'package_id':p or pkg(o),'version':version,'kind':k,'stable_id':i,'owner':o}
def base(k,i,o,r,st='CANDIDATE',conditions=None,negative=None):
 return {'kind':k,'stable_id':i,'owner':o,'status':st,'conditions':conditions or ['Recorded source/fixture scope; not independent qualification'],'negative_boundary':negative or 'Recorded candidate does not establish evidence support or applicability.','provenance':[prov(r,st)]}
rows=[]
for sh in led['shards']:
 p=Q/sh['file'];assert sha(p)==sh['sha256']
 for line in p.read_text().splitlines():
  t=dict(zip(led['topic_columns'],json.loads(line),strict=True));t['claims']=[dict(zip(led['claim_columns'],c,strict=True)) for c in t['claims']];rows.append(t)
claims={c['id']:(t,c) for t in rows for c in t['claims']};assert len(claims)==1743
record_store={};refs=[]
def add(p,r):
 validators[r['kind']].validate(r)
 key=(p,version,r['kind'],r['stable_id'],r['owner']);assert key not in record_store
 record_store[key]=r
def c_ref(cid):
 t,c=claims[cid];return ref('Claim',cid,t['owner'])
# source records from exact source files (including uncited records).
for i,f in enumerate(files):
 if not f['path'].endswith('/sources.json'):continue
 for j,x in enumerate(inputs[i].get('sources',[])):
  rid=x['id'];r=[i,'/sources/'+str(j)]
  rec=base('Source',rid,'EVIDENCE',r)|{'title':x['title'],'identifier':x.get('url') or rid,'access':x['access'],'rights':'HOLD','qualification':'NOT_RUN','bibliography':x['title'],'recorded_locator':x.get('locator') or None,'recorded_rights':x['rights']}
  add('evidence',rec)
assert sum(k[2]=='Source' for k in record_store)==455
# Case specs represent the four distinct views; exact original fixture/text retained.
case_by_id={}
for i,f in enumerate(files):
 if not f['path'].endswith('/cases.json') or '/depth/' in f['path']:continue
 for j,x in enumerate(inputs[i]['records']):
  r=[i,'/records/'+str(j)];cid=x['id'];o=x['owner'];rr=[]
  assert set(x['views'])=={'forward','reverse','intervention','counterexample'}
  for name,expected in x['views'].items():
   ident=cid+':'+name;rr.append(ref('Case',ident,o))
   rec=base('Case',ident,o,r)|{'target_refs':[c_ref(a) for a in x['claim_refs']],'view':name.upper(),'input_spec':x['fixture'],'expected_spec':expected,'oracle_ref':None,'actual_status':'NOT_RUN'}
   add(pkg(o),rec)
  case_by_id[cid]=rr
assert len(case_by_id)==648
replacements=collections.defaultdict(list)
for old,(_,prev) in claims.items():
 for new in prev['replacement_claim_refs']:replacements[new].append(c_ref(old))
for cid,(t,c) in claims.items():
 x=ptr(c['record']);o=t['owner'];locs=[];vals=[]
 for sr in c['source_refs']:
  sid,sp,field,locstate,access,rights=sr
  k=cid+':'+sid;locs.append(ref('Locator',k,o))
  rec=base('Locator',k,o,c['record'])|{'source_ref':ref('Source',sid,'EVIDENCE','evidence'),'location':x[field] if field else None,'attribution':{'RECORDED_CLAIM_LOCATOR_NOT_REVERIFIED':'RECORDED_NOT_REVERIFIED','HOLD_CLAIM_LOCATOR_MISSING':'MISSING','HOLD_MULTI_SOURCE_ATTRIBUTION':'MULTI_SOURCE_HOLD'}[locstate],'verification':'NOT_RUN'}
  rec['provenance'].append(prov(sp,'RECORDED_SOURCE_ONLY'));add(pkg(o),rec)
 # Numeric designs remain historical case references, distinct from the four-view case set.
 for n in c['validation_refs']:
  case=ptr(n['case_pointer']);k=n['case_id'];v=k+':validation';vals.append(ref('Validation',v,o))
  add(pkg(o),base('Case',k,o,n['case_pointer'])|{'target_refs':[c_ref(cid)],'view':'COMPOSITION','input_spec':json.dumps(case,ensure_ascii=False,sort_keys=True),'expected_spec':'Original numeric fixture; oracle remains historical builder design','oracle_ref':None,'actual_status':'RECORDED_BUILDER_ONLY' if n['result_pointer'] else 'NOT_RUN'})
  rec=base('Validation',v,o,n['case_pointer'])|{'target_refs':[c_ref(cid)],'case_refs':[ref('Case',k,o)],'method':'Historical arithmetic fixture; no independent oracle issued','oracle_identity':None,'input_digest':None,'result_digest':None,'run_status':'NOT_RUN'}
  if n['result_pointer']:rec['provenance'].append(prov(n['result_pointer'],'RECORDED_BUILDER_ONLY'))
  add(pkg(o),rec)
 record=base('Claim',cid,o,c['record'],'HISTORICAL' if c['status']=='HISTORICAL_SUPERSEDED_CANDIDATE' else 'CANDIDATE',x['conditions'],x['negative_boundary'])|{'topic_id':t['d3_id'],'requirement_id':t['requirement_id'],'claim_type':x['claim_type'],'statement':x['statement'],'source_status':x['evidence_status'],'locator_refs':locs,'case_refs':[r for k in c['case_refs'] for r in case_by_id[k]],'validation_refs':vals,'supersedes_refs':[],'refinement_of':c_ref(c['parent_candidate']) if c['parent_candidate'] else None}
 # Actual replacement direction: replacement supersedes old historical candidate.
 record['supersedes_refs']=replacements[cid]
 add(pkg(o),record)
def allrefs(x):
 if isinstance(x,dict):
  if set(x)=={'package_id','version','kind','stable_id','owner'}:yield x
  else:
   for v in x.values():yield from allrefs(v)
 elif isinstance(x,list):
  for v in x:yield from allrefs(v)
for k,v in record_store.items():
 for r in allrefs(v):
  key=(r['package_id'],r['version'],r['kind'],r['stable_id'],r['owner']);assert key in record_store
  assert key[0]==k[0] or key[0] in m['package_roles'][k[0]]['depends_on']
  refs.append(key)
# Canonical serialization checks and finite schema negative probes.
for v in record_store.values():
 assert json.loads(json.dumps(v,ensure_ascii=False,sort_keys=True,allow_nan=False))==v
sample=next(v for v in record_store.values() if v['kind']=='Claim')
negative=[]
def reject(name,v,kind='Claim'):
 if validators[kind].is_valid(v):raise AssertionError(name)
 negative.append(name)
x=copy.deepcopy(sample);del x['conditions'];reject('missing_conditions',x)
x=copy.deepcopy(sample);x['conditions']=[];reject('empty_conditions',x)
x=copy.deepcopy(sample);x['unexpected']=1;reject('unknown_field',x)
x=copy.deepcopy(sample);x['status']='PASS';reject('invalid_status',x)
x=copy.deepcopy(sample);x['locator_refs']=['bare-id'];reject('bare_id',x)
x=copy.deepcopy(sample);x['negative_boundary']=' ';reject('empty_boundary',x)
x=copy.deepcopy(sample);x['provenance'][0]['source_sha256']='fake';reject('bad_source_digest',x)
x=copy.deepcopy(sample);x['kind']='Source';reject('wrong_kind',x)
expr={'op':'mul','args':[{'variable':'x'},{'variable':'x'}]}
ev=jsonschema.Draft202012Validator({'$defs':defs,'$ref':'#/$defs/expr'})
ev.validate(expr);assert not ev.is_valid({'op':'eval','args':[{'constant':1}]});negative.append('arbitrary_expression')
manifestvalidator=jsonschema.Draft202012Validator({'$defs':defs,'$ref':'#/$defs/manifest'})
mf={'schema_version':m['schema_version'],'package_id':'learning-core','version':version,'status':'CANDIDATE','rights':'HOLD','owners':['K01'],'dependencies':[],'files':[{'path':'records.jsonl','sha256':'0'*64,'format':'JSONL_RECORDS','record_count':1}],'qualification_receipt_refs':[]}
manifestvalidator.validate(mf)
for name,path in [('parent_path','../records.jsonl'),('absolute_path','/records.jsonl'),('database_file','records.sqlite')]:
 v=copy.deepcopy(mf);v['files'][0]['path']=path;assert not manifestvalidator.is_valid(v);negative.append(name)
receipt={'status':'DB01_AUTHORING_SCHEMA_CANDIDATE_VALIDATION','schema_sha256':sha(P/'canonical.schema.json'),'mapping_sha256':sha(P/'mapping-contract.json'),'record_kinds':len(validators),'table_mappings':len(m['record_tables']),'relation_types':len(m['relations']),'exact_inputs':len(files),'coverage_shards':len(led['shards']),'actual_adapter_record_counts':dict(collections.Counter(k[2] for k in record_store)),'actual_adapter_typed_ref_count':len(refs),'negative_rejected':negative,'limits':['Finite design/adapter witness, no DB02 importer or SQLite database generated. No persisted converted facts; original files are authoritative; exact provenance pointers retain unprojected professional fields and historical records.','Schema shapes are baseline not proof of scientific adequacy, semantic endpoint/type/owner applicability, package rights, full field adapter or formal release. IF01 adds shared semantic contract; DB02 implements strict parser and exact manifest resolution; module tasks expand professional fields under version control.','All 1743 claims remain candidates/historical, no independent qualification. Only historical numeric validation specs are preserved; no new CQ/LC executed.']}
(P/'validation-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
print(json.dumps(receipt,ensure_ascii=False))
