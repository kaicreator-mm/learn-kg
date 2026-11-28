#!/usr/bin/env python3
"""Finite HS00 schema, source-binding, parsing and preservation tests."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from build_hs00 import parse_level_label, RIGHTS_SCOPE
from hs00_semantic import HS00Validator, digest
from jsonschema.exceptions import ValidationError


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(schema: dict, value: dict) -> list:
    return list(Draft202012Validator(schema).iter_errors(value))


def page_locator_valid(value: dict) -> bool:
    index = value.get("pdf_page_index_zero_based")
    page_number = value.get("pdf_page_number_one_based")
    printed = value.get("printed_page_label_recorded_raw")
    printed_numeric = value.get("printed_page_numeric_value")
    if index is not None and (type(index) is not int or index < 0):
        return False
    if page_number is not None and (type(page_number) is not int or page_number < 1):
        return False
    if index is not None and page_number is not None and page_number != index + 1:
        return False
    if printed is None and printed_numeric is not None:
        return False
    if printed is not None and not isinstance(printed, str):
        return False
    return True


def source_ids_unique(ids: list[str]) -> bool:
    return len(ids) == len(set(ids))


def source_block_binding_valid(source_record_ids: list[str], block_source_ref: str) -> bool:
    return block_source_ref in set(source_record_ids)


class HS00Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load(HERE / "schema.json")
        cls.mapping = load(HERE / "source-mapping.json")
        cls.fixtures = load(HERE / "fixtures.json")
        cls.contract = load(HERE / "interface-contract.json")
        cls.db01 = load(HERE / "db01-projections.json")
        cls.db01_schema = load(ROOT / "docs/implementation/db01/canonical.schema.json")
        cls.semantic = HS00Validator.from_pinned_files(HERE, sha(HERE / "interface-contract.json"))

    def validate_def(self, name: str, value: dict) -> list:
        wrapper = {"$schema": self.schema["$schema"], "$defs": self.schema["$defs"], "$ref": f"#/$defs/{name}"}
        return validate(wrapper, value)

    def test_01_source_mapping_matches_hs00_json_schema(self):
        errors = validate(self.schema, self.mapping)
        self.assertEqual([], errors, [f"{list(e.absolute_path)}: {e.message}" for e in errors])

    def test_02_exact_source_record_and_sourceblock_counts(self):
        self.assertEqual(len(self.mapping["source_records"]), 3)
        self.assertEqual(len(self.mapping["source_blocks"]), 94)
        self.assertEqual(len(self.mapping["level_bands"]), 11)
        self.assertEqual(len(self.mapping["level_label_observations"]), 28)
        self.assertEqual(sum(x["occurrence_count"] for x in self.mapping["level_label_observations"] if "（" in x["raw_level_label"]), 102)
        self.assertEqual(self.mapping["level_label_summary"]["lexical_record_count"], 11000)
        self.assertEqual(self.mapping["source_block_summary"]["count"], 94)
        self.assertEqual(self.mapping["source_block_summary"]["block_kind_counts"], {"Grammar": 21, "Task": 53, "Topic": 20})
        self.assertEqual(self.mapping["source_block_summary"]["recorded_printed_page_values"]["contiguous_ranges"], [[2, 54], [56, 75], [383, 403]])
        by_source = {x["source_id"]: x for x in self.mapping["source_records"]}
        self.assertEqual(set(by_source), {"RHSK01", "RHSK02", "RHSK03"})
        self.assertEqual(by_source["RHSK01"]["source_block_count"], 94)
        self.assertEqual(by_source["RHSK02"]["source_block_count"], 0)
        self.assertEqual(by_source["RHSK03"]["source_block_count"], 0)
        self.assertTrue(all(x["source_record_id"] == "urn:learn-kg:source:RHSK01" for x in self.mapping["source_blocks"]))

    def test_03_source_provider_identity_is_explicit_without_leaking_private_ids(self):
        for source in self.mapping["source_records"]:
            provider = source["provider_identity"]
            self.assertEqual(provider["provider"], "GOOGLE_DRIVE")
            self.assertIsNone(provider["provider_file_id"])
            self.assertEqual(provider["provider_file_id_status"], "NOT_STORED_IN_PUBLIC_REPOSITORY")
            self.assertTrue(provider["original_name"].endswith(".pdf"))
            self.assertIsNone(provider["original_path"])
            self.assertEqual(provider["original_path_status"], "NOT_STORED_IN_PUBLIC_REPOSITORY")
            self.assertEqual(provider["current_revision_count"], 1)
            self.assertFalse(provider["previous_revision_available"])
            self.assertIsNone(provider["current_revision_id"])
            self.assertEqual(provider["revision_identity_status"], "ONE_CURRENT_REVISION_ONLY_ID_NOT_CAPTURED")

    def test_04_current_pdf_historical_pdf_connector_text_and_sourceblock_digests_are_separate(self):
        for source in self.mapping["source_records"]:
            self.assertRegex(source["current_raw_pdf"]["sha256"], r"^[a-f0-9]{64}$")
            self.assertIsNone(source["historical_raw_pdf_sha256"])
            self.assertEqual(source["historical_raw_pdf_status"], "HOLD_NO_HISTORICAL_DIGEST_OR_PRIOR_REVISION")
            self.assertRegex(source["canonical_connector_text_sha256"], r"^[a-f0-9]{64}$")
            self.assertNotEqual(source["current_raw_pdf"]["sha256"], source["canonical_connector_text_sha256"])
        archive = self.mapping["archive_evidence"]
        self.assertRegex(archive["source_block_jsonl_sha256"], r"^[a-f0-9]{64}$")
        self.assertNotEqual(archive["source_block_jsonl_sha256"], self.mapping["source_records"][0]["current_raw_pdf"]["sha256"])
        self.assertEqual(archive["sourceblock_replay"]["historical_block_count"], 94)
        self.assertEqual(archive["sourceblock_replay"]["replayed_block_count"], 94)
        self.assertEqual(archive["sourceblock_replay"]["exact_metadata_and_raw_text_matches"], 94)
        self.assertEqual(archive["sourceblock_replay"]["mismatches"], 0)
        self.assertTrue(archive["canonical_connector_text_current_historical_match"])

    def test_05_all_src01_restricted_holds_propagate(self):
        self.assertEqual(self.mapping["preservation_scope"], RIGHTS_SCOPE)
        for source in self.mapping["source_records"]:
            self.assertEqual(source["rights_scope"], RIGHTS_SCOPE)
        for block in self.mapping["source_blocks"]:
            self.assertEqual(block["rights_scope"], RIGHTS_SCOPE)
            self.assertEqual(block["source_block_status"], "LAYOUT_REVIEW_PENDING")
        for band in self.mapping["level_bands"]:
            self.assertEqual(band["rights_scope"], RIGHTS_SCOPE)
        for label in self.mapping["level_label_observations"]:
            self.assertEqual(label["rights_scope"], RIGHTS_SCOPE)
        for case in self.fixtures["positive_cases"] + self.fixtures["negative_cases"]:
            self.assertEqual(case["preservation_scope"], RIGHTS_SCOPE)
        self.assertEqual(self.contract["preservation_scope"], RIGHTS_SCOPE)
        self.assertEqual(self.contract["standard_identity"]["identity_status"], "UNKNOWN_HOLD")
        self.assertEqual(self.contract["standard_identity"]["H07_final_standard_mapping"], "NOT_RUN")

    def test_06_cross_fault_archive_and_pdf_restore_evidence_is_exact(self):
        archive = self.mapping["archive_evidence"]
        self.assertEqual(archive["cross_fault_archive"]["portable_file_count"], 17)
        self.assertEqual(archive["cross_fault_archive"]["cross_fault_portable_archive"], "ALL_LISTED_FILES_BYTE_IDENTICAL")
        self.assertEqual(archive["cross_fault_archive"]["portable_total_bytes"], 45610208)
        self.assertTrue(archive["current_pdf_cross_fault_sha256_matches"])
        self.assertEqual(archive["current_pdf_isolated_v100_restore"]["files"], 3)
        self.assertEqual(archive["current_pdf_isolated_v100_restore"]["exact"], 3)
        self.assertEqual(archive["rdf_readable_export_isolated_v100_restore"]["files"], 17)
        self.assertEqual(archive["rdf_readable_export_isolated_v100_restore"]["exact"], 17)

    def test_07_level_label_parser_preserves_observed_punctuation_and_expands_ranges(self):
        positive = {x["case_id"]: x for x in self.fixtures["positive_cases"] if x["case_type"] == "LEVEL_LABEL"}
        for case in positive.values():
            status, members = parse_level_label(case["input"]["raw_level_label"])
            self.assertEqual(status, case["expected"]["parse_status"])
            self.assertEqual(members, case["expected"]["normalized_member_levels"])
            self.assertEqual(case["input"]["raw_level_label"], case["expected"]["raw_preserved_exactly"])
        expected = {
            "4（5）": [4, 5],
            "2（3）（5）": [2, 3, 5],
            "3（4）（7-9）": [3, 4, 7, 8, 9],
            "7-9": [7, 8, 9],
            "1-2": [1, 2]
        }
        for raw, members in expected.items():
            self.assertEqual(parse_level_label(raw), ("PARSED_CANDIDATE", members))

    def test_08_every_observed_level_label_parses_without_rewriting(self):
        labels = self.mapping["level_label_observations"]
        for item in labels:
            status, members = parse_level_label(item["raw_level_label"])
            self.assertEqual(status, item["parse_status"], item["raw_level_label"])
            self.assertEqual(members, item["normalized_member_levels"], item["raw_level_label"])
            self.assertEqual(item["merged_level_identity"] is not None, members is not None)
        self.assertTrue(any(x["raw_level_label"] == "1（2）（4）" for x in labels))
        self.assertTrue(any(x["raw_level_label"] == "3（4）（7-9）" for x in labels))

    def test_09_page_index_number_and_printed_label_are_distinct(self):
        case = next(x for x in self.fixtures["positive_cases"] if x["case_id"] == "HS00-P06")
        locator = case["input"]
        self.assertTrue(page_locator_valid(locator))
        self.assertEqual([], self.validate_def("HSKSourceLocator", locator))
        self.assertEqual(locator["pdf_page_number_one_based"], locator["pdf_page_index_zero_based"] + 1)
        self.assertEqual(locator["printed_page_label_recorded_raw"], "383")
        self.assertNotEqual(locator["printed_page_label_recorded_raw"], str(locator["pdf_page_index_zero_based"]))
        actual = self.mapping["source_blocks"]
        self.assertTrue(all(x["pdf_page_index_zero_based"] is None for x in actual))
        self.assertTrue(all(x["pdf_page_number_one_based"] is None for x in actual))
        self.assertTrue(all(x["pdf_page_locator_status"] == "UNKNOWN_NOT_DERIVED_FROM_PRINTED_LABEL" for x in actual))

    def test_10_missing_printed_page_is_not_fabricated(self):
        case = next(x for x in self.fixtures["positive_cases"] if x["case_id"] == "HS00-P07")
        self.assertTrue(page_locator_valid(case["input"]))
        self.assertEqual([], self.validate_def("HSKSourceLocator", case["input"]))
        negative = next(x for x in self.fixtures["negative_cases"] if x["case_id"] == "HS00-N07")
        self.assertFalse(page_locator_valid(negative["input"]))

    def test_11_source_block_raw_text_is_digest_only_and_topic_locator_is_preserved(self):
        self.assertEqual(len(self.mapping["source_blocks"]), 94)
        for block in self.mapping["source_blocks"]:
            self.assertNotIn("rawText", block)
            self.assertNotIn("raw_text", block)
            self.assertEqual(block["raw_text_storage"], "PRIVATE_ARCHIVE_ONLY_NOT_COPIED")
            self.assertRegex(block["raw_text_sha256"], r"^[a-f0-9]{64}$")
            self.assertIn(block["scope_topic_ref"], {
                "urn:learn-kg:taxonomy:H07.03.01",
                "urn:learn-kg:taxonomy:H07.03.02",
                "urn:learn-kg:taxonomy:H07.03.05"
            })
        counts = {}
        for block in self.mapping["source_blocks"]:
            counts[block["block_kind_raw"]] = counts.get(block["block_kind_raw"], 0) + 1
        self.assertEqual(counts, {"Grammar": 21, "Task": 53, "Topic": 20})

    def test_12_record_kind_is_explicit_and_not_inferred_from_surface_shape(self):
        examples = [x for x in self.fixtures["positive_cases"] if x["case_type"] == "TYPED_RECORD"]
        self.assertEqual(len(examples), 2)
        kinds = set()
        for case in examples:
            record = case["input"]
            kinds.add(record["record_kind"])
            wrapper = {"$schema": self.schema["$schema"], "$defs": self.schema["$defs"], "$ref": "#/$defs/HSKTypedRecord"}
            errors = validate(wrapper, record)
            self.assertEqual([], errors)
            self.assertEqual(record["raw_surface"], "一")
            self.assertNotEqual(record["source_record_id"], record["normalized_knowledge_id"])
        self.assertEqual(kinds, {"VOCABULARY_ITEM", "CHARACTER_ITEM"})

    def test_13_raw_and_normalized_fields_are_separate_and_parser_is_required(self):
        case = next(x for x in self.fixtures["positive_cases"] if x["case_type"] == "RAW_FIELD")
        field = case["input"]
        self.assertEqual([], validate(self.schema["$defs"]["HSKRawFieldCapture"], field))
        self.assertEqual(field["normalized_value"], None)
        self.assertEqual(field["parse_status"], "NOT_ATTEMPTED")
        self.assertEqual(field["raw_value"], "vendor_field: Ω")
        typed_case = next(x for x in self.fixtures["positive_cases"] if x["case_type"] == "TYPED_RECORD")
        queryable = {x["field_name"]: x for x in typed_case["input"]["raw_fields"]}
        self.assertIn("vendor_extension", queryable)
        self.assertEqual(queryable["vendor_extension"]["raw_value"], "vendor_field: Ω")
        missing_parser = next(x for x in self.fixtures["negative_cases"] if x["case_id"] == "HS00-N08")
        self.assertTrue(validate(self.schema["$defs"]["HSKRawFieldCapture"], missing_parser["input"]))

    def test_14_unknown_malformed_or_whitespace_level_labels_hold_without_silent_repair(self):
        for case in self.fixtures["negative_cases"]:
            if case["case_type"] == "LEVEL_LABEL":
                status, members = parse_level_label(case["input"]["raw_level_label"])
                self.assertEqual(status, "HOLD_UNPARSED")
                self.assertIsNone(members)
                self.assertEqual(case["input"]["raw_level_label"], case["expected"]["raw_preserved_exactly"])
        malformed = next(x for x in self.fixtures["negative_cases"] if x["case_id"] == "HS00-N09")
        status, members = parse_level_label(malformed["input"]["raw_level_label"])
        self.assertNotEqual((status, members), (malformed["input"]["parse_status"], malformed["input"]["normalized_member_levels"]))

    def test_15_source_id_mismatch_and_duplicate_source_ids_are_rejected(self):
        mismatch = next(x for x in self.fixtures["negative_cases"] if x["case_type"] == "SOURCE_ID_MISMATCH")["input"]
        self.assertNotEqual(mismatch["source_record_id"], mismatch["source_block_source_ref"])
        known_ids = [x["source_record_id"] for x in self.mapping["source_records"]]
        self.assertIn(mismatch["source_block_source_ref"], known_ids)
        self.assertIn(mismatch["source_record_id"], known_ids)
        full = copy.deepcopy(self.fixtures["positive_cases"][5]["input"])
        full["source_record_id"] = mismatch["source_record_id"]
        with self.assertRaises(ValueError):
            self.semantic.validate(full, "HSKSourceLocator")
        self.assertTrue(source_block_binding_valid(known_ids, "urn:learn-kg:source:RHSK01"))
        duplicate = next(x for x in self.fixtures["negative_cases"] if x["case_type"] == "DUPLICATE_SOURCE_ID")["input"]
        self.assertFalse(source_ids_unique(duplicate["source_record_ids"]))
        ids = [x["source_record_id"] for x in self.mapping["source_records"]]
        self.assertTrue(source_ids_unique(ids))

    def test_16_source_record_ids_are_not_normalized_knowledge_ids(self):
        for example in self.mapping["record_kind_examples"]:
            if example["source_record_id"] is not None:
                self.assertNotEqual(example["source_record_id"], example["normalized_knowledge_id"])
        self.assertEqual({x["record_kind"] for x in self.mapping["record_kind_examples"]}, {
            "VOCABULARY_ITEM", "CHARACTER_ITEM", "SOURCE_BLOCK", "CAPABILITY", "CATEGORY", "CHARACTER_MEMBERSHIP"
        })

    def test_17_db01_projections_and_if01_typed_refs_are_schema_compatible(self):
        db_validator = Draft202012Validator(self.db01_schema)
        records = self.db01["records"] + self.db01["synthetic_records"]
        self.assertEqual(len(self.db01["records"]), 109)
        self.assertEqual(len(self.db01["synthetic_records"]), 1)
        for record in records:
            errors = list(db_validator.iter_errors(record))
            self.assertEqual([], errors, [(record["kind"], list(e.absolute_path), e.message) for e in errors])
        ref_validator = Draft202012Validator(self.db01_schema["$defs"]["ref"])
        for item in self.db01["if01_typed_reference_examples"]:
            self.assertEqual([], list(ref_validator.iter_errors(item)))
        self.assertEqual(self.db01["package_binding_status"], "NOT_REGISTERED_NO_PACKAGE_MANIFEST")
        self.assertEqual(self.db01["synthetic_records"][0]["mapping_status"], "HOLD")

    def test_18_fixture_and_contract_hashes_bind_exact_inputs(self):
        self.assertEqual(self.contract["schema"]["sha256"], sha(HERE / "schema.json"))
        self.assertEqual(self.contract["source_mapping"]["sha256"], sha(HERE / "source-mapping.json"))
        self.assertEqual(self.contract["fixtures"]["sha256"], sha(HERE / "fixtures.json"))
        self.assertEqual(self.contract["db01_projection"]["sha256"], sha(HERE / "db01-projections.json"))
        self.assertEqual(self.contract["inputs"]["DB01_schema_sha256"], sha(ROOT / "docs/implementation/db01/canonical.schema.json"))
        self.assertEqual(self.contract["inputs"]["IF01_interface_contract_sha256"], sha(ROOT / "docs/implementation/if01/interface-contract.json"))
        self.assertEqual(self.contract["inputs"]["SRC01_receipt_sha256"], sha(ROOT / "evidence/tasks/SRC01/SRC01-FORMAL-02.json"))

    def test_19_all_examples_keep_preservation_scope_and_rights_hold(self):
        self.assertEqual(self.fixtures["preservation_scope"], RIGHTS_SCOPE)
        for case in self.fixtures["positive_cases"] + self.fixtures["negative_cases"]:
            self.assertEqual(case["preservation_scope"], RIGHTS_SCOPE)
        source = next(x for x in self.fixtures["positive_cases"] if x["case_type"] == "SOURCE_RECORD")["input"]
        self.assertIsNone(source["historical_raw_pdf_sha256"])
        self.assertEqual(source["rights_scope"], RIGHTS_SCOPE)
        standard = self.mapping["standard_identity"]
        self.assertEqual(standard["identity_status"], "UNKNOWN_HOLD")
        self.assertEqual([], self.validate_def("HSKStandardIdentity", standard))
        promoted = dict(standard)
        promoted["identity_status"] = "VERIFIED"
        self.assertTrue(self.validate_def("HSKStandardIdentity", promoted))

    def test_20_no_sqlite_private_paths_drive_ids_or_download_links_are_generated(self):
        for path in HERE.rglob("*"):
            if path.is_file():
                self.assertFalse(path.name.endswith((".sqlite", ".sqlite3", ".db")))
        mapping_text = (HERE / "source-mapping.json").read_text(encoding="utf-8")
        self.assertNotIn("drive.google.com", mapping_text)
        self.assertNotIn("private_directory_location", mapping_text)
        for source in self.mapping["source_records"]:
            self.assertIsNone(source["provider_identity"]["provider_file_id"])
            self.assertIsNone(source["provider_identity"]["original_path"])

    def test_21_hsk01_scope_is_not_started_and_no_qualification_is_claimed(self):
        self.assertEqual(self.mapping["status"], "CANDIDATE_PREPARATION_ONLY")
        self.assertIn("HSK01 bulk conversion", " ".join(self.mapping["limits"]))
        self.assertEqual(self.contract["status"], "CANDIDATE_PREPARATION_ONLY")
        self.assertIn("No HSK01 bulk conversion", " ".join(self.contract["non_goals"]))
        self.assertEqual(self.contract["candidate_package_binding"]["status"], "SYNTACTIC_REF_EXAMPLE_ONLY_NO_PACKAGE_MANIFEST")


    def test_22_validation_results_bind_exact_artifact_hashes_and_scope(self):
        result = load(HERE / "validation-results.json")
        self.assertEqual(result["validation"]["finite_tests"], {"passed": 31, "total": 31, "status": "PASS"})
        self.assertEqual(result["validation"]["deterministic_replay"], {"artifacts": 5, "identical_sha256": 5, "status": "PASS"})
        for name, record in result["artifacts"].items():
            self.assertEqual(record["sha256"], sha(HERE / name), name)
        self.assertEqual(result["qualification"], "NOT_GRANTED")
        self.assertFalse(result["safety_boundaries"]["sqlite_file_generated"])
        self.assertFalse(result["safety_boundaries"]["task_dag_completion_registered"])
        self.assertEqual(result["independent_delta_review"], "PENDING")

    def positive(self, case_id):
        return copy.deepcopy(next(x["input"] for x in self.fixtures["positive_cases"] if x["case_id"] == case_id))

    def rejects(self, value, kind):
        with self.assertRaises((ValueError, ValidationError)):
            self.semantic.validate(value, kind)

    def test_23_all_original_fixtures_through_supported_boundary(self):
        kinds = {"PAGE_LOCATOR": "HSKSourceLocator", "RAW_FIELD": "HSKRawFieldCapture",
                 "TYPED_RECORD": "HSKTypedRecord", "SOURCE_RECORD": "HSKSourceRecord"}
        for c in self.fixtures["positive_cases"]:
            v = c["input"]
            if c["case_type"] == "LEVEL_LABEL":
                row = copy.deepcopy(self.mapping["level_label_observations"][0])
                row.update(evidence_origin="UNBOUND_CAPTURE", occurrence_count=None, source_record_refs=[], raw_level_label=v["raw_level_label"], raw_field_sha256=digest(v["raw_level_label"]),
                           parse_status=c["expected"]["parse_status"], normalized_member_levels=c["expected"]["normalized_member_levels"])
                from build_hs00 import merged_identity
                row["merged_level_identity"] = merged_identity(row["raw_level_label"])
                self.assertTrue(self.semantic.validate(row, "HSKLevelLabelObservation"))
            else:
                self.assertTrue(self.semantic.validate(v, kinds[c["case_type"]]))
        for c in self.fixtures["negative_cases"]:
            with self.subTest(case=c["case_id"]):
                v = c["input"]
                t = c["case_type"]
                if t in ("LEVEL_LABEL", "LEVEL_FIELD_SILENT_NORMALIZATION"):
                    row = copy.deepcopy(self.mapping["level_label_observations"][0])
                    row.update(evidence_origin="UNBOUND_CAPTURE", occurrence_count=None, source_record_refs=[], raw_level_label=v["raw_level_label"], raw_field_sha256=digest(v["raw_level_label"]),
                               parse_status="HOLD_UNPARSED", normalized_member_levels=None, merged_level_identity=None)
                    if t == "LEVEL_LABEL":
                        self.assertTrue(self.semantic.validate(row, "HSKLevelLabelObservation"))
                        self.assertEqual(row["raw_level_label"], c["expected"]["raw_preserved_exactly"])
                    else:
                        row.update(parse_status=v["parse_status"], normalized_member_levels=v["normalized_member_levels"], merged_level_identity="FORGED")
                        self.rejects(row, "HSKLevelLabelObservation")
                elif t == "DUPLICATE_SOURCE_ID":
                    mapping = copy.deepcopy(self.mapping)
                    mapping["source_records"][1] = copy.deepcopy(mapping["source_records"][0])
                    with self.assertRaises(ValueError):
                        HS00Validator(self.schema, mapping)
                elif t == "SOURCE_ID_MISMATCH":
                    self.rejects({**self.positive("HS00-P06"), "source_record_id": v["source_record_id"]}, "HSKSourceLocator")
                elif t == "PAGE_LOCATOR":
                    self.rejects({**self.positive("HS00-P06"), **v}, "HSKSourceLocator")
                elif t == "SOURCE_KNOWLEDGE_ID":
                    self.rejects({**self.positive("HS00-P08"), **v}, "HSKTypedRecord")
                elif t == "STANDARD_IDENTITY":
                    self.rejects({**self.mapping["standard_identity"], **v}, "HSKStandardIdentity")
                elif t == "RIGHTS_SCOPE":
                    self.rejects({**self.positive("HS00-P08"), "rights_scope": v}, "HSKTypedRecord")
                else:
                    self.rejects(v, kinds[t])

    def test_24_full_record_locator_and_source_identity_mutations(self):
        original = self.positive("HS00-P06")
        for delta in ({"pdf_page_number_one_based":14},
                      {"printed_page_label_recorded_raw":None},
                      {"printed_page_numeric_value":384},
                      {"source_record_id":"urn:learn-kg:source:RHSK02"},
                      {"source_text_sha256":"0"*64},
                      {"source_block_jsonl_sha256":"0"*64},
                      {"raw_text_sha256":"0"*64},
                      {"scope_topic_ref":"WRONG"},
                      {"pdf_page_index_zero_based":406,"pdf_page_number_one_based":407},
                      {"locator_origin":"SOURCE_BLOCK_RDF","printed_page_status":"RECORDED_NOT_VISUALLY_VERIFIED"}):
            self.rejects({**original, **delta}, "HSKSourceLocator")
        typed = self.positive("HS00-P08")
        self.rejects({**typed,"normalized_knowledge_id":typed["source_record_id"]}, "HSKTypedRecord")
        self.rejects({**typed,"source_record_id":"urn:learn-kg:source:RHSK02"}, "HSKTypedRecord")

    def test_25_full_raw_capture_status_and_digest_mutations(self):
        raw = self.positive("HS00-P10")
        for change in ({"normalized_value":"invented"},{"raw_value":"changed"},
                       {"raw_field_sha256":"0"*64},{"source_locator_ref":"unknown"},
                       {"raw_value_status":"MISSING"},{"parse_status":"ERROR","normalized_value":123}):
            self.rejects({**raw,**change}, "HSKRawFieldCapture")
        for value in ("", " ", None, {"x":[1,True,None]}, ["a",2]):
            row = {**raw,"raw_value":value,"raw_field_sha256":digest(value),"parse_status":"HOLD"}
            self.assertTrue(self.semantic.validate(row,"HSKRawFieldCapture"))
        self.rejects({**raw,"raw_value":None,"raw_field_sha256":digest(None),"raw_value_status":"MISSING",
                      "parse_status":"PARSED_CANDIDATE"}, "HSKRawFieldCapture")

    def test_26_unresolved_labels_lossless_full_records_and_digest_binding(self):
        for raw in ("", " ", "9（10）", "4(5)", "3（4"):
            observation = copy.deepcopy(self.mapping["level_label_observations"][0])
            observation.update(evidence_origin="UNBOUND_CAPTURE",occurrence_count=None,source_record_refs=[],raw_level_label=raw,raw_field_sha256=digest(raw),parse_status="HOLD_UNPARSED",
                               normalized_member_levels=None,merged_level_identity=None)
            self.assertTrue(self.semantic.validate(observation,"HSKLevelLabelObservation"))
            self.rejects({**observation,"normalized_member_levels":[9],"merged_level_identity":"FORGED"},"HSKLevelLabelObservation")
            self.rejects({**observation,"raw_field_sha256":"0"*64},"HSKLevelLabelObservation")
            band = copy.deepcopy(self.mapping["level_bands"][0])
            band["raw_label_term"]["value"]=raw
            band.update(evidence_origin="UNBOUND_CAPTURE",source_band_id=None,source_record_line_sha256=None,stable_id="HS00.UNBOUND.BAND."+digest(band["raw_label_term"])[:24],raw_level_label=raw,raw_field_sha256=digest(band["raw_label_term"]),
                        parse_status="HOLD_UNPARSED",normalized_member_levels=None,merged_level_identity=None)
            self.assertTrue(self.semantic.validate(band,"HSKLevelBand"))
            self.rejects({**band,"raw_level_label":raw+"x"},"HSKLevelBand")
            self.rejects({**band,"merged_level_identity":"FORGED"},"HSKLevelBand")
        band = copy.deepcopy(self.mapping["level_bands"][0])
        self.rejects({**band,"source_standard_id":"OTHER"},"HSKLevelBand")

    def test_27_standalone_examples_preserve_all_holds_and_pins(self):
        for row in self.mapping["record_kind_examples"]:
            self.assertEqual(row["rights_scope"], RIGHTS_SCOPE)
        mapping=copy.deepcopy(self.mapping)
        del mapping["record_kind_examples"][0]["rights_scope"]
        with self.assertRaises(ValidationError):
            HS00Validator(self.schema,mapping)
        with self.assertRaises(ValueError):
            HS00Validator.from_pinned_files(HERE,"0"*64)
        self.assertEqual(self.contract["semantic_validation"]["validator_sha256"],sha(HERE/"hs00_semantic.py"))

    def test_28_actual_source_locator_requires_exact_archive_values(self):
        block = self.mapping["source_blocks"][0]
        source = next(s for s in self.mapping["source_records"] if s["source_record_id"]==block["source_record_id"])
        loc = self.positive("HS00-P06")
        loc.update(locator_origin="SOURCE_BLOCK_RDF",printed_page_status="RECORDED_NOT_VISUALLY_VERIFIED",
                   pdf_page_index_zero_based=None,pdf_page_number_one_based=None,
                   printed_page_label_recorded_raw=block["printed_page_label_recorded_raw"],
                   printed_page_numeric_value=int(block["printed_page_label_recorded_raw"]))
        self.assertTrue(self.semantic.validate(loc,"HSKSourceLocator"))
        self.rejects({**loc,"pdf_page_index_zero_based":0,"pdf_page_number_one_based":1},"HSKSourceLocator")
        self.rejects({**loc,"printed_page_label_recorded_raw":"999","printed_page_numeric_value":999},"HSKSourceLocator")
        self.rejects({**source,"canonical_connector_text_sha256":"0"*64},"HSKSourceRecord")
        self.rejects({**block,"source_record_id":"urn:learn-kg:source:RHSK02"},"HSKSourceBlockMapping")

    def test_29_pinned_level_evidence_cannot_be_substituted_with_recomputed_hashes(self):
        from build_hs00 import merged_identity
        b=copy.deepcopy(self.mapping["level_bands"][0])
        b["raw_label_term"]["value"]="8"
        b.update(raw_level_label="8",normalized_member_levels=[8],merged_level_identity=merged_identity("8"),
                 raw_field_sha256=digest(b["raw_label_term"]))
        self.rejects(b,"HSKLevelBand")
        self.rejects({**b,"evidence_origin":"UNBOUND_CAPTURE"},"HSKLevelBand")
        o=copy.deepcopy(self.mapping["level_label_observations"][0])
        self.rejects({**o,"occurrence_count":o["occurrence_count"]+100000,
                      "source_record_refs":["urn:learn-kg:source:RHSK03"]},"HSKLevelLabelObservation")
        self.rejects({**o,"evidence_origin":"UNBOUND_CAPTURE"},"HSKLevelLabelObservation")
        for b in self.mapping["level_bands"]:
            self.assertTrue(self.semantic.validate(b,"HSKLevelBand"))
        for o in self.mapping["level_label_observations"]:
            self.assertTrue(self.semantic.validate(o,"HSKLevelLabelObservation"))

    def test_30_public_accessors_are_defensive_copies(self):
        v=HS00Validator.from_pinned_files(HERE,sha(HERE/"interface-contract.json"))
        original=v.mapping["source_records"][0]
        for r in (v.mapping["source_records"][0],v.sources[original["source_record_id"]]):
            r["canonical_connector_text_sha256"]="0"*64
            with self.assertRaises(ValueError):
                v.validate(r,"HSKSourceRecord")
        self.assertTrue(v.validate(original,"HSKSourceRecord"))
        b=v.mapping["level_bands"][0]
        altered=v.bands[b["source_band_id"]]
        altered["source_record_line_sha256"]="0"*64
        with self.assertRaises(ValueError):v.validate(altered,"HSKLevelBand")
        schema=v.schema
        schema["$defs"]["HSKSourceRecord"]={}
        with self.assertRaises((ValueError,ValidationError)):
            v.validate({"kind":"HSKSourceRecord","source_record_id":original["source_record_id"]},"HSKSourceRecord")
        self.assertTrue(v.validate(b,"HSKLevelBand"))

    def test_31_unresolved_first_and_all_bands_have_no_dangling_synthetic_refs(self):
        from build_hs00_contract import make_db01_projections
        for all_bands in (False,True):
            mapping=copy.deepcopy(self.mapping)
            for band in mapping["level_bands"] if all_bands else mapping["level_bands"][:1]:
                band.update(parse_status="HOLD_UNPARSED",normalized_member_levels=None,merged_level_identity=None)
            projection=make_db01_projections(mapping)
            ids={(r["kind"],r["stable_id"]) for r in projection["records"]+projection["synthetic_records"]}
            for ref in projection["if01_typed_reference_examples"]:
                self.assertIn((ref["kind"],ref["stable_id"]),ids)
            if all_bands:
                self.assertEqual(projection["synthetic_records"],[])
                self.assertFalse(any(r["kind"]=="StandardBand" for r in projection["records"]))
            else:
                self.assertEqual(len(projection["synthetic_records"]),1)
                self.assertIn(("StandardBand",projection["synthetic_records"][0]["band_ref"]["stable_id"]),ids)
                self.assertNotEqual(projection["synthetic_records"][0]["band_ref"]["stable_id"],mapping["level_bands"][0]["stable_id"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
