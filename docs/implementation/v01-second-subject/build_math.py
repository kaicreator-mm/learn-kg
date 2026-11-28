"""Original mathematical slice in the existing canonical schema."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
PKG=ROOT/'knowledge/v0.1.0/other-subject-math-v01'
V='0.1.0-math-v01-candidate-1'
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 d=HERE/'design.json';design=json.loads(d.read_text());rows={}
 def ref(id,kind):return dict(package_id='other-subject',version=V,stable_id=id,kind=kind,owner='M01')
 def add(kind,id,pointer,**kw):
  r=dict(kind=kind,stable_id=id,owner='M01',status='CANDIDATE',conditions=['Original bounded mathematical construction; nonnegative integer numerators and positive integer denominators, finite fixture domain.'],negative_boundary='Not learner mastery, general proficiency, curriculum or approved release.',provenance=[dict(source_path=d.relative_to(ROOT).as_posix(),source_sha256=sha(d),json_pointer=pointer,source_status='PROJECT_AUTHORED_ORIGINAL_DERIVATION')],**kw)
  assert id not in rows;rows[id]=r;return ref(id,kind)
 t=add('Topic','M01.COMPARE','/claim',label='Fraction magnitude comparison',depth=1,parent_ref=None)
 q=add('Requirement','M01.RQ.COMPARE','/claim',topic_ref=t,scope='Exact integer cross-products for positive denominators',source_leads=[],coverage_status='FINITE_ORIGINAL_CANDIDATE_ONLY')
 cr=add('Claim','M01.CLAIM.COMPARE','/claim',topic_id=t['stable_id'],requirement_id=q['stable_id'],claim_type='MATHEMATICAL_DERIVATION',statement=design['claim']['statement']+' '+design['claim']['proof'],source_status='ORIGINAL_DERIVATION_PENDING_INDEPENDENT_REVIEW',locator_refs=[],case_refs=[],validation_refs=[],supersedes_refs=[],refinement_of=None)
 e=add('Element','M01.ELEMENT.COMPARE','/claim',topic_id=t['stable_id'],element_type='FRACTION_COMPARISON',label='Cross-product comparison',definition=design['claim']['proof'],claim_refs=[cr])
 sk=add('SkillType','M01.SKILL.COMPARE','/task',label='Fraction magnitude comparison',performance_boundary=design['task']['construct'],claim_refs=[cr])
 lo=add('LearningObject','M01.OBJECT.COMPARE','/task',granularity='FINITE_TASK_OBJECT',target_refs=[sk,e],component_refs=[],claim_refs=[cr])
 ob=add('ObservationSpec','M01.OBS.COMPARE','/task',construct_ref=sk,method='Record exact displayed pair, independent response, assistance, task and scoring versions; missing remains unknown.',unit='FINITE_TASK_RESPONSE',independence_requirement='Synthetic response only; independent flag stipulated, not actual verified person.',missing='UNKNOWN_NOT_ZERO',claim_refs=[cr])
 add('TaskSpec','M01.TASK.COMPARE','/task',construct_ref=sk,object_refs=[lo],observation_refs=[ob],prompt=design['task']['prompt'],scoring_spec=design['task']['scoring'],independence_requirement='Explicit assistance and separate variant; no general mastery.',claim_refs=[cr])
 PKG.mkdir(exist_ok=True)
 p=PKG/'M01.jsonl';p.write_text(''.join(canonical(r)+'\n' for r in rows.values()))
 m=dict(schema_version='learn-kg-canonical-candidate-1',package_id='other-subject',version=V,status='CANDIDATE',rights='HOLD',owners=['M01'],dependencies=[],files=[dict(path=p.name,sha256=sha(p),format='JSONL_RECORDS',record_count=len(rows))],qualification_receipt_refs=[])
 (PKG/'other-subject.manifest.json').write_text(json.dumps(m,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
 print('MATH',len(rows),sha(PKG/'other-subject.manifest.json'))
if __name__=='__main__':main()
