#!/usr/bin/env python3
"""Explicit candidate authoring adapter for K14/K18, no scientific qualification."""
import json,hashlib,pathlib,collections,urllib.parse,copy
import jsonschema
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
Q=ROOT/'docs/drafts/stage-handoff/qualification-preparation'
D=ROOT/'docs/drafts/s01';DB=ROOT/'docs/implementation/db01';IF=ROOT/'docs/implementation/if01'
VERSION='0.1.0-domain-development-candidate-2'
MODS=['K14','K18']
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def need(ok,msg):
 if not ok:raise ValueError(msg)
s=load(DB/'canonical.schema.json');defs=s['$defs'];interface=load(IF/'interface-contract.json')
validators={k:jsonschema.Draft202012Validator({'$defs':defs,'$ref':'#/$defs/'+k}) for k in interface['endpoint_rules']}
def validator(k):
 if k not in validators:validators[k]=jsonschema.Draft202012Validator({'$defs':defs,'$ref':'#/$defs/'+k})
 return validators[k]
led=load(Q/'ledger-manifest.json');files=led['files'];data=[]
for f in files:
 p=ROOT/f['path'];need(sha(p)==f['sha256'],'source digest '+f['path']);data.append(load(p))
def at(r):
 i,p=r;need(type(i) is int and 0<=i<len(data),'pointer index');x=data[i]
 for k in p[1:].split('/'):x=x[int(k)] if isinstance(x,list) else x[k.replace('~1','/').replace('~0','~')]
 return x
def prov(p,ptr,status):
 return {'source_path':p.relative_to(ROOT).as_posix(),'source_sha256':sha(p),'json_pointer':ptr,'source_status':status}
def oldprov(r,status):
 i,p=r;return {'source_path':files[i]['path'],'source_sha256':files[i]['sha256'],'json_pointer':p,'source_status':status}
def sourcepath(f,ptr,status):return prov(P/f,ptr,status)
def base(kind,id,owner,provenance,conditions=None,negative=None,status='CANDIDATE'):
 return {'kind':kind,'stable_id':id,'owner':owner,'status':status,'conditions':conditions or ['限定已声明的候选证据及任务情境。'],'negative_boundary':negative or '不得从记录、示例或结构校验推断独立专业资格。','provenance':[provenance]}
def ref(k,id,o,p='learning-core'):return {'package_id':p,'version':VERSION,'kind':k,'stable_id':id,'owner':o}
store={};byowner=collections.defaultdict(list)
def add(p,r):
 validator(r['kind']).validate(r)
 k=(p,VERSION,r['stable_id']);need(k not in store,'duplicate stable id '+str(k))
 store[k]=r;byowner[r['owner']].append(r);return ref(r['kind'],r['stable_id'],r['owner'],p)
rows={}
for sh in led['shards']:
 f=Q/sh['file'];need(sha(f)==sh['sha256'],'shard hash')
 for line in f.read_text().splitlines():
  t=dict(zip(led['topic_columns'],json.loads(line),strict=True))
  if t['owner'] not in MODS:continue
  t['claims']=[dict(zip(led['claim_columns'],x,strict=True)) for x in t['claims']];rows[t['d3_id']]=t
need(len(rows)==41,'scope')
oldclaims={c['id']:(t,c) for t in rows.values() for c in t['claims']};need(len(oldclaims)==sum(len(t['claims']) for t in rows.values()),'duplicate claim')
def cr(cid):return ref('Claim',cid,cid.split('.')[0])

PREP=ROOT/'docs/implementation/k14-k18-preparation'
depth=load(PREP/'depth.json')
need(len(depth)==41 and set(x['topic'] for x in depth)==set(rows),'depth coverage')
need(len(oldclaims)==109,'historical claims')
# Earlier access labels are withdrawn; only actual current checked passages enter canonical locators.
research=[];verified={}
bounded=[(i,x) for i,x in enumerate(load(P/'current-source-observations.json')['records']) if x['topic'].split('.')[0] in MODS and x['access']=='ACTUAL_RETURNED_BODY_SECTION']
need(len(bounded)==5,'bounded observed sources')
sources={}
for _,c in oldclaims.values():
 for sid,sp,*_ in c['source_refs']:
  x=at(sp)
  if sid in sources:need(sources[sid][0]==x,'source identity collision '+sid)
  else:sources[sid]=(x,oldprov(sp,'HISTORICAL_RECORDED_SOURCE'))
