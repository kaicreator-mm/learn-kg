# DB02 — candidate text validation and in-memory import (first functional slice)

Status: IMPLEMENTATION_CANDIDATE_PARTIAL, not G04 freeze, release, or DB02 complete receipt. DB01 and IF01 remain immutable. Implementation: tools/knowledge_import/importer.py and candidate_pointer.py.

- Explicit manifest pins with SHA-256, strict UTF-8 JSON/JSONL, duplicate-key and duplicate-ID rejection, normalized paths/no symlink, file hash/count, schema, provenance byte and JSON-pointer checks.
- Each selected package uses its own SQLite :memory: connection, temp_store MEMORY, foreign_keys ON, typed origin and local-target foreign keys. Direct dependency, package/version, kind and owner resolved explicitly across databases. The selected R3 manifest and its local relation extension are exact-hash pinned; no globally introduced vocabulary. All 38 actual record kind tables are generated from DB01; the embedded ref schema is not treated as a free-standing record.
- Mapped field roundtrip and per-kind count checks; JSON scalar boolean and nested/null preserved, full record rebuilt from SQL values. Read-only query mode after import; actual indexed query-plan probes. Unselected manifest pins are not opened.
- Candidate-only research mode explicitly denies private-only, self-claimed APPROVED/QUALIFIED and unknown package roles. It is not a sandbox for malicious file trees: selected manifests and repository root must be trusted, stable read-only research inputs; no learner/private data. Approved/public runtime remains fail-closed pending actual authority and G04 binding. No source rights qualification.
- Candidate text pointer witness validates selected pinned text, serializes writers with Linux flock, checks expected pointer, fsyncs new pointer, atomically replaces same-directory path, fsyncs directory. Reader snapshots pin inputs. Process death before/after replace tested in temporary fixture; not filesystem power-loss or physical cross-database guarantees. No publication pointer or REL01 invocation.

## Reproduction
From repo root:
```sh
python3 -m py_compile tools/knowledge_import/*.py
python3 -m unittest -v tools.knowledge_import.test_importer tools.knowledge_import.test_pointer
python3 -m tools.knowledge_import.importer --research \
 --select learning-core 0.1.0-foundation-candidate-3 \
 --pin learning-core 0.1.0-foundation-candidate-3 knowledge/v0.1.0/foundation-r3/learning-core.manifest.json 17f3bf2e25f6d70f53d90beed651d752843541e350824bd3c53f360dc67740d5 \
 --pin evidence 0.1.0-foundation-candidate-3 knowledge/v0.1.0/foundation-r3/evidence.manifest.json 2e35f5431088b47cbd02f43c30e7f3519e777f22b78e33d1e5d27672f3319355 \
 --extension knowledge/v0.1.0/foundation-r3/relation-types.json 967a0154abf902678dd789f12fd03a40daf0fbe3fe3deb9b444459b8730b8029
```
Dependencies Python 3.12.3, jsonschema 4.10.3, SQLite 3.45.1 tested on Linux. Python stdlib SQLite; no persistent SQLite output.

## Actual limited evidence
R3 1663 records (78 Source, 1585 learning-core), 3899 typed refs, 10 nonempty record kinds, actual schema/provenance/roundtrip/FK/indexed lookup and package routing. 29 unittest methods passed, including adversarial subprobes and actual interrupted child processes. Initial test assumed SQLite would not show in-memory temp schema; corrected assertion to check no on-disk filenames; actual final test includes temp_store MEMORY. No false PASS of first test attempt.

Remaining before DB02 completion: positive/negative mapping witnesses for the other record kinds and semantic field contracts as their modules become concrete; actual approved qualification/rights/receipt resolver and trusted activation contract, future subject package policy, full conditional flow/policy semantics, malicious mutable root hardening. DB03/V00/G04 and all professional/CQ/LC gates not implied. This slice intentionally does not introduce a production platform or persistent DB.

## R2 structural mapping extension
All 38 actual DB01 record kinds now have nonempty synthetic mapping witnesses across four separately materialized package roles: evidence, learning-core, chinese and learning-process. Every kind is tested for a missing required domain field; three additional probes reject wrong cross-domain version/owner and forbidden evaluation approval bypass. Full regression 32 methods PASS. Both actual foundation R3 and practice-teaching R6 packages imported from a combined pin catalog using separate explicit root selection; no unselected snapshot was opened. See validation-r2.json. This closes the structural mapping witness gap, not domain semantics or approval authority. Other-subject remains explicitly unsupported; no persistent database.

## R3 — candidate delivery scope
DB02 candidate acceptance is the D014 text-first research importer and temporary text-manifest switching witness. The R2 extension covers all 38 record kinds; R3 additionally tests repeat imports from unchanged input into fresh in-memory connections and compares every table plus routing report. No persistent SQLite, learner/private input, approval authority, production release pointer or full domain-policy evaluator is authorized or claimed. Approved/public access remains fail-closed; physical multi-file SQLite crash and power-loss tests are HOLD. The earlier partial-slice limitations are preserved; the structural witness gap is resolved, while approval authority, broader subject support and complete integrated semantics remain downstream. This is not G04/G05 acceptance.
