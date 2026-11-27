#!/usr/bin/env python3
"""D014 candidate text importer. No persistent SQLite, no release authority."""
import argparse
import hashlib
import json
import pathlib
import re
import sqlite3
from collections import Counter
from dataclasses import dataclass
import jsonschema

ROOT = pathlib.Path(__file__).resolve().parents[2]
DB01 = ROOT / "docs/implementation/db01"
IF01 = ROOT / "docs/implementation/if01/interface-contract.json"
REF_FIELDS = {"package_id", "version", "stable_id", "kind", "owner"}
# Explicitly pinned candidate-local extension, not accepted global vocabulary.
R3_EXT_SHA = "967a0154abf902678dd789f12fd03a40daf0fbe3fe3deb9b444459b8730b8029"
R3_CORE_SHA = "17f3bf2e25f6d70f53d90beed651d752843541e350824bd3c53f360dc67740d5"
R3_EXT_TYPES = {"contrasted_with", "joint_evidence_with", "limits_inference_to"}
class Reject(ValueError):
    pass

def need(ok, code, detail=""):
    if not ok:
        raise Reject(f"{code}: {detail}")

def digest(b):
    return hashlib.sha256(b).hexdigest()

def canonical(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)

def pairs(seq):
    r = {}
    for k, v in seq:
        need(k not in r, "DUPLICATE_JSON_KEY", k)
        r[k] = v
    return r

def invalid_constant(v):
    raise Reject("INVALID_JSON_CONSTANT: " + v)

def parse(b):
    try:
        x = json.loads(b.decode("utf-8", errors="strict"), object_pairs_hook=pairs, parse_constant=invalid_constant)
        canonical(x)  # also reject overflow-to-inf and lone surrogates below
        canonical(x).encode("utf-8", errors="strict")
        return x
    except (UnicodeError, ValueError, OverflowError) as e:
        if isinstance(e, Reject):
            raise
        raise Reject("INVALID_JSON: " + str(e)) from e

def within(root, relative):
    need(isinstance(relative, str) and relative and "\\" not in relative, "PATH_INVALID", str(relative))
    p = pathlib.PurePosixPath(relative)
    need(not p.is_absolute() and all(v not in ("", ".", "..") for v in relative.split("/")), "PATH_ESCAPE", relative)
    f = root
    for part in p.parts:
        f = f / part
        need(not f.is_symlink(), "SYMLINK_REJECTED", relative)
    need(f.is_file() and f.resolve().is_relative_to(root.resolve()), "PATH_NOT_FILE", relative)
    return f

def verified(root, rel, sha):
    p = within(root, rel)
    b = p.read_bytes()
    need(digest(b) == sha, "HASH_MISMATCH", rel)
    return b

def schema_validator(schema, name):
    return jsonschema.Draft202012Validator({"$defs": schema["$defs"], "$ref": "#/$defs/" + name})

def validate(v, x, label):
    try:
        v.validate(x)
    except jsonschema.ValidationError as e:
        raise Reject("SCHEMA: " + label + ": " + "/".join(map(str, e.absolute_path)) + ": " + e.message[:240]) from e

def ptr_escape(v):
    return str(v).replace("~", "~0").replace("/", "~1")

def pointer(x, ptr):
    need(ptr.startswith("/"), "POINTER_INVALID", ptr)
    for part in ptr[1:].split("/"):
        need(not re.search(r"~(?![01])", part), "POINTER_INVALID", ptr)
        part = part.replace("~1", "/").replace("~0", "~")
        try:
            if isinstance(x, list):
                need(re.fullmatch(r"0|[1-9][0-9]*", part) is not None, "POINTER_INVALID", ptr)
                x = x[int(part)]
            else:
                x = x[part]
        except (IndexError, KeyError, TypeError) as e:
            raise Reject("POINTER_MISSING: " + ptr) from e
    return x

def refs(x, path=()):
    if isinstance(x, dict):
        if set(x) == REF_FIELDS:
            yield path, x
        else:
            for k, v in x.items():
                yield from refs(v, path + (k,))
    elif isinstance(x, list):
        for k, v in enumerate(x):
            yield from refs(v, path + (k,))

