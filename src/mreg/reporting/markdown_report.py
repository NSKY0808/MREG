import html
import re
from typing import Any

from mreg.models.result import Result


def escape(value: Any) -> str:
    text = html.escape(str(value), quote=True)
    text = re.sub(r"([\\`*{}_\[\]()#+.!|>~-])", r"\\\1", text)
    return text.replace("\r", " ").replace("\n", " ")


def render(result: Result) -> str:
    lines = [
        "# MREG release review",
        "",
        f"Verdict: **{result.verdict}**",
        "",
        "PASS means eligible for the next configured step; it does not certify production safety.",
        "",
        f"Candidate: {escape(result.candidate_identity)}",
        f"Baseline: {escape(result.baseline_identity)}",
        f"Policy: {escape(result.policy_id)} / {escape(result.policy_digest)}",
        f"Evidence: {escape(result.evidence_id)} / {escape(result.evidence_digest)}",
        "",
        "| Check | Required | State | Candidate | Baseline | Compared | Requirement "
        "| Reasons | Evidence | Next investigation |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for check in result.checks:
        cells = [
            check.rule_id,
            check.required,
            check.state,
            check.candidate_value,
            check.baseline_value,
            check.compared_value,
            check.requirement,
            ", ".join(check.reason_codes),
            ", ".join(check.evidence_references),
            check.next_investigation,
        ]
        lines.append("| " + " | ".join(escape(c) for c in cells) + " |")
    lines.extend(
        ["", "Reason codes: " + escape(", ".join(result.reason_codes) or "CHECK_PASSED"), ""]
    )
    return "\n".join(lines)
