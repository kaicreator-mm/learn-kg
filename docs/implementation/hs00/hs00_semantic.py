"""Finite HS00 consumption boundary. A pinned contract is not rights or source authority."""
from __future__ import annotations
import copy
import hashlib
import json
import re
from pathlib import Path
from jsonschema import Draft202012Validator
from build_hs00 import RIGHTS_SCOPE, PARSER_NAME, PARSER_VERSION, parse_level_label, merged_identity

def digest(value):
    data = value.encode("utf-8") if isinstance(value, str) else json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()

def require(condition, reason):
    if not condition:
        raise ValueError(reason)

def unique(rows, field):
    values = [r[field] for r in rows]
    require(len(set(values)) == len(values), "DUPLICATE_" + field.upper())
    return {r[field]: r for r in rows}

class HS00Validator:
    @classmethod
    def from_pinned_files(cls, directory, expected_contract_sha256):
        root = Path(directory)
        def read(name, expected):
            data = (root / name).read_bytes()
            require(hashlib.sha256(data).hexdigest() == expected, "PIN_MISMATCH:" + name)
            return json.loads(data)
        contract = read("interface-contract.json", expected_contract_sha256)
        schema = read("schema.json", contract["schema"]["sha256"])
        mapping = read("source-mapping.json", contract["source_mapping"]["sha256"])
        return cls(schema, mapping)

    def __init__(self, schema, mapping):
        self.schema = copy.deepcopy(schema)
        self.mapping = copy.deepcopy(mapping)
        Draft202012Validator(self.schema).validate(self.mapping)
        self.sources = unique(self.mapping["source_records"], "source_record_id")
        unique(self.mapping["source_records"], "source_id")
        unique(self.mapping["source_records"], "stable_id")
        self.blocks = unique(self.mapping["source_blocks"], "source_block_id")
        self.bands = unique(self.mapping["level_bands"], "source_band_id")
        unique(self.mapping["level_bands"], "stable_id")
        unique(self.mapping["level_label_observations"], "raw_level_label")
        for source in self.sources.values():
            require(source["source_record_id"] == "urn:learn-kg:source:" + source["source_id"], "SOURCE_ID_MISMATCH")
            require(source["stable_id"] == "HS00.SOURCE." + source["source_id"], "SOURCE_STABLE_ID_MISMATCH")
            count = sum(b["source_record_id"] == source["source_record_id"] for b in self.blocks.values())
            require(source["source_block_count"] == count and (source["source_block_jsonl_subset_sha256"] is None) == (count == 0), "SOURCE_SUBSET_MISMATCH")
            if count == len(self.blocks):
                require(source["source_block_jsonl_subset_sha256"] == self.mapping["archive_evidence"]["source_block_jsonl_sha256"], "SOURCE_SUBSET_DIGEST_MISMATCH")
        for block in self.blocks.values():
            require(block["source_record_id"] in self.sources and block["level_band_ref"] in self.bands, "BLOCK_REFERENCE_MISMATCH")
        for row in self.mapping["level_bands"] + self.mapping["level_label_observations"]:
            self.validate(row, row["kind"])
        for row in self.mapping["record_kind_examples"]:
            require(row["rights_scope"] == RIGHTS_SCOPE, "RIGHTS_HOLD")
            require(row["source_record_id"] is None or row["source_record_id"] in self.sources, "SOURCE_UNKNOWN")
            require(row["normalized_knowledge_id"] not in self.sources, "SOURCE_KNOWLEDGE_COLLISION")

    def validate(self, record, expected_kind):
        require(type(record) is dict and record.get("kind") == expected_kind, "KIND_MISMATCH")
        require(expected_kind in self.schema["$defs"], "UNKNOWN_KIND")
        wrapper = {"$schema": self.schema["$schema"], "$defs": self.schema["$defs"], "$ref": "#/$defs/" + expected_kind}
        Draft202012Validator(wrapper).validate(record)
        r = record
        if expected_kind in ("HSKSourceRecord", "HSKSourceBlockMapping", "HSKStandardIdentity"):
            if expected_kind == "HSKSourceRecord":
                original = self.sources.get(r["source_record_id"])
            elif expected_kind == "HSKSourceBlockMapping":
                original = self.blocks.get(r["source_block_id"])
            else:
                original = self.mapping["standard_identity"]
            require(r == original, "PINNED_RECORD_MISMATCH")
        elif expected_kind in ("HSKLevelBand", "HSKLevelLabelObservation"):
            raw = r["raw_level_label"]
            status, members = parse_level_label(raw)
            standard = self.mapping["standard_identity"]["source_standard_id"]
            require((r["parser_name"], r["parser_version"]) == (PARSER_NAME, PARSER_VERSION), "PARSER_IDENTITY")
            require(r["parse_status"] == status and r["normalized_member_levels"] == members, "PARSE_CONTRADICTION")
            require(r["merged_level_identity"] == (merged_identity(raw, standard) if members is not None else None), "MERGED_ID_MISMATCH")
            if expected_kind == "HSKLevelBand":
                require(r["source_standard_id"] == standard, "STANDARD_MISMATCH")
                require(r["raw_label_term"]["value"] == raw, "RAW_TERM_MISMATCH")
                require(r["raw_field_sha256"] == digest(r["raw_label_term"]), "RAW_DIGEST_MISMATCH")
            else:
                require(all(ref in self.sources for ref in r["source_record_refs"]), "SOURCE_UNKNOWN")
                require(r["raw_field_sha256"] == digest(raw), "RAW_DIGEST_MISMATCH")
        elif expected_kind == "HSKRawFieldCapture":
            require(r["raw_field_sha256"] == digest(r["raw_value"]), "RAW_DIGEST_MISMATCH")
            require(r["parse_status"] == "PARSED_CANDIDATE" or r["normalized_value"] is None, "PARSE_CONTRADICTION")
            if r["raw_value_status"] in ("PRIVATE_ARCHIVE_ONLY", "MISSING"):
                require(r["raw_value"] is None and r["normalized_value"] is None and r["parse_status"] != "PARSED_CANDIDATE", "MISSING_RAW_PROMOTION")
            require(r["source_locator_ref"] is None or r["source_locator_ref"] in self.blocks, "LOCATOR_UNKNOWN")
        elif expected_kind == "HSKTypedRecord":
            sid = r["source_record_id"]
            require(sid is None or sid in self.sources, "SOURCE_UNKNOWN")
            require(r["normalized_knowledge_id"] not in self.sources, "SOURCE_KNOWLEDGE_COLLISION")
            unique(r["raw_fields"], "field_name")
            for field in r["raw_fields"]:
                self.validate(field, "HSKRawFieldCapture")
            for loc in [r["source_locator_ref"]] + [f["source_locator_ref"] for f in r["raw_fields"]]:
                if loc is not None:
                    require(loc in self.blocks and self.blocks[loc]["source_record_id"] == sid, "SOURCE_RECORD_BLOCK_BINDING_MISMATCH")
        elif expected_kind == "HSKSourceLocator":
            source = self.sources.get(r["source_record_id"])
            block = self.blocks.get(r["source_block_id"])
            require(source is not None and block is not None and block["source_record_id"] == r["source_record_id"], "SOURCE_RECORD_BLOCK_BINDING_MISMATCH")
            require(r["source_text_sha256"] == source["canonical_connector_text_sha256"] and r["source_block_jsonl_sha256"] == self.mapping["archive_evidence"]["source_block_jsonl_sha256"] and r["raw_text_sha256"] == block["raw_text_sha256"], "SOURCE_BLOCK_DIGEST_MISMATCH")
            require(r["scope_topic_ref"] == block["scope_topic_ref"] and r["section_locator_raw"] == block["section_locator_raw"], "SOURCE_BLOCK_SCOPE_MISMATCH")
            i, n = r["pdf_page_index_zero_based"], r["pdf_page_number_one_based"]
            require(i is None or i < source["current_raw_pdf"]["pdf_pages"], "PDF_INDEX_OUT_OF_RANGE")
            require(n is None or n <= source["current_raw_pdf"]["pdf_pages"], "PDF_PAGE_OUT_OF_RANGE")
            require(i is None or n is None or n == i+1, "PDF_INDEX_AND_PAGE_NUMBER_CONFLICT")
            raw, num, datatype = r["printed_page_label_recorded_raw"], r["printed_page_numeric_value"], r["printed_page_source_datatype"]
            if raw is None:
                require(num is None and datatype is None and r["printed_page_status"] == "MISSING_HOLD", "MISSING_PRINTED_LABEL_MUST_NOT_BE_FABRICATED")
            else:
                require(r["printed_page_status"] != "MISSING_HOLD", "PRINTED_STATUS_MISMATCH")
                if datatype == "http://www.w3.org/2001/XMLSchema#integer":
                    require(re.fullmatch(r"[1-9][0-9]*", raw) is not None and num == int(raw), "PRINTED_VALUE_MISMATCH")
                else:
                    require(num is None, "UNSUPPORTED_PRINTED_NUMERIC_VALUE")
            if r["locator_origin"] == "SOURCE_BLOCK_RDF":
                require((i,n) == (block["pdf_page_index_zero_based"], block["pdf_page_number_one_based"]) and raw == block["printed_page_label_recorded_raw"] and datatype == block["printed_page_source_datatype"] and r["printed_page_status"] == "RECORDED_NOT_VISUALLY_VERIFIED", "UNVERIFIED_ACTUAL_LOCATOR")
            else:
                require(r["printed_page_status"] in ("SYNTHETIC_ONLY", "MISSING_HOLD"), "SYNTHETIC_NOT_ACTUAL")
        else:
            raise ValueError("UNSUPPORTED_CONSUMER_RECORD_KIND")
        return True
