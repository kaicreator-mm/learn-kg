#!/usr/bin/env python3
"""Canonical restricted professional candidate plus retained historical research HOLDs."""
from pathlib import Path
import collections,json,hashlib,sys,re
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];sys.path.insert(0,str(ROOT))
from tools.knowledge_import.importer import Importer,ManifestPin
from semantic_rules import evaluate
D=ROOT/'docs/drafts/s01';PKG=ROOT/'knowledge/v0.1.0/chinese-cumulative-r2';V='0.1.0-chinese-cumulative-candidate-2'
OWNERS=['H05','H06','H07'];PRIOR=['H01','H02','H03','H04']
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
 oldpkg=ROOT/'knowledge/v0.1.0/chinese-h01-h04-r1'
 oldm=load(oldpkg/'chinese.manifest.json');oldv=oldm['version']
 assert sha(oldpkg/'chinese.manifest.json')=='9df9fac440aaee6c97b2e5c58699af48f0b9e937dc58fceef2228d1b99621380'
 olde=load(oldpkg/'evidence.manifest.json');assert sha(oldpkg/'evidence.manifest.json')==oldm['dependencies'][0]['manifest_sha256']
 def remap(x):
  if isinstance(x,list):return [remap(y) for y in x]
  if isinstance(x,dict):
   y={k:remap(v) for k,v in x.items()}
   if set(y)=={'package_id','version','stable_id','kind','owner'} and y['package_id'] in ('chinese','evidence'):
    assert y['version']==oldv;y['version']=V
   return y
  return x
 migration=[]
 for m in (olde,oldm):
  for f in m['files']:
   p=oldpkg/f['path'];assert sha(p)==f['sha256']
   for line in p.read_text().splitlines():
    r=json.loads(line);i=r['stable_id'];assert i not in records
    nr=remap(r);records[i]=nr;migration.append(dict(id=i,owner=r['owner'],old_sha256=dig(r),new_sha256=dig(nr),change='TYPED_REF_VERSION_ONLY' if r!=nr else 'UNCHANGED'))
 assert len(migration)==1294
 old_tests=load(ROOT/'docs/implementation/h01-h04-batch/validation-results.json')['tests']
 preparation={}

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
   if dep in OWNERS:
    assert dep in preparation
    inputs[o].append(dict(task_id=dep,state='PREPARATION_ONLY_NO_RECEIPT',record_set_sha256=preparation[dep],version=V))
    continue
   p=ROOT/tasks[dep]['current_receipt'];r=load(p)
   inputs[o].append(dict(task_id=dep,receipt_id=r['receipt_id'],content_digest=r['content_digest'],version=r.get('version',r['exact_head']),receipt_path=p.relative_to(ROOT).as_posix(),receipt_sha256=sha(p)))
  p=D/o
  source_files=[p/'sources.json',*sorted((D/'depth/D2').glob('*/'+o+'/sources.json'))]
  for f in source_files:
   for n,s in enumerate(load(f)['sources']):source(o,s,f,'/sources/'+str(n))
  for n,s in enumerate(design['sources']):
   if s['owner']==o:source(o,s,HERE/'professional-design.json','/sources/'+str(n),s['access']=='TEXT_RECHECKED_20261128')
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
   rr=base(o,'Claim',i,pr,'CANDIDATE',c['conditions'],c['negative'])|dict(topic_id=t,requirement_id=t+'.RQ01',claim_type='PROJECT_RULE' if c['rule'] in ('repair','standard_mapping','membership','task_modality','pragmatic_context') else 'PROFESSIONAL_BOUNDED_CANDIDATE',statement=c['statement'],source_status='PROJECT_RECEIPT_BOUND_PENDING_REVIEW' if c['rule']=='membership' else 'TEXT_RECHECKED_LIMITED_PENDING_INDEPENDENT_QUALIFICATION',locator_refs=l,case_refs=[ref(o,'Case',z['id']) for j,z in cases],validation_refs=[ref(o,'Validation',vid)],supersedes_refs=[],refinement_of=None)
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
  # Explicit finite canonical task templates, not observed performance.
  def rr(id):
   z=records[id];return ref(z['owner'],z['kind'],id)
  def obj(kind,id,claim,**fields):
   c=records[claim]
   return add(base(o,kind,id,c['provenance'][0],'CANDIDATE',negative='原创有限任务模板；不是标准等级映射、真实学习者表现或能力证明。')|fields)
  if o=='H05':
   c='H05.01.01.R2.C01'
   obj('Element','H05.RFC.SEQUENCE',c,topic_id='H05.01.01',element_type='COMMUNICATIVE_SEQUENCE',label='确认请求及应答序列',definition='记录前序命题、请求形式、确认或否认应答；未知应答不推断理解。',claim_refs=[rr(c)])
  if o=='H06':
   for skill,artifact,operation,prompt in [('LISTENING','AUDIO','MEANING_RESPONSE','听一段原创路线说明后回答目的地；必须提供音频。'),('READING','TEXT','MEANING_RESPONSE','阅读原创路线说明后回答目的地。'),('SPEAKING','AUDIO_OUTPUT','PRODUCTION','用口头中文说明到图书馆的路线；保存音频。'),('WRITING','TEXT_OUTPUT','PRODUCTION','写出到图书馆的路线；保存原始文字。')]:
    c='H06.01.02.R2.C01';support='H06.06.04.R2.C01';id='H06.TASK.'+skill
    cr=[rr(c),rr(support)]
    sk=obj('SkillType',id+'.SKILL',c,label=skill,performance_boundary='仅目标任务的通道与操作证据；未知不计零分或熟练度。',claim_refs=cr)
    lo=obj('LearningObject',id+'.OBJECT',c,granularity='FINITE_ORIGINAL_ROUTE_TASK',target_refs=[sk],component_refs=[],claim_refs=cr)
    ob=obj('ObservationSpec',id+'.OBS',c,construct_ref=sk,method='记录 '+artifact+' 与 '+operation+'，另记帮助、时点及任务条件。',unit='TASK_OBSERVATION',independence_requirement='本人独立表现与帮助分开，缺失保持未知。',missing='UNKNOWN_NOT_ZERO',claim_refs=cr)
    obj('TaskSpec',id,c,construct_ref=sk,object_refs=[lo],observation_refs=[ob],prompt=prompt,scoring_spec='通道与操作匹配只触发证据复核；不自动评定分数、掌握或等级。',independence_requirement='需记录独立完成条件；无真实产物不得评估。',claim_refs=cr)
   c='H06.02.04.R2.C01';dep='H05.01.01.R2.C01'
   cr=[rr(c),rr(dep),rr('H06.06.04.R2.C01')]
   sk=obj('SkillType','H06.CONFIRM.SKILL',c,label='交际确认与回应',performance_boundary='确认或否认观察不证明一般互动能力。',claim_refs=cr)
   lo=obj('LearningObject','H06.CONFIRM.OBJECT',c,granularity='FINITE_DIALOGUE_SEQUENCE',target_refs=[sk,rr('H05.RFC.SEQUENCE')],component_refs=[],claim_refs=cr)
   ob=obj('ObservationSpec','H06.CONFIRM.OBS',c,construct_ref=sk,method='保存前序命题、回应与原始对话；记录是否需要帮助。',unit='DIALOGUE_TURN_SEQUENCE',independence_requirement='独立回应且前序命题和应答可核查。',missing='UNKNOWN_NOT_ZERO',claim_refs=cr)
   task=obj('TaskSpec','H06.CONFIRM.TASK',c,construct_ref=sk,object_refs=[lo],observation_refs=[ob],prompt='甲：明天九点见，对吗？乙按收到的安排确认或纠正，并在不清楚时询问。',scoring_spec='只记录给定序列是否完成确认或否认；缺少应答证据保持HOLD。',independence_requirement='记录真实应答及帮助，模板本身不是观察。',claim_refs=cr)
   obj('Competency','H06.CONFIRM.COMPETENCY',c,dimensions=['前序命题理解','确认或否认回应','必要时澄清'],claim_refs=cr,evidence_refs=[task,ob])
  if o=='H07':
   c='H07.01.01.R2.C01'
   st=obj('Standard','H07.GF0025.2021',c,edition='2021',standard_name='国际中文教育中文水平等级标准（GF0025-2021）',effective_date='2021-07-01',source_refs=[srcs['H07-R2-MOE'][0],srcs['H07-R2-MOE-QA'][0]])
   # Only published structure of three groups, not particular official member assignments.
   for i,label in enumerate(('初等','中等','高等'),1):
    obj('StandardBand','H07.GF0025.2021.GROUP.'+str(i),c,standard_ref=st,raw_band=label,band_scope='官方三等框架；每等三个级别，不附词表成员、学习先修或水平等价。')
   c='H07.01.04.R2.C01'
   obj('Standard','H07.HSK3.ANNOUNCEMENT',c,edition='3.0',standard_name='HSK 3.0 正式开考公告（考试体系身份候选）',effective_date=None,source_refs=[srcs['H07-R2-CTI'][0]])
   c='H07.05.03.R2.C01'
   obj('Element','H07.ALIGNMENT.EVIDENCE_GATE',c,topic_id='H07.05.03',element_type='EVIDENCE_GATE',label='跨标准对齐证据门',definition='仅比较明确版本与独立对齐证据；同名等级、词表量与任务模板不构成等级等价。',claim_refs=[rr(c),rr('H07.02.02.R2.C01'),rr('H06.06.04.R2.C01')])
  # Staged internal dependency pins are not formal task receipts.
  preparation[o]=dig([r for r in records.values() if r['owner']==o])
 # All files are canonical JSONL text, including historical HOLDs with exact original provenance.
 PKG.mkdir(parents=True,exist_ok=True)
 def shard(name,rows):
  p=PKG/name;p.write_text(''.join(canonical(r)+'\n' for r in rows));return dict(path=name,format='JSONL_RECORDS',record_count=len(rows),sha256=sha(p))
 def manifest(name,package,owners,files,deps):
  p=PKG/name;write(p,dict(schema_version='learn-kg-canonical-candidate-1',package_id=package,version=V,status='CANDIDATE',rights='HOLD',owners=owners,files=files,dependencies=deps,qualification_receipt_refs=[]));return p
 ep=manifest('evidence.manifest.json','evidence',['EVIDENCE'],[shard('evidence.jsonl',[r for r in records.values() if r['kind']=='Source'])],[])
 cp=manifest('chinese.manifest.json','chinese',PRIOR+OWNERS,[shard(o+'.jsonl',[r for r in records.values() if r['owner']==o]) for o in PRIOR+OWNERS],[dict(package_id='evidence',version=V,manifest_sha256=sha(ep))])
 catalog={('evidence',V):ManifestPin(ep.relative_to(ROOT).as_posix(),sha(ep)),('chinese',V):ManifestPin(cp.relative_to(ROOT).as_posix(),sha(cp))}
 im=Importer(ROOT,mode='research',catalog=catalog)
 try:
  imported=im.run(('chinese',V))
  for z in tests+old_tests:
   r=im.connections[('chinese',V)].execute('select input_spec,expected_spec from record_case where stable_id=?',(z['id'],)).fetchone();assert r
   # SQL stores JSON strings for these spec fields or plain strings depending on DB01 mapping.
   def read_spec(v):
    return json.loads(v)
   assert evaluate(z['rule'],read_spec(r[0]))==read_spec(r[1])==z['actual']
 finally:im.close()
 stats={o:dict(topics=len(cov[o]),restricted_candidate_topics=sum(bool(t['candidate_claim_ids']) for t in cov[o]),held_only_topics=sum(not t['candidate_claim_ids'] for t in cov[o]),records=sum(r['owner']==o for r in records.values()),candidate_claims=sum(r['owner']==o and r['kind']=='Claim' and r['status']=='CANDIDATE' for r in records.values()),held_claims=sum(r['owner']==o and r['kind']=='Claim' and r['status']=='HOLD' for r in records.values()),executed_cases=sum(z['owner']==o for z in tests)) for o in OWNERS}
 write(HERE/'coverage.json',dict(status='RESTRICTED_PARTIAL_PROFESSIONAL_CANDIDATE_NOT_FULL_DEPTH',modules=cov,stats=stats,inputs=inputs,private_manifest_sha256=hs['scope_restriction']['private_manifest_sha256'],rights='HOLD',cq='NOT_RUN',lc='NOT_RUN',independent_qualification='NOT_RUN'))
 write(HERE/'validation-results.json',dict(status='BUILDER_FINITE_REPLAY_ONLY',tests=tests,inherited_cases_replayed=len(old_tests),import_result=imported,stats=stats,manifest_sha256=sha(cp),persistent_sqlite=False))
 write(HERE/'migration.json',dict(status='PREPARATION_ONLY_VERSION_REBIND_REVIEW_REQUIRED',old_manifest_sha256=sha(oldpkg/'chinese.manifest.json'),new_manifest_sha256=sha(cp),records=migration,counts=dict(collections.Counter(x['change'] for x in migration)),internal_preparation_record_sets=preparation))
 print(json.dumps(dict(stats=stats,imported=imported,tests=len(tests),manifest_sha256=sha(cp)),ensure_ascii=False))
if __name__=='__main__':main()
