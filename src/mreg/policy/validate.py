from typing import Any

from pydantic import ValidationError

from mreg.evidence.validate import InputError
from mreg.models.policy import Policy


def validate_policy(data: Any) -> Policy:
    if isinstance(data, dict) and data.get("schema_version") not in {None, "1.0"}:
        raise InputError("UNSUPPORTED_SCHEMA_VERSION")
    try:
        return Policy.model_validate(data)
    except ValidationError as error:
        raise InputError("INVALID_POLICY") from error
