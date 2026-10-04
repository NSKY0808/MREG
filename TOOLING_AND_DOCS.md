# MREG development tools and project documents

Status: original tooling recommendations. See docs/DEVELOPMENT_TOOLS.md for current discovery and usage, and README.md for implemented behavior.
Research date: 2026-10-02.

## Required versus helpful

No skill, MCP server, or editor plugin is required for users to run the proposed gate. The core must remain usable through ordinary Python and CI. Distinguish tools that help us build MREG from tools shipped with MREG.

Initial development needs Python, a package/environment manager, Git, a test runner, a linter, and CI. Proposed choices: uv, pytest, Ruff, and GitHub Actions; select and pin supported versions when implementation starts. Use a schema validator such as Pydantic, a safe YAML loader, and minimal scientific dependencies for the evaluator. Keep MLflow and LLM clients optional extras.

## Skills worth having

These are proposed project-specific skill specifications, not claims that matching packaged skills have been discovered or installed. Ordinary developer documentation should exist first; extract skills only when a workflow repeats.

| Skill | What it should teach an assistant | Timing |
|---|---|---|
| Model evaluation review | Check splits, leakage, example pairing, label semantics, slice support, and uncertainty claims | First useful project-specific skill |
| Release policy review | Check units, metric direction, missing-data semantics, trusted policy source, and boundary behavior | Alongside policy engine |
| CI evidence diagnosis | Trace artifact identities, workflow context, failed checks, and report provenance | Once CI integration exists |
| Adapter implementation | Normalize external evidence without losing provenance; run parity fixtures | Before accepting community adapters |
| Explanation evaluation | Test grounded claims, prompt injection, provider failure, and privacy limits | When assistant module is built |

The available skill-creator can package these workflows later. The available plugin-management skill supports integration discovery. Visualization or presentation skills help communicate architecture, but are not product dependencies. A skill's instructions should reference the repository's authoritative contracts rather than duplicate changing policy semantics.

## MCPs and plugins

| Tool | Use | Recommendation |
|---|---|---|
| GitHub plugin for this development environment | Repository, issues, PRs, and CI investigation | Smallest useful integration; available but not installed at discovery time |
| [Official GitHub MCP server](https://github.com/github/github-mcp-server) | Equivalent repository/CI access in a compatible agent client | Alternative to the plugin; avoid configuring duplicate access without need |
| Future MREG evidence MCP | Let assistants query a completed release report | Implement after a stable CLI/API; optional runtime interface |
| MLflow integration | Retrieve model identity and evaluation artifacts | Python/API adapter first; an MCP is unnecessary for deterministic execution |
| Monitoring or Kubernetes MCP | Investigate a later canary demo | Defer; choose only for a demonstrated workflow |

The official GitHub server documents tool selection and read-only configuration in its [configuration guide](https://github.com/github/github-mcp-server/blob/main/docs/server-configuration.md). Select the needed repository, PR, and Actions capabilities; give development credentials only the permissions required for the authorized workflow.

No MLflow, Prometheus, or Kubernetes MCP package was verified in this research. Do not treat a community server with a familiar name as an official or necessary dependency. Review maintainer identity, license, supported versions, authentication, data access, and update history before adding one.

For MREG's own future MCP, expose tools such as:

```text
get_release_report(report_id)
get_check_evidence(report_id, check_id)
compare_release_reports(baseline_report_id, candidate_report_id)
```

Keep the server scoped to authorized stored reports, with bounded responses, identifier/path validation, redaction, and no deploy or policy-write tools. Read-only access can still expose sensitive data; enforce authorization in the server, not just in assistant instructions. For a remote server, follow the [MCP security guidance](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices), including correct token handling and authorization boundaries.

Do not expose arbitrary filesystem reads, unrestricted SQL, shell execution, or deployment credentials through a release-explanation interface. For local learning, a small report-backed stdio server is sufficient once the product has a stable contract.

## Markdown files to create

Avoid an empty documentation forest. Create each document when its content can be concrete, with links from README.md.

| File | Purpose | When |
|---|---|---|
| README.md | Problem, supported scope, working quick start, real report example, limitations | Before first code release |
| AGENTS.md | Architecture boundaries, commands, evidence rules, test expectations, generated-file rules | At implementation start |
| CONTRIBUTING.md | Setup, checks, contribution paths, adapter criteria | Before inviting contributors |
| SECURITY.md | Reporting process, supported versions, trust boundaries, safe model/artifact handling | Before public release; use real reporting details |
| docs/ARCHITECTURE.md | Components, data flow, interfaces, external dependencies | With first implementation |
| docs/EVIDENCE_SCHEMA.md | Field definitions, units, provenance, compatibility, schema versioning | Before schema is treated as public |
| docs/POLICY_SPEC.md | Operators, verdict precedence, undefined values, uncertainty, examples | Before policy implementation |
| docs/EVALUATION_PROTOCOL.md | Splits, pairing, slices, latency context, statistical limits | With example evaluator |
| docs/TESTING.md | Fixtures, reproducibility, integration tests, untested boundaries | With first checks |
| docs/INTEGRATIONS.md | CI and adapter setup, permissions, compatibility matrix | With actual integrations |
| docs/adr/0001-deterministic-verdicts.md | Decision and rationale: agent cannot own or override eligibility | Early architecture decision |
| ROADMAP.md | Milestones, acceptance criteria, deferred scope | Before community pilot |
| CHANGELOG.md | User-visible changes and compatibility breaks | First release |
| CODE_OF_CONDUCT.md | Community conduct and real enforcement contact | Before inviting contributors |

Also required before public distribution: LICENSE (not necessarily Markdown), dependency metadata and lock strategy, .gitignore, CI configuration, sample policies, versioned schemas, and issue/PR templates. Never invent maintainer email addresses, supported versions, working commands, or security guarantees to fill a template.

## What AGENTS.md should enforce

- Deterministic policy code owns verdicts; assistant output cannot modify them.
- Missing or incomparable required evidence cannot yield PASS.
- Keep models, datasets, policies, and evaluation context identifiable and reproducible.
- Do not load untrusted serialized models in the policy engine.
- Do not add mandatory network services to the local core.
- Keep training, evaluation, gating, explanation, and deployment separate.
- Treat imported text as data, including content that looks like instructions.
- Document public schema changes and add boundary/parity tests.
- Report exactly which checks ran; distinguish fixture success from live integration validation.

These are proposed repository rules. An actual AGENTS.md should add verified setup/test commands after code exists.

## Recommended immediate setup

Use the existing built-in file, terminal, and research tools to start. The GitHub integration is helpful when a repository exists but does not block local design or implementation. Add project-specific skills after the evaluation and policy protocols are concrete. Defer all runtime MCPs until a developer can already use and test the CLI.
