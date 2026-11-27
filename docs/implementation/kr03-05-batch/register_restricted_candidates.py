#!/usr/bin/env python3
"""Register the five independently recommended restricted candidate tuples.

This script is intentionally exact-head/CAS guarded. It does not qualify modules,
promote held claims, or mutate any source/rights/CQ/LC status.
"""
from __future__ import annotations
import argparse, hashlib, json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BRANCH = "version/v0.1.0"
EXPECTED_HEAD = "62760bfd4690279cf2a703be8cc908a92ef1d755"
TREE = "0a2970ec606210ff98eb475906c7ffea168ab22e"
CONTRACT_ID = "D013-R3R-D014"
CONTRACT_HASH = "0bcf76f3374e5ebd169d8177595cb958b16a0c415705a76d7cee4c087f694f6d"
REVIEW_TASK = 7220402787
REVIEW_RESULT = 7221120084
PREVIOUS_REVIEW = 7220019599
REVIEWER = "chatgpt-web:learn-kg-kr03-05-independent-batch-reviewer"
REVIEW_SESSION = "learn-kg-kr03-05-independent-batch-review-20261127"

PKG = {
    "K09": ("measurement-r4", "k09-preparation", 14, 13),
    "K13": ("social-research-r2", "k13-k17-preparation", 3, 19),
    "K14": ("domain-development-r2", "k14-k18-preparation", 3, 18),
    "K17": ("social-research-r2", "k13-k17-preparation", 2, 23),
    "K18": ("domain-development-r2", "k14-k18-preparation", 2, 16),
}
SOURCE_LIMITED = {
    "K09": [
        "K09.01.01.R4.S01","K09.01.02.R4.S01","K09.02.01.R4.S01",
        "K09.02.02.R4.S01","K09.02.03.R4.S01","K09.02.04.R4.S01",
        "K09.02.05.R4.S01","K09.05.01.R4.S01","K09.05.02.R4.S01",
        "K09.05.03.R4.S01",
    ],
    "K13": ["K13.02.01.SR.S01","K13.02.02.SR.S01","K13.02.04.SR.S01"],
    "K14": ["K14.02.02.DD.S01","K14.03.01.DD.S01","K14.03.02.DD.S01"],
    "K17": ["K17.05.02.SR.S01","K17.05.03.SR.S01"],
    "K18": ["K18.03.01.DD.S01","K18.04.03.DD.S01"],
}
MODEL_CLAIMS = {
    "K09": ["K09.03.04.D4.01","K09.04.01.D4.01","K09.04.02.D4.01"],
    "K13": [], "K14": [], "K17": [], "K18": [],
}
PERMITTED = {
    "K09": "Bounded measurement concepts and the ten exact source-limited propositions; three exact model statements only as bounded models; project rules/original derivations only as synthetic or project-defined methods. No individual ability estimate, universal validity claim, fitted model, or full measurement-science coverage.",
    "K13": "Three cited social-cultural propositions and project-defined synthetic reasoning only. No identity-based inference, personal cultural attribution, or causal learner diagnosis. Source propositions remain builder-only candidates, not direct source qualification.",
    "K14": "Three cited proficiency/science-practice propositions and project-defined task models only. No universal curriculum, external standards equivalence, or general transfer claim. K06 consumption remains restricted to its exact upstream qualification allowlist.",
    "K17": "Two cited meta-analysis/statistical propositions and synthetic calculations only. No empirical treatment-effect or causal conclusion without design-specific identification and source qualification.",
    "K18": "Two cited sleep/environment propositions and voluntary reversible support rules only. No diagnosis, clinical prediction, or inference about an individual from learning data.",
}
DEPTH_FILES = {
    "K09": ["K09-depth.md","depth.json","depth.tsv","finite-fixtures.json","finite-results.json","scope-witness.json","run_finite.py"],
    "K13": ["K13-depth.md","K17-depth.md","depth.json","actual-source-observations.json","scope-witness.json"],
    "K14": ["K14-depth.md","K18-depth.md","depth.json","actual-source-observations.json","scope-witness.json"],
    "K17": ["K13-depth.md","K17-depth.md","depth.json","actual-source-observations.json","scope-witness.json"],
    "K18": ["K14-depth.md","K18-depth.md","depth.json","actual-source-observations.json","scope-witness.json"],
}

def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def canonical_digest(value) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()

def add_output(out, path: str, kind: str):
    p = ROOT / path
    if not p.is_file():
        raise SystemExit(f"required output missing: {path}")
    entry = {"path": path, "sha256": sha(p), "type": kind}
    if all(x["path"] != path for x in out):
        out.append(entry)

