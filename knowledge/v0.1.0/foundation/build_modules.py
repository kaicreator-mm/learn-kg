#!/usr/bin/env python3
"""Explicit candidate authoring adapter for K01–K04, no scientific qualification."""
import json,hashlib,pathlib,collections,urllib.parse,copy
import jsonschema
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
Q=ROOT/'docs/drafts/stage-handoff/qualification-preparation'
D=ROOT/'docs/drafts/s01';DB=ROOT/'docs/implementation/db01';IF=ROOT/'docs/implementation/if01'
VERSION='0.1.0-foundation-candidate-1'
MODS=['K01','K02','K03','K04']
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
need(len(rows)==97,'scope')
oldclaims={c['id']:(t,c) for t in rows.values() for c in t['claims']};need(len(oldclaims)==sum(len(t['claims']) for t in rows.values()),'duplicate claim')
def cr(cid):return ref('Claim',cid,cid.split('.')[0])
source_research=load(P/'source-research.json');newcases=load(P/'discrimination-cases.json');oracles=load(P/'finite-oracles.json');results=load(P/'oracle-results.json')['results']
need(set(rows)=={r['topic'] for r in newcases} and len(newcases)==97,'new case set')
checks={(x['claim'],x['source']):(i,x) for i,x in enumerate(source_research['checks'])}
need(len(checks)==len(source_research['checks']),'duplicate source check')
sources={}
for i,f in enumerate(files):
 if f['path'].endswith('/sources.json'):
  for j,x in enumerate(data[i].get('sources',[])):sources[x['id']]=(x,oldprov([i,'/sources/'+str(j)],'HISTORICAL_RECORDED_SOURCE'))
for j,x in enumerate(source_research['new_sources']):
 need(x['id'] not in sources,'new source ID');sources[x['id']]=(x,sourcepath('source-research.json','/new_sources/'+str(j),'BUILDER_HTML_BODY_READ'))
used_sources={sr[0] for _,c in oldclaims.values() for sr in c['source_refs']}|{x['source'] for x in source_research['additions']}
for sid in sorted(used_sources):
 x,p=sources[sid]
 add('evidence',base('Source',sid,'EVIDENCE',p)|{'title':x['title'],'identifier':x.get('url') or sid,'access':x['access'],'rights':'HOLD','qualification':'NOT_RUN','bibliography':x['title'],'recorded_locator':x.get('locator') or None,'recorded_rights':x['rights']})
def check_url(sid,url):need(urllib.parse.unquote(sources[sid][0]['url'])==urllib.parse.unquote(url),'source url '+sid)
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
  for v,e in c['views'].items():case(c['id']+':'+v,o,c['claim_refs'],v.upper(),c['fixture'],e,prov(f,'/records/'+str(j),'HISTORICAL_SYNTHETIC_DESIGN'))
 # Keep original calculation/logic identities and actual builder results, never claim re-execution.
 field='logic_cases' if 'logic_cases' in a else 'numerical_cases'
 ev=D/o/('logic-evidence.json' if field=='logic_cases' else 'arithmetic-evidence.json')
 erows=load(ev)['results'];ri={x['id']:j for j,x in enumerate(erows)}
 for j,c in enumerate(a.get(field,[])):
  cid=c['claim_ref'];id=c['id'];vr=ref('Validation',id+':validation',o);p=prov(f,'/'+field+'/'+str(j),'HISTORICAL_BUILDER_FIXTURE')
  expected=c.get('expected',{k:v for k,v in c.items() if k.startswith('expected_')})
  r=case(id,o,[cid],'COMPOSITION',c,expected,p,actual='RECORDED_BUILDER_ONLY' if id in ri else 'NOT_RUN',oracle=vr)
  z=base('Validation',vr['stable_id'],o,p)|{'target_refs':[cr(cid)],'case_refs':[r],'method':'历史有限算术或逻辑设计；本轮仅保留原证据，不作为独立oracle','oracle_identity':None,'input_digest':digest(c),'result_digest':digest(erows[ri[id]]) if id in ri else None,'run_status':'BUILDER_RUN' if id in ri else 'NOT_RUN'}
  if id in ri:z['provenance'].append(prov(ev,'/results/'+str(ri[id]),'HISTORICAL_BUILDER_RESULT'))
  val_refs[cid].append(add('learning-core',z))
for j,x in enumerate(newcases):
 need(x['target_claim'] in oldclaims and oldclaims[x['target_claim']][0]['d3_id']==x['topic'],'case owner')
 case(x['topic']+'.F01.CASE',x['topic'].split('.')[0],[x['target_claim']],'COMPOSITION',x['input'],x['expected'],sourcepath('discrimination-cases.json','/'+str(j),'ORIGINAL_DISCRIMINATION_CASE'),x['negative_boundary'])
