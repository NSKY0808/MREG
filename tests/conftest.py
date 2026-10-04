from pathlib import Path

import pytest

from mreg.models.evidence import Evidence
from mreg.models.policy import Policy
from mreg.utils.hashing import digest


@pytest.fixture
def evidence() -> Evidence:
    context = {
        "dataset_fingerprint": digest("dataset"),
        "dataset_version": "1",
        "split": "test",
        "examples_fingerprint": digest("examples"),
        "labels_fingerprint": digest("labels"),
        "label_definition": "binary",
        "positive_class": 1,
        "prediction_threshold": 0.5,
    }
    metric = {"value": 0.9, "unit": "score", "definition": "binary_f1_v1", "averaging": "binary"}
    run = {
        "model": {
            "model_id": "demo",
            "version": "1",
            "artifact_digest": digest("model"),
            "artifact_size_bytes": 100,
            "source_revision": "abc",
            "configuration_digest": digest("config"),
        },
        "origin": "externally_asserted",
        "context": context,
        "support": {"samples": 100, "positive": 50, "negative": 50},
        "metrics": {"f1": metric, "recall": {**metric, "definition": "binary_recall_v1"}},
        "slices": {
            "priority": {
                "definition": "priority==true",
                "examples_fingerprint": digest("slice"),
                "support": {"samples": 20, "positive": 10, "negative": 10},
                "metrics": {"recall": {**metric, "definition": "binary_recall_v1"}},
            }
        },
        "benchmark": {
            "origin": "externally_asserted",
            "context": {
                "hardware": "cpu",
                "runtime": "py",
                "workload": "single",
                "concurrency": 1,
                "batch_size": 1,
                "warmup": "100",
                "repetitions": 100,
                "statistic": "p95",
            },
            "latency": {
                "value": 40.0,
                "unit": "ms",
                "definition": "inference_p95_v1",
                "averaging": "none",
            },
        },
    }
    return Evidence.model_validate(
        {
            "schema_version": "1.0",
            "task": "binary_classification",
            "evidence_id": "fixture",
            "collected_at": "2026-10-03T00:00:00Z",
            "evaluator_version": "test",
            "baseline": run,
            "candidate": run,
        }
    )


@pytest.fixture
def policy() -> Policy:
    return Policy.model_validate(
        {
            "schema_version": "1.0",
            "policy_id": "test",
            "version": "1",
            "task": "binary_classification",
            "rules": [
                {
                    "id": "f1",
                    "kind": "minimum",
                    "field": "f1",
                    "direction": "higher",
                    "operator": "ge",
                    "threshold": 0.9,
                    "unit": "score",
                    "inclusive": True,
                    "required": True,
                }
            ],
        }
    )


@pytest.fixture
def root() -> Path:
    return Path(__file__).resolve().parents[1]