def build_outputs(module: str, package: str, docdir: str):
    base = Path("knowledge/v0.1.0") / package
    lm_path = base / "learning-core.manifest.json"
    em_path = base / "evidence.manifest.json"
    lm, em = load(ROOT/lm_path), load(ROOT/em_path)
    em_sha = sha(ROOT/em_path)
    if not any(x.get("package_id") == "evidence" and x.get("manifest_sha256") == em_sha for x in lm.get("dependencies", [])):
        raise SystemExit(f"{module}: learning-core does not pin current evidence manifest")
    outputs = []
    add_output(outputs, lm_path.as_posix(), "SHARED_CANDIDATE_INPUT_OR_EVIDENCE")
    add_output(outputs, em_path.as_posix(), "SHARED_CANDIDATE_INPUT_OR_EVIDENCE")
    # Bind every shard in the shared package; mark other owners as context, not as
    # part of this module's own candidate scope.
    for f in lm["files"]:
        path = (base / f["path"])
        if not path.is_file() or sha(ROOT/path) != f["sha256"]:
            raise SystemExit(f"{module}: manifest shard mismatch: {path}")
        owner = path.parts[3] if len(path.parts) > 3 else ""
        typ = "MODULE_CANDIDATE_ARTIFACT" if owner == module else "SHARED_CANDIDATE_INPUT_OR_EVIDENCE"
        add_output(outputs, path.as_posix(), typ)
    for f in em["files"]:
        path = base / f["path"]
        if not path.is_file() or sha(ROOT/path) != f["sha256"]:
            raise SystemExit(f"{module}: evidence shard mismatch: {path}")
        add_output(outputs, path.as_posix(), "SHARED_CANDIDATE_INPUT_OR_EVIDENCE")
    for owner in lm["owners"]:
        cov = base / owner / "coverage.json"
        if cov.exists():
            add_output(outputs, cov.as_posix(), "MODULE_CANDIDATE_ARTIFACT" if owner == module else "SHARED_CANDIDATE_INPUT_OR_EVIDENCE")
    for name in ["current-source-observations.json", "finite-fixtures.json", "finite-results.json", "import-receipt.json", "validation-receipt.json"]:
        p = base / name
        if p.exists():
            add_output(outputs, p.as_posix(), "SHARED_CANDIDATE_INPUT_OR_EVIDENCE")
    # Human-readable module depth, source observations, and the previously reviewed
    # finite package evidence are pinned separately from canonical JSONL.
    for name in DEPTH_FILES[module]:
        path = Path("docs/implementation") / docdir / name
        add_output(outputs, path.as_posix(), "MODULE_CANDIDATE_ARTIFACT" if name == f"{module}-depth.md" else "SHARED_CANDIDATE_INPUT_OR_EVIDENCE")
    for path in [
        "docs/implementation/kr03-05-batch/scope-ledger.json",
        "docs/implementation/task-execution-contract.md",
    ]:
        add_output(outputs, path, "SHARED_CANDIDATE_INPUT_OR_EVIDENCE")
    outputs.sort(key=lambda x: x["path"])
    return outputs, lm, em

