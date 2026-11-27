# P01 candidate package

Human-readable contract: catalog.md.
Machine-authored design input: mode-design.json.
Canonical structured records: knowledge/v0.1.0/learning-process-p01/records-00.jsonl.
D3/D4 coverage and exact upstream scope: coverage.json and input-ledger.json.
Mode-to-flow links: mode-flow-bindings.json.
Lifecycle and pause/resume semantics: recovery-contract.json.

All records remain CANDIDATE. The package is designed for UTF-8 text review and later SQLite import; no persistent database is created. Run build_p01.py to regenerate the package, then check_p01.py to validate canonical schema, exact upstream scopes, typed references, bounded flow contracts and finite authored cases.

The 36 finite cases are builder-only contract checks (six common guard patterns across six mode identities; not 36 distinct mechanisms or actual flow runs). The 121 rows are upstream applicability routes, 29 direct and 92 indirect, not independent depth or coverage acceptance. No numeric model is used. Independent qualification is pending; source rights remain HOLD; CQ/LC are NOT_RUN; this is not a product-effect or release claim.
