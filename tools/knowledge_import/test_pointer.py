"""Actual process interruption and reader snapshot checks in temp text dir."""
import multiprocessing
import pathlib
import tempfile
import unittest
from tools.knowledge_import.candidate_pointer import read_pointer,resolve,switch
from tools.knowledge_import.importer import Reject
from tools.knowledge_import.test_importer import Fixture

class PointerTests(unittest.TestCase):
    def test_interrupt_and_restore(self):
        with tempfile.TemporaryDirectory() as td:
            root=pathlib.Path(td)
            (root/"ptr").mkdir();f=Fixture(root)
            ev=f.pkg("evidence","EVIDENCE",[f.source_record()])
            def snap(k):return {"mode":"CANDIDATE_RESEARCH_ONLY","select":list(k),"catalog":[[*key,p.path,p.sha256] for key,p in f.catalog.items()]}
            old=snap(ev)
            core=f.pkg("learning-core","K01",[f.topic(),f.locator()],deps=(ev,))
            new=snap(core)
            d=root/"ptr"
            switch(d,root,old,None)
            reader_old=read_pointer(d)
            self.assertEqual(len(resolve(reader_old,root)["packages"]),1)
            for phase,code,expected in (("before_replace",71,old),("after_replace",72,new)):
                child=multiprocessing.get_context("fork").Process(target=switch,args=(d,root,new,old),kwargs={"_crash":phase})
                child.start();child.join(10)
                self.assertFalse(child.is_alive())
                self.assertEqual(child.exitcode,code)
                self.assertEqual(read_pointer(d),expected)
                self.assertEqual(len(resolve(read_pointer(d),root)["packages"]),1 if expected==old else 2)
            self.assertEqual(len(resolve(reader_old,root)["packages"]),1)
            with self.assertRaisesRegex(Reject,"POINTER_CAS"):
                switch(d,root,old,old)
            bad={**old,"catalog":[["evidence","v1",f.catalog[ev].path,"0"*64]]}
            with self.assertRaisesRegex(Reject,"HASH_MISMATCH"):
                switch(d,root,bad,new)
            self.assertEqual(read_pointer(d),new)
            switch(d,root,old,new)
            self.assertEqual(read_pointer(d),old)
            self.assertFalse(list(root.rglob("*.sqlite*")))
if __name__=="__main__":unittest.main(verbosity=2)
