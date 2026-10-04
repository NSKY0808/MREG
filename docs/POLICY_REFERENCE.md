# Policy reference, schema 1.0

Use declarative YAML with `schema_version`, `policy_id`, `version`, `task`, and
nonempty `rules`. Safe loading rejects duplicate keys, aliases, merge keys, and
executable Python YAML tags. The exported schema is `schemas/policy.schema.json`.

Each rule explicitly supplies `id`, `kind`, `field`, `direction`, `operator`,
`threshold`, `unit`, `inclusive`, and `required`; optional `slice`, `min_samples`
(default 1), `min_positive` and `min_negative` (default 0) apply to quality evidence.
IDs must be unique; at least one rule must be required.

| Kind | Fields | Operator | Unit | Meaning |
|---|---|---|---|---|
| minimum | accuracy/precision/recall/f1, latency, artifact_size | ge | score, ms, bytes | Candidate floor |
| maximum | accuracy/precision/recall/f1, latency, artifact_size | le | score, ms, bytes | Candidate ceiling |
| regression | classification metrics | le | percentage_points or relative_percent | Maximum allowed baseline-minus-candidate loss |
| regression | latency | le | ms or relative_percent | Maximum allowed candidate-minus-baseline increase |
| support | samples/positive/negative | ge | count | Minimum support for candidate on comparable examples |
| interval | classification metrics | le | percentage_points | Maximum permitted regression established by paired interval |

Directions describe the metric, independent of the bound: classification/support
are higher, latency/artifact_size lower. An absolute minimum latency is possible
but usually not a useful release policy. The operator defines the bound. `inclusive`
selects >=/<= versus >/<. Scores range [0,1]; percentage-point tolerances [0,100];
counts and bytes use integer thresholds. Relative-percent tolerances are nonnegative.

For higher-is-better metrics, point regression is baseline minus candidate. For
latency it is candidate minus baseline. Negative loss means improvement. One
percentage point means a 0.01 score change. Relative_percent divides the loss by
the absolute baseline and multiplies by 100. A zero baseline yields
RELATIVE_BASELINE_ZERO / INSUFFICIENT_EVIDENCE, never an invented percentage.

Intervals compare candidate-minus-baseline to `-threshold/100`:

- Lower bound meets the inclusive/exclusive boundary: PASS.
- Upper bound is entirely on the forbidden side: FAIL.
- Otherwise: INSUFFICIENT_EVIDENCE.

Point checks and interval checks are separate rules. Any demonstrated required
failure takes precedence over another inconclusive required interval. Required
missing slices, metric values, or adequate class support prevent PASS. Warning
rules retain their state and reasons but do not change the top-level verdict.

Sample guardrails are eligibility prerequisites, so low support yields insufficient
evidence. A dedicated support threshold rule is an explicit policy check and yields
FAIL when comparable known counts violate its bound. Choose the rule matching your intent.

The engine validates each rule's field/unit/direction/range and IDs. Cross-rule
contradiction analysis is not implemented: contradictory floors/ceilings will fail
at least one check and cannot silently pass. Task-profile inference and policy inheritance
remain future work.

Policies contain no runtime expressions, custom code, or automatic threshold guesses.
Changing the policy changes its digest. To review an intentional change, run `mreg check`
twice on the same evidence with old and proposed policies and separate output directories.
Compare verdicts, per-check states, requirements, and digests. See INTEGRATIONS.md for
the target-branch policy trust boundary.
