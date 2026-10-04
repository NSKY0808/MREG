"""Public deterministic gate API; evaluation dependencies are optional."""

from mreg.gate.evaluator import evaluate
from mreg.models.evidence import Evidence
from mreg.models.policy import Policy
from mreg.models.result import Result

__version__ = "0.1.0"
SEMANTICS_VERSION = "1.0"
__all__ = ["Evidence", "Policy", "Result", "evaluate"]
