from mreg import evaluate
from mreg.models.evidence import Evidence
from mreg.models.policy import Policy


def test_references_resolve(evidence: Evidence, policy: Policy) -> None:
    data = evidence.model_dump(mode="json")
    for check in evaluate(evidence, policy).checks:
        for reference in check.evidence_references:
            value = data
            for key in reference.split("/")[1:]:
                value = value[key.replace("~1", "/").replace("~0", "~")]


def test_slice_pointer_escaping(evidence: Evidence, policy: Policy) -> None:
    name = "priority/~test"
    for run in [evidence.baseline, evidence.candidate]:
        run.slices[name] = run.slices.pop("priority")
    data = policy.model_dump()
    data["rules"][0].update(field="recall", slice=name)
    result = evaluate(evidence, Policy.model_validate(data))
    assert result.verdict == "PASS"
    assert (
        "/candidate/slices/priority~1~0test/metrics/recall" in result.checks[0].evidence_references
    )
