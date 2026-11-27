"""Restricted dependency use: exact local SQL records, no inferred canonical edge."""
import json,hashlib,sys
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[2];sys.path.insert(0,str(ROOT))
from tools.knowledge_import.importer import Importer,ManifestPin
from tools.knowledge_import.v00_prototype import load_record
B=ROOT/'knowledge/v0.1.0'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dig(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
# Each pair is a local candidate use, not external empirical evidence.
# The boolean facts are explicit synthetic inputs, not classifier outputs.
PAIRS=[
 ('K10','K02.06.01.D4.02','K10.01.02.TR.01','辅助与独立复测隔离','hint_absent','INDEPENDENT_RECORD','ASSISTED_ONLY'),
 ('K10','K09.01.04.ME.01','K10.01.05.TR.01','缺答不是错误','valid_response','OBSERVE_RESPONSE','NO_UPDATE'),
 ('K11','K05.02.04.PT.01','K11.02.04.TR.01','日程建议先查目标期限及预算','within_budget','ADVICE_CANDIDATE','DEFER'),
 ('K11','K08.04.02.PT.01','K11.01.03.TR.01','计划不能改写本人目标','goal_confirmed','ADVICE_CANDIDATE','HOLD'),
 ('K11','K10.03.01.TR.01','K11.02.02.TR.01','模型概率不等于最优复习间隔','same_model_unit','MODEL_THRESHOLD_ONLY','HOLD'),
 ('K12','K03.06.02.D4.02','K12.01.02.TR.01','任务规格匹配构念与响应','same_construct','TASK_CANDIDATE','SEPARATE_CONSTRUCT'),
 ('K12','K06.03.01.PT.01','K12.03.03.TR.01','提示前后分别保存','hint_absent','INDEPENDENT_RECORD','ASSISTED_ONLY'),
 ('K12','K09.01.04.ME.01','K12.06.01.TR.01','评分合同版本精确匹配','same_scoring_version','SCORING_CANDIDATE','HOLD'),
 ('K15','K06.03.01.PT.01','K15.02.04.TG.01','辅导提示不等于独立表现','hint_absent','INDEPENDENT_RECORD','ASSISTED_ONLY'),
 ('K15','K09.01.04.ME.01','K15.03.02.TG.01','指标分母与缺失规则明确','denominator_defined','INDICATOR_CANDIDATE','HOLD'),
 ('K16','K02.05.04.D4.02','K16.01.01.TG.01','先备证据不得以身份补值','individual_evidence','SUPPORT_CANDIDATE','HOLD'),
 ('K16','K13.02.03.SR.01','K16.03.04.TG.01','语言适配不得改变构念','same_construct','SUPPORT_CANDIDATE','SEPARATE_CONSTRUCT'),
 ('K19','K13.04.02.SR.01','K19.01.01.TG.01','机会障碍与能力分开','access_observed','OPPORTUNITY_OBSERVATION','HOLD'),
 ('K19','K17.02.02.SR.01','K19.04.05.TG.01','分配记录不替代权限与审查','human_authorized','DESIGN_REVIEW_ONLY','HOLD'),
]
PACK={**{f'K{i:02}':'foundation-r3' for i in range(1,5)},**{f'K{i:02}':'practice-teaching-r10' for i in range(5,9)},'K09':'measurement-r4',**{f'K{i:02}':'trace-adaptation-resources-r1' for i in range(10,13)},'K13':'social-research-r2','K17':'social-research-r2','K14':'domain-development-r2','K18':'domain-development-r2',**{k:'technology-inclusion-governance-r1' for k in ('K15','K16','K19')}}
def main():
 dag=load(ROOT/'docs/implementation/task-dag.json');tasks={t['id']:t for t in dag['tasks']}
 wanted=set([v for x in PAIRS for v in x[1:3]])
 records={};bindings={};ims={}
 try:
  for n in sorted({PACK[x.split('.')[0]] for x in wanted}):
   p=B/n;m=load(p/'learning-core.manifest.json');v=m['version']
   cat={(k,v):ManifestPin((p/(k+'.manifest.json')).relative_to(ROOT).as_posix(),sha(p/(k+'.manifest.json'))) for k in ('learning-core','evidence')}
   im=Importer(mode='research',catalog=cat,extension=ManifestPin((p/'relation-types.json').relative_to(ROOT).as_posix(),sha(p/'relation-types.json')) if n=='foundation-r3' else None);ims[n]=im;im.run(('learning-core',v))
   for f in m['files']:
    fp=p/f['path'];assert sha(fp)==f['sha256']
    for l in fp.read_text().splitlines():
     r=json.loads(l);id=r['stable_id']
     if id not in wanted:continue
     assert id not in records and r['kind']=='Claim' and r['status']=='CANDIDATE'
     assert r['claim_type'] in ('PROJECT_RULE','ENGINEERING_POLICY','ORIGINAL_METHOD_DERIVATION'),(id,r['claim_type'])
     ref={k:r[k] for k in ('kind','owner','stable_id')};ref.update(package_id='learning-core',version=v)
     sql=load_record(im,ref);assert sql['statement']==r['statement'] and sql['conditions']==r['conditions'] and sql['negative_boundary']==r['negative_boundary']
     records[id]=r
     bindings[id]={'ref':ref,'record_sha256':dig(r),'file':str(fp.relative_to(ROOT)),'file_sha256':sha(fp),'manifest_sha256':sha(p/'learning-core.manifest.json'),'statement':sql['statement'],'conditions':sql['conditions'],'negative_boundary':sql['negative_boundary']}
  assert set(records)==wanted
  results=[]
  for i,(k,up,local,meaning,field,yes,no) in enumerate(PAIRS,1):
   assert up.split('.')[0] in tasks[k]['depends_on'] and local.startswith(k+'.')
   # This is a deliberately tiny authored condition-to-action adapter, not a general inference engine.
   for label,value,expected in [('positive',True,yes),('negative',False,no),('unknown',None,'HOLD'),('malformed',1,'HOLD')]:
    inp={field:value}
    v=inp.get(field);actual=yes if v is True else no if v is False else 'HOLD'
    assert actual==expected
    results.append({'id':f'D{i:02}-{label}','owner':k,'upstream':up,'local':local,'intent':meaning,'input':inp,'expected':expected,'actual':actual,'status':'BUILDER_ONLY'})
  write(P/'dependency-witness.json',{'status':'BOUNDED_BUILDER_DEPENDENCY_USE_NOT_SEMANTIC_CLOSURE','pairs':len(PAIRS),'bindings':bindings,'results':results,'limits':'Explicit boolean synthetic guards, independently reviewed professional applicability still pending. No empirical inference, source qualification, canonical relation, or CQ/LC.'})
  print('dependency pairs',len(PAIRS),'bound records',len(bindings),'finite guards',len(results))
 finally:
  for im in ims.values():im.close()
if __name__=='__main__':main()
