from mreg.models.result import CheckResult, Verdict


def aggregate(checks: list[CheckResult]) -> Verdict:
    required = [c.state for c in checks if c.required]
    if "ERROR" in required:
        return "ERROR"
    if "FAIL" in required:
        return "FAIL"
    if "INSUFFICIENT_EVIDENCE" in required:
        return "INSUFFICIENT_EVIDENCE"
    return "PASS"
