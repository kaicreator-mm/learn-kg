#!/usr/bin/env python3
"""Materialize immutable R2 candidate packages. No source or professional qualification."""
import copy, hashlib, json, pathlib, collections
import jsonschema
P=pathlib.Path(__file__).resolve().parent
ROOT=P.parents[2]
OLD=P.parent/'foundation'
V0='0.1.0-foundation-candidate-1'
V='0.1.0-foundation-candidate-2'
REVIEW='https://github.com/kaicreator-mm/learn-kg/issues/6#issuecomment-7213482417'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
def rows(name,n):
    result=[l.split('|') for l in (P/name).read_text().splitlines() if l and not l.startswith('#')]
    assert all(len(r)==n for r in result),(name,[(len(r),r[0]) for r in result if len(r)!=n])
    return result
def prov(name,pointer,status):
    f=P/name
    return dict(source_path=str(f.relative_to(ROOT)),source_sha256=sha(f),json_pointer=pointer,source_status=status)
def ref(x):
    return dict(kind=x['kind'],owner=x['owner'],stable_id=x['stable_id'],package_id='evidence' if x['kind']=='Source' else 'learning-core',version=V)
def common(kind,id,owner,conditions,boundary,provenance):
    return dict(kind=kind,stable_id=id,owner=owner,status='CANDIDATE',conditions=conditions,negative_boundary=boundary,provenance=provenance)
def reversion(x):
    if isinstance(x,dict):
        if 'version' in x and 'package_id' in x and 'stable_id' in x:
            assert x['version']==V0
            x['version']=V
        for v in x.values():reversion(v)
    elif isinstance(x,list):
        for v in x:reversion(v)
records={}
old_manifests={}
for pkg in ('evidence','learning-core'):
    m=read(OLD/(pkg+'.manifest.json'));old_manifests[pkg]=m
    assert m['version']==V0
    for f in m['files']:
        p=OLD/f['path'];assert sha(p)==f['sha256']
        rr=[json.loads(l) for l in p.read_text().splitlines()]
        assert len(rr)==f['record_count']
        for x in rr:
            assert x['stable_id'] not in records
            reversion(x);records[x['stable_id']]=x
assert len(records)==1427
def add(x):
    assert x['stable_id'] not in records,x['stable_id']
    records[x['stable_id']]=x
    return x
source_map={}
for cid,sid,mode,loc,note in rows('source-bindings.tsv',5):
    assert (cid,sid) not in source_map
    source_map[cid,sid]=(mode,loc,note)
missing={(x['stable_id'].split(':')[0],x['source_ref']['stable_id']) for x in records.values() if x['kind']=='Locator' and x['attribution'] in ('MISSING','MULTI_SOURCE_HOLD')}
assert missing==set(source_map),(missing-set(source_map),set(source_map)-missing)
mode_meaning={'C':'BUILDER_BODY_SECTION_CORROBORATION_ONLY','I':'PRIOR_KR01_INDEPENDENT_SOURCE_CORROBORATION_ONLY','H':'HISTORICAL_LOCATED_EVIDENCE_NOT_NEWLY_REVERIFIED','A':'ABSTRACT_LIMITED_NOT_FULL_CLAIM_SUPPORT','U':'UNAVAILABLE_HOLD'}
support=[]
for x in sorted(records.values(),key=lambda x:x['stable_id']):
    if x['kind']!='Locator':continue
    cid=x['stable_id'].split(':')[0];sid=x['source_ref']['stable_id'];s=records[sid];c=records[cid]
    prior=x['attribution'];oldloc=x['location']
    if (cid,sid) in source_map:
        mode,loc,note=source_map[cid,sid]
    elif prior=='VERIFIED':
        mode='I';loc=oldloc;note='KR01正文独立佐证该有限命题范围；只继承其明确核对结论，不作专业资格或出版许可。'
    elif sid=='K01-S30' or (cid=='K03.06.03.D4.05' and sid=='K03-B05-KLI'):
        mode='I';loc=oldloc;note='KR01另核对源公式/假设及有限数学推导；不证明个体或实证效果。'
    else:
        mode='A' if s['access'] in ('ABSTRACT_ONLY','ABSTRACT_READ') else 'H'
        loc=oldloc
        note='原命题级定位及原记录条件与反例保留；按历史访问范围支持候选审查，不冒充本轮新读或独立资格。'
    assert loc or mode=='U',(cid,sid)
    d=dict(claim_id=cid,source_id=sid,source_url=s['identifier'],evidence_kind=c['claim_type'],source_access=s['access'],prior_attribution=prior,prior_location=oldloc,location=loc,mode=mode,disposition=mode_meaning[mode],support_and_limits=note,review_evidence=REVIEW if mode=='I' else None)
    support.append(d)
    x['location']=loc;x['attribution']='VERIFIED' if mode in ('C','I') else 'MISSING' if mode=='U' else 'RECORDED_NOT_REVERIFIED'
    x['verification']=mode_meaning[mode]
    if mode=='U':x['status']='HOLD'