for sid,(x,p) in sorted(sources.items()):
 add('evidence',base('Source',sid,'EVIDENCE',p,status='HOLD')|{'title':x['title'],'identifier':x.get('url') or sid,'access':x['access'],'rights':'HOLD','qualification':'NOT_RUN','bibliography':x['title'],'recorded_locator':x.get('locator') or None,'recorded_rights':x['rights']})
# Preserve source identity; verified alternate URLs appear in exact claim-specific locators.
full_claims=set()
context_topics={oldclaims[x['claim']][0]['d3_id'] for x in research if x['access']!='HISTORICAL_RECORDED_NOT_REVERIFIED'}
# Taxonomy and scope requirements in explicit typed records.
invpath=ROOT/'docs/drafts/s01-scope-inventory.json';inv=load(invpath)
for j,t in enumerate(inv['topics']):
 if t['owner'] not in MODS:continue
 add('learning-core',base('Topic',t['id'],t['owner'],prov(invpath,'/topics/'+str(j),'ADOPTED_G01_SCOPE'))|{'label':t['label'],'depth':t['depth'],'parent_ref':ref('Topic',t['parent'],t['owner']) if t['parent'] else None})
for t in rows.values():
 r=at(t['requirement_ref'])
 add('learning-core',base('Requirement',r['requirement_id'],r['owner'],oldprov(t['requirement_ref'],'G01_SCOPE'),negative=r['negative_boundary'])|{'topic_ref':ref('Topic',r['d3_id'],r['owner']),'scope':r['research_requirement'],'source_leads':r['source_leads'],'coverage_status':'CANDIDATE_NOT_QUALIFIED'})
case_refs=collections.defaultdict(list);val_refs=collections.defaultdict(list);locator_refs=collections.defaultdict(list)
def case(id,owner,target,view,inp,expected,p,negative=None,actual='NOT_RUN',oracle=None):
 r=base('Case',id,owner,p,negative=negative)|{'target_refs':[cr(x) for x in target],'view':view,'input_spec':inp if isinstance(inp,str) else json.dumps(inp,ensure_ascii=False,sort_keys=True),'expected_spec':expected if isinstance(expected,str) else json.dumps(expected,ensure_ascii=False,sort_keys=True),'oracle_ref':oracle,'actual_status':actual}
 rr=add('learning-core',r)
 for x in target:case_refs[x].append(rr)
 return rr
for o in MODS:
 f=D/o/'cases.json';a=load(f)
 for j,c in enumerate(a['records']):
  for v,e in c['views'].items():
   ca=case(c['id']+':'+v,o,c['claim_refs'],v.upper(),c['fixture'],e,prov(f,'/records/'+str(j),'HISTORICAL_SYNTHETIC_DESIGN'))
   r=store[('learning-core',VERSION,ca['stable_id'])];r['status']='HISTORICAL';r['negative_boundary']='历史叙述例 NOT_RUN，不作为当前反事实条件或可执行预期。';validator('Case').validate(r)

