#!/usr/bin/env python3
"""Finite HLR and review policy research witness; no learner data or database."""
import copy, hashlib, json, math, platform
from pathlib import Path
from importlib.metadata import version
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parent
def pairs(xs):
    d={}
    for k,v in xs:
        if k in d: raise ValueError("duplicate key")
        d[k]=v
    return d
def parse(s): return json.loads(s,object_pairs_hook=pairs,parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))
def load(n): return parse((ROOT/n).read_text(encoding="utf-8"))
FIELDS={"recall":{"delta","half_life","unit"},"estimate_half_life":{"weights","features","unit"},"inverse_half_life":{"delta","p","unit"},"policy":{"p","target","authorized","applicable","cost_minutes","budget_minutes"}}
GUARDS=["NOT_AUTHORIZED","MISSING_OR_INVALID_INPUT","NOT_APPLICABLE","PROBABILITY_ABOVE_TARGET","COST_EXCEEDS_BUDGET","ALWAYS"]
ACTIONS=["REJECT_PERMISSION","UNKNOWN","UNKNOWN","WAIT","DEFER_BUDGET","SUGGEST_REVIEW"]
VARS={"recall":{"delta","half_life"},"estimate_half_life":{"weights","features"},"inverse_half_life":{"delta","p"}}
def variables(e):
    if "var" in e: return {e["var"]}
    if "const" in e: return set()
    return set().union(*(variables(a) for a in e["args"]))
def check(p,s):
    Draft202012Validator(s).validate(p)
    idx={r["stable_id"]:r for r in p["records"]}
    if len(idx)!=len(p["records"]): raise ValueError("duplicate ID")
    def target(r,k):
        x=idx.get(r["stable_id"])
        if x is None or x["kind"]!=k or r["kind"]!=k or r["package_id"]!=p["package_id"] or r["version"]!=p["version"]: raise ValueError("bad typed ref")
        return x
    for r in p["records"]:
        k=r["kind"]
        expected={"source_ref":"Source","evidence_refs":"EvidenceLocator","claim_refs":"Claim","model_ref":"ModelSpec","element_ref":"Element","from_ref":"ModelSpec","to_ref":"PolicySpec","case_refs":"Case"}
        for key,t in expected.items():
            if key in r:
                for x in (r[key] if isinstance(r[key],list) else [r[key]]): target(x,t)
        if k=="Claim" and bool(r["evidence_refs"])==(r["claim_type"]=="ENGINEERING_POLICY"): raise ValueError("claim source separation")
        if k=="ModelSpec":
            if {f["name"] for f in r["formulas"]}!=set(VARS): raise ValueError("formula set")
            if any(variables(f["expr"])!=VARS[f["name"]] for f in r["formulas"]): raise ValueError("formula variables")
            if target(r["element_ref"],"Element")["model_ref"]["stable_id"]!=r["stable_id"]: raise ValueError("reverse link")
        if k=="PolicySpec" and ([x["guard"] for x in r["rules"]]!=GUARDS or [x["action"] for x in r["rules"]]!=ACTIONS): raise ValueError("policy contract")
        if k=="Case":
            target(r["target_ref"],"PolicySpec" if r["mode"]=="policy" else "ModelSpec")
            if set(r["input"])!=FIELDS[r["mode"]]: raise ValueError("mode/input mismatch")
    return idx
def finite(x): return type(x) in (float,int) and math.isfinite(x)
def eval_expr(e,env):
    if "var" in e: return env[e["var"]]
    if "const" in e: return e["const"]
    a=[eval_expr(x,env) for x in e["args"]]; o=e["op"]
    if o=="pow2": return 2.0**a[0]
    if o=="neg": return -a[0]
    if o=="log2": return math.log2(a[0])
    if o=="div": return a[0]/a[1]
    if o=="dot": return math.fsum(x*y for x,y in zip(*a,strict=True))
    raise ValueError("unknown op")
