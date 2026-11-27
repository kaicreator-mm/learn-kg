# 历史工具：HSK 私有候选 RDF 图导入（D010）

D014之后不作为当前知识建设入口；仅在必要时复现原R2，保留历史代码与依赖。当前要求先生成可读知识源，禁止直接生成SQLite文件。[D014文本合同](../../docs/design/text-knowledge-package.md) / [SRC01保全与可读归档](../../docs/implementation/src01-readable-archive.md)。以下是历史执行方式，不代表当前要重新运行。

# HSK 私有候选图导入
Python 3.12 verified, pyoxigraph 0.5.13. Run from repository root:
```sh
python -m venv .venv
.venv/bin/python -m pip install -r tools/hsk_import/requirements.txt
.venv/bin/python -m py_compile tools/hsk_import/import_hsk.py
.venv/bin/python tools/hsk_import/import_hsk.py /private/source-text.json /private/new-graph-dir --taxonomy docs/product/system/learning-science-taxonomy.md docs/product/system/hsk-taxonomy.md
```
Input JSON maps RHSK01, RHSK02, RHSK03 to the corresponding unmodified connector-extracted text. Parser is intentionally bound to this layout and R1 inventory, not a general PDF reader. No original source/PDF/data fixture is committed. Retain exact source text and report privately; do not publish unless rights confirmed. New target only, use a unique directory, no concurrent writers; results are staging, never accepted. See ../../docs/design/graph-database.md and ../../docs/implementation/hsk-import-r2.md. Use explicit named graph in SPARQL.