# Historical numerical records remain preserved as input evidence, not replayed or promoted.
for cid,(t,c) in oldclaims.items():
 x=at(c['record']);o=t['owner']
 for sid,sp,field,state,access,rights in c['source_refs']:
  lid=cid+':'+sid;loc=x[field] if field else None
  attribution={'RECORDED_CLAIM_LOCATOR_NOT_REVERIFIED':'RECORDED_NOT_REVERIFIED','HOLD_CLAIM_LOCATOR_MISSING':'MISSING','HOLD_MULTI_SOURCE_ATTRIBUTION':'MULTI_SOURCE_HOLD'}[state]
  p=oldprov(c['record'],'HISTORICAL_CLAIM_LOCATOR')
  z=base('Locator',lid,o,p,status='HOLD')|{'source_ref':ref('Source',sid,'EVIDENCE','evidence'),'location':loc,'attribution':attribution,'verification':'NOT_RUN'}
  z['provenance'].append(oldprov(sp,'PRESERVED_ORIGINAL_SOURCE'))
  locator_refs[cid].append(add('learning-core',z))
  if (cid,sid) in verified:
   i,v=verified[cid,sid];p=sourcepath('source-trace.json','/records/'+str(i),'ACTUAL_BOUNDED_SOURCE_CHECK')
   full=v['support_scope']=='FULL_SCOPED' and v['access'] in ('BODY_SECTION_READ','ABSTRACT_READ','GUIDE_RECOMMENDATION_READ') and v.get('receipt_sha256')==sha(P/'source-retrieval-receipt.json')
   lr=base('Locator',lid+':current',o,p,negative=v['support_and_limits'],status='CANDIDATE' if full else 'HOLD')|{'source_ref':ref('Source',sid,'EVIDENCE','evidence'),'location':v['url']+' — '+v['locator'],'attribution':'VERIFIED' if full else 'RECORDED_NOT_REVERIFIED','verification':v['access']+'_'+v['support_scope']+'_BUILDER_ONLY'}
   lr['provenance'].append(oldprov(sp,'PRESERVED_SOURCE_IDENTITY'))
   receipt=load(P/'source-retrieval-receipt.json')
   need(receipt['http_status']==200 and receipt['final_url']==v['url'] and v['receipt_sha256']==sha(P/'source-retrieval-receipt.json'),'actual retrieval receipt')
   need(set(v['paragraph_ordinals'])<={x['ordinal'] for x in receipt['observed_sections']},'observed passage')
   lr['provenance'].append(sourcepath('source-retrieval-receipt.json','/observed_sections','ACTUAL_HTTP_RESPONSE_DIGEST_BOUND'))

   locator_refs[cid].append(add('learning-core',lr))
   if full and len(c['source_refs'])==1:full_claims.add(cid)
for j,x in enumerate(depth):
 t=x['topic'];o=rows[t]['owner'];cid=t+'.DD.01';p=prov(PREP/'depth.json','/'+str(j),'ORIGINAL_METHOD_DERIVATION')
 case(cid+':case',o,[cid],'COMPOSITION',x['fixture'],x['expected_and_boundary'],p,'合成例非实证；未知或缺失证据不补值。')
 add('learning-core',base('Claim',cid,o,p,['按原D3范围与合成案例明确条件执行；适用性、因果及外推待独立专业审查。'],at(rows[t]['requirement_ref'])['negative_boundary'])|{'topic_id':t,'requirement_id':rows[t]['requirement_id'],'claim_type':'ORIGINAL_METHOD_DERIVATION','statement':x['method'],'source_status':'ORIGINAL_METHOD_DERIVATION_NOT_EMPIRICAL_FINDING','locator_refs':locator_refs[cid],'case_refs':case_refs[cid],'validation_refs':[],'supersedes_refs':[],'refinement_of':None})
replacements=collections.defaultdict(list)
for old,(_,c) in oldclaims.items():
 for new in c['replacement_claim_refs']:replacements[new].append(cr(old))
for cid,(t,c) in oldclaims.items():
 x=at(c['record']);o=t['owner'];need(x['stable_id']==cid and x['owner']==o and x['requirement_id']==t['requirement_id'],'claim identity')
 # Inline examples stay exact, not rendered into a claim or inferred oracle.
 for field in c['inline_case_fields']:
  val=x[field]
  case(cid+':inline:'+field,o,[cid],'COMPOSITION',val,'原记录内联例；须单独确定预期与独立oracle。',oldprov(c['record'],'HISTORICAL_INLINE_EXAMPLE'),x['negative_boundary'])
 r=base('Claim',cid,o,oldprov(c['record'],'HISTORICAL_AUTHORING_RECORD'),x['conditions'],x['negative_boundary'],'HISTORICAL' if c['status']=='HISTORICAL_SUPERSEDED_CANDIDATE' else ('HOLD' if c['source_refs'] and cid not in full_claims else 'CANDIDATE'))|{'topic_id':t['d3_id'],'requirement_id':t['requirement_id'],'claim_type':x['claim_type'],'statement':x['statement'],'source_status':'HTTP_RESPONSE_DIGEST_BOUND_SCOPED_BUILDER_CHECK' if cid in full_claims else x['evidence_status'],'locator_refs':locator_refs[cid],'case_refs':case_refs[cid],'validation_refs':val_refs[cid],'supersedes_refs':replacements[cid],'refinement_of':cr(c['parent_candidate']) if c['parent_candidate'] else None}
 add('learning-core',r)