ridx={x['id']:j for j,x in enumerate(results)}
need(len(ridx)==len(oracles)==20,'oracle inventory')
for j,x in enumerate(oracles):
 cid=x['claim'];o=cid.split('.')[0];id=x['id'];need(cid in oldclaims,'oracle target')
 rj=ridx[id];need(results[rj]['status']=='PASS_BUILDER_FINITE_ONLY','actual oracle receipt')
 p=sourcepath('finite-oracles.json','/'+str(j),'AUTHOR_FROZEN_EXPECTATION')
 vr=ref('Validation',id+':validation',o)
 c=case(id,o,[cid],'COMPOSITION',x['input'],x['expected'],p,negative='只在所列输入及公式定义下的有限值；非独立科学资格。',actual='RECORDED_BUILDER_ONLY',oracle=vr)
 v=base('Validation',vr['stable_id'],o,p)|{'target_refs':[cr(cid)],'case_refs':[c],'method':'实际Python Fraction/NormalDist/有限三值逻辑等固定预期检查','oracle_identity':'author-frozen:'+sha(P/'finite-oracles.json'),'input_digest':digest(x['input']),'result_digest':digest(results[rj]),'run_status':'BUILDER_RUN'}
 v['provenance'].append(sourcepath('oracle-results.json','/results/'+str(rj),'ACTUAL_BUILDER_RESULT'));val_refs[cid].append(add('learning-core',v))
for cid,(t,c) in oldclaims.items():
 x=at(c['record']);o=t['owner']
 for sid,sp,field,state,access,rights in c['source_refs']:
  lid=cid+':'+sid;loc=x[field] if field else None
  attribution={'RECORDED_CLAIM_LOCATOR_NOT_REVERIFIED':'RECORDED_NOT_REVERIFIED','HOLD_CLAIM_LOCATOR_MISSING':'MISSING','HOLD_MULTI_SOURCE_ATTRIBUTION':'MULTI_SOURCE_HOLD'}[state]
  p=oldprov(c['record'],'HISTORICAL_CLAIM_LOCATOR')
  vr='NOT_RUN'
  if (cid,sid) in checks:
   j,z=checks[(cid,sid)];check_url(sid,z['url']);need(len(c['source_refs'])==1,'multi-source recheck needs separate disposition')
   loc=z['locator'];attribution='VERIFIED';vr='BUILDER_BODY_LOCATOR_CHECK_ONLY_NOT_QUALIFIED';p=sourcepath('source-research.json','/checks/'+str(j),'CURRENT_BODY_LOCATOR_CHECK')
  locrec=base('Locator',lid,o,p)|{'source_ref':ref('Source',sid,'EVIDENCE','evidence'),'location':loc,'attribution':attribution,'verification':vr}
  locrec['provenance'] += [oldprov(c['record'],'PRESERVED_ORIGINAL_CLAIM'),oldprov(sp,'PRESERVED_ORIGINAL_SOURCE')]
  # identical provenance objects are disallowed by schema; preserve distinct status.
  locator_refs[cid].append(add('learning-core',locrec))
for j,x in enumerate(source_research['additions']):
 t=x['topic'];cid=t+'.'+x['suffix'];o=t.split('.')[0];need(t in rows and cid not in oldclaims,'new claim')
 check_url(x['source'],x['url'])
 p=sourcepath('source-research.json','/additions/'+str(j),'CURRENT_BODY_LOCATOR_CHECK')
 lid=cid+':'+x['source'];locator_refs[cid].append(add('learning-core',base('Locator',lid,o,p)|{'source_ref':ref('Source',x['source'],'EVIDENCE','evidence'),'location':x['locator'],'attribution':'VERIFIED','verification':'BUILDER_BODY_LOCATOR_CHECK_ONLY_NOT_QUALIFIED'}))
 case(cid+':case',o,[cid],'COMPOSITION',x['fixture'],x['expected'],p,x['negative'])
 add('learning-core',base('Claim',cid,o,p,x['conditions'],x['negative'])|{'topic_id':t,'requirement_id':rows[t]['requirement_id'],'claim_type':x['type'],'statement':x['statement'],'source_status':'BODY_LOCATOR_RECHECKED_BUILDER_ONLY','locator_refs':locator_refs[cid],'case_refs':case_refs[cid],'validation_refs':[],'supersedes_refs':[],'refinement_of':None})
