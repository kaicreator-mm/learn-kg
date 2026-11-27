"""R5 finite correction witness. Old R3 remains an immutable historical snapshot."""
import pathlib,json,copy,collections,importlib.util,hashlib
from fractions import Fraction
HERE=pathlib.Path(__file__).resolve().parent
R=HERE.parent/"R3";R2=HERE.parent/"R2";P=HERE.parents[4]
def read(p):return json.loads(p.read_text())
def load(path):
    spec=importlib.util.spec_from_file_location("historical_r3",path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
old=load(R/"validate.py")
C=read(HERE/"contracts.json")
F=read(HERE/"fixtures.json")
D=read(R/"domain-cases.json")
def sign(s):return hashlib.sha256(s.encode()).hexdigest()
def integer(x):return type(x) is int
def text(x):return isinstance(x,str) and bool(x.strip())
def score(c,t,o):
    if c["subject"]=="zh":return old.score(c,t,o)
    r=o["response"]
    if r is None:return "UNKNOWN_MISSING"
    if t["same_unit"] is not True:return "HOLD_UNIT_UNKNOWN"
    a,b=t["a"];u,v=t["b"]
    assert b>0 and v>0
    expected=old.relation(Fraction(a,b),Fraction(u,v))
    assert expected==old.relation(a*v,u*b)
    out={"relation":int(r["relation"]==expected),"valid_justification":None}
    method=r.get("method");reason=r.get("reason")
    rc=C["reason_contract"]
    if method=="NUMERATOR_ONLY" or reason in rc["known_contradictions"]:
        out["valid_justification"]=0;return out
    if method not in rc["required_assertions"]:return out
    required=rc["required_assertions"][method];actual=r.get("assertions")
    if not isinstance(actual,dict) or set(actual)!=set(required) or any(type(x) is not bool for x in actual.values()):return out
    if actual!=required:
        out["valid_justification"]=0;return out
    if method=="CROSS":
        l,h=r.get("left_product"),r.get("right_product")
        if not integer(l) or not integer(h):return out
        if (l,h)!=(a*v,u*b):
            out["valid_justification"]=0;return out
        if reason=="容量相同，两分母为正，比较21和20" and (t["context"]!="同规格量杯情境" or (l,h)!=(21,20)):
            out["valid_justification"]=0;return out
    else:
        q,l,h=r.get("denominator"),r.get("left_n"),r.get("right_n")
        if not all(integer(x) for x in (q,l,h)):return out
        if q<=0 or Fraction(l,q)!=Fraction(a,b) or Fraction(h,q)!=Fraction(u,v):
            out["valid_justification"]=0;return out
        if reason=="同为十分之一单位" and q!=10:
            out["valid_justification"]=0;return out
    if reason not in rc["canonical"][method]:return out
    if t["context"]=="同规格量杯情境":
        if r.get("same_unit_ack") is False:
            out["valid_justification"]=0;return out
        if r.get("same_unit_ack") is not True:return out
    out["valid_justification"]=1
    return out
def full(s):return isinstance(s,dict) and bool(s) and all(type(v) is int and v==1 for v in s.values())
def classify(c,rule,min_delay):
    prefix="Z-" if c["subject"]=="zh" else "M-"
    obs={x["id"]:x for x in c["observations"]};tasks={x["id"]:x for x in c["tasks"]}
    a,b=obs[prefix+rule["baseline"]],obs[prefix+rule["target"]]
    t,u=tasks[a["task"]],tasks[b["task"]]
    if rule.get("wrong_scope") or any(t[k]!=u[k] for k in ("construct_id","rubric_id","knowledge_version","subject")):return "HOLD_SCOPE"
    if rule.get("missing"):return "UNKNOWN_MISSING"
    if a["assistance"]!="NONE" or rule.get("assistance",b["assistance"])!="NONE":return "HOLD_ASSISTANCE"
    if not full(score(c,t,a)):return "HOLD_BASELINE"
    if rule.get("known_complete") is not True:return "HOLD_EXPOSURE_HISTORY"
    if rule.get("equivalence",True) is not True or t["characteristics"]!=u["characteristics"]:return "HOLD_COMPARABILITY"
    if u["content_signature"]!=sign(u["prompt"]) or t["content_signature"]!=sign(t["prompt"]):return "HOLD_COMPARABILITY"
    start,end=a["minute"],b["minute"]
    if not integer(start) or not integer(end) or end<=start:return "HOLD_EVENT_ORDER"
    others=[x for x in c["observations"] if x["id"] not in (a["id"],b["id"])]
    if any(not integer(x["minute"]) for x in others):return "HOLD_EXPOSURE_HISTORY"
    if any(x["minute"] in (start,end) for x in others):return "HOLD_EVENT_ORDER"
    earlier=[x for x in c["observations"] if x["minute"]<end]
    if rule.get("reuse_baseline_content") or any(tasks[x["task"]]["content_signature"]==u["content_signature"] for x in earlier):return "HOLD_ITEM_PREEXPOSED"
    history=c["exposure_log"]+rule["exposures"]
    targets={"TARGET",u["id"],u["content_signature"]}
    valid_kinds={"TEACHING","FEEDBACK","PRACTICE","PREVIEW_TARGET","TEST","REVIEW"}
    for x in history:
        if not integer(x.get("minute")) or x.get("kind") not in valid_kinds or not text(x.get("item")) or type(x.get("related")) is not bool:return "HOLD_EXPOSURE_HISTORY"
        is_target=x["item"] in targets
        if (is_target and not x["related"]) or (x["kind"]=="PREVIEW_TARGET" and not is_target):return "HOLD_EXPOSURE_CONFLICT"
    if any(x["related"] and x["minute"] in (start,end) for x in history):return "HOLD_EVENT_ORDER"
    if any(x["item"] in targets and x["minute"]<end for x in history):return "HOLD_ITEM_PREEXPOSED"
    purpose=rule.get("purpose","RETENTION")
    s=score(c,u,b)
    if not isinstance(s,dict):return "HOLD_OBSERVATION"
    if any(v is None for v in s.values()):return "HOLD_JUSTIFICATION"
    if purpose=="TRANSFER":
        if t["context"]==u["context"]:return "HOLD_COMPARABILITY"
        return "NEAR_TRANSFER_CANDIDATE" if full(s) else "NEAR_TRANSFER_NEGATIVE_CANDIDATE"
    if purpose!="RETENTION" or t["context"]!=u["context"]:return "HOLD_COMPARABILITY"
    last=max([start]+[x["minute"] for x in earlier if start<=x["minute"]<end]+[x["minute"] for x in history if x["related"] and start<=x["minute"]<end])
    if end-last<min_delay:return "HOLD_DELAY_FROM_LAST_EXPOSURE"
    return "RETENTION_POSITIVE_CANDIDATE" if full(s) else "RETENTION_NEGATIVE_CANDIDATE"
def locate(c,id):
    return next(x for x in c["observations"] if x["id"]==id)
def task(c,o):
    return next(x for x in c["tasks"] if x["id"]==o["task"])
def rule(b="E2",t="E3",**kw):
    return {"baseline":b,"target":t,"known_complete":True,"exposures":[],**kw}
def main():
    triage=[x for f in R2.glob("triage-*.json") for x in read(f)["records"]]
    by={x["topic"]:x for x in triage}
    assert len(by)==len(triage)==327
    depth=read(HERE/"depth-disposition.json")
    original={}
    for f in list(old.P.glob("*/claims.json"))+list((old.P/"depth/D2").glob("**/claims.json")):
        for x in read(f)["records"]:original[x["stable_id"]]=x
    new={x["stable_id"]:x for x in read(R2/"claims.json")["records"]}
    roots={"cases":D,"design":read(R/"composition-design.json"),"r5":C}
    def resolve(path):
        a=roots
        for k in path.strip("/").split("/"):a=a[int(k)] if isinstance(a,list) else a[k]
        return a
    retained={x["topic"] for x in triage if x["decision"]=="SUBSTANTIVE_ORIGINAL_RETAIN_PENDING_QUALIFICATION"}
    targeted={x["topic"] for x in depth["targeted"]};pending={x["topic"] for x in depth["retention_pending_adequacy"]}
    assert len(retained)==189 and len(targeted)==12 and len(pending)==180 and not targeted&pending and (targeted&retained)|pending==retained
    for x in depth["targeted"]:
        assert x["requirement"]==by[x["topic"]]["requirement"] and x["scope"]==by[x["topic"]]["requirement_scope"]
        for f in x["facets"]:
            assert f["status"] in ("PARTIAL","CANDIDATE_EXAMPLE","HOLD") and f["claim_refs"] and text(f["rationale"])
            assert all((original|new)[i]["d3_id"]==x["topic"] for i in f["claim_refs"])
            for ref in f["case_paths"]:resolve(ref)
    for x in depth["retention_pending_adequacy"]:
        assert x["decision"]=="RETAIN_PENDING_PROFESSIONAL_ADEQUACY_NOT_ASSESSED" and x["original_claim_refs"]==by[x["topic"]]["original_claim_refs"] and x["qualification"]=="NOT_RUN"
    mapping={x["requirement_id"]:x for x in read(R/"requirement-mapping.json")["records"]}
    delta=read(HERE/"requirement-corrections.json")["records"]
    assert len(mapping)==108 and len(delta)==len({x["requirement_id"] for x in delta})==14
    for x in delta:
        previous=mapping[x["requirement_id"]]
        assert previous["status"]==x["previous_status"] and previous["interpretation"]==x["previous_interpretation"] and x["formal_receipt"]=="NOT_ISSUED"
        for ref in x["evidence_paths"]:resolve(ref)
        mapping[x["requirement_id"]]={**previous,**x}
    cases=copy.deepcopy(D["cases"])
    math=next(c for c in cases if c["subject"]=="math-pilot")
    for id,assertions in F["reason_assertion_patches"].items():locate(math,id)["response"]["assertions"]=assertions
    historic_fail=[]
    for f in F["reason_cases"][:2]:
        c=copy.deepcopy(next(x for x in D["cases"] if x["subject"]=="math-pilot"))
        o=locate(c,f["obs"]);o["response"].update(f["set"])
        assert old.score(c,task(c,o),o)["valid_justification"]==1 and old.classify(c,rule(),1440)=="RETENTION_POSITIVE_CANDIDATE"
        historic_fail.append(f["id"])
    reason_results={}
    for f in F["reason_cases"]:
        c=copy.deepcopy(math);o=locate(c,f["obs"]);o["response"].update(f.get("set",{}))
        for k in f.get("remove",[]):o["response"].pop(k)
        s=score(c,task(c,o),o);v=classify(c,rule(f["baseline"],f["target"]),1440)
        assert s=={"relation":1,"valid_justification":f["expected"]} and v==f["outcome"],(f["id"],s,v)
        reason_results[f["id"]]={"score":s,"outcome":v}
    history_results={};original_counts={};reproduced={}
    for c in cases:
        prefix="Z-" if c["subject"]=="zh" else "M-"
        for o in c["observations"]:assert score(c,task(c,o),o)==o["expected"],o["id"]
        for x in D["history_cases"]:
            actual=classify(c,x,1440);assert actual==x["expected"],(c["id"],x["id"],actual)
        original_counts[c["id"]]={"scores":len(c["observations"]),"history":len(D["history_cases"])}
        result={};repro=[]
        for x in F["history_cases"]:
            cc=copy.deepcopy(c);target=x.get("target","E3")
            r=rule(t=target,purpose=x.get("purpose","RETENTION"))
            if "event" in x:
                e=copy.deepcopy(x["event"]);u=task(cc,locate(cc,prefix+target))
                if e.get("item")=="$TARGET_ID":e["item"]=u["id"]
                if e.get("item")=="$TARGET_SIGNATURE":e["item"]=u["content_signature"]
                r["exposures"]=[e]
            else:locate(cc,prefix+x["observation"])["minute"]=x["minute"]
            if x in F["history_cases"][:4]:
                assert old.classify(cc,r,1440)=="RETENTION_POSITIVE_CANDIDATE"
                repro.append(x["id"])
            v=classify(cc,r,1440);assert v==x["expected"],(c["id"],x["id"],v)
            result[x["id"]]=v
        history_results[c["id"]]=result;reproduced[c["id"]]=repro
    print(json.dumps({"status":"R5_FINITE_CORRECTION_CANDIDATE_ONLY","depth":{"original_generic_retained":189,"generic_explicit_pending":180,"targeted_topics":12,"targeted_previous_retained":9,"facets":sum(len(x["facets"]) for x in depth["targeted"]),"facet_states":dict(collections.Counter(f["status"] for x in depth["targeted"] for f in x["facets"])),"qualification":"NOT_RUN"},"historical_reason_false_positives":historic_fail,"historical_exposure_false_positives":reproduced,"preserved_original_cases":original_counts,"reason_checks":reason_results,"history_checks":history_results,"mapping_delta":len(delta),"mapping_states":dict(collections.Counter(x["status"] for x in mapping.values())),"formal_CQ":"26_NOT_RUN","qualification":"NOT_RUN","persistent_db_files":0,"oracle":"SAME_AUTHOR_FIXED_EXPECTATIONS"},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