# Source-limited new claims, not promotion of broad historical source claims.
for i,x in bounded:
 t=x['topic'];o=t.split('.')[0];cid=t+'.DD.S01';sid=x['source_id']
 need(sid in sources,'source identity')
 pp=sourcepath('current-source-observations.json','/records/'+str(i),'ACTUAL_RETURNED_BODY_SECTION_BOUNDED')
 lr=add('learning-core',base('Locator',cid+':locator',o,pp,negative=x['boundary'])|{'source_ref':ref('Source',sid,'EVIDENCE','evidence'),'location':x['url']+' — '+x['locator'],'attribution':'VERIFIED','verification':'ACTUAL_RETURNED_BODY_SECTION_BUILDER_ONLY'})
 locator_refs[cid].append(lr);context_topics.add(t)
 d=next(z for z in depth if z['topic']==t)
 ca=case(cid+':case',o,[cid],'COMPOSITION',d['fixture'],d['expected_and_boundary'],pp,x['boundary'])
 add('learning-core',base('Claim',cid,o,pp,negative=x['boundary'])|{'topic_id':t,'requirement_id':rows[t]['requirement_id'],'claim_type':'SOURCE_LIMITED_FRAMEWORK_OR_METHOD','statement':x['support'],'source_status':'ACTUAL_RETURNED_BOUNDED_BODY_SECTION_BUILDER_ONLY','locator_refs':[lr],'case_refs':[ca],'validation_refs':[],'supersedes_refs':[],'refinement_of':None})
 add('learning-core',base('Relation',cid+':evidence',o,pp,negative=x['boundary'])|{'relation_type':'evidence_for','from_ref':lr,'to_ref':cr(cid),'claim_refs':[cr(cid)],'condition_refs':[],'direction':'DIRECTED','automatic_inverse':False,'automatic_transitive':False})
for j,x in enumerate(depth):
 cid=x['topic']+'.DD.01';o=cid.split('.')[0];pp=prov(PREP/'depth.json','/'+str(j),'ORIGINAL_METHOD_DERIVATION')
 add('learning-core',base('Relation',cid+':example',o,pp,negative='合成案例非真实结果。')|{'relation_type':'example_of','from_ref':ref('Case',cid+':case',o),'to_ref':cr(cid),'claim_refs':[cr(cid)],'condition_refs':[],'direction':'DIRECTED','automatic_transitive':False,'automatic_inverse':False})
old_fixtures=load(P/'finite-fixtures.json');old_results=load(P/'finite-results.json')
new_fixtures=load(P/'guarded-fixtures.json');new_results=load(P/'guarded-results.json')
review_path=ROOT/'evidence/validation/K13-K14-K17-K18-FINITE-01.json';review=load(review_path)
group=review['groups'][1]
need(review['status']=='INDEPENDENT_FINITE_ACCEPT_SCOPED' and group['fixture_sha256']==sha(P/'finite-fixtures.json') and group['result_sha256']==sha(P/'finite-results.json') and group['method_sha256']==sha(P/'run_finite.py'),'exact prior independent finite identity')
need(old_results['fixture_sha256']==sha(P/'finite-fixtures.json') and new_results['fixture_sha256']==sha(P/'guarded-fixtures.json'),'fixture identity')
oracles=old_fixtures+new_fixtures
for j,(x,z) in enumerate(zip(oracles,old_results['results']+new_results['results'],strict=True)):
 historical=j<len(old_fixtures);k=j if historical else j-len(old_fixtures)
 fx='finite-fixtures.json' if historical else 'guarded-fixtures.json';rz='finite-results.json' if historical else 'guarded-results.json'
 cid=x['topic']+'.DD.01';o=cid.split('.')[0];id=cid+'.F'+str(j);vr=ref('Validation',id+':validation',o)
 need(z['id']==x['id'] and z['actual']==x['expected']==z['expected'] and z['status']=='PASS_BUILDER_FINITE_ONLY','finite result')
 pp=sourcepath(fx,'/'+str(k),'AUTHOR_FROZEN_EXPECTATION')
 ca=case(id,o,[cid],'COMPOSITION',x['input'],x['expected'],pp,'旧独立精确合成结果；不得作为通用因果、临床或资格判据。' if historical else '新通用守卫有限合成测试；独立复审待定。','INDEPENDENTLY_CHECKED' if historical else 'RECORDED_BUILDER_ONLY',vr)
 vv=base('Validation',vr['stable_id'],o,pp)|{'target_refs':[cr(cid)],'case_refs':[ca],'method':'Prior independently derived exact finite expectation; not generic evaluator approval' if historical else 'New bounded author guard; independent derivation pending','oracle_identity':'issue-comment:7219401206:'+sha(review_path) if historical else 'author-frozen:'+sha(P/fx),'input_digest':digest(x['input']),'result_digest':digest(z),'run_status':'INDEPENDENT_RUN' if historical else 'BUILDER_RUN'}
 vv['provenance'].append(sourcepath(rz,'/results/'+str(k),'ACTUAL_BUILDER_RESULT'))
 if historical:vv['provenance'].append(prov(review_path,'/groups/1','EXACT_PRIOR_INDEPENDENT_RESULT'))
 val_refs[cid].append(add('learning-core',vv));claim=store[('learning-core',VERSION,cid)];claim['case_refs']=case_refs[cid];claim['validation_refs']=val_refs[cid];validator('Claim').validate(claim)
