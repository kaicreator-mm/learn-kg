#!/usr/bin/env python3
"""Exploratory DB01 text-only schema/semantic and BKT arithmetic witness. Not production importer."""
import copy, hashlib, json, sys, platform
from pathlib import Path
from fractions import Fraction
from importlib.metadata import version
from jsonschema import Draft202012Validator

def reject_pairs(pairs):
    obj={}
    for k,v in pairs:
        if k in obj: raise ValueError("duplicate JSON key: "+k)
        obj[k]=v
    return obj

def load(p):
    return json.loads(p.read_text(encoding="utf-8"),object_pairs_hook=reject_pairs,parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))

def typed_refs(obj):
    if isinstance(obj,dict):
        if set(obj)=={"package_id","version","stable_id","kind"}: yield obj
        else:
            for v in obj.values(): yield from typed_refs(v)
    elif isinstance(obj,list):
        for v in obj: yield from typed_refs(v)

def check(p,schema):
    Draft202012Validator(schema).validate(p)
    rows=p["records"]; index={r["stable_id"]:r for r in rows}
    if len(index)!=len(rows): raise ValueError("duplicate stable ID")
    expected={"source_ref":"Source","evidence_refs":"EvidenceLocator","claim_refs":"Claim","element_ref":"Element","model_ref":"ModelSpec","from_ref":"Element","to_ref":"ModelSpec","target_ref":"ModelSpec","case_refs":"Case"}
    for row in rows:
        for key,kind in expected.items():
            if key not in row: continue
            v=row[key]; refs=v if isinstance(v,list) else [v]
            for ref in refs:
                target=index.get(ref["stable_id"])
                if ref["package_id"]!=p["package_id"] or ref["version"]!=p["version"] or target is None or ref["kind"]!=kind or target["kind"]!=kind:
                    raise ValueError("unresolved or mistyped reference: "+str(ref))
        if row["kind"]=="Claim" and row["claim_type"]!="ENGINEERING_POLICY" and not row["evidence_refs"]:
            raise ValueError("missing professional locator")
        if row["kind"]=="Claim" and row["claim_type"]=="ENGINEERING_POLICY" and row["evidence_refs"]:
            raise ValueError("project policy may not masquerade as source claim")
        if row["kind"]=="ModelSpec":
            if {v["name"] for v in row["parameters"]}!={"p","G","S","T"}: raise ValueError("parameter identity")
            if {v["name"] for v in row["formulas"]}!={"prediction_correct","posterior_correct","posterior_incorrect","next_prior"}: raise ValueError("formula identity")
            if index[row["element_ref"]["stable_id"]]["model_ref"]["stable_id"]!=row["stable_id"]: raise ValueError("inconsistent model/element link")
    return index

def evaluate(e,env):
    if "var" in e: return env[e["var"]]
    if "const" in e: return Fraction(e["const"])
    a,b=(evaluate(x,env) for x in e["args"])
    op=e["op"]
    if op=="add": return a+b
    if op=="sub": return a-b
    if op=="mul": return a*b
    if op=="div": return a/b
    raise ValueError("unapproved operation")

def run_case(model, x):
    try: env={k:Fraction(x[k]) for k in ("p","G","S","T")}
    except (ValueError,ZeroDivisionError): return {"status":"REJECT_PARAMETER"}
    if any(not 0<=v<=1 for v in env.values()): return {"status":"REJECT_PARAMETER"}
    if x["observation"]=="missing" or not x["independent"] or not x["single_component"]: return {"status":"UNKNOWN"}
    formula={x["name"]:x["expr"] for x in model["formulas"]}
    pred=evaluate(formula["prediction_correct"],env)
    try: posterior=evaluate(formula["posterior_"+x["observation"]],env)
    except ZeroDivisionError: return {"status":"REJECT_ZERO_LIKELIHOOD"}
    nxt=evaluate(formula["next_prior"],{**env,"posterior":posterior})
    if any(not 0<=v<=1 for v in (pred,posterior,nxt)): raise ValueError("invalid result")
    return {"status":"OK","prediction_correct":str(pred),"posterior":str(posterior),"next_prior":str(nxt)}

def main():
    root=Path(__file__).resolve().parent
    s=load(root/"schema.json"); p=load(root/"records.json")
    Draft202012Validator.check_schema(s); index=check(p,s)
    results=[]
    for r in p["records"]:
        if r["kind"]!="Case": continue
        actual=run_case(index[r["model_ref"]["stable_id"]],r["input"])
        if actual!=r["expected"]: raise AssertionError((r["stable_id"],actual,r["expected"]))
        results.append({"id":r["stable_id"],"expected":r["expected"],"actual":actual,"status":"PASS"})
    negatives=[]
    def reject(label,change):
        q=copy.deepcopy(p); change(q)
        try: check(q,s)
        except Exception as e: negatives.append({"id":label,"status":"PASS","error":type(e).__name__}); return
        raise AssertionError(label)
    def find(q,kind): return next(x for x in q["records"] if x["kind"]==kind)
    reject("duplicate-id",lambda q:q["records"].append(copy.deepcopy(q["records"][0])))
    reject("unknown-field",lambda q:q["records"][0].update({"surprise":1}))
    reject("missing-target",lambda q:find(q,"Case")["model_ref"].update(stable_id="bkt:nonexistent"))
    reject("wrong-kind",lambda q:find(q,"Case")["model_ref"].update(kind="Claim"))
    reject("wrong-version",lambda q:find(q,"Case")["model_ref"].update(version="0.9.9"))
    reject("empty-locator",lambda q:next(r for r in q["records"] if r["kind"]=="Claim" and r["claim_type"]!="ENGINEERING_POLICY").update(evidence_refs=[]))
    reject("unapproved-op",lambda q:find(q,"ModelSpec")["formulas"][0]["expr"].update(op="execute"))
    reject("accepted-claim",lambda q:find(q,"Claim").update(status="ACCEPTED_SCOPED"))
    try: json.loads('{"a":1,"a":2}',object_pairs_hook=reject_pairs)
    except ValueError: negatives.append({"id":"duplicate-key","status":"PASS","error":"ValueError"})
    else: raise AssertionError("duplicate-key")
    print(json.dumps({"scope":"DRAFT_SCHEMA_AND_MATH_ONLY","python":platform.python_version(),"jsonschema":version("jsonschema"),"sha256":{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ("schema.json","records.json","validate.py")},"records":len(index),"cases":results,"negative_tests":negatives,"status":"PASS","professional_qualification":"NOT_RUN","sqlite_generated":False},ensure_ascii=False))
if __name__=="__main__": main()
