from decimal import Decimal

from mreg.evidence.compatibility import quality_compatibility
from mreg.gate.verdict import aggregate
from mreg.models.evidence import Evidence, Metric, Support
from mreg.models.policy import Policy, Rule
from mreg.models.result import CheckResult, Result
from mreg.policy.rules import regression, satisfies
from mreg.utils.hashing import digest


def violation_code(rule: Rule) -> str:
    if rule.kind == "interval":
        return "INTERVAL_REGRESSION_EXCEEDED"
    if rule.kind == "regression":
        if rule.field == "recall" and rule.slice:
            return "SLICE_RECALL_REGRESSION"
        return "F1_REGRESSION_EXCEEDED" if rule.field == "f1" else "METRIC_REGRESSION_EXCEEDED"
    if rule.field == "latency" and rule.kind == "maximum":
        return "LATENCY_CEILING_EXCEEDED"
    if rule.field == "artifact_size" and rule.kind == "maximum":
        return "ARTIFACT_SIZE_EXCEEDED"
    if rule.kind == "support":
        return "SLICE_SUPPORT_TOO_LOW" if rule.slice else "SAMPLE_SUPPORT_TOO_LOW"
    if rule.kind == "minimum" and rule.field in {"f1", "recall"}:
        return f"{rule.field.upper()}_MINIMUM_NOT_MET"
    return "METRIC_THRESHOLD_NOT_MET"


def _support_ok(support: Support, rule: Rule) -> bool:
    return (
        support.samples >= rule.min_samples
        and support.positive >= rule.min_positive
        and support.negative >= rule.min_negative
    )


