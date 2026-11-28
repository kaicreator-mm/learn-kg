"""Registered root reconciliation and bounded current A01–A08 decision chain."""
import sys,json,hashlib,copy,importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
from tools.knowledge_import.importer import Importer,ManifestPin,refs
from tools.knowledge_import.v00_prototype import load_record
from build_projection import remap,OLD,NEW,OWNERS,HEAD,TREE,load,sha,dig,write
def module(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
fa=module('fa',HERE.parent/'f-a-batch/semantic_rules.py')
old=module('prior',HERE.parent/'f-composition-preparation/semantic_checks.py')
def main():
 ts={t['id']:t for t in load(ROOT/'docs/implementation/task-dag.json')['tasks']}
 pkey=('learning-process',OLD);hkey=('chinese','0.1.0-chinese-cumulative-candidate-2')
 accepted=load(HERE.parent/'f-a-batch/cumulative-evidence.json')
 # Known selected package closure pins from the reviewed evidence (no scanning).
 cat={}
 for p in sorted((ROOT/'knowledge/v0.1.0').glob('*/*manifest.json')):
  # This is administrative catalog assembly, not subject-route access.
  m=load(p);k=m.get('package_id'),m.get('version')
  if None not in k:cat[k]=ManifestPin(p.relative_to(ROOT).as_posix(),sha(p))
 owners=[f'K{i:02}' for i in range(1,20)]+[f'H{i:02}' for i in range(1,8)]+[f'P{i:02}' for i in range(1,11)]+[f'F{i:02}' for i in range(1,9)]+[f'A{i:02}' for i in range(1,9)]+['E01']
 roots={};bindings={}
 for o in owners:
  t=ts[o];p=ROOT/t['current_receipt'];r=load(p);assert t['status']=='CANDIDATE_READY'
  for f in r['output']:assert sha(ROOT/f['path'])==f['sha256']
  matches=[]
  for f in r['output']:
   mp=ROOT/f['path']
   if not mp.name.endswith('manifest.json'):continue
   m=load(mp);k=m.get('package_id'),m.get('version')
   if k[0] in ('learning-core','chinese','learning-process') and o in m.get('owners',[]):
    matches.append(k);assert cat[k].sha256==f['sha256']
  assert len(matches)==1,(o,matches)
  k=matches[0];roots[k]=cat[k]
  q=t.get('qualification_receipt');qr=load(ROOT/q) if q else None
  if qr:assert qr['reviewed_content_digest']==r['content_digest']
  bindings[o]=dict(receipt_path=t['current_receipt'],receipt_sha256=sha(p),content_digest=r['content_digest'],qualification_sha256=sha(ROOT/q) if q else None,package=list(k),manifest_sha256=cat[k].sha256)
 assert {k for k in roots if k[0]=='learning-process'}=={pkey}
 assert {k for k in roots if k[0]=='chinese'}=={hkey}
 db=load(ROOT/ts['DB03']['current_receipt']);assert db['scope_restriction']['process_manifest_sha256']==cat[pkey].sha256
 ext=ROOT/'knowledge/v0.1.0/foundation-r3/relation-types.json'
 im=Importer(ROOT,mode='research',catalog=cat,extension=ManifestPin(ext.relative_to(ROOT).as_posix(),sha(ext)))
 def pr(o,kind,id):return dict(package_id=pkey[0],version=pkey[1],owner=o,kind=kind,stable_id=id)
 def hr(kind,id):return dict(package_id=hkey[0],version=hkey[1],owner='H06',kind=kind,stable_id=id)
 try:
  for k in roots:im._load(k,set())
  links={k:im._validate_refs(k) for k in im.packages}
  for k,v in links.items():im._materialize(k,v)
  counts=dict(packages=len(im.connections),records=sum(len(v[3]) for v in im.packages.values()),typed_refs=sum(map(len,links.values())))
  assert counts=={'packages':18,'records':12568,'typed_refs':29902}
  # SQL actual current registry and projection source records correspond.
  projection=ROOT/'knowledge/v0.1.0/v01-shared-process-projection'
  nr=0
  for o in OWNERS:
   for line in (projection/(o+'.jsonl')).read_text().splitlines():
    r=json.loads(line);q=load_record(im,pr(o,r['kind'],r['stable_id']));rev=remap(r,NEW,OLD)
    for k,v in q.items():
     if type(rev[k]) is bool and isinstance(v,str):v=json.loads(v)
     assert v==rev[k],(o,r['stable_id'],k)
    nr+=1
  assert nr==1436
  # Exact current A composition inputs/outputs and evidence resolved before decisions.
  comps={}
  for o in [f'A{i:02}' for i in range(1,9)]:
   c=load_record(im,pr(o,'CompositionSpec',o+'.COMPOSITION'))
   assert c['effect']=='CANDIDATE_DECISION_ONLY'
   for r in c['input_refs']+c['output_refs']+c['claim_refs']+c['condition_refs']+c['evidence_refs']:load_record(im,r)
   comps[o]=dig(c)
  # Reuse actual scored ZH event chain, not a made-up independently diagnosed cause.
  zh=next(x for x in load(HERE/'lifecycle-results.json')['routes'] if x['domain']=='ZH')
  ev=zh['events'];scores=zh['actual']['events'];task=load_record(im,hr('TaskSpec','H06.CONFIRM.TASK'))
  for e,r in zip(ev,scores):
   assert e['construct_ref']==task['construct_ref'] and e['observation_ref'] in task['observation_refs']
   assert e['sha256']==r['event_sha256']==dig({k:v for k,v in e.items() if k!='sha256'})
  design=load(HERE.parent/'f-a-batch/design.json')
  def fixture(o):return copy.deepcopy(next(c['input'] for c in design['cases'] if c['id']==o+'.R4.CASE.1'))
  a1=fixture('A01');assert a1['object']['object'] in {r['stable_id'] for r in task['object_refs']}
  a2=fixture('A02');a2['artifact']='TEXT';a2['resource_gate']['modality']='TEXT'
  a3=fixture('A03');a3['diagnosis'].update(observation='INCORRECT',competing_explanations_checked=False,distinguished_gap=None)
  a3['state_channels']=dict(expected_scoring_version='S1',response=dict(status='OBSERVED',value=ev[0]['response'],task_version=ev[0]['task_version']),self_report=dict(status='MISSING'),score=dict(status='OBSERVED',value=scores[0]['score'],scoring_version='S1',denominator=1),estimate=dict(status='NOT_RUN'))
  a4=fixture('A04');a4['diagnosis']=copy.deepcopy(a3['diagnosis']);a4['state_channels']=copy.deepcopy(a3['state_channels'])
  a5=fixture('A05')
  # Variant is only a new fixture instance, not verified structural novelty: do not promote it.
  a5['retention']['events']=[dict(phase=phase,task_instance=e['id'],time=e['observed_at'],template=e['task_ref']['stable_id'],outcome='CORRECT' if r['score']==1 else 'INCORRECT',independent=True,construct_match=True,conditions_verified=True,structural_novelty_verified=False) for e,r,phase in zip(ev[1:3],scores[1:3],('IMMEDIATE','DELAYED'))]
  a6=fixture('A06');a6['independent_content_review']=False
  a8=fixture('A08');a8['retention']=copy.deepcopy(a5['retention'])
  a7=next(x for x in load(HERE.parent/'f-composition-preparation/fixtures.json') if x['owner']=='A07' and x['name']=='PRESERVED_CONSTRUCT_OPTIONAL_SUPPORT')
  expects={
   'A01':dict(goal='CONFIRMATION',task='H06.CONFIRM.TASK',object='H06.CONFIRM.OBJECT',necessary_prerequisites=[],level='UNKNOWN'),
   'A02':'REJECT_CONSTRUCT_SUBSTITUTION','A03':dict(state='UNKNOWN',diagnosis=dict(hypotheses=['PROPOSITION_UNDERSTANDING','RESPONSE_FORM','TASK_INSTRUCTION'],decision='REQUEST_OBSERVATION',mastery='UNKNOWN')),
   'A04':'HOLD','A05':dict(task='H06.CONFIRM.TASK',observations=dict(IMMEDIATE='CORRECT',DELAYED='CORRECT',NOVEL='UNKNOWN'),mastery='UNKNOWN',general_transfer='UNKNOWN'),
   'A06':'HOLD','A07':a7['expected'],'A08':'SIMULATION_ONLY_NOT_EFFECT'}
  cases=[]
  for o,x in [('A01',a1),('A02',a2),('A03',a3),('A04',a4),('A05',a5),('A06',a6),('A07',a7['input']),('A08',a8)]:
   y=old.FUN['A07'](x) if o=='A07' else fa.evaluate(o,x)
   assert y==expects[o],(o,y,expects[o])
   cases.append(dict(owner=o,input=x,expected=expects[o],actual=y,composition_sha256=comps[o]))
  assert all(c.execute('PRAGMA query_only').fetchone()==(1,) and not c.execute('PRAGMA foreign_key_check').fetchall() and all(not r[2] for r in c.execute('PRAGMA database_list')) for c in im.connections.values())
  report=dict(status='CURRENT_REGISTERED_ROOTS_AND_LIMITED_A_ROUTES_NOT_FULL_CQ_LC',registration_head=HEAD,registration_tree=TREE,roots=[list(k) for k in roots],bindings=bindings,closure=counts,projection_source_SQL_comparison=nr,DB03_receipt_sha256=sha(ROOT/ts['DB03']['current_receipt']),cases=cases,scope='A07 historical authority denial separate fixture, other A paths use synthetic event evidence or explicit missing conditions; not actual instruction/authority, no independent content review, no mastery or transfer',persistent_sqlite=False)
 finally:im.close()
 write(HERE/'current-assembly-results.json',report)
 print('ASSEMBLY',counts,'PROJECTION_SQL',nr,'A_ROUTES',len(cases))
if __name__=='__main__':main()
