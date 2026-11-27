"""Finite remediation witness. Historic G05-G06/D4 remain immutable."""
import copy, importlib.util, json, pathlib, sys
from collections import Counter
ROOT=pathlib.Path(__file__).resolve().parents[7]
D=ROOT/"docs/drafts/s01/depth/D3"
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
old=load("old_probe",D/"G05-G06/probe.py")
project=load("old_projection",D/"D4/project.py")
def textid(v):return isinstance(v,str) and bool(v.strip()) and v==v.strip()
def ids(x,*keys):return all(textid(x.get(k)) for k in keys)
CHECKS=("fact","domain_language","rubric","source","rights","accessibility")
def content_gate(x):
    if not ids(x,"content_id","content_digest","version","current_version","author_id") or x["version"]!=x["current_version"]:
        return "HOLD_CONTENT_ID"
    if x.get("authorized") is not True:return "HOLD_AUTH"
    receipts=x.get("receipts")
    if not isinstance(receipts,dict) or set(receipts)!=set(CHECKS):return "HOLD_INCOMPLETE"
    seen=set()
    for k in CHECKS:
        r=receipts[k]
        if not isinstance(r,dict) or not ids(r,"receipt_id","evidence_id","content_id","digest","version","reviewer_id","review_role"):
            return "HOLD_RECEIPT_ID"
        if r["receipt_id"] in seen:return "HOLD_RECEIPT_ID"
        seen.add(r["receipt_id"])
        if (r["content_id"],r["digest"],r["version"])!=(x["content_id"],x["content_digest"],x["version"]) or r["reviewer_id"]==x["author_id"] or r["review_role"]!="QUALIFIED_REVIEWER" or r.get("independent") is not True:
            return "HOLD_RECEIPT_SCOPE"
        if r.get("decision")=="FAIL":return "REJECT_CANDIDATE"
        if r.get("decision")!="PASS":return "HOLD_UNKNOWN"
    return "ELIGIBLE_FOR_SEPARATE_DELIVERY_REVIEW"
def improvement_gate(x):
    if x.get("withdrawn") is True:return "STOP_AND_REVIEW"
    if x.get("withdrawn") is not False:return "HOLD_WITHDRAWAL"
    if x.get("authorized") is not True or x.get("ethics")!="CLEARED":return "HOLD_ETHICS_AUTH"
    fields=("protocol_id","evaluated_protocol_id","protocol_version","evaluated_protocol","current_protocol_version","candidate_id","tested_candidate_id","candidate_version","tested_version","current_candidate_version")
    if not ids(x,*fields):return "HOLD_VERSION"
    if not (x["protocol_id"]==x["evaluated_protocol_id"] and x["protocol_version"]==x["evaluated_protocol"]==x["current_protocol_version"] and x["candidate_id"]==x["tested_candidate_id"] and x["candidate_version"]==x["tested_version"]==x["current_candidate_version"]):return "HOLD_VERSION"
    if not all(x.get(k) is True for k in ("outcomes_prespecified","comparison_appropriate","attrition_assessed","construct_comparable")):return "EXPLORATORY_ONLY"
    if x.get("safety_outcome")!="ACCEPTABLE":return "HOLD_OR_ROLLBACK"
    if x.get("outcome")=="NEGATIVE":return "KEEP_BASELINE"
    if x.get("outcome")!="SUPPORTED":return "HOLD_INCONCLUSIVE"
    if not ids(x,"author_id","reviewer_id","review_receipt_id","evaluation_evidence_id") or x["author_id"]==x["reviewer_id"] or x.get("reviewer_role")!="QUALIFIED_REVIEWER" or x.get("independent_review")!="ACCEPT_SCOPED" or x.get("review_binding")!=[x["protocol_id"],x["protocol_version"],x["candidate_id"],x["candidate_version"],x["evaluation_evidence_id"]]:return "HOLD_REVIEW"
    if x.get("human_approval") is not True or not ids(x,"approver_id","approval_receipt_id") or x.get("approval_binding")!=[x["candidate_id"],x["candidate_version"],x["review_receipt_id"]]:return "HOLD_APPROVAL"
    return "ELIGIBLE_FOR_SEPARATE_RELEASE_DECISION"
