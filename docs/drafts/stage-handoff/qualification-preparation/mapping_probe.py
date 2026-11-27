#!/usr/bin/env python3
"""DB01 investigation: static typed reference and pointer mapping witness, not importer."""
from pathlib import Path
import hashlib,json,collections
P=Path(__file__).resolve().parent
ROOT=P.parents[3]
M=json.loads((P/'ledger-manifest.json').read_text())
V=M['source_head']
def check(condition,reason):
    if not condition:raise ValueError(reason)
def sha(b):return hashlib.sha256(b).hexdigest()
def blob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
data=[]
for f in M['files']:
    p=(ROOT/f['path']).resolve()
    check(p.is_relative_to(ROOT) and p.is_file(),'input path')
    raw=p.read_bytes()
    check(sha(raw)==f['sha256'] and blob(raw)==f['git_blob'],'input digest')
    data.append(json.loads(raw))
def resolve_pointer(pointer):
    i,path=pointer
    check(type(i) is int and 0<=i<len(data) and isinstance(path,str) and path.startswith('/'),'pointer shape')
    d=data[i]
    for part in path[1:].split('/'):
        part=part.replace('~1','/').replace('~0','~')
        d=d[int(part)] if isinstance(d,list) else d[part]
    return d
def ref(package,kind,stable_id):return (package,V,kind,stable_id)
def owner_pkg(owner):return 'learning-core' if owner.startswith('K') else 'chinese'
registry={}
edges=[]
history=set()
def insert(key,pointer):
    check(key not in registry,'duplicate '+str(key))
    registry[key]=pointer
deps={'evidence':set(),'learning-core':{'evidence'},'chinese':{'evidence'},'learning-process':{'learning-core','chinese'},'research-overlay':{'learning-core','chinese','learning-process'}}
allowed={'HAS_REQUIREMENT':('TOPIC','REQUIREMENT'),'HAS_CLAIM':('TOPIC','CLAIM'),'RECORDED_REFINEMENT':('CLAIM','CLAIM'),'CITES_RECORDED_SOURCE':('CLAIM','SOURCE_RECORD'),'HAS_LOCATOR':('CLAIM','LOCATOR'),'LOCATES_SOURCE':('LOCATOR','SOURCE_RECORD'),'HAS_CASE_CANDIDATE':('CLAIM','CASE'),'BINDS_CLAIM_CANDIDATE':('VIEW','CLAIM'),'HAS_VIEW_REQUIREMENT':('VIEW','VIEW_REQUIREMENT'),'SEMANTIC_FROM':('RELATION','TOPIC'),'SEMANTIC_TO':('RELATION','TOPIC'),'SEMANTIC_CLAIM_CANDIDATE':('RELATION','CLAIM'),'HAS_VALIDATION_DESIGN':('CLAIM','VALIDATION_DESIGN'),'SUPERSESSION_CANDIDATE':('CLAIM','CLAIM')}
def add(typ,a,b):edges.append((typ,a,b))
topics={};claims={};cases={};reqs={};srcs={};source_ptrs={};numerical={};view_refs={}
for i,f in enumerate(M['files']):
    if f['path'].endswith('/sources.json'):
        for j,s in enumerate(data[i].get('sources',[])):
            if not isinstance(s,dict) or 'id' not in s:continue
            k=ref('evidence','SOURCE_RECORD',s['id'])
            insert(k,[i,'/sources/'+str(j)])
            srcs[s['id']]=k
    if f['path'].endswith('/cases.json') and '/depth/' not in f['path']:
        for j,c in enumerate(data[i].get('records',[])):
            k=ref(owner_pkg(c['owner']),'CASE',c['id'])
            insert(k,[i,'/records/'+str(j)])
            cases[c['id']]=k
            check(c['validation']=='NOT_RUN','case status')
check(len(srcs)==455 and len(cases)==648,'source or case inventory')
all_rows=[]
for sh in M['shards']:
    raw=(P/sh['file']).read_bytes()
    check(sha(raw)==sh['sha256'] and len(raw)==sh['bytes'],'shard digest')
    tcount=ccount=0
    for line in raw.decode().splitlines():
        t=dict(zip(M['topic_columns'],json.loads(line),strict=True))
        t['claims']=[dict(zip(M['claim_columns'],c,strict=True)) for c in t['claims']]
        all_rows.append(t);tcount+=1;ccount+=len(t['claims'])
    check((tcount,ccount)==(sh['topics'],sh['claims']),'shard count')
