"""Finite content and history checks on authored cases, not an independent education trial."""
import json, pathlib, hashlib, collections
from fractions import Fraction
ROOT=pathlib.Path(__file__).resolve().parents[7]
P=ROOT/"docs/drafts/s01";D=P/"depth/D3";R=D/"remediation/R3";R2=D/"remediation/R2"
def read(p):return json.loads(p.read_text())
def sign(s):return hashlib.sha256(s.encode()).hexdigest()
def relation(a,b):return "<" if a<b else ">" if a>b else "="
def score(c,t,o):
    r=o["response"]
    if r is None:return "UNKNOWN_MISSING"
    if c["subject"]=="zh":
        if t["goods_from"] is None or t["money_from"] is None:return "HOLD_AMBIGUOUS"
        assert t["goods_from"]==t["money_to"] and t["goods_to"]==t["money_from"] and t["goods_from"]!=t["goods_to"]
        if t["actor"]==t["goods_to"]:verb,role="买","PAY_RECEIVE"
        elif t["actor"]==t["goods_from"]:verb,role="卖","GIVE_RECEIVE_MONEY"
        else:return "HOLD_AMBIGUOUS"
        return {"role_direction":int(r["role"]==role),"lexical_choice":int(r["verb"]==verb),"actor_object":int((r["actor"],r["object"])==(t["actor"],t["object"]))}
    if t["same_unit"] is not True:return "HOLD_UNIT_UNKNOWN"
    a,b=t["a"];c_,e=t["b"]
    assert b>0 and e>0
    # Fraction comparison independently derived from rational arithmetic, not copying expected relation.
    expected=relation(Fraction(a,b),Fraction(c_,e))
    assert expected==relation(a*e,c_*b)
    ok=False
    if r["method"]=="CROSS":
        ok=(r["left_product"],r["right_product"])==(a*e,c_*b) and "正" in r["reason"]
    elif r["method"]=="COMMON_DENOM":
        q=r["denominator"];l=r["left_n"];rr=r["right_n"]
        ok=type(q)==int and q>0 and Fraction(l,q)==Fraction(a,b) and Fraction(rr,q)==Fraction(c_,e) and ("单位" in r["reason"])
    if t["context"]=="同规格量杯情境":ok=ok and r.get("same_unit_ack") is True
    return {"relation":int(r["relation"]==expected),"valid_justification":int(ok)}
def full(s):return isinstance(s,dict) and all(v==1 for v in s.values())
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
    assert end>start
    earlier=[x for x in c["observations"] if x["minute"]<end]
    if rule.get("reuse_baseline_content") or any(tasks[x["task"]]["content_signature"]==u["content_signature"] for x in earlier):return "HOLD_ITEM_PREEXPOSED"
    history=c["exposure_log"]+rule["exposures"]
    if any(x["related"] is not True and x["related"] is not False for x in history):return "HOLD_EXPOSURE_HISTORY"
    if any(x["related"] is True and x["item"] in ("TARGET",u["id"],u["content_signature"]) and x["minute"]<end for x in history):return "HOLD_ITEM_PREEXPOSED"
    purpose=rule.get("purpose","RETENTION")
    s=score(c,u,b)
    if not isinstance(s,dict):return "HOLD_OBSERVATION"
    if purpose=="TRANSFER":
        if t["context"]==u["context"]:return "HOLD_COMPARABILITY"
        return "NEAR_TRANSFER_CANDIDATE" if full(s) else "NEAR_TRANSFER_NEGATIVE_CANDIDATE"
    if t["context"]!=u["context"]:return "HOLD_COMPARABILITY"
    last=max([start]+[x["minute"] for x in earlier if start<=x["minute"]<end]+[x["minute"] for x in history if x["related"] is True and start<=x["minute"]<end])
    if end-last<min_delay:return "HOLD_DELAY_FROM_LAST_EXPOSURE"
    return "RETENTION_POSITIVE_CANDIDATE" if full(s) else "RETENTION_NEGATIVE_CANDIDATE"
