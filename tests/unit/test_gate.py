import copy

import pytest

from mreg import evaluate
from mreg.evidence.validate import InputError, validate_evidence
from mreg.gate.reason_codes import REASONS
from mreg.models.evidence import Evidence, Interval, Support
from mreg.models.policy import Policy
from mreg.policy.validate import validate_policy
from mreg.utils.hashing import digest


def rule_policy(policy: Policy, **changes: object) -> Policy:
    data = policy.model_dump()
    data["rules"][0].update(changes)
    return Policy.model_validate(data)


@pytest.mark.parametrize("inclusive,expected", [(True, "PASS"), (False, "FAIL")])
def test_boundary(evidence: Evidence, policy: Policy, inclusive: bool, expected: str) -> None:
    result = evaluate(evidence, rule_policy(policy, inclusive=inclusive))
    assert result.verdict == expected


def test_maximum_and_direction(evidence: Evidence, policy: Policy) -> None:
    p = rule_policy(
        policy,
        kind="maximum",
        field="latency",
        direction="lower",
        operator="le",
        threshold=40.0,
        unit="ms",
    )
    assert evaluate(evidence, p).verdict == "PASS"
    assert evaluate(evidence, rule_policy(p, inclusive=False)).reason_codes == [
        "LATENCY_CEILING_EXCEEDED"
    ]
    with pytest.raises(InputError):
        validate_policy(
            rule_policy(policy).model_dump()
            | {"rules": [p.rules[0].model_dump() | {"direction": "higher"}]}
        )


@pytest.mark.parametrize("tolerance,expected", [(1.0, "PASS"), (0.99, "FAIL")])
def test_percentage_points(
    evidence: Evidence, policy: Policy, tolerance: float, expected: str
) -> None:
    evidence.candidate.metrics["f1"].value = 0.89
    p = rule_policy(
        policy, kind="regression", operator="le", threshold=tolerance, unit="percentage_points"
    )
    assert evaluate(evidence, p).verdict == expected


def test_relative_zero(evidence: Evidence, policy: Policy) -> None:
    evidence.baseline.metrics["f1"].value = 0.0
    p = rule_policy(
        policy, kind="regression", operator="le", threshold=1.0, unit="relative_percent"
    )
    result = evaluate(evidence, p)
    assert result.verdict == "INSUFFICIENT_EVIDENCE"
    assert result.reason_codes == ["RELATIVE_BASELINE_ZERO"]


def test_lower_regression(evidence: Evidence, policy: Policy) -> None:
    assert evidence.candidate.benchmark is not None
    evidence.candidate.benchmark.latency.value = 44.0
    p = rule_policy(
        policy,
        kind="regression",
        field="latency",
        direction="lower",
        operator="le",
        threshold=10.0,
        unit="relative_percent",
    )
    assert evaluate(evidence, p).verdict == "PASS"
    assert evaluate(evidence, rule_policy(p, threshold=9.0)).verdict == "FAIL"


@pytest.mark.parametrize(
    "missing,code", [(True, "MISSING_REQUIRED_METRIC"), (False, "UNDEFINED_REQUIRED_METRIC")]
)
def test_missing_and_undefined(
    evidence: Evidence, policy: Policy, missing: bool, code: str
) -> None:
    if missing:
        del evidence.candidate.metrics["f1"]
    else:
        evidence.candidate.metrics["f1"].value = None
    result = evaluate(evidence, policy)
    assert result.verdict == "INSUFFICIENT_EVIDENCE"
    assert code in result.reason_codes


@pytest.mark.parametrize("number", [float("nan"), float("inf"), -float("inf"), "0.9", True])
def test_bad_numbers(evidence: Evidence, number: object) -> None:
    data = evidence.model_dump()
    data["candidate"]["metrics"]["f1"]["value"] = number
    with pytest.raises(InputError) as error:
        validate_evidence(data)
    assert error.value.code == "INVALID_NUMERIC_VALUE"


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("dataset_fingerprint", digest("different"), "DATASET_MISMATCH"),
        ("split", "train", "EVALUATION_SPLIT_MISMATCH"),
        ("examples_fingerprint", digest("different"), "EXAMPLE_PAIRING_MISMATCH"),
        ("positive_class", 0, "POSITIVE_CLASS_MISMATCH"),
        ("prediction_threshold", 0.7, "PREDICTION_THRESHOLD_MISMATCH"),
        ("label_definition", "different", "LABEL_DEFINITION_MISMATCH"),
    ],
)
def test_contexts(evidence: Evidence, policy: Policy, field: str, value: object, code: str) -> None:
    data = evidence.model_dump()
    data["candidate"]["context"][field] = value
    result = evaluate(validate_evidence(data), policy)
    assert result.verdict == "INSUFFICIENT_EVIDENCE"
    assert code in result.reason_codes


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("unit", "percent", "UNIT_MISMATCH"),
        ("averaging", "macro", "METRIC_DEFINITION_MISMATCH"),
        ("definition", "other", "METRIC_DEFINITION_MISMATCH"),
    ],
)
def test_metric_context(
    evidence: Evidence, policy: Policy, field: str, value: str, code: str
) -> None:
    setattr(evidence.candidate.metrics["f1"], field, value)
    assert code in evaluate(evidence, policy).reason_codes


def test_benchmark_context(evidence: Evidence, policy: Policy) -> None:
    assert evidence.candidate.benchmark
    evidence.candidate.benchmark.context.hardware = "gpu"
    p = rule_policy(
        policy,
        kind="maximum",
        field="latency",
        direction="lower",
        operator="le",
        threshold=60.0,
        unit="ms",
    )
    assert evaluate(evidence, p).reason_codes == ["BENCHMARK_CONTEXT_MISMATCH"]


