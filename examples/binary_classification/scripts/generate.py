"""Train local sklearn demo models; generate paired evidence, never deserialize models."""

import argparse
from pathlib import Path

from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

from mreg.metrics.bootstrap import paired_bootstrap
from mreg.metrics.classification import evaluate_paired
from mreg.models.evidence import (
    Benchmark,
    BenchmarkContext,
    BootstrapConfig,
    Metric,
    ModelIdentity,
    Support,
)
from mreg.reporting.json_report import write_json
from mreg.utils.hashing import digest


def generate(output: Path) -> None:
    x, y = make_classification(
        n_samples=2400, n_features=8, n_informative=6, n_redundant=0, class_sep=2.5, random_state=42
    )
    xt, xe, yt, ye = train_test_split(x, y, test_size=0.3, stratify=y, random_state=42)
    baseline = LogisticRegression(max_iter=1000, random_state=42).fit(xt[:, :1], yt)
    candidate = LogisticRegression(max_iter=1000, random_state=42).fit(xt, yt)
    bp, cp, labels = (
        baseline.predict(xe[:, :1]).tolist(),
        candidate.predict(xe).tolist(),
        ye.tolist(),
    )
    ids = [f"test-{i}" for i in range(len(labels))]

    def identity(model: LogisticRegression, version: str) -> ModelIdentity:
        # Fingerprint the actual learned numeric state; this demo does not persist a model file.
        state = {
            "coef": model.coef_.tolist(),
            "intercept": model.intercept_.tolist(),
            "classes": model.classes_.tolist(),
        }
        return ModelIdentity(
            model_id="synthetic-classifier",
            version=version,
            artifact_digest=digest(state),
            artifact_size_bytes=len(str(state).encode()),
            source_revision="example-v1",
            configuration_digest=digest(model.get_params()),
        )

    evidence = evaluate_paired(
        y_true=labels,
        baseline_predictions=bp,
        candidate_predictions=cp,
        example_ids=ids,
        baseline_example_ids=ids,
        candidate_example_ids=ids,
        baseline_model=identity(baseline, "baseline-1"),
        candidate_model=identity(candidate, "candidate-2"),
        dataset_fingerprint=digest({"features": xe.tolist(), "labels": labels}),
        dataset_version="generated-seed-42-v1",
        source_evidence_id="scenario-pass",
        slices={"priority": [i < 200 for i in range(len(labels))]},
        slice_definitions={
            "priority": "First 200 holdout IDs; demo-only slice, no business meaning"
        },
        collected_at="2026-10-03T00:00:00Z",
    )
    context = BenchmarkContext(
        hardware="DEMO-ASSERTED-CPU",
        runtime="demo-v1",
        workload="illustrative-fixture",
        concurrency=1,
        batch_size=1,
        warmup="fixture-no-measurement",
        repetitions=100,
        statistic="p95",
    )
    for run, value in [(evidence.baseline, 40.0), (evidence.candidate, 45.0)]:
        run.benchmark = Benchmark(
            origin="externally_asserted",
            context=context,
            latency=Metric(value=value, unit="ms", definition="inference_p95_v1", averaging="none"),
        )
    interval = paired_bootstrap(
        y_true=labels,
        baseline_predictions=bp,
        candidate_predictions=cp,
        metric="f1",
        config=BootstrapConfig(seed=42, resamples=200, confidence=0.95),
        examples_fingerprint=evidence.candidate.context.examples_fingerprint,
        baseline_artifact_digest=evidence.baseline.model.artifact_digest,
        candidate_artifact_digest=evidence.candidate.model.artifact_digest,
    )
    if interval:
        evidence.intervals = [interval]
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "pass.json", evidence.model_dump(mode="json"))
    failed = evidence.model_copy(deep=True)
    failed.evidence_id = "scenario-fail"
    assert failed.candidate.benchmark is not None
    failed.candidate.benchmark.latency.value = 87.0
    write_json(output / "fail.json", failed.model_dump(mode="json"))
    insufficient = evidence.model_copy(deep=True)
    insufficient.evidence_id = "scenario-insufficient"
    for run in [insufficient.baseline, insufficient.candidate]:
        group = run.slices["priority"]
        group.support = Support(samples=2, positive=1, negative=1)
        group.definition = "Two examples; deliberately limited imported support fixture"
        group.examples_fingerprint = digest(ids[:2])
        run.origin = "externally_asserted"
    write_json(output / "insufficient.json", insufficient.model_dump(mode="json"))
    malformed = evidence.model_dump(mode="json")
    malformed["schema_version"] = "unsupported"
    write_json(output / "error.json", malformed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=Path("examples/binary_classification/generated")
    )
    generate(parser.parse_args().output)