# Verify every typed field against IF01 plus exact stable identity and package dependency.
rules=interface['endpoint_rules'];counts=collections.Counter()
def values(x,path):
 if not path:return [x] if x is not None else []
 k,*rest=path
 if k=='*':return [z for v in x for z in values(v,rest)]
 return values(x.get(k),rest) if isinstance(x,dict) and k in x else []
for (p,v,id),r in store.items():
 for path,kinds in rules.get(r['kind'],{}).items():
  for x in values(r,path.split('/')):
   target=store.get((x['package_id'],x['version'],x['stable_id']))
   need(target is not None and x['kind']==target['kind'] and x['owner']==target['owner'] and x['kind'] in kinds,'typed ref '+id+':'+path)
   need(x['package_id']==p or p=='learning-core' and x['package_id']=='evidence','dependency')
   counts[r['owner']]+=1
 if r['kind']=='Relation':need([r['from_ref']['kind'],r['to_ref']['kind']] in interface['relation_endpoints'][r['relation_type']],'relation matrix')
 for p0 in r['provenance']:
  f=ROOT/p0['source_path'];need(sha(f)==p0['source_sha256'],'record provenance')
# Write canonical UTF-8 JSONL shards. Originals remain immutable evidence; derived files are generated, not separately edited.
def shard(directory,records):
 directory.mkdir(exist_ok=True,parents=True);out=[];buf=[];size=0
 for r in sorted(records,key=lambda x:(x['kind'],x['stable_id'])):
  line=(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
  need(len(line)<=78000,'oversize record')
  if size+len(line)>78000 and buf:
   f=directory/('records-%02d.jsonl'%len(out));f.write_bytes(b''.join(buf));out.append({'path':f.relative_to(P).as_posix(),'sha256':sha(f),'format':'JSONL_RECORDS','record_count':len(buf)});buf=[];size=0
  buf.append(line);size+=len(line)
 if buf:
  f=directory/('records-%02d.jsonl'%len(out));f.write_bytes(b''.join(buf));out.append({'path':f.relative_to(P).as_posix(),'sha256':sha(f),'format':'JSONL_RECORDS','record_count':len(buf)})
 return out
# All package manifest paths relative to foundation root; not release.
ef=shard(P/'evidence',byowner['EVIDENCE'])
def manifest(p,owners,files,deps):
 x={'schema_version':interface['schema_version'],'package_id':p,'version':VERSION,'status':'CANDIDATE','rights':'HOLD','owners':owners,'dependencies':deps,'files':files,'qualification_receipt_refs':[]}
 validator('manifest').validate(x);save(P/(p+'.manifest.json'),x);return x
em=manifest('evidence',['EVIDENCE'],ef,[])
modules=[];cf=[]
cq=load(Q/'views-cq-relations.json')['cq']
for o in MODS:
 rr=byowner[o];fs=shard(P/o,rr);cf+=fs
 bytopic=[]
 for t in rows.values():
  if t['owner']!=o:continue
  cid=[r['stable_id'] for r in rr if r['kind']=='Claim' and r['topic_id']==t['d3_id']]
  active=[i for i in cid if store[('learning-core',VERSION,i)]['status']=='CANDIDATE']
  ls=[store[('learning-core',VERSION,a['stable_id'])] for k in cid for a in locator_refs[k]]
  gaps=collections.Counter(x['attribution'] for x in ls)
  bytopic.append({'d3_id':t['d3_id'],'requirement_id':t['requirement_id'],'claim_ids':cid,'active_claim_ids':active,'prior_adequacy_disposition':t['adequacy_disposition'],'current_depth_disposition':'TARGETED_DISCRIMINATION_CASE_ADDED_NOT_ADEQUACY_VERDICT','source_locator_states':dict(gaps),'no_source_claim_ids':[k for k in cid if not locator_refs[k]],'case_ids':sorted({a['stable_id'] for k in cid for a in case_refs[k]}),'validation_ids':sorted({a['stable_id'] for k in cid for a in val_refs[k]}),'source_gap_policy':'Missing/ambiguous/unverified locator and unsupported empirical claims remain HOLD; original derivation and project rules distinguished.','view_scope_refs':t['applicable_view_scope_refs'],'explicit_view_claim_refs':{x['id']:x['explicit_view_bindings'] for x in t['claims'] if x['explicit_view_bindings']},'historical_relation_candidate_refs':t['topic_relation_refs'],'relation_disposition':'Explicit example/evidence relations only; historical semantic anchors pending integration.','qualification':'NOT_RUN'})
 links=D/o/'cross-topic-links.json'
 rc={'owner':o,'status':'STRUCTURAL_CANDIDATE_PARTIAL_PROFESSIONAL_WORK','module_package':'learning-core','version':VERSION,'record_files':fs,'record_counts':dict(collections.Counter(x['kind'] for x in rr)),'typed_refs':counts[o],'topics':bytopic,'cross_topic_candidate_source':prov(links,'/records','HISTORICAL_CANDIDATE_ONLY') if links.exists() else None,'cq_routes':[{'id':x['cq_id'],'route':x['route'],'status':'NOT_RUN'} for x in cq if o in x['route']],'independent_receipt':None,'limits':['Per-topic discriminating synthetic case is new authoring; NOT_RUN for nonnumerical cases. No automatic professional adequacy closure.','Original claim statement, conditions, boundary and source/case pointers retained; no source/publication qualification, no automatic view applicability or relation promotion.','New finite cases builder-only; source and professional qualification pending.']}
 save(P/o/'coverage.json',rc);modules.append({'owner':o,'topics':len(bytopic),'records':len(rr),'claims':sum(r['kind']=='Claim' for r in rr),'active_claims':sum(r['kind']=='Claim' and r['status']=='CANDIDATE' for r in rr),'coverage_sha256':sha(P/o/'coverage.json'),'typed_refs':counts[o],'files':len(fs)})
cm=manifest('learning-core',MODS,cf,[{'package_id':'evidence','version':VERSION,'manifest_sha256':sha(P/'evidence.manifest.json')}])

result={'status':'STRUCTURAL_PROJECTION_PARTIAL_NOT_MODULE_READY','version':VERSION,'prior_input_files_checked':len(files),'modules':modules,'source_records':len(byowner['EVIDENCE']),'record_count':len(store),'typed_refs':sum(counts.values()),'new_topic_cases':len(depth),'old_claims':len(oldclaims),'finite_builder_cases':len(new_fixtures),'prior_independent_finite_cases':len(old_fixtures),'bounded_source_propositions':len(bounded),'actual_current_claim_source_checks':sum(x['access']!='HISTORICAL_RECORDED_NOT_REVERIFIED' for x in research),'historical_source_leads_retained':sum(x['access']=='HISTORICAL_RECORDED_NOT_REVERIFIED' for x in research),'direct_full_scoped_claims':len(full_claims),'topics_with_current_checks':len(context_topics),'topics_without_current_checks':sorted(set(rows)-context_topics),'canonical_record_types':dict(collections.Counter(x['kind'] for x in store.values())),'manifests':{'learning-core':sha(P/'learning-core.manifest.json'),'evidence':sha(P/'evidence.manifest.json')},'formal_cq_lc':'NOT_RUN','limits':'Prior independent exact finite cases retained; new guards builder-only. Current source observations narrowly rechecked. Professional qualification, integration, rights and CQ/LC pending. No SQLite artifact.'}
save(P/'validation-receipt.json',result);print(json.dumps(result,ensure_ascii=False))
