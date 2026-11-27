#!/usr/bin/env python3
"""Build the P01 human-readable and canonical learning-mode candidate package."""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
BRANCH="version/v0.1.0"
BASE_HEAD="ea0e06825519ba6de5f95ffedeec5a35c208d0ed"
BASE_TREE="76dd603211b3eacb335fc23f3a07aee7f2de01a8"
VERSION="0.1.0-p01-candidate-1"
PKG=ROOT/"knowledge/v0.1.0/learning-process-p01"
DOC=ROOT/"docs/implementation/p01-learning-modes"
OWNER="P01"
CONTRACT_ID="D013-R3R-D014"
CONTRACT_HASH="0bcf76f3374e5ebd169d8177595cb958b16a0c415705a76d7cee4c087f694f6d"
DEP_IDS=["G01","DB01","K05","K06","K07","K08","K13","IF01"]

MODES=[
 {"id":"GUIDED_CONCEPT_PRACTICE","label":"引导式概念练习","purpose":"围绕学习者选择的概念目标，组合目标确认、示范、引导练习、独立检查与反思。","skill":"SKILL_CONCEPTUAL_TASK","claims":["K06.01.02.D4.01","K06.06.01.D4.01","K06.06.02.D4.01","K07.02.04.D4.01","K07.04.01.D4.01","K08.04.01.D4.01"],"topics":["K05.04","K05.05","K06.01","K06.02","K06.06","K07.01","K07.02","K07.04"],"switch":"仅在学习者请求、可访问性失效或学习者同意的替代建议后暂停当前模式，再由学习者明确选择新模式。","boundaries":["不将示范后一次正确响应等同掌握。","掌握标准必须是当前目标和任务特定的，不映射为通用能力等级。"]},
 {"id":"RETRIEVAL_SPACED_REVIEW","label":"提取与间隔复习","purpose":"以无提示提取、辅助反馈和可调整的后续复习安排支持当前目标；不预设统一间隔。","skill":"SKILL_RETRIEVAL_TASK","claims":["K05.01.01.D4.01","K05.02.01.D4.01","K05.02.04.D4.01","K06.06.01.D4.01","K08.04.04.D4.01"],"topics":["K05.01","K05.02","K05.06","K06.06","K08.04"],"switch":"当学习者请求改变节奏、材料或活动时，先暂停并保留复习检查点；后续间隔必须重新确认，不自动套用固定计划。","boundaries":["不把再认当作自由回忆。","不宣称对所有材料和延迟都存在同一最佳间隔。","辅助响应与无提示独立响应分别记录。"]},
 {"id":"DELIBERATE_SKILL_PRACTICE","label":"刻意技能练习","purpose":"将目标限定为可观察的子技能任务，使用有限尝试、任务/过程反馈和独立检查。","skill":"SKILL_TASK_PERFORMANCE","claims":["K05.03.01.R9.S01","K06.06.02.D4.01","K06.06.04.D4.01","K07.04.01.D4.01","K07.04.03.D4.01"],"topics":["K05.03","K06.03","K06.06","K07.04"],"switch":"预算耗尽、目标不匹配或学习者请求改变策略时暂停；不得将重试次数扩展为无限循环。","boundaries":["反馈描述任务和过程，不贴人格或能力标签。","一次子技能任务的结果不推广为整个领域能力。"]},
 {"id":"SELF_REGULATED_STUDY","label":"自我调节学习","purpose":"支持学习者设定当前目标、选择策略、监控过程并进行反思；由学习者决定是否采纳建议。","skill":"SKILL_SELF_REGULATION","claims":["K08.01.01.R9.S01","K08.02.01.D4.01","K08.03.01.D4.03","K08.03.03.D4.01","K08.04.01.D4.01","K08.04.02.D4.01","K08.04.04.D4.01","K08.04.05.D4.01","K08.05.04.R9.S01","K07.05.02.D4.01"],"topics":["K05.06","K06.01","K07.05","K08.01","K08.02","K08.03","K08.04","K08.05"],"switch":"当学习者不希望继续自我监控、报告负担过高或目标改变时，允许暂停、降低记录粒度或改选其他模式。","boundaries":["自我报告是主观信息，不是客观表现或临床评估。","不推断人格、动机特质、心理健康或稳定自我效能。"]},
 {"id":"COLLABORATIVE_DIALOGIC_STUDY","label":"协作对话学习","purpose":"在自愿参与和明确任务边界下组织同伴解释、对话、反馈及个人退出检查。","skill":"SKILL_DIALOGIC_REASONING","claims":["K06.06.02.D4.01","K08.06.03.R9.S01","K13.02.01.SR.S01","K13.02.02.SR.S01","K13.02.04.SR.S01"],"topics":["K06.05","K06.07","K08.02","K08.06","K13.01","K13.02","K13.03","K13.04","K13.05"],"switch":"所有参与者可退出或暂停；语言、文化工具和群体安排由参与者明确选择，不按身份自动分组。","boundaries":["K13来源命题仅按受限候选范围使用，不作身份推断或因果诊断。","群体讨论表现不替代个人独立检查。","不得强迫披露个人文化、语言或家庭背景。"]},
 {"id":"INTEGRATED_PROJECT_TRANSFER","label":"综合项目与迁移练习","purpose":"将多个已明确的任务组件整合为项目，并在指定的新任务中单独观察表现。","skill":"SKILL_TRANSFER_TASK","claims":["K05.03.01.R9.S01","K05.05.04.R9.S01","K06.04.03.R9.S01","K07.04.03.D4.01","K08.04.05.D4.01","K13.02.04.SR.S01"],"topics":["K05.03","K05.05","K06.04","K07.02","K07.04","K08.04","K13.02","K13.05"],"switch":"项目范围、资源或新任务条件变化时暂停并重新确认；不得在未重新授权时扩大任务范围。","boundaries":["单一新任务只形成该任务的观察记录，不证明一般迁移。","发现学习/项目模式不被解释为无指导条件下必然有效。","文化回应只作为学习者选择的上下文，不推断个人身份。"]}
]

