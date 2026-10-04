from typing import Protocol

from mreg.models.evidence import Evidence


class EvidenceAdapter(Protocol):
    """Return normalized evidence with immutable identities and explicit origins."""

    def collect(self) -> Evidence: ...
