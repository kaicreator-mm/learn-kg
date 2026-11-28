"""Exact current SQL model/claim consumption plus original finite numerical/decision fixtures."""
import json,hashlib,sys,math,copy,importlib.util
from fractions import Fraction as Q
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];B=ROOT/'knowledge/v0.1.0'
sys.path.insert(0,str(ROOT))
from tools.knowledge_import.importer import Importer,ManifestPin
from tools.knowledge_import.v00_prototype import load_record
from tools.knowledge_import.model_spec import load_domain_contract,validate_model_parameters,ModelParameterError
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dig(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def module(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
f=module('f05',HERE.parent/'f-composition-preparation/semantic_checks.py')
p=module('p_rules',HERE.parent/'process-cumulative/semantic_checks.py')
ASSEMBLY=load(HERE.parent/'v01-current-projection/current-assembly-results.json')
V='0.1.0-trace-adaptation-resources-candidate-1'
P='0.1.0-process-candidate-4'
DOMAIN=load_domain_contract(B/'trace-adaptation-resources-r1/model-domain-constraints.json')
def need(v):
 if not v:raise ValueError('GUARD')
def num(v):
 need(type(v) in (int,float) and math.isfinite(v));return Q(str(v))
def nat(v):need(type(v)is int and v>=0);return v
def ast(e,v,binary=False):
 if 'variable' in e:return v[e['variable']]
 if 'constant' in e:return float(e['constant']) if binary else Q(str(e['constant']))
 a=[ast(z,v,binary) for z in e['args']];op=e['op']
 if op=='add':return sum(a)
 if op=='mul':return math.prod(a)
 if op=='sub':return a[0]-a[1]
 if op=='div':return a[0]/a[1]
 if op=='neg':return -a[0]
 if op=='pow':need(binary and (a[0]>0 or a[0]==0 and a[1]>0));return a[0]**a[1]
 raise ValueError(op)
def record(im,o,k,id):
 key=ASSEMBLY['bindings'][o]['package'];return load_record(im,dict(package_id=key[0],version=key[1],owner=o,kind=k,stable_id=id))
def claim(im,id,used):
 o=id.split('.')[0];r=record(im,o,'Claim',id);key=tuple(ASSEMBLY['bindings'][o]['package']);need(im.packages[key][3][id]['status']=='CANDIDATE')
 t=load(ROOT/ASSEMBLY['bindings'][o]['receipt_path']);s=t['scope_restriction']
 need(id in s['candidate_claim_ids'] and id not in s.get('excluded_claim_ids',[]) and id not in s.get('source_limited_candidate_claim_ids',[]))
 tq=next(t for t in load(ROOT/'docs/implementation/task-dag.json')['tasks'] if t['id']==o)
 qs=load(ROOT/tq['qualification_receipt'])['scope_restriction']
 need(id in qs['candidate_claim_ids'] and id not in qs.get('excluded_claim_ids',[]) and id not in qs.get('source_limited_candidate_claim_ids',[]))
 used[id]=dict(record_sha256=dig(r),statement=r['statement'],owner_receipt_sha256=ASSEMBLY['bindings'][o]['receipt_sha256'],qualification_sha256=ASSEMBLY['bindings'][o]['qualification_sha256'])
 return r
def model(im,id,vals,used,models):
 o=id.split('.')[0];m=record(im,o,'ModelSpec',id)
 need(m['missing_policy']=='HOLD')
 for r in m['claim_refs']:
  need(r['kind']=='Claim' and r['owner']==o and (r['package_id'],r['version'])==tuple(ASSEMBLY['bindings'][o]['package']))
  claim(im,r['stable_id'],used)
 # Shared domain guard is mandatory; use explicit K09 constraints as well.
 values=validate_model_parameters(m,vals,DOMAIN,model_id=id)
 binary=m['numeric_domain']=='BINARY64'
 if binary:values={k:float(z) for k,z in values.items()}
 result={r['name']:ast(r['expr'],values,binary) for r in m['formulas']}
 need(all(math.isfinite(float(z)) for z in result.values()))
 models[id]=dict(record_sha256=dig(m),numeric_domain=m['numeric_domain'],values={k:str(v) if isinstance(v,Q) else v for k,v in vals.items()})
 return {k:round(v,12) if binary else str(v) for k,v in result.items()}
def evaluate(im,mode,x,used,models):
 try:
  if not isinstance(x,dict):return 'HOLD'
  if mode=='bkt':
   need(x['model_version']==V and x['independent'] is True and x['construct_match'] is True and type(x['correct']) is bool and x['transition']=='NO_FORGETTING_AFTER_OBSERVATION')
   return model(im,'K10.BKT.'+('CORRECT' if x['correct'] else 'INCORRECT'),{k:x[k] for k in ('p','s','g','t')},used,models)
  if mode=='hlr':
   need(x['model_version']==V and x['unit']=='day' and x['fixed_model'] is True)
   return model(im,'K10.HLR.FIXED',{k:x[k] for k in ('half_life','lag')},used,models)
  if mode=='ctt':
   for id in ('K09.01.01.ME.01','K09.02.03.ME.01','K09.02.04.ME.01','K16.05.02.TG.01','K19.01.03.TG.01'):claim(im,id,used)
   a,b=x['group_scores'];need(isinstance(a,list) and isinstance(b,list) and a and b)
   delta=sum(map(num,a))/len(a)-sum(map(num,b))/len(b)
   result=dict(reliability='UNKNOWN',sem_squared='UNKNOWN',interpretation='UNSUPPORTED',group_difference=str(delta),bias='UNKNOWN',ability='UNKNOWN')
   if not all(x.get(k) is True for k in ('same_population','same_scale','error_uncorrelated','zero_mean_error')) or x.get('construct')!='FRACTION_MAGNITUDE':return result
   t,e,sd=[num(x[k]) for k in ('true_var','error_var','sd')];need(t>=0 and e>=0 and t+e>0 and sd>=0 and sd**2==t+e)
   rr=model(im,'K09.02.02.MODEL.01',dict(true_var=x['true_var'],error_var=x['error_var']),used,models)
   rel=Q(rr['reliability'])
   sem=model(im,'K09.03.04.MODEL.01',dict(sd=x['sd'],r=rel),used,models)
   expect=sd**2*(1-rel);need(math.isclose(sem['sem']**2,float(expect),abs_tol=1e-9,rel_tol=1e-9))
   return dict(result,reliability=str(rel),sem_squared=str(expect),interpretation='CTT_CONDITIONAL_ONLY')
  if mode=='research':
   for id in ('K17.03.02.SR.01','K17.06.03.SR.01','K19.05.01.TG.01'):claim(im,id,used)
   if x['design']=='CORRELATION_ONLY':
    need(-1<=num(x['r'])<=1);return dict(causal='UNKNOWN',transport='UNKNOWN')
   need(x['design']=='OBSERVATIONAL' and x['confounder']=='PRIOR_SKILL' and x['measured_before_exposure'] is True)
   rows=x['strata'];need(isinstance(rows,list) and len(rows)==2 and [r['id'] for r in rows]==['HIGH','LOW'])
   w=[num(z) for z in x['target_strata_weights']];need(len(w)==2 and sum(w)==1 and min(w)>=0)
   diff=[];sc=st=nc=nt=0
   for r in rows:
    a,b=map(nat,r['treated']);c,d=map(nat,r['control']);need(0<b and 0<d and a<=b and c<=d)
    sc+=c;st+=a;nc+=d;nt+=b;diff.append(Q(a,b)-Q(c,d))
   return dict(crude_difference=str(Q(st,nt)-Q(sc,nc)),stratum_differences=list(map(str,diff)),standardized_association=str(sum(a*b for a,b in zip(w,diff))),causal='UNKNOWN',transport='UNKNOWN')
  if mode=='plan':
   if x.get('exit') is True:return 'STOP'
   if x.get('permission') is False:return 'REFUSE'
   need(x.get('exit') is False and x.get('permission') is True and x.get('state_version')=='S1' and x.get('goal')=='CONFIRMATION' and x.get('estimate_status')=='BOUNDED')
   for id in ('K11.01.03.R2.09','K11.02.04.TR.01','K11.05.04.TR.01'):claim(im,id,used)
   budget=nat(x['budget']);opts=x['options'];need(isinstance(opts,list) and 0<len(opts)<=8)
   reasons={};costs={}
   for z in opts:
    i=z['id'];need(type(i)is str and i and i==i.strip() and i not in reasons);costs[i]=nat(z['cost'])
    if z['goal']!=x['goal']:r='GOAL_MISMATCH'
    elif any(z.get(k) is False for k in ('construct_preserved','accessible','authorized')):r='CONDITION_REJECTED'
    elif not all(z.get(k) is True for k in ('construct_preserved','accessible','authorized')):r='UNKNOWN_CONDITION'
    elif costs[i]>budget:r='OVER_BUDGET'
    else:r='ELIGIBLE'
    reasons[i]=r
   selected=x.get('learner_selection')
   if not isinstance(selected,str) or reasons.get(selected)!='ELIGIBLE':return 'HOLD'
   # Reuse the actual registered P08 FlowSpec and companion on the same candidates.
   flow=record(im,'P08','FlowSpec','P08.FLOW')
   inp=dict(exit=False,budget=budget,goal=x['goal'],authorized=True,estimate_status=x['estimate_status'],learner_selection=selected,options=opts)
   got=p.evaluate(im,flow,inp,'P08',load_record)
   need(got=={'status':'CANDIDATE_SELECTED_NOT_EXECUTED','id':selected})
   return dict(decision='REVIEW_PLAN_ONLY',selected=selected,cost=costs[selected],remaining=budget-costs[selected],alternatives=reasons,state_version=x['state_version'])
  if mode=='channels':
   for id in ('K09.01.01.ME.01','K10.02.01.TR.01'):claim(im,id,used)
   a=x['response'];key=x['key'];hint=x['hint_used'];elapsed=x['elapsed'];sr=x['self_report'];need(type(hint)is bool and key in ('CONFIRM','DISCONFIRM'))
   need(a is None or a in ('CONFIRM','DISCONFIRM'));need(sr is None or type(sr)is str and bool(sr))
   need((a is None and elapsed is None) or (a is not None and nat(elapsed)>=0))
   score=None if a is None else int(a==key)
   inp=dict(expected_scoring_version='S1',response=dict(status='MISSING') if a is None else dict(status='OBSERVED',value=a,task_version='T1'),score=dict(status='MISSING') if score is None else dict(status='OBSERVED',value=score,scoring_version='S1',denominator=1),self_report=dict(status='MISSING') if sr is None else dict(status='OBSERVED',value=sr,respondent='LEARNER'),estimate=dict(status='NOT_RUN'))
   fc=record(im,'F05','CompositionSpec','F05.COMPOSITION')
   for r in fc['input_refs']+fc['output_refs']+fc['claim_refs']+fc['condition_refs']:load_record(im,r)
   result=f.f05(inp);need(isinstance(result,dict) and result['combined_mastery']=='NOT_INFERRED')
   need(result['channels']['estimate']['status']=='NOT_ESTIMATED')
   return dict(response=a,score=score,assistance='UNKNOWN' if a is None else 'ASSISTED' if hint else 'INDEPENDENT_FIXTURE',elapsed=elapsed,self_report=sr,estimate='NOT_ESTIMATED',mastery='UNKNOWN')
  return 'HOLD'
 except (ValueError,TypeError,KeyError,ZeroDivisionError,OverflowError,IndexError):return 'HOLD'
def main():
 ts={t['id']:t for t in load(ROOT/'docs/implementation/task-dag.json')['tasks']}
 cat={}
 # Administrative manifest assembly outside any per-subject route.
 for mp in sorted(B.glob('*/*manifest.json')):
  m=load(mp);k=(m.get('package_id'),m.get('version'))
  if None not in k:cat[k]=ManifestPin(mp.relative_to(ROOT).as_posix(),sha(mp))
 for o,b in ASSEMBLY['bindings'].items():
  t=ts[o];pp=ROOT/t['current_receipt'];r=load(pp);assert t['current_receipt']==b['receipt_path'] and sha(pp)==b['receipt_sha256'] and r['content_digest']==b['content_digest']
  for z in r['output']:assert sha(ROOT/z['path'])==z['sha256']
  if t.get('qualification_receipt'):
   qp=ROOT/t['qualification_receipt'];assert sha(qp)==b['qualification_sha256'] and load(qp)['reviewed_content_digest']==r['content_digest']
  assert cat[tuple(b['package'])].sha256==b['manifest_sha256']
 ext=B/'foundation-r3/relation-types.json';im=Importer(ROOT,mode='research',catalog=cat,extension=ManifestPin(ext.relative_to(ROOT).as_posix(),sha(ext)))
 try:
  for k in ASSEMBLY['roots']:im._load(tuple(k),set())
  links={k:im._validate_refs(k) for k in im.packages}
  for k,v in links.items():im._materialize(k,v)
  fixtures=load(HERE/'fixtures.json')['cases'];cases=list(fixtures)
  variants={
   'CQ06.BKT.C':[('assisted',{'independent':False},'HOLD'),('missing_match',{'construct_match':None},'HOLD'),('bool',{'p':True},'HOLD'),('out_of_range',{'g':1.1},'HOLD'),('zero_likelihood',{'p':0,'g':0},'HOLD'),('wrong_model',{'model_version':'OLD'},'HOLD'),('wrong_transition',{'transition':'FORGETTING'},'HOLD')],
   'CQ06.HLR':[('zero_h',{'half_life':0},'HOLD'),('negative_lag',{'lag':-1},'HOLD'),('wrong_unit',{'unit':'hour'},'HOLD'),('not_fixed',{'fixed_model':False},'HOLD')],
   'CQ09.CTT':[('bad_variance',{'error_var':-1},'HOLD'),('wrong_sd',{'sd':3},'HOLD'),('zero_total',{'sd':0,'true_var':0,'error_var':0},'HOLD')],
   'CQ10.CONFOUND':[('no_preexposure',{'measured_before_exposure':False},'HOLD'),('invalid_weight',{'target_strata_weights':[1,1]},'HOLD'),('duplicate_strata',{'strata':[{'id':'HIGH','treated':[8,10],'control':[72,90]}]*2},'HOLD')],
   'CQ07.CHOICE':[('overbudget',{'budget':1},'HOLD'),('unknown_goal',{'goal':None},'HOLD'),('wrong_choice',{'learner_selection':'B'},'HOLD'),('unknown_state',{'state_version':None},'HOLD'),('unknown_estimate',{'estimate_status':'UNKNOWN'},'HOLD'),('exit',{'exit':True},'STOP'),('denied',{'permission':False},'REFUSE')],
   'CQ05.CHANNELS':[('invalid_elapsed',{'elapsed':-1},'HOLD'),('wrong_hint',{'hint_used':1},'HOLD'),('invalid_answer',{'response':'OTHER'},'HOLD')]}
  for c in fixtures:
   for n,patch,e in variants.get(c['id'],[]):cases.append(dict(id=c['id']+'.'+n,mode=c['mode'],input=dict(c['input'],**patch),expected=e,derivation='Explicit negative contract: '+n))
  out=[]
  for c in cases:
   used={};models={};v=evaluate(im,c['mode'],c['input'],used,models)
   assert v==c['expected'],(c['id'],v,c['expected'])
   out.append(c|dict(actual=v,input_sha256=dig(c['input']),claim_bindings=used,model_bindings=models))
  assert all(c.execute('PRAGMA query_only').fetchone()==(1,) and not c.execute('PRAGMA foreign_key_check').fetchall() and all(not v[2] for v in c.execute('PRAGMA database_list')) for c in im.connections.values())
  report=dict(status='AUTHOR_EXECUTED_FINITE_WITNESS_NOT_FULL_CQ_OR_INDEPENDENT_ORACLE',registered_head=ASSEMBLY['registration_head'],assembly_sha256=sha(HERE.parent/'v01-current-projection/current-assembly-results.json'),fixture_sha256=sha(HERE/'fixtures.json'),cases=out,case_count=len(out),packages=len(im.connections),records=sum(len(z[3]) for z in im.packages.values()),typed_refs=sum(map(len,links.values())),persistent_sqlite=False)
 finally:im.close()
 (HERE/'results.json').write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n')
 print('CQ MODEL EVIDENCE',len(out),'cases',report['packages'],report['records'],report['typed_refs'])
if __name__=='__main__':main()