def test_slices_and_support(evidence: Evidence, policy: Policy) -> None:
    p = rule_policy(policy, field="recall", slice="priority", min_samples=30)
    assert evaluate(evidence, p).reason_codes == ["SLICE_SUPPORT_TOO_LOW"]
    del evidence.candidate.slices["priority"]
    assert "REQUIRED_SLICE_MISSING" in evaluate(evidence, p).reason_codes


def test_support_rule(evidence: Evidence, policy: Policy) -> None:
    p = rule_policy(
        policy, field="positive", kind="support", threshold=11.0, unit="count", slice="priority"
    )
    assert evaluate(evidence, p).reason_codes == ["SLICE_SUPPORT_TOO_LOW"]


def test_support_structural_validation(evidence: Evidence) -> None:
    data = evidence.model_dump()
    data["candidate"]["support"]["samples"] = 1
    with pytest.raises(InputError):
        validate_evidence(data)
    with pytest.raises(ValueError):
        Support(samples=4, positive=3, negative=3)


def test_fail_preserves_insufficient(evidence: Evidence, policy: Policy) -> None:
    p = rule_policy(
        policy,
        id="size",
        field="artifact_size",
        kind="maximum",
        direction="lower",
        operator="le",
        threshold=99.0,
        unit="bytes",
    )
    p.rules.append(policy.rules[0])
    evidence.candidate.context.dataset_version = "other"
    result = evaluate(evidence, p)
    assert result.verdict == "FAIL"
    assert set(result.reason_codes) == {"ARTIFACT_SIZE_EXCEEDED", "DATASET_MISMATCH"}


def test_warning_not_blocking(evidence: Evidence, policy: Policy) -> None:
    p = policy.model_copy(deep=True)
    warning = p.rules[0].model_dump() | {"id": "warning", "threshold": 1.0, "required": False}
    data = p.model_dump()
    data["rules"].append(warning)
    result = evaluate(evidence, Policy.model_validate(data))
    assert result.verdict == "PASS"
    assert result.checks[1].state == "FAIL"


@pytest.mark.parametrize(
    "change",
    [
        {"threshold": 2.0},
        {"unit": "ms"},
        {"id": ""},
        {"operator": "le"},
        {"kind": "support"},
        {"inclusive": "true"},
        {"required": False},
    ],
)
def test_invalid_policy(policy: Policy, change: dict[str, object]) -> None:
    data = policy.model_dump()
    data["rules"][0].update(change)
    with pytest.raises(InputError):
        validate_policy(data)


def test_duplicate_rule_ids(policy: Policy) -> None:
    data = policy.model_dump()
    data["rules"].append(copy.deepcopy(data["rules"][0]))
    with pytest.raises(InputError):
        validate_policy(data)


def test_policy_change_identity(evidence: Evidence, policy: Policy) -> None:
    old = evaluate(evidence, policy)
    new = evaluate(evidence, rule_policy(policy, threshold=0.95))
    assert old.verdict == "PASS" and new.verdict == "FAIL"
    assert old.policy_digest != new.policy_digest


@pytest.mark.parametrize(
    "lower,upper,expected",
    [(-0.01, 0.02, "PASS"), (-0.03, -0.02, "FAIL"), (-0.02, 0.02, "INSUFFICIENT_EVIDENCE")],
)
def test_interval(
    evidence: Evidence, policy: Policy, lower: float, upper: float, expected: str
) -> None:
    evidence.intervals = [
        Interval.model_validate(
            {
                "metric": "f1",
                "lower": lower,
                "upper": upper,
                "difference": 0.0,
                "config": {"seed": 42, "resamples": 100, "confidence": 0.95},
                "examples_fingerprint": evidence.candidate.context.examples_fingerprint,
                "baseline_artifact_digest": evidence.baseline.model.artifact_digest,
                "candidate_artifact_digest": evidence.candidate.model.artifact_digest,
            }
        )
    ]
    p = rule_policy(policy, kind="interval", operator="le", threshold=1.0, unit="percentage_points")
    assert evaluate(evidence, p).verdict == expected
    evidence.intervals[0].candidate_artifact_digest = digest("other")
    assert evaluate(evidence, p).reason_codes == ["INTERVAL_CONTEXT_MISMATCH"]


def test_registry_minimum_codes() -> None:
    required = {
        "F1_MINIMUM_NOT_MET",
        "F1_REGRESSION_EXCEEDED",
        "RECALL_MINIMUM_NOT_MET",
        "SLICE_RECALL_REGRESSION",
        "SLICE_SUPPORT_TOO_LOW",
        "REQUIRED_SLICE_MISSING",
        "LATENCY_CEILING_EXCEEDED",
        "ARTIFACT_SIZE_EXCEEDED",
        "DATASET_MISMATCH",
        "EVALUATION_SPLIT_MISMATCH",
        "EXAMPLE_PAIRING_MISMATCH",
        "POSITIVE_CLASS_MISMATCH",
        "PREDICTION_THRESHOLD_MISMATCH",
        "METRIC_DEFINITION_MISMATCH",
        "BENCHMARK_CONTEXT_MISMATCH",
        "UNIT_MISMATCH",
        "MISSING_REQUIRED_METRIC",
        "INVALID_NUMERIC_VALUE",
        "UNDEFINED_REQUIRED_METRIC",
        "UNSUPPORTED_SCHEMA_VERSION",
        "INVALID_POLICY",
        "EXECUTION_ERROR",
    }
    assert required <= REASONS.keys()
