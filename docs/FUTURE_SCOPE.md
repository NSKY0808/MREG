# Future scope

Status: roadmap, not implemented features. All 20 requested additions are preserved below.
The MVP already has a binary task field, per-rule validation, explicit fields, a small
adapter protocol, immutable identity checks, and a reason-code registry. Those form
foundations; full profile, onboarding, inheritance, and registry systems remain future work.

## 1. Task profiles / evidence profiles

Define reusable evidence requirements by ML task instead of by estimator implementation.

Start with:

```text
binary_classification
```

Potential later profiles:

```text
multiclass_classification
regression
ranking
forecasting
```

A Random Forest and Logistic Regression solving the same binary-classification problem should normally use the same task profile.

## 2. Explicit release-target configuration

Each independently deployable model should explicitly declare:

- model ID
- task
- candidate
- baseline
- policy
- deployment target
- environment

MREG should not infer the binding silently.

## 3. Multi-model repository support

Support repositories containing several independently deployable models.

Example:

```text
fraud_model → fraud policy
churn_model → churn policy
pricing_model → regression policy
```

## 4. Policy inheritance

Allow:

```text
organization defaults
→ task defaults
→ project/model policy
→ environment override
```

Avoid copying identical requirements into every policy file.

## 5. Environment-specific policy overlays

Allow the same model to have different operational requirements for:

- development
- staging
- production
- mobile
- edge
- batch
- real-time/API serving

Quality policy and operational policy should be separable where useful.

## 6. Semi-automated `mreg init`

Provide an onboarding command that inspects declared repository metadata and evaluation outputs and scaffolds MREG configuration.

Example:

```bash
mreg init
```

The result should be a draft, not an authoritative policy.

## 7. Repository/evaluation discovery

During initialization, discover when available:

- evaluation outputs
- existing metrics
- slices
- benchmark scripts/results
- CI configuration
- model registry metadata
- MLflow configuration
- known model/release targets

Do not execute arbitrary repository code simply to infer configuration.

## 8. Automatic task suggestion with explicit confirmation

MREG may suggest:

```text
Detected likely task: binary_classification
```

but a developer must explicitly confirm or configure the task.

## 9. Policy scaffolding

Once the task is known, create an editable policy template with sensible fields.

Do not silently choose business-critical thresholds.

## 10. Historical policy suggestions

If historical runs are available, summarize:

- production baseline
- recent metric distributions
- latency history
- artifact-size history
- historical regressions

Use those observations to suggest possible starting values.

Suggestions must be clearly labeled as suggestions and require human acceptance.

## 11. Separate evidence requirements from threshold values

Represent separately:

```text
evidence requirement:
    recall must exist

policy threshold:
    recall >= 0.92
```

This lets task profiles define structure while teams own business thresholds.

## 12. Policy validation at setup time

Detect nonsensical or invalid configuration before release review.

Examples:

- classification metric required for a regression task
- missing units
- unsupported metric
- impossible range
- duplicate rule IDs
- relative comparison against invalid baseline
- contradictory requirements

## 13. Policy provenance and ownership

Record:

- policy version
- content digest
- release target
- source repository revision
- creation/modification metadata where available

Treat policy as reviewed release code.

## 14. Policy-change impact review

When a policy changes, show how known evidence evaluates under:

```text
old policy
vs
new policy
```

Example:

```text
Candidate v18
Old policy: FAIL
Proposed policy: PASS
Changed because latency ceiling moved from 60 ms to 80 ms.
```

## 15. Normalized adapter interface

Standardize how integrations such as:

- MLflow
- custom evaluation pipelines
- future experiment trackers
- CI-generated evidence
- other testing tools

produce normalized MREG evidence.

Adapter source must not affect core verdict semantics.

## 16. Evidence-source mapping

Each requirement should identify the evidence source it expects.

Examples:

```text
f1
→ evaluation.aggregate.f1

p95 latency
→ benchmark.candidate.p95_ms

high-value transaction recall
→ slices.high_value.recall
```

Missing mappings should produce explicit insufficient-evidence findings.

## 17. Baseline-resolution rules

Support explicit methods such as:

- pinned digest
- explicitly supplied version
- current production version from registry
- trusted registry alias resolved to immutable version

Never bind eligibility to an unresolved mutable alias.

## 18. Model-family metadata without model-family-specific gating

Record metadata such as:

```text
random_forest
logistic_regression
xgboost
neural_network
```

but normally bind release requirements to the task/release target, not the estimator class.

## 19. Expandable reason-code registry

Design reason codes so future task profiles and adapters can extend them without destabilizing existing machine consumers.

Potential namespaces:

```text
POLICY_*
EVIDENCE_*
COMPATIBILITY_*
STATISTICS_*
BENCHMARK_*
ADAPTER_*
SYSTEM_*
```

Preserve backwards compatibility.

## 20. Onboarding usability milestone

Add a formal success target:

A developer with an existing supported binary-classification project should be able to:

```text
install MREG
→ run mreg init
→ review generated config/policy
→ provide or generate evidence
→ run first gate
→ understand the report
```

with minimal hand-written boilerplate.

Measure this during community pilots.