write(P/'source-support.json',support)
for i,d in enumerate(support):
    x=records[d['claim_id']+':'+d['source_id']]
    x['provenance'].append(prov('source-support.json','/'+str(i),d['disposition']))
for c in list(records.values()):
    if c['kind']=='Claim' and c['locator_refs'] and all(records[r['stable_id']]['status']=='HOLD' for r in c['locator_refs']):
        c['status']='HOLD';c['source_status']='OPTIONAL_UNAVAILABLE_SOURCE_HOLD'
# one new feature demonstration source, not primary experiment
source_info=[dict(stable_id='K02-R2-S01',url='https://cdn.sinauer.com/wolfe4e/wa04.02.html',title='Wolfe et al., Sensation & Perception, feature detectors web activity',locator='Feature detectors and classification lines64–85',basis='BUILDER_BODY_SECTION_CORROBORATION_ONLY')]
write(P/'new-sources.json',source_info)
for i,s in enumerate(source_info):
    add(common('Source',s['stable_id'],'EVIDENCE',['教材演示；仅特征模型范围。'],'不以教材示例证明全部知觉理论。',[prov('new-sources.json','/'+str(i),'AUTHOR_LOCATED_SOURCE')])|dict(access='HTML_TEXT_READ',bibliography=s['title'],title=s['title'],identifier=s['url'],qualification='NOT_RUN',rights='HOLD',recorded_locator=s['locator'],recorded_rights='ORIGINAL_SUMMARY_ONLY_PUBLICATION_QUALIFICATION_PENDING'))
depth=[]
for topic,sid,loc,typ,statement,cond,bound,inp,expect in rows('depth.tsv',9):
    cid=topic+'.R2.01';assert cid not in records
    depth.append(dict(claim_id=cid,topic_id=topic,source_id=sid,location=loc,claim_type=typ,statement=statement,conditions=[cond],negative_boundary=bound,input=inp,expected=expect,source_basis='HISTORICAL_MARR_PLUS_CURRENT_CULTURE_AND_REPRESENTATION' if topic=='K01.05.01' else 'BUILDER_LOCATED_BODY_AND_ORIGINAL_BOUNDED_DERIVATION',qualification='NOT_RUN'))
write(P/'depth-additions.json',depth)
for i,d in enumerate(depth):
    cid=d['claim_id'];o=cid[:3];topic=d['topic_id'];sid=d['source_id'];p=prov('depth-additions.json','/'+str(i),'R2_AUTHOR_REMEDIATION')
    sr=records[sid]
    loc=add(common('Locator',cid+':'+sid,o,d['conditions'],d['negative_boundary'],[p])|dict(source_ref=ref(sr),location=d['location'],attribution='RECORDED_NOT_REVERIFIED' if topic=='K01.05.01' else 'VERIFIED',verification=d['source_basis']))
    case=add(common('Case',cid+':case',o,d['conditions'],d['negative_boundary'],[p])|dict(view='COMPOSITION',target_refs=[dict(kind='Claim',owner=o,stable_id=cid,package_id='learning-core',version=V)],input_spec=d['input'],expected_spec=d['expected'],oracle_ref=None,actual_status='NOT_RUN'))
    add(common('Claim',cid,o,d['conditions'],d['negative_boundary'],[p])|dict(topic_id=topic,requirement_id=topic+'.RQ01',claim_type=d['claim_type'],statement=d['statement'],source_status='BODY_LOCATED_OR_BOUNDED_DERIVATION_CANDIDATE',locator_refs=[ref(loc)],case_refs=[ref(case)],validation_refs=[],refinement_of=None,supersedes_refs=[]))