replacements=collections.defaultdict(list)
for old,(_,c) in oldclaims.items():
 for new in c['replacement_claim_refs']:replacements[new].append(cr(old))
for cid,(t,c) in oldclaims.items():
 x=at(c['record']);o=t['owner'];need(x['stable_id']==cid and x['owner']==o and x['requirement_id']==t['requirement_id'],'claim identity')
 # Inline examples stay exact, not rendered into a claim or inferred oracle.
 for field in c['inline_case_fields']:
  val=x[field]
  case(cid+':inline:'+field,o,[cid],'COMPOSITION',val,'原记录内联例；须单独确定预期与独立oracle。',oldprov(c['record'],'HISTORICAL_INLINE_EXAMPLE'),x['negative_boundary'])
 r=base('Claim',cid,o,oldprov(c['record'],'HISTORICAL_AUTHORING_RECORD'),x['conditions'],x['negative_boundary'],'HISTORICAL' if c['status']=='HISTORICAL_SUPERSEDED_CANDIDATE' else 'CANDIDATE')|{'topic_id':t['d3_id'],'requirement_id':t['requirement_id'],'claim_type':x['claim_type'],'statement':x['statement'],'source_status':x['evidence_status'],'locator_refs':locator_refs[cid],'case_refs':case_refs[cid],'validation_refs':val_refs[cid],'supersedes_refs':replacements[cid],'refinement_of':cr(c['parent_candidate']) if c['parent_candidate'] else None}
 add('learning-core',r)
