#!/usr/bin/env python3
"""Build the HS00 source/standard interface mapping without copying source text."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
from pathlib import Path
from typing import Any

PARSER_NAME = "hs00-level-label-parser"
PARSER_VERSION = "0.1.0"
STANDARD_ID = "urn:learn-kg:standard:hsk:2025-11"
RIGHTS_SCOPE = {
    "historical_pdf_byte_identity": "HOLD_NO_HISTORICAL_RAW_DIGEST",
    "rights": "HOLD_NO_PUBLICATION_OR_REDISTRIBUTION",
    "visual_layout": "HOLD_LAYOUT_REVIEW_PENDING",
    "publication": "NOT_AUTHORIZED",
    "visibility": "PRIVATE_ONLY",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def term_digest(term: dict[str, Any]) -> str:
    return sha256(canonical_json(term))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def jsonl_with_bytes(path: Path) -> list[tuple[dict[str, Any], bytes]]:
    raw = path.read_bytes()
    out = []
    for line in raw.splitlines(keepends=True):
        if not line.strip():
            continue
        out.append((json.loads(line.decode("utf-8")), line))
    return out


def short_name(iri: str) -> str:
    return iri.rsplit(":", 1)[-1]


def property_terms(record: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    return {short_name(key): value for key, value in record.get("properties", {}).items()}


def one_term(record: dict[str, Any], name: str) -> dict[str, Any]:
    values = property_terms(record).get(name, [])
    if len(values) != 1:
        raise ValueError(f"{record.get('stable_id')} property {name} expected exactly one term, got {len(values)}")
    return values[0]


def literal_value(record: dict[str, Any], name: str) -> Any:
    term = one_term(record, name)
    if term.get("kind") != "literal":
        raise ValueError(f"{record.get('stable_id')} property {name} is not a literal")
    return term["value"]


def iri_value(record: dict[str, Any], name: str) -> str:
    term = one_term(record, name)
    if term.get("kind") != "iri":
        raise ValueError(f"{record.get('stable_id')} property {name} is not an IRI")
    return term["value"]


def parse_level_label(raw: str) -> tuple[str, list[int] | None]:
    """Parse only the observed exact grammar; never trim or rewrite source punctuation."""
    if not isinstance(raw, str) or not raw:
        return "HOLD_UNPARSED", None
    tokens = re.findall(r"[1-9](?:-[1-9])?", raw)
    if not tokens:
        return "HOLD_UNPARSED", None
    rebuilt = tokens[0] + "".join("（" + token + "）" for token in tokens[1:])
    if rebuilt != raw:
        return "HOLD_UNPARSED", None
    members: list[int] = []
    for token in tokens:
        if "-" in token:
            start, end = (int(part) for part in token.split("-", 1))
            if start >= end:
                return "HOLD_UNPARSED", None
            members.extend(range(start, end + 1))
        else:
            members.append(int(token))
    if any(level < 1 or level > 9 for level in members) or len(members) != len(set(members)):
        return "HOLD_UNPARSED", None
    return "PARSED_CANDIDATE", sorted(members)


def merged_identity(raw: str, standard_id: str = STANDARD_ID) -> str:
    digest = sha256((standard_id + "\0" + raw).encode("utf-8"))
    return "HS00.LEVELSET." + digest[:24]


def validate_source_archive(archive_root: Path, restore_root: Path) -> dict[str, Any]:
    export_root = archive_root.parent
    preservation_path = export_root / "PRESERVATION-MANIFEST.json"
    preservation = read_json(preservation_path)
    files = preservation["files"]
    if preservation.get("file_count") != len(files):
        raise ValueError("PRESERVATION-MANIFEST file_count mismatch")
    checked = []
    for entry in files:
        rel = entry["path"]
        primary = export_root / rel
        restored = restore_root / rel
        if not primary.is_file() or not restored.is_file():
            raise ValueError(f"missing cross-fault archive file: {rel}")
        primary_bytes = primary.read_bytes()
        restored_bytes = restored.read_bytes()
        expected = entry["sha256"]
        if sha256(primary_bytes) != expected or sha256(restored_bytes) != expected:
            raise ValueError(f"cross-fault archive SHA256 mismatch: {rel}")
        if primary_bytes != restored_bytes:
            raise ValueError(f"cross-fault archive byte mismatch: {rel}")
        checked.append({"path": rel, "bytes": len(primary_bytes), "sha256": expected})
    return {
        "preservation_manifest_sha256": sha256(preservation_path.read_bytes()),
        "portable_file_count": len(checked),
        "portable_total_bytes": sum(x["bytes"] for x in checked),
        "cross_fault_portable_archive": "ALL_LISTED_FILES_BYTE_IDENTICAL",
        "cross_fault_files": checked,
    }


def build(args: argparse.Namespace) -> dict[str, Any]:
    archive_root = args.archive_root.resolve()
    export_root = archive_root.parent
    restore_root = args.restore_root.resolve()
    private_manifest_path = args.private_backup_manifest.resolve()
    pdf_root = args.pdf_root.resolve()
    repo_root = Path(__file__).resolve().parents[3]

    archive_manifest_path = archive_root / "manifest.json"
    archive_manifest = read_json(archive_manifest_path)
    source_manifest = read_json(export_root / "manifest.json")
    import_report = read_json(export_root / "import-report-r2.json")
    private_manifest = read_json(private_manifest_path)
    cross_fault = read_json(repo_root / "docs/drafts/stage-handoff/src01-cross-fault-backup-evidence-20261128.json")
    reconciliation = read_json(repo_root / "docs/drafts/stage-handoff/src01-reconciliation-delta-20261128.json")
    receipt = read_json(repo_root / "evidence/tasks/SRC01/SRC01-FORMAL-02.json")

    archive_restore = validate_source_archive(archive_root, restore_root)
    if archive_manifest.get("scope") != "SRC01_PRIVATE_RDF_ARCHIVAL_TEXT_ONLY":
        raise ValueError("unexpected readable archive scope")
    if archive_manifest.get("exact_quad_set_equal") is not True:
        raise ValueError("RDF exact quad-set restoration is not verified")
    if archive_manifest.get("original_pdf_identity") != "HOLD" or archive_manifest.get("publication_rights") != "HOLD":
        raise ValueError("SRC01 preservation holds changed")
    if private_manifest.get("classification") is None:
        raise ValueError("private backup manifest classification missing")

    # Verify the private backup manifest is exactly the evidence referenced by SRC01.
    private_manifest_sha = sha256(private_manifest_path.read_bytes())
    if private_manifest_sha != receipt["validation"]["private_backup_manifest_sha256"]:
        raise ValueError("private backup manifest SHA256 differs from SRC01 receipt")
    if private_manifest_sha != cross_fault["private_backup_manifest_sha256"]:
        raise ValueError("private backup manifest SHA256 differs from cross-fault evidence")

    # Verify source archive files against their own manifest.
    for filename, metadata in archive_manifest["files"].items():
        p = archive_root / filename
        if not p.is_file() or p.stat().st_size != metadata["bytes"] or sha256(p.read_bytes()) != metadata["sha256"]:
            raise ValueError(f"readable archive file mismatch: {filename}")

    source_rows = jsonl_with_bytes(archive_root / "SourceRecord.jsonl")
    block_rows = jsonl_with_bytes(archive_root / "SourceBlock.jsonl")
    band_rows = jsonl_with_bytes(archive_root / "LevelBand.jsonl")
    lexical_rows = jsonl_with_bytes(archive_root / "LexicalRecord.jsonl")
    version_rows = jsonl_with_bytes(archive_root / "SyllabusVersion.jsonl")
    character_rows = jsonl_with_bytes(archive_root / "CharacterMembership.jsonl")
    han_rows = jsonl_with_bytes(archive_root / "HanCharacter.jsonl")
    ability_rows = jsonl_with_bytes(archive_root / "AbilityRecord.jsonl")
    taxonomy_rows = jsonl_with_bytes(archive_root / "TaxonomyTopic.jsonl")

    source_text = read_json(export_root / "source-text.json")
    source_text_file_sha = sha256((export_root / "source-text.json").read_bytes())
    if source_text_file_sha != source_manifest["files"]["source-text.json"]["sha256"]:
        raise ValueError("source-text.json does not match source manifest")

    private_files = {x["source_id"]: x for x in private_manifest["sources"]["files"]}
    pdf_identity_files = {x["source_id"]: x for x in reconciliation["raw_pdf_identity"]["files"]}
    cross_fault_files = {x["source_id"]: x for x in cross_fault["raw_pdf_copies"]["files"]}

    source_records = []
    source_record_ids: set[str] = set()
    source_record_raw_by_id: dict[str, dict[str, Any]] = {}
    for record, line in source_rows:
        source_id = short_name(record["stable_id"])
        source_record_id = record["stable_id"]
        if source_record_id in source_record_ids:
            raise ValueError(f"duplicate source record id: {source_record_id}")
        source_record_ids.add(source_record_id)
        source_record_raw_by_id[source_record_id] = record
        status = literal_value(record, "status")
        connector_sha = literal_value(record, "textSha256")
        if source_id not in source_text or sha256(source_text[source_id].encode("utf-8")) != connector_sha:
            raise ValueError(f"canonical connector text digest mismatch: {source_id}")
        if source_id not in private_files or source_id not in pdf_identity_files or source_id not in cross_fault_files:
            raise ValueError(f"missing private/current PDF identity evidence: {source_id}")
        private = private_files[source_id]
        current = pdf_identity_files[source_id]
        fault = cross_fault_files[source_id]
        if private["historical_pdf_sha256"] != "UNKNOWN":
            raise ValueError(f"historical PDF digest must remain explicitly unknown: {source_id}")
        if private["sha256"] != current["sha256"] or private["sha256"] != fault["sha256"]:
            raise ValueError(f"current raw PDF SHA256 cross-fault mismatch: {source_id}")
        pdf_path = pdf_root / private["filename"]
        if not pdf_path.is_file() or sha256(pdf_path.read_bytes()) != private["sha256"] or pdf_path.stat().st_size != private["bytes"]:
            raise ValueError(f"private current PDF byte mismatch: {source_id}")
        if private["drive_revision_count"] != 1 or private["previous_revision_available"] is not False:
            raise ValueError(f"revision history evidence changed: {source_id}")
        subset = [line for block, line in block_rows if iri_value(block, "source") == source_record_id]
        source_blocks_sha = sha256(b"".join(subset)) if subset else None
        source_records.append({
            "kind": "HSKSourceRecord",
            "stable_id": "HS00.SOURCE." + source_id,
            "source_record_id": source_record_id,
            "source_id": source_id,
            "source_status": status,
            "provider_identity": {
                "provider": "GOOGLE_DRIVE",
                "provider_file_id": None,
                "provider_file_id_status": "NOT_STORED_IN_PUBLIC_REPOSITORY",
                "original_name": private["filename"],
                "original_name_status": "VERIFIED_IN_PRIVATE_BACKUP_MANIFEST",
                "original_path": None,
                "original_path_status": "NOT_STORED_IN_PUBLIC_REPOSITORY",
                "current_revision_id": None,
                "current_revision_id_status": "NOT_CAPTURED_IN_SAFE_EVIDENCE",
                "current_revision_count": private["drive_revision_count"],
                "previous_revision_available": private["previous_revision_available"],
                "revision_identity_status": "ONE_CURRENT_REVISION_ONLY_ID_NOT_CAPTURED"
            },
            "current_raw_pdf": {
                "sha256": private["sha256"],
                "bytes": private["bytes"],
                "pdf_pages": private["pdf_pages"],
                "verification": "CURRENT_DRIVE_TO_ALIYUN_TO_V100_SHA256_MATCH"
            },
            "historical_raw_pdf_sha256": None,
            "historical_raw_pdf_status": "HOLD_NO_HISTORICAL_DIGEST_OR_PRIOR_REVISION",
            "canonical_connector_text_sha256": connector_sha,
            "source_block_count": len(subset),
            "source_block_jsonl_subset_sha256": source_blocks_sha,
            "source_record_jsonl_line_sha256": sha256(line),
            "raw_field_digests": {
                "status": term_digest(one_term(record, "status")),
                "textSha256": term_digest(one_term(record, "textSha256"))
            },
            "rights_scope": RIGHTS_SCOPE.copy()
        })

    if len(source_records) != 3 or {x["source_id"] for x in source_records} != {"RHSK01", "RHSK02", "RHSK03"}:
        raise ValueError("expected exactly RHSK01/RHSK02/RHSK03 source records")

    if len(version_rows) != 1:
        raise ValueError("expected exactly one source syllabus version record")
    version_record = version_rows[0][0]
    release_label = literal_value(version_record, "releaseLabel")
    if release_label != "2025-11" or literal_value(version_record, "status") != "STAGING":
        raise ValueError("source-declared release label/status changed")

    standard_identity = {
        "kind": "HSKStandardIdentity",
        "stable_id": "HS00.STANDARD.HSK.2025-11",
        "source_standard_id": version_record["stable_id"],
        "source_family_hint": "HSK",
        "source_declared_version_label_raw": release_label,
        "normalized_internal_version_candidate": "hsk-2025-11",
        "normalization_status": "CANDIDATE_UNVERIFIED",
        "identity_status": "UNKNOWN_HOLD",
        "source_record_status": "STAGING",
        "source_version_record_sha256": sha256(version_rows[0][1]),
        "raw_field_sha256": term_digest(one_term(version_record, "releaseLabel")),
        "authority_verification": "NOT_RUN",
        "negative_boundary": "No official standard identity, edition authority, effective date, equivalence or H07 final mapping is asserted.",
        "rights_scope": RIGHTS_SCOPE.copy()
    }

    level_bands = []
    for record, line in band_rows:
        raw_label = literal_value(record, "label")
        parse_status, members = parse_level_label(raw_label)
        level_bands.append({
            "kind": "HSKLevelBand",
            "evidence_origin": "PINNED_ARCHIVE",
            "stable_id": "HS00.BAND." + sha256(raw_label.encode("utf-8"))[:20],
            "source_band_id": record["stable_id"],
            "source_standard_id": iri_value(record, "version"),
            "raw_level_label": raw_label,
            "raw_field_sha256": term_digest(one_term(record, "label")),
            "raw_label_term": one_term(record, "label"),
            "normalized_member_levels": members,
            "merged_level_identity": merged_identity(raw_label, iri_value(record, "version")) if members is not None else None,
            "parser_name": PARSER_NAME,
            "parser_version": PARSER_VERSION,
            "parse_status": parse_status,
            "semantics_status": "UNKNOWN_HOLD",
            "source_record_line_sha256": sha256(line),
            "rights_scope": RIGHTS_SCOPE.copy()
        })

    level_counts: collections.Counter[str] = collections.Counter()
    level_sources: dict[str, set[str]] = collections.defaultdict(set)
    level_raw_digests: dict[str, str] = {}
    for record, _line in lexical_rows:
        raw_label = literal_value(record, "levelRaw")
        level_counts[raw_label] += 1
        level_sources[raw_label].add(iri_value(record, "source"))
        level_raw_digests[raw_label] = sha256(raw_label.encode("utf-8"))
    level_label_observations = []
    for raw_label, count in sorted(level_counts.items()):
        parse_status, members = parse_level_label(raw_label)
        level_label_observations.append({
            "kind": "HSKLevelLabelObservation",
            "evidence_origin": "PINNED_ARCHIVE",
            "raw_level_label": raw_label,
            "occurrence_count": count,
            "source_record_refs": sorted(level_sources[raw_label]),
            "raw_field_sha256": level_raw_digests[raw_label],
            "parser_name": PARSER_NAME,
            "parser_version": PARSER_VERSION,
            "parse_status": parse_status,
            "normalized_member_levels": members,
            "merged_level_identity": merged_identity(raw_label) if members is not None else None,
            "semantics_status": "UNKNOWN_HOLD",
            "rights_scope": RIGHTS_SCOPE.copy()
        })

    source_blocks = []
    for record, line in block_rows:
        props = property_terms(record)
        source_ref = iri_value(record, "source")
        raw_text = literal_value(record, "rawText")
        page_term = one_term(record, "printedPage")
        if page_term.get("datatype") != "http://www.w3.org/2001/XMLSchema#integer":
            raise ValueError(f"unexpected printedPage datatype: {record['stable_id']}")
        raw_page = str(page_term["value"])
        raw_field_digests = {
            name: term_digest(one_term(record, name))
            for name in ("source", "blockKind", "levelBand", "printedPage", "scopeTopic", "status")
        }
        raw_field_digests["rawText"] = sha256(raw_text.encode("utf-8"))
        source_blocks.append({
            "kind": "HSKSourceBlockMapping",
            "source_record_id": source_ref,
            "source_block_id": record["stable_id"],
            "block_kind_raw": literal_value(record, "blockKind"),
            "level_band_ref": iri_value(record, "levelBand"),
            "printed_page_label_recorded_raw": raw_page,
            "printed_page_source_datatype": page_term["datatype"],
            "printed_page_original_visual_verification": "HOLD_LAYOUT_REVIEW_PENDING",
            "pdf_page_index_zero_based": None,
            "pdf_page_number_one_based": None,
            "pdf_page_locator_status": "UNKNOWN_NOT_DERIVED_FROM_PRINTED_LABEL",
            "section_locator_raw": None,
            "scope_topic_ref": iri_value(record, "scopeTopic"),
            "source_block_status": literal_value(record, "status"),
            "raw_text_sha256": sha256(raw_text.encode("utf-8")),
            "raw_text_utf8_bytes": len(raw_text.encode("utf-8")),
            "source_block_jsonl_line_sha256": sha256(line),
            "raw_field_digests": raw_field_digests,
            "raw_text_storage": "PRIVATE_ARCHIVE_ONLY_NOT_COPIED",
            "rights_scope": RIGHTS_SCOPE.copy()
        })

    if len(source_blocks) != 94:
        raise ValueError(f"expected 94 source blocks, got {len(source_blocks)}")
    block_kind_counts = collections.Counter(x["block_kind_raw"] for x in source_blocks)
    topic_counts = collections.Counter(x["scope_topic_ref"] for x in source_blocks)
    band_counts = collections.Counter(x["level_band_ref"] for x in source_blocks)
    page_values = sorted(int(x["printed_page_label_recorded_raw"]) for x in source_blocks)
    page_ranges = []
    for value in page_values:
        if not page_ranges or value > page_ranges[-1][1] + 1:
            page_ranges.append([value, value])
        else:
            page_ranges[-1][1] = value
    source_block_summary = {
        "count": len(source_blocks),
        "source_record_counts": dict(sorted(collections.Counter(x["source_record_id"] for x in source_blocks).items())),
        "block_kind_counts": dict(sorted(block_kind_counts.items())),
        "scope_topic_counts": dict(sorted(topic_counts.items())),
        "level_band_counts": dict(sorted(band_counts.items())),
        "recorded_printed_page_values": {
            "count": len(page_values),
            "unique_count": len(set(page_values)),
            "minimum": min(page_values),
            "maximum": max(page_values),
            "contiguous_ranges": page_ranges,
            "visual_verification": "HOLD_LAYOUT_REVIEW_PENDING",
            "pdf_page_index_and_number_bound": False
        }
    }
    level_label_summary = {
        "lexical_record_count": len(lexical_rows),
        "unique_raw_label_count": len(level_label_observations),
        "parenthetical_raw_label_record_count": sum(x["occurrence_count"] for x in level_label_observations if "（" in x["raw_level_label"]),
        "range_raw_label_record_count": sum(x["occurrence_count"] for x in level_label_observations if "-" in x["raw_level_label"]),
        "parser_name": PARSER_NAME,
        "parser_version": PARSER_VERSION,
        "semantics_status": "UNKNOWN_HOLD"
    }
    if any(x["source_record_id"] != "urn:learn-kg:source:RHSK01" for x in source_blocks):
        raise ValueError("SourceBlock source identity mismatch")
    if any(x["source_block_status"] != "LAYOUT_REVIEW_PENDING" for x in source_blocks):
        raise ValueError("SourceBlock layout hold changed")
    if any(x["pdf_page_index_zero_based"] is not None or x["pdf_page_number_one_based"] is not None for x in source_blocks):
        raise ValueError("PDF page indices must remain unknown absent exact block mapping")

    def first_id(rows: list[tuple[dict[str, Any], bytes]]) -> str:
        return rows[0][0]["stable_id"]

    record_kind_examples = [
        {"record_kind": "VOCABULARY_ITEM", "source_rdf_kind": "LexicalRecord", "source_record_id": iri_value(lexical_rows[0][0], "source"), "normalized_knowledge_id": first_id(lexical_rows)},
        {"record_kind": "CHARACTER_ITEM", "source_rdf_kind": "HanCharacter", "source_record_id": None, "normalized_knowledge_id": first_id(han_rows), "membership_record_id": first_id(character_rows)},
        {"record_kind": "SOURCE_BLOCK", "source_rdf_kind": "SourceBlock", "source_record_id": iri_value(block_rows[0][0], "source"), "normalized_knowledge_id": first_id(block_rows)},
        {"record_kind": "CAPABILITY", "source_rdf_kind": "AbilityRecord", "source_record_id": iri_value(ability_rows[0][0], "source"), "normalized_knowledge_id": first_id(ability_rows)},
        {"record_kind": "CATEGORY", "source_rdf_kind": "TaxonomyTopic", "source_record_id": None, "normalized_knowledge_id": first_id(taxonomy_rows)},
        {"record_kind": "CHARACTER_MEMBERSHIP", "source_rdf_kind": "CharacterMembership", "source_record_id": iri_value(character_rows[0][0], "source"), "normalized_knowledge_id": first_id(character_rows)}
    ]

    for example in record_kind_examples:
        example["rights_scope"] = RIGHTS_SCOPE.copy()

    archive_evidence = {
        "source_manifest_sha256": sha256((export_root / "manifest.json").read_bytes()),
        "preservation_manifest_sha256": archive_restore["preservation_manifest_sha256"],
        "private_backup_manifest_sha256": private_manifest_sha,
        "readable_archive_manifest_sha256": sha256(archive_manifest_path.read_bytes()),
        "source_text_json_sha256": source_text_file_sha,
        "source_record_jsonl_sha256": sha256((archive_root / "SourceRecord.jsonl").read_bytes()),
        "source_block_jsonl_sha256": sha256((archive_root / "SourceBlock.jsonl").read_bytes()),
        "level_band_jsonl_sha256": sha256((archive_root / "LevelBand.jsonl").read_bytes()),
        "syllabus_version_jsonl_sha256": sha256((archive_root / "SyllabusVersion.jsonl").read_bytes()),
        "lexical_record_jsonl_sha256": sha256((archive_root / "LexicalRecord.jsonl").read_bytes()),
        "source_text_record_hashes": {k: sha256(v.encode("utf-8")) for k, v in sorted(source_text.items())},
        "cross_fault_archive": archive_restore,
        "current_pdf_cross_fault_sha256_matches": cross_fault["raw_pdf_copies"]["all_three_sha256_match"],
        "current_pdf_isolated_v100_restore": cross_fault["restore_tests"]["raw_pdf_backup_to_isolated_v100_restore"],
        "rdf_readable_export_isolated_v100_restore": cross_fault["restore_tests"]["rdf_readable_export_to_isolated_v100_restore"],
        "sourceblock_replay": reconciliation["canonical_extraction"]["sourceblock_replay"],
        "canonical_connector_text_current_historical_match": reconciliation["canonical_extraction"]["current_text_exact_match"],
        "src01_receipt_id": receipt["receipt_id"],
        "src01_receipt_sha256": sha256((repo_root / "evidence/tasks/SRC01/SRC01-FORMAL-02.json").read_bytes()),
        "src01_scope": receipt["scope_restriction"]
    }

    return {
        "schema_version": "learn-kg-hs00-source-mapping-1",
        "kind": "HSKSourceMapping",
        "status": "CANDIDATE_PREPARATION_ONLY",
        "standard_identity": standard_identity,
        "source_records": source_records,
        "level_bands": level_bands,
        "level_label_observations": level_label_observations,
        "source_blocks": source_blocks,
        "source_block_summary": source_block_summary,
        "level_label_summary": level_label_summary,
        "record_kind_examples": record_kind_examples,
        "archive_evidence": archive_evidence,
        "preservation_scope": RIGHTS_SCOPE.copy(),
        "limits": [
            "No source PDF bytes, full extracted source text, Drive file IDs, private paths, download URLs or learner data are copied into the repository.",
            "Original filename is preserved from the private backup manifest; original path and provider file ID remain private-only and are not embedded.",
            "A single current Drive revision exists for each PDF; its exact Drive revision ID was not captured in safe evidence. No prior revision is available.",
            "Current raw-PDF SHA256 is distinct from canonical connector-text SHA256 and SourceBlock JSONL SHA256. Historical raw-PDF SHA256 remains unknown/HOLD.",
            "Printed page values are recorded RDF integer literals, not visually reverified original glyphs. PDF page index and one-based PDF page number are not inferred from printed page labels.",
            "The source standard release label is preserved exactly as 2025-11, but authoritative standard identity and H07 final mapping remain UNKNOWN/HOLD.",
            "Parenthetical/range level parsing is syntactic candidate normalization only; semantics and official standard membership remain UNKNOWN/HOLD.",
            "HSK01 bulk conversion, source-level professional reconciliation, H07 qualification, CQ/LC and publication are outside HS00."
        ]
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-root", type=Path, required=True, help="Private readable archive directory")
    parser.add_argument("--restore-root", type=Path, required=True, help="Independent restored export root")
    parser.add_argument("--private-backup-manifest", type=Path, required=True, help="Private raw-PDF backup manifest")
    parser.add_argument("--pdf-root", type=Path, required=True, help="Private raw-PDF copy directory")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("source-mapping.json"))
    args = parser.parse_args()
    result = build(args)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "HS00_SOURCE_MAPPING_BUILT",
        "output": str(args.output),
        "sha256": sha256(args.output.read_bytes()),
        "source_records": len(result["source_records"]),
        "source_blocks": len(result["source_blocks"]),
        "level_bands": len(result["level_bands"]),
        "observed_level_labels": len(result["level_label_observations"]),
        "parenthetical_level_records": sum(x["occurrence_count"] for x in result["level_label_observations"] if "（" in x["raw_level_label"]),
        "private_source_text_copied": False,
        "private_file_ids_copied": False,
        "rights": RIGHTS_SCOPE["rights"],
        "qualification": "NOT_GRANTED"
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
