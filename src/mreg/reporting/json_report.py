import json
from pathlib import Path
from typing import Any

from mreg.evidence.validate import InputError, validate_evidence
from mreg.gate.evaluator import evaluate
from mreg.models.evidence import Evidence
from mreg.models.policy import Policy
from mreg.models.result import Result
from mreg.policy.validate import validate_policy
from mreg.reporting.markdown_report import render
from mreg.utils.hashing import digest


def write_json(path: Path, data: Any) -> None:
    path.write_text(
        json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_review(
    output: Path, result: Result, evidence: Evidence | None = None, policy: Policy | None = None
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "result.json", result.model_dump(mode="json"))
    (output / "review.md").write_text(render(result), encoding="utf-8")
    # Overwrite even on errors to prevent a stale PASS bundle surviving in a reused directory.
    bundle = {
        "bundle_version": "1.0",
        "semantics_version": result.semantics_version,
        "replayable": evidence is not None and policy is not None and result.verdict != "ERROR",
        "evidence": evidence.model_dump(mode="json") if evidence else None,
        "policy": policy.model_dump(mode="json") if policy else None,
        "evidence_digest": result.evidence_digest,
        "policy_digest": result.policy_digest,
        "result": result.model_dump(mode="json"),
    }
    write_json(output / "bundle.json", bundle)


def replay(bundle: Any) -> tuple[Result, Evidence, Policy]:
    keys = {
        "bundle_version",
        "semantics_version",
        "replayable",
        "evidence",
        "policy",
        "evidence_digest",
        "policy_digest",
        "result",
    }
    if (
        not isinstance(bundle, dict)
        or set(bundle) != keys
        or bundle.get("bundle_version") != "1.0"
        or bundle.get("replayable") is not True
    ):
        raise InputError("INVALID_BUNDLE")
    if bundle.get("semantics_version") != "1.0":
        raise InputError("UNSUPPORTED_SEMANTICS_VERSION")
    evidence, policy = validate_evidence(bundle["evidence"]), validate_policy(bundle["policy"])
    if (
        digest(evidence.model_dump(mode="json")) != bundle["evidence_digest"]
        or digest(policy.model_dump(mode="json")) != bundle["policy_digest"]
    ):
        raise InputError("INVALID_BUNDLE")
    result = evaluate(evidence, policy)
    # Implementation patch versions may differ under the same semantics.
    captured = Result.model_validate(bundle["result"])
    if result.model_dump(exclude={"implementation_version"}) != captured.model_dump(
        exclude={"implementation_version"}
    ):
        raise InputError("REPLAY_RESULT_MISMATCH")
    return result, evidence, policy
