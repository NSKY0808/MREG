# Evidence contract, schema 1.0

The authoritative structural schema is `schemas/evidence.schema.json`, exported
from `mreg.models.evidence.Evidence`. Pydantic validators additionally enforce
cross-field invariants that JSON Schema alone does not capture. Unknown fields,
implicit string-to-number conversions, boolean numerics, NaN/infinity, negative
counts, out-of-range scores, and inconsistent class counts are rejected.

One JSON evidence bundle has `schema_version`, `task` (binary_classification),
`evidence_id`, timezone-aware `collected_at`, `evaluator_version`, `baseline`,
`candidate`, and optional `intervals`. Each run has:

- `model`: model ID/version, immutable SHA-256 artifact digest, optional byte size,
  source revision, and configuration digest.
- `origin`: computed, imported, or externally_asserted. A benchmark has its own
  origin because computed quality can coexist with asserted operational fixtures.
- `context`: dataset fingerprint/version, split, ordered example fingerprint,
  ordered label fingerprint, label definition, encoded positive class (0 or 1),
  and prediction threshold.
- `support`: total samples, positive, and negative counts; the two classes sum
  to total samples.
- `metrics`: accuracy, precision, recall, and/or f1 entries. Each has `value`
  (number or null), `unit`, `definition`, and `averaging`. Null means undefined;
  an absent key means missing. Classification values are normalized to [0,1].
- `slices`: explicit names, definitions, ordered example fingerprints, support,
  and metrics. Slice counts cannot exceed aggregate counts.
- `benchmark`: optional context and latency measurement. Context includes hardware,
  runtime, workload, concurrency, batch size, warm-up, repetitions, and p95 statistic.
  Latency carries explicit units, metric definition, and averaging.

Example metrics are `binary_f1_v1`, averaging `binary`, unit `score`; benchmark
latency is `inference_p95_v1`, averaging `none`, unit `ms`. Definitions are producer
identifiers, not executed expressions. The engine checks matching meanings; it
cannot prove a producer implemented them honestly.

Intervals record metric/slice, lower/upper bounds, candidate-minus-baseline point
difference, paired-percentile method, seed, resamples, confidence, example fingerprint,
and candidate/baseline artifact digests. The gate verifies binding and consistency
with reported point differences; it does not reconstruct raw bootstrap samples.

Decision provenance lives in result.json and bundle.json: policy/evidence normalized
digests, model identities, implementation/semantics versions, and per-check references.
References are JSON Pointers into normalized evidence, including escaping of slice keys.
For missing evidence they identify the expected location rather than an existing value.
Canonical JSON sorts keys, uses compact UTF-8 JSON, and disallows nonfinite values.
Digests cover validated, default-expanded normalized objects, not original file bytes.

The bundle stores normalized evidence and the full normalized policy, allowing replay
without network or registry access. It contains metrics and identities, not raw labels,
features, or prediction arrays. Fingerprints are assertions of pairing, not cryptographic
proof of truthful measurement. Resolve registry aliases upstream to immutable versions.

Avoid putting credentials, sensitive IDs, personal data, or free-form private text into
identity/definition fields. Fields are bounded and unknown fields rejected, but a local
report deliberately displays accepted identities; automatic detection of arbitrary secrets
is not claimed. Trusted collectors remain responsible for redaction.
