"""Finite consumer of exact SQL Case, Claim, Composition, Policy and Condition records."""
import json, hashlib
from fractions import Fraction as F
from check_models import P,ROOT,PREP,load,sha,need,nat,num,Importer,ManifestPin,load_record as load_fields
V='0.1.0-measurement-candidate-2'
def load_record(im,r):
 out=load_fields(im,r);key=(r['package_id'],r['version'])
 z=im.connections[key].execute('SELECT stable_id,status FROM local_registry WHERE package_id=? AND version=? AND stable_id=? AND kind=? AND owner=?',(*key,r['stable_id'],r['kind'],r['owner'])).fetchone()
 need(z is not None)
 return out|{'stable_id':z[0],'status':z[1]}

def ref(kind,id):return dict(kind=kind,stable_id=id,owner='K09',package_id='learning-core',version=V)
def compute(op,x):
 if op=='score':
  s,m=x['scores'],x['max'];p=x['policy']
  valid=len(s)==len(m)>0 and p in ('EXCLUDE_MISSING','ZERO_MISSING') and all(type(v) is int and v>0 for v in m) and all(v is None or type(v) is int and 0<=v<=t for v,t in zip(s,m))
  denominator=sum(t for v,t in zip(s,m) if v is not None or p=='ZERO_MISSING') if valid else 0
  return ({'score':str(F(sum(v for v in s if v is not None),denominator)),'missing':s.count(None)} if denominator else 'HOLD'),{'scoring_inputs_valid':bool(denominator)}
 if op=='ordinal':
  a,b=x['x'],x['y'];return {'preserves_order':all((a[j]>a[i])==(b[j]>b[i]) and (a[j]==a[i])==(b[j]==b[i]) for i in range(len(a)) for j in range(len(a))), 'preserves_equal_gaps':all((a[j]-a[i]==a[l]-a[k])==(b[j]-b[i]==b[l]-b[k]) for i in range(len(a)) for j in range(i+1,len(a)) for k in range(len(a)) for l in range(k+1,len(a)))},{}
 if op=='total':
  a,b=x['a'],x['b'];return {'a':sum(a),'b':sum(b),'same_pattern':a==b},{}
 if op=='rasch_mle':
  c,n=x['correct'],x['total'];need(type(c) is int and type(n) is int and 0<=c<=n and n>0)
  return ('NO_FINITE_UNCONSTRAINED_MLE' if c in (0,n) else 'OUTSIDE_FIXTURE_SCOPE'),{}
 if op=='q_signature':
  q,a,b=x['q'],x['a'],x['b'];need(len(a)==len(b)>0 and all(len(r)==len(a) and any(r) for r in q))
  sig=lambda v:[int(all(not z or w for z,w in zip(r,v))) for r in q]
  sa,sb=sig(a),sig(b);return {'a':sa,'b':sb,'distinguishable':sa!=sb},{}
 if op=='cat_select':
  items=x['items'];need(len({i['id'] for i in items})==len(items) and all(type(i['eligible']) is bool and num(i['info'])>=0 for i in items))
  eligible=[i for i in items if i['eligible']]
  if not eligible:return 'NO_ELIGIBLE_ITEM',{'eligible_candidate_exists':False,'no_eligible_candidate':True}
  best=max(num(i['info']) for i in eligible);w=[i['id'] for i in eligible if num(i['info'])==best]
  need(len(w)==1)
  return w[0],{'eligible_candidate_exists':True,'no_eligible_candidate':False}
 if op=='cat_stop':
  c,m=x['count'],x['maximum'];se,t=num(x['se']),num(x['target']);co=x['content_complete']
  need(type(c) is int and type(m) is int and 0<=c<=m and m>0 and se>=0 and t>0 and type(co) is bool)
  limit=c==m;precision=se<=t;met=precision and co
  result='STOP_CRITERIA_MET' if met else ('STOP_LIMIT_PRECISION_NOT_MET' if not precision else 'STOP_LIMIT_CONTENT_NOT_MET') if limit else 'CONTINUE_CONTENT' if not co else 'CONTINUE_PRECISION'
  return result,{'limit_reached':limit,'precision_and_content_met':met,'continue_needed':not(limit or met)}
 if op=='kappa':
  a,b=x['table'];need(len(a)==len(b)==2 and all(type(v) is int and v>=0 for v in a+b))
  n=sum(a+b);need(n>0);po=F(a[0]+b[1],n);pe=F(sum(a)*(a[0]+b[0])+sum(b)*(a[1]+b[1]),n*n)
  return {'po':str(po),'pe':str(pe),'kappa':str((po-pe)/(1-pe)) if pe!=1 else 'UNDEFINED'},{}
 raise ValueError(op)