def provenance(cx):
    # Source-level locator never impersonates a claim-to-source locator.
    cx.execute("""CREATE TABLE recorded_locator(edge_id TEXT PRIMARY KEY REFERENCES edges(id),claim_id TEXT NOT NULL REFERENCES claims(id),source_id TEXT NOT NULL REFERENCES sources(id),claim_field TEXT,claim_locator TEXT,source_locator TEXT NOT NULL,location_status TEXT NOT NULL,attribution TEXT NOT NULL,qualification TEXT NOT NULL)""")
    counts=Counter()
    for edge,cid,sid,cp,sp in cx.execute("SELECT e.id,c.id,s.id,c.payload,s.payload FROM edges e JOIN claims c ON c.id=e.source JOIN sources s ON s.id=e.target WHERE e.type='CITES_RECORDED_SOURCE'").fetchall():
        c=json.loads(cp);s=json.loads(sp)
        fields=[k for k in ("source_locator","evidence_locator_note") if textid(c.get(k))]
        if len(fields)>1:field=None;loc=None;status="HOLD_CONFLICTING_LOCATOR_FIELDS"
        elif fields:
            field=fields[0];loc=c[field]
            status="RECORDED_CLAIM_LOCATOR_NOT_REVERIFIED" if len(c["source_refs"])==1 else "HOLD_MULTI_SOURCE_ATTRIBUTION"
        else:field=None;loc=None;status="HOLD_CLAIM_LOCATOR_MISSING"
        attribution="EXPLICIT_SINGLE_RECORDED_SOURCE" if len(c["source_refs"])==1 else "MULTI_SOURCE_NOT_DISAMBIGUATED"
        cx.execute("INSERT INTO recorded_locator VALUES(?,?,?,?,?,?,?,?,?)",(edge,cid,sid,field,loc,s["locator"],status,attribution,"NOT_RUN"))
        counts[status]+=1
    rows=cx.execute("SELECT claim_id,source_id,claim_field,claim_locator,source_locator,location_status FROM recorded_locator").fetchall()
    for cid,sid,field,loc,sl,status in rows:
        cp=json.loads(cx.execute("SELECT payload FROM claims WHERE id=?",(cid,)).fetchone()[0]);sp=json.loads(cx.execute("SELECT payload FROM sources WHERE id=?",(sid,)).fetchone()[0])
        assert sid in cp["source_refs"] and sl==sp["locator"]
        if field:assert loc==cp[field]
        else:assert loc is None
    assert len(rows)==974 and not cx.execute("PRAGMA foreign_key_check").fetchall()
    x=cx.execute("SELECT claim_field,claim_locator,location_status FROM recorded_locator WHERE claim_id='K01.01.01.D4.01' AND source_id='K01-S33'").fetchone()
    assert x==("evidence_locator_note","PDF p.176引言；定义保留时点条件","RECORDED_CLAIM_LOCATOR_NOT_REVERIFIED"),x
    assert cx.execute("SELECT count(*) FROM recorded_locator WHERE qualification!='NOT_RUN'").fetchone()[0]==0
    return dict(counts),list(x)
def main():
    f=pathlib.Path(__file__).with_name("fixtures.json");d=json.loads(f.read_text())
    historic=json.loads((D/"G05-G06/fixtures.json").read_text())
    # Original fail-open cases reproduced from exact historic functions; do not rewrite historic evidence.
    a=copy.deepcopy(historic["content"][0]["input"]);a.pop("version")
    for r in a["receipts"].values():r.pop("version")
    b=copy.deepcopy(historic["improvement"][0]["input"])
    for k in ("protocol_version","evaluated_protocol","candidate_version","tested_version"):b.pop(k)
    c=copy.deepcopy(historic["improvement"][0]["input"]);c.pop("withdrawn")
    original=[old.content_gate(a),old.improvement_gate(b),old.improvement_gate(c)]
    assert original==["ELIGIBLE_FOR_SEPARATE_DELIVERY_REVIEW","ELIGIBLE_FOR_SEPARATE_RELEASE_DECISION","ELIGIBLE_FOR_SEPARATE_RELEASE_DECISION"]
    result={}
    for group,fn in [("content",content_gate),("improvement",improvement_gate)]:
        cases=d[group];base=d[group+"_base"];passed=[]
        for case in cases:
            x=copy.deepcopy(base)
            for path,v in case.get("set",[]):
                z=x;keys=path.split(".")
                for k in keys[:-1]:z=z[k]
                z[keys[-1]]=v
            for path in case.get("remove",[]):
                z=x;keys=path.split(".")
                for k in keys[:-1]:z=z[k]
                z.pop(keys[-1])
            actual=fn(x);assert actual==case["expect"],(case["id"],actual,case["expect"])
            passed.append(case["id"])
        result[group]={"passed":len(passed),"ids":passed}
    m=project.decode((D/"D4/manifest.json").read_bytes())
    cx,_,_,_=project.projection(ROOT,m,"research-overlay")
    loc,query=provenance(cx)
    # Apply explicit narrowed candidate edge only in the revised research view.
    corr=json.loads(pathlib.Path(__file__).with_name("relation-correction.json").read_text())
    raw=json.loads(cx.execute("SELECT payload FROM edges WHERE id=?",(corr["id"],)).fetchone()[0])
    assert raw==corr["previous"]
    cx.execute("UPDATE edges SET payload=? WHERE id=?",(project.compact(corr["replacement"]),corr["id"]))
    assert json.loads(cx.execute("SELECT payload FROM edges WHERE id=?",(corr["id"],)).fetchone()[0])==corr["replacement"]
    assert corr["replacement"]["qualification"]=="NOT_RUN" and corr["replacement"]["materialize_accepted"] is False
    cx.close()
    print(json.dumps({"status":"SCOPED_REMEDIATION_CANDIDATE_ONLY","original_fail_open_reproduced":original,"gate_results":result,"recorded_locator_rows":974,"locator_status_counts":loc,"K01_locator_query":query,"narrowed_relation":corr["id"],"qualification":"NOT_RUN","persistent_db_files":0,"oracle":"SAME_AUTHOR_FIXED_EXPECTATIONS"},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