for t in all_rows:
    pkg=owner_pkg(t['owner']);tid=t['d3_id'];r=t['requirement_id']
    rr=resolve_pointer(t['requirement_ref']);cc=resolve_pointer(t['original_coverage_ref'])
    check(rr['d3_id']==tid==cc['d3_id'] and rr['requirement_id']==r==cc['requirement_id'],'topic/requirement pointer')
    k=ref(pkg,'TOPIC',tid);q=ref(pkg,'REQUIREMENT',r);insert(k,t['original_coverage_ref']);insert(q,t['requirement_ref']);topics[tid]=k;reqs[r]=q
    add('HAS_REQUIREMENT',k,q)
    for c in t['claims']:
        x=resolve_pointer(c['record']);cid=c['id']
        check(x['stable_id']==cid and x['d3_id']==tid and x['owner']==t['owner'] and x['requirement_id']==r and x['claim_type']==c['claim_type'] and x['evidence_status']==c['source_status'],'claim pointer')
        check(x['conditions'] and x['negative_boundary'] and x['qualification']=='NOT_RUN' and c['qualification_receipt'] is None and c['consumed_tuple'] is None,'qualification boundary')
        a=ref(pkg,'CLAIM',cid);insert(a,c['record']);claims[cid]=a
        if c['status']=='HISTORICAL_SUPERSEDED_CANDIDATE':history.add(a)
        add('HAS_CLAIM',k,a)
for t in all_rows:
    for c in t['claims']:
        a=claims[c['id']];x=resolve_pointer(c['record'])
        if c['parent_candidate']:add('RECORDED_REFINEMENT',a,claims[c['parent_candidate']])
        for old in c['replacement_claim_refs']:add('SUPERSESSION_CANDIDATE',a,claims[old])
        check([r[0] for r in c['source_refs']]==x['source_refs'],'citation list')
        for s,sp,field,status,access,rights in c['source_refs']:
            source=resolve_pointer(sp)
            check(source['id']==s and source['access']==access and rights=='HOLD_PUBLICATION_QUALIFICATION','source provenance')
            expected='HOLD_CLAIM_LOCATOR_MISSING' if not field else ('RECORDED_CLAIM_LOCATOR_NOT_REVERIFIED' if len(x['source_refs'])==1 else 'HOLD_MULTI_SOURCE_ATTRIBUTION')
            check(status==expected and (field is None or bool(x[field])),'locator status')
            locator=ref(a[0],'LOCATOR',c['id']+':'+s)
            insert(locator,{'claim':c['record'],'source':sp,'claim_locator_field':field})
            add('CITES_RECORDED_SOURCE',a,srcs[s]);add('HAS_LOCATOR',a,locator);add('LOCATES_SOURCE',locator,srcs[s])
        for caseid in c['case_refs']:
            case=resolve_pointer(registry[cases[caseid]])
            check(c['id'] in case['claim_refs'],'case scope')
            add('HAS_CASE_CANDIDATE',a,cases[caseid])
        for n in c['validation_refs']:
            case=resolve_pointer(n['case_pointer'])
            check(case['id']==n['case_id'] and case['claim_ref']==c['id'],'validation scope')
            if n['result_pointer']:check(resolve_pointer(n['result_pointer'])['id']==n['case_id'],'saved result ID')
            val=ref(a[0],'VALIDATION_DESIGN',n['case_id']);insert(val,n)
            add('HAS_VALIDATION_DESIGN',a,val)
        for k,path,pointer in c['explicit_view_bindings']:
            fidx=next(i for i,f in enumerate(M['files']) if f['path']==path)
            b=resolve_pointer([fidx,pointer]);check(b['claim_id']==c['id'],'explicit binding')
            add('BINDS_CLAIM_CANDIDATE',ref('learning-process','VIEW',k),a)
b=(P/'views-cq-relations.json').read_bytes()
check(sha(b)==M['views_cq_relations']['sha256'],'views file hash')
v=json.loads(b)
for view in v['views']:
    k=ref('learning-process','VIEW',view['id']);insert(k,view['contract_ref']);view_refs[view['id']]=k
    check(resolve_pointer(view['contract_ref'])['task_id']==view['id'],'view binding')
    for rq in view['requirements']:
        q=ref('learning-process','VIEW_REQUIREMENT',rq['id']);insert(q,rq['map_record'])
        check(resolve_pointer(rq['map_record'])['requirement_id']==rq['id'] and rq['formal_receipt'] is None,'view requirement')
        add('HAS_VIEW_REQUIREMENT',k,q)
