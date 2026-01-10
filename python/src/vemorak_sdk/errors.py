from dataclasses import dataclass
from typing import Any


class VemorakSdkError(Exception):
    """Base SDK error."""


@dataclass
class VmpHttpError(VemorakSdkError):
    """
    Raised for non-2xx HTTP responses.

    VMP error contract:
      { "error": "message" }
    sometimes:
      { "error": "invalid input", "details": {...} }
    """

    status: int
    error: str
    raw_body_text: str
    details: Any | None = None

    def __str__(self) -> str:
        return f"VMP request failed ({self.status}): {self.error}"


class VmpTimeoutError(VemorakSdkError):
    """Raised when the request times out."""
