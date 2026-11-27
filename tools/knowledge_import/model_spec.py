"""Shared fail-closed parameter-domain guard for canonical ModelSpec consumers."""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Any


class ModelParameterError(ValueError):
    """A ModelSpec input is outside its declared executable domain."""


def load_domain_contract(path: str | Path) -> dict[str, Any]:
    contract = json.loads(Path(path).read_text(encoding="utf-8"))
    if contract.get("schema_version") != "learn-kg-model-domain-guard-1" or contract.get("contract_id") != "LEARN_KG_MODEL_DOMAIN_GUARD_V1":
        raise ModelParameterError("unsupported model-domain contract identity")
    if contract.get("required_before_evaluation") is not True:
        raise ModelParameterError("model-domain guard is not mandatory")
    if not isinstance(contract.get("constraints"), dict):
        raise ModelParameterError("model-domain constraints must be an object")
    for model_id, model_rule in contract["constraints"].items():
        if not isinstance(model_id, str) or not isinstance(model_rule, dict) or not isinstance(model_rule.get("parameters"), dict):
            raise ModelParameterError("model-domain constraint entry is malformed")
        for name, rule in model_rule["parameters"].items():
            if not isinstance(name, str) or not isinstance(rule, dict):
                raise ModelParameterError("model-domain parameter rule is malformed")
            for flag in ("lower_exclusive", "upper_exclusive"):
                if flag in rule and type(rule[flag]) is not bool:
                    raise ModelParameterError(f"{name} {flag} must be boolean")
    return contract


def _numeric(value: Any) -> Fraction:
    # bool is an int subclass in Python; it is never a numeric model parameter.
    if type(value) not in (int, float) and not isinstance(value, Fraction):
        raise ModelParameterError("parameter must be a finite JSON number")
    try:
        result = value if isinstance(value, Fraction) else Fraction(str(value))
    except (ValueError, ZeroDivisionError, OverflowError) as exc:
        raise ModelParameterError("parameter must be a finite number") from exc
    return result


def validate_model_parameters(
    model: dict[str, Any],
    values: dict[str, Any],
    domain_contract: dict[str, Any],
    *,
    model_id: str | None = None,
) -> dict[str, Fraction]:
    """Validate exact parameter identity, numeric types, ModelSpec bounds and stricter guards.

    The domain contract is mandatory even for models without overrides. It supplies
    the shared execution semantics that adapter-specific checks must not duplicate.
    """
    if not isinstance(domain_contract, dict) or domain_contract.get("schema_version") != "learn-kg-model-domain-guard-1":
        raise ModelParameterError("missing or unsupported model-domain guard contract")
    model_id = model_id or model.get("stable_id")
    if not isinstance(model_id, str) or not model_id:
        raise ModelParameterError("ModelSpec stable_id is required")
    params = model.get("parameters")
    if not isinstance(params, list) or not params:
        raise ModelParameterError("ModelSpec parameters are required")
    names = [p.get("name") for p in params]
    if any(not isinstance(n, str) or not n for n in names) or len(set(names)) != len(names):
        raise ModelParameterError("ModelSpec parameter names must be unique")
    if not isinstance(values, dict) or set(values) != set(names):
        raise ModelParameterError("input parameter names must exactly match ModelSpec")

    model_constraints = domain_contract.get("constraints", {}).get(model_id, {})
    if not isinstance(model_constraints, dict):
        raise ModelParameterError("model-domain model entry must be an object")
    overrides = model_constraints.get("parameters", {})
    if not isinstance(overrides, dict):
        raise ModelParameterError("model-domain parameters must be an object")
    if set(overrides) - set(names):
        raise ModelParameterError("domain contract references an unknown ModelSpec parameter")

    normalized: dict[str, Fraction] = {}
    for spec in params:
        name = spec["name"]
        rule = overrides.get(name, {})
        if not isinstance(rule, dict):
            raise ModelParameterError(f"{name} domain rule must be an object")
        value = values[name]
        if rule.get("value_type") == "INTEGER" and type(value) is not int:
            raise ModelParameterError(f"{name} must be an integer")
        if rule.get("value_type") not in (None, "INTEGER", "NUMBER"):
            raise ModelParameterError(f"{name} has an unsupported value_type")
        number = _numeric(value)
        if rule.get("value_type") == "INTEGER" and number.denominator != 1:
            raise ModelParameterError(f"{name} must be an integer")
        allowed = rule.get("allowed_values")
        if allowed is not None:
            if not isinstance(allowed, list) or not allowed:
                raise ModelParameterError(f"{name} allowed_values must be nonempty")
            if number not in {_numeric(x) for x in allowed}:
                raise ModelParameterError(f"{name} is not in its allowed_values")
        lower = spec.get("lower")
        if rule.get("lower_exclusive") is True and lower is None:
            raise ModelParameterError(f"{name} exclusive lower bound is missing")
        if lower is not None:
            bound = _numeric(lower)
            if number <= bound if rule.get("lower_exclusive") is True else number < bound:
                raise ModelParameterError(f"{name} is below its ModelSpec lower bound")
        upper = spec.get("upper")
        if rule.get("upper_exclusive") is True and upper is None:
            raise ModelParameterError(f"{name} exclusive upper bound is missing")
        if upper is not None:
            bound = _numeric(upper)
            if number >= bound if rule.get("upper_exclusive") is True else number > bound:
                raise ModelParameterError(f"{name} is above its ModelSpec upper bound")
        normalized[name] = number
    return normalized
