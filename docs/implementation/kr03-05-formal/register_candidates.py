"""Register restricted builder candidates after preparation and dependency checks.
No independent qualification is inferred from preparation review.
"""
import json,hashlib,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[2]
B=ROOT/'knowledge/v0.1.0'
ART='d4e50eebb8605f7326b2b5d6afc3a9c3edce656a'
BASE='bd7ffbd9240a63af23cd3b91595c3e5b7a04603b'
ORDER=['K10','K12','K15','K16','K19','K11']
PACK={k:('trace-adaptation-resources-r1' if k in ('K10','K11','K12') else 'technology-inclusion-governance-r1') for k in ORDER}
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dig(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def main():
 assert git('rev-parse','HEAD')==ART and git('branch','--show-current')=='version/v0.1.0'
 dp=ROOT/'docs/implementation/task-dag.json';d=load(dp);tasks={x['id']:x for x in d['tasks']}
 w=load(P/'dependency-witness.json');assert w['pairs']==14 and len(w['results'])==56
 for k in ORDER:
  t=tasks[k];assert t['status']=='PLANNED' and not t.get('current_receipt')
  p=B/PACK[k];m=load(p/'learning-core.manifest.json');e=load(p/'evidence.manifest.json');cov=load(p/k/'coverage.json')
  idx={};out=[]
  def add(fp,kind='SHARED_CANDIDATE_INPUT_OR_EVIDENCE'):
   q=fp.relative_to(ROOT).as_posix()
   assert fp.is_file() and hashlib.sha256(subprocess.check_output(['git','show',ART+':'+q],cwd=ROOT)).hexdigest()==sha(fp),q
   if not any(x['path']==q for x in out):out.append({'path':q,'sha256':sha(fp),'type':kind})
  for mf in ('learning-core.manifest.json','evidence.manifest.json'):add(p/mf)
  for man in (m,e):
   for f in man['files']:
    fp=p/f['path'];assert sha(fp)==f['sha256'];add(fp,'MODULE_CANDIDATE_ARTIFACT' if f['path'].startswith(k+'/') else 'SHARED_CANDIDATE_INPUT_OR_EVIDENCE')
    if f['path'].startswith(k+'/'):
     for l in fp.read_text().splitlines():
      x=json.loads(l);idx[x['stable_id']]=x
  assert m['dependencies'][0]['manifest_sha256']==sha(p/'evidence.manifest.json')
  add(p/k/'coverage.json','MODULE_CANDIDATE_ARTIFACT')
  for f in ['README.md','anchor-dispositions.json','finite-fixtures.json','finite-results.json','consumption-results.json','import-receipt.json','validation-receipt.json','model-design.json','decision-design.json','run_finite.py','check_consumption.py','model-domain-constraints.json','model-spec-guard-fixtures.json','model-spec-guard-results.json']:
   if (p/f).is_file():add(p/f)
  doc=ROOT/'docs/implementation'/('kr03-kt-policy-resource-preparation' if k in ('K10','K11','K12') else 'k15-k16-k19-preparation')
  for f in [f'{k}-depth.md','depth.json','scope-witness.json','current-source-observations.json']:add(doc/f)
  for f in [P/'dependency-witness.json',P/'bind_dependencies.py',ROOT/'docs/implementation/kr03-05-batch/scope-ledger.json',ROOT/'docs/implementation/kr03-05-batch/p2-remediation.md',ROOT/'tools/knowledge_import/model_spec.py']:add(f)
  active={cid for z in cov['topics'] for cid in z['active_claim_ids']}
  allids={cid for z in cov['topics'] for cid in z['claim_ids']}
  assert active<=set(idx) and all(idx[c]['status']=='CANDIDATE' for c in active)
  allowed=sorted(c for c in active if idx[c]['claim_type'] in ('PROJECT_RULE','ORIGINAL_METHOD_DERIVATION','MATHEMATICAL_DERIVATION','METHOD') and not idx[c].get('source_status','').startswith('HOLD'))
  excluded=sorted(allids-set(allowed))
  rows=[x for x in w['results'] if x['owner']==k];assert rows and all(x['local'] in allowed for x in rows)
  direct=[];inputs=[]
  for dep in t['depends_on']:
   a=tasks[dep];rp=a['current_receipt'];rr=load(ROOT/rp)
   assert a['status'] in ('CANDIDATE_READY','GATE_ACCEPTED') and rr['state']==a['status'] and rr['task_id']==dep
   refs=[{'path':rp,'sha256':sha(ROOT/rp)}]
   ids=sorted({x['upstream'] for x in rows if x['upstream'].split('.')[0]==dep})
   if dep.startswith('K'):assert ids,(k,dep)
   for id in ids:
    b=w['bindings'][id];assert any(o['path']==b['file'] and o['sha256']==b['file_sha256'] for o in rr['output']),id
    if 'candidate_claim_ids' in rr.get('scope_restriction',{}):assert id in rr['scope_restriction']['candidate_claim_ids']
    refs.append({'path':b['file'],'sha256':b['file_sha256'],'stable_id':id,'record_sha256':b['record_sha256']})
   if a.get('qualification_receipt'):
    q=a['qualification_receipt'];qr=load(ROOT/q);assert qr['reviewed_content_digest']==rr['content_digest'] and qr['state']=='QUALIFIED_LOCAL'
    refs.append({'path':q,'sha256':sha(ROOT/q)})
   inputs.append({'task_id':dep,'receipt_id':rr['receipt_id'],'content_digest':rr['content_digest'],'version':rr['version'],'specific_refs':refs})
   direct.append({'task_id':dep,'claims':ids,'scope':a.get('qualification_scope','LOCAL_OR_CANDIDATE'),'qualification':a.get('qualification_receipt','NOT_ISSUED')})
  out.sort(key=lambda x:x['path'])
  restriction={'status':'RESTRICTED_CANDIDATE_SCOPE','candidate_claim_ids':allowed,'excluded_claim_ids':excluded,'canonical_candidate_count':len(active),'candidate_claim_count':len(allowed),'canonical_hold_count':len(allids-active),'additional_excluded_count':len(active-set(allowed)),'source_limited_candidate_claim_ids':[],'source_claim_policy':'Source-limited and unverified hypotheses excluded from consumption; canonical snapshot unchanged. P3 source pinning remains HOLD.','manifest_sha256':sha(p/'learning-core.manifest.json'),'coverage_sha256':sha(p/k/'coverage.json'),'dependency_uses':direct,'witness_sha256':sha(P/'dependency-witness.json'),'rights':'HOLD','cq':'NOT_RUN','lc':'NOT_RUN','limits':'Project rules, bounded synthetic methods and mathematical derivations only; no generic execution, empirical/source qualification or full D3 adequacy. Exact dependency witnesses are restricted authored guard checks, not canonical semantic edges.'}
  r={'operator':'chatgpt-web:learn-kg-controller','session':'learn-kg-kr03-05-formal-20261127','role':'BUILDER_NON_REVIEWER','branch':'version/v0.1.0','base':BASE,'exact_head':ART,'version':ART,'contract_id':'D013-R3R-D014','contract_hash':sha(ROOT/'docs/implementation/task-execution-contract.md'),'time':'2026-11-27','task_id':k,'attempt_id':k+'-FORMAL-01','receipt_id':'TASK:'+k+':'+k+'-FORMAL-01','input':inputs,'output':out,'state':'CANDIDATE_READY','receipt_type':'CANDIDATE_READY','scope':'Restricted nonempirical candidate after formal prerequisite binding; not independent readiness verdict or qualification.','scope_restriction':restriction,'validation':{'previous_preparation_review_comment':7221120084,'previous_independent_finite_cases':68 if k in ('K10','K11','K12') else 47,'previous_finite_count_is_shared_package_not_per_module':True,'current_builder_dependency_cases':len(rows),'current_independent_review':'NOT_RUN','qualification':'NOT_ISSUED'},'issues':['P2 repairs pending independent delta adjudication.','P3 source pinning HOLD; all source-limited claims excluded.','Broader professional depth and canonical semantic closure remain unresolved.'],'next':'KR03–KR05 cumulative independent exact-tuple qualification review.'}
  r['content_digest']=dig({'input':inputs,'output':out})
  rp=ROOT/'evidence/tasks'/k/(k+'-FORMAL-01.json');assert not rp.exists();write(rp,r)
  t['status']='CANDIDATE_READY';t['current_receipt']=rp.relative_to(ROOT).as_posix();t['qualification_scope']='RESTRICTED'
  print(k,len(allowed),'allowed',len(excluded),'excluded',len(rows),'guard cases',r['content_digest'])
 # Candidates may be consumed before local qualification; never treat them as a final gate.
 for t in d['tasks']:
  if t['status']=='PLANNED' and t['requirements'] and all(tasks[z['task_id']]['status']==z['receipt'] and tasks[z['task_id']].get('current_receipt') for z in t['requirements']):
   t['status']='READY';print('READY',t['id'])
 d['dispatch']['current_task_state_note']='K01–K19 current candidate receipts; KR01/KR02 restricted/local qualifications retained; KR03–KR05 ready for batch review; P01 restricted candidate; P02/P03 etc only as exact requirements allow. SRC01 blocked.'
 write(dp,d)
if __name__=='__main__':main()