# source-backed auxiliary references for cross-scale and metric derivations
aux=[('K01.05.01.R2.01','K01-S17','NASEM How People Learn II Ch2 dynamic interaction lines190–195','多层文化情境与生物交互；并非Marr三层映射。'),('K01.05.01.R2.01','K01-S11','SEP Mental Representation introduction lines14–18','表征理论构念；行为不能直接识别神经实现为本文方法推论。'),('K04.03.04.R2.01','K04-S01','NRC Ch2 meaningful patterns and conditional knowledge lines54–68','专家识别模式与条件知识；资源分离比较是本文候选诊断设计。'),('K04.01.03.R2.01','K04-S06','MacKenzie effective width lines144–150,239','跨试次散布与测量；本文MAE/极差为明确合成定义。')]
write(P/'aux-source-support.json',[dict(claim_id=c,source_id=s,location=l,support_and_limits=n,qualification='NOT_RUN') for c,s,l,n in aux])
for i,(cid,sid,loc,note) in enumerate(aux):
    c=records[cid]
    x=add(common('Locator',cid+':'+sid,c['owner'],c['conditions'],note,[prov('aux-source-support.json','/'+str(i),'R2_AUTHOR_LOCATOR')])|dict(source_ref=ref(records[sid]),location=loc,attribution='VERIFIED',verification='BUILDER_BODY_OR_PRIOR_KR01_CORROBORATION_ONLY'))
    c['locator_refs'].append(ref(x))
# Explicit four-view transformation semantics; originals unchanged.
transforms=[]
for x in sorted(records.values(),key=lambda x:x['stable_id']):
    if x['kind']!='Case' or not any(p['source_status']=='HISTORICAL_SYNTHETIC_DESIGN' for p in x['provenance']):continue
    old=x['input_spec'];expect=x['expected_spec']
    if x['stable_id']=='K01.01.01.CASE.01:counterexample':
        spec={'mode':'EXPLICIT_TRANSFORMED_FIXTURE','practice_end':[90,75],'delayed':None,'transform':'delete both delayed scores','unit':'percent','synthetic':True}
    else:
        spec={'mode':'NARRATIVE_TRANSFORMATION_DESIGN_NOT_LITERAL_EXECUTION','base_fixture':old,'view':x['view'],'instruction_and_expected':expect}
    transforms.append(dict(case_id=x['stable_id'],old_input=old,new_input=spec,expected=expect,actual_status='NOT_RUN'))
    x['input_spec']=json.dumps(spec,ensure_ascii=False,sort_keys=True)
    assert x['actual_status']=='NOT_RUN'
assert len(transforms)==388,len(transforms)
write(P/'view-transformations.json',transforms)
for i,t in enumerate(transforms):records[t['case_id']]['provenance'].append(prov('view-transformations.json','/'+str(i),'EXPLICIT_VIEW_TRANSFORMATION'))
duplicate_groups=[
    {'claim_ids':['K02.01.02.D4.02','K02.01.02.D4.05'],'disposition':'同一SDT敏感度公式与同文证据，不重复计独立支持。'},
    {'claim_ids':['K02.01.02.D4.03','K02.01.02.D4.06'],'disposition':'同一判准公式与同文证据，不重复计独立支持。'},
    {'claim_ids':['K04.04.04.D4.01','K04.04.04.D4.03'],'disposition':'同一Morris等1977摘要交叉结果，不重复计独立证据。'}]
for g in duplicate_groups:assert all(c in records for c in g['claim_ids'])
write(P/'duplicate-dispositions.json',duplicate_groups)
for i,g in enumerate(duplicate_groups):
    a,b=g['claim_ids']
    records[b]['refinement_of']=ref(records[a])
    records[b]['provenance'].append(prov('duplicate-dispositions.json','/'+str(i),'SAME_WORK_NOT_INDEPENDENT_CORROBORATION'))
# Local relation semantics extension, no changes to IF01; not a general engine rule.
iface=ROOT/'docs/implementation/if01/interface-contract.json'
ext={'version':'foundation-r2-local-relations-1','base_if01_sha256':sha(iface),'status':'CANDIDATE_NOT_QUALIFIED','types':{
'contrasted_with':{'endpoints':['Element','Element'],'meaning':'对照构念或模型，按具体条件区别；不推出互斥/反向或等价'},
'joint_evidence_with':{'endpoints':['Element','Element'],'meaning':'组合判断要求保留两项证据，未知不得用单项填补'},
'limits_inference_to':{'endpoints':['Element','Element'],'meaning':'约束从首端证据到末端结论的推断，不是因果或蕴涵'}},'automatic_inverse':False,'automatic_transitive':False}
write(P/'relation-types.json',ext)
rels=[]
for aid,a,b,typ,cond,negative,inp,expect in rows('relations.tsv',8):
    assert typ in ext['types'] and a in records and b in records and a!=b,(aid,a,b)
    rels.append(dict(anchor_id=aid,from_claim=a,to_claim=b,relation_type=typ,conditions=[cond],negative_boundary=negative,input=inp,expected=expect,qualification='NOT_RUN'))
