from typing import Any

import pytest
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

from mreg.metrics.bootstrap import paired_bootstrap
from mreg.metrics.classification import binary_metrics, evaluate_paired
from mreg.models.evidence import BootstrapConfig, Evidence


def test_sklearn_metric_parity() -> None:
    y = [0, 0, 1, 1, 1, 0]
    p = [0, 1, 1, 0, 1, 0]
    metrics = binary_metrics(y, p)
    for name, function in {
        "accuracy": accuracy_score,
        "precision": precision_score,
        "recall": recall_score,
        "f1": f1_score,
    }.items():
        assert metrics[name].value == pytest.approx(function(y, p))
    undefined = binary_metrics([0, 0], [0, 0])
    assert undefined["recall"].value is None
    assert undefined["precision"].value is None
    assert undefined["f1"].value is None


def paired_args(evidence: Evidence) -> dict[str, Any]:
    return dict(
        y_true=[0, 1, 0, 1],
        baseline_predictions=[0, 1, 0, 0],
        candidate_predictions=[0, 1, 0, 1],
        example_ids=["a", "b", "c", "d"],
        baseline_example_ids=["a", "b", "c", "d"],
        candidate_example_ids=["a", "b", "c", "d"],
        baseline_model=evidence.baseline.model,
        candidate_model=evidence.candidate.model,
        dataset_fingerprint=evidence.candidate.context.dataset_fingerprint,
        dataset_version="1",
        source_evidence_id="paired",
    )


@pytest.mark.parametrize(
    "change",
    [
        {"candidate_example_ids": ["b", "a", "c", "d"]},
        {"example_ids": ["a", "a", "c", "d"]},
        {"candidate_predictions": [0, 1]},
        {"y_true": [0, 2, 0, 1]},
        {"candidate_predictions": [True, 1, 0, 1]},
        {"slices": {"priority": [True]}, "slice_definitions": {"priority": "test"}},
    ],
)
def test_alignment_errors(evidence: Evidence, change: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        evaluate_paired(**(paired_args(evidence) | change))


def test_probability_threshold(evidence: Evidence) -> None:
    args = paired_args(evidence) | {
        "prediction_kind": "probabilities",
        "baseline_predictions": [0.1, 0.5, 0.2, 0.4],
        "candidate_predictions": [0.1, 0.5, 0.2, 0.9],
    }
    result = evaluate_paired(**args)
    assert result.candidate.metrics["f1"].value == 1.0
    assert result.baseline.metrics["recall"].value == 0.5


def test_bootstrap_reproducible(evidence: Evidence) -> None:
    args = dict(
        y_true=[0, 1] * 30,
        baseline_predictions=[0, 0] * 30,
        candidate_predictions=[0, 1] * 30,
        metric="accuracy",
        config=BootstrapConfig(seed=42, resamples=100, confidence=0.95),
        examples_fingerprint=evidence.candidate.context.examples_fingerprint,
        baseline_artifact_digest=evidence.baseline.model.artifact_digest,
        candidate_artifact_digest=evidence.candidate.model.artifact_digest,
    )
    first = paired_bootstrap(**args)
    assert first == paired_bootstrap(**args)
    assert first is not None and first.lower > 0 and first.difference == 0.5


def test_bootstrap_undefined(evidence: Evidence) -> None:
    assert (
        paired_bootstrap(
            y_true=[0] * 10,
            baseline_predictions=[0] * 10,
            candidate_predictions=[0] * 10,
            metric="f1",
            config=BootstrapConfig(seed=1, resamples=100, confidence=0.95),
            examples_fingerprint=evidence.candidate.context.examples_fingerprint,
            baseline_artifact_digest=evidence.baseline.model.artifact_digest,
            candidate_artifact_digest=evidence.candidate.model.artifact_digest,
        )
        is None
    )