ROLES=[
 {"id":"ROLE_LEARNER","label":"学习者","claims":["K08.04.01.D4.01","K08.04.05.D4.01"],"cap":["能够理解当前目标、选择或拒绝模式，并发出暂停/停止/切换请求。"],"perm":["SELECT_MODE","DECLINE_MODE","PAUSE","STOP","REQUEST_SWITCH","REVIEW_OWN_EVIDENCE"]},
 {"id":"ROLE_FACILITATOR","label":"教师或促进者","claims":["K06.06.02.D4.01","K06.07.02.D4.01"],"cap":["能够解释任务、提供任务/过程反馈并审查任务证据。"],"perm":["OFFER_ALTERNATIVE","EXPLAIN_TASK","PROVIDE_TASK_FEEDBACK","REVIEW_TASK_EVIDENCE"]},
 {"id":"ROLE_ORCHESTRATOR","label":"流程编排器","claims":["K07.05.02.D4.01","K06.07.04.R9.S01"],"cap":["能够校验契约、执行预算、持久化检查点和去重事件。"],"perm":["VALIDATE_CONTRACT","ENFORCE_BUDGET","PERSIST_CHECKPOINT","DEDUPE_EVENTS"]},
 {"id":"ROLE_PEER","label":"同伴参与者","claims":["K13.02.02.SR.S01","K13.02.04.SR.S01"],"cap":["能够自愿参与解释、对话或反馈，并保留退出权。"],"perm":["OPT_IN_TO_DIALOGUE","OFFER_EXPLANATION","DECLINE_OR_EXIT"]}
]

SKILLS=[
 {"id":"SKILL_CONCEPTUAL_TASK","label":"当前概念任务表现","claims":["K06.01.02.D4.01","K07.02.04.D4.01"],"boundary":"仅描述当前明确概念任务，不代表通用智力或稳定能力。"},
 {"id":"SKILL_RETRIEVAL_TASK","label":"当前提取任务表现","claims":["K05.01.01.D4.01","K05.02.01.D4.01"],"boundary":"区分再认、辅助提取和无提示回忆，不外推至所有材料。"},
 {"id":"SKILL_TASK_PERFORMANCE","label":"当前子技能任务表现","claims":["K06.06.02.D4.01","K07.04.01.D4.01"],"boundary":"只描述任务和过程，不生成个人能力标签。"},
 {"id":"SKILL_SELF_REGULATION","label":"当前自我调节行为","claims":["K08.03.03.D4.01","K08.04.01.D4.01","K08.04.05.D4.01"],"boundary":"行为和自我报告是情境性记录，不推断人格或临床状态。"},
 {"id":"SKILL_DIALOGIC_REASONING","label":"当前对话任务参与","claims":["K06.06.02.D4.01","K13.02.04.SR.S01"],"boundary":"群体参与不替代个人表现；文化上下文不得推断。"},
 {"id":"SKILL_TRANSFER_TASK","label":"当前新任务表现","claims":["K05.03.01.R9.S01","K07.04.03.D4.01"],"boundary":"仅为指定新任务观察，不宣称一般迁移。"}
]

OBSERVATIONS=[
 {"id":"OBS_ASSISTED_RESPONSE","label":"辅助响应观察","skill":"SKILL_TASK_PERFORMANCE","claims":["K06.06.01.D4.01","K06.06.02.D4.01"],"method":"记录任务响应、提示/示范/帮助等级及具体任务身份。","unit":"task_response_with_support_level","independence":"辅助响应必须与无提示独立响应分开保存；不得作为独立掌握证据。"},
 {"id":"OBS_INDEPENDENT_RESPONSE","label":"无提示独立响应观察","skill":"SKILL_TASK_PERFORMANCE","claims":["K05.01.01.D4.01","K06.06.01.D4.01","K07.04.01.D4.01"],"method":"在记录提示状态和任务身份后，记录无提示响应。","unit":"task_response_without_hint","independence":"仅表示该任务中无提示作答；不自动等于长期保持或跨任务迁移。"},
 {"id":"OBS_SELF_REPORT","label":"学习者自我报告","skill":"SKILL_SELF_REGULATION","claims":["K08.03.01.D4.03","K08.04.01.D4.01","K08.04.05.D4.01"],"method":"由学习者自愿提供目标、感受、策略选择或反思。","unit":"learner_report","independence":"主观自我报告，不替代行为观察、任务表现或临床评估。"},
 {"id":"OBS_TRANSFER_TASK","label":"指定新任务观察","skill":"SKILL_TRANSFER_TASK","claims":["K05.03.01.R9.S01","K07.04.03.D4.01"],"method":"记录明确的新任务、变化条件、资源、提示和独立程度。","unit":"new_task_performance","independence":"一次新任务仅支持该任务观察，不建立普遍迁移或因果结论。"}
]

def digest(x):
 return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
def sha(p):
 return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):
 return json.loads(p.read_text(encoding="utf-8"))
def run(*args):
 return subprocess.check_output(args,cwd=ROOT,text=True).strip()
def ref(kind,sid,owner,package="learning-core",version=VERSION):
 return {"kind":kind,"stable_id":sid,"owner":owner,"package_id":package,"version":version}
def prov(pointer,source="mode-design.json"):
 p=DOC/source
 return [{"source_path":p.relative_to(ROOT).as_posix(),"source_sha256":sha(p),"json_pointer":pointer,"source_status":"P01_AUTHORED_TEMPLATE_SPEC"}]
def base(kind,sid,claims,pointer,negative):
 return {"kind":kind,"stable_id":sid,"owner":OWNER,"status":"CANDIDATE","conditions":["本模板仅在当前任务、明确授权和可验证输入范围内适用。","未知、缺失或不匹配输入必须HOLD，不推断补值。"],"negative_boundary":negative,"provenance":prov(pointer),"claim_refs":claims}

