#!/usr/bin/env python3
"""Exact-scope schema, reference, import and finite contract checks for P01."""
import hashlib,json,sys
from pathlib import Path
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));DOC=Path(__file__).resolve().parent
PKG=ROOT/"knowledge/v0.1.0/learning-process-p01";VERSION="0.1.0-p01-candidate-1";OWNER="P01"
def load(p):return json.loads(p.read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def refkey(r):return (r["package_id"],r["version"],r["kind"],r["owner"],r["stable_id"])
def walk(x,path):
 if not path:return [x] if x is not None else []
 k,*rest=path
 if k=="*":return [z for v in x for z in walk(v,rest)]
 return walk(x.get(k),rest) if isinstance(x,dict) and k in x else []
def main():
 schema=load(ROOT/"docs/implementation/db01/canonical.schema.json")
 validator=Draft202012Validator(schema)
 records=[]
 for line in (PKG/"records-00.jsonl").read_text(encoding="utf-8").splitlines():
  x=json.loads(line);validator.validate(x);records.append(x)
 evidence_records=[json.loads(line) for line in (PKG/"evidence/records-00.jsonl").read_text(encoding="utf-8").splitlines()]
 for x in evidence_records:validator.validate(x)
 local={refkey({"package_id":"learning-process","version":VERSION,"kind":x["kind"],"owner":x["owner"],"stable_id":x["stable_id"]}):x for x in records}
 if len(local)!=len(records):raise SystemExit("duplicate canonical identity")
 # Verify all typed refs against IF01 and exact local/upstream snapshots.
 iface=load(ROOT/"docs/implementation/if01/interface-contract.json")
 deps={}
 for package in ["practice-teaching-r10","social-research-r2"]:
  base=ROOT/"knowledge/v0.1.0"/package
  lm=load(base/"learning-core.manifest.json");em=load(base/"evidence.manifest.json")
  for manifest,kind in [(lm,"learning-core"),(em,"evidence")]:
   for f in manifest["files"]:
    fp=base/f["path"]
    if sha(fp)!=f["sha256"]:raise SystemExit("upstream manifest file hash mismatch "+str(fp))
    if kind=="learning-core":
     for line in fp.read_text(encoding="utf-8").splitlines():
      z=json.loads(line);deps[refkey({"package_id":"learning-core","version":manifest["version"],"kind":z["kind"],"owner":z["owner"],"stable_id":z["stable_id"]})]=z
 # local evidence identity is separate; no P01 record points to it.
 for x in records:
  for path,kinds in iface["endpoint_rules"].get(x["kind"],{}).items():
   for r in walk(x,path.split("/")):
    if r["kind"] not in kinds:raise SystemExit("IF01 endpoint kind mismatch "+x["stable_id"]+":"+path)
    key=refkey(r)
    target=local.get(key) or deps.get(key)
    if target is None:raise SystemExit("unresolved exact typed ref "+str(key))
    if target["kind"]!=r["kind"] or target["owner"]!=r["owner"]:raise SystemExit("typed ref identity mismatch")
    if target["status"]!="CANDIDATE":raise SystemExit("noncandidate upstream or local ref consumed")
 # Upstream source claim allowlist is checked from exact input ledger.
 ledger=load(DOC/"input-ledger.json")
 allowed=set(ledger["used_claim_ids"])
 for x in records:
  for r in x.get("claim_refs",[]):
   if r["owner"] in ("K05","K06","K07","K08","K13") and r["stable_id"] not in allowed:
    raise SystemExit("claim outside P01 upstream allowlist")
 # Mode/flow invariants.
 modes=[x for x in records if x["kind"]=="Mode"]
 flows={x["stable_id"]:x for x in records if x["kind"]=="FlowSpec"}
 activities={x["stable_id"]:x for x in records if x["kind"]=="Activity"}
 if len(modes)!=6 or len(flows)!=6 or len(activities)!=24:raise SystemExit("unexpected mode/flow/activity count")
 for m in modes:
  if m["learner_choice"] is not True:raise SystemExit("mode must remain learner-selected")
  flow_id="FLOW_"+m["stable_id"];f=flows[flow_id]
  if f["effect"]!="TEMPLATE_ONLY" or f["unknown_terminal"]!="HOLD" or f["stop_terminal"]!="STOP" or f["max_events"]>24:raise SystemExit("flow fail-closed/budget contract mismatch")
  step_ids={s["id"] for s in f["steps"]};terminal_ids={t["id"] for t in f["terminals"]}
  if f["entry"] not in step_ids:raise SystemExit("flow entry missing")
  if any(t["from_step"] not in step_ids or t["to_step"] not in step_ids|terminal_ids for t in f["transitions"]):raise SystemExit("flow transition endpoint missing")
  if {r["stable_id"] for r in m["activity_refs"]}!={s["activity_ref"]["stable_id"] for s in f["steps"]}:raise SystemExit("mode/flow activity set mismatch")
  for ar in m["activity_refs"]:
   a=activities[ar["stable_id"]]
   if a["budget"]<1 or not a["stop_condition"]:raise SystemExit("activity budget/stop guard missing")
 # Execute deterministic finite authored cases.
 results=[]
 for line in (PKG/"records-00.jsonl").read_text(encoding="utf-8").splitlines():
  x=json.loads(line)
  if x["kind"]!="Case":continue
  inp=json.loads(x["input_spec"]);view=x["view"]
  from build_p01 import evaluate
  actual=evaluate(view,inp);expected=x["expected_spec"]
  if actual!=expected:raise SystemExit(f"finite case mismatch {x['stable_id']}: {actual} != {expected}")
  results.append({"case_id":x["stable_id"],"view":view,"actual":actual,"expected":expected,"status":"PASS_BUILDER_ONLY"})
 if len(results)!=36:raise SystemExit("expected 36 finite cases")
 fixtures=load(DOC/"fixtures.json")
 if {x["case_id"] for x in fixtures}!={x["case_id"] for x in results}:raise SystemExit("fixture/Case identity mismatch")
 coverage=load(DOC/"coverage.json")
 if len(coverage["topics"])!=121:raise SystemExit("expected 121 D3 coverage rows")
 # Check exact Mode-to-Flow binding table; no invented Relation kind.
 bindings=load(DOC/"mode-flow-bindings.json")["bindings"]
 if len(bindings)!=6 or any(x["binding"]!="EXPLICIT_MODE_FLOW_BINDING" or x["effect"]!="TEMPLATE_ONLY" for x in bindings):raise SystemExit("mode-flow binding mismatch")
 for b in bindings:
  if refkey(b["mode_ref"]) not in local or refkey(b["flow_ref"]) not in local:raise SystemExit("mode-flow reference unresolved")
 # In-memory package import only; no persistent SQLite file.
 from tools.knowledge_import.importer import Importer,ManifestPin
 cat={}
 for package,version,base in [
  ("learning-process",VERSION,PKG),("evidence",VERSION,PKG),
  ("learning-core",load(ROOT/"knowledge/v0.1.0/practice-teaching-r10/learning-core.manifest.json")["version"],ROOT/"knowledge/v0.1.0/practice-teaching-r10"),
  ("evidence",load(ROOT/"knowledge/v0.1.0/practice-teaching-r10/evidence.manifest.json")["version"],ROOT/"knowledge/v0.1.0/practice-teaching-r10"),
  ("learning-core",load(ROOT/"knowledge/v0.1.0/social-research-r2/learning-core.manifest.json")["version"],ROOT/"knowledge/v0.1.0/social-research-r2"),
  ("evidence",load(ROOT/"knowledge/v0.1.0/social-research-r2/evidence.manifest.json")["version"],ROOT/"knowledge/v0.1.0/social-research-r2")]:
  mf=base/(package+".manifest.json")
  cat[(package,version)]=ManifestPin(mf.relative_to(ROOT).as_posix(),sha(mf))
 im=Importer(mode="research",catalog=cat)
 try:
  im.run(("learning-process",VERSION))
 finally:im.close()
 (DOC/"validation-results.json").write_text(json.dumps({"status":"BUILDER_P01_FINITE_AND_IMPORT_CHECK_ONLY","case_count":len(results),"results":results,"schema_valid_records":len(records),"typed_reference_checks":"PASS","mode_count":len(modes),"flow_count":len(flows),"activity_count":len(activities),"in_memory_import":"PASS","persistent_sqlite":"NOT_CREATED","numeric_models":"NONE","limits":"Builder-only synthetic contract checks; no independent oracle or learning-effect claim."},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 v={"status":"BUILDER_CANDIDATE_READY_NOT_QUALIFIED","canonical_records":len(records),"mode_count":len(modes),"flow_count":len(flows),"activity_count":len(activities),"d3_topics":len(load(DOC/"coverage.json")["topics"]),"finite_cases":len(results),"schema":"PASS","if01_typed_references":"PASS","in_memory_import":"PASS","persistent_sqlite":"NOT_CREATED","numeric_models":"NONE","independent_review":"NOT_RUN","qualification":"NOT_ISSUED","rights":"HOLD","cq":"NOT_RUN","lc":"NOT_RUN"}
 (DOC/"validation-receipt.json").write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(v,ensure_ascii=False))
if __name__=="__main__":main()
