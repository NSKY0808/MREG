# Verification record — 2026-10-03

## Rename verification — 2026-10-04

Renamed the project, package, CLI, imports, CI workflow, metadata/lockfile, and
documentation to MREG. Offline installation replaced the previous package with
`mreg`. All 67 tests, Ruff lint/format, mypy, Bandit, and dependency checks passed.
`mreg --version`, `mreg check`, and `mreg replay` ran successfully; generated example
evidence/reports and distribution archives were rebuilt under the new name.
The local workspace directory was not renamed; the published project and package
use MREG throughout.

## Executed checks

Final environment: Windows, Python 3.12.7, isolated project `.venv`, dependency
versions from uv.lock. System-site-package inheritance is disabled.
Pydantic 2.13.5, NumPy 2.5.3, scikit-learn 1.9.1, pytest 9.1.1.

- `python -m pip install -e ".[evaluation]"`: successful documented install, including build isolation.
- `uv sync --locked --extra evaluation`: resolved/installed the locked environment;
  subsequent offline sync succeeded.
- `python -m pytest -q`: **67 passed**; includes unit/integration tests, actual
  scikit-learn generation, subprocess CLI exits, all valid-verdict replays, and a
  core-only check with optional scientific/registry imports blocked.
- `python -m ruff check .`: passed.
- `python -m ruff format --check .`: 57 Python files already formatted.
- `python -m mypy`: no issues in 30 source files.
- `python -m bandit -r src -q`: passed; no findings or blanket security-rule exclusions.
- `python -m pip check`: no broken requirements in the isolated environment.
- `python scripts/export_schemas.py`: generated evidence, policy, result schemas and
  reason-code docs; schema equality/validation tested.
- `uv build --offline`: source archive and wheel built successfully. Inspection found
  no virtual environment, cache, Git metadata, or verification/private files in the archive.
- `pip-audit` on all 13 resolved runtime/evaluation dependencies: no known advisory
  findings at lookup time. This does not establish vulnerability-free software or audit
  every development/build dependency.

CLI scenarios were also run directly using the installed executable:

| Input | Verdict | Exit | Primary finding | Replay |
|---|---|---|---|---|
| pass.json | PASS | 0 | CHECK_PASSED | Byte-identical result |
| fail.json | FAIL | 1 | LATENCY_CEILING_EXCEEDED | Byte-identical result |
| insufficient.json | INSUFFICIENT_EVIDENCE | 2 | SLICE_SUPPORT_TOO_LOW | Byte-identical result |
| error.json | ERROR | 3 | UNSUPPORTED_SCHEMA_VERSION | Deliberately non-replayable |

The real synthetic example produced baseline F1 approximately 0.508 and candidate
F1 approximately 0.985. Operational latency values are explicitly asserted fixtures,
not a measured inference benchmark. Bootstrap is implemented and tested but experimental.

## CI checks and limits

The workflow YAML was parsed locally; target-SHA checkout, separate evaluation/review
jobs, trusted locked core environment, always-upload behavior, and PASS-only progression
were inspected. No hosted GitHub Actions run was possible because no remote repository
exists. Action references use major-version tags and should be pinned to reviewed SHAs
before production adoption; protect the required workflow independently of candidate PRs.

Python 3.11+ is declared; only Python 3.12 on Windows was executed here. Linux CI,
other Python versions, a real registry adapter, real operational benchmarks, external
developer onboarding, and production attestation remain unverified.

## Implementation decisions and deviations

- MIT license selected for the initial open-source scaffold.
- argparse keeps the two-command CLI dependency footprint small.
- Closely related validation/rule responsibilities are combined in focused modules
  rather than reproducing every suggested empty file.
- Evidence references use JSON Pointers, including escaped slice names.
- Paired bootstrap was implemented, not merely scaffolded; its limitations are documented.
- Adapter protocol/documentation exist; MLflow adapter implementation is deferred.
- Git repository initialized without commits, remote publication, or deployment.
- Initial branch is main. Git metadata created in a Windows sandbox can have
  different ownership from the desktop user. Command-scoped repository trust was
  used during setup; no global trust setting was changed.
- All 20 requested future additions are preserved in FUTURE_SCOPE.md.

The first meaningful next increment is a read-only MLflow evidence adapter with immutable
baseline resolution and parity tests against a real, reproducible binary-evaluation run.