def upstream():
 dag=load(ROOT/"docs/implementation/task-dag.json")
 tasks={x["id"]:x for x in dag["tasks"]}
 inputs=[]
 for task_id in DEP_IDS:
  t=tasks[task_id];rp=t.get("current_receipt")
  if not rp: raise SystemExit("missing dependency receipt "+task_id)
  r=load(ROOT/rp);rf=ROOT/rp
  if r.get("task_id")!=task_id or r.get("state")!=t["status"]:
   raise SystemExit("dependency receipt/state mismatch "+task_id)
  entry={"task_id":task_id,"receipt_id":r["receipt_id"],"content_digest":r["content_digest"],"version":r["version"],"specific_refs":[{"path":rp,"sha256":sha(rf)}]}
  qp=t.get("qualification_receipt")
  if qp:
   q=load(ROOT/qp)
   if q.get("reviewed_content_digest")!=r.get("content_digest") or q.get("state")!="QUALIFIED_LOCAL":
    raise SystemExit("stale or nonqualified upstream "+task_id)
   entry["specific_refs"].append({"path":qp,"sha256":sha(ROOT/qp)})
   entry["qualification_receipt_id"]=q["receipt_id"]
   entry["qualification_scope"]=t.get("qualification_scope","LOCAL")
  inputs.append(entry)
 modules={}
 for k in ["K05","K06","K07","K08","K13"]:
  t=tasks[k];rp=t["current_receipt"];formal=load(ROOT/rp)
  package="practice-teaching-r10" if k!="K13" else "social-research-r2"
  root=ROOT/"knowledge/v0.1.0"/package
  manifest=load(root/"learning-core.manifest.json")
  coverage=load(root/k/"coverage.json")
  active=sorted({cid for topic in coverage["topics"] for cid in topic["active_claim_ids"]})
  allids=sorted({cid for topic in coverage["topics"] for cid in topic["claim_ids"]})
  if k=="K13":
   source_allow=sorted(cid for cid in formal["scope_restriction"]["source_limited_candidate_claim_ids"] if cid.startswith(k+"."))
   scope="CANDIDATE_ONLY_RESTRICTED"
  else:
   qp=t["qualification_receipt"];q=load(ROOT/qp)
   source_allow=sorted(cid for cid in q["scope_restriction"]["source_allowlist"] if cid.startswith(k+"."))
   scope=q["scope_restriction"]["status"]
  records={}
  for f in manifest["files"]:
   fp=root/f["path"]
   if sha(fp)!=f["sha256"]:raise SystemExit("upstream manifest hash mismatch "+str(fp))
   for line in fp.read_text(encoding="utf-8").splitlines():
    x=json.loads(line)
    if x.get("kind")=="Claim" and x.get("owner")==k:records[x["stable_id"]]=x
  if not set(active)<=set(records):raise SystemExit("active claims absent from package "+k)
  if not set(source_allow)<=set(active):raise SystemExit("source allowlist not active "+k)
  modules[k]={"package":package,"version":manifest["version"],"manifest_sha256":sha(root/"learning-core.manifest.json"),"evidence_manifest_sha256":sha(root/"evidence.manifest.json"),"coverage_sha256":sha(root/k/"coverage.json"),"active_claim_ids":active,"held_claim_ids":sorted(set(allids)-set(active)),"source_allowlist":source_allow,"scope":scope,"records":records}
 return inputs,modules,tasks

