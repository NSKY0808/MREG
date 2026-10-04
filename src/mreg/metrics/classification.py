from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from math import isfinite

from mreg.models.evidence import (
    EvaluationContext,
    Evidence,
    Metric,
    ModelIdentity,
    RunEvidence,
    Slice,
    Support,
)
from mreg.utils.hashing import digest


def binary_metrics(y_true: Sequence[int], predictions: Sequence[int]) -> dict[str, Metric]:
    """Binary metrics with undefined denominators represented as null."""
    if len(y_true) != len(predictions) or not y_true:
        raise ValueError("nonempty aligned labels and predictions required")
    if any(type(v) is not int or v not in {0, 1} for v in [*y_true, *predictions]):
        raise ValueError("binary labels/predictions must be integer 0 or 1")
    tp = sum(y == p == 1 for y, p in zip(y_true, predictions, strict=True))
    fp = sum(y == 0 and p == 1 for y, p in zip(y_true, predictions, strict=True))
    fn = sum(y == 1 and p == 0 for y, p in zip(y_true, predictions, strict=True))
    tn = len(y_true) - tp - fp - fn
    values = {
        "accuracy": (tp + tn) / len(y_true),
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None,
    }
    return {
        key: Metric(value=value, unit="score", definition=f"binary_{key}_v1", averaging="binary")
        for key, value in values.items()
    }


def support(labels: Sequence[int]) -> Support:
    positive = sum(labels)
    return Support(samples=len(labels), positive=positive, negative=len(labels) - positive)


def evaluate_paired(
    *,
    y_true: Sequence[int],
    baseline_predictions: Sequence[float | int],
    candidate_predictions: Sequence[float | int],
    example_ids: Sequence[str],
    baseline_example_ids: Sequence[str],
    candidate_example_ids: Sequence[str],
    baseline_model: ModelIdentity,
    candidate_model: ModelIdentity,
    dataset_fingerprint: str,
    dataset_version: str,
    source_evidence_id: str,
    prediction_kind: str = "labels",
    threshold: float = 0.5,
    slices: Mapping[str, Sequence[bool]] | None = None,
    slice_definitions: Mapping[str, str] | None = None,
    collected_at: str | None = None,
) -> Evidence:
    """Build paired evidence; require identical explicit ID order, never realign rows."""
    ids = list(example_ids)
    n = len(ids)
    if not n or len(set(ids)) != n or any(not isinstance(i, str) or not i for i in ids):
        raise ValueError("example IDs must be nonempty and unique")
    if ids != list(baseline_example_ids) or ids != list(candidate_example_ids):
        raise ValueError("candidate/baseline ID order must match labels exactly")
    if len(y_true) != n or len(baseline_predictions) != n or len(candidate_predictions) != n:
        raise ValueError("all paired inputs must have identical length")
    if not isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("threshold must be finite and between 0 and 1")
    if prediction_kind not in {"labels", "probabilities"}:
        raise ValueError("prediction_kind must be labels or probabilities")

    def convert(values: Sequence[float | int]) -> list[int]:
        if prediction_kind == "labels":
            if any(type(v) is not int or v not in {0, 1} for v in values):
                raise ValueError("labels must be integer 0 or 1")
            return [int(v) for v in values]
        if any(isinstance(v, bool) or not isfinite(v) or not 0 <= v <= 1 for v in values):
            raise ValueError("probabilities must be finite and between 0 and 1")
        return [int(v >= threshold) for v in values]

    bp, cp = convert(baseline_predictions), convert(candidate_predictions)
    labels = list(y_true)
    binary_metrics(labels, bp)  # validates labels even before constructing slices
    context = EvaluationContext(
        dataset_fingerprint=dataset_fingerprint,
        dataset_version=dataset_version,
        split="test",
        examples_fingerprint=digest(ids),
        labels_fingerprint=digest(labels),
        label_definition="synthetic_or_user_supplied_binary_label",
        positive_class=1,
        prediction_threshold=threshold,
    )

    def run(predictions: list[int], model: ModelIdentity) -> RunEvidence:
        groups: dict[str, Slice] = {}
        for name, mask in (slices or {}).items():
            if len(mask) != n or any(type(v) is not bool for v in mask):
                raise ValueError("slice masks must be aligned booleans")
            if not slice_definitions or name not in slice_definitions:
                raise ValueError("every slice requires an explicit definition")
            indices = [i for i, selected in enumerate(mask) if selected]
            sy = [labels[i] for i in indices]
            sp = [predictions[i] for i in indices]
            groups[name] = Slice(
                definition=slice_definitions[name],
                examples_fingerprint=digest([ids[i] for i in indices]),
                support=support(sy),
                metrics=binary_metrics(sy, sp) if sy else {},
            )
        return RunEvidence(
            model=model,
            origin="computed",
            context=context.model_copy(deep=True),
            support=support(labels),
            metrics=binary_metrics(labels, predictions),
            slices=groups,
        )

    return Evidence(
        schema_version="1.0",
        task="binary_classification",
        evidence_id=source_evidence_id,
        collected_at=collected_at or datetime.now(UTC).isoformat(),
        evaluator_version="mreg-0.1.0",
        baseline=run(bp, baseline_model),
        candidate=run(cp, candidate_model),
    )