def main():
    original={}
    for f in list(P.glob("*/claims.json"))+list((P/"depth/D2").glob("**/claims.json")):
        for x in read(f)["records"]:
            assert x["stable_id"] not in original;original[x["stable_id"]]=x
    assert len(original)==1712
    req={x["d3_id"]:x for f in P.glob("*-requirements.json") if len(f.name.split("-")[0])==3 and f.name[0] in "KH" for x in read(f)["records"]}
    r2=read(R2/"claims.json");new={x["stable_id"]:x for x in r2["records"]};src={x["id"]:x for x in read(R2/"sources.json")["sources"]}
    assert len(new)==31 and len(src)==14 and not set(new)&set(original)
    for x in new.values():
        assert (x["owner"],x["requirement_id"])==(req[x["d3_id"]]["owner"],req[x["d3_id"]]["requirement_id"])
        assert set(x["source_refs"])<=set(src) and x["qualification"]=="NOT_RUN"
        if x["source_refs"]:assert x.get("source_locator")
        if x["claim_type"]=="PROJECT_RULE":assert not x["source_refs"]
    for x in r2["split"]:
        a,b=[new[i] for i in x["replacement_ids"]]
        assert x["previous_statement"]==original[x["previous_id"]]["statement"] and a["d3_id"]==b["d3_id"]==original[x["previous_id"]]["d3_id"] and a["source_refs"] and b["claim_type"]=="PROJECT_RULE" and not b["source_refs"]
    triage=[x for f in R2.glob("triage-*.json") for x in read(f)["records"]]
    assert len(triage)==len({x["topic"] for x in triage})==327
    no_depth={x["d3_id"] for x in original.values() if "base_claim_ref" in x}
    assert {x["topic"] for x in triage}==set(req)-no_depth
    for x in triage:
        assert x["requirement"]==req[x["topic"]]["requirement_id"] and all(original[i]["d3_id"]==x["topic"] for i in x["original_claim_refs"]) and all(new[i]["d3_id"]==x["topic"] for i in x["supplement_refs"])
        assert x["qualification"]=="NOT_RUN"
    result={"R2":{"original":len(original),"new":len(new),"new_topics":len({x["d3_id"] for x in new.values()}),"source_records":len(src),"split":len(r2["split"]),"triage":dict(collections.Counter(x["decision"] for x in triage))}}
    d=read(R/"domain-cases.json");design=read(R/"composition-design.json");ids=set(new)|set(original)
    assert set(d["policy"]["claim_refs"])<=ids and set(d["policy"]["source_refs"])<=set(src)
    cases={}
    for c in d["cases"]:
        assert set(c["claim_refs"])<=ids and set(c["source_refs"])<=set(src)
        tasks={t["id"]:t for t in c["tasks"]};assert len(tasks)==len(c["tasks"])==7
        assert len({t["content_signature"] for t in c["tasks"]})==7 and all(t["content_signature"]==sign(t["prompt"]) for t in tasks.values())
        scores={}
        for o in c["observations"]:
            s=score(c,tasks[o["task"]],o);assert s==o["expected"],(o["id"],s,o["expected"]);scores[o["id"]]=s
        hist={}
        for x in d["history_cases"]:
            a=classify(c,x,d["policy"]["min_delay_minutes"]);assert a==x["expected"],(c["id"],x["id"],a,x["expected"]);hist[x["id"]]=a
        alternatives={x["id"]:x for x in c["plan"]["alternatives"]}
        for opt in c["plan"]["option_comparison"]:
            cost=sum(alternatives[x]["cost"] for x in opt["action_ids"])
            assert cost==opt["cost"] and (cost<=c["plan"]["budget_minutes"])==opt["feasible_budget"]
        assert sum(alternatives[x]["cost"] for x in c["plan"]["chosen"])==12
        cases[c["id"]]={"raw_scores":scores,"history_cases":hist,"plan_comparison":len(c["plan"]["option_comparison"])}
    assert len({c["construct"] for c in d["cases"]})==2 and len({c["rubric"]["id"] for c in d["cases"]})==2
    steps={x["id"] for x in design["flow"]["steps"]}
    assert len(steps)==11 and all(x["from"] in steps and x["to"] in steps and x["unknown"] in steps for x in design["flow"]["transitions"])
    assert len(design["modes"])==8 and len(design["activities"])==14
    original_views=read(P/"process-view-requirements.json")["views"]
    requirements={r["id"]:v["id"] for v in original_views for r in v["requirements"]}
    mapping=read(R/"requirement-mapping.json")["records"];assert len(mapping)==len(requirements)==108
    roots={"cases":d,"design":design}
    for x in mapping:
        assert requirements[x["requirement_id"]]==x["contract"] and x["formal_receipt"]=="NOT_ISSUED"
        for ref in x["evidence_paths"]:
            a=roots
            for k in ref.strip("/").split("/"):a=a[int(k)] if isinstance(a,list) else a[k]
    assert design["content_precheck"]["gate"]=="HOLD" and design["external_improvement"]["outcome"]=="NOT_RUN"
    result["R3"]={"cases":cases,"modes":8,"activities":14,"flow_steps":11,"transitions":len(design["flow"]["transitions"]),"mapping":dict(collections.Counter(x["status"] for x in mapping)),"formal_CQ":"26_NOT_RUN","content_gate":"HOLD","study":"NOT_RUN"}
    result["status"]="SAME_AUTHOR_FINITE_KNOWLEDGE_CHECKS_NOT_QUALIFICATION"
    result["persistent_db_files"]=0
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
