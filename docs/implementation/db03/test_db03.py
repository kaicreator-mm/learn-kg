import json,os,sys,tempfile,unittest,copy
from pathlib import Path
from private_adapter import *
from tools.knowledge_import.importer import Importer,ManifestPin,Reject
class Tests(unittest.TestCase):
 def test_01_private_path_denials(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);os.chmod(p,0o700);f=p/'safe.json';f.write_text('{}');os.chmod(f,0o600)
   self.assertEqual(relative(p,'safe.json'),f)
   for n in ('../safe.json','/tmp/anything','./safe.json','bad//x','bad\\x','absent'):
    with self.assertRaises(Reject):relative(p,n)
   (p/'link').symlink_to(f)
   with self.assertRaises(Reject):relative(p,'link')
   os.chmod(f,0o644)
   with self.assertRaises(Reject):relative(p,'safe.json')
 def test_02_wrong_root_mode(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);os.chmod(p,0o755)
   with self.assertRaisesRegex(Reject,'PRIVATE_DIR_MODE'):checked_root(p)
 def test_03_wrong_descriptor_pin(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);os.chmod(p,0o700);f=p/'adapter-manifest.json';f.write_text('{}');os.chmod(f,0o600)
   with self.assertRaisesRegex(Reject,'PRIVATE_PIN'):import_private(p,'0'*64,p,'x','y')
 def test_04_nonprivate_descriptor_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);os.chmod(p,0o700);f=p/'adapter-manifest.json'
   write(f,dict(status='PUBLIC',rights_scope=RIGHTS_SCOPE,stage_manifest_sha256='x',hsk01_receipt_sha256='y',version=VERSION));os.chmod(f,0o600)
   with self.assertRaisesRegex(Reject,'PRIVATE_DESCRIPTOR_SCOPE'):import_private(p,file_sha(f),p,'x','y')
 def test_05_hs00_rebind_exact(self):
  h,shapes=hs00_shapes();self.assertEqual(len(shapes),109)
  for r in shapes.values():
   x=held_shape(r,r['provenance']);self.assertEqual(x['status'],'HOLD')
   self.assertEqual(x['owner'],'H07' if r['kind']=='Locator' else r['owner'])
   for _,ref in refs(x):
    self.assertEqual(ref['version'],VERSION);self.assertIn(ref['package_id'],('evidence','chinese'))
   schema(x['kind']).validate(x)
 def test_06_wrong_hs00_tuple(self):
  with self.assertRaisesRegex(Reject,'HS00_REF_SCOPE'):
   refs_rebind(dict(package_id='wrong',version='0.1.0-hs00-candidate-1',kind='Source',owner='EVIDENCE',stable_id='X'))
 def test_07_public_importer_denies_private_manifest(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);m=dict(schema_version='learn-kg-canonical-candidate-1',package_id='evidence',version=VERSION,status='CANDIDATE',rights='PRIVATE_ONLY',owners=['EVIDENCE'],dependencies=[],files=[dict(path='x.jsonl',format='JSONL_RECORDS',record_count=1,sha256='0'*64)],qualification_receipt_refs=[])
   p=root/'private.manifest.json';write(p,m)
   im=Importer(root,mode='research',catalog={('evidence',VERSION):ManifestPin(p.name,file_sha(p))})
   try:
    with self.assertRaisesRegex(Reject,'RESEARCH_SCOPE'):im.run(('evidence',VERSION))
   finally:im.close()
 def test_08_schema_denies_forged_membership(self):
  from jsonschema import ValidationError
  with self.assertRaises(ValidationError):
   schema('SourceMembership').validate({'kind':'SourceMembership','stable_id':'S','owner':'H07','status':'HOLD','raw_fields':{'raw':'not-array'}})
if __name__=='__main__':unittest.main(verbosity=2)
