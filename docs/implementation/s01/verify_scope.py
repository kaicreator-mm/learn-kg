#!/usr/bin/env python3
"""S01 candidate scope acceptance preparation, not scientific qualification."""
import json,hashlib,pathlib,collections
ROOT=pathlib.Path(__file__).resolve().parents[3]
P=ROOT/'docs/drafts/s01'
Q=ROOT/'docs/drafts/stage-handoff/qualification-preparation'
OUT=pathlib.Path(__file__).resolve().parent
def load(p):return json.loads(p.read_text())
def digest(p):
 b=p.read_bytes()
 return {'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'git_blob':hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()}
inv=load(P.parent/'s01-scope-inventory.json');led=load(Q/'ledger-manifest.json');vc=load(Q/'views-cq-relations.json');dag=load(ROOT/'docs/implementation/task-dag.json')
tasks={t['id']:t for t in dag['tasks']};topic={x['id']:x for x in inv['topics']}
assert len(topic)==823==len(inv['topics'])
for t in topic.values():
 assert t['owner'] in tasks and (t['depth']==1 and t['parent'] is None and t['id']==t['owner'] or t['depth']>1 and t['parent'] in topic and topic[t['parent']]['depth']==t['depth']-1 and topic[t['parent']]['owner']==t['owner'])
assert collections.Counter(t['depth'] for t in topic.values())=={1:26,2:149,3:648}
source_data=[]
for f in led['files']:
 p=ROOT/f['path'];a=digest(p)
 assert a['git_blob']==f['git_blob'] and a['sha256']==f['sha256']
 source_data.append(load(p))
def resolve(ref):
 i,ptr=ref;assert type(i) is int and 0<=i<len(source_data)
 x=source_data[i]
 for k in ptr[1:].split('/'): x=x[int(k)] if isinstance(x,list) else x[k.replace('~1','/').replace('~0','~')]
 return x
rows={};claims={};mod=collections.defaultdict(list)
for sh in led['shards']:
 p=Q/sh['file'];assert digest(p)['sha256']==sh['sha256']
 for line in p.read_text().splitlines():
  t=dict(zip(led['topic_columns'],json.loads(line),strict=True));tid=t['d3_id'];assert tid not in rows and topic[tid]['depth']==3 and topic[tid]['owner']==t['owner']
  r=resolve(t['requirement_ref']);assert r['d3_id']==tid and r['requirement_id']==t['requirement_id'] and r['research_requirement'] and r['negative_boundary']
  assert t['omission_or_na']=='NO_FORMAL_OMISSION_OR_NA_DECISION' and t['qualification']=='NOT_RUN'
  t['claims']=[dict(zip(led['claim_columns'],c,strict=True)) for c in t['claims']]
  assert t['claims']
  for c in t['claims']:
   x=resolve(c['record']);assert c['id'] not in claims and x['stable_id']==c['id'] and x['d3_id']==tid and x['owner']==t['owner'] and x['requirement_id']==r['requirement_id']
   assert x[c['conditions_field']] and x[c['counterexample_field']] and c['qualification_receipt'] is None and c['consumed_tuple'] is None
   assert [s[0] for s in c['source_refs']]==x['source_refs']
   claims[c['id']]=c
  rows[tid]=t;mod[t['owner']].append(t)
assert set(rows)=={i for i,t in topic.items() if t['depth']==3} and len(claims)==1743 and len(mod)==26
superseded=[c for c in claims.values() if c['status']=='HISTORICAL_SUPERSEDED_CANDIDATE'];assert len(superseded)==3
assert all(c['replacement_claim_refs'] and all(k in claims for k in c['replacement_claim_refs']) for c in superseded)
qual=dag['qualification_by_module']
modules=[]
for m,rr in sorted(mod.items()):
 cc=[c for t in rr for c in t['claims']]
 modules.append({'owner':m,'d1_id':m,'d2_count':sum(t['depth']==2 and t['owner']==m for t in topic.values()),'d3_count':len(rr),'candidate_claim_count':sum(c['status']!='HISTORICAL_SUPERSEDED_CANDIDATE' for c in cc),'historical_claim_count':sum(c['status']=='HISTORICAL_SUPERSEDED_CANDIDATE' for c in cc),'source_status_counts':dict(collections.Counter(c['source_status'] for c in cc)),'scope_source_leads':sorted({s for t in rr for s in t['scope_source_leads']}),'source_locator_state_counts':dict(collections.Counter(s[3] for c in cc for s in c['source_refs'])),'adequacy_disposition_counts':dict(collections.Counter(t['adequacy_disposition'][0] for t in rr)),'no_scope_omission_proposed':True,'qualification_task':qual[m],'qualification':'NOT_RUN','formal_claim_receipts':0})
views=load(P/'process-view-requirements.json')['views'];vmap={x['id']:x for x in vc['views']}
assert set(vmap)=={x['id'] for x in views} and len(views)==27
viewout=[]
for v in views:
 vid=v['id'];assert vid in tasks and v['owner']==vid and set(v['professional_topic_refs'])<=set(rows) and v['original_scope'] and v['negative_boundary'] and v['validation_requirement']['status']=='NOT_RUN'
 assert set(v['task_dependencies'])==set(tasks[vid]['depends_on'])
 rr=vmap[vid]['requirements'];assert len(rr)==4 and {r['id'] for r in rr}=={r['id'] for r in v['requirements']}
 assert all(r['formal_receipt'] is None for r in rr)
 viewout.append({'id':vid,'owner':vid,'requirement_ids':[r['id'] for r in rr],'candidate_status_counts':dict(collections.Counter(r['status'] for r in rr)),'scope_omission':'NONE_PROPOSED','qualification_task':qual.get(vid,'G03'),'qualification':'NOT_RUN'})
assert len(qual)==36 and sum(x['qualification_task']=='G03' for x in viewout)==17
cqs=load(ROOT/'docs/implementation/coverage-ledger.json');cr=cqs['items'];cq=vc['cq']
assert len(cr)==len(cq)==26
for a,b in zip(cr,cq):
 assert (a['id'],a['owner'],a['route'],a['lc_id'])==(b['cq_id'],b['owner'],b['route'],b['lc_id']) and a['status']==b['status']=='NOT_RUN'
 assert all(x in tasks for x in b['route']) and b['owner'] in tasks and b['actual_result'] is None and b['review_receipt'] is None
 assert set(cqs['required_case_fields'])<=set(b)
assert len({x['lc_id'] for x in cq if x['lc_id']})==12
leads=load(P/'source-leads.json')['sources'];assert len(leads)==45 and len({x['id'] for x in leads})==45
assert {s for m in modules for s in m['scope_source_leads']}<={x['id'] for x in leads}
hsk=load(P/'hsk-source-domain-mapping.json');assert hsk['qualification']=='NOT_RUN' and hsk['publication']=='HOLD' and len(hsk['mappings'])==9
assert all(set(x['target_requirement_topics'])<=set(rows) for x in hsk['mappings'])
fields={'owner':'topic.owner','d3_id':'topic.d3_id','d4_id_or_coverage_reason':'claim.id and topic.d4_coverage_reason (historical split excluded only in consumption)','claim_type':'claim.claim_type','source_locator':'claim.source_refs[3] status and [2] original locator field; source pointer [1], not evidence support','source_status':'claim.source_status + individual citation state','claim_id':'claim.id','element_relation_refs':'claim.element_relation_refs (candidate only; empty means no explicit binding)','conditions':'resolve(claim.record)[claim.conditions_field]','counterexample':'resolve(claim.record)[claim.counterexample_field] and explicit case counterexample if present','case_refs':'claim.case_refs plus explicit inline_case_fields; no inferred validation','validation_refs':'claim.validation_refs; saved historical builder arithmetic result only; empty not validated','applicable_views':'explicit_view_bindings; topic scope/anchors separate; absent explicit binding unresolved, never NA','qualification_receipt':'claim.qualification_receipt null (not issued)','consumed_tuple':'claim.consumed_tuple null (not issued)','status':'claim.status + topic.adequacy_disposition; qualification NOT_RUN'}
assert set(fields)==set(cqs['required_module_fields'])
files=[Q/'ledger-manifest.json',Q/'views-cq-relations.json',Q/'build_ledger.py',Q/'mapping_probe.py',Q/'mapping-receipt.json',P.parent/'s01-scope-inventory.json',P/'source-leads.json',P/'process-view-requirements.json',P/'cq-lifecycle-fixture-requirements.json',P/'hsk-source-domain-mapping.json',ROOT/'docs/implementation/coverage-ledger.json',ROOT/'docs/product/decision-index.md',ROOT/'docs/implementation/task-execution-contract.md',Q/'src01-original-pdf-backup-evidence.json']
files += [Q/s['file'] for s in led['shards']]
record={'task_id':'S01','status':'SCOPE_CANDIDATE_READY_FOR_G01_NOT_QUALIFIED','planning_review_comment':7211695681,'planning_head':'be5c9c4b032d04070c0ad4643222df4a0c828f06','candidate_overlay_review_comments':[7203292140,7203533827],'scope_policy':'All planned K/H D1-D3 and P/F/A/E views remain in scope; no proposed omissions or NA. Unassessed adequacy, gaps, rights and actual validation are HOLD/NOT_RUN, not exclusions. Historical inventory status superseded for scope inventory only, never professional qualification. G01 may reject scope or identify omissions.',
 'counts':led['counts']|{'taxonomy_nodes':823,'d1':26,'d2':149,'view_owners':27,'local_qualification_modules':36,'g03_combination_owners':17},
 'module_field_mapping':fields,'module_scope':modules,'view_scope':viewout,
 'cq_lc':{'ledger':digest(Q/'views-cq-relations.json'),'status':'26_NOT_RUN','lc_count':12,'fixture_plan':digest(P/'cq-lifecycle-fixture-requirements.json'),'rule':'fixture/oracle and actual result must be populated by downstream V01/G03/G04/V02; no textual match as PASS.'},
 'source_qualification_plan':{'45_scope_leads':dict(collections.Counter(x['status'] for x in leads)),'455_source_records':'Candidate only; per-claim source identity and locator, applicability, access/rights and validation qualified by owner tasks/local batches then G03/G05. Project rules do not require fabricated empirical source; no direct source means explicit state, not automatic error or support.','995_citation_states':led['counts']['citation_locator_states'],'HSK':'9 source mapping kinds; RHSK01–03 current originals fingerprinted and restored, historical PDF identity/14 blocks/rights unresolved; SRC01 no preservation receipt, HS00/HSK01 not dispatched. HSK3.0 version records separate from other standards and levels are not skill equivalence.'},
 'decision_alignment':{'D001_D006':'Independent repo/consumer boundary and Git identity','D002_D007_D009':'K19/H7 primary owners, Chinese pilot not universal scope; 823 hierarchy nodes','D003_D005_D013':'Finite module evidence and independent gates; no qualification by quotas','D004_D008':'Private original source/rights isolated, no raw release','D010_D014':'Historical RDF retained; human-readable authoritative inputs; optional derived SQLite only, no persistent database','D011_D012':'27 composition views, 108 requirements, 26 CQ/12 LC dual loops and role/evidence boundaries','D015':'Documented historical and adopted candidate evidence, no lost history'},
 'inputs':[digest(x) for x in files],'original_ledger_input_count':len(led['files']),'formal_qualification_receipts':0,'formal_cq':'NOT_RUN','limits':['All candidate scope records and pointers checked, not professional adequacy or source verification; no claims qualified. G01 independent scope gate is still required.','Formal module field mapping resolves exact original JSON; no new duplicate authoritative knowledge records. 180 explicitly unassessed topics and other HOLDs carried forward.','No persistent SQLite, private content, runtime execution or learning-effect evidence.']}
(OUT/'scope-candidate.json').write_text(json.dumps(record,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
print(json.dumps({'topics':len(rows),'claims':len(claims),'owners':len(modules)+len(viewout),'sources':455,'views':len(views),'cq':len(cq),'lc':12,'input_hashes':len(led['files']),'shards':len(led['shards']),'field_map':len(fields),'source_leads':len(leads),'scope_candidate':'READY_FOR_G01'},ensure_ascii=False))
