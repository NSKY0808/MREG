from collections.abc import Sequence

import numpy as np

from mreg.metrics.classification import binary_metrics
from mreg.models.evidence import BootstrapConfig, Interval


def paired_bootstrap(
    *,
    y_true: Sequence[int],
    baseline_predictions: Sequence[int],
    candidate_predictions: Sequence[int],
    metric: str,
    config: BootstrapConfig,
    examples_fingerprint: str,
    baseline_artifact_digest: str,
    candidate_artifact_digest: str,
    slice_name: str | None = None,
) -> Interval | None:
    """Experimental paired percentile interval. Any undefined resample yields no interval."""
    b = binary_metrics(y_true, baseline_predictions)
    c = binary_metrics(y_true, candidate_predictions)
    if metric not in b:
        raise ValueError("unsupported bootstrap metric")
    bv, cv = b[metric].value, c[metric].value
    if bv is None or cv is None:
        return None
    rng = np.random.default_rng(config.seed)
    differences: list[float] = []
    for _ in range(config.resamples):
        indices = rng.integers(0, len(y_true), size=len(y_true)).tolist()
        sy = [y_true[i] for i in indices]
        sb = [baseline_predictions[i] for i in indices]
        sc = [candidate_predictions[i] for i in indices]
        bm, cm = binary_metrics(sy, sb)[metric].value, binary_metrics(sy, sc)[metric].value
        if bm is None or cm is None:
            return None
        differences.append(cm - bm)
    alpha = (1 - config.confidence) / 2
    lower, upper = np.quantile(differences, [alpha, 1 - alpha], method="linear")
    return Interval.model_validate(
        {
            "metric": metric,
            "slice": slice_name,
            "lower": float(lower),
            "upper": float(upper),
            "difference": cv - bv,
            "config": config.model_dump(),
            "examples_fingerprint": examples_fingerprint,
            "baseline_artifact_digest": baseline_artifact_digest,
            "candidate_artifact_digest": candidate_artifact_digest,
        }
    )
