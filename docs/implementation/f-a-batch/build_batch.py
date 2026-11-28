"""Bounded F/A composition preparation; immutable old process tuple, explicit cumulative migration."""
import json,hashlib,sys,collections
from pathlib import Path
from jsonschema import Draft202012Validator
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];B=ROOT/'knowledge/v0.1.0'
sys.path.insert(0,str(ROOT))
from tools.knowledge_import.importer import Importer,ManifestPin
from tools.knowledge_import.v00_prototype import load_record
from semantic_rules import evaluate
OLD=B/'learning-process-cumulative-r3';PKG=B/'learning-process-cumulative-r4';H=B/'chinese-cumulative-r2';V='0.1.0-process-candidate-4'
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dig(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
def path(p):return p.relative_to(ROOT).as_posix()
def main():
 d=load(HERE/'design.json');ts={x['id']:x for x in load(ROOT/'docs/implementation/task-dag.json')['tasks']};schema=load(ROOT/'docs/implementation/db01/canonical.schema.json');defs=schema['$defs']
 oldm=load(OLD/'learning-process.manifest.json');ov=oldm['version'];hm=load(H/'chinese.manifest.json');hv=hm['version']
 assert sha(H/'chinese.manifest.json')=='e2e92a12595c8a15bda667bc8d68c587efdea65dc07b0aab38637853881eae35'
 def remap(x):
  if isinstance(x,list):return [remap(y) for y in x]
  if isinstance(x,dict):
   y={k:remap(v) for k,v in x.items()}
   if set(y)=={'package_id','version','stable_id','kind','owner'} and y['package_id']=='learning-process':
    assert y['version']==ov;y['version']=V
   return y
  return x
 old={};records={};hrows={};migration=[]
 def read(m,p,dest,change=False):
  for f in m['files']:
   fp=p/f['path'];assert sha(fp)==f['sha256']
   for l in fp.read_text().splitlines():
    z=json.loads(l);i=z['stable_id'];assert i not in dest
    dest[i]=z
 read(oldm,OLD,old);read(hm,H,hrows)
 for i,r in old.items():
  n=remap(r);records[i]=n;migration.append(dict(id=i,owner=r['owner'],old_sha256=dig(r),new_sha256=dig(n),change='TYPED_REF_VERSION_ONLY' if r!=n else 'UNCHANGED'))
 assert len(old)==1725
 catalog={}
 for p in B.glob('*/*manifest.json'):
  m=load(p)
  if not {'package_id','version'}<=m.keys():continue
  k=(m['package_id'],m['version']);pin=ManifestPin(path(p),sha(p))
  if k in catalog:assert catalog[k].sha256==pin.sha256
  catalog[k]=pin
 deps={(z['package_id'],z['version']):z for z in oldm['dependencies']}
 def dep(k):
  deps[k]=dict(package_id=k[0],version=k[1],manifest_sha256=catalog[k].sha256)
 dep(('chinese',hv))
 def ref(r,p='learning-process',v=V):return dict(package_id=p,version=v,kind=r['kind'],stable_id=r['stable_id'],owner=r['owner'])
 def rr(id):
  if id in records:return ref(records[id])
  return ref(hrows[id],'chinese',hv)
 def verify_receipt(k):
  t=ts[k];p=ROOT/t['current_receipt'];r=load(p)
  for f in r['output']:assert sha(ROOT/f['path'])==f['sha256']
  result=dict(task_id=k,receipt_id=r['receipt_id'],receipt_sha256=sha(p),receipt_path=path(p),content_digest=r['content_digest'],version=r.get('version',r['exact_head']))
  if t.get('qualification_receipt'):
   qp=ROOT/t['qualification_receipt'];q=load(qp);assert q['reviewed_content_digest']==r['content_digest'];result.update(qualification_receipt=path(qp),qualification_receipt_sha256=sha(qp),qualification_content_digest=q['content_digest'])
  return r,result
 bindings={};prep={};claimbindings={};objbindings={};coverage={}
 ic=load(ROOT/'docs/implementation/if01/interface-contract.json');routes={r['owner']:r for r in ic['view_routes']}
 def claim(o,id):
  k=id.split('.')[0];assert k in ts[o]['depends_on'],(o,id)
  r,b=verify_receipt(k);s=r['scope_restriction']
  assert id in s['candidate_claim_ids'] and id not in set(s.get('source_limited_candidate_claim_ids',[])) and id not in set(s.get('model_claim_ids',[])),(o,id)
  hits=[]
  for f in r['output']:
   p=ROOT/f['path']
   if p.suffix!='.jsonl':continue
   for l in p.read_text().splitlines():
    z=json.loads(l)
    if z['stable_id']==id and z['owner']==k:hits.append((p,z))
  assert len(hits)==1,(o,id,len(hits))
  p,z=hits[0];assert z['kind']=='Claim' and z['status']=='CANDIDATE'
  if k.startswith('H'):
   assert ts[k].get('qualification_receipt') and id in load(ROOT/ts[k]['qualification_receipt'])['scope']['claim_ids']
   pkg='chinese';m=hm;mp=H/'chinese.manifest.json'
  else:
   assert ts[k].get('qualification_receipt');pkg='learning-core';mp=next(a/(pkg+'.manifest.json') for a in p.parents if (a/(pkg+'.manifest.json')).exists());m=load(mp)
   assert z['claim_type'] in ('PROJECT_RULE','ENGINEERING_POLICY','ORIGINAL_METHOD_DERIVATION','METHOD','MATHEMATICAL_DERIVATION')
  key=(pkg,m['version']);dep(key);assert sha(mp)==catalog[key].sha256 and any((mp.parent/f['path']).resolve()==p.resolve() and sha(p)==f['sha256'] for f in m['files'])
  rf=ref(z,*key);claimbindings[o][id]=b|dict(ref=rf,record_sha256=dig(z),path=path(p),shard_sha256=sha(p),manifest_sha256=sha(mp))
  return rf
 def add(o,kind,id,cr,**kw):
  assert id not in records
  z=dict(owner=o,kind=kind,stable_id=id,status='CANDIDATE',conditions=['合成候选输入；精确对象与版本绑定，未知HOLD；无真实授权或执行。'],negative_boundary='不推断真实能力、授权、先修、正式资格或效果；无直接知识写入。',provenance=[dict(source_path=path(HERE/'design.json'),source_sha256=sha(HERE/'design.json'),json_pointer='/modules/'+o,source_status='PROJECT_AUTHORED_CANDIDATE_DESIGN')])
  if 'claim_refs' in defs[kind]['properties']:z['claim_refs']=cr
  records[id]=z|kw
  return rr(id)
 for o,mod in d['modules'].items():
  assert set(routes[o]['task_dependencies'])==set(ts[o]['depends_on'])
  bindings[o]=[]
  for k in ts[o]['depends_on']:
   if k in d['modules']:
    assert k in prep;bindings[o].append(dict(task_id=k,state='PREPARATION_ONLY_NO_RECEIPT',owner_record_set_sha256=prep[k],version=V))
   else:bindings[o].append(verify_receipt(k)[1])
  claimbindings[o]={};objbindings[o]={};cr=[claim(o,i) for i in mod['claims']]
  inputs=[]
  for i in mod['inputs']:
   rf=rr(i);k=rf['owner'];assert k in ts[o]['depends_on'],(o,i,k)
   z=records.get(i,hrows.get(i));assert z['status']=='CANDIDATE'
   if i in old:
    r,_=verify_receipt(k)
    assert any(f['path']==path(OLD/(k+'.jsonl')) and f['sha256']==sha(OLD/(k+'.jsonl')) for f in r['output']),(o,i,'old receipt shard')
    assert remap(old[i])==z
   elif i in hrows:
    r,_=verify_receipt(k);assert r['scope_restriction']['owner_shard_sha256']==sha(H/(k+'.jsonl'))
   else:assert k in prep
   inputs.append(rf);objbindings[o][i]=dict(ref=rf,record_sha256=dig(z),source='PREPARATION' if k in prep else 'REGISTERED_EXACT_OR_VERSION_ONLY_REBIND')
   # Inherit professional refs through already typed composition contracts only.
   if z['kind']=='CompositionSpec':
    for c in z['claim_refs']:
     if c not in cr:cr.append(c)
  assert cr
  g=add(o,'ConditionSpec',o+'.R4.GUARD',cr,clauses=[dict(field='permission',op='EQ',value=True),dict(field='exit',op='EQ',value=False)],combination='ALL',unknown='HOLD')
  outputs=[]
  if o=='F01':
   for name,id in [('CONFIRMATION','H06.CONFIRM'),*[(k,'H06.TASK.'+k) for k in ('LISTENING','READING','SPEAKING','WRITING')]]:
    outputs.append(add(o,'Goal',o+'.R4.GOAL.'+name,cr,construct_ref=rr(id+'.SKILL'),scope='仅目标任务和其观测证据；等级、先修、掌握未知。',success_evidence_refs=[rr(id+'.OBS')]))
  if o=='F02':
   for name,id in [('CONFIRMATION','H06.CONFIRM'),*[(k,'H06.TASK.'+k) for k in ('LISTENING','READING','SPEAKING','WRITING')]]:
    outputs.append(add(o,'LearningObject',o+'.R4.OBJECT.'+name,cr,granularity='EXACT_TASK_OBJECT',target_refs=[rr(id+'.SKILL')],component_refs=[rr(id+'.OBJECT')]))
  if o=='F06':
   state=add(o,'StateDimension',o+'.R4.STATE',cr,construct_ref=rr('H06.CONFIRM.SKILL'),estimator_ref=None,observation_refs=[rr('H06.CONFIRM.OBS')],uncertainty='仅竞争解释和区分性观测；未知不推断掌握。',effect='DEFINITION_ONLY')
   # No automatically issued support suggestion; request observation or review.
   pol=add(o,'PolicySpec',o+'.R4.POLICY',cr,policy_type='REMEDIATION',rules=[dict(condition_ref=g,action='REQUEST_OBSERVATION',reason='仅复核证据与候选补救，不自动执行。',priority=0)],unknown_action='CLARIFY',effect='ADVICE_ONLY')
   outputs=[state,pol]
  if o=='F08':
   outputs=[rr('H06.CONFIRM.TASK'),rr('H06.CONFIRM.OBS')]
  if not outputs:outputs=[r for r in inputs if r['kind'] in ('CompositionSpec','TaskSpec','ObservationSpec','StateDimension','EvaluationProtocol','FlowSpec')][:3]
  target=add(o,'CompositionSpec',o+'.COMPOSITION',cr,view_id=o,input_refs=inputs,output_refs=outputs,condition_refs=[g],alternative_refs=[],evidence_refs=[],effect='CANDIDATE_DECISION_ONLY',failure_policy='STOP退出；REFUSE无权限；未知或不匹配HOLD；仅候选复核，不执行。')
  for c in [x for x in d['cases'] if x['owner']==o]:
   assert evaluate(o,c['input'])==c['expected'],c['id']
   cf=add(o,'Case',c['id'],cr,target_refs=[target],view=c['view'],input_spec=json.dumps(c['input'],ensure_ascii=False,sort_keys=True,separators=(',',':')),expected_spec=json.dumps(c['expected'],ensure_ascii=False,sort_keys=True,separators=(',',':')) if isinstance(c['expected'],dict) else c['expected'],oracle_ref=None,actual_status='RECORDED_BUILDER_ONLY')
   vf=add(o,'Validation',c['id']+'.VAL',cr,target_refs=[target],case_refs=[cf],method='FINITE_SYNTHETIC_BUILDER_REPLAY',oracle_identity='PROJECT_AUTHORED_NOT_INDEPENDENT',input_digest=dig(c['input']),result_digest=dig(c['expected']),run_status='BUILDER_RUN')
   records[c['id']]['oracle_ref']=vf;records[o+'.COMPOSITION']['evidence_refs'] += [cf,vf]
  prep[o]=dig([r for r in records.values() if r['owner']==o])
  coverage[o]=dict(required_scope_ids=routes[o]['required_scope_ids'],professional_topic_refs=routes[o]['professional_topic_refs'],status='PARTIAL_FINITE_PREPARATION_FULL_CQ_LC_NOT_RUN',scope=mod['description'],actual_cases=[c['id'] for c in d['cases'] if c['owner']==o],claim_ids=[r['stable_id'] for r in cr],inputs=mod['inputs'],full_scope='HOLD_UNTIL_INDEPENDENT_COMPLETE_COVERAGE')
 # Add exact H06 skill refs consumed by F06 via explicit input list (needed for canonical state).
 for r in records.values():
  if r['kind']=='CompositionSpec' and r['owner'] in prep:
   for cr in r['claim_refs']:assert (cr['package_id'],cr['version']) in deps
 validator=Draft202012Validator(schema)
 for r in records.values():validator.validate(r)
 PKG.mkdir(exist_ok=True)
 owners=oldm['owners']+list(d['modules']);files=[]
 for o in owners:
  rrlist=[z for z in records.values() if z['owner']==o]
  p=PKG/(o+'.jsonl');p.write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for r in rrlist))
  files.append(dict(path=p.name,sha256=sha(p),format='JSONL_RECORDS',record_count=len(rrlist)))
 mf=PKG/'learning-process.manifest.json';write(mf,dict(schema_version='learn-kg-canonical-candidate-1',package_id='learning-process',version=V,status='CANDIDATE',rights='HOLD',owners=owners,dependencies=sorted(deps.values(),key=lambda z:(z['package_id'],z['version'])),files=files,qualification_receipt_refs=[]))
 catalog['learning-process',V]=ManifestPin(path(mf),sha(mf))
 ext=B/'foundation-r3/relation-types.json';im=Importer(mode='research',catalog=catalog,extension=ManifestPin(path(ext),sha(ext)))
 try:
  report=im.run(('learning-process',V));actual=[]
  for c in d['cases']:
   z=load_record(im,rr(c['id']));inp=json.loads(z['input_spec']);expected=json.loads(z['expected_spec']) if isinstance(c['expected'],dict) else z['expected_spec']
   assert inp==c['input'] and evaluate(c['owner'],inp)==expected==c['expected']
   comp=load_record(im,z['target_refs'][0]);assert comp['effect']=='CANDIDATE_DECISION_ONLY'
   for r in comp['input_refs']+comp['output_refs']+comp['claim_refs']+comp['condition_refs']:load_record(im,r)
   actual.append(dict(case_id=c['id'],owner=c['owner'],actual=expected))
  for k,c in im.connections.items():
   assert c.execute('PRAGMA query_only').fetchone()==(1,) and not c.execute('PRAGMA foreign_key_check').fetchall() and all(not r[2] for r in c.execute('PRAGMA database_list'))
  assert ('learning-process',ov) not in im.packages and ('chinese',hv) in im.packages
 finally:im.close()
 write(HERE/'migration.json',dict(status='PREPARATION_VERSION_ONLY_NOT_RECEIPT',old_manifest_sha256=sha(OLD/'learning-process.manifest.json'),new_manifest_sha256=sha(mf),records=migration,counts=dict(collections.Counter(x['change'] for x in migration)),old_case_input_strings_unchanged=True,owner_preparation_sets=prep))
 write(HERE/'bindings.json',dict(status='PREPARATION_ONLY',input_receipts=bindings,claim_bindings=claimbindings,object_bindings=objbindings,owner_preparation_sets=prep))
 write(HERE/'coverage.json',coverage)
 write(HERE/'results.json',dict(status='AUTHOR_SQL_FINITE_PREPARATION',manifest_sha256=sha(mf),records=len(records),inherited_records=len(old),new_records=len(records)-len(old),actual_cases=len(actual),results=actual,import_report=report,persistent_sqlite=False))
 print('FA',len(records),len(actual),sha(mf),len(report['packages']))
if __name__=='__main__':main()
