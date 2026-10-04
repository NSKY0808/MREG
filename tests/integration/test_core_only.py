import os
import subprocess
import sys
from pathlib import Path

from mreg.models.evidence import Evidence
from mreg.models.policy import Policy
from mreg.reporting.json_report import write_json


def test_gate_does_not_import_optional_evaluation_libraries(
    root: Path, tmp_path: Path, evidence: Evidence, policy: Policy
) -> None:
    evidence_path, policy_path = tmp_path / "evidence.json", tmp_path / "policy.yaml"
    write_json(evidence_path, evidence.model_dump(mode="json"))
    # JSON is a subset of safe YAML; this keeps the fixture deterministic.
    write_json(policy_path, policy.model_dump(mode="json"))
    code = """
import importlib.abc
import sys
class BlockOptional(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname.split('.')[0] in {'numpy', 'sklearn', 'mlflow'}:
            raise ImportError('optional package blocked for core-only test')
sys.meta_path.insert(0, BlockOptional())
from mreg.cli import main
raise SystemExit(main(sys.argv[1:]))
"""
    process = subprocess.run(
        [
            sys.executable,
            "-c",
            code,
            "check",
            "--evidence",
            str(evidence_path),
            "--policy",
            str(policy_path),
            "--output",
            str(tmp_path / "review"),
        ],
        env=os.environ | {"PYTHONPATH": str(root / "src")},
        capture_output=True,
        text=True,
    )
    assert process.returncode == 0, process.stderr
    assert "PASS" in process.stdout
