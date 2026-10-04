# CI and adapter integration

The `.github/workflows/mreg-example.yml` workflow has separate test, evaluation,
and release-review jobs. Evaluation generates a synthetic candidate evidence artifact.
Release review downloads JSON and checks out the PR target's immutable base SHA.
It installs gate code and loads policy from that trusted checkout, so modifying the
candidate policy or Python gate cannot change this review job's interpretation.
Jobs use the corresponding checkout's dependency lockfile; the trusted review installs
only core dependencies, not evaluation libraries or development tools.

The check step fails on every nonzero exit. The following upload step uses `always()`
to preserve reports when available, including non-pass outcomes. The final eligibility
step runs only after successful checks. It performs no production deployment.
Cancellation, runner failure, install failure, or disk failure may prevent report upload.

The workflow uses `pull_request`, not privileged `pull_request_target`, read-only
contents permissions, and no repository secrets. Candidate evaluation code runs in
an isolated job; its asserted evidence is still untrusted. This workflow is a teaching
integration, not an evidence-authenticity system. First merge the implementation into
the protected target branch: a PR against a base without MREG cannot install its gate.

Before using this for real releases, pin action references to reviewed immutable SHAs,
protect target branch/policy owners,
and enforce the trusted workflow as an organization-required workflow or equivalent
control. A PR-controlled YAML workflow is not itself an immutable security boundary;
changing/removing jobs must not bypass required checks. Bind downstream progression
to candidate/baseline/policy/evidence digests and approved execution context. Do not
trust a PR artifact's PASS claim or mutable model alias.

Intentional policy changes should be separate visible reviews. Use the trusted policy
for eligibility and run the proposed policy only as an informational impact comparison.
The existing CLI supports this by running `check` twice; no policy-diff command exists.

## Adapters

`EvidenceAdapter.collect() -> Evidence` is the small public conversion protocol.
Convert external values into normalized metric units and semantics explicitly;
preserve source identity, immutable artifact versions, configuration, dataset/split,
pairing/labels, and measurement context. Record imported versus externally asserted
origin. Do not fabricate missing measurements or silently coerce incomparable results.

An adapter must return a structurally valid Evidence object; the public evaluate API
revalidates it before use. Equivalent local and adapted normalized evidence must yield
identical digests and verdicts. No MLflow adapter or registry client is shipped yet.
Before implementing one, select supported API versions and add real adapter parity
fixtures and read-only access tests. Registry authentication remains outside the core.

Relevant official references: [GitHub secure use](https://docs.github.com/en/actions/reference/security/secure-use)
and [MLflow evaluation](https://mlflow.org/docs/latest/ml/evaluation/).
