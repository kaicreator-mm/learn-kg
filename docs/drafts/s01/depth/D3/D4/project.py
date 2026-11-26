"""D4 read-only text projection probe; no persistent database or formal schema."""
import collections, hashlib, json, pathlib, sqlite3, subprocess, sys
ROOT=pathlib.Path(__file__).resolve().parents[6]
BASE="c53d10f77b77c813233994f3fd9814b5fc20ccde"
P="docs/drafts/s01/"
D=P+"depth/D3/"
HERE=D+"D4/"
def require(ok,msg):
    if not ok: raise ValueError(msg)
def unique_pairs(pairs):
    d={}
    for k,v in pairs:
        require(k not in d,"duplicate JSON key "+k);d[k]=v
    return d
def decode(b): return json.loads(b.decode("utf-8"),object_pairs_hook=unique_pairs)
def digest(b): return hashlib.sha256(b).hexdigest()
def compact(v): return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def gitblob(b): return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def manifest(root):
    groups={k:[] for k in ("learning-core","chinese","learning-process","research-overlay")}
    def add(pkg,path,kind):
        b=(root/path).read_bytes();groups[pkg].append([path,kind,gitblob(b),digest(b)])
    for f in sorted((root/P).glob("*/coverage.json")):
        mod=f.parent.name;pkg="learning-core" if mod.startswith("K") else "chinese"
        for n,kind in (("coverage.json","coverage"),("claims.json","claims"),("sources.json","sources"),("cases.json","cases")):
            add(pkg,P+mod+"/"+n,kind)
    for f in sorted((root/(P+"depth/D2")).glob("**/claims.json")):
        pkg="learning-core" if f.parent.name.startswith("K") else "chinese"
        add(pkg,f.relative_to(root).as_posix(),"claims");add(pkg,f.with_name("sources.json").relative_to(root).as_posix(),"sources")
    add("learning-process",D+"G02/composition-contracts.json","contracts")
    add("learning-process",D+"G03/claim-bindings.json","bindings")
    add("learning-process",HERE+"flow-candidate.json","flow")
    add("research-overlay",D+"G01/relation-types.json","relation_types")
    add("research-overlay",D+"G01/semantic-candidates.json","semantic")
    add("research-overlay",D+"G01/anchor-ledger.json","anchors")
    add("research-overlay",D+"G05-G06/source-recheck.json","source_recheck")
    deps={"learning-core":[],"chinese":[],"learning-process":["learning-core"],"research-overlay":["learning-core","chinese","learning-process"]}
    # These dependencies apply only to this candidate projection, not formal physical package ownership.
    packages={}
    for pkg,files in groups.items():
        dependencies=[{"package_id":k,"version":BASE,"manifest_digest":packages[k]["manifest_digest"]} for k in deps[pkg]]
        body={"package_id":pkg,"version":BASE,"status":"DRAFT_ONLY","dependencies":dependencies,"files":files}
        packages[pkg]={**body,"manifest_digest":digest(compact(body).encode())}
    return {"base":BASE,"schema_version":"draft-d4-projection-1","status":"DRAFT_ONLY_NOT_RELEASE_MANIFEST","file_columns":["path","record_kind","git_blob","sha256"],"packages":packages,"excluded":["private HSK staging / source bytes / learner data","accepted knowledge or release receipts","formal DB01/DB02 schema and physical publishing"]}
