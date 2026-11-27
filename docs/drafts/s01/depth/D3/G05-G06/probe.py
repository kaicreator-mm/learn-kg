"""Finite knowledge-contract probe, not a production runtime or authenticated service."""
import json, math, sys
from pathlib import Path
from copy import deepcopy

def positive(x): return type(x) in (int,float) and math.isfinite(x) and x>0
def nonnegative(x): return type(x) in (int,float) and math.isfinite(x) and x>=0
def scope(x): return tuple(x.get(k) for k in ("learner","subject","version","construct","component","rubric"))
def check_fixture_registry(reg):
    assert all(len(scope(t))==6 and all(scope(t)) for t in reg["tasks"].values())
    assert all(positive(p["min_delay"]) for p in reg["retention"].values())
    assert all(nonnegative(b["limit"]) for b in reg["budgets"].values())

def replay(reg,events):
    check_fixture_registry(reg)
    seen={}; closed_global=set();closed_subject=set();closed_session=set()
    budgets={k:v["limit"] for k,v in reg["budgets"].items()}
    observed={}; candidate_keys=set(); times={}; out=[]
    for e in events:
        actor=e.get("actor"); learner=e.get("learner"); g=reg["grants"].get(e.get("grant"))
        if not g or actor!=g["actor"] or learner!=g["learner"]:
            out.append("HOLD_ACTOR");continue
        t=e.get("type"); subj=e.get("subject");sess=e.get("session")
        if t=="EXIT":
            # A verified learner control request is independent of ordinary data event time,
            # task identity, remaining budget and processing grant. No inferred reactivation.
            level=e.get("level")
            if actor!=learner or g.get("control") is not True or level not in ("GLOBAL","SUBJECT","SESSION"):
                out.append("HOLD_EXIT_AUTH");continue
            if level=="SUBJECT" and subj not in g["subjects"]:
                out.append("HOLD_EXIT_SCOPE");continue
            if level=="SESSION" and (subj not in g["subjects"] or not sess):
                out.append("HOLD_EXIT_SCOPE");continue
            if level=="GLOBAL": closed_global.add(learner)
            elif level=="SUBJECT": closed_subject.add((learner,subj))
            else: closed_session.add((learner,subj,sess))
            out.append("EXITED");continue
        if learner in closed_global or (learner,subj) in closed_subject or (learner,subj,sess) in closed_session:
            out.append("HOLD_EXITED");continue
        if g.get("processing") is not True or subj not in g["subjects"] or t not in g["actions"]:
            out.append("HOLD_AUTH");continue
        tick=e.get("receipt_tick")
        if not nonnegative(tick) or not g["from"]<=tick<=g["until"]:
            out.append("HOLD_AUTH_TIME");continue
        id=e.get("id")
        if not isinstance(id,str) or not id:
            out.append("HOLD_ID");continue
        ek=(learner,actor,id)
        if ek in seen:
            out.append("DUPLICATE" if seen[ek]==e else "HOLD_CONFLICT");continue
        if tick<times.get((learner,actor),-1):
            out.append("HOLD_TIME_ORDER");continue
        if t=="PLAN":
            b=reg["budgets"].get(e.get("budget")); task=reg["tasks"].get(e.get("task"))
            if not b or (b["learner"],b["session"])!=(learner,sess) or not task or scope(e)!=scope(task):
                out.append("HOLD_SCOPE");continue
            if task.get("eligible") is not True or not positive(task.get("cost")):
                out.append("HOLD_FEASIBILITY");continue
            cost=task["cost"]
            if cost>budgets[e["budget"]]:
                out.append("HOLD_BUDGET");continue
            budgets[e["budget"]]-=cost; result="PLAN_CANDIDATE"
        elif t=="OBSERVE":
            task=reg["tasks"].get(e.get("task"))
            if not task or scope(e)!=scope(task) or task.get("eligible") is not True:
                out.append("HOLD_TASK");continue
            if e.get("item")!=task["item"] or e.get("family")!=task["family"]:
                out.append("HOLD_TASK_IDENTITY");continue
            if not nonnegative(e.get("observed_tick")) or e["observed_tick"]>tick:
                out.append("HOLD_OBSERVATION_TIME");continue
            if e.get("available") is not True:
                out.append("UNKNOWN_MISSING");continue
            if e.get("ambiguous") is not False or task.get("construct_preserved") is not True:
                out.append("HOLD_OBSERVATION");continue
            if e.get("result") not in ("CORRECT","INCORRECT") or e.get("assistance") not in ("NONE","HINT","TOOL"):
                out.append("HOLD_RESULT");continue
            observed[ek]=(deepcopy(e),task)
            result="INDEPENDENT" if e["assistance"]=="NONE" else "ASSISTED"
        elif t=="ASSESS":
            ref=e.get("observation")
            if not isinstance(ref,list) or len(ref)!=3 or not all(isinstance(x,str) for x in ref):
                out.append("HOLD_EVIDENCE");continue
            o=observed.get(tuple(ref))
            if not o or scope(o[0])!=scope(e):
                out.append("HOLD_EVIDENCE");continue
            if o[0]["assistance"]!="NONE":
                out.append("HOLD_ASSISTED");continue
            phase=e.get("phase")
            if phase=="RETENTION":
                prior=e.get("prior"); pol=reg["retention"].get(e.get("policy"))
                if not isinstance(prior,list) or len(prior)!=3 or not all(isinstance(x,str) for x in prior):
                    out.append("HOLD_BASELINE");continue
                p=observed.get(tuple(prior))
                if not p or scope(p[0])!=scope(e) or p[0]["assistance"]!="NONE" or p[0]["result"]!="CORRECT":
                    out.append("HOLD_BASELINE");continue
                if not pol or tuple(pol["scope"])!=scope(e):
                    out.append("HOLD_POLICY");continue
                if o[1]["family"]==p[1]["family"] or o[1]["item"]==p[1]["item"]:
                    out.append("HOLD_NOVELTY");continue
                if o[0]["observed_tick"]-p[0]["observed_tick"]<pol["min_delay"]:
                    out.append("UNKNOWN_DELAY");continue
                if (tuple(prior),tuple(ref),"RETENTION",e["policy"]) in candidate_keys:
                    out.append("DUPLICATE_CANDIDATE");continue
                candidate_keys.add((tuple(prior),tuple(ref),"RETENTION",e["policy"]))
                result="RETENTION_CANDIDATE"
            elif phase=="IMMEDIATE":
                ck=(tuple(ref),"IMMEDIATE")
                if ck in candidate_keys:
                    out.append("DUPLICATE_CANDIDATE");continue
                candidate_keys.add(ck);result="IMMEDIATE_CANDIDATE"
            else:
                out.append("HOLD_PHASE");continue
        else:
            out.append("HOLD_TYPE");continue
        seen[ek]=deepcopy(e);times[(learner,actor)]=tick;out.append(result)
    return {"steps":out,"remaining":budgets,"candidates":len(candidate_keys),"production_writes":0}

