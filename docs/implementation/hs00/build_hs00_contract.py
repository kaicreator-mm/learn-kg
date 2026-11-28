#!/usr/bin/env python3
"""Generate HS00 JSON Schema, DB01 projections, fixtures and interface contract."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RIGHTS_SCOPE = {
    "historical_pdf_byte_identity": "HOLD_NO_HISTORICAL_RAW_DIGEST",
    "rights": "HOLD_NO_PUBLICATION_OR_REDISTRIBUTION",
    "visual_layout": "HOLD_LAYOUT_REVIEW_PENDING",
    "publication": "NOT_AUTHORIZED",
    "visibility": "PRIVATE_ONLY"
}
PACKAGE_ID = "hsk-source-interface"
PACKAGE_VERSION = "0.1.0-hs00-candidate-1"
STANDARD_ID = "HS00.STANDARD.HSK.2025-11"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dump(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ref(kind: str, stable_id: str, owner: str) -> dict[str, str]:
    return {
        "package_id": PACKAGE_ID,
        "version": PACKAGE_VERSION,
        "kind": kind,
        "stable_id": stable_id,
        "owner": owner
    }


def digest_schema() -> dict[str, Any]:
    return {"type": "string", "pattern": "^[a-f0-9]{64}$"}


def nonempty() -> dict[str, Any]:
    return {"type": "string", "minLength": 1, "pattern": "\\S"}


def nullable_string() -> dict[str, Any]:
    return {"type": ["string", "null"]}


def rights_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(RIGHTS_SCOPE),
        "properties": {
            "historical_pdf_byte_identity": {"const": RIGHTS_SCOPE["historical_pdf_byte_identity"]},
            "rights": {"const": RIGHTS_SCOPE["rights"]},
            "visual_layout": {"const": RIGHTS_SCOPE["visual_layout"]},
            "publication": {"const": RIGHTS_SCOPE["publication"]},
            "visibility": {"const": RIGHTS_SCOPE["visibility"]}
        }
    }


def make_schema() -> dict[str, Any]:
    digest = digest_schema()
    parser = {
        "type": "object",
        "additionalProperties": False,
        "required": ["name", "version"],
        "properties": {"name": nonempty(), "version": nonempty()}
    }
    provider_identity = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "provider", "provider_file_id", "provider_file_id_status",
            "original_name", "original_name_status", "original_path",
            "original_path_status", "current_revision_id",
            "current_revision_id_status", "current_revision_count",
            "previous_revision_available", "revision_identity_status"
        ],
        "properties": {
            "provider": {"const": "GOOGLE_DRIVE"},
            "provider_file_id": nullable_string(),
            "provider_file_id_status": {"enum": ["NOT_STORED_IN_PUBLIC_REPOSITORY", "AVAILABLE_PRIVATE_ONLY", "UNKNOWN_HOLD"]},
            "original_name": nonempty(),
            "original_name_status": {"const": "VERIFIED_IN_PRIVATE_BACKUP_MANIFEST"},
            "original_path": {"type": "null"},
            "original_path_status": {"const": "NOT_STORED_IN_PUBLIC_REPOSITORY"},
            "current_revision_id": {"type": "null"},
            "current_revision_id_status": {"const": "NOT_CAPTURED_IN_SAFE_EVIDENCE"},
            "current_revision_count": {"type": "integer", "minimum": 1},
            "previous_revision_available": {"const": False},
            "revision_identity_status": {"const": "ONE_CURRENT_REVISION_ONLY_ID_NOT_CAPTURED"}
        }
    }
    defs: dict[str, Any] = {
        "sha256": digest,
        "rightsScope": rights_schema(),
        "parser": parser,
        "providerIdentity": provider_identity,
        "HSKStandardIdentity": {
            "type": "object", "additionalProperties": False,
            "required": [
                "kind", "stable_id", "source_standard_id", "source_family_hint",
                "source_declared_version_label_raw", "normalized_internal_version_candidate",
                "normalization_status", "identity_status", "source_record_status",
                "source_version_record_sha256", "raw_field_sha256",
                "authority_verification", "negative_boundary", "rights_scope"
            ],
            "properties": {
                "kind": {"const": "HSKStandardIdentity"},
                "stable_id": nonempty(),
                "source_standard_id": nonempty(),
                "source_family_hint": {"const": "HSK"},
                "source_declared_version_label_raw": nonempty(),
                "normalized_internal_version_candidate": nonempty(),
                "normalization_status": {"const": "CANDIDATE_UNVERIFIED"},
                "identity_status": {"const": "UNKNOWN_HOLD"},
                "source_record_status": {"const": "STAGING"},
                "source_version_record_sha256": digest,
                "raw_field_sha256": digest,
                "authority_verification": {"const": "NOT_RUN"},
                "negative_boundary": nonempty(),
                "rights_scope": {"$ref": "#/$defs/rightsScope"}
            }
        },
        "HSKSourceRecord": {
            "type": "object", "additionalProperties": False,
            "required": [
                "kind", "stable_id", "source_record_id", "source_id", "source_status",
                "provider_identity", "current_raw_pdf", "historical_raw_pdf_sha256",
                "historical_raw_pdf_status", "canonical_connector_text_sha256",
                "source_block_count", "source_block_jsonl_subset_sha256",
                "source_record_jsonl_line_sha256", "raw_field_digests", "rights_scope"
            ],
            "properties": {
                "kind": {"const": "HSKSourceRecord"},
                "stable_id": nonempty(),
                "source_record_id": {"type": "string", "pattern": "^urn:learn-kg:source:[A-Za-z0-9._:-]+$"},
                "source_id": {"type": "string", "pattern": "^RHSK[0-9]{2}$"},
                "source_status": {"const": "EXTRACTED_TEXT_ONLY"},
                "provider_identity": {"$ref": "#/$defs/providerIdentity"},
                "current_raw_pdf": {
                    "type": "object", "additionalProperties": False,
                    "required": ["sha256", "bytes", "pdf_pages", "verification"],
                    "properties": {
                        "sha256": digest, "bytes": {"type": "integer", "minimum": 1},
                        "pdf_pages": {"type": "integer", "minimum": 1},
                        "verification": {"const": "CURRENT_DRIVE_TO_ALIYUN_TO_V100_SHA256_MATCH"}
                    }
                },
                "historical_raw_pdf_sha256": {"type": "null"},
                "historical_raw_pdf_status": {"const": "HOLD_NO_HISTORICAL_DIGEST_OR_PRIOR_REVISION"},
                "canonical_connector_text_sha256": digest,
                "source_block_count": {"type": "integer", "minimum": 0},
                "source_block_jsonl_subset_sha256": {"oneOf": [digest, {"type": "null"}]},
                "source_record_jsonl_line_sha256": digest,
                "raw_field_digests": {
                    "type": "object", "additionalProperties": False,
                    "required": ["status", "textSha256"],
                    "properties": {"status": digest, "textSha256": digest}
                },
                "rights_scope": {"$ref": "#/$defs/rightsScope"}
            }
        },
        "HSKLevelBand": {
            "type": "object", "additionalProperties": False,
            "required": [
                "kind", "stable_id", "source_band_id", "source_standard_id",
                "raw_level_label", "raw_field_sha256", "raw_label_term", "normalized_member_levels",
                "merged_level_identity", "parser_name", "parser_version",
                "parse_status", "semantics_status", "source_record_line_sha256",
                "rights_scope"
            ],
            "properties": {
                "kind": {"const": "HSKLevelBand"}, "stable_id": nonempty(),
                "source_band_id": nonempty(), "source_standard_id": nonempty(),
                "raw_level_label": {"type": "string"}, "raw_field_sha256": digest,
                "raw_label_term": {"type": "object", "additionalProperties": False, "required": ["kind", "value", "datatype", "language"], "properties": {"kind": {"const": "literal"}, "value": {"type": "string"}, "datatype": nullable_string(), "language": nullable_string()}},
                "normalized_member_levels": {"oneOf": [{"type": "array", "minItems": 1, "uniqueItems": True, "items": {"type": "integer", "minimum": 1, "maximum": 9}}, {"type": "null"}]},
                "merged_level_identity": {"oneOf": [nonempty(), {"type": "null"}]},
                "parser_name": nonempty(), "parser_version": nonempty(),
                "parse_status": {"enum": ["PARSED_CANDIDATE", "HOLD_UNPARSED"]},
                "semantics_status": {"const": "UNKNOWN_HOLD"},
                "source_record_line_sha256": digest,
                "rights_scope": {"$ref": "#/$defs/rightsScope"}
            }
        },
        "HSKLevelLabelObservation": {
            "type": "object", "additionalProperties": False,
            "required": [
                "kind", "raw_level_label", "occurrence_count", "source_record_refs",
                "raw_field_sha256", "parser_name", "parser_version", "parse_status",
                "normalized_member_levels", "merged_level_identity", "semantics_status",
                "rights_scope"
            ],
            "properties": {
                "kind": {"const": "HSKLevelLabelObservation"},
                "raw_level_label": {"type": "string"},
                "occurrence_count": {"type": "integer", "minimum": 1},
                "source_record_refs": {"type": "array", "minItems": 1, "uniqueItems": True, "items": nonempty()},
                "raw_field_sha256": digest,
                "parser_name": nonempty(), "parser_version": nonempty(),
                "parse_status": {"enum": ["PARSED_CANDIDATE", "HOLD_UNPARSED"]},
                "normalized_member_levels": {
                    "oneOf": [
                        {"type": "array", "minItems": 1, "uniqueItems": True, "items": {"type": "integer", "minimum": 1, "maximum": 9}},
                        {"type": "null"}
                    ]
                },
                "merged_level_identity": {"oneOf": [nonempty(), {"type": "null"}]},
                "semantics_status": {"const": "UNKNOWN_HOLD"},
                "rights_scope": {"$ref": "#/$defs/rightsScope"}
            }
        },
        "HSKSourceBlockMapping": {
            "type": "object", "additionalProperties": False,
            "required": [
                "kind", "source_record_id", "source_block_id", "block_kind_raw",
                "level_band_ref", "printed_page_label_recorded_raw",
                "printed_page_source_datatype", "printed_page_original_visual_verification",
                "pdf_page_index_zero_based", "pdf_page_number_one_based",
                "pdf_page_locator_status", "section_locator_raw", "scope_topic_ref",
                "source_block_status", "raw_text_sha256", "raw_text_utf8_bytes",
                "source_block_jsonl_line_sha256", "raw_field_digests", "raw_text_storage",
                "rights_scope"
            ],
            "properties": {
                "kind": {"const": "HSKSourceBlockMapping"},
                "source_record_id": {"type": "string", "pattern": "^urn:learn-kg:source:[A-Za-z0-9._:-]+$"},
                "source_block_id": nonempty(),
                "block_kind_raw": {"enum": ["Task", "Topic", "Grammar"]},
                "level_band_ref": nonempty(),
                "printed_page_label_recorded_raw": nonempty(),
                "printed_page_source_datatype": {"const": "http://www.w3.org/2001/XMLSchema#integer"},
                "printed_page_original_visual_verification": {"const": "HOLD_LAYOUT_REVIEW_PENDING"},
                "pdf_page_index_zero_based": {"type": "null"},
                "pdf_page_number_one_based": {"type": "null"},
                "pdf_page_locator_status": {"const": "UNKNOWN_NOT_DERIVED_FROM_PRINTED_LABEL"},
                "section_locator_raw": {"type": "null"},
                "scope_topic_ref": nonempty(),
                "source_block_status": {"const": "LAYOUT_REVIEW_PENDING"},
                "raw_text_sha256": digest,
                "raw_text_utf8_bytes": {"type": "integer", "minimum": 0},
                "source_block_jsonl_line_sha256": digest,
                "raw_field_digests": {
                    "type": "object", "additionalProperties": False,
                    "required": ["source", "blockKind", "levelBand", "printedPage", "scopeTopic", "status", "rawText"],
                    "properties": {
                        "source": digest, "blockKind": digest, "levelBand": digest,
                        "printedPage": digest, "scopeTopic": digest, "status": digest, "rawText": digest
                    }
                },
                "raw_text_storage": {"const": "PRIVATE_ARCHIVE_ONLY_NOT_COPIED"},
                "rights_scope": {"$ref": "#/$defs/rightsScope"}
            }
        },
        "HSKRawFieldCapture": {
            "type": "object", "additionalProperties": False,
            "required": [
                "kind", "field_name", "raw_value", "raw_value_status",
                "normalized_value", "parser_name", "parser_version", "parse_status",
                "raw_field_sha256", "source_locator_ref"
            ],
            "properties": {
                "kind": {"const": "HSKRawFieldCapture"},
                "field_name": nonempty(),
                "raw_value": {},
                "raw_value_status": {"enum": ["PRESERVED", "PRIVATE_ARCHIVE_ONLY", "UNKNOWN_PRESERVED", "MISSING", "SYNTHETIC_ONLY"]},
                "normalized_value": {},
                "parser_name": nonempty(),
                "parser_version": nonempty(),
                "parse_status": {"enum": ["PARSED_CANDIDATE", "NOT_ATTEMPTED", "UNPARSED", "AMBIGUOUS", "ERROR", "HOLD"]},
                "raw_field_sha256": digest,
                "source_locator_ref": {"oneOf": [nonempty(), {"type": "null"}]}
            }
        },
        "HSKTypedRecord": {
            "type": "object", "additionalProperties": False,
            "required": [
                "kind", "record_kind", "record_kind_source", "source_record_id",
                "normalized_knowledge_id", "raw_surface", "raw_fields",
                "source_locator_ref", "rights_scope"
            ],
            "properties": {
                "kind": {"const": "HSKTypedRecord"},
                "record_kind": {"enum": ["VOCABULARY_ITEM", "CHARACTER_ITEM", "SOURCE_BLOCK", "CAPABILITY", "CATEGORY", "CHARACTER_MEMBERSHIP"]},
                "record_kind_source": {"const": "EXPLICIT_TYPED_FIELD_NOT_STRING_HEURISTIC"},
                "source_record_id": {"oneOf": [nonempty(), {"type": "null"}]},
                "normalized_knowledge_id": nonempty(),
                "raw_surface": {"oneOf": [nonempty(), {"type": "null"}]},
                "raw_fields": {"type": "array", "items": {"$ref": "#/$defs/HSKRawFieldCapture"}},
                "source_locator_ref": {"oneOf": [nonempty(), {"type": "null"}]},
                "rights_scope": {"$ref": "#/$defs/rightsScope"}
            }
        },
        "HSKSourceLocator": {
            "type": "object", "additionalProperties": False,
            "required": [
                "kind", "source_record_id", "source_block_id", "source_text_sha256",
                "source_block_jsonl_sha256", "pdf_page_index_zero_based",
                "pdf_page_number_one_based", "printed_page_label_recorded_raw",
                "printed_page_source_datatype", "printed_page_numeric_value",
                "printed_page_status", "scope_topic_ref", "section_locator_raw",
                "raw_text_sha256", "locator_origin", "rights_scope"
            ],
            "properties": {
                "kind": {"const": "HSKSourceLocator"},
                "source_record_id": nonempty(), "source_block_id": nonempty(),
                "source_text_sha256": digest, "source_block_jsonl_sha256": digest,
                "pdf_page_index_zero_based": {"oneOf": [{"type": "integer", "minimum": 0}, {"type": "null"}]},
                "pdf_page_number_one_based": {"oneOf": [{"type": "integer", "minimum": 1}, {"type": "null"}]},
                "printed_page_label_recorded_raw": {"oneOf": [nonempty(), {"type": "null"}]},
                "printed_page_source_datatype": {"oneOf": [nonempty(), {"type": "null"}]},
                "printed_page_numeric_value": {"oneOf": [{"type": "integer", "minimum": 1}, {"type": "null"}]},
                "printed_page_status": {"enum": ["RECORDED_NOT_VISUALLY_VERIFIED", "MISSING_HOLD", "SYNTHETIC_ONLY"]},
                "scope_topic_ref": {"oneOf": [nonempty(), {"type": "null"}]},
                "section_locator_raw": {"oneOf": [nonempty(), {"type": "null"}]},
                "raw_text_sha256": digest,
                "locator_origin": {"enum": ["SOURCE_BLOCK_RDF", "SYNTHETIC_ONLY"]},
                "rights_scope": {"$ref": "#/$defs/rightsScope"}
            }
        }
    }
    for name in ("HSKLevelBand", "HSKLevelLabelObservation"):
        defs[name]["allOf"] = [{"if": {"properties": {"parse_status": {"const": "HOLD_UNPARSED"}}},
            "then": {"properties": {"normalized_member_levels": {"type": "null"}, "merged_level_identity": {"type": "null"}}},
            "else": {"properties": {"normalized_member_levels": {"type": "array"}, "merged_level_identity": {"type": "string"}}}}]
    defs["HSKRawFieldCapture"]["allOf"] = [{"if": {"properties": {"parse_status": {"not": {"const": "PARSED_CANDIDATE"}}}},
        "then": {"properties": {"normalized_value": {"type": "null"}}}}]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:learn-kg:hs00:source-mapping-schema:1",
        "title": "HS00 HSK Source and Standard Mapping Candidate",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version", "kind", "status", "standard_identity", "source_records",
            "level_bands", "level_label_observations", "source_blocks",
            "record_kind_examples", "archive_evidence", "preservation_scope", "limits"
        ],
        "properties": {
            "schema_version": {"const": "learn-kg-hs00-source-mapping-1"},
            "kind": {"const": "HSKSourceMapping"},
            "status": {"const": "CANDIDATE_PREPARATION_ONLY"},
            "standard_identity": {"$ref": "#/$defs/HSKStandardIdentity"},
            "source_records": {"type": "array", "minItems": 3, "items": {"$ref": "#/$defs/HSKSourceRecord"}},
            "level_bands": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/HSKLevelBand"}},
            "level_label_observations": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/HSKLevelLabelObservation"}},
            "source_blocks": {"type": "array", "minItems": 94, "items": {"$ref": "#/$defs/HSKSourceBlockMapping"}},
            "source_block_summary": {
                "type": "object", "additionalProperties": False,
                "required": ["count", "source_record_counts", "block_kind_counts", "scope_topic_counts", "level_band_counts", "recorded_printed_page_values"],
                "properties": {
                    "count": {"const": 94},
                    "source_record_counts": {"type": "object"},
                    "block_kind_counts": {"type": "object"},
                    "scope_topic_counts": {"type": "object"},
                    "level_band_counts": {"type": "object"},
                    "recorded_printed_page_values": {
                        "type": "object", "additionalProperties": False,
                        "required": ["count", "unique_count", "minimum", "maximum", "contiguous_ranges", "visual_verification", "pdf_page_index_and_number_bound"],
                        "properties": {
                            "count": {"const": 94}, "unique_count": {"const": 94},
                            "minimum": {"const": 2}, "maximum": {"const": 403},
                            "contiguous_ranges": {"const": [[2, 54], [56, 75], [383, 403]]},
                            "visual_verification": {"const": "HOLD_LAYOUT_REVIEW_PENDING"},
                            "pdf_page_index_and_number_bound": {"const": False}
                        }
                    }
                }
            },
            "level_label_summary": {
                "type": "object", "additionalProperties": False,
                "required": ["lexical_record_count", "unique_raw_label_count", "parenthetical_raw_label_record_count", "range_raw_label_record_count", "parser_name", "parser_version", "semantics_status"],
                "properties": {
                    "lexical_record_count": {"const": 11000},
                    "unique_raw_label_count": {"const": 28},
                    "parenthetical_raw_label_record_count": {"const": 102},
                    "range_raw_label_record_count": {"type": "integer", "minimum": 1},
                    "parser_name": {"const": "hs00-level-label-parser"},
                    "parser_version": {"const": "0.1.0"},
                    "semantics_status": {"const": "UNKNOWN_HOLD"}
                }
            },
            "record_kind_examples": {
                "type": "array", "minItems": 6,
                "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["record_kind", "source_rdf_kind", "source_record_id", "normalized_knowledge_id", "rights_scope"],
                    "properties": {
                        "record_kind": {"enum": ["VOCABULARY_ITEM", "CHARACTER_ITEM", "SOURCE_BLOCK", "CAPABILITY", "CATEGORY", "CHARACTER_MEMBERSHIP"]},
                        "source_rdf_kind": nonempty(),
                        "source_record_id": {"oneOf": [nonempty(), {"type": "null"}]},
                        "normalized_knowledge_id": nonempty(),
                        "membership_record_id": {"oneOf": [nonempty(), {"type": "null"}]},
                        "rights_scope": {"$ref": "#/$defs/rightsScope"}
                    }
                }
            },
            "archive_evidence": {"type": "object"},
            "preservation_scope": {"$ref": "#/$defs/rightsScope"},
            "limits": {"type": "array", "minItems": 1, "items": nonempty()}
        },
        "$defs": defs
    }


def make_fixtures(mapping: dict[str, Any]) -> dict[str, Any]:
    source = next(x for x in mapping["source_records"] if x["source_id"] == "RHSK01")
    block = mapping["source_blocks"][0]
    raw_unknown = "vendor_field: Ω"
    raw_field = {
        "kind": "HSKRawFieldCapture", "field_name": "vendor_extension",
        "raw_value": raw_unknown, "raw_value_status": "PRESERVED",
        "normalized_value": None, "parser_name": "hs00-raw-field-capture",
        "parser_version": "0.1.0", "parse_status": "NOT_ATTEMPTED",
        "raw_field_sha256": sha(raw_unknown.encode("utf-8")),
        "source_locator_ref": block["source_block_id"]
    }
    def typed(kind: str, normalized_id: str) -> dict[str, Any]:
        return {
            "kind": "HSKTypedRecord", "record_kind": kind,
            "record_kind_source": "EXPLICIT_TYPED_FIELD_NOT_STRING_HEURISTIC",
            "source_record_id": source["source_record_id"],
            "normalized_knowledge_id": normalized_id,
            "raw_surface": "一", "raw_fields": [{
                "kind": "HSKRawFieldCapture", "field_name": "surfaceRaw",
                "raw_value": "一", "raw_value_status": "SYNTHETIC_ONLY",
                "normalized_value": "一", "parser_name": "hs00-synthetic-surface",
                "parser_version": "0.1.0", "parse_status": "PARSED_CANDIDATE",
                "raw_field_sha256": sha("一".encode("utf-8")), "source_locator_ref": None
            }, raw_field],
            "source_locator_ref": None, "rights_scope": RIGHTS_SCOPE.copy()
        }
    source_locator = {
        "kind": "HSKSourceLocator", "source_record_id": source["source_record_id"],
        "source_block_id": block["source_block_id"],
        "source_text_sha256": source["canonical_connector_text_sha256"],
        "source_block_jsonl_sha256": mapping["archive_evidence"]["source_block_jsonl_sha256"],
        "pdf_page_index_zero_based": 12, "pdf_page_number_one_based": 13,
        "printed_page_label_recorded_raw": "383",
        "printed_page_source_datatype": "http://www.w3.org/2001/XMLSchema#integer",
        "printed_page_numeric_value": 383, "printed_page_status": "SYNTHETIC_ONLY",
        "scope_topic_ref": block["scope_topic_ref"], "section_locator_raw": None,
        "raw_text_sha256": block["raw_text_sha256"], "locator_origin": "SYNTHETIC_ONLY",
        "rights_scope": RIGHTS_SCOPE.copy()
    }
    missing_page_locator = dict(source_locator)
    missing_page_locator.update({
        "pdf_page_index_zero_based": 5, "pdf_page_number_one_based": 6,
        "printed_page_label_recorded_raw": None, "printed_page_source_datatype": None,
        "printed_page_numeric_value": None, "printed_page_status": "MISSING_HOLD"
    })
    positive = [
        {"case_id": "HS00-P01", "case_type": "LEVEL_LABEL", "input": {"raw_level_label": "4（5）"}, "expected": {"parse_status": "PARSED_CANDIDATE", "normalized_member_levels": [4, 5], "raw_preserved_exactly": "4（5）"}},
        {"case_id": "HS00-P02", "case_type": "LEVEL_LABEL", "input": {"raw_level_label": "2（3）（5）"}, "expected": {"parse_status": "PARSED_CANDIDATE", "normalized_member_levels": [2, 3, 5], "raw_preserved_exactly": "2（3）（5）"}},
        {"case_id": "HS00-P03", "case_type": "LEVEL_LABEL", "input": {"raw_level_label": "3（4）（7-9）"}, "expected": {"parse_status": "PARSED_CANDIDATE", "normalized_member_levels": [3, 4, 7, 8, 9], "raw_preserved_exactly": "3（4）（7-9）"}},
        {"case_id": "HS00-P04", "case_type": "LEVEL_LABEL", "input": {"raw_level_label": "7-9"}, "expected": {"parse_status": "PARSED_CANDIDATE", "normalized_member_levels": [7, 8, 9], "raw_preserved_exactly": "7-9"}},
        {"case_id": "HS00-P05", "case_type": "LEVEL_LABEL", "input": {"raw_level_label": "1-2"}, "expected": {"parse_status": "PARSED_CANDIDATE", "normalized_member_levels": [1, 2], "raw_preserved_exactly": "1-2"}},
        {"case_id": "HS00-P06", "case_type": "PAGE_LOCATOR", "input": source_locator, "expected": {"valid": True, "pdf_page_index_zero_based": 12, "pdf_page_number_one_based": 13, "printed_page_label_recorded_raw": "383", "printed_page_numeric_value": 383}},
        {"case_id": "HS00-P07", "case_type": "PAGE_LOCATOR", "input": missing_page_locator, "expected": {"valid": True, "printed_page_label_recorded_raw": None, "printed_page_numeric_value": None}},
        {"case_id": "HS00-P08", "case_type": "TYPED_RECORD", "input": typed("VOCABULARY_ITEM", "urn:learn-kg:hsk:2025-11:lex:synthetic-one"), "expected": {"valid": True, "record_kind": "VOCABULARY_ITEM", "raw_surface": "一"}},
        {"case_id": "HS00-P09", "case_type": "TYPED_RECORD", "input": typed("CHARACTER_ITEM", "urn:learn-kg:han:synthetic-one"), "expected": {"valid": True, "record_kind": "CHARACTER_ITEM", "raw_surface": "一"}},
        {"case_id": "HS00-P10", "case_type": "RAW_FIELD", "input": raw_field, "expected": {"valid": True, "raw_value_preserved": raw_unknown, "normalized_value": None, "parse_status": "NOT_ATTEMPTED"}},
        {"case_id": "HS00-P11", "case_type": "SOURCE_RECORD", "input": source, "expected": {"valid": True, "historical_raw_pdf_sha256": None, "rights": "HOLD_NO_PUBLICATION_OR_REDISTRIBUTION", "publication": "NOT_AUTHORIZED"}}
    ]
    negative = [
        {"case_id": "HS00-N01", "case_type": "LEVEL_LABEL", "input": {"raw_level_label": "9（10）"}, "expected": {"parse_status": "HOLD_UNPARSED", "normalized_member_levels": None, "raw_preserved_exactly": "9（10）"}},
        {"case_id": "HS00-N02", "case_type": "LEVEL_LABEL", "input": {"raw_level_label": "3（4"}, "expected": {"parse_status": "HOLD_UNPARSED", "normalized_member_levels": None, "raw_preserved_exactly": "3（4"}},
        {"case_id": "HS00-N03", "case_type": "LEVEL_LABEL", "input": {"raw_level_label": " 4（5）"}, "expected": {"parse_status": "HOLD_UNPARSED", "normalized_member_levels": None, "raw_preserved_exactly": " 4（5）"}},
        {"case_id": "HS00-N04", "case_type": "SOURCE_ID_MISMATCH", "input": {"source_record_id": "urn:learn-kg:source:RHSK02", "source_block_source_ref": "urn:learn-kg:source:RHSK01"}, "expected": {"valid": False, "reason": "SOURCE_RECORD_BLOCK_BINDING_MISMATCH"}},
        {"case_id": "HS00-N05", "case_type": "DUPLICATE_SOURCE_ID", "input": {"source_record_ids": ["urn:learn-kg:source:RHSK01", "urn:learn-kg:source:RHSK01"]}, "expected": {"valid": False, "reason": "DUPLICATE_SOURCE_RECORD_ID"}},
        {"case_id": "HS00-N06", "case_type": "PAGE_LOCATOR", "input": {"pdf_page_index_zero_based": 12, "pdf_page_number_one_based": 14, "printed_page_label_recorded_raw": "383"}, "expected": {"valid": False, "reason": "PDF_INDEX_AND_PAGE_NUMBER_CONFLICT"}},
        {"case_id": "HS00-N07", "case_type": "PAGE_LOCATOR", "input": {"pdf_page_index_zero_based": 5, "pdf_page_number_one_based": 6, "printed_page_label_recorded_raw": None, "printed_page_numeric_value": 383}, "expected": {"valid": False, "reason": "MISSING_PRINTED_LABEL_MUST_NOT_BE_FABRICATED"}},
        {"case_id": "HS00-N08", "case_type": "RAW_FIELD", "input": {"kind": "HSKRawFieldCapture", "field_name": "x", "raw_value": "x", "raw_value_status": "PRESERVED", "normalized_value": None, "parse_status": "NOT_ATTEMPTED", "raw_field_sha256": sha(b"x"), "source_locator_ref": None}, "expected": {"valid": False, "reason": "PARSER_NAME_AND_VERSION_REQUIRED"}},
        {"case_id": "HS00-N09", "case_type": "LEVEL_FIELD_SILENT_NORMALIZATION", "input": {"raw_level_label": " 4（5）", "normalized_member_levels": [4, 5], "parse_status": "PARSED_CANDIDATE"}, "expected": {"valid": False, "reason": "RAW_FIELD_MUST_NOT_BE_TRIMMED_OR_REWRITTEN"}},
        {"case_id": "HS00-N10", "case_type": "TYPED_RECORD", "input": {"kind": "HSKTypedRecord", "record_kind_source": "EXPLICIT_TYPED_FIELD_NOT_STRING_HEURISTIC", "source_record_id": source["source_record_id"], "normalized_knowledge_id": "urn:learn-kg:hsk:2025-11:lex:missing-kind", "raw_surface": "一", "raw_fields": [], "source_locator_ref": None, "rights_scope": RIGHTS_SCOPE.copy()}, "expected": {"valid": False, "reason": "RECORD_KIND_REQUIRED"}},
        {"case_id": "HS00-N11", "case_type": "RIGHTS_SCOPE", "input": {**RIGHTS_SCOPE, "rights": "PUBLIC_AUTHORIZED"}, "expected": {"valid": False, "reason": "RIGHTS_MUST_REMAIN_HOLD"}},
        {"case_id": "HS00-N12", "case_type": "STANDARD_IDENTITY", "input": {"identity_status": "VERIFIED"}, "expected": {"valid": False, "reason": "STANDARD_IDENTITY_REQUIRES_UNKNOWN_HOLD"}},
        {"case_id": "HS00-N13", "case_type": "SOURCE_KNOWLEDGE_ID", "input": {"source_record_id": "urn:learn-kg:source:RHSK01", "normalized_knowledge_id": "urn:learn-kg:source:RHSK01"}, "expected": {"valid": False, "reason": "SOURCE_RECORD_ID_MUST_NOT_BE_KNOWLEDGE_ID"}}
    ]
    for case in positive + negative:
        case["preservation_scope"] = RIGHTS_SCOPE.copy()
    return {
        "schema_version": "learn-kg-hs00-fixtures-1",
        "status": "ORIGINAL_FINITE_SYNTHETIC_AND_SOURCE_METADATA_FIXTURES",
        "preservation_scope": RIGHTS_SCOPE.copy(),
        "positive_cases": positive,
        "negative_cases": negative,
        "limits": [
            "Fixtures are synthetic protocol examples except when explicitly identified as source metadata; they are not HSK professional correctness or learner outcome evidence.",
            "No full vocabulary, character, capability or taxonomy conversion is included.",
            "A HOLD parse result preserves raw text; it is not a schema failure when the source value is unknown or ambiguous."
        ]
    }


def make_db01_projections(mapping: dict[str, Any]) -> dict[str, Any]:
    mapping_sha = sha((HERE / "source-mapping.json").read_bytes())
    source_records = mapping["source_records"]
    standard_ref = ref("Standard", STANDARD_ID, "H07")
    source_refs = []
    records: list[dict[str, Any]] = []
    for index, source in enumerate(source_records):
        sid = source["source_id"]
        stable_id = "HS00.SOURCE." + sid
        source_ref = ref("Source", stable_id, "EVIDENCE")
        source_refs.append(source_ref)
        records.append({
            "kind": "Source", "stable_id": stable_id, "owner": "EVIDENCE",
            "status": "HOLD",
            "conditions": [
                "CURRENT_RAW_PDF_BYTES_VERIFIED_CROSS_FAULT",
                "CANONICAL_CONNECTOR_TEXT_HASH_SEPARATE",
                "HISTORICAL_RAW_PDF_BYTE_IDENTITY_HOLD",
                "RIGHTS_HOLD_NO_PUBLICATION_OR_REDISTRIBUTION",
                "VISUAL_LAYOUT_HOLD"
            ],
            "negative_boundary": "Current byte identity does not establish historical PDF identity, rights, publication authority, official source title or semantic qualification.",
            "provenance": [{
                "source_path": "docs/implementation/hs00/source-mapping.json",
                "source_sha256": mapping_sha,
                "json_pointer": f"/source_records/{index}",
                "source_status": "PRIVATE_PRESERVATION_CANDIDATE"
            }],
            "title": source["provider_identity"]["original_name"],
            "identifier": source["source_record_id"],
            "access": "PRIVATE_ONLY",
            "rights": "HOLD",
            "qualification": "NOT_RUN",
            "bibliography": f"Private extracted-text source alias {sid}; authoritative publication title and bibliographic identity are not verified.",
            "recorded_locator": None,
            "recorded_rights": "HOLD_NO_PUBLICATION_OR_REDISTRIBUTION"
        })
    records.append({
        "kind": "Standard", "stable_id": STANDARD_ID, "owner": "H07", "status": "HOLD",
        "conditions": [
            "SOURCE_RELEASE_LABEL_2025_11_PRESERVED_EXACTLY",
            "SOURCE_GRAPH_STATUS_STAGING",
            "AUTHORITATIVE_STANDARD_IDENTITY_NOT_VERIFIED",
            "H07_FINAL_STANDARD_MAPPING_NOT_RUN",
            "RIGHTS_HOLD_NO_PUBLICATION_OR_REDISTRIBUTION"
        ],
        "negative_boundary": "HSK is a source-family hint only. No official edition, effective date, equivalence, normative mapping or qualification is asserted.",
        "provenance": [{
            "source_path": "docs/implementation/hs00/source-mapping.json",
            "source_sha256": mapping_sha,
            "json_pointer": "/standard_identity",
            "source_status": "PRIVATE_PRESERVATION_CANDIDATE"
        }],
        "edition": mapping["standard_identity"]["source_declared_version_label_raw"],
        "standard_name": "HSK",
        "source_refs": source_refs,
        "effective_date": None
    })
    for index, band in enumerate(mapping["level_bands"]):
        if band["parse_status"] != "PARSED_CANDIDATE":
            continue  # lossless HOLD stays in source mapping, not a DB01 projection
        records.append({
            "kind": "StandardBand",
            "stable_id": band["stable_id"],
            "owner": "H07",
            "status": "HOLD",
            "conditions": [
                "RAW_LEVEL_LABEL_PRESERVED",
                "NORMALIZED_MEMBER_LEVELS_ARE_SYNTACTIC_CANDIDATE_ONLY",
                "PARENTHETICAL_SEMANTICS_UNKNOWN_HOLD"
            ],
            "negative_boundary": "Do not treat the parsed member set as official standard membership or a qualified level equivalence.",
            "provenance": [{
                "source_path": "docs/implementation/hs00/source-mapping.json",
                "source_sha256": mapping_sha,
                "json_pointer": f"/level_bands/{index}",
                "source_status": "PRIVATE_PRESERVATION_CANDIDATE"
            }],
            "standard_ref": standard_ref,
            "raw_band": band["raw_level_label"],
            "band_scope": "Source-recorded level label; candidate syntactic members only, authoritative semantics unknown."
        })
    for index, block in enumerate(mapping["source_blocks"]):
        sid = block["source_record_id"].rsplit(":", 1)[-1]
        source_ref = ref("Source", "HS00.SOURCE." + sid, "EVIDENCE")
        location = (
            "source_block_id=" + block["source_block_id"] +
            ";printed_page_label_recorded=" + block["printed_page_label_recorded_raw"] +
            ";pdf_page_index_zero_based=UNKNOWN;pdf_page_number_one_based=UNKNOWN" +
            ";scope_topic_ref=" + block["scope_topic_ref"]
        )
        records.append({
            "kind": "Locator",
            "stable_id": f"HS00.LOCATOR.{index + 1:03d}",
            "owner": "EVIDENCE",
            "status": "HOLD",
            "conditions": [
                "SOURCEBLOCK_REPLAY_94_OF_94",
                "PRINTED_PAGE_VALUE_IS_RECORDED_RDF_INTEGER",
                "PDF_PAGE_INDEX_AND_PAGE_NUMBER_NOT_MAPPED",
                "VISUAL_LAYOUT_HOLD"
            ],
            "negative_boundary": "Recorded printed-page integer is not a PDF page index or one-based PDF page number; no visual layout or page glyph qualification is asserted.",
            "provenance": [{
                "source_path": "docs/implementation/hs00/source-mapping.json",
                "source_sha256": mapping_sha,
                "json_pointer": f"/source_blocks/{index}",
                "source_status": "PRIVATE_PRESERVATION_CANDIDATE"
            }],
            "source_ref": source_ref,
            "location": location,
            "attribution": "RECORDED_NOT_REVERIFIED",
            "verification": "SourceBlock metadata and text digest are preserved; printed label is not visually reverified and PDF page index/number remain unknown."
        })
    synthetic_membership = {
        "kind": "SourceMembership",
        "stable_id": "HS00.SYNTHETIC.MEMBERSHIP",
        "owner": "H07",
        "status": "HOLD",
        "conditions": ["SYNTHETIC_INTERFACE_FIXTURE_ONLY", "NO_ACTUAL_HSK01_MEMBERSHIP_CONVERSION"],
        "negative_boundary": "Synthetic shape demonstration only; does not assert any real vocabulary/character membership or level qualification.",
        "provenance": [{
            "source_path": "docs/implementation/hs00/fixtures.json",
            "source_sha256": sha((HERE / "fixtures.json").read_bytes()) if (HERE / "fixtures.json").exists() else "0" * 64,
            "json_pointer": "/positive_cases/0",
            "source_status": "ORIGINAL_SYNTHETIC_FIXTURE"
        }],
        "standard_ref": standard_ref,
        "band_ref": ref("StandardBand", mapping["level_bands"][0]["stable_id"], "H07"),
        "source_ref": source_refs[0],
        "section": "SYNTHETIC_INTERFACE_FIXTURE_ONLY",
        "ordinal": 1,
        "printed_page": None,
        "raw_fields": [{"name": "levelRaw", "value": "3（4）（7-9）"}],
        "mapping_status": "HOLD",
        "semantic_refs": []
    }
    # The synthetic record is stored separately and never counted as an imported source membership.
    refs = [
        source_refs[0], standard_ref,
        ref("StandardBand", mapping["level_bands"][0]["stable_id"], "H07"),
        ref("Locator", "HS00.LOCATOR.001", "EVIDENCE"),
        ref("SourceMembership", "HS00.SYNTHETIC.MEMBERSHIP", "H07")
    ]
    return {
        "schema_version": "learn-kg-hs00-db01-projection-1",
        "status": "SYNTACTIC_COMPATIBILITY_ONLY",
        "package_binding_status": "NOT_REGISTERED_NO_PACKAGE_MANIFEST",
        "candidate_package_ref": {"package_id": PACKAGE_ID, "version": PACKAGE_VERSION},
        "db01_schema_sha256": sha((ROOT / "docs/implementation/db01/canonical.schema.json").read_bytes()),
        "if01_interface_sha256": sha((ROOT / "docs/implementation/if01/interface-contract.json").read_bytes()),
        "source_mapping_sha256": mapping_sha,
        "records": records,
        "synthetic_records": [synthetic_membership],
        "if01_typed_reference_examples": refs,
        "limits": [
            "All DB01 records are HOLD candidate projections. The candidate package ID/version is a shape example only; no HSK package manifest is created or registered.",
            "The single SourceMembership is synthetic and must not be counted as HSK01 conversion output.",
            "No DB01 schema or IF01 contract is modified."
        ]
    }


def main() -> None:
    mapping = json.loads((HERE / "source-mapping.json").read_text(encoding="utf-8"))
    schema = make_schema()
    dump(HERE / "schema.json", schema)
    fixtures = make_fixtures(mapping)
    dump(HERE / "fixtures.json", fixtures)
    db01 = make_db01_projections(mapping)
    dump(HERE / "db01-projections.json", db01)
    schema_sha = sha((HERE / "schema.json").read_bytes())
    fixtures_sha = sha((HERE / "fixtures.json").read_bytes())
    db01_sha = sha((HERE / "db01-projections.json").read_bytes())
    mapping_sha = sha((HERE / "source-mapping.json").read_bytes())
    db01_schema_sha = sha((ROOT / "docs/implementation/db01/canonical.schema.json").read_bytes())
    if01_sha = sha((ROOT / "docs/implementation/if01/interface-contract.json").read_bytes())
    src01_receipt_sha = sha((ROOT / "evidence/tasks/SRC01/SRC01-FORMAL-02.json").read_bytes())
    contract = {
        "schema_version": "learn-kg-hs00-interface-1",
        "task_issue": 22,
        "status": "CANDIDATE_PREPARATION_ONLY",
        "owner": "HS00",
        "schema": {"path": "docs/implementation/hs00/schema.json", "sha256": schema_sha},
        "source_mapping": {"path": "docs/implementation/hs00/source-mapping.json", "sha256": mapping_sha},
        "fixtures": {"path": "docs/implementation/hs00/fixtures.json", "sha256": fixtures_sha, "positive_cases": len(fixtures["positive_cases"]), "negative_cases": len(fixtures["negative_cases"])},
        "db01_projection": {"path": "docs/implementation/hs00/db01-projections.json", "sha256": db01_sha, "actual_records": len(db01["records"]), "synthetic_records": len(db01["synthetic_records"])},
        "inputs": {
            "DB01_schema_sha256": db01_schema_sha,
            "IF01_interface_contract_sha256": if01_sha,
            "SRC01_receipt_sha256": src01_receipt_sha,
            "SRC01_scope": "PRESERVATION_VERIFIED_RESTRICTED_ONLY"
        },
        "standard_identity": {
            "source_standard_id": mapping["standard_identity"]["source_standard_id"],
            "source_declared_version_label_raw": mapping["standard_identity"]["source_declared_version_label_raw"],
            "normalized_internal_version_candidate": mapping["standard_identity"]["normalized_internal_version_candidate"],
            "identity_status": "UNKNOWN_HOLD",
            "authority_verification": "NOT_RUN",
            "H07_final_standard_mapping": "NOT_RUN"
        },
        "source_identity": {
            "stable_source_record_ids": [x["source_record_id"] for x in mapping["source_records"]],
            "source_provider": "GOOGLE_DRIVE",
            "original_filename": "preserved from private backup manifest",
            "provider_file_id": "NOT_STORED_IN_PUBLIC_REPOSITORY",
            "original_path": "NOT_STORED_IN_PUBLIC_REPOSITORY",
            "current_revision_id": "NOT_CAPTURED_IN_SAFE_EVIDENCE",
            "current_revision_count": 1,
            "previous_revision_available": False
        },
        "digest_separation": {
            "current_raw_pdf_sha256": "per-source; current bytes verified across Google Drive/Aliyun/V100",
            "historical_raw_pdf_sha256": "null/HOLD; no prior Drive revision or historical raw digest",
            "canonical_connector_text_sha256": "per-source; exact historical text match",
            "source_block_jsonl_sha256": "overall file digest plus per-source subset digest",
            "source_block_raw_text_sha256": "per SourceBlock rawText value; raw text remains in private archive"
        },
        "level_label_contract": {
            "raw_value_is_immutable": True,
            "parser_name": "hs00-level-label-parser",
            "parser_version": "0.1.0",
            "supported_observed_grammar": "single digit or ascending digit range; optional repeated fullwidth-parenthesis groups; exact punctuation required",
            "normalized_member_levels": "candidate syntax only",
            "merged_level_identity": "hash over exact source standard ID and raw label; punctuation-sensitive",
            "unknown_or_ambiguous": "raw preserved; parse_status HOLD_UNPARSED; no normalization"
        },
        "page_locator_contract": {
            "pdf_page_index_zero_based": "independent nullable integer",
            "pdf_page_number_one_based": "independent nullable integer; when both PDF values exist, page number must equal index + 1",
            "printed_page_label_recorded_raw": "separate exact recorded value",
            "no_inference": "printed page label never populates PDF page index or one-based page number",
            "current_source_blocks": "all 94 have recorded RDF integer printedPage values; block-specific PDF page index/number are UNKNOWN/HOLD"
        },
        "record_kind_contract": {
            "enum": ["VOCABULARY_ITEM", "CHARACTER_ITEM", "SOURCE_BLOCK", "CAPABILITY", "CATEGORY", "CHARACTER_MEMBERSHIP"],
            "source_of_truth": "explicit typed record field or source RDF kind mapping",
            "forbidden_heuristic": "never infer vocabulary versus character from string length, Unicode shape or glyph count",
            "source_record_id_is_not_normalized_knowledge_id": True
        },
        "parsing_contract": {
            "raw_and_normalized_fields_separate": True,
            "parser_name_and_version_required": True,
            "parse_status_required": True,
            "source_locator_required_or_explicit_null": True,
            "raw_field_sha256_required": True,
            "unknown_unparsed_fields": "raw value retained and queryable; normalized value null; parse_status NOT_ATTEMPTED/UNPARSED/AMBIGUOUS/ERROR/HOLD"
        },
        "semantic_validation": {
            "entrypoint": "hs00_semantic.py:HS00Validator.from_pinned_files",
            "validator_sha256": sha((HERE / "hs00_semantic.py").read_bytes()),
            "record_api": "validate(record, expected_kind)",
            "required": True,
            "mapping_binding": "caller must supply independently pinned interface-contract SHA256; schema and source mapping bytes checked against it; validate against pinned source and block index",
            "raw_field_digest_encoding": "UTF-8 exact string bytes; other JSON values sorted-key compact UTF-8 JSON, ensure_ascii=false, allow_nan=false; null means captured null, not hidden archive digest",
            "level_band_digest_encoding": "canonical sorted-key compact UTF-8 JSON of exact raw_label_term (RDF literal); raw label must equal term.value",
            "level_observation_digest_encoding": "UTF-8 exact raw label bytes",
            "unresolved_band": "HOLD_UNPARSED retains raw string and RDF term; null members and merged identity; no DB01 StandardBand projection",
            "synthetic_locator": "synthetic page values may differ from archive; source/block IDs and digest linkage still exact; not source evidence"
        },
        "hsk01_consumption_contract": [
            "Mandatory schema plus HS00 semantic validator using trusted pinned contract digest; schema alone is insufficient.",
            "Consume source_record_id, provider identity status, raw PDF/text/block digests and preservation_scope as immutable source provenance.",
            "Do not infer official standard identity from source alias, filename, graph namespace or release label; UNKNOWN/HOLD must propagate.",
            "Preserve every raw level label and punctuation before producing any normalized member-level candidate.",
            "Use source_record_id for source provenance and separate normalized_knowledge_id for Lexeme/HanCharacter/Topic/Competency objects.",
            "Use explicit record_kind; never infer character versus vocabulary from surface length or glyph shape.",
            "Use source_block_id, scope_topic_ref, printed page label and raw text digest; keep PDF page index and one-based PDF page number separate and unknown unless directly mapped.",
            "Unknown fields and parser failures remain preserved/queryable; no silent correction, deduplication or overwrite.",
            "Rights HOLD, publication NOT_AUTHORIZED, historical PDF identity HOLD and visual layout HOLD propagate to all downstream records and outputs."
        ],
        "non_goals": [
            "No HSK01 bulk conversion of 11,000 lexical records, 4,288 character memberships, 3,088 characters, 94 SourceBlocks, 9 capabilities or 823 taxonomy categories.",
            "No source-level professional content correction, H07 final standard mapping, CQ/LC, semantic qualification or learning-effect claim.",
            "No SQLite file, public release, rights promotion, SRC01 scope expansion, Task DAG update, qualification receipt, PR or merge."
        ],
        "preservation_scope": RIGHTS_SCOPE,
        "candidate_package_binding": {
            "package_id": PACKAGE_ID,
            "version": PACKAGE_VERSION,
            "status": "SYNTACTIC_REF_EXAMPLE_ONLY_NO_PACKAGE_MANIFEST"
        }
    }
    dump(HERE / "interface-contract.json", contract)
    print(json.dumps({
        "status": "HS00_CONTRACT_ARTIFACTS_BUILT",
        "schema_sha256": schema_sha,
        "fixtures_sha256": fixtures_sha,
        "db01_projection_sha256": db01_sha,
        "source_mapping_sha256": mapping_sha,
        "positive_cases": len(fixtures["positive_cases"]),
        "negative_cases": len(fixtures["negative_cases"]),
        "db01_records": len(db01["records"]),
        "synthetic_db01_records": len(db01["synthetic_records"]),
        "qualification": "NOT_GRANTED"
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
