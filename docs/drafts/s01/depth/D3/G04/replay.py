"""G04 synthetic reference evaluator; not a learner model or production runtime."""
import json, sys, math
from pathlib import Path
from copy import deepcopy

IDENTITY=("learner","subject","knowledge_version","construct","component","rubric")
def key(x): return tuple(x.get(k) for k in IDENTITY)
def valid_identity(x): return all(isinstance(x.get(k),str) and x[k].strip() for k in IDENTITY)
def finite_number(x): return type(x) in (int,float) and math.isfinite(x)
def run(scenario):
    s={"seen":{}, "sessions":{}, "observations":{}, "exited":set(), "candidates":{}, "suggestions":[], "time":{}}
    results=[]
    def reply(code, **fields):
        return {"code":code, **fields}
    for e in scenario["events"]:
        eid=e.get("id")
        if not isinstance(eid,str) or not eid:
            results.append(reply("HOLD_EVENT_ID"));continue
        if eid in s["seen"]:
            results.append(reply("DUPLICATE" if s["seen"][eid]==e else "HOLD_EVENT_CONFLICT"));continue
        if not valid_identity(e):
            results.append(reply("HOLD_IDENTITY"));continue
        k=key(e); session=e.get("session"); sk=(k,session)
        if not isinstance(session,str) or not session:
            results.append(reply("HOLD_SESSION"));continue
        if e.get("authorized") is not True:
            results.append(reply("HOLD_AUTH"));continue
        if not finite_number(e.get("time")) or e["time"]<0:
            results.append(reply("HOLD_TIME"));continue
        if e["time"] < s["time"].get(k,-1):
            results.append(reply("HOLD_TIME_ORDER"));continue
        # Accepted event identifiers are immutable. Rejected ingress is not committed.
        s["seen"][eid]=deepcopy(e)
        s["time"][k]=e["time"]
        t=e.get("type")
        if t=="EXIT":
            s["exited"].add((e["learner"],e["subject"]))
            results.append(reply("EXITED"));continue
        if (e["learner"],e["subject"]) in s["exited"]:
            results.append(reply("HOLD_EXITED"));continue
        if t=="START":
            if sk in s["sessions"]:
                results.append(reply("HOLD_SESSION_EXISTS"));continue
            b=e.get("budget")
            if not finite_number(b) or b<0:
                results.append(reply("HOLD_BUDGET"));continue
            s["sessions"][sk]={"remaining":b,"closed":False}
            results.append(reply("STARTED",remaining=b));continue
        ss=s["sessions"].get(sk)
        if ss is None or ss["closed"]:
            results.append(reply("HOLD_SESSION"));continue
        if t=="END":
            ss["closed"]=True
            results.append(reply("ENDED"));continue
        if t=="PLAN":
            cost=e.get("cost")
            if e.get("feasible") is not True or not finite_number(cost) or cost<0:
                results.append(reply("HOLD_FEASIBILITY"));continue
            if cost>ss["remaining"]:
                results.append(reply("HOLD_BUDGET"));continue
            ss["remaining"]-=cost
            results.append(reply("PLAN_CANDIDATE",remaining=ss["remaining"]));continue
        if t=="MOTIVATE":
            if e.get("opt_in") is not True:
                results.append(reply("HOLD_MOTIVATION_CONSENT"));continue
            if e.get("strategy") not in ("OPTIONAL_REST","OFFER_HELP","PROCESS_FEEDBACK"):
                results.append(reply("HOLD_MOTIVATION_STRATEGY"));continue
            s["suggestions"].append(eid)
            results.append(reply("OPTIONAL_SUGGESTION"));continue
        if t=="OBSERVE":
            if e.get("available") is not True:
                results.append(reply("UNKNOWN_MISSING"));continue
            if e.get("ambiguous") is not False:
                results.append(reply("HOLD_AMBIGUOUS"));continue
            if e.get("construct_preserved") is not True:
                results.append(reply("HOLD_CONSTRUCT"));continue
            if not isinstance(e.get("task_version"),str) or not e["task_version"] or not isinstance(e.get("family"),str) or not e["family"]:
                results.append(reply("HOLD_TASK"));continue
            if e.get("result") not in ("CORRECT","INCORRECT"):
                results.append(reply("UNKNOWN_RESULT"));continue
            if e.get("assistance") not in ("NONE","HINT","DEMONSTRATION","TOOL"):
                results.append(reply("UNKNOWN_ASSISTANCE"));continue
            kind="INDEPENDENT" if e["assistance"]=="NONE" else "ASSISTED"
            s["observations"][eid]=(k,deepcopy(e),kind)
            results.append(reply(kind+"_OBSERVATION",result=e["result"]));continue
        if t=="FEEDBACK":
            o=s["observations"].get(e.get("observation"))
            if o is None or o[0]!=k:
                results.append(reply("HOLD_EVIDENCE"));continue
            results.append(reply("FEEDBACK_CANDIDATE"));continue
        if t=="ASSESS":
            o=s["observations"].get(e.get("observation"))
            if o is None or o[0]!=k:
                results.append(reply("HOLD_EVIDENCE"));continue
            if o[2]!="INDEPENDENT":
                results.append(reply("UNKNOWN_ASSISTED"));continue
            phase=e.get("phase")
            if phase not in ("IMMEDIATE","RETENTION","TRANSFER"):
                results.append(reply("HOLD_PHASE"));continue
            if phase!="IMMEDIATE":
                p=s["observations"].get(e.get("prior"))
                if p is None or p[0]!=k or p[2]!="INDEPENDENT" or p[1]["result"]!="CORRECT":
                    results.append(reply("HOLD_BASELINE"));continue
                if p[1]["family"]==o[1]["family"] or p[1]["id"]==o[1]["id"]:
                    results.append(reply("HOLD_NOVELTY"));continue
                # Cross-session is allowed only within same fully scoped identity.
                if o[1]["time"]<=p[1]["time"]:
                    results.append(reply("HOLD_ORDER"));continue
                if phase=="RETENTION":
                    interval=e.get("min_delay")
                    if not finite_number(interval) or interval<=0 or o[1]["time"]-p[1]["time"]<interval:
                        results.append(reply("UNKNOWN_DELAY"));continue
                if phase=="TRANSFER" and (e.get("target_context_defined") is not True or e.get("mapping_verified") is not True or o[1].get("context")==p[1].get("context") or not o[1].get("context") or not p[1].get("context")):
                    results.append(reply("HOLD_TRANSFER_MAPPING"));continue
            value=o[1]["result"]
            s["candidates"][(k,phase,eid)]=value
            results.append(reply(phase+"_CANDIDATE",result=value));continue
        results.append(reply("HOLD_EVENT_TYPE"))
    return {"steps":results,"candidate_count":len(s["candidates"]),"observation_count":len(s["observations"]),"suggestion_count":len(s["suggestions"]),"production_writes":0}
def main():
    fixture=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).with_name("scenarios.json")
    d=json.loads(fixture.read_text())
    receipt=[]
    for sc in d["scenarios"]:
        actual=run(sc)
        if actual!=sc["expected"]:
            print(json.dumps({"id":sc["id"],"actual":actual,"expected":sc["expected"]},ensure_ascii=False))
            raise SystemExit(1)
        receipt.append({"id":sc["id"],"steps":len(sc["events"]),"status":"PASS"})
    print(json.dumps({"cases":len(receipt),"steps":sum(x["steps"] for x in receipt),"production_writes":0,"results":receipt,"oracle":"SAME_AUTHOR_FIXED_EXPECTATIONS"},ensure_ascii=False))
if __name__=="__main__": main()