def decide(im,comp,flags):
 pol=load_record(im,comp['output_refs'][0]);need(pol['effect']=='ADVICE_ONLY')
 for r in sorted(pol['rules'],key=lambda v:v['priority']):
  c=load_record(im,r['condition_ref']);need(c['combination']=='ALL' and c['unknown']=='HOLD')
  vals=[]
  for z in c['clauses']:
   need(z['op']=='EQ' and z['value'] is True)
   v=flags.get(z['field'])
   vals.append(v if type(v) is bool else None)
  if None in vals:return pol['unknown_action']
  if all(vals):return r['action']
 return pol['unknown_action']
def main():
 cat={(pkg,V):ManifestPin((P/(pkg+'.manifest.json')).relative_to(ROOT).as_posix(),sha(P/(pkg+'.manifest.json'))) for pkg in ('learning-core','evidence')}
 im=Importer(mode='research',catalog=cat)
 try:
  im.run(('learning-core',V));fs=load(PREP/'finite-fixtures.json');rr=load(P/'model-representation-results.json');covered={r['ordinal'] for r in rr['results']}
  assert len(covered)==22
  review=load(ROOT/'evidence/validation/KR02-R6-K09-FINITE-01.json');g=next(x for x in review['groups'] if x['fixture']==(PREP/'finite-fixtures.json').relative_to(ROOT).as_posix())
  assert g['fixture_sha256']==sha(PREP/'finite-fixtures.json') and g['result_sha256']==sha(PREP/'finite-results.json')
  comps={}
  for d in load(P/'decision-design.json'):
   comp=load_record(im,ref('CompositionSpec',d['id']))
   for j in d['ordinals']:comps[j]=comp
  out=[]
  for i,f in enumerate(fs):
   if i in covered:continue
   case=load_record(im,ref('Case',f['topic']+'.ME.01.F'+str(i)))
   claim=load_record(im,case['target_refs'][0]);x=json.loads(case['input_spec'])
   assert x==f['input'] and claim['status']=='CANDIDATE' and case['actual_status']=='INDEPENDENTLY_CHECKED'
   result,flags=compute(f['op'],x);assert result==f['expected'],(i,result,f['expected'])
   row={'ordinal':i,'case_id':case['stable_id'],'claim_id':claim['stable_id'],'actual':result,'expected':f['expected'],'status':'PASS_BUILDER_SQL_CASE_CONSUMPTION'}
   if i in comps:
    c=comps[i];assert any(r['stable_id']==case['stable_id'] for r in c['evidence_refs'])
    action=decide(im,c,flags);expected='CLARIFY' if result=='HOLD' else 'STOP' if isinstance(result,str) and (result.startswith('STOP_') or result=='NO_ELIGIBLE_ITEM') else 'REQUEST_OBSERVATION' if isinstance(result,str) and result.startswith('CONTINUE_') else 'SUGGEST'
    assert action==expected,(i,action,expected)
    assert decide(im,c,{})=='CLARIFY'
    row.update(composition_id=c['stable_id'],derived_flags=flags,policy_action=action,missing_flags='CLARIFY')
   out.append(row)
  assert len(out)==16 and {r['ordinal'] for r in out}|covered==set(range(38))
  (P/'decision-representation-results.json').write_text(json.dumps({'status':'FINITE_SQL_CASE_AND_POLICY_CONSUMPTION_BUILDER_ONLY','fixture_sha256':g['fixture_sha256'],'previously_reviewed_fixtures':38,'model_cases':22,'other_cases':16,'policy_cases':sum('policy_action' in x for x in out),'results':out,'limits':'Explicit finite adapter reads actual typed records; no general scoring or CAT runtime, no model fit or independent assessment of new policy implementation.'},ensure_ascii=False,indent=2)+'\n')
  print('16 SQL case checks; 8 policy checks; total 38 frozen expectations exercised')
 finally:im.close()
if __name__=='__main__':main()
