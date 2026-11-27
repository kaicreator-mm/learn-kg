"""Read actual SQL Case and policy/condition records for exact finite witnesses."""
import pathlib,sys,json,hashlib
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2];sys.path.insert(0,str(ROOT))
from tools.knowledge_import.importer import Importer,ManifestPin
from tools.knowledge_import.v00_prototype import load_record
from run_finite import gate
V='0.1.0-technology-inclusion-governance-candidate-1'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(k,i,o):return dict(kind=k,stable_id=i,owner=o,package_id='learning-core',version=V)
def flags(mode,x):
 f={}
 if mode=='adaptation':
  if type(x.get('confirmed_need')) is bool:f['need_confirmed']=x['confirmed_need']
  if x.get('confirmed_need') is True and type(x.get('authorized')) is bool:
   f['unauthorized']=not x['authorized']
   if x['authorized'] is True and type(x.get('construct_preserved')) is bool:
    f['construct_changed']=not x['construct_preserved']
    if x['construct_preserved'] and type(x.get('actual_access_verified')) is bool:f['support_verified']=x['actual_access_verified']
 elif mode=='decision':
  if type(x.get('withdrawn')) is bool:f['withdrawn']=x['withdrawn']
  if x.get('withdrawn') is False and type(x.get('high_risk')) is bool:
   f['high_risk']=x['high_risk']
   if not x['high_risk'] and type(x.get('authorized')) is bool:
    f['unauthorized']=not x['authorized']
    if x['authorized'] and type(x.get('evidence_matches')) is bool:f['advice_eligible']=x['evidence_matches']
 return f
def policy(im,mode,x):
 o='K16' if mode=='adaptation' else 'K19';c=load_record(im,ref('CompositionSpec',o+'.TG.COMP.01',o));p=load_record(im,c['output_refs'][0]);f=flags(mode,x)
 assert p['effect']=='ADVICE_ONLY'
 for r in sorted(p['rules'],key=lambda z:z['priority']):
  q=load_record(im,r['condition_ref']);assert q['combination']=='ALL' and q['unknown']=='HOLD'
  a=[]
  for z in q['clauses']:
   assert z['op']=='EQ' and type(z['value']) is bool
   if type(f.get(z['field'])) is not bool:return p['unknown_action']
   a.append(f[z['field']]==z['value'])
  if all(a):return r['action']
 return p['unknown_action']
def main():
 catalog={(p,V):ManifestPin((P/(p+'.manifest.json')).relative_to(ROOT).as_posix(),sha(P/(p+'.manifest.json'))) for p in ('learning-core','evidence')}
 im=Importer(mode='research',catalog=catalog)
 try:
  im.run(('learning-core',V));a=load(P/'finite-fixtures.json');r=load(P/'finite-results.json');assert r['fixture_sha256']==sha(P/'finite-fixtures.json')
  out=[]
  for i,f in enumerate(a):
   o=f['topic'].split('.')[0];c=load_record(im,ref('Case',f['topic']+'.TG.01.F'+str(i),o));x=json.loads(c['input_spec'])
   assert x==f['input'] and c['expected_spec']==f['expected'] and c['actual_status']=='RECORDED_BUILDER_ONLY'
   claim=load_record(im,c['target_refs'][0]);assert claim['topic_id']==f['topic']
   v=gate(f['mode'],x);assert v==f['expected']==r['results'][i]['actual']
   row=dict(id=f['id'],actual=v,status='PASS_SQL_CASE_CONSUMPTION')
   if f['mode'] in ('adaptation','decision'):
    p=policy(im,f['mode'],x);expected={'HOLD':'CLARIFY','CLARIFY':'CLARIFY','REFUSE':'REFUSE','SEPARATE_CONSTRUCT':'DEFER','SUGGEST_REVERSIBLE_SUPPORT_ONLY':'SUGGEST','STOP':'STOP','DEFER_TO_AUTHORIZED_HUMAN':'DEFER','SUGGEST_ONLY':'SUGGEST'}[v];assert p==expected,(f['id'],p,expected)
    row['policy_action']=p
   out.append(row)
  result=dict(status='BUILDER_SQL_CONSUMPTION_ONLY',case_count=len(out),policy_cases=sum('policy_action'in x for x in out),fixture_sha256=sha(P/'finite-fixtures.json'),manifest_sha256=sha(P/'learning-core.manifest.json'),results=out,limits='Finite synthetic project-policy witnesses only, not implementation security, statutory compliance, clinical, or real learning evidence.')
  (P/'consumption-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in result.items() if k!='results'})
 finally:im.close()
if __name__=='__main__':main()