def content_gate(x):
    # Each check is a separate required receipt in a synthetic fixture.
    expected=x.get("content_digest")
    if not isinstance(expected,str) or not expected: return "HOLD_CONTENT_ID"
    checks=("fact","domain_language","rubric","source","rights","accessibility")
    receipts=x.get("receipts",{})
    if set(receipts)!=set(checks): return "HOLD_INCOMPLETE"
    for k in checks:
        r=receipts[k]
        if r.get("digest")!=expected or r.get("version")!=x.get("version") or r.get("review_role")!="QUALIFIED_REVIEWER":
            return "HOLD_RECEIPT_SCOPE"
        if r.get("decision")=="FAIL": return "REJECT_CANDIDATE"
        if r.get("decision")!="PASS": return "HOLD_UNKNOWN"
    if x.get("authorized") is not True: return "HOLD_AUTH"
    return "ELIGIBLE_FOR_SEPARATE_DELIVERY_REVIEW"

def improvement_gate(x):
    if x.get("authorized") is not True or x.get("ethics")!="CLEARED": return "HOLD_ETHICS_AUTH"
    if x.get("withdrawn") is True: return "STOP_AND_REVIEW"
    if x.get("protocol_version")!=x.get("evaluated_protocol") or x.get("candidate_version")!=x.get("tested_version"): return "HOLD_VERSION"
    if not (x.get("outcomes_prespecified") is True and x.get("comparison_appropriate") is True and x.get("attrition_assessed") is True and x.get("construct_comparable") is True):
        return "EXPLORATORY_ONLY"
    if x.get("safety_outcome")!="ACCEPTABLE": return "HOLD_OR_ROLLBACK"
    if x.get("outcome")=="NEGATIVE": return "KEEP_BASELINE"
    if x.get("outcome")!="SUPPORTED": return "HOLD_INCONCLUSIVE"
    if x.get("independent_review")!="ACCEPT_SCOPED": return "HOLD_REVIEW"
    if x.get("human_approval") is not True: return "HOLD_APPROVAL"
    return "ELIGIBLE_FOR_SEPARATE_RELEASE_DECISION"

def main():
    f=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).with_name("fixtures.json")
    d=json.loads(f.read_text());summary={}
    for name,fn in [("scope",lambda x:replay(d["registry"],x)),("content",content_gate),("improvement",improvement_gate)]:
        rows=d[name];results=[]
        for r in rows:
            a=fn(r["input"])
            if a!=r["expected"]:
                print(json.dumps({"id":r["id"],"actual":a,"expected":r["expected"]},ensure_ascii=False));raise SystemExit(1)
            results.append(r["id"])
        summary[name]={"cases":len(rows),"passed":len(results),"ids":results}
    summary["scope"]["steps"]=sum(len(r["input"]) for r in d["scope"])
    print(json.dumps({"status":"SYNTHETIC_PASS_ONLY","summary":summary,"production_writes":0,"oracle":"SAME_AUTHOR_FIXED_EXPECTATIONS"},ensure_ascii=False))
if __name__=="__main__":main()