DDL="""
PRAGMA foreign_keys=ON;
CREATE TABLE registry(id TEXT PRIMARY KEY, kind TEXT NOT NULL, package TEXT NOT NULL);
CREATE TABLE modules(id TEXT PRIMARY KEY REFERENCES registry(id));
CREATE TABLE topics(id TEXT PRIMARY KEY REFERENCES registry(id), module TEXT NOT NULL REFERENCES modules(id), requirement TEXT NOT NULL, label TEXT NOT NULL, payload TEXT NOT NULL);
CREATE TABLE sources(id TEXT PRIMARY KEY REFERENCES registry(id), title TEXT NOT NULL, url TEXT NOT NULL, locator TEXT NOT NULL, access TEXT, rights TEXT, payload TEXT NOT NULL);
CREATE TABLE claims(id TEXT PRIMARY KEY REFERENCES registry(id), topic TEXT NOT NULL REFERENCES topics(id), statement TEXT NOT NULL, claim_type TEXT NOT NULL, conditions TEXT NOT NULL, negative_boundary TEXT NOT NULL, evidence_status TEXT NOT NULL, qualification TEXT NOT NULL, payload TEXT NOT NULL);
CREATE TABLE cases(id TEXT PRIMARY KEY REFERENCES registry(id), topic TEXT NOT NULL REFERENCES topics(id), fixture TEXT NOT NULL, payload TEXT NOT NULL);
CREATE TABLE contracts(id TEXT PRIMARY KEY REFERENCES registry(id), title TEXT NOT NULL, inputs TEXT NOT NULL, outputs TEXT NOT NULL, guard TEXT NOT NULL, hold TEXT NOT NULL, payload TEXT NOT NULL);
CREATE TABLE flows(id TEXT PRIMARY KEY, entry TEXT NOT NULL, payload TEXT NOT NULL);
CREATE TABLE flow_steps(flow TEXT REFERENCES flows(id), id TEXT, contract TEXT REFERENCES contracts(id), payload TEXT NOT NULL, PRIMARY KEY(flow,id));
CREATE TABLE flow_guards(flow TEXT REFERENCES flows(id), id TEXT, contract TEXT REFERENCES contracts(id), payload TEXT NOT NULL, PRIMARY KEY(flow,id));
CREATE TABLE flow_transitions(flow TEXT REFERENCES flows(id), id TEXT, source TEXT, target TEXT, guard TEXT, payload TEXT NOT NULL, PRIMARY KEY(flow,id), FOREIGN KEY(flow,source) REFERENCES flow_steps(flow,id), FOREIGN KEY(flow,target) REFERENCES flow_steps(flow,id), FOREIGN KEY(flow,guard) REFERENCES flow_guards(flow,id));
CREATE TABLE relation_types(id TEXT PRIMARY KEY, from_kind TEXT NOT NULL, to_kind TEXT NOT NULL, classification TEXT NOT NULL);
CREATE TABLE edges(id TEXT PRIMARY KEY, source TEXT NOT NULL REFERENCES registry(id), target TEXT NOT NULL REFERENCES registry(id), type TEXT NOT NULL REFERENCES relation_types(id), payload TEXT NOT NULL);
CREATE TRIGGER edge_type BEFORE INSERT ON edges BEGIN SELECT CASE WHEN NOT EXISTS (SELECT 1 FROM relation_types t JOIN registry s ON s.id=NEW.source JOIN registry d ON d.id=NEW.target WHERE t.id=NEW.type AND t.from_kind=s.kind AND t.to_kind=d.kind) THEN RAISE(ABORT,'wrong endpoint type') END; END;
CREATE TABLE held_anchors(id TEXT PRIMARY KEY, source TEXT NOT NULL, target TEXT NOT NULL, payload TEXT NOT NULL);
CREATE TABLE overlays(id TEXT PRIMARY KEY, payload TEXT NOT NULL);
CREATE INDEX edge_forward ON edges(source,type,target);
CREATE INDEX edge_reverse ON edges(target,type,source);
CREATE INDEX claim_topic ON claims(topic);
"""
def projection(root,m,requested):
    require(m["status"]=="DRAFT_ONLY_NOT_RELEASE_MANIFEST","manifest status")
    require(m["schema_version"]=="draft-d4-projection-1","schema version")
    require(m["base"]==BASE,"base")
    pkgs=m["packages"];loaded=[];visiting=set();data=[]
    def visit(k):
        require(k in pkgs,"missing package "+k)
        if k in loaded:return
        require(k not in visiting,"dependency cycle")
        visiting.add(k);p=pkgs[k];body={a:b for a,b in p.items() if a!="manifest_digest"}
        require(p["package_id"]==k and p["version"]==BASE and p["status"]=="DRAFT_ONLY","package identity")
        require(digest(compact(body).encode())==p["manifest_digest"],"manifest digest")
        for dep in p["dependencies"]:
            v=pkgs.get(dep["package_id"]);require(v is not None,"missing dependency")
            require((dep["version"],dep["manifest_digest"])==(v["version"],v["manifest_digest"]),"dependency version/digest")
            visit(dep["package_id"])
        paths=set()
        for path,kind,blob,sha in p["files"]:
            f=(root/path).resolve();require(f.is_relative_to(root.resolve()) and path.startswith(P) and path not in paths,"invalid path")
            paths.add(path);b=f.read_bytes();require(digest(b)==sha and gitblob(b)==blob,"file digest "+path)
            data.append((k,kind,decode(b),path))
        visiting.remove(k);loaded.append(k)
    visit(requested)
    cx=sqlite3.connect(":memory:");cx.executescript(DDL)
    q=cx.execute; registry={}; pending=[]; expected={}; seq=0
    def reg(id,kind,pkg):
        require(isinstance(id,str) and id and id not in registry,"duplicate/missing id "+str(id))
        registry[id]=(kind,pkg);q("INSERT INTO registry VALUES(?,?,?)",(id,kind,pkg))
    def row(table,id,columns,payload):
        q("INSERT INTO "+table+" VALUES("+",".join("?" for _ in range(len(columns)+2))+")",(id,*columns,compact(payload)))
        expected[(table,id)]=payload
    def edge(a,b,t,payload,id=None):
        nonlocal seq
        seq+=1;pending.append((id or "generated:"+str(seq),a,b,t,compact(payload)))
    types={"HAS_TOPIC":("MODULE","TOPIC","STRUCTURAL_ONLY"),"HAS_CLAIM":("TOPIC","CLAIM","STRUCTURAL_ONLY"),"CITES_RECORDED_SOURCE":("CLAIM","SOURCE_RECORD","RECORDED_NOT_SUPPORT"),"RECORDED_REFINEMENT_CANDIDATE":("CLAIM","CLAIM","RESEARCH_ONLY"),"HAS_CASE":("TOPIC","CASE","STRUCTURAL_ONLY"),"CASE_REFERENCES_CLAIM":("CASE","CLAIM","DESIGN_ONLY"),"CONTRACT_TOPIC":("CONTRACT","TOPIC","RESEARCH_ONLY"),"CONTRACT_CLAIM":("CONTRACT","CLAIM","RESEARCH_ONLY")}
    for pkg,kind,d,path in data:
        if kind=="coverage":
            mod=d["owner"];reg(mod,"MODULE",pkg);q("INSERT INTO modules VALUES(?)",(mod,))
            for x in d["records"]:
                id=x["d3_id"];reg(id,"TOPIC",pkg);row("topics",id,(mod,x["requirement_id"],x["topic"]),x);edge(mod,id,"HAS_TOPIC",{})
        elif kind=="sources":
            for x in d["sources"]:
                id=x["id"];reg(id,"SOURCE_RECORD",pkg);row("sources",id,(x["title"],x["url"],x["locator"],x.get("access"),x.get("rights")),x)
    for pkg,kind,d,path in data:
        if kind=="claims":
            for x in d["records"]:
                id=x["stable_id"];reg(id,"CLAIM",pkg);require(x["qualification"]=="NOT_RUN","unexpected qualification "+id)
                require(registry[x["d3_id"]][1]==pkg,"claim topic package")
                require(q("SELECT requirement,module FROM topics WHERE id=?",(x["d3_id"],)).fetchone()==(x["requirement_id"],x["owner"]),"topic/owner")
                row("claims",id,(x["d3_id"],x["statement"],x["claim_type"],compact(x["conditions"]),x["negative_boundary"],x["evidence_status"],x["qualification"]),x)
                edge(x["d3_id"],id,"HAS_CLAIM",{})
                for s in x["source_refs"]:edge(id,s,"CITES_RECORDED_SOURCE",{"claim_locator":x.get("source_locator"),"qualification":"NOT_RUN"})
                if "base_claim_ref" in x:edge(id,x["base_claim_ref"],"RECORDED_REFINEMENT_CANDIDATE",{"qualification":"NOT_RUN"})
        elif kind=="cases":
            for x in d["records"]:
                id=x["id"];reg(id,"CASE",pkg);row("cases",id,(x["d3_id"],compact(x["fixture"])),x);edge(x["d3_id"],id,"HAS_CASE",{})
                for c in x["claim_refs"]:edge(id,c,"CASE_REFERENCES_CLAIM",{"validation":x.get("validation")})
        elif kind=="contracts":
            for x in d["contracts"]:
                id=x["task_id"];reg(id,"CONTRACT",pkg);row("contracts",id,(x["title"],x["inputs"],x["outputs"],x["selection_and_inference"],x["fail_closed"]),x)
                for a in x["research_topic_anchors"]:edge(id,a,"CONTRACT_TOPIC",{})
        elif kind=="bindings":
            for x in d["contracts"]:
                for a in x["bindings"]:edge(x["task_id"],a["claim_id"],"CONTRACT_CLAIM",a)
        elif kind=="flow":
            id=d["id"];q("INSERT INTO flows VALUES(?,?,?)",(id,d["entry"],compact(d)))
            steps={x["id"] for x in d["steps"]};guards={x["id"] for x in d["guards"]}
            require(d["entry"] in steps and set(d["terminal"])<=steps,"flow entry/terminal")
            require(d["global_control"]["target"] in d["terminal"] and d["global_control"]["priority"]==0,"exit priority")
            for x in d["steps"]:q("INSERT INTO flow_steps VALUES(?,?,?,?)",(id,x["id"],x["contract"],compact(x)))
            for x in d["guards"]:q("INSERT INTO flow_guards VALUES(?,?,?,?)",(id,x["id"],x["contract"],compact(x)))
            for x in d["transitions"]:
                require(x["from"] not in d["terminal"] and x["unknown_branch"] in d["terminal"] and x["failure_branch"] in d["terminal"] and x["budget"]=="REQUIRE_REMAINING_TURN_AND_TIME","flow bounds")
                q("INSERT INTO flow_transitions VALUES(?,?,?,?,?,?)",(id,x["id"],x["from"],x["to"],x["guard"],compact(x)))
            require(decode(q("SELECT payload FROM flows WHERE id=?",(id,)).fetchone()[0].encode())==d,"flow roundtrip")
        elif kind=="relation_types":
            for t,v in d["types"].items():
                if t not in types:types[t]=(v["from"],v["to"],v["class"])
                else:require(types[t][:2]==(v["from"],v["to"]),"type conflict")
        elif kind=="semantic":
            for x in d["records"]:
                require(x["materialize_accepted"] is False and x["transitive"] is False and x["reversible"] is False,"unsafe semantic edge")
                for c in x["claim_refs"]:require(registry.get(c,("",))[0]=="CLAIM","semantic evidence")
                edge(x["from"],x["to"],x["type"],x,x["id"])
        elif kind=="anchors":
            for x in d["records"]:
                # All original research anchors remain unpromoted, including resolvable endpoints.
                q("INSERT INTO held_anchors VALUES(?,?,?,?)",(x["id"],x["from"],x["target"],compact(x)))
        elif kind=="source_recheck":
            for x in d["records"]:q("INSERT INTO overlays VALUES(?,?)",(x["parent"],compact(x)))
    for t,v in types.items():q("INSERT INTO relation_types VALUES(?,?,?,?)",(t,*v))
    for eid,a,b,t,v in pending:
        require(a in registry and b in registry,"orphan "+str((a,b,t)))
        q("INSERT INTO edges VALUES(?,?,?,?,?)",(eid,a,b,t,v))
    require(q("PRAGMA foreign_key_check").fetchall()==[],"foreign keys")
    for (table,id),v in expected.items():require(decode(q("SELECT payload FROM "+table+" WHERE id=?",(id,)).fetchone()[0].encode())==v,"roundtrip")
    return cx,loaded,len(data),len(expected)