write(P/'relation-design.json',rels)
for i,d in enumerate(rels):
    p=prov('relation-design.json','/'+str(i),'R2_BOUNDED_RELATION_DESIGN')
    a,b=[records[d[k]] for k in ('from_claim','to_claim')]
    def elem(c):
        id=c['stable_id']+':R2:construct'
        if id not in records:
            add(common('Element',id,c['owner'],c['conditions'],c['negative_boundary'],[p])|dict(topic_id=c['topic_id'],element_type='PROFESSIONAL_DISTINCTION_CONSTRUCT',label=c['topic_id']+' '+c['stable_id'],definition=c['statement'],claim_refs=[ref(c)]))
        return records[id]
    o=d['anchor_id'][:3]; rid=d['anchor_id']+':R2:relation'
    r=add(common('Relation',rid,o,d['conditions'],d['negative_boundary'],[p])|dict(relation_type=d['relation_type'],from_ref=ref(elem(a)),to_ref=ref(elem(b)),claim_refs=[ref(a),ref(b)],condition_refs=[],direction='DIRECTED',automatic_inverse=False,automatic_transitive=False))
    case=add(common('Case',rid+':case',o,d['conditions'],d['negative_boundary'],[p])|dict(view='COMPOSITION',target_refs=[ref(r),ref(a),ref(b)],input_spec=d['input'],expected_spec=d['expected'],oracle_ref=None,actual_status='NOT_RUN'))
    for c in (a,b):c['case_refs'].append(ref(case))
# Each original anchor accounted for, foreign modules never implicitly qualified.
dispositions=[];selected={d['anchor_id']:d for d in rels};hold_reasons=read(P/'anchor-holds.json')
for o in ('K01','K02','K03','K04'):
    f=ROOT/'docs/drafts/s01'/o/('theory-comparison.json' if o=='K01' else 'cross-topic-links.json')
    for i,a in enumerate(read(f)['records']):
        aid=a['id']
        if aid in selected:
            d=selected[aid];status='TYPED_CONDITIONAL_CANDIDATE';reason='见明确双命题端点、条件、反例与组合案例；未独立资格。';rid=aid+':R2:relation'
        else:
            endpoints=[a.get(k,'') for k in ('from','to','from_d3','to_d3')]
            foreign=any(e.startswith('K') and e[:3] not in ('K01','K02','K03','K04') for e in endpoints)
            status='FOREIGN_MODULE_PENDING' if foreign else 'OPTIONAL_RESEARCH_ANCHOR_HOLD'
            reason=hold_reasons[aid]
            rid=None
        dispositions.append(dict(anchor_id=aid,source_path=str(f.relative_to(ROOT)),source_sha256=sha(f),json_pointer='/records/'+str(i),status=status,reason=reason,relation_id=rid))
assert len(dispositions)==43 and len({d['anchor_id'] for d in dispositions})==43
assert set(hold_reasons)=={d['anchor_id'] for d in dispositions if d['relation_id'] is None}
write(P/'anchor-dispositions.json',dispositions)
# R2 actual finite execution refs, old independent judgement remains separate.
oracles=read(P/'new-oracles.json');results=read(P/'oracle-results.json')
result_by_id={r['id']:(i,r) for i,r in enumerate(results['results'])}
assert results['prior_regression']==20 and results['new_cases']==len(oracles)
for i,c in enumerate(oracles):
    cl=records[c['claim']];o=cl['owner'];id=c['id'];vid=id+':validation';idx,res=result_by_id[id]
    p=prov('new-oracles.json','/'+str(i),'AUTHOR_FROZEN_EXPECTATION')
    r=add(common('Case',id,o,['有限合成输入；条件以明确算例为准。'],'实际结果仅为有限计算，不是教育效果。',[p])|dict(view='COMPOSITION',target_refs=[ref(cl)],input_spec=json.dumps(c['input'],ensure_ascii=False,sort_keys=True),expected_spec=json.dumps(c['expected'],ensure_ascii=False),oracle_ref=dict(kind='Validation',owner=o,stable_id=vid,package_id='learning-core',version=V),actual_status='RECORDED_BUILDER_ONLY'))
    v=add(common('Validation',vid,o,r['conditions'],r['negative_boundary'],[p,prov('oracle-results.json','/results/'+str(idx),'ACTUAL_BUILDER_RESULT')])|dict(case_refs=[ref(r)],target_refs=[ref(cl)],method='R2有限合成参数域与推理输出核验',input_digest=digest(c['input']),oracle_identity='author-frozen:'+sha(P/'new-oracles.json'),result_digest=digest(res),run_status='BUILDER_RUN'))
    cl['case_refs'].append(ref(r));cl['validation_refs'].append(ref(v))
