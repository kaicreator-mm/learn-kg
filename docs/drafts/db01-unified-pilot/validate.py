#!/usr/bin/env python3
"""Research-only common package validator, finite model interpreter, and in-memory SQL projection."""
import copy, hashlib, json, math, platform, sqlite3, unicodedata
from fractions import Fraction
from pathlib import Path
from importlib.metadata import version
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
PREFIX="learn-kg.draft.unified."
KINDS=("Source","EvidenceLocator","Claim","Element","ModelSpec","PolicySpec","Relation","Case","ValidationSpec","HanCharacter","Reading","Lexeme","Sense","ConditionSpec","TaskSpec","FlowSpec","ScenarioCase")
FIELDS={"bkt_observation":{"p","G","S","T","observation","independent","single_component"},
"recall":{"delta","half_life","unit"},"estimate_half_life":{"weights","features","unit"},
"inverse_half_life":{"delta","p","unit"},"policy":{"p","target","authorized","applicable","cost_minutes","budget_minutes"}}
VARS={"prediction_correct":{"p","G","S"},"posterior_correct":{"p","G","S"},"posterior_incorrect":{"p","G","S"},"next_prior":{"posterior","T"},
"recall":{"delta","half_life"},"estimate_half_life":{"weights","features"},"inverse_half_life":{"delta","p"}}
GUARDS=["NOT_AUTHORIZED","MISSING_OR_INVALID_INPUT","NOT_APPLICABLE","PROBABILITY_ABOVE_TARGET","COST_EXCEEDS_BUDGET","ALWAYS"]
ACTIONS=["REJECT_PERMISSION","UNKNOWN","UNKNOWN","WAIT","DEFER_BUDGET","SUGGEST_REVIEW"]
REF_FIELDS={"source_ref":"Source","evidence_refs":"EvidenceLocator","claim_refs":"Claim","model_ref":"ModelSpec","element_ref":"Element","form_refs":"HanCharacter","reading_refs":"Reading","lexeme_ref":"Lexeme","condition_refs":"ConditionSpec","sense_ref":"Sense"}
REL_TYPES={"defined_by_model":("Element","ModelSpec"),"informs_decision":("ModelSpec","PolicySpec"),"script_variant":("HanCharacter","HanCharacter"),"converse_in_context":("Sense","Sense")}
def require(b,msg):
    if not b: raise ValueError(msg)
def pairs(xs):
    d={}
    for k,v in xs:
        require(k not in d,"duplicate key")
        d[k]=v
    return d
