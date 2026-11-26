"""Bounded research fixtures, not a product runtime or empirical calibration."""
import json, math
from pathlib import Path

def finite(x):
    return type(x) in (int,float) and math.isfinite(x)
def prob(x):
    return finite(x) and 0 <= x <= 1
def count(x):
    return type(x) is int and x>=0

def run(x):
    mode=x["mode"]
    if mode=="ranking":
        scores,labels=x["scores"],x["labels"]
        if not scores or len(scores)!=len(labels) or not all(map(prob,scores)) or not all(type(y) is int and y in (0,1) for y in labels):
            return "INVALID"
        pos=[s for s,y in zip(scores,labels) if y==1]
        neg=[s for s,y in zip(scores,labels) if y==0]
        auc=sum(1 if a>b else .5 if a==b else 0 for a in pos for b in neg)/(len(pos)*len(neg)) if pos and neg else "UNDEFINED"
        return {"auc":auc,"brier":sum((s-y)**2 for s,y in zip(scores,labels))/len(labels),"calibration":"NOT_ESTABLISHED"}
    if mode=="attrition":
        a,b,am,bm,ai,bi=(x[k] for k in ("assigned_a","assigned_b","missing_a","missing_b","imputed_a","imputed_b"))
        if not all(map(count,(a,b,am,bm,ai,bi))) or not a or not b or am>a or bm>b or ai>am or bi>bm:
            return "INVALID"
        return {"overall":(am+bm)/(a+b),"differential":abs(am/a-bm/b),"wwc_rating":"NOT_ESTABLISHED"}
    if mode=="drift":
        if not all(type(x[k]) is bool for k in ("same_label_version","has_labels","input_change","conditional_change")):
            return "INVALID"
        if not x["same_label_version"]: return "HOLD_MEASUREMENT_IDENTITY"
        if x["conditional_change"] and not x["has_labels"]: return "HOLD_LABEL_EVIDENCE"
        return {"input_signal":x["input_change"],"conditional_signal":x["conditional_change"] if x["has_labels"] else "UNKNOWN","model_failure":"NOT_INFERRED"}
    if mode=="risk":
        scenarios,actions=x["scenarios"],x["actions"]
        if not scenarios or not actions or any(not isinstance(b,list) or not b or not all(map(prob,b)) or not math.isclose(sum(b),1,abs_tol=1e-9) for b in scenarios):
            return "INVALID"
        if not all(len(b)==len(scenarios[0]) for b in scenarios): return "INVALID"
        ids=[a["id"] for a in actions]
        if len(ids)!=len(set(ids)) or any(not isinstance(i,str) or not i for i in ids): return "INVALID"
        if any(a["eligible"] not in ("yes","no","unknown") for a in actions): return "INVALID"
        if x["stopped"]: return "STOP"
        if not count(x["budget"]): return "INVALID"
        if any(not count(a["cost"]) for a in actions): return "INVALID"
        eligible=[a for a in actions if a["eligible"]=="yes" and a["cost"]<=x["budget"]]
        if not eligible: return "HOLD_NO_ELIGIBLE"
        if any(not isinstance(a["loss"],list) or len(a["loss"])!=len(scenarios[0]) or not all(finite(v) and v>=0 for v in a["loss"]) for a in eligible):
            return "HOLD_LOSS"
        ranks=[]
        for b in scenarios:
            losses={a["id"]:sum(v*l for v,l in zip(b,a["loss"])) for a in eligible}
            best=min(losses.values())
            ranks.append(sorted(i for i,v in losses.items() if math.isclose(v,best,abs_tol=1e-9)))
        shared=sorted(set(ranks[0]).intersection(*map(set,ranks[1:])))
        return {"offer":shared,"status":"CANDIDATE_ONLY" if shared else "HOLD_RANK_REVERSAL","scenario_minima":ranks,"executed":False}
    if mode=="cutoff":
        # prediction context is a single learner, with authoritative question-attempt IDs
        target=x["target"]
        if not count(target["cutoff"]) or not target["attempt"] or not target["learner"]: return "INVALID"
        seen=set()
        for row in x["history"]:
            if not row["attempt"] or not row["learner"] or not count(row["available"]): return "INVALID"
            if row["learner"]!=target["learner"]: return "HOLD_LEARNER_SCOPE"
            if row["attempt"]==target["attempt"]: return "HOLD_SAME_ATTEMPT"
            if row["available"]>=target["cutoff"]: return "HOLD_TIME_CUTOFF"
            if row["attempt"] in seen: return "HOLD_DUPLICATE_ATTEMPT"
            seen.add(row["attempt"])
        return {"history_attempts":len(seen),"status":"SCOPED_HISTORY","leakage_free_globally":"NOT_ESTABLISHED"}
    if mode=="loop":
        # fixed synthetic learner and goal, immutable task/version registry. No actual execution.
        goal=x["goal"]; budget=x["budget"]; registry=x["registry"]; events=x["events"]
        if type(x["consent"]) is not bool or not count(budget): return "INVALID"
        if not x["consent"]: return "STOP" if not events else "HOLD_CONSENT"
        if not goal or goal not in ("produce","recognize"): return "INVALID"
        seen=set(); attempts=set(); observed=[]; chosen=None; stopped=False; last=-1; last_observation_time=-1
        reflection=None
        for e in events:
            if e["id"] in seen: return "HOLD_DUPLICATE_EVENT"
            seen.add(e["id"])
            if stopped: return "HOLD_AFTER_STOP"
            if not count(e["time"]) or e["time"]<=last: return "HOLD_TIME_ORDER"
            last=e["time"]
            kind=e["kind"]
            if kind=="stop":
                stopped=True;continue
            if kind=="feedback":
                # proposal is not observation; feedback is accepted explicitly
                if chosen is not None or not any(o["target"]==goal and o["correct"] is False and o["support"]=="independent" for o in observed):
                    return "HOLD_FEEDBACK_SEQUENCE"
                if not e["accepted"]: return "HOLD_CONSENT"
                if budget<2: return "HOLD_BUDGET"
                chosen=e["time"];budget-=2;continue
            if kind=="reflect":
                if not observed or e["attempt"]!=observed[-1]["attempt"] or not prob(e["confidence"]):
                    return "HOLD_REFLECTION_BINDING"
                reflection={"confidence":e["confidence"],"observed":observed[-1]["correct"]}
                continue
            if kind!="response": return "INVALID"
            if budget<1: return "HOLD_BUDGET"
            if e["attempt"] in attempts: return "HOLD_DUPLICATE_ATTEMPT"
            attempts.add(e["attempt"])
            t=registry.get(e["task"])
            if not t or e["version"]!=t["version"]: return "HOLD_TASK_VERSION"
            if t["target"]!=e["target"] or e["target"] not in ("produce","recognize"): return "HOLD_TARGET"
            if e["support"] not in ("independent","hinted") or type(e["correct"]) is not bool: return "INVALID"
            if e["phase"] not in ("baseline","retest","delayed"): return "INVALID"
            if e["phase"]!="baseline":
                if chosen is None or e["time"]<=chosen: return "HOLD_FEEDBACK_SEQUENCE"
                if any(o["task"]==e["task"] for o in observed): return "HOLD_REPEATED_TASK"
                if e["phase"]=="delayed" and e["time"]-chosen<1440: return "HOLD_DELAY"
            observed.append({"task":e["task"],"attempt":e["attempt"],"target":e["target"],"correct":e["correct"],"support":e["support"],"phase":e["phase"]})
            last_observation_time=e["time"];budget-=1
        independent={o["phase"] for o in observed if o["target"]==goal and o["correct"] and o["support"]=="independent"}
        if stopped: status="STOP"
        elif chosen is not None and {"retest","delayed"}<=independent: status="EVIDENCE_RECORDED"
        elif chosen is not None: status="OFFER_PROBE" if budget else "HOLD_BUDGET"
        elif any(o["target"]==goal and not o["correct"] and o["support"]=="independent" for o in observed):
            status="OFFER_FEEDBACK" if budget>=2 else "HOLD_BUDGET"
        else: status="HOLD_TARGET_EVIDENCE"
        return {"status":status,"observations":len(observed),"remaining":budget,"reflection":reflection,"mastery":"NOT_INFERRED","model_update":"NOT_PERFORMED"}
    raise ValueError(mode)

def eq(a,b):
    if type(b) in (float,int): return finite(a) and math.isclose(a,b,rel_tol=1e-8,abs_tol=1e-8)
    if isinstance(b,dict): return isinstance(a,dict) and a.keys()==b.keys() and all(eq(a[k],v) for k,v in b.items())
    if isinstance(b,list): return isinstance(a,list) and len(a)==len(b) and all(eq(v,w) for v,w in zip(a,b))
    return a==b

def main():
    f=json.loads(Path(__file__).with_name("fixtures.json").read_text())
    results=[]
    for c in f["cases"]:
        actual=run(c["input"])
        results.append({"id":c["id"],"actual":actual,"pass":eq(actual,c["expected"])})
    print(json.dumps({"total":len(results),"passed":sum(r["pass"] for r in results),"results":results},ensure_ascii=False))
    if not all(r["pass"] for r in results): raise SystemExit(1)
if __name__=="__main__": main()