for x in records.values():
    if x['kind']!='ModelSpec':continue
    for p in x['parameters']:
        if x['owner']=='K01' or x['owner']=='K03' or (x['owner']=='K04' and p['name'] in ('r','k')):
            p['lower']=0;p['upper']=1
        if x['owner']=='K02':p['lower']=0
# A complete topic/claim support ledger. Not a professional verdict.
claim_ledger=[]; by_topic=collections.defaultdict(list)
for c in sorted(records.values(),key=lambda x:x['stable_id']):
    if c['kind']!='Claim':continue
    ls=[records[r['stable_id']] for r in c['locator_refs']]
    if not ls:
        disp='PROJECT_POLICY_NO_EMPIRICAL_SOURCE' if c['claim_type']=='ENGINEERING_POLICY' else 'ORIGINAL_LOGICAL_DERIVATION_NO_EMPIRICAL_SOURCE'
    elif c['status']=='HOLD':disp='OPTIONAL_UNAVAILABLE_HOLD'
    else:disp='LOCATED_CANDIDATE_NOT_QUALIFIED'
    d=dict(claim_id=c['stable_id'],topic_id=c['topic_id'],claim_type=c['claim_type'],disposition=disp,locator_ids=[x['stable_id'] for x in ls],source_states=[x['verification'] for x in ls],condition_count=len(c['conditions']),negative_boundary_present=bool(c['negative_boundary']),case_ids=[x['stable_id'] for x in c['case_refs']],qualification='NOT_RUN')
    claim_ledger.append(d);by_topic[c['topic_id']].append(d)
write(P/'claim-support-ledger.json',claim_ledger)
# Validate schema, all reference endpoints and source JSON pointers. No qualification.
schema=read(ROOT/'docs/implementation/db01/canonical.schema.json')
validator=jsonschema.Draft202012Validator(schema)
interface=read(iface)
def pointer(obj,path):
    for k in path.split('/')[1:]:
        k=k.replace('~1','/').replace('~0','~')
        obj=obj[int(k)] if isinstance(obj,list) else obj[k]
    return obj
def refs_at(o,path):
    if not path:return [o]
    if path[0]=='*':return [r for item in o for r in refs_at(item,path[1:])] if isinstance(o,list) else []
    if not isinstance(o,dict) or path[0] not in o:return []
    return refs_at(o[path[0]],path[1:])
cache={};refs_count=0;prov_count=0
for x in records.values():
    validator.validate(x)
    for path,kinds in interface['endpoint_rules'].get(x['kind'],{}).items():
        for r in refs_at(x,path.split('/')):
            if r is None:continue
            t=records[r['stable_id']];assert r==ref(t) and t['kind'] in kinds,(x['stable_id'],path,r,kinds)
            refs_count+=1
    if x['kind']=='Relation':
        endpoints=[x['from_ref']['kind'],x['to_ref']['kind']]
        allowed=interface['relation_endpoints'].get(x['relation_type'])
        if allowed is None:allowed=[ext['types'][x['relation_type']]['endpoints']]
        assert endpoints in allowed and not x['automatic_inverse'] and not x['automatic_transitive'],x['stable_id']
    for p in x['provenance']:
        f=ROOT/p['source_path'];assert sha(f)==p['source_sha256'],(x['stable_id'],p)
        if f not in cache:cache[f]=read(f)
        pointer(cache[f],p['json_pointer']);prov_count+=1
