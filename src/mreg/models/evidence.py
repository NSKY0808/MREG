from datetime import datetime
from typing import Literal, Self

from pydantic import Field, field_validator, model_validator

from mreg.models.common import Contract, Count, Digest, Number, Text


class Metric(Contract):
    value: Number | None
    unit: Text
    definition: Text
    averaging: Text


class Support(Contract):
    samples: Count
    positive: Count
    negative: Count

    @model_validator(mode="after")
    def consistent(self) -> Self:
        if self.positive + self.negative != self.samples:
            raise ValueError("positive + negative must equal samples")
        return self


class EvaluationContext(Contract):
    dataset_fingerprint: Digest
    dataset_version: Text
    split: Text
    examples_fingerprint: Digest
    labels_fingerprint: Digest
    label_definition: Text
    positive_class: Literal[0, 1]
    prediction_threshold: Number = Field(ge=0, le=1)

    @field_validator("positive_class", mode="before")
    @classmethod
    def integer_class(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("positive class must be integer 0 or 1")
        return value


class ModelIdentity(Contract):
    model_id: Text
    version: Text
    artifact_digest: Digest
    artifact_size_bytes: Count | None
    source_revision: Text
    configuration_digest: Digest


class Slice(Contract):
    definition: Text
    examples_fingerprint: Digest
    support: Support
    metrics: dict[str, Metric]


class BenchmarkContext(Contract):
    hardware: Text
    runtime: Text
    workload: Text
    concurrency: int = Field(ge=1)
    batch_size: int = Field(ge=1)
    warmup: Text
    repetitions: int = Field(ge=1)
    statistic: Literal["p95"]


class Benchmark(Contract):
    origin: Literal["computed", "imported", "externally_asserted"]
    context: BenchmarkContext
    latency: Metric

    @model_validator(mode="after")
    def nonnegative(self) -> Self:
        if self.latency.value is not None and self.latency.value < 0:
            raise ValueError("latency must be nonnegative")
        return self


class RunEvidence(Contract):
    model: ModelIdentity
    origin: Literal["computed", "imported", "externally_asserted"]
    context: EvaluationContext
    support: Support
    metrics: dict[str, Metric]
    slices: dict[str, Slice] = Field(default_factory=dict)
    benchmark: Benchmark | None = None

    @model_validator(mode="after")
    def binary_metrics(self) -> Self:
        for group in [self.metrics, *(s.metrics for s in self.slices.values())]:
            if set(group) - {"accuracy", "precision", "recall", "f1"}:
                raise ValueError("unsupported binary classification metric")
            for m in group.values():
                if m.value is not None and not 0 <= m.value <= 1:
                    raise ValueError("classification metrics must be between 0 and 1")
        for s in self.slices.values():
            if any(
                getattr(s.support, key) > getattr(self.support, key)
                for key in ("samples", "positive", "negative")
            ):
                raise ValueError("slice support exceeds aggregate support")
        return self


class BootstrapConfig(Contract):
    seed: int = Field(ge=0)
    resamples: int = Field(ge=100, le=100000)
    confidence: Number = Field(gt=0, lt=1)
    method: Literal["paired_percentile"] = "paired_percentile"


class Interval(Contract):
    metric: Literal["accuracy", "precision", "recall", "f1"]
    slice: Text | None = None
    lower: Number = Field(ge=-1, le=1)
    upper: Number = Field(ge=-1, le=1)
    difference: Number = Field(ge=-1, le=1)
    config: BootstrapConfig
    examples_fingerprint: Digest
    baseline_artifact_digest: Digest
    candidate_artifact_digest: Digest

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.lower > self.upper:
            raise ValueError("interval lower bound exceeds upper bound")
        return self


class Evidence(Contract):
    schema_version: Literal["1.0"]
    task: Literal["binary_classification"]
    evidence_id: Text
    collected_at: Text
    evaluator_version: Text
    baseline: RunEvidence
    candidate: RunEvidence
    intervals: list[Interval] = Field(default_factory=list)

    @field_validator("collected_at")
    @classmethod
    def timestamp(cls, value: str) -> str:
        date = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if date.tzinfo is None:
            raise ValueError("collection timestamp must include timezone")
        return value

    @model_validator(mode="after")
    def unique_intervals(self) -> Self:
        keys = [(i.metric, i.slice) for i in self.intervals]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate interval metric/slice")
        return self
