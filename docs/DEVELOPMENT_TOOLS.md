# Development capabilities and tool strategy

Discovery date: 2026-10-03. No repository source, datasets, artifacts, or private
information was uploaded to an external service. Web queries were generic product/API
research. Package downloads and advisory lookup are dependency operations, not source uploads.

## Initial inventory and actual use

The workspace initially contained DESIGN.md, PROJECT_PROPOSAL.md, and TOOLING_AND_DOCS.md.
There were no sources, tests, manifests, lockfiles, models, CI files, evaluation scripts,
or Git history. Python 3.12.7, Pydantic 2.11.7, PyYAML 6.0.3, pytest 9.0.2, NumPy 2.3.3,
scikit-learn 1.7.2, and Ruff were available locally. rg provided fast file/code lookup.

The system uv launcher failed; a project-local uv installation was obtained for dependency
locking. Docker CLI was present but its daemon was unavailable; Docker was not needed.
The desktop dependency-discovery tool located a bundled runtime, but the ordinary Python
environment already supported implementation. A project venv isolates additional tools;
it initially inherited local site packages to avoid blocking on downloads. That
inheritance was then disabled, locked dependencies synced, and all final checks
rerun in the isolated environment with no broken requirements.

Actually used: filesystem/terminal tools, rg, local Python, pytest, Ruff, mypy, Bandit,
JSON Schema validation, package/build tools, web lookup of official docs, and plugin
search. The plugin-management skill guided discovery. No plugin was connected, no
MCP runtime was added to MREG, and no external repository/CI was accessed.

Plugin searches confirmed GitHub was available but uninstalled. Searches for MLflow
and W&B did not return a confirmed matching installable connector in this environment;
unrelated search results were ignored. Official web documentation independently identified
MLflow and W&B MCP offerings. That does not imply they are connected or used here.

Skill inventory: plugin-management is useful for discovery; skill-creator/installer could
package repeated local workflows later; document/visualization skills support artifacts
but were not needed to implement a Python CLI. No task-specific evaluation/policy skill
was installed. No subagents were used.

## Forward-looking capability assessment

All rows below are optional; none changes the deterministic core's runtime requirements.

| Name | Purpose and benefit | Required permissions | External data exposure | Risk | Adoption stage |
|---|---|---|---|---|---|
| rg / local editor indexing | Find evaluation entry points and CI topology in unfamiliar repos | Local repository read | None | Indexes may contain private text; keep local | Now; rg used |
| GitHub plugin or official GitHub MCP | PR/issue review, CI logs, artifact inspection | Selected repositories; read-only initially, explicit write scope for authorized work | Repository/log data reaches GitHub and the agent context | Broad tokens, private logs, write tools; least privilege | When a remote repo exists |
| Official documentation web lookup | Verify package/API behavior without guessing | Public web read | Generic queries only | Version drift; prefer supported-version docs | Now; used |
| MLflow Python/API adapter | Normalize run metrics and immutable registry identities | Selected tracking/registry read | Depends on local versus hosted tracking server | Missing provenance, aliases, misleading imported metrics | Next adapter milestone |
| MLflow MCP | Trace exploration for later assistant work | Tracking server credentials; restrict exposed tools | Trace text/metadata can be sensitive | Experimental; includes write/delete operations; not a binary registry adapter | Only if trace workflow is needed |
| W&B MCP | Inspect experiment history and evidence sources | Authorized project/account access | Hosted run metadata and possibly artifacts | Verify available tools and restrict access; no default artifact upload | After a W&B adapter is requested |
| Cloud ML registry SDK/connector | Resolve explicit release-target baselines | Read-only scoped cloud role | Cloud model metadata | Credential exposure, mutable aliases; provider not selected/verified | After a concrete deployment target |
| Dataset versioning (local DVC-style workflow) | Reproduce dataset identity and split | Local data/manifest read; storage access only if configured | None by default; remote storage optional | Sensitive labels/features, cache permissions | With first real pilot dataset |
| Evidently reports | Import data/quality tests as evidence | Local report read; hosted credentials optional | Local by default | Metric semantics differ; adapter must retain provenance | Optional evidence-producer adapter |
| pytest / JSON Schema | Boundary/regression and exported-schema validation | Local execution | None | Tests must not execute untrusted repositories with credentials | Now; used |
| Ruff / mypy / Bandit | Formatting, types, static security review | Local source read | None | Static analysis does not prove runtime security | Now; used |
| pip-audit | Dependency advisory lookup | Public advisory/package endpoints | Dependency names and versions | Advisory coverage/network availability; scope scan to project deps | Initial release checks |
| GitHub Actions inspection | Confirm workflow runs and preserved artifacts | Repo Actions/artifacts read | CI logs and artifacts | Logs can contain secrets; redact | Once a remote CI run exists |
| MkDocs or Sphinx | Publish API/schema/example docs | Local build; hosting write only for publishing | None for local build | Plugin supply chain and accidental private docs publication | After docs volume warrants it |
| MREG report-backed MCP | Read completed report/check evidence | Authorized report read only | Local stdio by default; remote depends on host | Read-only still exposes data; enforce IDs/paths/redaction | After API and real users stabilize |

Optional development skills to extract later: evaluation-review (pairing/splits/support),
policy-review (units/boundaries/trust), CI diagnosis (digests/logs), adapter parity, and
grounded explanation testing. Their sources should be the authoritative repository docs.

## Sources and limits

- [Pydantic strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/): avoid implicit coercion.
- [scikit-learn metrics](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_recall_fscore_support.html): undefined metrics and binary conventions.
- [pytest](https://docs.pytest.org/en/stable/getting-started.html), [Ruff](https://docs.astral.sh/ruff/linter/), [uv locking](https://docs.astral.sh/uv/concepts/projects/sync/).
- [GitHub MCP](https://github.com/github/github-mcp-server) and [Actions secure use](https://docs.github.com/en/actions/reference/security/secure-use).
- [MLflow MCP](https://mlflow.org/docs/latest/genai/mcp/): documented experimental trace operations; distinct from evidence adapter.
- [W&B MCP](https://wandb.ai/site/mcp/): official offering; no account connection was attempted.
- [Evidently tests](https://docs.evidentlyai.com/docs/library/tests): optional producer, not verdict authority.

Do not blindly install suggested servers. Check maintainer identity, supported versions,
license, permissions, authentication, data exposure, and read/write tool inventory.
No production CI, registry, container, or security attestation is claimed as tested.
Actual check results and environment limitations are recorded in VERIFICATION.md.
