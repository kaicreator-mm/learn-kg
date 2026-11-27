import json
import unittest
from pathlib import Path

from tools.knowledge_import.model_spec import (
    ModelParameterError,
    load_domain_contract,
    validate_model_parameters,
)

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = load_domain_contract(
    ROOT / "knowledge/v0.1.0/trace-adaptation-resources-r1/model-domain-constraints.json"
)


def model(model_id, parameters):
    return {"stable_id": model_id, "parameters": parameters}


class ModelSpecDomainGuardTests(unittest.TestCase):
    def test_brier_requires_binary_integer_labels(self):
        m = model("K10.BRIER.TWO", [
            {"name": "p0", "lower": 0, "upper": 1},
            {"name": "p1", "lower": 0, "upper": 1},
            {"name": "y0", "lower": 0, "upper": 1},
            {"name": "y1", "lower": 0, "upper": 1},
        ])
        valid = {"p0": 0.5, "p1": 0.75, "y0": 0, "y1": 1}
        self.assertEqual(set(validate_model_parameters(m, valid, CONTRACT)), set(valid))
        for bad in (0.5, True, "1"):
            with self.subTest(bad=bad):
                with self.assertRaises(ModelParameterError):
                    validate_model_parameters(m, {**valid, "y0": bad}, CONTRACT)

    def test_half_life_is_strictly_positive(self):
        m = model("K10.HLR.FIXED", [
            {"name": "lag", "lower": 0, "upper": None},
            {"name": "half_life", "lower": 0, "upper": None},
        ])
        self.assertEqual(validate_model_parameters(m, {"lag": 0, "half_life": 1}, CONTRACT)["half_life"], 1)
        for bad in (0, -1, True):
            with self.subTest(bad=bad):
                with self.assertRaises(ModelParameterError):
                    validate_model_parameters(m, {"lag": 0, "half_life": bad}, CONTRACT)

    def test_rectangle_sides_are_strictly_positive(self):
        m = model("K12.RECT.AREA", [
            {"name": "a", "lower": 0, "upper": None},
            {"name": "b", "lower": 0, "upper": None},
        ])
        self.assertEqual(validate_model_parameters(m, {"a": 1, "b": 2}, CONTRACT)["a"], 1)
        with self.assertRaises(ModelParameterError):
            validate_model_parameters(m, {"a": 0, "b": 2}, CONTRACT)

    def test_unknown_or_missing_parameters_fail_closed(self):
        m = model("K10.HLR.FIXED", [{"name": "half_life", "lower": 0, "upper": None}])
        with self.assertRaises(ModelParameterError):
            validate_model_parameters(m, {"half_life": 1, "extra": 2}, CONTRACT)
        with self.assertRaises(ModelParameterError):
            validate_model_parameters(m, {}, CONTRACT)


if __name__ == "__main__":
    unittest.main()