def q(name):
    need(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) is not None, "SQL_IDENTIFIER", name)
    return '"' + name + '"'

@dataclass(frozen=True)
class ManifestPin:
    path: str
    sha256: str

class Importer:
    def __init__(self, root=ROOT, *, mode, catalog, extension=None):
        need(mode == "research", "APPROVAL_AUTHORITY_UNAVAILABLE", "Only explicit candidate research is implemented; no released/public/learner mode")
        self.root = pathlib.Path(root).resolve()
        self.schema = parse((DB01 / "canonical.schema.json").read_bytes())
        self.mapping = parse((DB01 / "mapping-contract.json").read_bytes())
        self.interface = parse(IF01.read_bytes())
        need(digest((DB01 / "canonical.schema.json").read_bytes()) == self.interface["schema_sha256"], "CONTRACT_HASH")
        need(digest((DB01 / "mapping-contract.json").read_bytes()) == self.interface["mapping_sha256"], "CONTRACT_HASH")
        self.catalog = dict(catalog)
        self.extensions = {}
        if extension is not None:
            b = verified(self.root, extension.path, extension.sha256)
            need(extension.sha256 == R3_EXT_SHA, "EXTENSION_NOT_PINNED")
            e = parse(b)
            need(e["base_if01_sha256"] == digest(IF01.read_bytes()) and e["status"] == "CANDIDATE_NOT_QUALIFIED" and set(e["types"]) == R3_EXT_TYPES and e["automatic_inverse"] is False and e["automatic_transitive"] is False, "EXTENSION_CONTRACT")
            self.extensions = {k: [v["endpoints"]] for k, v in e["types"].items()}
        self.packages = {}
        self.connections = {}
        self.opened = []
        self.source_cache = {}
        self.mv = schema_validator(self.schema, "manifest")
        self.rv = {k: schema_validator(self.schema, k) for k in self.mapping["record_tables"] if k != "ref"}

    def close(self):
        for c in self.connections.values():
            c.close()
        self.connections.clear()

    def _load(self, key, visiting):
        need(key not in visiting, "DEPENDENCY_CYCLE", str(key))
        if key in self.packages:
            return
        need(key in self.catalog, "MISSING_PACKAGE", str(key))
        pin = self.catalog[key]
        b = verified(self.root, pin.path, pin.sha256)
        self.opened.append(pin.path)
        m = parse(b)
        validate(self.mv, m, pin.path)
        need(key == (m["package_id"], m["version"]), "MANIFEST_IDENTITY", str(key))
        need(m["status"] == "CANDIDATE" and m["rights"] != "PRIVATE_ONLY", "RESEARCH_SCOPE", pin.path)
        need(m["package_id"] in self.mapping["package_roles"], "UNKNOWN_PACKAGE_ROLE", str(key))
        role = self.mapping["package_roles"][m["package_id"]]
        need(m["package_id"] in ("evidence", "learning-core", "chinese", "learning-process"), "PACKAGE_ROLE_NOT_IMPLEMENTED", str(key))
        allowed_owner = {
            "evidence": {"EVIDENCE"},
            "learning-core": {f"K{i:02}" for i in range(1,20)},
            "chinese": {f"H{i:02}" for i in range(1,8)},
            "learning-process": set(self.interface["owner_policy"]["view_owners"]),
        }[m["package_id"]]
        need(set(m["owners"]) <= allowed_owner, "PACKAGE_OWNER_SCOPE", str(key))
        deps = {}
        for d in m["dependencies"]:
            dk = d["package_id"], d["version"]
            need(dk not in deps and dk != key and dk[0] in role["depends_on"], "DEPENDENCY_POLICY", str(dk))
            need(dk in self.catalog and self.catalog[dk].sha256 == d["manifest_sha256"], "DEPENDENCY_PIN", str(dk))
            deps[dk] = d["manifest_sha256"]
            self._load(dk, visiting | {key})
        folder = pathlib.PurePosixPath(pin.path).parent
        data = {}
        paths = set()
        for f in m["files"]:
            rel = str(folder / f["path"])
            need(rel not in paths, "DUPLICATE_FILE", rel)
            paths.add(rel)
            raw = verified(self.root, rel, f["sha256"])
            self.opened.append(rel)
            if f["format"] == "MARKDOWN":
                raw.decode("utf-8", errors="strict")
                need(f["record_count"] == 0 and rel.endswith(".md"), "MARKDOWN_COUNT", rel)
                continue
            if f["format"] == "JSONL_RECORDS":
                need(rel.endswith(".jsonl"), "FORMAT_SUFFIX", rel)
                rows = [parse(line) for line in raw.splitlines()]
            else:
                need(rel.endswith(".json"), "FORMAT_SUFFIX", rel)
                rows = parse(raw)
                need(isinstance(rows, list), "JSON_RECORDS_ARRAY", rel)
            need(len(rows) == f["record_count"], "COUNT_MISMATCH", rel)
            for r in rows:
                need(isinstance(r, dict) and r.get("kind") in self.rv, "RECORD_KIND", rel)
                validate(self.rv[r["kind"]], r, rel)
                need(r["status"] in ("CANDIDATE", "HOLD", "HISTORICAL"), "UNVERIFIED_QUALIFIED_RECORD", r["stable_id"])
                need(r["owner"] in m["owners"], "RECORD_OWNER", r["stable_id"])
                need((r["kind"] == "Source") == (key[0] == "evidence"), "SOURCE_PACKAGE", r["stable_id"])
                need(r.get("rights") != "PRIVATE_ONLY", "PRIVATE_RECORD", r["stable_id"])
                need(r["stable_id"] not in data, "DUPLICATE_ID", r["stable_id"])
                for p in r["provenance"]:
                    relp = p["source_path"]
                    need(not any(part.lower() in {"private", ".git", "learner", "personal"} for part in pathlib.PurePosixPath(relp).parts), "PROVENANCE_PRIVATE_PATH", relp)
                    cachekey = (relp, p["source_sha256"])
                    if cachekey not in self.source_cache:
                        # Only source paths explicitly referenced by this package.
                        self.source_cache[cachekey] = parse(verified(self.root, relp, p["source_sha256"]))
                    pointer(self.source_cache[cachekey], p["json_pointer"])
                data[r["stable_id"]] = r
        self.packages[key] = (m, pin.sha256, deps, data)

    def _validate_refs(self, key):
        m, manifest_sha, deps, data = self.packages[key]
        links = []
        for id_, r in data.items():
            rules = self.interface["endpoint_rules"].get(r["kind"], {})
            for path, ref in refs(r):
                rule = "/".join("*" if type(k) is int else k for k in path)
                need(rule in rules and ref["kind"] in rules[rule], "ENDPOINT_KIND", f"{id_}:{rule}")
                target = ref["package_id"], ref["version"]
                need(target == key or target in deps, "UNDECLARED_DIRECT_DEPENDENCY", str(target))
                need(target in self.packages and ref["stable_id"] in self.packages[target][3], "ORPHAN_REF", ref["stable_id"])
                t = self.packages[target][3][ref["stable_id"]]
                need(t["kind"] == ref["kind"] and t["owner"] == ref["owner"], "REF_IDENTITY", ref["stable_id"])
                links.append((id_, "/" + "/".join(ptr_escape(k) for k in path), *target, t["stable_id"], t["kind"], t["owner"]))
            if r["kind"] == "Claim":
                topic, requirement = data.get(r["topic_id"]), data.get(r["requirement_id"])
                need(topic is not None and topic["kind"]=="Topic" and topic["owner"]==r["owner"], "CLAIM_TOPIC", id_)
                need(requirement is not None and requirement["kind"]=="Requirement" and requirement["owner"]==r["owner"] and requirement["topic_ref"]["stable_id"]==topic["stable_id"], "CLAIM_REQUIREMENT", id_)
            if r["kind"] == "Relation":
                typ = r["relation_type"]
                allowed = self.interface["relation_endpoints"].get(typ)
                if allowed is None and key == ("learning-core","0.1.0-foundation-candidate-3") and manifest_sha == R3_CORE_SHA:
                    allowed = self.extensions.get(typ)
                need(allowed is not None and [r["from_ref"]["kind"],r["to_ref"]["kind"]] in allowed, "RELATION_ENDPOINT", typ)
        return links

    def _materialize(self, key, links):
        m, sha, deps, data = self.packages[key]
        c = sqlite3.connect(":memory:")
        try:
            c.execute("PRAGMA temp_store=MEMORY")
            c.execute("PRAGMA foreign_keys=ON")
            need(c.execute("PRAGMA foreign_keys").fetchone()[0] == 1, "FK_DISABLED")
            c.executescript("""
            CREATE TABLE package_meta(package_id TEXT NOT NULL, version TEXT NOT NULL, manifest_sha256 TEXT NOT NULL,status TEXT NOT NULL, rights TEXT NOT NULL,PRIMARY KEY(package_id,version));
            CREATE TABLE local_registry(package_id TEXT NOT NULL,version TEXT NOT NULL,stable_id TEXT NOT NULL,kind TEXT NOT NULL,owner TEXT NOT NULL,status TEXT NOT NULL,PRIMARY KEY(package_id,version,stable_id),UNIQUE(package_id,version,stable_id,kind,owner),FOREIGN KEY(package_id,version) REFERENCES package_meta);
            CREATE TABLE dependency_manifest(target_package TEXT NOT NULL,target_version TEXT NOT NULL,manifest_sha256 TEXT NOT NULL,PRIMARY KEY(target_package,target_version));
            CREATE TABLE typed_refs(origin_package TEXT NOT NULL,origin_version TEXT NOT NULL,origin_id TEXT NOT NULL,field_pointer TEXT NOT NULL,target_package TEXT NOT NULL,target_version TEXT NOT NULL,target_id TEXT NOT NULL,expected_kind TEXT NOT NULL,expected_owner TEXT NOT NULL,PRIMARY KEY(origin_package,origin_version,origin_id,field_pointer),FOREIGN KEY(origin_package,origin_version,origin_id) REFERENCES local_registry(package_id,version,stable_id));
            CREATE TABLE local_ref_targets(origin_package TEXT NOT NULL,origin_version TEXT NOT NULL,origin_id TEXT NOT NULL,field_pointer TEXT NOT NULL,target_package TEXT NOT NULL,target_version TEXT NOT NULL,target_id TEXT NOT NULL,expected_kind TEXT NOT NULL,expected_owner TEXT NOT NULL,PRIMARY KEY(origin_package,origin_version,origin_id,field_pointer),FOREIGN KEY(origin_package,origin_version,origin_id,field_pointer) REFERENCES typed_refs,FOREIGN KEY(target_package,target_version,target_id,expected_kind,expected_owner) REFERENCES local_registry(package_id,version,stable_id,kind,owner));
            CREATE INDEX registry_kind_owner ON local_registry(kind,owner,stable_id);
            CREATE INDEX refs_target ON typed_refs(target_package,target_version,target_id);
            """)
            with c:
                c.execute("INSERT INTO package_meta VALUES(?,?,?,?,?)", (*key, sha,m["status"],m["rights"]))
                c.executemany("INSERT INTO dependency_manifest VALUES(?,?,?)", [(*k,v) for k,v in deps.items()])
                c.executemany("INSERT INTO local_registry VALUES(?,?,?,?,?,?)",[(*key,r["stable_id"],r["kind"],r["owner"],r["status"]) for r in data.values()])
                for kind, spec in self.mapping["record_tables"].items():
                    if kind == "ref":
                        continue  # schema ref is an embedded reference, not a record kind
                    fields = spec["fields"]
                    columns = ",".join(q(f)+" "+v["sqlite_type"]+" NOT NULL" for f,v in fields.items())
                    table=q(spec["table"])
                    c.execute(f"CREATE TABLE {table}(package_id TEXT NOT NULL,version TEXT NOT NULL,stable_id TEXT NOT NULL,kind TEXT NOT NULL CHECK(kind='{kind}'),owner TEXT NOT NULL,{columns},PRIMARY KEY(package_id,version,stable_id),FOREIGN KEY(package_id,version,stable_id,kind,owner) REFERENCES local_registry(package_id,version,stable_id,kind,owner))")
                    rr=[r for r in data.values() if r["kind"]==kind]
                    names=["package_id","version","stable_id","kind","owner",*fields]
                    def enc(f,r):
                        v=r[f]
                        if fields[f]["encoding"]=="CANONICAL_JSON" or type(v) is bool:
                            return canonical(v)
                        return v
                    c.executemany(f"INSERT INTO {table}({','.join(map(q,names))}) VALUES({','.join('?' for _ in names)})",[(*key,r["stable_id"],kind,r["owner"],*(enc(f,r) for f in fields)) for r in rr])
                    need(c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]==len(rr),"SQL_COUNT",kind)
                    for row in c.execute(f"SELECT {','.join(map(q,names))} FROM {table}"):
                        orig=data[row[2]]
                        out=dict(zip(names,row))
                        out.pop("package_id");out.pop("version")
                        out["status"]=c.execute("SELECT status FROM local_registry WHERE package_id=? AND version=? AND stable_id=?",(*key,row[2])).fetchone()[0]
                        for f in fields:
                            if fields[f]["encoding"]=="CANONICAL_JSON" or type(orig[f]) is bool:
                                out[f]=parse(out[f].encode())
                        need(canonical(out)==canonical(orig),"ROUNDTRIP",row[2])
                for table,cols in [("record_claim","topic_id,requirement_id"),("record_hancharacter","character"),("record_lexeme","lemma"),("record_sourcemembership","section,ordinal")]:
                    c.execute(f"CREATE INDEX idx_{table} ON {table}({cols})")
                c.executemany("INSERT INTO typed_refs VALUES(?,?,?,?,?,?,?,?,?)",[(*key,*r) for r in links])
                c.executemany("INSERT INTO local_ref_targets VALUES(?,?,?,?,?,?,?,?,?)",[(*key,*r) for r in links if tuple(r[2:4])==key])
                need(not c.execute("PRAGMA foreign_key_check").fetchall(),"FK_CHECK")
                need(c.execute("PRAGMA integrity_check").fetchone()==("ok",),"INTEGRITY_CHECK")
            c.execute("PRAGMA query_only=ON")
            self.connections[key]=c
        except BaseException:
            c.close()
            raise

    def run(self, root_key):
        need(not self.packages and not self.connections,"IMPORTER_SINGLE_USE")
        try:
            self._load(root_key,set())
            all_links={key:self._validate_refs(key) for key in self.packages}
            for key,links in all_links.items():
                self._materialize(key,links)
            return {"status":"CANDIDATE_RESEARCH_ONLY","packages":[{"package":list(k),"records":len(self.packages[k][3]),"counts":dict(Counter(r["kind"] for r in self.packages[k][3].values())),"typed_refs":len(v)} for k,v in all_links.items()],"opened_manifest_and_records":self.opened,"persistent_sqlite":False,"release_authority":"NOT_IMPLEMENTED_FAIL_CLOSED"}
        except BaseException:
            self.close()
            raise

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",default=str(ROOT))
    ap.add_argument("--research",action="store_true",required=True)
    ap.add_argument("--select",nargs=2,required=True,metavar=("PACKAGE","VERSION"))
    ap.add_argument("--pin",nargs=4,action="append",required=True,metavar=("PACKAGE","VERSION","PATH","SHA256"))
    ap.add_argument("--extension",nargs=2,metavar=("PATH","SHA256"))
    a=ap.parse_args()
    catalog={}
    for pkg,ver,p,h in a.pin:
        need((pkg,ver) not in catalog,"DUPLICATE_CATALOG")
        catalog[pkg,ver]=ManifestPin(p,h)
    im=Importer(a.root,mode="research",catalog=catalog,extension=ManifestPin(*a.extension) if a.extension else None)
    try:
        print(json.dumps(im.run(tuple(a.select)),ensure_ascii=False,indent=2))
    finally:
        im.close()

if __name__=="__main__":
    main()
