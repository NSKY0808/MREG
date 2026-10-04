from typing import Literal

from pydantic import Field

from mreg.models.common import Contract

Verdict = Literal["PASS", "FAIL", "INSUFFICIENT_EVIDENCE", "ERROR"]
# These are process status codes, not credentials.
EXIT_CODES = dict([("PASS", 0), ("FAIL", 1), ("INSUFFICIENT_EVIDENCE", 2), ("ERROR", 3)])


class CheckResult(Contract):
    rule_id: str
    required: bool
    state: Verdict
    reason_codes: list[str]
    candidate_value: float | None = None
    baseline_value: float | None = None
    compared_value: float | None = None
    requirement: str
    evidence_references: list[str]
    next_investigation: str


class Result(Contract):
    schema_version: Literal["1.0"] = "1.0"
    implementation_version: str = "0.1.0"
    semantics_version: str = "1.0"
    verdict: Verdict
    candidate_identity: dict[str, str] = Field(default_factory=dict)
    baseline_identity: dict[str, str] = Field(default_factory=dict)
    evidence_id: str | None = None
    evidence_digest: str | None = None
    policy_id: str | None = None
    policy_digest: str | None = None
    checks: list[CheckResult] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)

    @property
    def exit_code(self) -> int:
        return EXIT_CODES[self.verdict]
