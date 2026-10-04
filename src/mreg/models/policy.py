from typing import Literal, Self

from pydantic import Field, model_validator

from mreg.models.common import Contract, Count, Number, Text


class Rule(Contract):
    id: Text
    kind: Literal["minimum", "maximum", "regression", "support", "interval"]
    field: Literal[
        "accuracy",
        "precision",
        "recall",
        "f1",
        "latency",
        "artifact_size",
        "samples",
        "positive",
        "negative",
    ]
    slice: Text | None = None
    direction: Literal["higher", "lower"]
    operator: Literal["ge", "le"]
    threshold: Number = Field(ge=0)
    unit: Literal["score", "ms", "bytes", "count", "percentage_points", "relative_percent"]
    inclusive: bool
    required: bool
    min_samples: Count = 1
    min_positive: Count = 0
    min_negative: Count = 0

    @model_validator(mode="after")
    def semantics(self) -> Self:
        metric = self.field in {"accuracy", "precision", "recall", "f1"}
        expected_direction = "lower" if self.field in {"latency", "artifact_size"} else "higher"
        if self.direction != expected_direction:
            raise ValueError("direction must match the supported field's meaning")
        if self.kind in {"regression", "interval"}:
            if self.operator != "le":
                raise ValueError("regression/interval threshold is a maximum allowed regression")
            if self.kind == "interval" and (not metric or self.unit != "percentage_points"):
                raise ValueError("interval checks support classification percentage points only")
            if self.kind == "regression":
                if self.field in {"artifact_size", "samples", "positive", "negative"}:
                    raise ValueError("unsupported regression field")
                allowed = (
                    {"percentage_points", "relative_percent"}
                    if metric
                    else {"ms", "relative_percent"}
                )
                if self.unit not in allowed:
                    raise ValueError("invalid regression unit")
        else:
            expected_unit = (
                "score"
                if metric
                else {"latency": "ms", "artifact_size": "bytes"}.get(self.field, "count")
            )
            if self.unit != expected_unit:
                raise ValueError("unit does not match field")
            expected_operator = "le" if self.kind == "maximum" else "ge"
            if self.operator != expected_operator:
                raise ValueError("operator does not match rule kind")
            if self.kind == "support" and self.field not in {"samples", "positive", "negative"}:
                raise ValueError("support rules require a support field")
            if self.kind != "support" and self.field in {"samples", "positive", "negative"}:
                raise ValueError("support fields require support rules")
        if metric and self.unit == "score" and self.threshold > 1:
            raise ValueError("score thresholds must be between 0 and 1")
        if self.unit == "percentage_points" and self.threshold > 100:
            raise ValueError("percentage points must be between 0 and 100")
        if self.unit in {"count", "bytes"} and not self.threshold.is_integer():
            raise ValueError("count and byte thresholds must be integers")
        if self.slice and not (metric or self.kind == "support"):
            raise ValueError("slice is only supported for classification/support")
        return self


class Policy(Contract):
    schema_version: Literal["1.0"]
    policy_id: Text
    version: Text
    task: Literal["binary_classification"]
    rules: list[Rule] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_rules(self) -> Self:
        ids = [r.id for r in self.rules]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate rule IDs")
        if not any(r.required for r in self.rules):
            raise ValueError("at least one required rule is needed")
        return self