def validate(root,m):
    import copy
    checks=[]
    def ck(id,ok):require(ok,id);checks.append(id)
    def reject(id,fn):
        try:fn()
        except (ValueError,sqlite3.IntegrityError,KeyError):checks.append(id);return
        raise ValueError("negative accepted "+id)
    routes={}
    for pkg in m["packages"]:
        c,loaded,files,roundtrip=projection(root,m,pkg);q=c.execute
        counts={k:q("SELECT count(*) FROM "+k).fetchone()[0] for k in ("modules","topics","claims","sources","cases","contracts","edges","held_anchors","overlays","flows","flow_steps","flow_guards","flow_transitions")}
        routes[pkg]={"loaded":loaded,"files":files,"roundtrip":roundtrip,"counts":counts}
        ck("fk:"+pkg,q("PRAGMA foreign_key_check").fetchall()==[])
        if pkg=="learning-core":ck("core_only",loaded==["learning-core"] and q("SELECT count(*) FROM modules WHERE id LIKE 'H%'").fetchone()[0]==0)
        if pkg=="chinese":ck("chinese_only",loaded==["chinese"] and q("SELECT count(*) FROM modules WHERE id LIKE 'K%'").fetchone()[0]==0)
        if pkg=="learning-process":
            ck("process_no_chinese",loaded==["learning-core","learning-process"] and counts["contracts"]==27)
            ck("flow_structure",counts["flows"]==1 and counts["flow_steps"]==10 and counts["flow_guards"]==9 and counts["flow_transitions"]==9)
            ck("flow_guard_query",q("SELECT g.contract FROM flow_transitions t JOIN flow_guards g ON t.flow=g.flow AND t.guard=g.id WHERE t.source='ADAPT' AND t.target='ACTIVITY'").fetchone()==("P08",))
            reject("flow_orphan_guard",lambda:q("INSERT INTO flow_transitions VALUES('D4:LEARNING_CYCLE','BAD','ADAPT','ACTIVITY','BAD','{}')"))
        if pkg=="research-overlay":
            ck("totals",counts["modules"]==26 and counts["topics"]==648 and counts["claims"]==1712 and counts["sources"]==441 and counts["contracts"]==27 and counts["held_anchors"]==189)
            ck("binding_count",q("SELECT count(*) FROM edges WHERE type='CONTRACT_CLAIM'").fetchone()[0]==100)
            ck("depth_count",q("SELECT count(*) FROM edges WHERE type='RECORDED_REFINEMENT_CANDIDATE'").fetchone()[0]==364)
            ck("citation_count",q("SELECT count(*) FROM edges WHERE type='CITES_RECORDED_SOURCE'").fetchone()[0]==974)
            ck("no_qualified",q("SELECT count(*) FROM claims WHERE qualification!='NOT_RUN'").fetchone()[0]==0)
            ck("no_semantic_promotion",q("SELECT count(*) FROM edges WHERE type IN ('PREREQUISITE','CAUSES','MASTERY','EQUIVALENT')").fetchone()[0]==0)
            ck("semantic_count",q("SELECT count(*) FROM edges WHERE id LIKE 'D3G-R%'").fetchone()[0]==20)
            ck("held_anchor_unresolved",q("SELECT count(*) FROM held_anchors WHERE json_extract(payload,'$.resolution')!='IN_INDEX_REFERENCE_ONLY'").fetchone()[0]==15)
            ck("query_p05",q("SELECT c.statement FROM edges e JOIN claims c ON c.id=e.target WHERE e.source='P05' AND e.type='CONTRACT_CLAIM' AND c.id='K05.02.01.D4.01'").fetchone() is not None)
            ck("query_h01",q("SELECT count(*) FROM claims WHERE topic='H01.03.04'").fetchone()[0]>=3)
            plan=q("EXPLAIN QUERY PLAN SELECT target FROM edges WHERE source=? AND type=?",("P05","CONTRACT_CLAIM")).fetchall()
            ck("index_plan",any("edge_forward" in str(x) for x in plan))
            reject("sql_wrong_type",lambda:q("INSERT INTO edges VALUES('bad','P05','K05.02.01.D4.01','HAS_TOPIC','{}')"))
            reject("sql_orphan",lambda:q("INSERT INTO edges VALUES('bad','P05','missing','CONTRACT_CLAIM','{}')"))
            reject("sql_duplicate",lambda:q("INSERT INTO registry VALUES('P05','CONTRACT','learning-process')"))
        c.close()
    def mutate(f):
        x=copy.deepcopy(m);f(x);return projection(root,x,"learning-process")
    def reseal(x,k):
        p=x["packages"][k];p["manifest_digest"]=digest(compact({a:b for a,b in p.items() if a!="manifest_digest"}).encode())
    reject("unknown_package",lambda:projection(root,m,"unknown"))
    reject("missing_dependency",lambda:mutate(lambda x:x["packages"].pop("learning-core")))
    def stale(x):x["packages"]["learning-process"]["dependencies"][0]["version"]="wrong";reseal(x,"learning-process")
    reject("stale_dependency",lambda:mutate(stale))
    def tamper(x):x["packages"]["learning-process"]["files"][0][3]="0"*64;reseal(x,"learning-process")
    reject("wrong_file_digest",lambda:mutate(tamper))
    reject("duplicate_json_key",lambda:decode(b'{"x":1,"x":2}'))
    return {"status":"CANDIDATE_MEMORY_PROJECTION_ONLY","sqlite":sqlite3.sqlite_version,"routes":routes,"checks":checks,"count":len(checks),"query_plan":plan,"persistent_database_files":0,"qualification":"NOT_RUN","oracle":"SAME_AUTHOR_FIXED_ASSERTIONS"}
if __name__=="__main__":
    root=pathlib.Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT
    if len(sys.argv)>2 and sys.argv[2]=="manifest":print(json.dumps(manifest(root),ensure_ascii=False,indent=2))
    else:
        m=decode((root/(HERE+"manifest.json")).read_bytes())
        print(json.dumps(validate(root,m),ensure_ascii=False,indent=2))
