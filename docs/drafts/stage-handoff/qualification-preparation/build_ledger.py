#!/usr/bin/env python3
"""Deterministic draft S01 scope/evidence ledger. No knowledge or task promotion."""
from pathlib import Path
from collections import defaultdict, Counter
import hashlib, json, re, sys
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
P=ROOT/'docs/drafts/s01'
D=P/'depth/D3'
R=D/'remediation'
VERSION='6fcd93a6cd74c22e9b002613bfad3d0f2a4a1fae'
TREE='10ee6e1ea608d9f2c67b8dbd631b63bd0777fb13'
def unique_pairs(items):
    result={}
    for k,v in items:
        if k in result: raise ValueError('duplicate JSON key '+k)
        result[k]=v
    return result
files={}
def read(path):
    path=Path(path)
    name=path.relative_to(ROOT).as_posix()
    raw=path.read_bytes()
    files[name]={'git_blob':hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),'sha256':hashlib.sha256(raw).hexdigest()}
    return json.loads(raw,object_pairs_hook=unique_pairs)
def ptr(path,section,i):
    return [Path(path).relative_to(ROOT).as_posix(),f'/{section}/{i}']
def add_unique(store,k,v):
    if k in store:raise ValueError('duplicate ID '+k)
    store[k]=v
def save(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def rows(path,section):
    for i,x in enumerate(read(path)[section]):yield x,ptr(path,section,i)
def index(paths,section,key):
    result={}
    for path in paths:
        for x,p in rows(path,section):add_unique(result,x[key],(x,p))
    return result
def nonempty(s):return isinstance(s,str) and bool(s.strip())
inventory=read(P.parent/'s01-scope-inventory.json')
topics={x['id']:x for x in inventory['topics'] if x['depth']==3}
mods=sorted({x['owner'] for x in topics.values()})
assert len(mods)==26 and len(topics)==648
requirements=index([P/(m+'-requirements.json') for m in mods],'records','d3_id')
coverage=index([P/m/'coverage.json' for m in mods],'records','d3_id')
assert set(topics)==set(requirements)==set(coverage)
claimfiles=[P/m/'claims.json' for m in mods]+sorted((P/'depth/D2').glob('**/claims.json'))+[R/'R2/claims.json']
claims=index(claimfiles,'records','stable_id')
sources=index([f.with_name('sources.json') for f in claimfiles],'sources','id')
cases=index([P/m/'cases.json' for m in mods],'records','id')
assert len(claims)==1743 and len(sources)==455 and len(cases)==648
split=read(R/'R2/claims.json')['split']
superseded={x['previous_id']:x['replacement_ids'] for x in split}
assert len(superseded)==3
for k,rs in superseded.items():
    assert k in claims and rs and len(rs)==len(set(rs))
    assert all(x in claims and x not in superseded and claims[x][0]['d3_id']==claims[k][0]['d3_id'] for x in rs)
views=index([P/'process-view-requirements.json'],'views','id')
composition=index([D/'G02/composition-contracts.json'],'contracts','task_id')
bindings=index([D/'G03/claim-bindings.json'],'contracts','task_id')
assert set(views)==set(composition)==set(bindings) and len(views)==27
view_by_topic=defaultdict(set); anchor_by_topic=defaultdict(set); bind_by_claim=defaultdict(list)
for k,(v,p) in views.items():
    for t in v['professional_topic_refs']:
        assert t in topics;view_by_topic[t].add(k)
    for t in composition[k][0]['research_topic_anchors']:
        assert t in topics;anchor_by_topic[t].add(k)
    for i,b in enumerate(bindings[k][0]['bindings']):
        c=b['claim_id'];assert c in claims and b['topic']==claims[c][0]['d3_id']
        bind_by_claim[c].append([k,bindings[k][1][0],bindings[k][1][1]+'/bindings/'+str(i)])
rel=index([D/'G01/semantic-candidates.json'],'records','id')
correction=read(R/'R1/relation-correction.json')
assert rel[correction['id']][0]==correction['previous']
rel[correction['id']]=(correction['replacement'],[(R/'R1/relation-correction.json').relative_to(ROOT).as_posix(),'/replacement'])
relation_types=read(D/'G01/relation-types.json')['types']
rel_by_claim=defaultdict(list);rel_by_topic=defaultdict(list);relations=[]
for k,(x,p) in sorted(rel.items()):
    assert x['from'] in topics and x['to'] in topics and relation_types[x['type']]['from']==relation_types[x['type']]['to']=='TOPIC'
    assert x['qualification']=='NOT_RUN' and x['materialize_accepted'] is False
    assert all(c in claims for c in x['claim_refs'])
    for c in x['claim_refs']:rel_by_claim[c].append(k)
    for t in (x['from'],x['to']):rel_by_topic[t].append(k)
    relations.append({'id':k,'type':x['type'],'from':x['from'],'to':x['to'],'claim_refs':x['claim_refs'],'pointer':p,'historical_claim_refs':[c for c in x['claim_refs'] if c in superseded],'status':'CANDIDATE_ONLY','qualification':'NOT_RUN'})
triage=index(sorted((R/'R2').glob('triage-*.json')),'records','topic')
r5=read(R/'R5/depth-disposition.json')
targeted={x['topic']:i for i,x in enumerate(r5['targeted'])}
retained={x['topic']:i for i,x in enumerate(r5['retention_pending_adequacy'])}
assert len(triage)==327 and len(targeted)==12 and len(retained)==180 and not set(targeted)&set(retained)
assert set(targeted)|set(retained)<=set(triage)
r5path=(R/'R5/depth-disposition.json').relative_to(ROOT).as_posix()
claim_cases=defaultdict(list);claim_num=defaultdict(list)
for k,(c,p) in cases.items():
    assert c['d3_id'] in topics and c['owner']==topics[c['d3_id']]['owner'] and c['validation']=='NOT_RUN'
    for a in c['claim_refs']:
        assert a in claims and claims[a][0]['d3_id']==c['d3_id']
        claim_cases[a].append(k)
# Only exact numerical case ID + claim reference + matching saved result are bound.
# Module-level test presence is not a claim-level validation.
num_count=0;num_results=0
for m in mods:
    cp=P/m/'cases.json';data=read(cp)
    n=data.get('numerical_cases',[])
    if not n:continue
    evidence=P/m/'arithmetic-evidence.json'
    if not evidence.exists():continue
    ev=read(evidence)
    result_idx={x['id']:i for i,x in enumerate(ev.get('results',[]))}
    assert len(result_idx)==len(ev.get('results',[]))
    for i,x in enumerate(n):
        assert x['claim_ref'] in claims
        item={'case_id':x['id'],'case_pointer':ptr(cp,'numerical_cases',i),'result_pointer':None,'result_status':'NOT_BOUND','qualification':'NOT_RUN'}
        if x['id'] in result_idx:
            j=result_idx[x['id']];item['result_pointer']=ptr(evidence,'results',j)
            item['result_status']=ev['results'][j].get('status','SAVED_RESULT_ONLY')
            num_results+=1
        claim_num[x['claim_ref']].append(item);num_count+=1
c_by_topic=defaultdict(list)
locator_counts=Counter();claim_states=Counter();active_states=Counter();case_counts=Counter();binding_counts=Counter();no_source=Counter()
for cid,(c,p) in sorted(claims.items()):
    t=c['d3_id'];req=requirements[t][0]
    assert c['owner']==req['owner']==topics[t]['owner'] and c['requirement_id']==req['requirement_id']
    assert c['qualification']=='NOT_RUN' and c['status']=='DRAFT' and c['conditions'] and nonempty(c['negative_boundary']) and nonempty(c['statement'])
    assert len(c['source_refs'])==len(set(c['source_refs']))
    refs=[]
    fields=[k for k in ('source_locator','evidence_locator_note') if nonempty(c.get(k))]
    assert len(fields)<=1
    for s in c['source_refs']:
        source,sp=sources[s];assert source['qualification']=='NOT_RUN'
        field=fields[0] if fields else None
        locstatus=('HOLD_CLAIM_LOCATOR_MISSING' if not field else 'RECORDED_CLAIM_LOCATOR_NOT_REVERIFIED' if len(c['source_refs'])==1 else 'HOLD_MULTI_SOURCE_ATTRIBUTION')
        locator_counts[locstatus]+=1
        refs.append([s,sp,field,locstatus,source['access'],'HOLD_PUBLICATION_QUALIFICATION'])
    active=cid not in superseded
    if not refs:no_source['ACTIVE' if active else 'HISTORICAL']+=1
    claim_states[c['evidence_status']]+=1
    if active:active_states[c['evidence_status']]+=1
    parent=c.get('base_claim_ref')
    if parent:assert parent in claims and claims[parent][0]['d3_id']==t
    inline=[k for k in ('example','case') if k in c]
    case_counts['EXPLICIT_ORIGINAL_CASE' if claim_cases[cid] else 'NO_ORIGINAL_CLAIM_CASE']+=1
    if inline:case_counts['INLINE_EXAMPLE_OR_CASE']+=1
    binding_counts['EXPLICIT' if bind_by_claim[cid] else 'UNBOUND']+=1
    row={'id':cid,'kind':'CLAIM','claim_type':c['claim_type'],'record':p,
         'source_status':c['evidence_status'],'source_refs':refs,
         'conditions_field':'conditions','counterexample_field':'negative_boundary',
         'parent_candidate':parent,'parent_is_historical':parent in superseded if parent else False,
         'case_refs':sorted(claim_cases[cid]),'inline_case_fields':inline,
         'validation_refs':claim_num[cid],'validation_status':'HISTORICAL_SYNTHETIC_RESULT_ONLY' if any(x['result_pointer'] for x in claim_num[cid]) else 'NOT_RUN_OR_NOT_EXPLICITLY_BOUND',
         'element_relation_refs':sorted(rel_by_claim[cid]),'explicit_view_bindings':bind_by_claim[cid],
         'status':'CANDIDATE_PENDING_QUALIFICATION' if active else 'HISTORICAL_SUPERSEDED_CANDIDATE',
         'replacement_claim_refs':superseded.get(cid,[]),'qualification_receipt':None,'consumed_tuple':None}
    c_by_topic[t].append(row)
# Partition by D1 modules; no invented non-applicability, all qualification pending.
topic_rows=[]
for t in sorted(topics):
    req,rp=requirements[t];cov,cp=coverage[t];owner=req['owner']
    assert req['requirement_id']==cov['requirement_id'] and owner==topics[t]['owner']
    orig=set(cov['claim_refs']);assert orig<=set(claims)
    assert all(claims[c][0]['d3_id']==t for c in orig)
    assert all(c in cases and cases[c][0]['d3_id']==t for c in cov['case_refs'])
    rr=c_by_topic[t];assert rr and len({x['id'] for x in rr})==len(rr)
    if t in targeted:
        disposition=['R5_FACET_EXAMPLES_PARTIAL_OR_HOLD',r5path,'/targeted/'+str(targeted[t])]
    elif t in retained:
        disposition=['RETAIN_PENDING_PROFESSIONAL_ADEQUACY_NOT_ASSESSED',r5path,'/retention_pending_adequacy/'+str(retained[t])]
    elif t in triage:
        x,pp=triage[t];disposition=[x['decision'],*pp]
    else:
        disposition=['DEPTH_CANDIDATES_EXIST_NOT_ADEQUACY_PASS',None,None]
        assert any(x['parent_candidate'] for x in rr)
    topic_rows.append({'d3_id':t,'owner':owner,'requirement_id':req['requirement_id'],'requirement_ref':rp,'original_coverage_ref':cp,
       'd4_coverage_reason':'RECORDED_CANDIDATE_CLAIMS_NOT_ADEQUACY_VERDICT','adequacy_disposition':disposition,
       'omission_or_na':'NO_FORMAL_OMISSION_OR_NA_DECISION','scope_source_leads':req['source_leads'],
       'applicable_view_scope_refs':sorted(view_by_topic[t]),'contract_anchor_views':sorted(anchor_by_topic[t]),
       'topic_relation_refs':sorted(rel_by_topic[t]),'topic_case_refs':cov['case_refs'],'claims':rr,'qualification':'NOT_RUN'})
assert sum(len(x['claims']) for x in topic_rows)==1743
# Current 108 requirement coverage: original IDs + R3 and exact R5 overlay.
mappings=index([R/'R3/requirement-mapping.json'],'records','requirement_id')
corrections=index([R/'R5/requirement-corrections.json'],'records','requirement_id')
assert len(mappings)==108 and len(corrections)==14
view_rows=[]
for k,(v,p) in sorted(views.items()):
    rr=[]
    for rq in v['requirements']:
        rid=rq['id'];x,oldp=mappings[rid]
        assert x['contract']==k and x['original_scope']==rq['scope']
        y,newp=corrections.get(rid,(None,None))
        if y:assert y['previous_status']==x['status'] and y['previous_interpretation']==x['interpretation'] and y['contract']==k
        z=y or x
        assert z['formal_receipt']=='NOT_ISSUED'
        rr.append({'id':rid,'scope':rq['scope'],'status':z['status'],'map_record':newp or oldp,'prior_map_record':oldp if y else None,'evidence_paths':z['evidence_paths'],'formal_receipt':None})
    view_rows.append({'id':k,'scope_ref':p,'contract_ref':composition[k][1],'binding_ref':bindings[k][1],'requirements':rr,'qualification':'NOT_RUN'})
allmap=[q for v in view_rows for q in v['requirements']]
assert len(allmap)==108 and len({q['id'] for q in allmap})==108
assert Counter(q['status'] for q in allmap)=={'CANDIDATE_EXEMPLIFIED':61,'CANDIDATE_PARTIAL':37,'CANDIDATE_HOLD':10}
cq=[]
a=read(ROOT/'docs/implementation/coverage-ledger.json')['items']
b=read(P/'cq-lifecycle-fixture-requirements.json')['items']
for i,(x,y) in enumerate(zip(a,b)):
    assert (x['id'],x['owner'],x['route'],x['lc_id'],x['status'])==(y['id'],y['owner'],y['route'],y['lc_id'],y['status'])
    assert x['status']=='NOT_RUN' and all(y[k] is None for k in ('fixture_digest','oracle_digest','actual_result'))
    cq.append({'cq_id':x['id'],'lc_id':x['lc_id'],'owner':x['owner'],'route':x['route'],'requirement_record':ptr(P/'cq-lifecycle-fixture-requirements.json','items',i),'expected_positive':y['original_expected_positive'],'expected_negative':y['original_expected_negative'],'d4_refs':[],'fixture_id_hash':None,'oracle_id_hash':None,'actual_result':None,'evidence_hash':None,'input_manifest':None,'code_env_hash':None,'applicability':'PENDING','status':'NOT_RUN','review_receipt':None,'hold_or_na_reason':None})
assert len(a)==len(b)==len(cq)==26 and len({x['lc_id'] for x in cq if x['lc_id']})==12
# Source discovery records kept separate from claim-level citations.
leads=read(P/'source-leads.json')['sources']
assert len(leads)==45 and len({x['id'] for x in leads})==45
lead_ids={x['id'] for x in leads}
assert all(set(x['scope_source_leads'])<=lead_ids for x in topic_rows)
# Path index reduces repetitive long paths in readable JSONL (one object per D3).
# Pointer is [file_index, JSON pointer]. Full names/hash in manifest.
paths=sorted(files)
indices={p:i for i,p in enumerate(paths)}
def remap(v):
    if isinstance(v,list):
        if len(v)==2 and isinstance(v[0],str) and v[0] in indices and isinstance(v[1],str) and v[1].startswith('/'):
            return [indices[v[0]],v[1]]
        return [remap(x) for x in v]
    if isinstance(v,dict):return {k:remap(x) for k,x in v.items()}
    return v
# Stable readable per-module shards, grouped to reduce file count.
groups=[mods[i:i+4] for i in range(0,len(mods),4)]
output_manifest=[]
for group in groups:
    name='coverage-'+group[0]+'-'+group[-1]+'.jsonl'
    selected=[x for x in topic_rows if x['owner'] in group]
    # JSONL records remain fully readable, with original content only in source records.
    (OUT/name).write_text(''.join(json.dumps(remap(x),ensure_ascii=False,separators=(',',':'))+'\n' for x in selected),encoding='utf-8')
    raw=(OUT/name).read_bytes()
    output_manifest.append({'file':name,'topics':len(selected),'claims':sum(len(x['claims']) for x in selected),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
save('views-cq-relations.json',remap({'status':'DRAFT_NOT_RUN','views':view_rows,'cq':cq,'relations':relations}))
manifest={'status':'S01_DRAFT_LEDGER_NOT_CANDIDATE_READY_RECEIPT','source_head':VERSION,'source_tree':TREE,'schema_version':'candidate-coverage-1','formal_dispatch':'HOLD_PENDING_SCOPED_REVIEW','files':[dict(path=p,**files[p]) for p in paths],'shards':output_manifest,
 'counts':{'topics':648,'modules':26,'claim_records':1743,'active_claim_candidates':1740,'historical_superseded':3,'sources':455,'source_leads':45,'original_cases':648,'semantic_relation_candidates':20,'views':27,'view_requirements':dict(Counter(q['status'] for q in allmap)),'cq':26,'lc':12,'citation_locator_states':dict(locator_counts),'claim_evidence_states_all':dict(claim_states),'claim_evidence_states_active':dict(active_states),'no_source':dict(no_source),'case_binding_counts':dict(case_counts),'view_binding_counts':dict(binding_counts),'exact_numeric_case_ref_count':num_count,'exact_numeric_saved_result_count':num_results,'formal_qualified':0},
 'pointer_contract':'[file_index, JSON pointer] uses zero-based files index, original path and SHA256/Git blob. Embedded relation/binding/disposition historical paths remain as labeled path references where not a two-element pointer. No inference of provenance or applicable view from thematic proximity.',
 'limits':['Readiness preparation only. No independent S01/G01 qualification, no professional adequacy, no scope omission or NA acceptance, no official task consumption receipts.','Source-level locator is distinct from claim locator; citation not evidence support. Rights HOLD. Historical snapshots preserved; active excludes only three explicitly superseded candidates. Existing references to superseded claims remain historical, no automatic rebinding.','Only exact numeric case-ID matches in original arithmetic evidence bound; other old synthetic checks remain unbound for claim-level purposes. Inline examples and case refs not validation. No learner data, persistent SQLite or published private source.']}
save('ledger-manifest.json',manifest)
print(json.dumps({'counts':manifest['counts'],'shards':output_manifest,'input_files':len(paths)},ensure_ascii=False))

# Compact on-disk ledger uses fixed named columns to avoid reprinting 1,743
# identical field keys. The conversion is lossless and checked on every row.
topic_columns=list(topic_rows[0])
claim_columns=list(topic_rows[0]['claims'][0])
assert all(list(t)==topic_columns and all(list(c)==claim_columns for c in t['claims']) for t in topic_rows)
def pack_topic(t):
    t=remap(t)
    return [[list(c.values()) for c in t[k]] if k=='claims' else t[k] for k in topic_columns]
def unpack_topic(t):
    d=dict(zip(topic_columns,t,strict=True))
    d['claims']=[dict(zip(claim_columns,c,strict=True)) for c in d['claims']]
    return d
for t in topic_rows:assert unpack_topic(pack_topic(t))==remap(t)
# All groups are balanced by existing module ordering; split by two modules.
for old in output_manifest:(OUT/old['file']).unlink()
output_manifest=[]
for group in [mods[i:i+2] for i in range(0,len(mods),2)]:
    name='coverage-'+group[0]+'-'+group[-1]+'.jsonl'
    selected=[t for t in topic_rows if t['owner'] in group]
    (OUT/name).write_text(''.join(json.dumps(pack_topic(t),ensure_ascii=False,separators=(',',':'))+'\n' for t in selected),encoding='utf-8')
    raw=(OUT/name).read_bytes()
    assert [unpack_topic(json.loads(line,object_pairs_hook=unique_pairs)) for line in raw.decode().splitlines()]==[remap(t) for t in selected]
    output_manifest.append({'file':name,'topics':len(selected),'claims':sum(len(t['claims']) for t in selected),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
manifest['shards']=output_manifest
manifest['topic_columns']=topic_columns
manifest['claim_columns']=claim_columns
manifest['citation_columns']=['source_id','source_record_pointer','claim_locator_field','location_status','recorded_source_access','publication_status']
manifest['binding_columns']=['view_id','file_path','json_pointer']
manifest['row_encoding']='JSONL one D3 per line; fixed arrays with named columns; claims nested fixed arrays, source_refs and explicit_view_bindings use separate named columns; lossless to original derived objects; primary knowledge remains in original files.'
vp=(OUT/'views-cq-relations.json').read_bytes()
manifest['views_cq_relations']={'file':'views-cq-relations.json','bytes':len(vp),'sha256':hashlib.sha256(vp).hexdigest()}
save('ledger-manifest.json',manifest)
print(json.dumps({'compact_shards':output_manifest,'lossless_topic_roundtrip':648,'lossless_claim_roundtrip':1743},ensure_ascii=False))
