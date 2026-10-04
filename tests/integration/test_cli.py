import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from mreg import evaluate
from mreg.cli import main
from mreg.evidence.normalize import read_json
from mreg.evidence.validate import InputError
from mreg.models.evidence import Evidence
from mreg.models.policy import Policy
from mreg.policy.loader import read_policy
from mreg.reporting.json_report import replay, write_json, write_review
from mreg.reporting.markdown_report import render


def test_check_replay_and_determinism(tmp_path: Path, evidence: Evidence, policy: Policy) -> None:
    ep, pp = tmp_path / "evidence.json", tmp_path / "policy.yaml"
    write_json(ep, evidence.model_dump(mode="json"))
    pp.write_text(yaml.safe_dump(policy.model_dump()), encoding="utf-8")
    output = tmp_path / "review"
    assert main(["check", "--evidence", str(ep), "--policy", str(pp), "--output", str(output)]) == 0
    result_bytes = (output / "result.json").read_bytes()
    md_bytes = (output / "review.md").read_bytes()
    second = tmp_path / "replay"
    assert main(["replay", "--bundle", str(output / "bundle.json"), "--output", str(second)]) == 0
    assert result_bytes == (second / "result.json").read_bytes()
    assert md_bytes == (second / "review.md").read_bytes()


def test_bundle_tampering(tmp_path: Path, evidence: Evidence, policy: Policy) -> None:
    write_review(tmp_path, evaluate(evidence, policy), evidence, policy)
    bundle = read_json(tmp_path / "bundle.json")
    bundle["evidence"]["candidate"]["metrics"]["f1"]["value"] = 0.5
    with pytest.raises(InputError, match="INVALID_BUNDLE"):
        replay(bundle)


def test_bundle_semantics_and_result(tmp_path: Path, evidence: Evidence, policy: Policy) -> None:
    write_review(tmp_path, evaluate(evidence, policy), evidence, policy)
    bundle = read_json(tmp_path / "bundle.json")
    bundle["semantics_version"] = "different"
    with pytest.raises(InputError, match="UNSUPPORTED_SEMANTICS_VERSION"):
        replay(bundle)
    bundle["semantics_version"] = "1.0"
    bundle["result"]["verdict"] = "FAIL"
    with pytest.raises(InputError, match="REPLAY_RESULT_MISMATCH"):
        replay(bundle)


def test_error_overwrites_stale_bundle(tmp_path: Path, evidence: Evidence, policy: Policy) -> None:
    output = tmp_path / "review"
    write_review(output, evaluate(evidence, policy), evidence, policy)
    missing = tmp_path / "missing"
    assert (
        main(
            ["check", "--evidence", str(missing), "--policy", str(missing), "--output", str(output)]
        )
        == 3
    )
    assert read_json(output / "bundle.json")["replayable"] is False


def test_safe_yaml_and_duplicate_json(tmp_path: Path) -> None:
    for text in [
        "a: 1\na: 2",
        "a: &a [1]\nb: *a",
        "!!python/object/apply:os.system ['echo unsafe']",
    ]:
        path = tmp_path / "bad.yaml"
        path.write_text(text)
        with pytest.raises((ValueError, yaml.YAMLError)):
            read_policy(path)
    path = tmp_path / "bad.json"
    path.write_text('{"a":1,"a":2}')
    with pytest.raises(ValueError, match="duplicate"):
        read_json(path)


def test_report_escaping(evidence: Evidence, policy: Policy) -> None:
    evidence.candidate.model.model_id = "<script>alert(1)</script>|[click](https://bad)\n# forged"
    md = render(evaluate(evidence, policy))
    assert "<script>" not in md
    assert "\\[click\\]" in md
    assert "\n# forged" not in md


def test_real_examples_subprocess(root: Path, tmp_path: Path) -> None:
    env = os.environ | {"PYTHONPATH": str(root / "src")}
    generated = tmp_path / "evidence"
    subprocess.run(
        [
            sys.executable,
            str(root / "examples/binary_classification/scripts/generate.py"),
            "--output",
            str(generated),
        ],
        env=env,
        check=True,
    )
    policy = root / "examples/binary_classification/policies/release-policy.yaml"
    results = {}
    for scenario, exit_code in [("pass", 0), ("fail", 1), ("insufficient", 2), ("error", 3)]:
        output = tmp_path / scenario
        process = subprocess.run(
            [
                sys.executable,
                "-m",
                "mreg",
                "check",
                "--evidence",
                str(generated / f"{scenario}.json"),
                "--policy",
                str(policy),
                "--output",
                str(output),
            ],
            env=env,
            capture_output=True,
            text=True,
        )
        assert process.returncode == exit_code, process.stdout + process.stderr
        results[scenario] = read_json(output / "result.json")
        if scenario != "error":
            process = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "mreg",
                    "replay",
                    "--bundle",
                    str(output / "bundle.json"),
                    "--output",
                    str(tmp_path / f"replay-{scenario}"),
                ],
                env=env,
                capture_output=True,
                text=True,
            )
            assert process.returncode == exit_code
    assert "LATENCY_CEILING_EXCEEDED" in results["fail"]["reason_codes"]
    assert "SLICE_SUPPORT_TOO_LOW" in results["insufficient"]["reason_codes"]
    fail_input = read_json(generated / "fail.json")
    assert (
        fail_input["candidate"]["metrics"]["f1"]["value"]
        > fail_input["baseline"]["metrics"]["f1"]["value"]
    )


def test_parser_error_is_three() -> None:
    with pytest.raises(SystemExit) as error:
        main(["check"])
    assert error.value.code == 3