# Persist deterministic full revised human-readable JSONL, each record once.
def shard(owner,rr):
    d=P/owner;d.mkdir(exist_ok=True)
    for f in d.glob('records-*.jsonl'):f.unlink()
    files=[];buf=[];size=0
    def flush():
        if not buf:return
        f=d/('records-%02d.jsonl'%len(files));f.write_text(''.join(buf))
        files.append(dict(path=str(f.relative_to(P)),sha256=sha(f),format='JSONL_RECORDS',record_count=len(buf)))
    for x in sorted(rr,key=lambda x:(x['kind'],x['stable_id'])):
        l=json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n'
        if size+len(l.encode())>76000 and buf:
            flush();buf=[];size=0
        buf.append(l);size+=len(l.encode())
    flush();return files
ef=shard('evidence',[x for x in records.values() if x['kind']=='Source'])
em=copy.deepcopy(old_manifests['evidence']);em.update(version=V,files=ef)
write(P/'evidence.manifest.json',em)
all_files=[];coverage_counts={}
for o in ('K01','K02','K03','K04'):
    rr=[x for x in records.values() if x['owner']==o];ff=shard(o,rr);all_files+=ff
    cv=read(OLD/o/'coverage.json')
    for t in cv['topics']:
        topic=t['d3_id'];cs=by_topic[topic];assert cs
        active=[x for x in cs if x['disposition']!='OPTIONAL_UNAVAILABLE_HOLD']
        professional=[x for x in active if x['disposition']!='PROJECT_POLICY_NO_EMPIRICAL_SOURCE']
        assert professional,topic
        t['claim_ids']=[x['claim_id'] for x in cs];t['active_claim_ids']=[x['claim_id'] for x in active]
        t['case_ids']=sorted({a for x in cs for a in x['case_ids']})
        t['validation_ids']=sorted({r['stable_id'] for c in cs for r in records[c['claim_id']]['validation_refs']})
        t['current_depth_disposition']='R2_TARGETED_DEPTH_ADDED' if topic+'.R2.01' in records else 'PRESERVED_LOCATED_CANDIDATE_NOT_NEW_ADEQUACY_VERDICT'
        t['source_locator_states']=dict(collections.Counter(records[r]['attribution'] for x in cs for r in x['locator_ids']))
        t['no_source_claim_ids']=[x['claim_id'] for x in cs if not x['locator_ids']]
        t['relation_disposition']='R2 conditional typed relations where selected; see anchor-dispositions.json; no implicit closure.'
        t['source_gap_policy']='See claim-support-ledger and source-support; historical/abstract limited, optional unavailable claim HOLD, no professional qualification.'
        t['qualification']='NOT_RUN'
    cv['record_files']=ff;cv['record_counts']=dict(collections.Counter(x['kind'] for x in rr))
    cv['limits']=['R2 covers eight KR01 finding families for delta review; all professional qualification NOT_RUN.','Historical location and abstract limitations retained; no new source byte verification claimed.','Composition narratives not executed; finite synthetic oracle tests only. Local relation extension not IF01 global qualification.']
    write(P/o/'coverage.json',cv);coverage_counts[o]={'topics':len(cv['topics']),'records':len(rr),'claims':cv['record_counts']['Claim']}
lm=copy.deepcopy(old_manifests['learning-core']);lm.update(version=V,files=all_files,dependencies=[dict(package_id='evidence',version=V,manifest_sha256=sha(P/'evidence.manifest.json'))])
write(P/'learning-core.manifest.json',lm)
assert sum(v['topics'] for v in coverage_counts.values())==97
report=dict(status='BUILDER_VALIDATION_ONLY_NOT_QUALIFIED',base_review=REVIEW,prior_records=1427,records=len(records),claims=len(claim_ledger),source_support_modes=dict(collections.Counter(x['mode'] for x in support)),old_missing_or_multi_rebound=len(source_map),held_claims=[x['claim_id'] for x in claim_ledger if x['disposition']=='OPTIONAL_UNAVAILABLE_HOLD'],new_depth_claims=len(depth),typed_relation_additions=len(rels),old_anchor_count=len(dispositions),anchor_status_counts=dict(collections.Counter(x['status'] for x in dispositions)),view_transformations=len(transforms),prior_oracle_regression=20,new_finite_cases=len(oracles),refs_checked=refs_count,provenance_checked=prov_count,modules=coverage_counts,independent_qualification='NOT_RUN')
write(P/'validation-receipt.json',report)
print(json.dumps(report,ensure_ascii=False))
