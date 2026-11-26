# HSK 私有候选图导入
Python 3.12 verified, pyoxigraph 0.5.13. Run from repository root:
```sh
python -m venv .venv
.venv/bin/python -m pip install -r tools/hsk_import/requirements.txt
.venv/bin/python -m py_compile tools/hsk_import/import_hsk.py
.venv/bin/python tools/hsk_import/import_hsk.py /private/source-text.json /private/new-graph-dir --taxonomy docs/product/system/learning-science-taxonomy.md docs/product/system/hsk-taxonomy.md
```
Input JSON maps RHSK01, RHSK02, RHSK03 to the corresponding unmodified connector-extracted text. Parser is intentionally bound to this layout and R1 inventory, not a general PDF reader. No original source/PDF/data fixture is committed. Retain exact source text and report privately; do not publish unless rights confirmed. New target only, use a unique directory, no concurrent writers; results are staging, never accepted. See ../../docs/design/graph-database.md and ../../docs/implementation/hsk-import-r2.md. Use explicit named graph in SPARQL.
