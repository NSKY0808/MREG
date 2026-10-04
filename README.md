# MREG — Model Release Evidence Gate

MREG compares normalized candidate/baseline evidence against a reviewed YAML policy.
It returns a deterministic eligibility decision, a JSON result, and a Markdown review.
PASS means eligible for the next configured review/staging step, not universally safe
for production. The core does not train, deploy, deserialize models, or call an LLM.

## Local quick start

Python 3.11 or newer. From this repository:

```sh
python -m venv .venv
```

Activate with `.venv\Scripts\Activate.ps1` on Windows or `source .venv/bin/activate`
on Linux/macOS, then:

```sh
python -m pip install -e ".[evaluation]"
python examples/binary_classification/scripts/generate.py
mreg check --evidence examples/binary_classification/generated/pass.json --policy examples/binary_classification/policies/release-policy.yaml --output review/pass
mreg replay --bundle review/pass/bundle.json --output replay/pass
```

For expected non-pass examples replace `pass.json` and the output directory with
`fail`, `insufficient`, or `error`. Exit codes are 0 = PASS, 1 = FAIL,
2 = INSUFFICIENT_EVIDENCE, 3 = ERROR. See the [example guide](examples/binary_classification/README.md).

Each review contains `result.json`, `review.md`, and `bundle.json`. Valid decisions
can be replayed locally; an ERROR bundle is explicitly non-replayable.

## Implemented in 0.1.0

- Strict evidence/policy contracts and exported JSON Schemas.
- Aggregate/slice metric floors and ceilings, point-estimate regression, support,
  latency, artifact size, and explicit required versus warning rules.
- Compatibility checks, stable reason codes, digest-bound decision provenance.
- Local CLI/API, deterministic reports, validated replay, paired prediction evaluation.
- Runnable synthetic scikit-learn demo and a CI integration example.

Experimental: paired percentile bootstrap intervals and interval gating. They have
reproducibility tests but no guarantee against test-set reuse or multiple comparisons.

Proposed: MLflow adapter, onboarding/init, assistant/MCP, additional tasks, and canary
integration. They are **not implemented**.

## Python API

```python
from mreg import Evidence, Policy, evaluate

# evidence_data and policy_data are decoded local JSON/YAML mappings.
result = evaluate(Evidence.model_validate(evidence_data), Policy.model_validate(policy_data))
print(result.verdict, result.exit_code)
```

## Development

```sh
uv sync --extra evaluation
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run bandit -r src -q
python scripts/export_schemas.py
```

If uv is unavailable, install the development tools into the activated environment:
`python -m pip install pytest ruff mypy types-PyYAML jsonschema bandit pip-audit`.
Then use `python -m pytest`, `python -m ruff check .`, `python -m ruff format --check .`,
`python -m mypy`, and `python -m bandit -r src -q`.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Evidence contract](docs/EVIDENCE_CONTRACT.md)
- [Policy reference](docs/POLICY_REFERENCE.md)
- [Reason codes](docs/REASON_CODES.md)
- [CI and adapters](docs/INTEGRATIONS.md)
- [Evaluation protocol](docs/EVALUATION_PROTOCOL.md)
- [Development tools](docs/DEVELOPMENT_TOOLS.md)
- [Future scope: all 20 requested additions](docs/FUTURE_SCOPE.md)
- [Contributing](CONTRIBUTING.md) and [security](SECURITY.md)

The earlier PROJECT_PROPOSAL.md and TOOLING_AND_DOCS.md remain planning history.
This README and `docs/` describe the actual implementation.
