import pytest

from mreg import evaluate
from mreg.evidence.validate import InputError, validate_evidence
from mreg.models.evidence import Evidence, Support
from mreg.models.policy import Policy


def test_boolean_class_rejected(evidence: Evidence) -> None:
    data = evidence.model_dump()
    data["candidate"]["context"]["positive_class"] = True
    with pytest.raises(InputError):
        validate_evidence(data)


def test_positive_support_required_for_recall(evidence: Evidence, policy: Policy) -> None:
    for run in [evidence.candidate, evidence.baseline]:
        run.slices = {}
        run.support = Support(samples=100, positive=0, negative=100)
    data = policy.model_dump()
    data["rules"][0]["field"] = "recall"
    result = evaluate(evidence, Policy.model_validate(data))
    assert result.verdict == "INSUFFICIENT_EVIDENCE"
    assert "UNDEFINED_REQUIRED_METRIC" in result.reason_codes


def test_slice_regression_reason(evidence: Evidence, policy: Policy) -> None:
    evidence.candidate.slices["priority"].metrics["recall"].value = 0.89
    data = policy.model_dump()
    data["rules"][0].update(
        kind="regression",
        field="recall",
        slice="priority",
        operator="le",
        threshold=0.5,
        unit="percentage_points",
    )
    result = evaluate(evidence, Policy.model_validate(data))
    assert result.verdict == "FAIL"
    assert result.reason_codes == ["SLICE_RECALL_REGRESSION"]