for r in v['relations']:
    original=resolve_pointer(r['pointer'])
    check(original['id']==r['id'] and original['from']==r['from'] and original['to']==r['to'] and original['claim_refs']==r['claim_refs'] and original['materialize_accepted'] is False,'relation pointer')
    k=ref('research-overlay','RELATION',r['id']);insert(k,r['pointer'])
    add('SEMANTIC_FROM',k,topics[r['from']]);add('SEMANTIC_TO',k,topics[r['to']])
    for a in r['claim_refs']:add('SEMANTIC_CLAIM_CANDIDATE',k,claims[a])
def resolve(key,origin,mode='RESEARCH_READ'):
    check(isinstance(key,tuple) and len(key)==4 and all(isinstance(x,str) and x for x in key),'reference shape')
    pkg,ver,kind,sid=key
    check(ver==V,'version')
    check(origin in deps and pkg in deps,'unknown/private/learner package')
    check(pkg==origin or pkg in deps[origin],'undeclared direct dependency')
    check(key in registry,'missing or wrong type')
    check(mode=='RESEARCH_READ','no release qualification')
    return 'HISTORICAL_ONLY' if key in history else 'RESEARCH_CANDIDATE_ONLY'
def validate_edge(typ,a,b):
    check(typ in allowed and (a[2],b[2])==allowed[typ],'edge type')
    resolve(a,a[0]);return resolve(b,a[0])
edgecounts=collections.Counter()
historical_edges=0
for typ,a,b in edges:
    if validate_edge(typ,a,b)=='HISTORICAL_ONLY' or a in history:historical_edges+=1
    edgecounts[typ]+=1
check(len(set(edges))==len(edges),'duplicate edges')
check(len(topics)==648 and len(claims)==1743 and len(history)==3 and len(view_refs)==27,'inventory mismatch')
# Explicit rejection checks. No authorization service; mode denotes static use class only.
sample=next(iter(claims.values()))
source=next(iter(srcs.values()))
negative=[]
def reject(name,fn):
    try:fn()
    except (ValueError,KeyError,IndexError,TypeError):negative.append(name)
    else:raise RuntimeError('unexpected acceptance '+name)
reject('stale_version',lambda:resolve((sample[0],'old',sample[2],sample[3]),sample[0]))
reject('unknown_id',lambda:resolve(ref(sample[0],'CLAIM','missing'),sample[0]))
reject('wrong_kind',lambda:resolve(ref(sample[0],'SOURCE_RECORD',sample[3]),sample[0]))
reject('undeclared_dependency',lambda:resolve(sample,'evidence'))
reject('no_transitive_dependency',lambda:resolve(source,'learning-process'))
reject('unknown_private_source_package',lambda:resolve(ref('private-hsk-staging','SOURCE_RECORD','x'),'chinese'))
reject('learner_not_knowledge',lambda:resolve(ref('learner','STATE','x'),'learning-core'))
reject('release_denied',lambda:resolve(sample,sample[0],'PUBLICATION'))
reject('wrong_edge_type',lambda:validate_edge('HAS_CLAIM',sample,source))
reject('unknown_relation',lambda:validate_edge('IS_CAUSE',sample,source))
reject('wrong_pointer_index',lambda:resolve_pointer([-1,'/records/0']))
for q in v['cq']:check(q['status']=='NOT_RUN' and q['actual_result'] is None and q['review_receipt'] is None,'formal CQ')
receipt={'status':'DB01_STATIC_MAPPING_INVESTIGATION_ONLY','source_head':V,'source_tree':M['source_tree'],'input_file_hashes_checked':len(M['files']),'shards_checked':len(M['shards']),'registry_by_kind':dict(collections.Counter(k[2] for k in registry)),'registry_by_package':dict(collections.Counter(k[0] for k in registry)),'edge_counts':dict(edgecounts),'edge_count':len(edges),'historical_edge_occurrences':historical_edges,'negative_rejected':negative,'negative_count':len(negative),'formal_receipts':0,'sqlite_generated':False,'limits':['Static in-memory Python reference mapping, not DB02 or SQLite. Version pins exact candidate snapshot; package digest/authorized manifest resolver is design only. RESEARCH_READ is a use class not actual authentication. Every source is candidate only; no publication authorization.','Original scope coverage pointers retained; no promotion of semantic relations, inferred applicability, replacement IDs, model evidence, or CQ.']}
(P/'mapping-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
print(json.dumps(receipt,ensure_ascii=False))