def evaluate_rule(evidence: Evidence, rule: Rule) -> CheckResult:
    b, c = evidence.baseline, evidence.candidate
    slice_key = rule.slice.replace("~", "~0").replace("/", "~1") if rule.slice else None
    prefix = f"slices/{slice_key}/" if rule.slice else ""
    value_path = f"support/{rule.field}" if rule.kind == "support" else f"metrics/{rule.field}"
    refs = [f"/candidate/{prefix}{value_path}", f"/baseline/{prefix}{value_path}"]
    requirement = (
        f"{rule.kind}: {rule.field} {rule.operator} {rule.threshold} {rule.unit}; "
        f"{'inclusive' if rule.inclusive else 'exclusive'}; direction={rule.direction}; "
        f"support>={rule.min_samples}/{rule.min_positive}/{rule.min_negative}"
    )
    check = CheckResult(
        rule_id=rule.id,
        required=rule.required,
        state="INSUFFICIENT_EVIDENCE",
        reason_codes=[],
        requirement=requirement,
        evidence_references=refs,
        next_investigation="Collect compatible evidence and rerun this check.",
    )
    issues: list[str] = []
    bm: Metric | None = None
    cm: Metric | None = None
    if rule.field == "artifact_size":
        check.evidence_references = ["/candidate/model/artifact_size_bytes"]
        check.candidate_value = c.model.artifact_size_bytes
    elif rule.field == "latency":
        check.evidence_references = [
            "/candidate/benchmark/latency",
            "/baseline/benchmark/latency",
            "/candidate/benchmark/context",
            "/baseline/benchmark/context",
        ]
        if c.benchmark is None or b.benchmark is None:
            issues.append("MISSING_REQUIRED_METRIC")
        else:
            cm, bm = c.benchmark.latency, b.benchmark.latency
            if c.benchmark.context != b.benchmark.context:
                issues.append("BENCHMARK_CONTEXT_MISMATCH")
    else:
        issues.extend(quality_compatibility(b, c))
        bs, cs = b.support, c.support
        bg, cg = b.metrics, c.metrics
        if rule.slice:
            b_slice, c_slice = b.slices.get(rule.slice), c.slices.get(rule.slice)
            if b_slice is None or c_slice is None:
                issues.append("REQUIRED_SLICE_MISSING")
            else:
                bs, cs = b_slice.support, c_slice.support
                bg, cg = b_slice.metrics, c_slice.metrics
                if b_slice.definition != c_slice.definition:
                    issues.append("SLICE_DEFINITION_MISMATCH")
                if b_slice.examples_fingerprint != c_slice.examples_fingerprint or bs != cs:
                    issues.append("EXAMPLE_PAIRING_MISMATCH")
        if rule.kind == "support":
            check.candidate_value = float(getattr(cs, rule.field))
            check.baseline_value = float(getattr(bs, rule.field))
        else:
            cm, bm = cg.get(rule.field), bg.get(rule.field)
            if rule.field == "recall" and (cs.positive == 0 or bs.positive == 0):
                issues.append("UNDEFINED_REQUIRED_METRIC")
            if not _support_ok(cs, rule) or not _support_ok(bs, rule):
                issues.append("SLICE_SUPPORT_TOO_LOW" if rule.slice else "SAMPLE_SUPPORT_TOO_LOW")
        check.evidence_references.extend(
            [
                "/candidate/context",
                "/baseline/context",
                f"/candidate/{prefix}support",
                f"/baseline/{prefix}support",
            ]
        )
    if rule.field not in {"artifact_size", "samples", "positive", "negative"}:
        if cm is None or bm is None:
            issues.append("MISSING_REQUIRED_METRIC")
        else:
            check.candidate_value, check.baseline_value = cm.value, bm.value
            expected_unit = "ms" if rule.field == "latency" else "score"
            if cm.unit != expected_unit or bm.unit != expected_unit:
                issues.append("UNIT_MISMATCH")
            if cm.definition != bm.definition or cm.averaging != bm.averaging:
                issues.append("METRIC_DEFINITION_MISMATCH")
            if cm.value is None or bm.value is None:
                issues.append("UNDEFINED_REQUIRED_METRIC")
    elif check.candidate_value is None:
        issues.append("MISSING_REQUIRED_METRIC")
    if issues:
        check.reason_codes = list(dict.fromkeys(issues))
        return check
    candidate = check.candidate_value
    baseline = check.baseline_value
    if candidate is None:
        check.reason_codes = ["MISSING_REQUIRED_METRIC"]
        return check
    if rule.kind == "interval":
        interval_index = next(
            (
                i
                for i, item in enumerate(evidence.intervals)
                if item.metric == rule.field and item.slice == rule.slice
            ),
            None,
        )
        if interval_index is None:
            check.reason_codes = ["MISSING_INTERVAL"]
            return check
        interval = evidence.intervals[interval_index]
        check.evidence_references.append(f"/intervals/{interval_index}")
        example_fingerprint = (
            c.slices[rule.slice].examples_fingerprint
            if rule.slice
            else c.context.examples_fingerprint
        )
        if (
            interval.examples_fingerprint != example_fingerprint
            or interval.baseline_artifact_digest != b.model.artifact_digest
            or interval.candidate_artifact_digest != c.model.artifact_digest
            or baseline is None
            or abs(interval.difference - (candidate - baseline)) > 1e-12
        ):
            check.reason_codes = ["INTERVAL_CONTEXT_MISMATCH"]
            return check
        boundary = -Decimal(str(rule.threshold)) / 100
        lower, upper = Decimal(str(interval.lower)), Decimal(str(interval.upper))
        compliant = lower >= boundary if rule.inclusive else lower > boundary
        violating = upper < boundary if rule.inclusive else upper <= boundary
        check.compared_value = interval.lower
        if not compliant and not violating:
            check.reason_codes = ["INTERVAL_INCONCLUSIVE"]
            return check
        passed = compliant
    elif rule.kind == "regression":
        if baseline is None:
            check.reason_codes = ["MISSING_REQUIRED_METRIC"]
            return check
        if rule.unit == "relative_percent" and baseline == 0:
            check.reason_codes = ["RELATIVE_BASELINE_ZERO"]
            return check
        check.compared_value = regression(candidate, baseline, rule)
        passed = satisfies(check.compared_value, rule)
    else:
        check.compared_value = candidate
        passed = satisfies(candidate, rule)
    check.state = "PASS" if passed else "FAIL"
    check.reason_codes = ["CHECK_PASSED" if passed else violation_code(rule)]
    check.next_investigation = (
        "No action required for this check."
        if passed
        else "Investigate this measurement and rerun with the reviewed policy."
    )
    return check


def evaluate(evidence: Evidence, policy: Policy) -> Result:
    """Evaluate validated inputs with no network, model loading, or deployment side effects."""
    # Revalidate to guard against mutable nested contracts and model_construct misuse.
    evidence = Evidence.model_validate(evidence.model_dump(mode="json"))
    policy = Policy.model_validate(policy.model_dump(mode="json"))
    checks = [evaluate_rule(evidence, rule) for rule in policy.rules]
    return Result(
        verdict=aggregate(checks),
        checks=checks,
        candidate_identity={
            "model_id": evidence.candidate.model.model_id,
            "version": evidence.candidate.model.version,
            "artifact_digest": evidence.candidate.model.artifact_digest,
        },
        baseline_identity={
            "model_id": evidence.baseline.model.model_id,
            "version": evidence.baseline.model.version,
            "artifact_digest": evidence.baseline.model.artifact_digest,
        },
        evidence_id=evidence.evidence_id,
        evidence_digest=digest(evidence.model_dump(mode="json")),
        policy_id=policy.policy_id,
        policy_digest=digest(policy.model_dump(mode="json")),
        reason_codes=list(
            dict.fromkeys(
                code for check in checks if check.state != "PASS" for code in check.reason_codes
            )
        ),
    )
