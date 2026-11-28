#!/usr/bin/env python3
"""Canonical restricted professional candidate plus retained historical research HOLDs."""
from pathlib import Path
import collections,json,hashlib,sys,re
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];sys.path.insert(0,str(ROOT))
from tools.knowledge_import.importer import Importer,ManifestPin
from semantic_rules import evaluate
D=ROOT/'docs/drafts/s01';PKG=ROOT/'knowledge/v0.1.0/chinese-h01-h04-r1';V='0.1.0-chinese-h01-h04-candidate-1'
OWNERS=['H01','H02','H03','H04']
def load(p):return json.loads(p.read_text())
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dig(x):return hashlib.sha256(canonical(x).encode()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
def provenance(p,ptr,status):return dict(source_path=p.relative_to(ROOT).as_posix(),source_sha256=sha(p),json_pointer=ptr,source_status=status)
def ref(o,k,i):return dict(package_id='evidence' if k=='Source' else 'chinese',version=V,stable_id=i,kind=k,owner=o)
def base(o,k,i,pr,status='HOLD',conditions=None,negative=None):return dict(owner=o,kind=k,stable_id=i,status=status,conditions=conditions or ['限定所记录来源与候选用途；未建立专业资格。'],negative_boundary=negative or '不得据此推断真实学习效果、标准身份或发布授权。',provenance=[pr])
def main():
 design=load(HERE/'professional-design.json');dag=load(ROOT/'docs/implementation/task-dag.json');tasks={t['id']:t for t in dag['tasks']}
 e=ROOT/'evidence/tasks/HSK01/HSK01-FORMAL-01.json';hs=load(e);assert hs['validation']['independent_result']=='ACCEPT_SCOPED'
 records={};srcs={};cov={};tests=[];inputs={}
 taxpath=ROOT/'docs/product/system/hsk-taxonomy.md';tax=[]
 for line in taxpath.read_text().splitlines():
  m=re.fullmatch(r'(?:## |### |- )(H[0-9]{2}(?:[.][0-9]{2}){0,2}) (.+)',line)
  if m and m[1].split('.')[0] in OWNERS:tax.append({'id':m[1],'label':m[2],'depth':m[1].count('.')+1})
 taxfile=HERE/'taxonomy-index.json';write(taxfile,dict(source_path=taxpath.relative_to(ROOT).as_posix(),source_sha256=sha(taxpath),records=tax))
 taxby={r['id']:(n,r) for n,r in enumerate(tax)}

 def add(r):
  assert r['stable_id'] not in records,r['stable_id'];records[r['stable_id']]=r;return ref(r['owner'],r['kind'],r['stable_id'])
 def source(o,s,p,ptr,checked=False):
  sid=s['id'];assert sid not in srcs
  i='SRC.'+sid
  x=base('EVIDENCE','Source',i,provenance(p,ptr,'TEXT_RECHECKED_20261128' if checked else 'HISTORICAL_SOURCE_METADATA_ONLY'))
  x.update(title=s['title'],identifier=s['url'],access='TEXT_RECHECKED_LIMITED' if checked else s.get('access','HISTORICAL_NOT_RECHECKED'),rights='HOLD',qualification='NOT_RUN',bibliography=s['title']+'; '+s['url'],recorded_locator=s.get('locator'),recorded_rights='ORIGINAL_SUMMARY_ONLY; rights/publication not qualified')
  srcs[sid]=(add(x),s,checked)
 def loc(o,cid,sid,pr,locator=None):
  sr,s,checked=srcs[sid];i=cid+'.LOC.'+sid
  return add(base(o,'Locator',i,pr,negative='Recorded location supports only the stated limited claim; not independent source qualification.')|dict(source_ref=sr,location=locator or s.get('locator'),attribution='VERIFIED' if checked else 'RECORDED_NOT_REVERIFIED',verification='2026-11-28 text rechecked, bounded paraphrase; no full source/rights qualification' if checked else 'Historical author source trace; current exact proposition not rechecked.'))
 for o in OWNERS:
  inputs[o]=[]
  for dep in tasks[o]['depends_on']:
   p=ROOT/tasks[dep]['current_receipt'];r=load(p)
   inputs[o].append(dict(task_id=dep,receipt_id=r['receipt_id'],content_digest=r['content_digest'],version=r.get('version',r['exact_head']),receipt_path=p.relative_to(ROOT).as_posix(),receipt_sha256=sha(p)))
  p=D/o
  source_files=[p/'sources.json',*sorted((D/'depth/D2').glob('*/'+o+'/sources.json'))]
  for f in source_files:
   for n,s in enumerate(load(f)['sources']):source(o,s,f,'/sources/'+str(n))
  for n,s in enumerate(design['sources']):
   if s['owner']==o:source(o,s,HERE/'professional-design.json','/sources/'+str(n),True)
  coverage=load(p/'coverage.json')['records'];claim_files=[p/'claims.json',*sorted((D/'depth/D2').glob('*/'+o+'/claims.json'))];historical={};topic_refs={}
  for id,(j,t) in taxby.items():
   if id.split('.')[0]!=o or t['depth']==3:continue
   add(base(o,'Topic',id,provenance(taxfile,'/records/'+str(j),'EXACT_PROJECT_TAXONOMY_INDEX'))|dict(label=t['label'],depth=t['depth'],parent_ref=ref(o,'Topic',id.rsplit('.',1)[0]) if t['depth']==2 else None))
  requirement_file=D/(o+'-requirements.json');requirements=load(requirement_file)['records'];requirements_by_id={x['d3_id']:(j,x) for j,x in enumerate(requirements)}
  assert set(requirements_by_id)=={t['d3_id'] for t in coverage}
  for n,t in enumerate(coverage):
   i=t['d3_id'];j,q=requirements_by_id[i];pr=provenance(requirement_file,'/records/'+str(j),'ACCEPTED_SCOPE_RESEARCH_DRAFT')
   assert q['requirement_id']==t['requirement_id'] and q['label']==t['topic'] and taxby[i][1]['label']==t['topic']
   topic_refs[i]=add(base(o,'Topic',i,pr)|dict(label=t['topic'],depth=3,parent_ref=ref(o,'Topic',i.rsplit('.',1)[0])))
   add(base(o,'Requirement',q['requirement_id'],pr,negative=q['negative_boundary'])|dict(topic_ref=topic_refs[i],scope=q['research_requirement'],source_leads=q['source_leads'],coverage_status='RESTRICTED_CANDIDATE_OR_HOLD_SEE_SCOPE_LEDGER'))
  for f in claim_files:
   for n,c in enumerate(load(f)['records']):
    i=c['stable_id'];assert i not in historical,(o,i);historical[i]=c
    pr=provenance(f,'/records/'+str(n),'HISTORICAL_RESEARCH_DRAFT_ONLY')
    l=[loc(o,i,s,pr,c.get('source_locator')) for s in c['source_refs'] if s in srcs]
    assert len(l)==len(c['source_refs']),(o,i,c['source_refs'])
    r=base(o,'Claim',i,pr,conditions=c['conditions'],negative=c['negative_boundary'])|dict(topic_id=c['d3_id'],requirement_id=c['requirement_id'],claim_type=c['claim_type'],statement=c['statement'],source_status=c['evidence_status']+'_HISTORICAL_NOT_REQUALIFIED',locator_refs=l,case_refs=[],validation_refs=[],supersedes_refs=[],refinement_of=ref(o,'Claim',c['base_claim_ref']) if c.get('base_claim_ref') else None)
    add(r)
  # Preserve original design cases in all four views; deliberately not executed.
  for n,c in enumerate(load(p/'cases.json')['records']):
   pr=provenance(p/'cases.json','/records/'+str(n),'HISTORICAL_DESIGN_NOT_RUN')
   for view,text in c['views'].items():
    i=c['id']+'.'+view.upper();rr=[ref(o,'Claim',x) for x in c['claim_refs']]
    add(base(o,'Case',i,pr,negative='Historic synthetic design only; no observation or test result.')|dict(target_refs=rr,view=view.upper(),input_spec=c['fixture'],expected_spec=text,oracle_ref=None,actual_status='NOT_RUN'))
    for x in c['claim_refs']:records[x]['case_refs'].append(ref(o,'Case',i))
  for n,c in enumerate(design['claims']):
   if c['owner']!=o:continue
   i=c['id'];t=c['topic'];assert t in topic_refs
   pr=provenance(HERE/'professional-design.json','/claims/'+str(n),'ORIGINAL_BOUNDED_SOURCE_RECHECK')
   l=[loc(o,i,c['source'],pr,c['locator'])]
   cases=[(j,z) for j,z in enumerate(design['cases']) if z['claim']==i]
   assert {z['view'] for j,z in cases}=={'FORWARD','REVERSE','INTERVENTION','COUNTEREXAMPLE'}
   cr=ref(o,'Claim',i);vid=i+'.VALIDATION'
   rr=base(o,'Claim',i,pr,'CANDIDATE',c['conditions'],c['negative'])|dict(topic_id=t,requirement_id=t+'.RQ01',claim_type='PROFESSIONAL_BOUNDED_CANDIDATE',statement=c['statement'],source_status='TEXT_RECHECKED_LIMITED_PENDING_INDEPENDENT_QUALIFICATION',locator_refs=l,case_refs=[ref(o,'Case',z['id']) for j,z in cases],validation_refs=[ref(o,'Validation',vid)],supersedes_refs=[],refinement_of=None)
   add(rr);result=[]
   for j,z in cases:
    actual=evaluate(c['rule'],z['input']);assert actual==z['expected'],(z['id'],actual,z['expected'])
    test=dict(id=z['id'],owner=o,claim=i,rule=c['rule'],view=z['view'],input=z['input'],expected=z['expected'],actual=actual,status='PASS');result.append(test);tests.append(test)
    add(base(o,'Case',z['id'],provenance(HERE/'professional-design.json','/cases/'+str(j),'ORIGINAL_SYNTHETIC_FINITE_FIXTURE'),'CANDIDATE',negative='Finite symbolic example only; no real audio, assessment or universal grammaticality inference.')|dict(target_refs=[cr],view=z['view'],input_spec=canonical(z['input']),expected_spec=canonical(z['expected']),oracle_ref=ref(o,'Validation',vid),actual_status='RECORDED_BUILDER_ONLY'))
   add(base(o,'Validation',vid,pr,'CANDIDATE',negative='Builder fixture replay, not independent professional or empirical validation.')|dict(target_refs=[cr],case_refs=[ref(o,'Case',z['id']) for j,z in cases],method='FINITE_RULE_REPLAY',oracle_identity='AUTHOR_FIXED_SYNTHETIC_EXPECTED_NOT_INDEPENDENT',input_digest=dig([z['input'] for j,z in cases]),result_digest=dig(result),run_status='BUILDER_RUN'))
  cov[o]=[]
  for t in coverage:
   tid=t['d3_id'];claims=[r for r in records.values() if r['owner']==o and r['kind']=='Claim' and r['topic_id']==tid]
   candidates=[r['stable_id'] for r in claims if r['status']=='CANDIDATE'];held=[r['stable_id'] for r in claims if r['status']=='HOLD']
   cov[o].append(dict(d3_id=tid,requirement_id=t['requirement_id'],topic=t['topic'],candidate_claim_ids=candidates,held_claim_ids=held,coverage='RESTRICTED_SOURCE_RECHECK_CANDIDATE' if candidates else 'HOLD_PROFESSIONAL_DEPTH',remaining=t['remaining'],historical_d4_refs=t['existing_d4_refs'],qualification='NOT_RUN',full_depth='NOT_ESTABLISHED'))
 # All files are canonical JSONL text, including historical HOLDs with exact original provenance.
 PKG.mkdir(parents=True,exist_ok=True)
 def shard(name,rows):
  p=PKG/name;p.write_text(''.join(canonical(r)+'\n' for r in rows));return dict(path=name,format='JSONL_RECORDS',record_count=len(rows),sha256=sha(p))
 def manifest(name,package,owners,files,deps):
  p=PKG/name;write(p,dict(schema_version='learn-kg-canonical-candidate-1',package_id=package,version=V,status='CANDIDATE',rights='HOLD',owners=owners,files=files,dependencies=deps,qualification_receipt_refs=[]));return p
 ep=manifest('evidence.manifest.json','evidence',['EVIDENCE'],[shard('evidence.jsonl',[r for r in records.values() if r['kind']=='Source'])],[])
 cp=manifest('chinese.manifest.json','chinese',OWNERS,[shard(o+'.jsonl',[r for r in records.values() if r['owner']==o]) for o in OWNERS],[dict(package_id='evidence',version=V,manifest_sha256=sha(ep))])
 catalog={('evidence',V):ManifestPin(ep.relative_to(ROOT).as_posix(),sha(ep)),('chinese',V):ManifestPin(cp.relative_to(ROOT).as_posix(),sha(cp))}
 im=Importer(ROOT,mode='research',catalog=catalog)
 try:
  imported=im.run(('chinese',V))
  for z in tests:
   r=im.connections[('chinese',V)].execute('select input_spec,expected_spec from record_case where stable_id=?',(z['id'],)).fetchone();assert r
   # SQL stores JSON strings for these spec fields or plain strings depending on DB01 mapping.
   def read_spec(v):
    return json.loads(v)
   assert evaluate(z['rule'],read_spec(r[0]))==read_spec(r[1])==z['actual']
 finally:im.close()
 stats={o:dict(topics=len(cov[o]),restricted_candidate_topics=sum(bool(t['candidate_claim_ids']) for t in cov[o]),held_only_topics=sum(not t['candidate_claim_ids'] for t in cov[o]),records=sum(r['owner']==o for r in records.values()),candidate_claims=sum(r['owner']==o and r['kind']=='Claim' and r['status']=='CANDIDATE' for r in records.values()),held_claims=sum(r['owner']==o and r['kind']=='Claim' and r['status']=='HOLD' for r in records.values()),executed_cases=sum(z['owner']==o for z in tests)) for o in OWNERS}
 write(HERE/'coverage.json',dict(status='RESTRICTED_PARTIAL_PROFESSIONAL_CANDIDATE_NOT_FULL_DEPTH',modules=cov,stats=stats,inputs=inputs,private_manifest_sha256=hs['scope_restriction']['private_manifest_sha256'],rights='HOLD',cq='NOT_RUN',lc='NOT_RUN',independent_qualification='NOT_RUN'))
 write(HERE/'validation-results.json',dict(status='BUILDER_FINITE_REPLAY_ONLY',tests=tests,import_result=imported,stats=stats,manifest_sha256=sha(cp),persistent_sqlite=False))
 print(json.dumps(dict(stats=stats,imported=imported,tests=len(tests),manifest_sha256=sha(cp)),ensure_ascii=False))
if __name__=='__main__':main()
