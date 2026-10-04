import json
from pathlib import Path

from jsonschema import Draft202012Validator

from mreg import evaluate
from mreg.models.evidence import Evidence
from mreg.models.policy import Policy
from mreg.models.result import Result


def test_exported_contracts(root: Path, evidence: Evidence, policy: Policy) -> None:
    for name, model, instance in [
        ("evidence", Evidence, evidence),
        ("policy", Policy, policy),
        ("result", Result, evaluate(evidence, policy)),
    ]:
        schema = json.loads((root / f"schemas/{name}.schema.json").read_text())
        expected = model.model_json_schema() | {
            "$schema": "https://json-schema.org/draft/2020-12/schema"
        }
        assert schema == expected
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(instance.model_dump(mode="json"))
