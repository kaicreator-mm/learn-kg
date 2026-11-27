"""Finite research fixtures; not a product learning runtime."""
import json, math
from pathlib import Path
from statistics import NormalDist

def finite(x):
    return type(x) in (int,float) and math.isfinite(x)
def probability(x):
    return finite(x) and 0 <= x <= 1
def count(x):
    return type(x) is int and x >= 0

def run(x):
    mode=x["mode"]
    if mode=="sdt":
        h,miss,f,cr=(x[k] for k in ("hit","miss","fa","cr"))
        if not all(map(count,(h,miss,f,cr))) or h+miss==0 or f+cr==0 or x["policy"] not in ("reject","loglinear"):
            return "INVALID"
        H,F=h/(h+miss),f/(f+cr)
        if x["policy"]=="loglinear":
            H,F=(h+.5)/(h+miss+1),(f+.5)/(f+cr+1)
        elif H in (0,1) or F in (0,1):
            return "HOLD_ENDPOINT"
        a,b=NormalDist().inv_cdf(H),NormalDist().inv_cdf(F)
        return {"dprime":a-b,"criterion":-(a+b)/2,"raw":[h,miss,f,cr],"policy":x["policy"]}
    if mode=="switch":
        a,b,c=x["switch"],x["repeat"],x["single"]
        if not all(finite(v) and v>0 for v in (a,b,c)): return "INVALID"
        if not x["matched"]: return "HOLD_COMPARABILITY"
        return {"local":a-b,"mixing":b-c,"mechanism":"NOT_INFERRED"}
    if mode=="integrate":
        s,h=x["simple"],x["hard"]
        if not probability(s) or not probability(h): return "INVALID"
        if not all(x[k] is True for k in ("matched","independent","conjunctive","no_extra_error")) or s==0 or h>s:
            return "HOLD_MODEL"
        return {"conditional_ratio":h/s,"individual_mastery":"NOT_INFERRED"}
    if mode=="loop":
        # Fixed illustrative task family, not a general parser or diagnosis engine.
        # Goal: independently compute remaining budget B - q*price.
        events=x["events"]; allowed=x["consent"]; remaining=x["budget"]
        if not count(remaining) or type(allowed) is not bool: return "INVALID"
        seen=set(); observations=[]; feedback=False; stopped=False
        for ev in events:
            if ev["id"] in seen: return "HOLD_DUPLICATE"
            seen.add(ev["id"])
            if stopped: return "HOLD_AFTER_STOP"
            if ev["kind"]=="stop":
                stopped=True; continue
            if ev["kind"]=="feedback":
                if not allowed or remaining<2: return "HOLD_FEEDBACK_AUTHORIZATION"
                pre={o["target"]:o["correct"] for o in observations if o["phase"]=="baseline" and o["support"]=="independent"}
                if pre!={"multiply":True,"subtract":True,"compose":False}: return "HOLD_DIAGNOSIS"
                feedback=True; remaining-=2; continue
            if ev["kind"]!="task" or not allowed or remaining<1: return "HOLD_TASK_AUTHORIZATION"
            if ev["phase"] not in ("baseline","retest","delayed","transfer") or ev["support"] not in ("independent","hinted"):
                return "INVALID"
            if ev["phase"]!="baseline" and not feedback: return "HOLD_SEQUENCE"
            if ev["phase"]=="delayed" and ev["minutes"]<1440: return "HOLD_DELAY"
            if ev["phase"] in ("retest","delayed","transfer") and any(o["task"]==ev["task"] for o in observations):
                return "HOLD_REPEATED_ITEM"
            target=ev["target"]; a,b,c=ev["values"]
            if not all(count(v) for v in (a,b,c,ev["answer"],ev["minutes"])): return "INVALID"
            if target=="multiply": expected=b*c
            elif target=="subtract": expected=a-b
            elif target=="compose": expected=a-b*c
            else: return "INVALID"
            observations.append({"target":target,"phase":ev["phase"],"correct":ev["answer"]==expected,"support":ev["support"],"task":ev["task"]})
            remaining-=1
        pre={o["target"]:o["correct"] for o in observations if o["phase"]=="baseline" and o["support"]=="independent"}
        if stopped or not allowed: decision="STOP"
        elif pre=={"multiply":True,"subtract":True,"compose":False} and not feedback:
            decision="OFFER_COMPOSITION_EXPLANATION" if remaining>=2 else "HOLD_BUDGET"
        elif feedback:
            valid={o["phase"] for o in observations if o["target"]=="compose" and o["correct"] and o["support"]=="independent"}
            if not {"retest","delayed","transfer"} <= valid:
                decision="OFFER_INDEPENDENT_PROBE" if remaining>=1 else "HOLD_BUDGET"
            else: decision="EVIDENCE_RECORDED"
        else: decision="HOLD_COMPETING_EXPLANATIONS"
        return {"decision":decision,"remaining":remaining,"observations":len(observations),"mastery":"NOT_INFERRED","feedback_given":feedback}
    raise ValueError(mode)

def eq(a,b):
    if type(b) in (float,int): return finite(a) and math.isclose(a,b,rel_tol=1e-8,abs_tol=1e-8)
    if isinstance(b,dict): return isinstance(a,dict) and a.keys()==b.keys() and all(eq(a[k],v) for k,v in b.items())
    if isinstance(b,list): return isinstance(a,list) and len(a)==len(b) and all(eq(v,w) for v,w in zip(a,b))
    return a==b

def main():
    f=json.loads(Path(__file__).with_name("fixtures.json").read_text())
    records=[]
    for c in f["cases"]:
        actual=run(c["input"])
        records.append({"id":c["id"],"actual":actual,"pass":eq(actual,c["expected"])})
    print(json.dumps({"total":len(records),"passed":sum(r["pass"] for r in records),"results":records},ensure_ascii=False))
    if not all(r["pass"] for r in records): raise SystemExit(1)

if __name__=="__main__": main()
