"""Resolve exact declared prerequisite and candidate claim identities; no new qualified graph edges."""
import copy,hashlib,json,pathlib
P=pathlib.Path(__file__).resolve().parent
ROOT=P.parents[2]; F=P.parent/'foundation-r3'
def load(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x): return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def need(v,msg):
 if not v: raise ValueError(msg)
def index(d):
 m=load(d/'learning-core.manifest.json'); out={}
 for e in m['files']:
  f=d/e['path'];need(sha(f)==e['sha256'],'manifest shard')
  rows=[json.loads(l) for l in f.read_text().splitlines()];need(len(rows)==e['record_count'],'count')
  for x in rows:
   need(x['stable_id'] not in out,'duplicate')
   out[x['stable_id']]=(x,f,e)
 return m,out
lm,li=index(P);fm,fi=index(F)
w=load(P/'upstream-input-witness.json')['module_inputs']
d=load(P/'cross-input-design.json')
def resolve(x):
 o=x['owner'];u=x['upstream'].split('.')[0]
 need(o in w and u!=o,'owner')
 a=next((a for a in w[o] if a['task_id']==u),None);need(a is not None,'undeclared dependency')
 rref=a['specific_refs'][0];rp=ROOT/rref['path'];need(sha(rp)==rref['sha256'],'receipt hash')
 rr=load(rp);need(rr['content_digest']==a['content_digest'] and rr['version']==a['version'] and rr['receipt_id']==a['receipt_id'],'receipt tuple')
 qref=a['local_qualification_evidence'];qp=ROOT/qref['path'];need(sha(qp)==qref['sha256'],'qualification hash')
 qr=load(qp);need(qr['reviewed_content_digest']==a['content_digest'],'reviewed digest')
 need(x['local'] in li and x['upstream'] in fi,'unresolved')
 l,lf,le=li[x['local']];f,ff,fe=fi[x['upstream']]
 need(l['owner']==o and f['owner']==u and l['kind']==f['kind']=='Claim' and l['status']==f['status']=='CANDIDATE','claim endpoint')
 path=ff.relative_to(ROOT).as_posix()
 need(any(t['path']==path and t['sha256']==fe['sha256'] for t in rr['output']),'upstream not in formal output')
 return {'id':x['id'],'owner':o,'local':{'package_id':'learning-core','version':lm['version'],'kind':'Claim','stable_id':l['stable_id'],'owner':o,'record_sha256':digest(l),'path':lf.relative_to(ROOT).as_posix(),'file_sha256':le['sha256']},'upstream':{'package_id':'learning-core','version':fm['version'],'kind':'Claim','stable_id':f['stable_id'],'owner':u,'record_sha256':digest(f),'path':path,'file_sha256':fe['sha256'],'receipt':a},'use':x['use'],'boundary':x['boundary'],'status':'IDENTITY_AND_DECLARED_INPUT_VERIFIED_SEMANTIC_USE_PROPOSED'}
out=[resolve(x) for x in d['pairs']]
need({(x['owner'],x['upstream']['owner']) for x in out}=={(o,a['task_id']) for o,v in w.items() for a in v if a['task_id'].startswith('K')},'coverage of K inputs')
tests=[]
for key,patch in [('undeclared',{'upstream':'K03.03.02.R2.04'}),('missing',{'upstream':'K02.MISSING'}),('wrong_local',{'local':'K06.01.03.PT.01'}),('wrong_kind',{'upstream':'K02.06.04'})]:
 x=d['pairs'][0]|patch
 try:resolve(x)
 except (ValueError,KeyError) as e:tests.append({'probe':key,'result':'REJECTED','reason':str(e)})
 else:raise AssertionError(key)
result={'status':'BOUND_INPUT_IDENTITY_WITNESS_NOT_GRAPH_RELATION_OR_MODULE_QUALIFICATION','local_manifest_sha256':sha(P/'learning-core.manifest.json'),'upstream_manifest_sha256':sha(F/'learning-core.manifest.json'),'pairs':out,'negative_probes':tests,'limits':'Seven proposed semantic uses are bounded by declared prerequisites and exact current artifacts. No runtime graph relation, professional adequacy, causal inference or module receipt is issued. K08 has no K prerequisite. Remaining historical anchors stay HOLD.'}
(P/'cross-input-witness.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
print(len(out),'BOUND_INPUT_IDENTITY',len(tests),'NEGATIVE_REJECTED')
