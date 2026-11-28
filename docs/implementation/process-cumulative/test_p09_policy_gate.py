"""Independent P09 policy/flow gate checks against the real in-memory SQL importer.

The oracle below derives flow completion from the declared raw identity/time and
stage contract. It does not read builder expected_spec or results.json.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOC = Path(__file__).resolve().parent
PKG = ROOT / "knowledge/v0.1.0/learning-process-cumulative-r2"
B = ROOT / "knowledge/v0.1.0"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(DOC))

import build as process_build
from tools.knowledge_import.importer import Importer, ManifestPin
from tools.knowledge_import.v00_prototype import load_record


MAX_UTC_EPOCH_SECONDS = 253402300799
MIN_DELAY_SECONDS = 86400


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def independent_flow_oracle(value):
    """Derive only the P09 finite FlowSpec outcome from raw event data."""
    if not isinstance(value, dict):
        return "HOLD"
    events = value.get("events")
    if not isinstance(events, list) or any(not isinstance(e, dict) for e in events):
        return "HOLD"
    if any(e.get("type") == "STOP" for e in events):
        return "STOP"
    if any(e.get("type") == "PAUSE" for e in events):
        return "PAUSE"
    if (type(value.get("budget")) is not int or value["budget"] < 0
        or not isinstance(value.get("version"), str) or not value["version"]
        or value.get("authorized") is not True
        or value.get("goal_confirmed") is not True):
        return "HOLD"
    if not all(isinstance(value.get(k), str) and value[k]
               for k in ("goal", "scoring_version", "trained_family", "transfer_dimension")):
        return "HOLD"
    if len(events) != 4:
        return "HOLD"
    expected = (
        ("IMMEDIATE", "IMMEDIATE_RECORDED"),
        ("DELAYED", "DELAYED_RECORDED"),
        ("TRANSFER", "TRANSFER_RECORDED"),
        ("SUMMARY", "SUMMARY_RECORDED"),
    )
    ids = set()
    total_cost = 0
    for event, (stage, event_type) in zip(events, expected):
        event_id = event.get("id")
        if (not isinstance(event_id, str) or not event_id.strip()
            or event_id.strip() != event_id or event_id in ids
            or event.get("stage") != stage or event.get("type") != event_type
            or event.get("version") != value["version"]
            or type(event.get("cost")) is not int or event["cost"] < 0):
            return "HOLD"
        ids.add(event_id)
        total_cost += event["cost"]
    if total_cost > value["budget"]:
        return "HOLD"

    observations = events[:3]
    identity = None
    clock = None
    event_times = []
    recording_times = []
    for index, (event, stage) in enumerate(zip(observations, ("IMMEDIATE", "DELAYED", "TRANSFER"))):
        current_identity = event.get("learner_identity")
        if (not isinstance(current_identity, dict)
            or set(current_identity) != {"kind", "subject_id", "identity_version"}
            or current_identity.get("kind") != "LEARNER_SUBJECT"
            or not isinstance(current_identity.get("subject_id"), str)
            or not current_identity["subject_id"]
            or current_identity["subject_id"].strip() != current_identity["subject_id"]
            or len(current_identity["subject_id"]) > 128
            or current_identity.get("identity_version") != "V1"):
            return "HOLD"
        if identity is None:
            identity = copy.deepcopy(current_identity)
        elif current_identity != identity:
            return "HOLD"

        current_clock = (
            event.get("time_basis"), event.get("time_unit"),
            event.get("recording_time_basis"), event.get("recording_time_unit"),
            event.get("clock_source_id"), event.get("recording_clock_source_id"),
        )
        if (current_clock[:4] != (
                "UTC_EPOCH_SECONDS", "SECOND", "UTC_EPOCH_SECONDS", "SECOND")
            or not isinstance(current_clock[4], str) or not current_clock[4]
            or not isinstance(current_clock[5], str) or not current_clock[5]):
            return "HOLD"
        if clock is None:
            clock = current_clock
        elif current_clock != clock:
            return "HOLD"

        observed = event.get("observed_at")
        recorded = event.get("recorded_at")
        if (type(observed) is not int or type(recorded) is not int
            or observed <= 0 or recorded <= 0
            or observed > MAX_UTC_EPOCH_SECONDS
            or recorded > MAX_UTC_EPOCH_SECONDS):
            return "HOLD"
        event_times.append(observed)
        recording_times.append(recorded)

        if (event.get("goal") != value["goal"]
            or event.get("scoring_version") != value["scoring_version"]
            or event.get("independent") is not True
            or event.get("construct_match") is not True
            or event.get("scoring_version_match") is not True
            or not isinstance(event.get("family"), str) or not event["family"]
            or type(event.get("criteria_met")) is not bool):
            return "HOLD"
        if stage in ("IMMEDIATE", "DELAYED"):
            if event["family"] != value["trained_family"]:
                return "HOLD"
        else:
            if (event["family"] == value["trained_family"]
                or event.get("dimension") != value["transfer_dimension"]
                or event.get("new_task_family") is not True
                or event.get("transfer_dimension_declared") is not True):
                return "HOLD"
    if any(b <= a for a, b in zip(event_times, event_times[1:])):
        return "HOLD"
    if any(b < a for a, b in zip(recording_times, recording_times[1:])):
        return "HOLD"
    if event_times[1] - event_times[0] < MIN_DELAY_SECONDS:
        return "HOLD"
    if event_times[2] <= event_times[1]:
        return "HOLD"
    summary = events[3]
    if summary.get("evidence_separated") is not True or summary.get("goal_reviewed") is not True:
        return "HOLD"
    return "COMPLETE"


class P09PolicyGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load(PKG / "learning-process.manifest.json")
        cls.version = cls.manifest["version"]
        catalog = {}
        for manifest_path in sorted(B.glob("*/*manifest.json")):
            if manifest_path.parent == PKG:
                continue
            manifest = load(manifest_path)
            if not {"package_id", "version"} <= manifest.keys():
                continue
            key = (manifest["package_id"], manifest["version"])
            pin = ManifestPin(manifest_path.relative_to(ROOT).as_posix(), sha(manifest_path))
            if key in catalog:
                assert catalog[key].sha256 == pin.sha256
            catalog[key] = pin
        catalog[("learning-process", cls.version)] = ManifestPin(
            (PKG / "learning-process.manifest.json").relative_to(ROOT).as_posix(),
            sha(PKG / "learning-process.manifest.json"),
        )
        extension = B / "foundation-r3" / "relation-types.json"
        cls.importer = Importer(
            mode="research",
            catalog=catalog,
            extension=ManifestPin(extension.relative_to(ROOT).as_posix(), sha(extension)),
        )
        cls.importer.run(("learning-process", cls.version))
        cls.policy_ref = process_build.ref("P09", "PolicySpec", "P09.POLICY", cls.version)
        cls.flow_ref = process_build.ref("P09", "FlowSpec", "P09.FLOW", cls.version)
        cls.policy = load_record(cls.importer, cls.policy_ref)
        cls.flow = load_record(cls.importer, cls.flow_ref)
        fixture = next(
            x for x in load(DOC / "fixtures.json")
            if x["owner"] == "P09" and x["case_id"] == "P09.C001"
        )
        cls.valid = copy.deepcopy(fixture["input"])

    @classmethod
    def tearDownClass(cls):
        cls.importer.close()

    def test_01_policy_has_no_suggest_route_and_remains_advice_only(self):
        actions = {r["action"] for r in self.policy["rules"]}
        self.assertEqual(actions, {"REQUEST_OBSERVATION"})
        self.assertEqual(self.policy["effect"], "ADVICE_ONLY")
        self.assertEqual(self.policy["rules"][0]["condition_ref"]["stable_id"],
                         "P09.GUARD.COMPOSITE_VALID")

    def test_02_valid_exact_flow_completion_allows_only_request_observation(self):
        self.assertEqual(independent_flow_oracle(self.valid), "COMPLETE")
        self.assertEqual(process_build.p09_flow_eval(self.importer, self.flow, self.valid), "COMPLETE")
        self.assertEqual(process_build.p09_policy_eval(self.importer, self.policy_ref, self.valid),
                         "REQUEST_OBSERVATION")

    def test_03_mismatched_learner_identity_and_forged_computed_fields_stay_hold(self):
        altered = copy.deepcopy(self.valid)
        altered["events"][1]["learner_identity"]["subject_id"] = "SUBJECT-OTHER"
        altered.update({
            "computed_same_learner_identity": True,
            "immediate_subject_id": "SUBJECT-01",
            "delayed_subject_id": "SUBJECT-01",
            "transfer_subject_id": "SUBJECT-01",
            "computed_delay_seconds": 86400,
            "minimum_delay_seconds": 86400,
            "computed_timestamp_order_valid": True,
            "computed_recording_order_valid": True,
            "flow_result": {"status": "COMPLETE", "flow_instance_id": "OTHER", "input_sha256": "0" * 64},
        })
        self.assertEqual(independent_flow_oracle(altered), "HOLD")
        self.assertEqual(process_build.p09_flow_eval(self.importer, self.flow, altered), "HOLD")
        self.assertEqual(process_build.p09_policy_eval(self.importer, self.policy_ref, altered), "HOLD")

    def test_04_insufficient_delay_is_not_overridden_by_forged_computed_delay(self):
        altered = copy.deepcopy(self.valid)
        altered["events"][1]["observed_at"] = altered["events"][0]["observed_at"] + 86399
        altered["events"][2]["observed_at"] = altered["events"][1]["observed_at"] + 86400
        altered.update({
            "computed_delay_seconds": 86400,
            "minimum_delay_seconds": 86400,
            "computed_timestamp_order_valid": True,
            "computed_recording_order_valid": True,
        })
        self.assertEqual(independent_flow_oracle(altered), "HOLD")
        self.assertEqual(process_build.p09_policy_eval(self.importer, self.policy_ref, altered), "HOLD")

    def test_05_forged_summary_booleans_do_not_override_identity_hold(self):
        altered = copy.deepcopy(self.valid)
        altered["events"][2]["learner_identity"]["subject_id"] = "SUBJECT-OTHER"
        altered["events"][3]["evidence_separated"] = True
        altered["events"][3]["goal_reviewed"] = True
        altered.update({
            "computed_same_learner_identity": True,
            "computed_delay_seconds": 86400,
            "computed_timestamp_order_valid": True,
            "computed_recording_order_valid": True,
        })
        self.assertEqual(independent_flow_oracle(altered), "HOLD")
        self.assertEqual(process_build.p09_policy_eval(self.importer, self.policy_ref, altered), "HOLD")

    def test_06_missing_or_unknown_flow_completion_cannot_be_replaced_by_external_complete(self):
        altered = copy.deepcopy(self.valid)
        altered["events"] = None
        altered["flow_result"] = {
            "status": "COMPLETE",
            "flow_ref": self.flow_ref,
            "flow_instance_id": "P09:OTHER",
            "input_sha256": "0" * 64,
            "version": self.version,
        }
        self.assertEqual(independent_flow_oracle(altered), "HOLD")
        self.assertEqual(process_build.p09_policy_eval(self.importer, self.policy_ref, altered), "HOLD")

    def test_07_foreign_flow_instance_result_is_ignored_and_never_authorizes_suggest(self):
        altered = copy.deepcopy(self.valid)
        altered["flow_result"] = {
            "status": "COMPLETE",
            "flow_ref": self.flow_ref,
            "flow_instance_id": "ANOTHER-FLOW-INSTANCE",
            "input_sha256": "0" * 64,
            "version": self.version,
        }
        self.assertEqual(process_build.p09_policy_eval(self.importer, self.policy_ref, altered),
                         "REQUEST_OBSERVATION")
        altered["flow_result"]["status"] = "SUGGEST"
        self.assertEqual(process_build.p09_policy_eval(self.importer, self.policy_ref, altered),
                         "REQUEST_OBSERVATION")

    def test_08_foreign_input_digest_result_is_ignored_and_never_authorizes_suggest(self):
        altered = copy.deepcopy(self.valid)
        altered["flow_result"] = {
            "status": "COMPLETE",
            "flow_ref": self.flow_ref,
            "flow_instance_id": "P09:" + process_build.dig(self.valid),
            "input_sha256": "f" * 64,
            "version": self.version,
        }
        self.assertEqual(process_build.p09_policy_eval(self.importer, self.policy_ref, altered),
                         "REQUEST_OBSERVATION")

    def test_09_foreign_flow_version_result_is_ignored_and_never_authorizes_suggest(self):
        altered = copy.deepcopy(self.valid)
        altered["flow_result"] = {
            "status": "COMPLETE",
            "flow_ref": {**self.flow_ref, "version": "0.1.0-process-candidate-1"},
            "flow_instance_id": "P09:" + process_build.dig(self.valid),
            "input_sha256": process_build.dig(self.valid),
            "version": "0.1.0-process-candidate-1",
        }
        self.assertEqual(process_build.p09_policy_eval(self.importer, self.policy_ref, altered),
                         "REQUEST_OBSERVATION")

    def test_10_stop_and_pause_propagate_without_policy_suggestion(self):
        stop = copy.deepcopy(self.valid)
        stop["events"] = [{"type": "STOP"}]
        pause = copy.deepcopy(self.valid)
        pause["events"] = [{"type": "PAUSE"}]
        self.assertEqual(independent_flow_oracle(stop), "STOP")
        self.assertEqual(independent_flow_oracle(pause), "PAUSE")
        self.assertEqual(process_build.p09_policy_eval(self.importer, self.policy_ref, stop), "STOP")
        self.assertEqual(process_build.p09_policy_eval(self.importer, self.policy_ref, pause), "PAUSE")

    def test_11_malformed_flow_and_wrong_policy_tuple_fail_closed(self):
        malformed = copy.deepcopy(self.valid)
        malformed["events"] = [{"type": "UNKNOWN"}]
        self.assertEqual(independent_flow_oracle(malformed), "HOLD")
        self.assertEqual(process_build.p09_policy_eval(self.importer, self.policy_ref, malformed), "HOLD")
        wrong_version = {**self.policy_ref, "version": "0.1.0-process-candidate-1"}
        self.assertEqual(process_build.p09_policy_eval(self.importer, wrong_version, self.valid), "HOLD")
        wrong_owner = {**self.policy_ref, "owner": "P08"}
        self.assertEqual(process_build.p09_policy_eval(self.importer, wrong_owner, self.valid), "HOLD")

    def test_12_direct_policy_eval_cannot_use_caller_booleans_to_suggest(self):
        forged = {
            "exit": False, "declined": False, "paused": False,
            "computed_same_learner_identity": True,
            "computed_delay_seconds": 86400,
            "minimum_delay_seconds": 86400,
            "computed_timestamp_order_valid": True,
            "computed_recording_order_valid": True,
            "evidence_separated": True, "goal_reviewed": True,
            "selected": "ANY",
        }
        self.assertEqual(process_build.policy_eval(self.importer, self.policy, forged), "HOLD")
        malicious_policy = copy.deepcopy(self.policy)
        malicious_policy["rules"].append({
            "condition_ref": self.policy["rules"][0]["condition_ref"],
            "action": "SUGGEST", "reason": "forged route", "priority": 1,
        })
        self.assertEqual(process_build.policy_eval(self.importer, malicious_policy, forged), "HOLD")

    def test_13_non_json_inputs_and_non_plain_dicts_fail_closed(self):
        self.assertEqual(process_build.p09_policy_eval(self.importer, self.policy_ref, {"bad": object()}), "HOLD")
        class DictSubclass(dict):
            pass
        self.assertEqual(process_build.p09_policy_eval(self.importer, self.policy_ref, DictSubclass(self.valid)), "HOLD")
        altered = copy.deepcopy(self.valid)
        altered["events"][0]["bad_number"] = float("nan")
        self.assertEqual(process_build.p09_policy_eval(self.importer, self.policy_ref, altered), "HOLD")

    def test_14_tampered_policy_route_set_fails_closed(self):
        for extra_action in ("SUGGEST", "EXECUTE", "WRITE_STATE"):
            altered_policy = copy.deepcopy(self.policy)
            altered_policy["rules"].append({
                "action": extra_action,
                "condition_ref": self.policy["rules"][0]["condition_ref"],
                "priority": 0,
                "reason": "tampered route",
            })
            with patch.object(process_build, "load_record", side_effect=[altered_policy, self.flow]):
                self.assertEqual(
                    process_build.p09_policy_eval(self.importer, self.policy_ref, self.valid),
                    "HOLD",
                    extra_action,
                )

    def test_15_flow_evaluator_exception_fails_closed(self):
        with patch.object(process_build, "p09_flow_eval", side_effect=RuntimeError("synthetic evaluator failure")):
            self.assertEqual(process_build.p09_policy_eval(self.importer, self.policy_ref, self.valid), "HOLD")

    def test_16_no_state_write_and_input_is_unchanged(self):
        before_policy = process_build.dig(self.policy)
        before_flow = process_build.dig(self.flow)
        original = copy.deepcopy(self.valid)
        result = process_build.p09_policy_eval(self.importer, self.policy_ref, self.valid)
        self.assertEqual(result, "REQUEST_OBSERVATION")
        self.assertEqual(self.valid, original)
        self.assertEqual(process_build.dig(load_record(self.importer, self.policy_ref)), before_policy)
        self.assertEqual(process_build.dig(load_record(self.importer, self.flow_ref)), before_flow)
        for connection in self.importer.connections.values():
            rows = connection.execute("PRAGMA database_list").fetchall()
            self.assertTrue(all(row[2] == "" for row in rows), rows)

    def test_17_generic_entry_rejects_mutable_policy_objects_and_p09_refs(self):
        forged_input = {"exit": False, "declined": False, "paused": False,
                        "selected": "FORGED_POLICY_ROUTE"}
        foreign = process_build.ref("P07", "ConditionSpec", "P07.GUARD.EXIT", self.version)
        for condition in (None, foreign, self.policy["rules"][0]["condition_ref"]):
            policy = copy.deepcopy(self.policy)
            policy["rules"] = [{"action": "SUGGEST", "condition_ref": condition,
                                "priority": 1, "reason": "FORGED_POLICY_ROUTE"}]
            for label in ({}, {"owner": "P07", "kind": "PolicySpec",
                               "stable_id": "P07.POLICY", "version": self.version,
                               "package_id": "learning-process"}):
                with self.subTest(condition=condition, label=label):
                    self.assertEqual(process_build.policy_eval(self.importer, {**policy, **label},
                                                               forged_input), "HOLD")
        for ref in (self.policy_ref, {**self.policy_ref, "owner": "P07"},
                    {**self.policy_ref, "stable_id": "P07.POLICY"},
                    {**self.policy_ref, "kind": "ConditionSpec"}, None):
            with self.subTest(ref=ref):
                self.assertEqual(process_build.policy_eval(self.importer, ref, forged_input), "HOLD")

    def test_18_p07_canonical_tuple_regression_and_untrusted_route_rejection(self):
        ref = process_build.ref("P07", "PolicySpec", "P07.POLICY", self.version)
        canonical = load_record(self.importer, ref)
        # Fixed STOP priority from the declared P07 policy, not a builder expected result.
        self.assertEqual(process_build.policy_eval(self.importer, ref, {"exit": True}), "STOP")
        for bad_ref in ({**ref, "version": "0.1.0-process-candidate-1"},
                        {**ref, "package_id": "foreign"},
                        {**ref, "rules": canonical["rules"]}):
            self.assertEqual(process_build.policy_eval(self.importer, bad_ref, {"exit": True}), "HOLD")
        for bad_condition in (None, self.policy["rules"][0]["condition_ref"]):
            altered = copy.deepcopy(canonical)
            altered["rules"][0]["condition_ref"] = bad_condition
            with patch.object(process_build, "load_record", return_value=altered):
                self.assertEqual(process_build.policy_eval(self.importer, ref, {"exit": True}), "HOLD")
        altered = copy.deepcopy(canonical)
        altered["rules"][0]["action"] = "SUGGEST"
        with patch.object(process_build, "load_record", return_value=altered):
            self.assertEqual(process_build.policy_eval(self.importer, ref, {"exit": True}), "HOLD")



if __name__ == "__main__":
    unittest.main(verbosity=2)
