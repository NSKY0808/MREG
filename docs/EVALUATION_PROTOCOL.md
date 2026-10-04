# Paired binary evaluation and uncertainty

`evaluate_paired` accepts aligned integer 0/1 labels, candidate/baseline label or
probability sequences, and three explicit ID sequences: label IDs, candidate IDs,
baseline IDs. ID order must be identical, nonempty, and unique. Length mismatches
raise ValueError. There is no implicit alignment, sorting, joining, or row dropping.
Probability conversion uses `probability >= threshold` and records the threshold.
The helper encodes positive class 1; imported evidence may use 0 with declared semantics.

Slice masks are aligned booleans with explicit definitions. The producer fingerprints
ordered IDs and labels and computes accuracy, precision, recall, and F1 using binary
confusion counts. Undefined denominators yield null, not zero. Metric values have
parity tests against scikit-learn for defined cases. There is no pickle/joblib loading.

The demo uses generated data with a held-out test split, fixed seeds, and two locally
trained logistic classifiers. Baseline uses one feature; candidate uses all eight.
This is a learning fixture, not a useful real-world accuracy benchmark. Priority is an
explicit artificial slice without business meaning. Operational values are asserted
fixtures, not performance measurements. The insufficient scenario is explicitly
externally asserted, retaining promising metrics while withholding sufficient support.

`paired_bootstrap` is experimental. It draws the same resampled row indices for both
models, computes candidate-minus-baseline differences, and uses equal-tail percentile
quantiles. Seed, resamples, confidence, method, and model/example identities are recorded.
Undefined original metrics or any undefined resample return no interval, which blocks
an enabled interval rule with MISSING_INTERVAL. This conservative behavior avoids
silently conditioning on only defined samples.

Do not interpret bootstrap intervals as universal release guarantees. They assume
the sampling procedure fits the task, and do not handle clustered/time-dependent data,
multiple-comparison correction, repeated holdout use, leakage, or distribution shift.
Predeclare slices and class-support thresholds. For real latency evidence, measure
both models under comparable hardware/runtime/workload, batch size, concurrency,
warm-up, repetitions, units, and statistic. No live benchmark is claimed by the demo.
