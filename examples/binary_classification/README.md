# Binary classification example

Install the repository's evaluation extra as described in the root README, then
run these commands from the repository root:

```sh
python examples/binary_classification/scripts/generate.py
mreg check --evidence examples/binary_classification/generated/pass.json --policy examples/binary_classification/policies/release-policy.yaml --output review/pass
mreg check --evidence examples/binary_classification/generated/fail.json --policy examples/binary_classification/policies/release-policy.yaml --output review/fail
mreg check --evidence examples/binary_classification/generated/insufficient.json --policy examples/binary_classification/policies/release-policy.yaml --output review/insufficient
mreg check --evidence examples/binary_classification/generated/error.json --policy examples/binary_classification/policies/release-policy.yaml --output review/error
mreg replay --bundle review/pass/bundle.json --output replay/pass
```

Expected exits: PASS 0; FAIL 1 (asserted latency 87 ms exceeds 60 ms);
INSUFFICIENT_EVIDENCE 2 (asserted priority-slice support below minimum); ERROR 3
(unsupported schema). Nonzero exits are expected for the last three checks, so do not
chain all scenarios in a shell that stops at the first nonzero exit.

Actual classification metrics come from two trained scikit-learn models on a fixed
synthetic holdout. Latency and artifact representation sizes are illustrative; they
are not a production serving benchmark. The generated evidence clearly marks benchmark
origin. Candidate quality improves in the hard-failure example. The insufficient case
is an externally asserted fixture, not a second real holdout measurement.

The generator computes an experimental F1 bootstrap interval, but the default policy
does not require it. To enable interval gating, add a rule with kind `interval`, field
`f1`, direction `higher`, operator `le`, threshold `1.0`, unit `percentage_points`,
inclusive `true`, and required `true`. This means an allowed one-percentage-point
regression, not a one-score-unit loss.
