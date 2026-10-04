from typing import Any

from pydantic import ValidationError

from mreg.models.evidence import Evidence


class InputError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def validate_evidence(data: Any) -> Evidence:
    if isinstance(data, dict) and data.get("schema_version") not in {None, "1.0"}:
        raise InputError("UNSUPPORTED_SCHEMA_VERSION")
    try:
        return Evidence.model_validate(data)
    except ValidationError as error:
        code = "INVALID_EVIDENCE"
        if any(
            e["type"] in {"finite_number", "float_type", "float_parsing"} for e in error.errors()
        ):
            code = "INVALID_NUMERIC_VALUE"
        raise InputError(code) from error
