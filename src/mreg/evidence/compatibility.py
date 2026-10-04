from mreg.models.evidence import RunEvidence


def quality_compatibility(baseline: RunEvidence, candidate: RunEvidence) -> list[str]:
    """Return every incompatibility; do not align or coerce mismatched runs."""
    b, c = baseline.context, candidate.context
    checks = [
        (
            b.dataset_fingerprint != c.dataset_fingerprint
            or b.dataset_version != c.dataset_version,
            "DATASET_MISMATCH",
        ),
        (b.split != c.split, "EVALUATION_SPLIT_MISMATCH"),
        (
            b.examples_fingerprint != c.examples_fingerprint
            or baseline.support != candidate.support,
            "EXAMPLE_PAIRING_MISMATCH",
        ),
        (
            b.labels_fingerprint != c.labels_fingerprint
            or b.label_definition != c.label_definition,
            "LABEL_DEFINITION_MISMATCH",
        ),
        (b.positive_class != c.positive_class, "POSITIVE_CLASS_MISMATCH"),
        (b.prediction_threshold != c.prediction_threshold, "PREDICTION_THRESHOLD_MISMATCH"),
    ]
    return [code for condition, code in checks if condition]