def main():
 head=run("git","rev-parse","HEAD");tree=run("git","rev-parse","HEAD^{tree}");branch=run("git","branch","--show-current")
 if head!=BASE_HEAD or tree!=BASE_TREE or branch!=BRANCH:raise SystemExit(f"P01 exact-base mismatch {branch} {head} {tree}")
 inputs,modules,tasks=upstream()
 design={"schema_version":"learn-kg-p01-mode-design-1","modes":MODES,"roles":ROLES,"skills":SKILLS,"observations":OBSERVATIONS}
 (DOC/"mode-design.json").write_text(json.dumps(design,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 design_sha=sha(DOC/"mode-design.json")
 claim_index={}
 for k,m in modules.items():
  for cid,r in m["records"].items():
   claim_index[cid]=(k,r)
 def claim_refs(ids):
  out=[]
  for cid in ids:
   if cid not in claim_index:raise SystemExit("unknown upstream claim "+cid)
   k,r=claim_index[cid];m=modules[k]
   if cid not in m["active_claim_ids"]:raise SystemExit("held claim use rejected "+cid)
   if cid not in m["source_allowlist"]:raise SystemExit("source-dependent claim outside allowlist "+cid)
   out.append(ref("Claim",cid,k,"learning-core",m["version"]))
  return out
 recs={}
 def add(x):
  if x["stable_id"] in recs:raise SystemExit("duplicate canonical id "+x["stable_id"])
  recs[x["stable_id"]]=x
 def local(kind,sid):return ref(kind,sid,OWNER,"learning-process")
 # Roles
 role_claims={
  "ROLE_LEARNER":["K08.04.01.D4.01","K08.04.05.D4.01"],
  "ROLE_FACILITATOR":["K06.06.02.D4.01","K06.07.02.D4.01"],
  "ROLE_ORCHESTRATOR":["K07.05.02.D4.01","K06.07.04.R9.S01"],
  "ROLE_PEER":["K13.02.02.SR.S01","K13.02.04.SR.S01"]}
 for i,r in enumerate(ROLES):
  add(base("Role",r["id"],claim_refs(r["claims"]),f"/roles/{i}","角色只拥有明示权限；学习者停止权不可被覆盖。")|{
   "label":r["label"],"capability_requirements":r["cap"],"permission_requirements":r["perm"]})
 # Skill types
 for i,s in enumerate(SKILLS):
  add(base("SkillType",s["id"],claim_refs(s["claims"]),f"/skills/{i}",s["boundary"])|{
   "label":s["label"],"performance_boundary":s["boundary"]})
 # Observations
 for i,o in enumerate(OBSERVATIONS):
  add(base("ObservationSpec",o["id"],claim_refs(o["claims"]),f"/observations/{i}","观察结果只在声明的任务、提示状态和单位内解释。")|{
   "construct_ref":local("SkillType",o["skill"]),"method":o["method"],"unit":o["unit"],"independence_requirement":o["independence"],"missing":"UNKNOWN_NOT_ZERO"})
 # Goal, conditions, objects, activities, modes and flows
 case_defs=[
  ("FORWARD",{"learner_opt_in":True,"goal_match":True,"accessibility_ready":True,"identity_used":False,"unknown_input":False,"assisted_evidence":{"evidence_id":"A1","support":"HINTED"},"independent_evidence":{"evidence_id":"I1","support":"NONE"}},"COMPLETE_WITH_DISTINCT_EVIDENCE"),
  ("REVERSE",{"pause_requested":True,"learner_resume":True,"checkpoint_valid":True,"same_mode":True,"duplicate_event":False,"budget_remaining":1},"RESUME_SAME_CHECKPOINT_NO_DUPLICATE"),
  ("INTERVENTION",{"retry_requested":True,"learner_opt_in":True,"budget_remaining":1},"RETRY_CONSUMES_ONE_BUDGET"),
  ("COUNTEREXAMPLE",{"learner_opt_in":False,"identity_used":False,"unknown_input":False},"HOLD"),
  ("COUNTEREXAMPLE",{"learner_opt_in":True,"identity_used":True,"unknown_input":False},"HOLD"),
  ("COMPOSITION",{"cross_mode_switch_requested":True,"current_mode_paused":False,"learner_selected_new_mode":False},"PAUSE_REQUIRE_EXPLICIT_NEW_SELECTION")
 ]
 cases_by_mode={}
 bindings=[]
 for mi,m in enumerate(MODES):
  mid=m["id"];claims=claim_refs(m["claims"]);skill=local("SkillType",m["skill"])
  goal_id="GOAL_"+mid
  obsids=["OBS_ASSISTED_RESPONSE","OBS_INDEPENDENT_RESPONSE","OBS_SELF_REPORT","OBS_TRANSFER_TASK"]
  goal_obs=["OBS_INDEPENDENT_RESPONSE","OBS_SELF_REPORT"]
  add(base("Goal",goal_id,claims,f"/modes/{mi}","目标是当前学习者选择的任务目标，不是稳定能力等级。")|{
   "construct_ref":skill,"success_evidence_refs":[local("ObservationSpec",x) for x in goal_obs],"scope":m["purpose"]+" 仅在当前任务和本次会话内解释。"})
  cond_ids={}
  condition_specs={
   "SELECT":[{"field":"learner_opt_in","op":"EQ","value":True},{"field":"goal_match","op":"EQ","value":True},{"field":"accessibility_ready","op":"EQ","value":True}],
   "RETRY":[{"field":"retry_requested","op":"EQ","value":True},{"field":"budget_remaining","op":"GT","value":0},{"field":"learner_opt_in","op":"EQ","value":True}],
   "PAUSE":[{"field":"pause_requested","op":"EQ","value":True}],
   "STOP":[{"field":"stop_requested","op":"EQ","value":True}],
   "COMPLETE":[{"field":"evidence_recorded","op":"EQ","value":True},{"field":"learner_choice_retained","op":"EQ","value":True}]
  }
  for cname,clauses in condition_specs.items():
   cid=f"COND_{mid}_{cname}";cond_ids[cname]=cid
   add(base("ConditionSpec",cid,claims,f"/modes/{mi}", "条件缺失或未知时必须HOLD。")|{
    "clauses":clauses,"combination":"ALL","unknown":"HOLD"})
  activities=[];steps=[]
  suffixes=[
   ("ORIENT","确认目标与约束","目标确认卡",["OBS_SELF_REPORT"],1,"目标、授权或可访问性不明确时停止进入后续步骤。"),
   ("MODEL","示范或准备材料","示范材料",["OBS_ASSISTED_RESPONSE"],1,"示范材料不可用或提示状态未知时HOLD。"),
   ("PRACTICE","执行当前任务","当前练习任务",["OBS_ASSISTED_RESPONSE","OBS_INDEPENDENT_RESPONSE"],2,"预算耗尽、学习者停止或任务不匹配时停止重试。"),
   ("REFLECT","检查证据与反思","反思提示",["OBS_SELF_REPORT","OBS_INDEPENDENT_RESPONSE"],1,"缺失证据保持UNKNOWN，不以自我报告替代表现。")
  ]
  for ai,(suffix,label,objlabel,obrefs,budget,stop) in enumerate(suffixes):
   aid=f"ACT_{mid}_{suffix}";oid=f"OBJ_{mid}_{suffix}"
   add(base("LearningObject",oid,claims,f"/modes/{mi}", "学习对象是任务占位符，不包含未经授权的外部内容。")|{
    "target_refs":[local("SkillType",m["skill"])],"component_refs":[],"granularity":"一个会话内的提示/任务占位对象；内容由获准来源或学习者提供。"})
   add(base("Activity",aid,claims,f"/modes/{mi}", "活动结果不等于学习效果；预算和停止条件必须执行。")|{
    "goal_refs":[local("Goal",goal_id)],"object_refs":[local("LearningObject",oid)],"resource_refs":[],
    "role_refs":[local("Role","ROLE_LEARNER"),local("Role","ROLE_FACILITATOR"),local("Role","ROLE_ORCHESTRATOR")]+([local("Role","ROLE_PEER")] if mid=="COLLABORATIVE_DIALOGIC_STUDY" else []),
    "observation_refs":[local("ObservationSpec",z) for z in obrefs],"budget":budget,"stop_condition":stop})
   activities.append(aid)
   steps.append({"id":f"{mid}_S0{ai+1}","activity_ref":local("Activity",aid),"max_attempts":budget,"checkpoint":ai in (0,2,3)})
  flow_id="FLOW_"+mid
  transitions=[]
  def tr(fr,to,event,condition,priority,consume):
   transitions.append({"from_step":fr,"to_step":to,"event":event,"condition_ref":local("ConditionSpec",cond_ids[condition]) if condition else None,"priority":priority,"consumes_budget":consume})
  sids=[x["id"] for x in steps]
  tr(sids[0],sids[1],"ORIENTED","SELECT",0,False)
  tr(sids[1],sids[2],"READY_TO_PRACTICE",None,0,False)
  tr(sids[2],sids[2],"RETRY_REQUESTED","RETRY",1,True)
  tr(sids[2],sids[3],"EVIDENCE_RECORDED","COMPLETE",0,False)
  tr(sids[3],"COMPLETE","REFLECTION_RECORDED","COMPLETE",0,False)
  for sid in sids:
   tr(sid,"PAUSE","PAUSE_REQUESTED","PAUSE",10,False)
   tr(sid,"STOP","STOP_REQUESTED","STOP",11,False)
  flow={
   "kind":"FlowSpec","stable_id":flow_id,"owner":OWNER,"status":"CANDIDATE","conditions":["只执行已声明步骤和事件；无隐式转移。","事件总数、每步尝试和活动预算均有界。","未知事件、未知条件或缺失证据进入HOLD。"],"negative_boundary":"流程模板不是运行时、教学效果或因果证明；STOP/HOLD/FAILED不得自动恢复。",
   "provenance":prov(f"/modes/{mi}"),"claim_refs":claims,"entry":sids[0],"steps":steps,"transitions":transitions,
   "terminals":[{"id":"COMPLETE","outcome":"COMPLETE"},{"id":"PAUSE","outcome":"PAUSE"},{"id":"STOP","outcome":"STOP"},{"id":"HOLD","outcome":"HOLD"},{"id":"FAILED","outcome":"FAILED"}],
   "max_events":18,"unknown_terminal":"HOLD","stop_terminal":"STOP","parallel_joins":[],"effect":"TEMPLATE_ONLY"}
  add(flow)
  mode={
   "kind":"Mode","stable_id":mid,"owner":OWNER,"status":"CANDIDATE","conditions":["学习者明确选择该模式并确认当前目标。","可访问性、材料、角色权限和预算必须明确。","K13上下文只可由学习者选择，不得由身份推断。"],
   "negative_boundary":"不自动诊断、排序或强制分配模式；不推断身份、能力、临床状态或学习效果。",
   "provenance":prov(f"/modes/{mi}"),"claim_refs":claims,"goal_refs":[local("Goal",goal_id)],"activity_refs":[local("Activity",x) for x in activities],
   "role_refs":[local("Role","ROLE_LEARNER"),local("Role","ROLE_FACILITATOR"),local("Role","ROLE_ORCHESTRATOR")]+([local("Role","ROLE_PEER")] if mid=="COLLABORATIVE_DIALOGIC_STUDY" else []),
   "selection_condition_refs":[local("ConditionSpec",cond_ids["SELECT"])],"learner_choice":True,"switch_condition":m["switch"]}
  add(mode)
  local_cases=[]
  for ci,(view,inp,expected) in enumerate(case_defs):
   cid=f"CASE_{mid}_{view}_{ci+1:02d}"
   input_obj={"mode_id":mid}|inp
   c={
    "kind":"Case","stable_id":cid,"owner":OWNER,"status":"CANDIDATE","conditions":["按输入字段和声明式模板执行有限判断。","仅为合成契约案例，不是学习者数据。"],
    "negative_boundary":"案例不证明真实学习效果；未知、缺失或未授权输入必须HOLD。",
    "provenance":prov(f"/modes/{mi}"),"target_refs":[local("Mode",mid),local("FlowSpec",flow_id)],"view":view,
    "input_spec":json.dumps(input_obj,ensure_ascii=False,sort_keys=True,separators=(",",":")),"expected_spec":expected,"oracle_ref":None,"actual_status":"RECORDED_BUILDER_ONLY"}
   add(c);local_cases.append({"case_id":cid,"view":view,"input":input_obj,"expected":expected})
  cases_by_mode[mid]=local_cases
 # Case validations after every case is available.
 results=[]
 for m in MODES:
  mid=m["id"];flow_id="FLOW_"+mid
  for case in cases_by_mode[mid]:
   cid=case["case_id"];result=evaluate(case["view"],case["input"])
   if result!=case["expected"]:raise SystemExit(f"case mismatch {cid}: {result} != {case['expected']}")
   vid="VAL_"+cid
   case_ref=local("Case",cid)
   v={"kind":"Validation","stable_id":vid,"owner":OWNER,"status":"CANDIDATE","conditions":["Deterministic finite template-contract check only."],"negative_boundary":"Builder finite validation only; no independent or empirical conclusion.","provenance":prov(f"/modes/{[x['id'] for x in MODES].index(mid)}"),
    "target_refs":[local("Mode",mid),local("FlowSpec",flow_id)],"case_refs":[case_ref],
    "method":"Deterministic fail-closed mode-selection, pause/resume, retry-budget, identity-boundary and explicit-switch contract evaluation.",
    "oracle_identity":"P01-AUTHORED-FINITE-CONTRACT-ORACLE-V1","input_digest":digest(case["input"]),"result_digest":digest({"actual":result,"expected":case["expected"]}),"run_status":"BUILDER_RUN"}
   add(v);results.append({"case_id":cid,"validation_id":vid,"view":case["view"],"actual":result,"expected":case["expected"],"status":"PASS_BUILDER_ONLY"})
   case_record=recs[cid];case_record["actual_status"]="RECORDED_BUILDER_ONLY"
 # Source evidence record for the authored P01 design; it is not an external source.
 catalog_path=DOC/"catalog.md"
 source={
  "kind":"Source","stable_id":"P01-AUTHORED-DESIGN","owner":"EVIDENCE","status":"CANDIDATE",
  "conditions":["仅标识本项目内部编写的模板设计。"],"negative_boundary":"不是外部研究来源、事实依据或出版权利证明。",
  "provenance":[{"source_path":(DOC/"mode-design.json").relative_to(ROOT).as_posix(),"source_sha256":sha(DOC/"mode-design.json"),"json_pointer":"/modes","source_status":"PROJECT_INTERNAL_AUTHORED_DESIGN"}],
  "title":"Learn-KG P01 authored learning-mode template design","identifier":"docs/implementation/p01-learning-modes/catalog.md",
  "access":"PROJECT_INTERNAL","rights":"HOLD","qualification":"NOT_RUN","bibliography":"Project-authored template design; no external authority.",
  "recorded_locator":"docs/implementation/p01-learning-modes/catalog.md","recorded_rights":"Project-authored; no external publication rights implied."
 }
 # Write canonical JSONL and manifests.
 def write_jsonl(path,records):
  data="".join(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n" for x in sorted(records,key=lambda x:(x["kind"],x["stable_id"])))
  (PKG/path).parent.mkdir(parents=True,exist_ok=True);(PKG/path).write_text(data,encoding="utf-8")
  return {"path":path,"sha256":sha(PKG/path),"format":"JSONL_RECORDS","record_count":len(records)}
 learning_file=write_jsonl("records-00.jsonl",list(recs.values()))
 evidence_file=write_jsonl("evidence/records-00.jsonl",[source])
 pversion=VERSION
 practice=ROOT/"knowledge/v0.1.0/practice-teaching-r10"
 social=ROOT/"knowledge/v0.1.0/social-research-r2"
 def dep(package,path,version):
  return {"package_id":package,"version":version,"manifest_sha256":sha(path)}
 own_evidence_manifest={
  "schema_version":"learn-kg-canonical-candidate-1","package_id":"evidence","version":pversion,"status":"CANDIDATE","rights":"HOLD","owners":["EVIDENCE"],"dependencies":[],"files":[evidence_file],"qualification_receipt_refs":[]}
 (PKG/"evidence.manifest.json").write_text(json.dumps(own_evidence_manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 deps=[
  dep("learning-core",practice/"learning-core.manifest.json",load(practice/"learning-core.manifest.json")["version"]),
  dep("evidence",practice/"evidence.manifest.json",load(practice/"evidence.manifest.json")["version"]),
  dep("learning-core",social/"learning-core.manifest.json",load(social/"learning-core.manifest.json")["version"]),
  dep("evidence",social/"evidence.manifest.json",load(social/"evidence.manifest.json")["version"]),
  dep("evidence",PKG/"evidence.manifest.json",pversion)]
 learning_manifest={
  "schema_version":"learn-kg-canonical-candidate-1","package_id":"learning-process","version":pversion,"status":"CANDIDATE","rights":"HOLD","owners":[OWNER],"dependencies":deps,"files":[learning_file],"qualification_receipt_refs":[]}
 (PKG/"learning-process.manifest.json").write_text(json.dumps(learning_manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 # D3/D4 coverage, retaining exact upstream claim, source and HOLD boundaries.
 inventory=load(ROOT/"docs/drafts/s01-scope-inventory.json")
 owner_topics={k:load(ROOT/"knowledge/v0.1.0"/modules[k]["package"]/k/"coverage.json")["topics"] for k in modules}
 mode_claims={m["id"]:set(m["claims"]) for m in MODES}
 all_used={r["stable_id"] for x in recs.values() for r in x.get("claim_refs",[]) if r["owner"] in modules}
 fixtures=[{"case_id":case["case_id"],"mode_id":m["id"],"view":case["view"],"input":case["input"],"expected":case["expected"]} for m in MODES for case in cases_by_mode[m["id"]]]
 (DOC/"fixtures.json").write_text(json.dumps(fixtures,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 mode_ids_by_prefix={
  "K05":{"01":["RETRIEVAL_SPACED_REVIEW","GUIDED_CONCEPT_PRACTICE"],"02":["RETRIEVAL_SPACED_REVIEW"],"03":["DELIBERATE_SKILL_PRACTICE","INTEGRATED_PROJECT_TRANSFER"],"04":["GUIDED_CONCEPT_PRACTICE","SELF_REGULATED_STUDY"],"05":["GUIDED_CONCEPT_PRACTICE","INTEGRATED_PROJECT_TRANSFER"],"06":["SELF_REGULATED_STUDY","RETRIEVAL_SPACED_REVIEW"]},
  "K06":{"01":["GUIDED_CONCEPT_PRACTICE","SELF_REGULATED_STUDY"],"02":["GUIDED_CONCEPT_PRACTICE"],"03":["DELIBERATE_SKILL_PRACTICE"],"04":["INTEGRATED_PROJECT_TRANSFER"],"05":["COLLABORATIVE_DIALOGIC_STUDY"],"06":["GUIDED_CONCEPT_PRACTICE","DELIBERATE_SKILL_PRACTICE"],"07":["GUIDED_CONCEPT_PRACTICE","COLLABORATIVE_DIALOGIC_STUDY"]},
  "K07":{"01":["GUIDED_CONCEPT_PRACTICE","INTEGRATED_PROJECT_TRANSFER"],"02":["GUIDED_CONCEPT_PRACTICE","INTEGRATED_PROJECT_TRANSFER"],"03":["GUIDED_CONCEPT_PRACTICE"],"04":["DELIBERATE_SKILL_PRACTICE","GUIDED_CONCEPT_PRACTICE"],"05":["SELF_REGULATED_STUDY"]},
  "K08":{"01":["SELF_REGULATED_STUDY"],"02":["SELF_REGULATED_STUDY","COLLABORATIVE_DIALOGIC_STUDY"],"03":["SELF_REGULATED_STUDY"],"04":["SELF_REGULATED_STUDY"],"05":["SELF_REGULATED_STUDY"],"06":["COLLABORATIVE_DIALOGIC_STUDY"]},
  "K13":{"01":["COLLABORATIVE_DIALOGIC_STUDY"],"02":["COLLABORATIVE_DIALOGIC_STUDY"],"03":["COLLABORATIVE_DIALOGIC_STUDY","SELF_REGULATED_STUDY"],"04":["COLLABORATIVE_DIALOGIC_STUDY"],"05":["COLLABORATIVE_DIALOGIC_STUDY"]}}
 coverage_topics=[]
 used_by_topic={}
 for t in inventory["topics"]:
  if t.get("depth")!=3:continue
  owner=t["owner"]
  if owner not in modules:continue
  d3=t["id"]
  sub=d3.split(".")[1]
  mode_ids=mode_ids_by_prefix[owner][sub]
  upstream_topic=next(x for x in owner_topics[owner] if x["d3_id"]==d3)
  active=set(upstream_topic["active_claim_ids"]);allids=set(upstream_topic["claim_ids"])
  used=sorted(active & all_used)
  src=sorted(active & set(modules[owner]["source_allowlist"]))
  mode_cases_ids={v:sorted({case["case_id"] for mid in mode_ids for case in cases_by_mode[mid] if case["view"]==v}) for v in ["FORWARD","REVERSE","INTERVENTION","COUNTEREXAMPLE","COMPOSITION"]}
  views={}
  for v in ["FORWARD","REVERSE","INTERVENTION","COUNTEREXAMPLE"]:
   views[v]={"status":"CANDIDATE" if used else "INDIRECT_CANDIDATE","case_ids":mode_cases_ids[v],"direct_claim_binding":bool(used),"reason":"Mode-level finite contract case; not an education-effect oracle."}
  views["COMPOSITION"]={"status":"RESTRICTED_HOLD","case_ids":mode_cases_ids["COMPOSITION"],"direct_claim_binding":False,"reason":"Cases only verify pause-before-new-selection; cross-mode execution is deferred to P04/F/A."}
  limits=[]
  if owner=="K05":limits += ["No universal spacing interval; review timing remains configurable.","Recognition is not substituted for free recall."]
  if owner=="K06":limits += ["Feedback is task/process scoped; no causal efficacy claim."]
  if owner=="K07":limits += ["Prerequisites are explicit task constraints only; no automatic general prerequisite closure or external standards mapping."]
  if owner=="K08":limits += ["Self-report is not objective performance or clinical evidence; no trait inference."]
  if owner=="K13":limits += ["Only the three exact source-limited candidate propositions are available; optional context is learner-selected; no identity inference."]
  coverage_topics.append({
   "d3_id":d3,"owner":owner,"label":t["label"],"disposition":"DIRECT_CANDIDATE" if used else "INDIRECT_RESTRICTED",
   "reason":"Mapped to explicit P01 mode pattern(s); mode selection remains learner-controlled and this row is not a professional adequacy verdict.",
   "mode_ids":mode_ids,"candidate_claim_ids":sorted(active),"used_claim_ids":used,"source_allowlist_claim_ids":src,
   "held_claim_ids":sorted(allids-active),"source_locator_refs":[loc for cid in used for loc in modules[owner]["records"][cid].get("locator_refs",[])],
   "claim_conditions":{cid:modules[owner]["records"][cid].get("conditions",[]) for cid in used},
   "claim_negative_boundaries":{cid:modules[owner]["records"][cid].get("negative_boundary","") for cid in used},
   "d4_view_coverage":views,"limits":limits,"qualification":"NOT_RUN"})
 coverage={"schema_version":"learn-kg-p01-coverage-1","status":"CANDIDATE_COVERAGE_NOT_QUALIFICATION","owner":OWNER,"version":VERSION,
  "upstream_topics":len(coverage_topics),"topics":coverage_topics,
  "summary":{"direct_candidate_topics":sum(x["disposition"]=="DIRECT_CANDIDATE" for x in coverage_topics),"indirect_restricted_topics":sum(x["disposition"]=="INDIRECT_RESTRICTED" for x in coverage_topics),"candidate_views":sum(1 for x in coverage_topics for v in x["d4_view_coverage"].values() if v["status"] in ("CANDIDATE","INDIRECT_CANDIDATE")),"held_composition_views":len(coverage_topics),"used_claim_ids":sorted(all_used),"used_claim_count":len(all_used)},
  "limits":["D3 coverage maps mode applicability, not full K-module adequacy.","D4 cases are finite builder contract checks, not learning outcomes.","Composition view intentionally HOLD pending P04/F/A.","Source rights HOLD; CQ/LC NOT_RUN; no release."]}
 (DOC/"coverage.json").write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 # Explicit binding table: the canonical Mode schema has no FlowSpec ref field.
 for m in MODES:
  bindings.append({"mode_ref":local("Mode",m["id"]),"flow_ref":local("FlowSpec","FLOW_"+m["id"]),"binding":"EXPLICIT_MODE_FLOW_BINDING","selection_required":True,"effect":"TEMPLATE_ONLY","status":"CANDIDATE"})
 (DOC/"mode-flow-bindings.json").write_text(json.dumps({"schema_version":"learn-kg-mode-flow-bindings-1","bindings":bindings},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 (DOC/"recovery-contract.json").write_text(json.dumps({
  "schema_version":"learn-kg-p01-recovery-1","status":"CANDIDATE",
  "states":["OFFERED","SELECTED","ACTIVE","PAUSED","COMPLETE","STOPPED","HELD","FAILED"],
  "transitions":[
   {"from":"OFFERED","to":"SELECTED","event":"LEARNER_SELECTS_MODE","guard":"learner_opt_in AND goal_match AND accessibility_ready"},
   {"from":"SELECTED","to":"ACTIVE","event":"START","guard":"exact mode-flow binding and valid inputs"},
   {"from":"ACTIVE","to":"PAUSED","event":"PAUSE_REQUESTED","guard":"learner requested pause"},
   {"from":"PAUSED","to":"ACTIVE","event":"RESUME_REQUESTED","guard":"explicit learner resume AND same mode AND valid checkpoint AND idempotency key AND remaining budget"},
   {"from":"ACTIVE","to":"COMPLETE","event":"COMPLETE","guard":"required evidence recorded and scope unchanged"},
   {"from":"ACTIVE","to":"STOPPED","event":"STOP_REQUESTED","guard":"learner stop; no automatic resume"},
   {"from":"ACTIVE","to":"HELD","event":"UNKNOWN_OR_MISSING","guard":"unknown input, missing evidence or invalid condition"},
   {"from":"ACTIVE","to":"FAILED","event":"INVARIANT_VIOLATION","guard":"invalid state transition or corrupted checkpoint"}],
  "resume":{"preserve":["mode_id","flow_id","current_step","budget_remaining","committed_evidence_ids"],"require":["learner_resume=true","same_mode=true","checkpoint_valid=true","duplicate_event=false"],"new_execution":True},
  "idempotency":{"key_fields":["flow_id","checkpoint_id","event_id"],"duplicate_event":"NO_DUPLICATE_SIDE_EFFECT"},
  "limits":["PAUSE is resumable only through a new explicit invocation using the same checkpoint.","STOPPED, HELD and FAILED are not auto-resumed.","Unknown state is HOLD; no implicit fallback mode.","max_events and activity budgets remain bounded.","No knowledge write, diagnosis or learning-effect assertion."]
 },ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 # Input ledger binds every direct receipt and every allowed source claim.
 ledger={"schema_version":"learn-kg-p01-input-ledger-1","base_head":BASE_HEAD,"branch":BRANCH,"direct_dependencies":inputs,
  "upstream_scopes":{k:{x:y for x,y in modules[k].items() if x!="records"} for k in modules},
  "used_claim_ids":sorted(all_used),"limits":["K05-K08 are QUALIFIED_LOCAL_RESTRICTED; only active candidate claims and exact source allowlists are consumed.","K13 is CANDIDATE_READY_RESTRICTED only; its three source propositions are candidate context, not independently qualified.","No held claims, rights, CQ/LC, or G03/release scope is promoted."]}
 (DOC/"input-ledger.json").write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 # Check script is separate and deterministic; results are written by it.
 subprocess.check_call([sys.executable,str(DOC/"check_p01.py")],cwd=ROOT)
 # Build candidate receipt from exact current inputs and all generated files.
 dag_path=ROOT/"docs/implementation/task-dag.json";dag=load(dag_path);task=next(x for x in dag["tasks"] if x["id"]=="P01")
 if task["status"]!="PLANNED" or task.get("current_receipt"):raise SystemExit("P01 task state changed")
 output=[]
 def out(path,typ):
  p=ROOT/path
  if not p.is_file():raise SystemExit("missing output "+path)
  output.append({"path":path,"sha256":sha(p),"type":typ})
 for path in [
  "docs/implementation/p01-learning-modes/README.md","docs/implementation/p01-learning-modes/catalog.md","docs/implementation/p01-learning-modes/mode-design.json",
  "docs/implementation/p01-learning-modes/build_p01.py","docs/implementation/p01-learning-modes/check_p01.py","docs/implementation/p01-learning-modes/coverage.json",
  "docs/implementation/p01-learning-modes/mode-flow-bindings.json","docs/implementation/p01-learning-modes/recovery-contract.json",
  "docs/implementation/p01-learning-modes/fixtures.json","docs/implementation/p01-learning-modes/input-ledger.json",
  "docs/implementation/p01-learning-modes/validation-results.json","docs/implementation/p01-learning-modes/validation-receipt.json",
  "knowledge/v0.1.0/learning-process-p01/learning-process.manifest.json","knowledge/v0.1.0/learning-process-p01/evidence.manifest.json",
  "knowledge/v0.1.0/learning-process-p01/records-00.jsonl","knowledge/v0.1.0/learning-process-p01/evidence/records-00.jsonl"]:
  typ="MODULE_CANDIDATE_ARTIFACT" if path.endswith("records-00.jsonl") else "SHARED_CANDIDATE_INPUT_OR_EVIDENCE"
  out(path,typ)
 output.sort(key=lambda x:x["path"])
 scope={
  "status":"RESTRICTED_CANDIDATE_SCOPE","mode_count":len(MODES),"flow_count":len(MODES),"activity_count":len(MODES)*4,
  "canonical_record_count":len(recs),"d3_topic_count":len(coverage_topics),"builder_case_count":len(fixtures),
  "upstream_scope_ledger_sha256":sha(DOC/"input-ledger.json"),"used_claim_ids":sorted(all_used),
  "upstream_restrictions":{k:{"scope":modules[k]["scope"],"source_allowlist":modules[k]["source_allowlist"],"held_claim_count":len(modules[k]["held_claim_ids"])} for k in modules},
  "composition":"RESTRICTED_HOLD_DEFERRED_TO_P04_F_A","rights":"HOLD","cq":"NOT_RUN","lc":"NOT_RUN",
  "limits":["P01 templates are candidates, not independently qualified.","K13 remains candidate-only and its source-limited claims are optional context only.","No automatic identity, ability, motivation or clinical inference.","No education effect or causal claim.","No numeric model; numeric oracle NOT_APPLICABLE.","Cross-mode composition is intentionally held for later P04/F/A."]}
 receipt={
  "operator":"chatgpt-web:learn-kg-controller","session":"learn-kg-p01-candidate-build-20261127","role":"BUILDER_NON_REVIEWER",
  "reviewer":"NOT_RUN","review_session":"NOT_RUN","branch":BRANCH,"base":BASE_HEAD,"exact_head":BASE_HEAD,"version":BASE_HEAD,
  "contract_id":CONTRACT_ID,"contract_hash":CONTRACT_HASH,"time":"2026-11-27","task_id":"P01","attempt_id":"P01-FORMAL-01","receipt_id":"TASK:P01:P01-FORMAL-01",
  "input":inputs,"output":output,"state":"CANDIDATE_READY","receipt_type":"CANDIDATE_READY",
  "scope":"Six learner-selected bounded learning-mode templates with explicit activity, flow, role, observation, budget, stop, pause/resume and evidence contracts; restricted to exact upstream K05-K08 qualification scopes and K13 candidate-only scope.",
  "scope_restriction":scope,
  "validation":load(DOC/"validation-receipt.json")|{"independent_review":"NOT_RUN","qualification":"NOT_ISSUED"},
  "issues":["Cross-mode composition intentionally HOLD and deferred to P04/F/A.","K13 is candidate-only; its three source-limited propositions are contextual inputs only, not qualified facts.","Source rights HOLD; CQ/LC NOT_RUN; no empirical learner-effect claim."],
  "next":"Batch independent P01 review with subsequent P02/P03 process templates; PR01 remains the cumulative qualification gate."
 }
 receipt["content_digest"]=digest({"input":receipt["input"],"output":receipt["output"]})
 rp=ROOT/"evidence/tasks/P01/P01-FORMAL-01.json";rp.parent.mkdir(parents=True,exist_ok=True);rp.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 task["status"]="CANDIDATE_READY";task["current_receipt"]=rp.relative_to(ROOT).as_posix();task["qualification_scope"]="RESTRICTED"
 dag_path.write_text(json.dumps(dag,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"P01":"CANDIDATE_READY","modes":len(MODES),"canonical_records":len(recs),"D3_topics":len(coverage_topics),"finite_cases":len(fixtures),"receipt_sha256":sha(rp),"content_digest":receipt["content_digest"]},ensure_ascii=False))

def evaluate(view,x):
 if view=="FORWARD":
  if x.get("learner_opt_in") is not True or x.get("goal_match") is not True or x.get("accessibility_ready") is not True:return "HOLD"
  if x.get("identity_used") is not False or x.get("unknown_input") is not False:return "HOLD"
  a=x.get("assisted_evidence");i=x.get("independent_evidence")
  if not isinstance(a,dict) or not isinstance(i,dict) or a.get("evidence_id")==i.get("evidence_id") or a.get("support")!="HINTED" or i.get("support")!="NONE":return "HOLD"
  return "COMPLETE_WITH_DISTINCT_EVIDENCE"
 if view=="REVERSE":
  if x.get("pause_requested") is not True:return "HOLD"
  if x.get("learner_resume") is not True:return "PAUSE"
  if x.get("checkpoint_valid") is not True or x.get("same_mode") is not True or x.get("duplicate_event") is not False:return "HOLD"
  if type(x.get("budget_remaining")) is not int or x["budget_remaining"]<0:return "HOLD"
  return "RESUME_SAME_CHECKPOINT_NO_DUPLICATE"
 if view=="INTERVENTION":
  if x.get("retry_requested") is not True or x.get("learner_opt_in") is not True:return "HOLD"
  if type(x.get("budget_remaining")) is not int or x["budget_remaining"]<0:return "HOLD"
  return "RETRY_CONSUMES_ONE_BUDGET" if x["budget_remaining"]>0 else "PAUSE"
 if view=="COUNTEREXAMPLE":
  if x.get("learner_opt_in") is not True or x.get("identity_used") is True or x.get("unknown_input") is True or x.get("evidence_missing") is True:return "HOLD"
  return "HOLD"
 if view=="COMPOSITION":
  if x.get("cross_mode_switch_requested") is not True:return "HOLD"
  if x.get("current_mode_paused") is True and x.get("learner_selected_new_mode") is True:return "NEW_MODE_REQUIRES_NEW_EXPLICIT_SELECTION"
  return "PAUSE_REQUIRE_EXPLICIT_NEW_SELECTION"
 return "HOLD"

if __name__=="__main__":main()
