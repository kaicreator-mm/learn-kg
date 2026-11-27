"""DB02 author tests: real R3 and bounded isolated synthetic fixtures."""
import copy
import json
import pathlib
import sqlite3
import tempfile
import unittest
from tools.knowledge_import.importer import (
    ROOT, Importer, ManifestPin, Reject, R3_EXT_SHA, digest, canonical, parse,
)
V = "0.1.0-foundation-candidate-3"
P = "knowledge/v0.1.0/foundation-r3/"
R3_PINS = {
    ("learning-core", V): ManifestPin(P+"learning-core.manifest.json","17f3bf2e25f6d70f53d90beed651d752843541e350824bd3c53f360dc67740d5"),
    ("evidence", V): ManifestPin(P+"evidence.manifest.json","2e35f5431088b47cbd02f43c30e7f3519e777f22b78e33d1e5d27672f3319355"),
}

def ref(pkg, owner, id_, kind, version="v1"):
    return {"package_id":pkg,"version":version,"owner":owner,"stable_id":id_,"kind":kind}

class Fixture:
    def __init__(self, root):
        self.root = pathlib.Path(root)
        self.catalog = {}
        self.source = self.put("source.json", {"text":"原创合成夹具"})
        self.prov = [{"source_path":"source.json","source_sha256":digest(self.source.read_bytes()),"json_pointer":"/text","source_status":"SYNTHETIC"}]

    def put(self, path, x):
        p=self.root/path
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(x if isinstance(x,bytes) else canonical(x).encode("utf-8"))
        return p

    def base(self, owner, kind, id_):
        return {"kind":kind,"owner":owner,"stable_id":id_,"status":"CANDIDATE","conditions":["synthetic"],"negative_boundary":"not professional evidence","provenance":copy.deepcopy(self.prov)}

    def source_record(self):
        return self.base("EVIDENCE","Source","SRC") | {"title":"Synthetic","identifier":"synthetic","access":"SYNTHETIC","rights":"HOLD","qualification":"NOT_RUN","bibliography":"synthetic","recorded_locator":None,"recorded_rights":"HOLD"}

    def locator(self, owner="K01", reference=None):
        return self.base(owner,"Locator","L") | {"source_ref":reference or ref("evidence","EVIDENCE","SRC","Source"),"location":"fixture","attribution":"RECORDED_NOT_REVERIFIED","verification":"NOT_RUN"}

    def topic(self, owner="K01"):
        return self.base(owner,"Topic","T") | {"label":"主题","depth":1,"parent_ref":None}

    def pkg(self, pkg, owner, rows, deps=(), mut=None, raw=None, fmt="JSONL_RECORDS"):
        name=pkg+"/records."+("jsonl" if fmt=="JSONL_RECORDS" else "json")
        data=raw if raw is not None else (b"".join(canonical(r).encode()+b"\n" for r in rows) if fmt=="JSONL_RECORDS" else canonical(rows).encode())
        f=self.put(name,data)
        m={"schema_version":"learn-kg-canonical-candidate-1","package_id":pkg,"version":"v1","status":"CANDIDATE","rights":"HOLD","owners":[owner],"files":[{"path":f.name,"format":fmt,"record_count":len(rows),"sha256":digest(data)}],"dependencies":[{"package_id":k[0],"version":k[1],"manifest_sha256":self.catalog[k].sha256} for k in deps],"qualification_receipt_refs":[]}
        if mut:mut(m)
        p=self.put(pkg+"/manifest.json",m)
        self.catalog[pkg,"v1"]=ManifestPin(pkg+"/manifest.json",digest(p.read_bytes()))
        return pkg,"v1"

    def run(self,k):
        im=Importer(self.root,mode="research",catalog=self.catalog)
        try:return im.run(k)
        finally:im.close()

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.f=Fixture(self.tmp.name)
        self.ev=self.f.pkg("evidence","EVIDENCE",[self.f.source_record()])
    def reject(self, code, key):
        with self.assertRaisesRegex(Reject,code):
            self.f.run(key)
    def core(self,rows=None,**kw):
        return self.f.pkg("learning-core","K01",rows if rows is not None else [self.f.topic(),self.f.locator()],deps=(self.ev,),**kw)

    def test_real_r3_roundtrip_and_route(self):
        cat=R3_PINS|{("chinese","unused"):ManifestPin("does-not-exist.json","0"*64)}
        im=Importer(mode="research",catalog=cat,extension=ManifestPin(P+"relation-types.json",R3_EXT_SHA))
        try:
            r=im.run(("learning-core",V))
            self.assertEqual(sum(x["records"] for x in r["packages"]),1663)
            self.assertEqual(sum(x["typed_refs"] for x in r["packages"]),3899)
            self.assertEqual(set(im.connections),set(R3_PINS))
            self.assertNotIn("does-not-exist.json",im.opened)
            c=im.connections["learning-core",V]
            self.assertTrue(all(name in ("main","temp") and path=="" for _,name,path in c.execute("PRAGMA database_list")))
            self.assertEqual(c.execute("SELECT COUNT(*) FROM record_claim").fetchone(),(288,))
            plans=c.execute("EXPLAIN QUERY PLAN SELECT stable_id FROM record_claim WHERE topic_id=? AND requirement_id=?",("K03.03.03","K03.03.03.RQ01")).fetchall()
            self.assertTrue(any("idx_record_claim" in str(p) for p in plans),plans)
            plans=c.execute("EXPLAIN QUERY PLAN SELECT origin_id FROM typed_refs WHERE target_package=? AND target_version=? AND target_id=?",("evidence",V,"K03-S07")).fetchall()
            self.assertTrue(any("refs_target" in str(p) for p in plans),plans)
            with self.assertRaises(sqlite3.OperationalError):
                c.execute("DELETE FROM local_registry")
            # Deliberate negative write probe, not exposed by importer API.
            c.execute("PRAGMA query_only=OFF")
            with self.assertRaises(sqlite3.IntegrityError):
                c.execute("INSERT INTO typed_refs VALUES(?,?,?,?,?,?,?,?,?)",("learning-core",V,"absent","/bad","evidence",V,"K03-S07","Source","EVIDENCE"))
            c.rollback()
            with self.assertRaises(sqlite3.IntegrityError):
                c.execute("INSERT INTO local_ref_targets SELECT origin_package,origin_version,origin_id,field_pointer,target_package,target_version,'absent',expected_kind,expected_owner FROM typed_refs WHERE target_package='evidence' LIMIT 1")
            c.rollback()
            c.execute("PRAGMA query_only=ON")
            with self.assertRaisesRegex(Reject,"IMPORTER_SINGLE_USE"):
                im.run(("learning-core",V))
        finally:im.close()
    def test_no_extension(self):
        im=Importer(mode="research",catalog=R3_PINS)
        with self.assertRaisesRegex(Reject,"RELATION_ENDPOINT"):
            im.run(("learning-core",V))
        self.assertFalse(im.connections)
    def test_research_mode_required(self):
        with self.assertRaisesRegex(Reject,"APPROVAL_AUTHORITY_UNAVAILABLE"):
            Importer(mode="approved",catalog=self.f.catalog)
    def test_valid_json_records(self):
        self.assertEqual(self.f.run(self.core(fmt="JSON_RECORDS"))["packages"][-1]["records"],2)
    def test_duplicate_key(self):
        self.reject("DUPLICATE_JSON_KEY",self.core(rows=[self.f.topic()],raw=b'{"kind":"Topic","kind":"Topic"}\n'))
    def test_nonfinite(self):
        for v in (b'NaN',b'Infinity',b'1e9999'):
            with self.assertRaises(Reject):
                parse(v)
    def test_bad_utf8(self):
        with self.assertRaises(Reject):parse(b'\xff')
    def test_unknown_field(self):
        self.reject("SCHEMA",self.core([self.f.topic()|{"extra":"x"}]))
    def test_duplicate_record_id(self):
        self.reject("DUPLICATE_ID",self.core([self.f.topic(),self.f.topic()]))
    def test_record_count(self):
        self.reject("COUNT_MISMATCH",self.core(mut=lambda m:m["files"][0].update(record_count=3)))
    def test_bad_file_hash(self):
        self.reject("HASH_MISMATCH",self.core(mut=lambda m:m["files"][0].update(sha256="0"*64)))
    def test_bad_manifest_hash(self):
        k=self.core()
        self.f.catalog[k]=ManifestPin(self.f.catalog[k].path,"0"*64)
        self.reject("HASH_MISMATCH",k)
    def test_path_escape(self):
        self.reject("SCHEMA",self.core(mut=lambda m:m["files"][0].update(path="../source.json")))
    def test_symlink(self):
        k=self.core()
        p=self.f.root/"learning-core/records.jsonl"
        actual=p.with_name("actual.jsonl");p.rename(actual);p.symlink_to(actual)
        self.reject("SYMLINK_REJECTED",k)
    def test_bad_provenance(self):
        r=self.f.topic()
        r["provenance"][0]["json_pointer"]="/absent"
        self.reject("POINTER_MISSING",self.core([r]))
    def test_missing_package(self):
        k=self.core()
        del self.f.catalog[self.ev]
        self.reject("DEPENDENCY_PIN",k)
    def test_bad_dependency_hash(self):
        self.reject("DEPENDENCY_PIN",self.core(mut=lambda m:m["dependencies"][0].update(manifest_sha256="0"*64)))
    def test_wrong_version(self):
        self.reject("UNDECLARED_DIRECT_DEPENDENCY",self.core([self.f.locator(reference=ref("evidence","EVIDENCE","SRC","Source","v2"))]))
    def test_wrong_kind(self):
        self.reject("ENDPOINT_KIND",self.core([self.f.locator(reference=ref("evidence","EVIDENCE","SRC","Claim"))]))
    def test_wrong_owner(self):
        self.reject("REF_IDENTITY",self.core([self.f.locator(reference=ref("evidence","K01","SRC","Source"))]))
    def test_orphan(self):
        self.reject("ORPHAN_REF",self.core([self.f.locator(reference=ref("evidence","EVIDENCE","missing","Source"))]))
    def test_transitive_fallback(self):
        core=self.core()
        chinese=self.f.pkg("chinese","H01",[self.f.locator("H01")],deps=(core,))
        self.reject("UNDECLARED_DIRECT_DEPENDENCY",chinese)
    def test_private_manifest(self):
        self.reject("RESEARCH_SCOPE",self.core(mut=lambda m:m.update(rights="PRIVATE_ONLY")))
    def test_fake_approved(self):
        self.reject("RESEARCH_SCOPE",self.core(mut=lambda m:m.update(status="APPROVED",rights="PUBLIC_AUTHORIZED",qualification_receipt_refs=["forged"])))
    def test_fake_qualified_record(self):
        self.reject("UNVERIFIED_QUALIFIED_RECORD",self.core([self.f.topic()|{"status":"QUALIFIED"}]))
    def test_wrong_domain_owner(self):
        self.reject("PACKAGE_OWNER_SCOPE",self.core(mut=lambda m:m.update(owners=["H01"])))
    def test_foreign_record_owner(self):
        self.reject("RECORD_OWNER",self.core([self.f.topic("H01")]))
    def test_relation_type_and_endpoints(self):
        f=self.f
        topic=f.topic()
        rq=f.base("K01","Requirement","RQ") | {"topic_ref":ref("learning-core","K01","T","Topic"),"facets":["synthetic"],"required_views":["FORWARD"],"acceptance":"synthetic"}
        # Use a real schema-valid shape for Requirement, with no invented semantics.
        schema=Importer(f.root,mode="research",catalog=f.catalog).schema["$defs"]["Requirement"]
        rq={k:v for k,v in rq.items() if k in schema["properties"]}
        for k in schema["required"]:
            if k not in rq:
                prop=schema["properties"][k]
                if "const" in prop:rq[k]=prop["const"]
                elif prop.get("type")=="string":rq[k]="synthetic"
                elif prop.get("type")=="array":rq[k]=["FORWARD"] if "enum" in prop.get("items",{}) else ["synthetic"]
                else:raise AssertionError((k,prop))
        claim=f.base("K01","Claim","C")|{"topic_id":"T","requirement_id":"RQ","claim_type":"ENGINEERING_POLICY","statement":"synthetic","source_status":"NOT_RUN","locator_refs":[],"case_refs":[],"validation_refs":[],"supersedes_refs":[],"refinement_of":None}
        rel=f.base("K01","Relation","R")|{"relation_type":"unsupported","from_ref":ref("learning-core","K01","T","Topic"),"to_ref":ref("learning-core","K01","T","Topic"),"claim_refs":[ref("learning-core","K01","C","Claim")],"condition_refs":[],"direction":"DIRECTED","automatic_inverse":False,"automatic_transitive":False}
        self.reject("RELATION_ENDPOINT",self.core([topic,rq,claim,rel]))
        self.reject("RELATION_ENDPOINT",self.core([topic,rq,claim,rel|{"relation_type":"component_of"}]))
        self.assertEqual(self.f.run(self.core([topic,rq,claim,rel|{"relation_type":"taxonomy_parent"}]))["packages"][-1]["records"],4)
        self.reject("CLAIM_REQUIREMENT",self.core([topic,rq,claim|{"requirement_id":"absent"}]))

if __name__=="__main__":
    unittest.main(verbosity=2)