def parse(b): return json.loads(b,object_pairs_hook=pairs,parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
def digest(b): return hashlib.sha256(b).hexdigest()
def verified(path,sha):
    b=path.read_bytes();require(digest(b)==sha,"hash mismatch: "+path.name);return parse(b)
def key(r): return (r["package_id"],r["version"],r["stable_id"])
def refwalk(x,path=""):
    if isinstance(x,dict):
        if set(x)=={"package_id","version","stable_id","kind"}: yield path,x
        else:
            for k,v in x.items(): yield from refwalk(v,path+"/"+k)
    elif isinstance(x,list):
        for i,v in enumerate(x): yield from refwalk(v,path+"/"+str(i))
def variables(e):
    if "var" in e:return {e["var"]}
    if "const" in e:return set()
    return set().union(*(variables(x) for x in e["args"]))
def validate_manifest(m):
    require(set(m)=={"schema_version","status","schema","legacy","packages"} and m["schema_version"]=="draft-unified-manifest-1" and m["status"]=="INVESTIGATION_ONLY","manifest identity")
    require(m["schema"]["file"]=="schema.json","schema path")
    entries={x["package_id"]:x for x in m["packages"]}
    require(len(entries)==len(m["packages"]),"duplicate package")
    for p,x in entries.items():
        require(set(x)=={"package_id","version","file","sha256","count","dependencies"} and x["version"]=="0.0.2" and p.startswith(PREFIX),"entry contract")
        require(x["file"]==p.removeprefix(PREFIX)+".json" and Path(x["file"]).name==x["file"],"unsafe path")
        require(type(x["count"]) is int and x["count"]>0,"invalid count")
        deps=x["dependencies"];require(len({d["package_id"] for d in deps})==len(deps),"duplicate dependency")
        for d in deps:
            require(set(d)=={"package_id","version","sha256"} and d["package_id"] in entries,"missing dependency")
            t=entries[d["package_id"]];require((d["version"],d["sha256"])==(t["version"],t["sha256"]),"dependency identity mismatch")
    def visit(p,trail,done):
        require(p not in trail,"dependency cycle")
        if p in done:return
        for d in entries[p]["dependencies"]:visit(d["package_id"],trail|{p},done)
        done.add(p)
    for p in entries:visit(p,set(),set())
    return entries
def load_packages(m,roots):
    entries=validate_manifest(m);out={};opened=[]
    def visit(p):
        require(p in entries,"unknown package")
        if p in out:return
        x=entries[p]
        for d in x["dependencies"]:visit(d["package_id"])
        a=verified(ROOT/x["file"],x["sha256"]);require((a["package_id"],a["version"],len(a["records"]))==(p,x["version"],x["count"]),"package identity/count")
        out[p]=a;opened.append(x["file"])
    for p in roots:visit(p)
    return out,opened
def validate(packages,m,schema):
    entries=validate_manifest(m);idx={}
    for p,a in packages.items():
        Draft202012Validator(schema).validate(a)
        require(p==a["package_id"] and entries[p]["version"]==a["version"],"package key mismatch")
        for r in a["records"]:
            k=(p,a["version"],r["stable_id"])
            require(k not in idx,"duplicate ID");idx[k]=r
    for p,a in packages.items():
        allowed={p}|{d["package_id"] for d in entries[p]["dependencies"]}
        def resolve(ref,kind):
            require(ref["package_id"] in allowed,"undeclared package dependency")
            t=idx.get(key(ref))
            require(t is not None and t["kind"]==ref["kind"]==kind,"unresolved or mistyped reference")
            return t
        for r in a["records"]:
            k=r["kind"]
            for f,t in REF_FIELDS.items():
                if f in r:
                    for v in r[f] if isinstance(r[f],list) else [r[f]]:resolve(v,t)
            if k=="Relation":
                left,right=REL_TYPES[r["relation_type"]];resolve(r["from_ref"],left);resolve(r["to_ref"],right)
            if k=="Claim": require(bool(r["evidence_refs"])!=(r["claim_type"]=="ENGINEERING_POLICY"),"claim source separation")
            if k=="ModelSpec":
                mode=r["numeric_domain"]; fs=r["formulas"]
                expected=set(list(VARS)[:4] if mode=="RATIONAL" else list(VARS)[4:])
                require(len(fs)==len(expected) and {f["name"] for f in fs}==expected,"formula identity")
                require(all(variables(f["expr"])==VARS[f["name"]] for f in fs),"formula variables")
                require(resolve(r["element_ref"],"Element")["model_ref"]=={"package_id":p,"version":a["version"],"stable_id":r["stable_id"],"kind":"ModelSpec"},"inconsistent model linkage")
                if mode=="RATIONAL":
                    require(set(r)=={"stable_id","kind","owner","status","topic","element_ref","claim_refs","numeric_domain","parameters","formulas","input_policy"},"rational model fields")
                    require(len(r["parameters"])==4 and {x["name"] for x in r["parameters"]}=={"p","G","S","T"} and all(x["range"]==[0,1] and x["unit"]=="probability" for x in r["parameters"]),"probability parameter contract")
                    require(r["input_policy"]=={"missing":"UNKNOWN","not_independent":"UNKNOWN","unmapped":"UNKNOWN","zero_likelihood":"REJECT_ZERO_LIKELIHOOD","invalid_parameter":"REJECT_PARAMETER","no_forgetting":True,"not_calibrated_for_any_population":True},"input policy contract")
                else:require("conditions" in r and "limits" in r and "input_policy" not in r and "parameters" not in r,"binary64 model fields")
            if k=="PolicySpec":
                require([x["guard"] for x in r["rules"]]==GUARDS and [x["action"] for x in r["rules"]]==ACTIONS,"policy rule contract")
                require(resolve(r["model_ref"],"ModelSpec")["numeric_domain"]=="BINARY64","policy model mismatch")
            if k=="Case":
                mode=r["mode"];t=resolve(r["target_ref"],"PolicySpec" if mode=="policy" else "ModelSpec")
                require(set(r["input"])==FIELDS[mode],"case field contract")
                if mode=="bkt_observation":
                    require(t["numeric_domain"]=="RATIONAL" and all(type(r["input"][x]) is str for x in ("p","G","S","T")) and r["input"]["observation"] in ("correct","incorrect","missing") and all(type(r["input"][x]) is bool for x in ("independent","single_component")),"BKT input contract")
                elif mode!="policy":require(t["numeric_domain"]=="BINARY64","HLR domain")
            if k=="ValidationSpec":
                if "target_ref" in r:resolve(r["target_ref"],"ModelSpec")
                require(all(v["kind"] in ("Case","ScenarioCase") for v in r["case_refs"]),"invalid validation case kind")
                for v in r["case_refs"]:resolve(v,v["kind"])
            validate_extended(r,resolve)
            # Every ref is resolved including nested occurrences not covered by the explicit field matrix.
            for _,v in refwalk(r):resolve(v,v["kind"])
    return idx
FLOW_OUTCOMES={"CORRECT","INCORRECT_RETRY","INCORRECT_EXHAUSTED","UNKNOWN","STOP"}
TRADE_CONDITIONS={"domain":"MONEY_GOODS_TRANSACTION","same_transaction":True,"completed":True,"from_role":"BUYER","to_role":"SELLER"}

def validate_extended(r,resolve):
    k=r["kind"]
    if k=="HanCharacter":
        require(r["codepoint"]==f"U+{ord(r['character']):04X}","codepoint mismatch")
    if k=="Reading":
        marks={"\u0304":1,"\u0301":2,"\u030c":3,"\u0300":4}
        found=[marks[x] for x in unicodedata.normalize("NFD",r["pinyin"]) if x in marks]
        require(found==[r["tone"]],"pinyin tone mismatch")
    if k=="Lexeme":
        forms=[resolve(v,"HanCharacter")["character"] for v in r["form_refs"]]
        require(len(set(forms))==len(forms) and r["lemma"] in forms,"invalid lexeme form")
    if k=="ConditionSpec":
        fields=[x["field"] for x in r["clauses"]]
        require(len(fields)==len(set(fields)),"duplicate condition field")
        require(all(type(x["equals"]) is type(TRADE_CONDITIONS[x["field"]]) for x in r["clauses"]),"condition value type")
    if k=="Relation":
        typ=r["relation_type"]
        if typ=="script_variant":
            a,b=resolve(r["from_ref"],"HanCharacter"),resolve(r["to_ref"],"HanCharacter")
            require(a["script"]=="SIMPLIFIED" and b["script"]=="TRADITIONAL" and a["character"]!=b["character"],"variant endpoint mismatch")
        if typ=="converse_in_context":
            a,b=resolve(r["from_ref"],"Sense"),resolve(r["to_ref"],"Sense")
            require(a["lexeme_ref"]!=b["lexeme_ref"] and a["domain"]==b["domain"]=="MONEY_GOODS_TRANSACTION","invalid converse endpoints")
            require(len(r.get("condition_refs",[]))==1,"missing converse condition")
            c=resolve(r["condition_refs"][0],"ConditionSpec")
            require({x["field"]:x["equals"] for x in c["clauses"]}==TRADE_CONDITIONS,"unbounded converse relation")
        else:require("condition_refs" not in r,"unsupported conditional relation")
    if k=="TaskSpec":
        sense=resolve(r["sense_ref"],"Sense");lex=resolve(sense["lexeme_ref"],"Lexeme")
        forms={resolve(v,"HanCharacter")["character"] for v in lex["form_refs"]}
        require(set(r["accepted_answers"])<=forms and len(set(r["accepted_answers"]))==len(r["accepted_answers"]),"task answer not a lexical form")
    if k=="FlowSpec":
        steps={x["id"]:x for x in r["steps"]};term={x["id"]:x["status"] for x in r["terminals"]}
        require(len(steps)==len(r["steps"]) and len(term)==len(r["terminals"]) and not (steps.keys()&term.keys()) and r["entry"] in steps,"invalid flow state identities")
        require(set(term.values())=={"ACTIVITY_COMPLETE","RETRY_EXHAUSTED","UNKNOWN","STOPPED"},"terminal coverage")
        for step in steps.values():
            resolve(step["task_ref"],"TaskSpec");trans={x["outcome"]:x["target"] for x in step["transitions"]}
            require(set(trans)==FLOW_OUTCOMES and len(trans)==len(step["transitions"]),"missing or duplicate outcome")
            require(all(t in steps or t in term for t in trans.values()),"unknown flow target")
            require(trans["INCORRECT_RETRY"]==step["id"],"retry must be bounded self-loop")
            for outcome,status in (("INCORRECT_EXHAUSTED","RETRY_EXHAUSTED"),("UNKNOWN","UNKNOWN"),("STOP","STOPPED")):
                require(term.get(trans[outcome])==status,"invalid terminal outcome")
            require(trans["CORRECT"] in steps or term.get(trans["CORRECT"])=="ACTIVITY_COMPLETE","invalid correct transition")
        visited=set();at=r["entry"]
        while at in steps:
            require(at not in visited,"unbounded correct cycle");visited.add(at)
            at=next(x["target"] for x in steps[at]["transitions"] if x["outcome"]=="CORRECT")
        require(visited==set(steps) and term.get(at)=="ACTIVITY_COMPLETE","unreachable step or success")
    if k=="ScenarioCase":
        if r["mode"]=="relation_condition":
            t=resolve(r["target_ref"],"Relation");require(t["relation_type"]=="converse_in_context" and set(r["input"])=={"context"} and set(r["expected"])=={"status"},"relation case contract")
        else:
            resolve(r["target_ref"],"FlowSpec");require(set(r["input"])=={"authorized","events"} and set(r["expected"])=={"status","state","processed","feedback_count","observations"},"flow case contract")

def condition_result(rel,context,idx):
    unknown=False
    for cr in rel["condition_refs"]:
        for clause in idx[key(cr)]["clauses"]:
            field=clause["field"]
            if field not in context:unknown=True
            elif type(context[field]) is not type(clause["equals"]) or context[field]!=clause["equals"]:return {"status":"NOT_APPLICABLE"}
    return {"status":"UNKNOWN" if unknown else "APPLIES"}

def run_flow(flow,x,idx):
    steps={s["id"]:s for s in flow["steps"]};term={s["id"]:s["status"] for s in flow["terminals"]}
    at=flow["entry"];processed=0;feedback=0;observations=[];seen={};attempts={}
    def result(status):return {"status":status,"state":at,"processed":processed,"feedback_count":feedback,"observations":observations}
    if x["authorized"] is not True:return result("REJECT_PERMISSION")
    for event in x["events"]:
        eid=event["event_id"]
        if eid in seen:
            if seen[eid]!=event:return result("REJECT_EVENT_CONFLICT")
            continue
        if at in term:return result("REJECT_AFTER_TERMINAL")
        if processed>=flow["max_events"]:return result("BUDGET_EXHAUSTED")
        s=steps[at];task=idx[key(s["task_ref"])]
        if event["event"]=="EXIT":outcome="STOP"
        else:
            if event["task_id"]!=task["stable_id"]:return result("REJECT_TASK")
            if not event["independent"] or event["answer"]=="":outcome="UNKNOWN"
            else:
                correct=event["answer"] in task["accepted_answers"]
                attempts[at]=attempts.get(at,0)+1
                observations.append({"event_id":eid,"task_id":task["stable_id"],"result":"CORRECT" if correct else "INCORRECT"})
                outcome="CORRECT" if correct else "INCORRECT_RETRY" if attempts[at]<s["max_attempts"] else "INCORRECT_EXHAUSTED"
                if outcome=="INCORRECT_RETRY":feedback+=1
        seen[eid]=event;processed+=1;at=next(t["target"] for t in s["transitions"] if t["outcome"]==outcome)
    return result(term.get(at,"INCOMPLETE"))

def run_scenario(r,idx):
    t=idx[key(r["target_ref"])]
    if r["mode"]=="relation_condition":return condition_result(t,r["input"]["context"],idx)
    return run_flow(t,r["input"],idx)

def finite(x):
    try:return type(x) in (int,float) and math.isfinite(x)
    except OverflowError:return False
def evaluate(e,env,domain):
    if "var" in e:return env[e["var"]]
    if "const" in e:return Fraction(e["const"]) if domain=="RATIONAL" else float(e["const"])
    a=[evaluate(x,env,domain) for x in e["args"]];o=e["op"]
    if domain=="RATIONAL":require(o in ("add","sub","mul","div"),"rational op mismatch")
    if o=="add":return a[0]+a[1]
    if o=="sub":return a[0]-a[1]
    if o=="mul":return a[0]*a[1]
    if o=="div":return a[0]/a[1]
    if o=="neg":return -a[0]
    if o=="pow2":return 2.0**a[0]
    if o=="log2":return math.log2(a[0])
    if o=="dot":return math.fsum(x*y for x,y in zip(*a,strict=True))
    raise ValueError("unapproved op")
def run(spec,mode,x):
    if mode=="policy":
        valid=all(finite(x[k]) for k in ("p","target","cost_minutes","budget_minutes"))
        valid=valid and 0<=x["p"]<=1 and 0<x["target"]<1 and x["cost_minutes"]>=0 and x["budget_minutes"]>=0
        checks={"NOT_AUTHORIZED":lambda:x["authorized"] is not True,"MISSING_OR_INVALID_INPUT":lambda:not valid,"NOT_APPLICABLE":lambda:x["applicable"] is not True,"PROBABILITY_ABOVE_TARGET":lambda:x["p"]>x["target"],"COST_EXCEEDS_BUDGET":lambda:x["cost_minutes"]>x["budget_minutes"],"ALWAYS":lambda:True}
        for r in spec["rules"]:
            if checks[r["guard"]]():return {"status":r["action"]}
        raise ValueError("no terminal")
    domain=spec["numeric_domain"]; fs={f["name"]:f["expr"] for f in spec["formulas"]}
    if mode=="bkt_observation":
        try: env={k:Fraction(x[k]) for k in ("p","G","S","T")}
        except (ValueError,ZeroDivisionError):return {"status":"REJECT_PARAMETER"}
        if any(not 0<=v<=1 for v in env.values()):return {"status":"REJECT_PARAMETER"}
        if x["observation"]=="missing" or not x["independent"] or not x["single_component"]:return {"status":"UNKNOWN"}
        pred=evaluate(fs["prediction_correct"],env,domain)
        try:post=evaluate(fs["posterior_"+x["observation"]],env,domain)
        except ZeroDivisionError:return {"status":"REJECT_ZERO_LIKELIHOOD"}
        nxt=evaluate(fs["next_prior"],{**env,"posterior":post},domain)
        require(all(0<=v<=1 for v in (pred,post,nxt)),"invalid BKT output")
        return {"status":"OK","prediction_correct":str(pred),"posterior":str(post),"next_prior":str(nxt)}
    if x["unit"]!="day":return {"status":"REJECT_INPUT"}
    if mode=="recall":valid=finite(x["delta"]) and finite(x["half_life"]) and x["delta"]>=0 and x["half_life"]>0
    elif mode=="inverse_half_life":valid=finite(x["delta"]) and finite(x["p"]) and x["delta"]>0 and 0<x["p"]<1
    else:valid=isinstance(x["weights"],list) and isinstance(x["features"],list) and len(x["weights"])==len(x["features"]) and all(finite(y) for y in x["weights"]+x["features"])
    if not valid:return {"status":"REJECT_INPUT"}
    try:y=evaluate(fs[mode],x,domain)
    except (OverflowError,ValueError,ZeroDivisionError):return {"status":"REJECT_NUMERIC_RANGE"}
    if not finite(y) or y<=0 or (mode=="recall" and y>1):return {"status":"REJECT_NUMERIC_RANGE"}
    return {"status":"OK","value":y}
def equivalent(a,b):
    return a.keys()==b.keys() and all(math.isclose(a[k],b[k],rel_tol=1e-12,abs_tol=1e-12) if k=="value" else a[k]==b[k] for k in a)
def legacy_roundtrip(p,m):
    originals={}
    for x in m["legacy"]:
        require(x["path"] in ("docs/drafts/db01-bkt-pilot/records.json","docs/drafts/db01-hlr-pilot/records.json"),"legacy path")
        q=verified(REPO/x["path"],x["sha256"]);require(len(q["records"])==x["count"],"legacy count")
        for r in q["records"]:require(r["stable_id"] not in originals,"legacy duplicate");originals[r["stable_id"]]=r
    def unbind(v):
        if isinstance(v,list):return [unbind(x) for x in v]
        if isinstance(v,dict):
            if set(v)=={"package_id","version","stable_id","kind"}:return {**v,"package_id":"learn-kg.draft."+v["stable_id"].split(":")[0],"version":"0.0.1"}
            return {k:unbind(x) for k,x in v.items()}
        return v
    n=0
    for a in p.values():
        for row in a["records"]:
            r=unbind(row);b=r["stable_id"].startswith("bkt:")
            if r["kind"]=="Source" and not b:r["doi"]=r.pop("identifier")
            if r["kind"]=="Case" and b:r["model_ref"]=r.pop("target_ref");r.pop("mode")
            if r["kind"]=="ModelSpec":
                r.pop("numeric_domain")
                if b:r["policy"]=r.pop("input_policy")
            require(r==originals.pop(r["stable_id"]),"lossy migration: "+r["stable_id"]);n+=1
    require(not originals,"lost record")
    return n
def sql_project(p,idx,schema):
    # Only a memory connection. No physical database, ATTACH, export or persistence.
    db=sqlite3.connect(":memory:");db.execute("PRAGMA foreign_keys=ON")
    require(db.execute("PRAGMA foreign_keys").fetchone()==(1,),"foreign keys disabled")
    db.executescript("""CREATE TABLE registry(package_id TEXT NOT NULL,version TEXT NOT NULL,stable_id TEXT NOT NULL,kind TEXT NOT NULL,owner TEXT NOT NULL,status TEXT NOT NULL,PRIMARY KEY(package_id,version,stable_id),UNIQUE(package_id,version,stable_id,kind));
CREATE TABLE refs(src_package TEXT NOT NULL,src_version TEXT NOT NULL,src_id TEXT NOT NULL,path TEXT NOT NULL,target_package TEXT NOT NULL,target_version TEXT NOT NULL,target_id TEXT NOT NULL,target_kind TEXT NOT NULL,PRIMARY KEY(src_package,src_version,src_id,path),FOREIGN KEY(src_package,src_version,src_id) REFERENCES registry(package_id,version,stable_id),FOREIGN KEY(target_package,target_version,target_id,target_kind) REFERENCES registry(package_id,version,stable_id,kind));
CREATE INDEX refs_reverse ON refs(target_package,target_version,target_id,target_kind);""")
    columns={}
    for kind in KINDS:
        props=schema["$defs"][kind]["properties"];names=[n for n in props if n not in ("stable_id","kind","owner","status")]
        # Scalar SQL columns, JSON text only for structurally nested attributes; no whole-record payload column.
        types={n:("TEXT" if props[n].get("type")=="string" or "const" in props[n] and isinstance(props[n]["const"],str) or "enum" in props[n] else "INTEGER" if props[n].get("type") in ("integer","boolean") else "JSON") for n in names}
        columns[kind]=types
        decl=", ".join(f'"{n}" '+(f'TEXT CHECK ("{n}" IS NULL OR json_valid("{n}"))' if t=="JSON" else t) for n,t in types.items())
        db.execute('CREATE TABLE "k_'+kind+'"(package_id TEXT NOT NULL,version TEXT NOT NULL,stable_id TEXT NOT NULL,kind TEXT NOT NULL CHECK(kind=\''+kind+'\'),'+decl+',PRIMARY KEY(package_id,version,stable_id),FOREIGN KEY(package_id,version,stable_id,kind) REFERENCES registry(package_id,version,stable_id,kind))')
    for k,r in idx.items():db.execute("INSERT INTO registry VALUES(?,?,?,?,?,?)",(*k,r["kind"],r["owner"],r["status"]))
    refcount=0
    for k,r in idx.items():
        types=columns[r["kind"]]; vals=[]
        for n,t in types.items():
            v=r.get(n);vals.append(json.dumps(v,ensure_ascii=False,separators=(",",":")) if t=="JSON" and n in r else v)
        db.execute('INSERT INTO "k_'+r["kind"]+'" VALUES('+','.join('?' for _ in range(4+len(vals)))+')',(*k,r["kind"],*vals))
        for path,t in refwalk(r):
            db.execute("INSERT INTO refs VALUES(?,?,?,?,?,?,?,?)",(*k,path,*key(t),t["kind"]));refcount+=1
    db.commit()
    require(not db.execute("PRAGMA foreign_key_check").fetchall(),"FK violation")
    for k,r in idx.items():
        rr=db.execute("SELECT kind,owner,status FROM registry WHERE package_id=? AND version=? AND stable_id=?",k).fetchone()
        restored={"stable_id":k[2],"kind":rr[0],"owner":rr[1],"status":rr[2]}
        types=columns[r["kind"]];vals=db.execute('SELECT '+','.join('"'+n+'"' for n in types)+' FROM "k_'+r["kind"]+'" WHERE package_id=? AND version=? AND stable_id=?',k).fetchone()
        for (n,t),v in zip(types.items(),vals,strict=True):
            if v is not None:restored[n]=json.loads(v) if t=="JSON" else bool(v) if schema["$defs"][r["kind"]]["properties"][n].get("type")=="boolean" else v
        require(restored==r,"SQL roundtrip "+str(k))
    expected_refs={(k,path,key(t),t["kind"]) for k,r in idx.items() for path,t in refwalk(r)}
    actual_refs={(tuple(row[:3]),row[3],tuple(row[4:7]),row[7]) for row in db.execute("SELECT * FROM refs")}
    require(expected_refs==actual_refs and len(actual_refs)==refcount,"reference mismatch")
    policy=db.execute("SELECT src_id,target_id FROM refs WHERE src_id=? AND path=? AND target_kind=?",("hlr:policy:review","/model_ref","ModelSpec")).fetchall()
    require(policy==[("hlr:policy:review","hlr:model:hlr")],"cross-package lookup")
    key0=next(iter(idx));r0=idx[key0]
    negative=[]
    for name,sql,args in [
      ("sql-duplicate","INSERT INTO registry VALUES(?,?,?,?,?,?)",(*key0,r0["kind"],r0["owner"],r0["status"])),
      ("sql-orphan","INSERT INTO refs VALUES(?,?,?,?,?,?,?,?)",(*key0,"/invalid",*key0[:2],"not-present","Claim")),
      ("sql-wrong-kind","INSERT INTO refs VALUES(?,?,?,?,?,?,?,?)",(*key0,"/invalid",*key0,"Case" if r0["kind"]!="Case" else "Source"))]:
        try:db.execute(sql,args)
        except sqlite3.IntegrityError:db.rollback();negative.append(name)
        else:raise AssertionError(name)
    require(db.execute("SELECT count(*) FROM registry").fetchone()[0]==len(idx),"rollback count")
    require(db.execute("SELECT count(*) FROM refs").fetchone()[0]==refcount,"rollback references")
    table_counts={k:db.execute('SELECT count(*) FROM "k_'+k+'"').fetchone()[0] for k in KINDS}
    db.close()
    return {"rows":len(idx),"record_roundtrip":len(idx),"references":refcount,"reference_roundtrip":refcount,"per_kind_rows":table_counts,"foreign_key_check":"PASS","cross_package_query":policy,"negative_tests":negative,"database":":memory:","sqlite_version":sqlite3.sqlite_version}
def main():
    m=parse((ROOT/"manifest.json").read_bytes());schema=verified(ROOT/m["schema"]["file"],m["schema"]["sha256"]);Draft202012Validator.check_schema(schema)
    p,opened=load_packages(m,[PREFIX+"bkt",PREFIX+"review",PREFIX+"flow"]);idx=validate(p,m,schema)
    review,r_open=load_packages(m,[PREFIX+"review"]);validate(review,m,schema);require(r_open==["hlr.json","review.json"],"review route")
    bkt,b_open=load_packages(m,[PREFIX+"bkt"]);validate(bkt,m,schema);require(b_open==["bkt.json"],"BKT route")
    flow,flow_open=load_packages(m,[PREFIX+"flow"]);validate(flow,m,schema);require(flow_open==["chinese.json","flow.json"],"flow route")
    legacy=legacy_roundtrip({k:v for k,v in p.items() if k in (PREFIX+"bkt",PREFIX+"hlr",PREFIX+"review")},m)
    results=[]
    for k,r in idx.items():
        if r["kind"]!="Case":continue
        actual=run(idx[key(r["target_ref"])],r["mode"],r["input"])
        require(equivalent(actual,r["expected"]),"case mismatch "+r["stable_id"]);results.append({"id":r["stable_id"],"expected":r["expected"],"actual":actual,"status":"PASS"})
    pol=next(r for r in idx.values() if r["kind"]=="PolicySpec");mod=idx[key(pol["model_ref"])]
    comp=[]
    for name,d,b,a,expected in [("due",4,5,True,"SUGGEST_REVIEW"),("wait",1,5,True,"WAIT"),("budget",4,3,True,"DEFER_BUDGET"),("permission",4,5,False,"REJECT_PERMISSION"),("invalid-time",-1,5,True,"UNKNOWN")]:
        y=run(mod,"recall",{"delta":d,"half_life":2,"unit":"day"});z=run(pol,"policy",{"p":y.get("value"),"target":.5,"authorized":a,"applicable":y["status"]=="OK","cost_minutes":4,"budget_minutes":b})
        require(z["status"]==expected,"composition");comp.append({"id":name,"prediction":y,"expected":expected,"actual":z["status"],"status":"PASS"})
    negatives=[]
    def reject(name,fn):
        try:fn()
        except (ValueError,ValidationError,FileNotFoundError) as e:negatives.append({"id":name,"error":type(e).__name__});return
        raise AssertionError(name)
    def change(name,fn):
        a,b=copy.deepcopy(p),copy.deepcopy(m);fn(a,b);reject(name,lambda:validate(a,b,schema))
    def first(a,kind):return next(r for v in a.values() for r in v["records"] if r["kind"]==kind)
    def review_entry(b):return next(x for x in b["packages"] if x["package_id"]==PREFIX+"review")
    change("duplicate-id",lambda a,b:a[PREFIX+"bkt"]["records"].append(copy.deepcopy(a[PREFIX+"bkt"]["records"][0])))
    change("unknown-field",lambda a,b:first(a,"Source").update(extra=1))
    change("wrong-kind",lambda a,b:first(a,"PolicySpec")["model_ref"].update(kind="Claim"))
    change("wrong-version",lambda a,b:first(a,"PolicySpec")["model_ref"].update(version="0.0.1"))
    change("orphan-ref",lambda a,b:first(a,"PolicySpec")["model_ref"].update(stable_id="hlr:none"))
    change("undeclared-dependency",lambda a,b:review_entry(b).update(dependencies=[]))
    change("missing-package",lambda a,b:a.pop(PREFIX+"hlr"))
    change("dependency-digest",lambda a,b:review_entry(b)["dependencies"][0].update(sha256="0"*64))
    change("unsafe-path",lambda a,b:review_entry(b).update(file="../review.json"))
    change("unapproved-op",lambda a,b:first(a,"ModelSpec")["formulas"][0]["expr"].update(op="exec"))
    change("policy-order",lambda a,b:first(a,"PolicySpec")["rules"].reverse())
    change("unearned-qualification",lambda a,b:first(a,"Claim").update(status="ACCEPTED_SCOPED"))
    change("missing-evidence",lambda a,b:first(a,"Claim").update(evidence_refs=[]))
    reject("hash-mismatch",lambda:verified(ROOT/"bkt.json","0"*64))
    reject("duplicate-key",lambda:parse(b'{"a":1,"a":2}'))
    cyc=copy.deepcopy(m);e=next(x for x in cyc["packages"] if x["package_id"]==PREFIX+"hlr");r=review_entry(cyc);e["dependencies"]=[{"package_id":r["package_id"],"version":r["version"],"sha256":r["sha256"]}]
    reject("dependency-cycle",lambda:validate_manifest(cyc))
    change("codepoint-mismatch",lambda a,b:first(a,"HanCharacter").update(codepoint="U+0000"))
    change("tone-mismatch",lambda a,b:first(a,"Reading").update(tone=1))
    change("missing-condition",lambda a,b:next(r for r in a[PREFIX+"chinese"]["records"] if r["kind"]=="Relation" and r["relation_type"]=="converse_in_context").pop("condition_refs"))
    change("duplicate-condition-field",lambda a,b:first(a,"ConditionSpec")["clauses"].append(copy.deepcopy(first(a,"ConditionSpec")["clauses"][0])))
    change("wrong-task-answer",lambda a,b:first(a,"TaskSpec").update(accepted_answers=["非"]))
    change("invalid-flow-task",lambda a,b:first(a,"FlowSpec")["steps"][0]["task_ref"].update(kind="Sense"))
    change("unbounded-flow-cycle",lambda a,b:first(a,"FlowSpec")["steps"][0]["transitions"][0].update(target="buy"))
    change("flow-retry-edge",lambda a,b:first(a,"FlowSpec")["steps"][0]["transitions"][1].update(target="sell"))
    change("wrong-scenario-target",lambda a,b:first(a,"ScenarioCase")["target_ref"].update(kind="FlowSpec"))
    scenarios=[]
    for r in idx.values():
        if r["kind"]!="ScenarioCase":continue
        actual=run_scenario(r,idx);require(actual==r["expected"],"scenario mismatch "+r["stable_id"]);scenarios.append({"id":r["stable_id"],"mode":r["mode"],"expected":r["expected"],"actual":actual,"status":"PASS"})
    limited=copy.deepcopy(next(r for r in idx.values() if r["kind"]=="FlowSpec"));limited["max_events"]=1
    complete=next(r for r in idx.values() if r["stable_id"]=="flow:case:complete");budget=run_flow(limited,complete["input"],idx)
    require(budget=={"status":"BUDGET_EXHAUSTED","state":"sell","processed":1,"feedback_count":0,"observations":[{"event_id":"e1","task_id":"flow:task:buy","result":"CORRECT"}]},"budget cap")
    sql=sql_project(p,idx,schema)
    print(json.dumps({"scope":"DB01_INVESTIGATION_ONLY","python":platform.python_version(),"jsonschema":version("jsonschema"),"legacy_roundtrip":legacy,"records":len(idx),"routes":{"all":opened,"review":r_open,"bkt":b_open,"flow":flow_open},"cases":results,"composition":comp,"scenarios":scenarios,"budget_cap":budget,"negative_tests":negatives,"sql":sql,"files_sha256":{n:digest((ROOT/n).read_bytes()) for n in ("manifest.json","schema.json","bkt.json","hlr.json","review.json","chinese.json","flow.json","validate.py")},"professional_qualification":"NOT_RUN","persistent_sqlite_generated":False},ensure_ascii=False))
if __name__=="__main__":main()