# Four narrowly bounded explicit model/element relations. Preserve exact evidence, no inference.
def v(n):return {'variable':n}
def c(n):return {'constant':n}
def op(n,*a):return {'op':n,'args':list(a)}
modeldefs=[
('K01.02.04.D4.01','共同预测误差双线索模型','RATIONAL',[('lambda','strength','结果渐近值'),('a','strength','旧A强度'),('b','strength','旧B强度'),('rate_a','dimensionless','A学习率乘积'),('rate_b','dimensionless','B学习率乘积')],[('delta_a',op('mul',v('rate_a'),op('sub',v('lambda'),op('add',v('a'),v('b'))))),('delta_b',op('mul',v('rate_b'),op('sub',v('lambda'),op('add',v('a'),v('b')))))],['仅两线索同时在场，旧状态同步更新；本有限实例参数0..1','缺线索身份或学习率HOLD']),
('K02.06.05.D4.02','同标准未调整成本节省比','RATIONAL',[('initial','trials','首次成本'),('relearn','trials','再学成本')],[('savings',op('div',op('sub',v('initial'),v('relearn')),v('initial')))],['首次成本>0，再学成本≥0且标准、单位一致','成本下限和额外暴露限制解释；不等同直接保持']),
('K03.06.03.D4.05','简化整合KC条件比例模型','RATIONAL',[('hard','proportion','组合任务比例'),('simple','proportion','支持任务比例')],[('ratio',op('div',v('hard'),v('simple')))],['仅原命题独立合取、无额外观测误差等简化假设；0≤hard≤simple≤1且simple>0','不是个体掌握估计；缺假设HOLD']),
('K04.03.01.D4.02','零偏置标量状态更新','RATIONAL',[('x','state','旧状态'),('r','dimensionless','保留系数'),('k','dimensionless','更新系数'),('e','state','有符号校正误差')],[('next',op('add',op('mul',v('r'),v('x')),op('mul',v('k'),v('e'))))],['误差方向已明确定义且状态和误差单位一致；限定原简化模型','无校准与实际机制证据；缺符号HOLD'])]
for cid,label,domain,params,formulas,conditions in modeldefs:
 t,c0=oldclaims[cid];x=at(c0['record']);o=t['owner'];p=oldprov(c0['record'],'EXPLICIT_MODEL_FROM_ORIGINAL_CLAIM')
 e=add('learning-core',base('Element',cid+':element',o,p,conditions,x['negative_boundary'])|{'topic_id':t['d3_id'],'element_type':'BOUNDED_MATHEMATICAL_MODEL','label':label,'definition':'原命题所定义的有限计算对象，详见claim和ModelSpec。','claim_refs':[cr(cid)]})
 m=add('learning-core',base('ModelSpec',cid+':model',o,p,conditions,x['negative_boundary'])|{'claim_refs':[cr(cid)],'parameters':[{'name':n,'unit':u,'meaning':d,'lower':None,'upper':None} for n,u,d in params],'formulas':[{'name':n,'expr':f} for n,f in formulas],'numeric_domain':domain,'missing_policy':'HOLD','applicability':conditions})
 add('learning-core',base('Relation',cid+':defined_by_model',o,p,conditions,x['negative_boundary'])|{'relation_type':'defined_by_model','from_ref':e,'to_ref':m,'claim_refs':[cr(cid)],'condition_refs':[],'direction':'DIRECTED','automatic_transitive':False,'automatic_inverse':False})
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
  bytopic.append({'d3_id':t['d3_id'],'requirement_id':t['requirement_id'],'claim_ids':cid,'active_claim_ids':active,'prior_adequacy_disposition':t['adequacy_disposition'],'current_depth_disposition':'TARGETED_DISCRIMINATION_CASE_ADDED_NOT_ADEQUACY_VERDICT','source_locator_states':dict(gaps),'no_source_claim_ids':[k for k in cid if not locator_refs[k]],'case_ids':sorted({a['stable_id'] for k in cid for a in case_refs[k]}),'validation_ids':sorted({a['stable_id'] for k in cid for a in val_refs[k]}),'source_gap_policy':'Missing/ambiguous/unverified locator and unsupported empirical claims remain HOLD; original derivation and project rules distinguished.','view_scope_refs':t['applicable_view_scope_refs'],'explicit_view_claim_refs':{x['id']:x['explicit_view_bindings'] for x in t['claims'] if x['explicit_view_bindings']},'historical_relation_candidate_refs':t['topic_relation_refs'],'relation_disposition':'Only supported defined_by_model materialized as CANDIDATE; remaining semantic candidates/anchors retain original evidence and HOLD pending endpoint/claim qualification.','qualification':'NOT_RUN'})
 links=D/o/('theory-comparison.json' if o=='K01' else 'cross-topic-links.json')
 rc={'owner':o,'status':'CANDIDATE_READY_FOR_INDEPENDENT_MODULE_REVIEW_NOT_QUALIFIED','module_package':'learning-core','version':VERSION,'record_files':fs,'record_counts':dict(collections.Counter(x['kind'] for x in rr)),'typed_refs':counts[o],'topics':bytopic,'cross_topic_candidate_source':prov(links,'/records','HISTORICAL_CANDIDATE_ONLY'),'cq_routes':[{'id':x['cq_id'],'route':x['route'],'status':'NOT_RUN'} for x in cq if o in x['route']],'independent_receipt':None,'limits':['Per-topic discriminating synthetic case is new authoring; NOT_RUN for nonnumerical cases. No automatic professional adequacy closure.','Original claim statement, conditions, boundary and source/case pointers retained; no source/publication qualification, no automatic view applicability or relation promotion.','Finite author oracle executed; reviewer must independently derive and judge professional correctness. Wider professional depth, 180 prior unassessed themes overall, unresolved source locators and relations remain explicit.']}
 save(P/o/'coverage.json',rc);modules.append({'owner':o,'topics':len(bytopic),'records':len(rr),'claims':sum(r['kind']=='Claim' for r in rr),'active_claims':sum(r['kind']=='Claim' and r['status']=='CANDIDATE' for r in rr),'coverage_sha256':sha(P/o/'coverage.json'),'typed_refs':counts[o],'files':len(fs)})
cm=manifest('learning-core',MODS,cf,[{'package_id':'evidence','version':VERSION,'manifest_sha256':sha(P/'evidence.manifest.json')}])
result={'status':'FOUNDATION_MODULE_CANDIDATE_BUILDER_VALIDATION_ONLY','version':VERSION,'prior_input_files_checked':len(files),'modules':modules,'source_records':len(byowner['EVIDENCE']),'record_count':len(store),'typed_refs':sum(counts.values()),'new_topic_cases':len(newcases),'new_source_claims':len(source_research['additions']),'current_source_locator_checks':len(checks),'new_finite_oracles':len(oracles),'canonical_record_types':dict(collections.Counter(x['kind'] for x in store.values())),'manifests':{'learning-core':sha(P/'learning-core.manifest.json'),'evidence':sha(P/'evidence.manifest.json')},'historical_oracles_preserved':sum(len(load(D/o/'cases.json').get('logic_cases',load(D/o/'cases.json').get('numerical_cases',[]))) for o in MODS),'formal_cq_lc':'NOT_RUN','limits':'No independent qualification, actual learner or persistent SQLite. Source checks limited to listed HTML body passages; remaining locator/source/adequacy gaps explicit. Canonical projections deterministic, historical original files remain evidence, authoring inputs retained.'}
save(P/'validation-receipt.json',result);print(json.dumps(result,ensure_ascii=False))