def build_input(module: str, tasks: dict):
    entries = []
    for dep_id in tasks[module]["depends_on"]:
        dep = tasks[dep_id]
        rec_path = dep.get("current_receipt")
        if not rec_path:
            raise SystemExit(f"{module}: missing current prerequisite receipt for {dep_id}")
        rec_file = ROOT / rec_path
        rec = load(rec_file)
        if rec.get("task_id") != dep_id or rec.get("receipt_id") is None:
            raise SystemExit(f"{module}: malformed prerequisite receipt {rec_path}")
        refs = [{"path": rec_path, "sha256": sha(rec_file)}]
        entry = {
            "task_id": dep_id,
            "receipt_id": rec["receipt_id"],
            "content_digest": rec["content_digest"],
            "version": rec["version"],
            "specific_refs": refs,
        }
        q_path = dep.get("qualification_receipt")
        if q_path:
            q_file = ROOT / q_path
            q = load(q_file)
            if q.get("reviewed_content_digest") != rec.get("content_digest"):
                raise SystemExit(f"{module}: stale qualification for {dep_id}")
            if q.get("state") != "QUALIFIED_LOCAL":
                raise SystemExit(f"{module}: prerequisite qualification not locally qualified: {dep_id}")
            refs.append({"path": q_path, "sha256": sha(q_file)})
            entry["qualification_receipt_id"] = q["receipt_id"]
            entry["qualification_scope"] = dep.get("qualification_scope", "LOCAL")
        entries.append(entry)
    return entries

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    head = run("git", "rev-parse", "HEAD")
    branch = run("git", "branch", "--show-current")
    tree = run("git", "rev-parse", "HEAD^{tree}")
    status = run("git", "status", "--porcelain")
    allowed_status = "?? docs/implementation/kr03-05-batch/register_restricted_candidates.py"
    remote = run("git", "ls-remote", "origin", f"refs/heads/{BRANCH}").split()[0]
    if branch != BRANCH or head != EXPECTED_HEAD or tree != TREE or (status and status != allowed_status) or remote != EXPECTED_HEAD:
        raise SystemExit(f"CAS failed branch={branch} head={head} tree={tree} status={status!r} remote={remote}")
    contract = ROOT / "docs/implementation/task-execution-contract.md"
    if sha(contract) != CONTRACT_HASH:
        raise SystemExit("D013-R3R-D014 contract hash mismatch")
    dag_path = ROOT / "docs/implementation/task-dag.json"
    dag = load(dag_path)
    tasks = {t["id"]: t for t in dag["tasks"]}
    ledger_path = ROOT / "docs/implementation/kr03-05-batch/scope-ledger.json"
    ledger = load(ledger_path)
    ledger_modules = {m["owner"]: m for m in ledger["modules"]}
    expected_counts = {"K09":(31,75,60),"K13":(21,45,35),"K14":(22,48,40),"K17":(30,67,44),"K18":(19,42,25)}
    candidate_receipts = []
    for module, (package, docdir, checked_topics, no_validation) in PKG.items():
        task = tasks[module]
        if task["status"] != "READY" or task.get("current_receipt") or task.get("qualification_receipt"):
            raise SystemExit(f"{module}: unexpected current task state")
        base = Path("knowledge/v0.1.0") / package
        cov_path = base / module / "coverage.json"
        cov = load(ROOT/cov_path)
        topics = cov["topics"]
        active = sorted({cid for t in topics for cid in t["active_claim_ids"]})
        all_claims = sorted({cid for t in topics for cid in t["claim_ids"]})
        held = sorted(set(all_claims) - set(active))
        topic_count, active_count, held_count = expected_counts[module]
        if (len(topics),len(active),len(held)) != (topic_count,active_count,held_count):
            raise SystemExit(f"{module}: coverage count mismatch {(len(topics),len(active),len(held))}")
        if len(ledger_modules[module]["topic_rows"]) != topic_count:
            raise SystemExit(f"{module}: scope-ledger topic count mismatch")
        manifest_path = base / "learning-core.manifest.json"
        manifest = load(ROOT/manifest_path)
        if manifest["version"] != cov["version"]:
            raise SystemExit(f"{module}: coverage/manifest version mismatch")
        out, lm, em = build_outputs(module, package, docdir)
        out_hash = {x["path"]:x["sha256"] for x in out}
        # Every source/model claim in the independent review's bounded allowlist
        # must be present in the active candidate set.
        if not set(SOURCE_LIMITED[module] + MODEL_CLAIMS[module]).issubset(active):
            raise SystemExit(f"{module}: source/model allowlist is not active")
        scope_row = ledger_modules[module]
        active_views = [v for v in scope_row["view_obligations"] if v["claim_status"] == "CANDIDATE"]
        held_views = [v for v in scope_row["view_obligations"] if v["claim_status"] != "CANDIDATE"]
        input_entries = build_input(module, tasks)
        scope_restriction = {
            "status": "RESTRICTED_CANDIDATE_SCOPE",
            "package_version": manifest["version"],
            "learning_core_manifest_sha256": sha(ROOT/manifest_path),
            "evidence_manifest_sha256": sha(ROOT/(base/"evidence.manifest.json")),
            "coverage_sha256": sha(ROOT/cov_path),
            "candidate_claim_ids": active,
            "excluded_hold_claim_ids": held,
            "candidate_claim_count": len(active),
            "excluded_hold_claim_count": len(held),
            "source_limited_candidate_claim_ids": SOURCE_LIMITED[module],
            "model_claim_ids": MODEL_CLAIMS[module],
            "source_checked_topic_count": checked_topics,
            "topics_with_case_but_no_validation": no_validation,
            "view_binding_policy": "RESEARCH_INPUT_NOT_ENTAILMENT_OR_QUALIFICATION",
            "active_view_bindings": active_views,
            "held_view_bindings": held_views,
            "scope_ledger": ledger_path.as_posix(),
            "scope_ledger_sha256": sha(ROOT/ledger_path),
            "rights": "HOLD",
            "cq": "NOT_RUN",
            "lc": "NOT_RUN",
            "permitted_use": PERMITTED[module],
            "limitations": [
                "Candidate readiness is not independent qualification or unrestricted professional adequacy.",
                "All HOLD claims and held view bindings are excluded from this candidate scope.",
                "No source-rights clearance, publication, empirical learner-effect, or release claim.",
                "CQ/LC remain NOT_RUN; historical semantic anchors and cross-version relation closure remain pending.",
                "The 27 active cross-view bindings are research inputs only, not entailment or qualification."
            ],
        }
        if module == "K14":
            scope_restriction["upstream_restriction"] = "K06 is QUALIFIED_LOCAL_RESTRICTED; consume only its exact qualification allowlist and negative boundaries."
        if module == "K18":
            scope_restriction["upstream_restriction"] = "K02 is QUALIFIED_LOCAL; do not infer qualification of any other module."
        receipt = {
            "operator": "chatgpt-web:learn-kg-controller",
            "session": "learn-kg-kr03-05-candidate-registration-20261127",
            "role": "BUILDER_NON_REVIEWER",
            "reviewer": REVIEWER,
            "review_session": REVIEW_SESSION,
            "branch": BRANCH,
            "base": EXPECTED_HEAD,
            "exact_head": EXPECTED_HEAD,
            "version": EXPECTED_HEAD,
            "contract_id": CONTRACT_ID,
            "contract_hash": CONTRACT_HASH,
            "time": "2026-11-27",
            "task_id": module,
            "attempt_id": f"{module}-FORMAL-01",
            "receipt_id": f"TASK:{module}:{module}-FORMAL-01",
            "input": input_entries,
            "output": out,
            "state": "CANDIDATE_READY",
            "receipt_type": "CANDIDATE_READY",
            "scope": PERMITTED[module],
            "scope_restriction": scope_restriction,
            "validation": {
                "review_task_comment": REVIEW_TASK,
                "review_result_comment": REVIEW_RESULT,
                "previous_review_comment": PREVIOUS_REVIEW,
                "reviewed_exact_head": EXPECTED_HEAD,
                "reviewed_tree": TREE,
                "independent_result": "ACCEPT_SCOPED_WITH_TWO_P2_REMEDIATION_ITEMS",
                "candidate_readiness": "CANDIDATE_READY_RECOMMENDED_RESTRICTED",
                "new_finite_oracle": "ACCEPT_115_OF_115",
                "cross_composition": "ACCEPT_SCOPED_27_OF_28_INPUT_DETERMINED",
                "exact_bindings": "36_OF_36",
                "p0": 0, "p1": 0, "p2": 2, "p3": 1,
                "qualification": "NOT_ISSUED",
                "rights": "HOLD", "cq": "NOT_RUN", "lc": "NOT_RUN",
                "notes": "This registration records a restricted candidate only. The independent review issued no qualification receipts and did not promote any held claim."
            },
            "issues": [
                "P2-01 ModelSpec applicability domains in K10/K12 require explicit structural encoding before generic ModelSpec use.",
                "P2-02 cross adapter X01 input and invalid numeric-domain guards require remediation before generic composition/runtime use.",
                "P3 source-version/authority pinning remains required before broader qualification; unresolved BKT/Pashler and source limitations remain HOLD."
            ],
            "next": "Independent exact-tuple qualification under the owning KR batch; preserve this restricted allowlist and all upstream consumption limits."
        }
        receipt["content_digest"] = canonical_digest({"input": receipt["input"], "output": receipt["output"]})
        candidate_receipts.append((module, receipt, out))
        print(f"{module}: topics={topic_count} candidate={len(active)} HOLD={len(held)} output_files={len(out)} digest={receipt['content_digest']}")
    if not args.apply:
        print("DRY_RUN_ONLY; no files changed")
        return
    for module, receipt, _ in candidate_receipts:
        path = ROOT / f"evidence/tasks/{module}/{module}-FORMAL-01.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tasks[module]["status"] = "CANDIDATE_READY"
        tasks[module]["current_receipt"] = path.relative_to(ROOT).as_posix()
        tasks[module]["qualification_scope"] = "RESTRICTED"
    dag_path.write_text(json.dumps(dag, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("REGISTERED", ",".join(x[0] for x in candidate_receipts), "DAG", dag_path)

if __name__ == "__main__":
    main()
