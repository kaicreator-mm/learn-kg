"""Author-defined finite discriminations, with exact upstream claim/receipt binding."""
import json,hashlib,pathlib
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dig(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def nat(x):return type(x) is int and x>=0
def text(x):return isinstance(x,str) and bool(x.strip())
def booleans(x):return isinstance(x,list) and bool(x) and all(type(k) is bool for k in x)
def evaluate(pair,x):
 if pair=='X01':
  if x.get('goal')!='recall' or x.get('independent') is not True or x.get('scoring_contract_equal') is not True:return 'HOLD'
  if x.get('test')=='recognition' and x.get('options') is True:return 'RECALL_NOT_ESTABLISHED'
  return 'RECALL_EVIDENCE_CANDIDATE' if x.get('test')=='recall' and x.get('options') is False else 'HOLD'
 if pair=='X02':
  if not booleans(x.get('component_pass')) or x.get('whole_target_matches') is not True:return 'HOLD'
  if x.get('whole_result') is None:return 'REQUEST_WHOLE_TASK'
  if x.get('whole_independent') is not True or type(x.get('whole_result')) is not bool:return 'HOLD'
  if x['whole_result']:return 'WHOLE_EVIDENCE_CANDIDATE'
  return 'COMPONENT_SUCCESS_WHOLE_NOT_MET' if all(x['component_pass']) else 'HOLD'
 if pair=='X03':
  a,b,d=(x.get(k) for k in ('last_exposure_day','test_day','target_delay_days'))
  if not all(nat(k) for k in (a,b,d)) or b<a or d==0 or x.get('independent') is not True or type(x.get('context_same')) is not bool:return 'HOLD'
  if b-a<d:return 'DELAY_NOT_MET'
  return 'RETENTION_EVIDENCE_CANDIDATE' if x['context_same'] else 'TRANSFER_OBSERVATION_SEPARATE'
 if pair=='X04':
  s,o=x.get('steps'),x.get('observed_steps')
  if not text(x.get('target')) or x['target']!=x.get('observation_target') or not isinstance(s,list) or not s or not all(text(k) for k in s) or len(set(s))!=len(s) or not isinstance(o,list) or not all(text(k) for k in o):return 'HOLD'
  if not set(s)<=set(o):return 'REQUEST_STEP_OBSERVATION'
  return 'TASK_ANALYSIS_WITNESS_CANDIDATE' if x.get('whole_observed') is True else 'REQUEST_WHOLE_OBSERVATION'
 if pair=='X05':
  s,j,n,c=(x.get(k) for k in ('solo','joint','total','criterion'))
  if not isinstance(s,list) or len(s)!=2 or not all(nat(k) for k in [*s,j,n,c]) or not 0<c<=n or max(*s,j)>n or x.get('matched') is not True or x.get('independent') is not True:return 'HOLD'
  if j>=c:return 'JOINT_RULE_MET'
  return 'JOINT_DIFFICULTY_HYPOTHESIS_ONLY' if min(s)>=c else 'COMPONENT_GAP_POSSIBLE'
 if pair=='X06':
  if not text(x.get('target')) or x['target']!=x.get('observed_target') or not all(x.get(k) is True for k in ('allowed_route','same_conditions','independent')) or x.get('prerequisite_ability') not in ('PRESENT','ABSENT') or x.get('target_result') not in ('MET','NOT_MET'):return 'HOLD'
  return 'REFUTES_NECESSITY_IN_SCOPE' if x['prerequisite_ability']=='ABSENT' and x['target_result']=='MET' else 'NO_COUNTEREXAMPLE'
 if pair=='X07':
  if not booleans(x.get('component_results')) or x.get('same_rubric') is not True or x.get('independent') is not True:return 'HOLD'
  y=x.get('integration_result')
  return 'REQUEST_INTEGRATED_TASK' if y is None else 'INTEGRATED_EVIDENCE_CANDIDATE' if y is True else 'INTEGRATED_RULE_NOT_MET' if y is False else 'HOLD'
 raise ValueError('unknown pair')
def main():
 # Re-run actual identity resolver before consuming the witness.
 import subprocess,sys
 subprocess.run([sys.executable,str(P/'check_cross_inputs.py')],check=True)
 w=load(P/'cross-input-witness.json');pairs={x['id']:x for x in w['pairs']}
 dag={x['id']:x for x in load(ROOT/'docs/implementation/task-dag.json')['tasks']}
 depth={x['topic']+'.PT.01':x for x in load(P/'depth-additions.json')}
 out=[]
 for i,c in enumerate(load(P/'cross-semantic-fixtures.json')['cases']):
  pair=pairs[c['pair']];u=pair['upstream'];l=pair['local'];receipt=u['receipt']
  t=dag[u['owner']]
  assert t['current_receipt']==receipt['specific_refs'][0]['path']
  assert t['qualification_receipt']==receipt['local_qualification_evidence']['path']
  assert sha(ROOT/u['path'])==u['file_sha256']
  rows=[json.loads(x) for x in (ROOT/u['path']).read_text().splitlines()]
  row=next(x for x in rows if x['stable_id']==u['stable_id']);assert dig(row)==u['record_sha256']
  method=depth[l['stable_id']]
  actual=evaluate(c['pair'],c['input']);assert actual==c['expected'],(c['pair'],c['name'],actual)
  out.append({'id':c['pair']+'.'+c['name'],'local_claim':l['stable_id'],'local_method_digest':dig(method),'upstream_claim':u['stable_id'],'upstream_record_sha256':u['record_sha256'],'upstream_receipt_digest':receipt['content_digest'],'input':c['input'],'expected':c['expected'],'actual':actual,'status':'PASS_BUILDER_FINITE_ONLY'})
 f=P/'cross-semantic-fixtures.json'
 (P/'cross-semantic-results.json').write_text(json.dumps({'fixture_sha256':sha(f),'depth_sha256':sha(P/'depth-additions.json'),'upstream_manifest_sha256':w['upstream_manifest_sha256'],'results':out,'limit':'Author-defined case discrimination; not qualified graph edge or general inference engine.'},ensure_ascii=False,indent=2)+'\n')
 print(len(out),'PASS_CROSS_SEMANTIC_DISCRIMINATIONS')
if __name__=='__main__':main()