def run_case(spec,mode,x):
    if mode=="policy":
        valid=all(finite(x[k]) for k in ("p","target","cost_minutes","budget_minutes"))
        valid=valid and 0<=x["p"]<=1 and 0<x["target"]<1 and x["cost_minutes"]>=0 and x["budget_minutes"]>=0
        tests={"NOT_AUTHORIZED":lambda:not x["authorized"],"MISSING_OR_INVALID_INPUT":lambda:not valid,"NOT_APPLICABLE":lambda:not x["applicable"],"PROBABILITY_ABOVE_TARGET":lambda:x["p"]>x["target"],"COST_EXCEEDS_BUDGET":lambda:x["cost_minutes"]>x["budget_minutes"],"ALWAYS":lambda:True}
        for r in spec["rules"]:
            if tests[r["guard"]](): return {"status":r["action"]}
        raise AssertionError("no terminal rule")
    if x["unit"]!="day": return {"status":"REJECT_INPUT"}
    if mode=="recall": valid=finite(x["delta"]) and finite(x["half_life"]) and x["delta"]>=0 and x["half_life"]>0
    elif mode=="inverse_half_life": valid=finite(x["delta"]) and finite(x["p"]) and x["delta"]>0 and 0<x["p"]<1
    else: valid=len(x["weights"])==len(x["features"]) and all(finite(y) for y in x["weights"]+x["features"])
    if not valid: return {"status":"REJECT_INPUT"}
    f=next(f for f in spec["formulas"] if f["name"]==mode)
    try: value=eval_expr(f["expr"],x)
    except (OverflowError,ValueError,ZeroDivisionError): return {"status":"REJECT_NUMERIC_RANGE"}
    if not finite(value) or value<=0 or (mode=="recall" and value>1): return {"status":"REJECT_NUMERIC_RANGE"}
    return {"status":"OK","value":value}
def equal(a,b): return a["status"]==b["status"] and (a["status"]!="OK" or math.isclose(a["value"],b["value"],rel_tol=1e-12,abs_tol=1e-12))
def main():
    p,s=load("records.json"),load("schema.json"); Draft202012Validator.check_schema(s); idx=check(p,s)
    results=[]
    for r in p["records"]:
        if r["kind"]!="Case": continue
        actual=run_case(idx[r["target_ref"]["stable_id"]],r["mode"],r["input"])
        if not equal(actual,r["expected"]): raise AssertionError((r["stable_id"],actual,r["expected"]))
        results.append({"id":r["stable_id"],"expected":r["expected"],"actual":actual,"status":"PASS"})
    negatives=[]
    def find(q,k): return next(x for x in q["records"] if x["kind"]==k)
    def reject(label,mut):
        q=copy.deepcopy(p);mut(q)
        try: check(q,s)
        except (ValueError,Exception) as e:
            from jsonschema.exceptions import ValidationError
            if not isinstance(e,(ValueError,ValidationError)): raise
            negatives.append({"id":label,"status":"PASS","error":type(e).__name__});return
        raise AssertionError(label)
    reject("duplicate-id",lambda q:q["records"].append(copy.deepcopy(q["records"][0])))
    reject("unknown-field",lambda q:find(q,"Source").update(extra=True))
    reject("wrong-kind",lambda q:find(q,"Relation")["to_ref"].update(kind="Claim"))
    reject("missing-target",lambda q:find(q,"Element")["model_ref"].update(stable_id="hlr:none"))
    reject("wrong-version",lambda q:find(q,"Element")["model_ref"].update(version="9"))
    reject("unapproved-op",lambda q:find(q,"ModelSpec")["formulas"][0]["expr"].update(op="exec"))
    reject("policy-order",lambda q:find(q,"PolicySpec")["rules"].reverse())
    reject("policy-action",lambda q:find(q,"PolicySpec")["rules"][0].update(action="SUGGEST_REVIEW"))
    reject("missing-evidence",lambda q:find(q,"Claim").update(evidence_refs=[]))
    reject("unearned-qualification",lambda q:find(q,"Claim").update(status="ACCEPTED_SCOPED"))
    reject("mode-mismatch",lambda q:find(q,"Case").update(mode="policy"))
    try: parse('{"a":1,"a":2}')
    except ValueError: negatives.append({"id":"duplicate-key","status":"PASS","error":"ValueError"})
    else: raise AssertionError("duplicate-key")
    print(json.dumps({"scope":"INVESTIGATION_ONLY","python":platform.python_version(),"jsonschema":version("jsonschema"),"sha256":{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ("records.json","schema.json","validate.py")},"records":len(idx),"cases":results,"negative_tests":negatives,"professional_qualification":"NOT_RUN","sqlite_generated":False},ensure_ascii=False))
if __name__=="__main__": main()
