"""DB02 repeat import: separate memory snapshots, exact text, no persistent DB."""
import pathlib
import tempfile
import unittest
from tools.knowledge_import.importer import Importer, canonical, digest
from tools.knowledge_import.test_importer import Fixture
from tools.knowledge_import.test_mapping_witness import packages

class RepeatImport(unittest.TestCase):
    def test_repeat_fresh_imports(self):
        with tempfile.TemporaryDirectory() as d:
            f = Fixture(d)
            root, _ = packages(f)
            before = {str(p.relative_to(f.root)): digest(p.read_bytes())
                      for p in f.root.rglob('*') if p.is_file()}
            snapshots = []
            for _ in range(2):
                im = Importer(f.root, mode='research', catalog=f.catalog)
                try:
                    report = im.run(root)
                    sql = {}
                    for k, c in sorted(im.connections.items()):
                        tables = [x[0] for x in c.execute(
                            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
                        sql['/'.join(k)] = {
                            t: sorted([list(row) for row in c.execute('SELECT * FROM "' + t + '"')], key=canonical)
                            for t in tables
                        }
                        self.assertTrue(all(path == '' for _, _, path in c.execute('PRAGMA database_list')))
                    snapshots.append(digest(canonical({'report':report,'sql':sql}).encode()))
                finally:
                    im.close()
            self.assertEqual(snapshots[0], snapshots[1])
            self.assertEqual(before, {str(p.relative_to(f.root)): digest(p.read_bytes())
                                      for p in f.root.rglob('*') if p.is_file()})
if __name__ == '__main__':
    unittest.main()
