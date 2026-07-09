"""
Custom exception hierarchy for the AI Customs backend.

Every error carries a stable ``error_code`` (for clients/logs) and an HTTP
``status_code``. The global exception handler in ``main.py`` maps any
``BaseCustomsError`` to a consistent ``ErrorResponse`` JSON body.
"""

from typing import Any, Dict, Optional


class BaseCustomsError(Exception):
    """Base exception for all custom errors."""

    # Overridden by subclasses.
    error_code: str = "internal_error"
    status_code: int = 500

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to the shape used by the API error response."""
        payload: Dict[str, Any] = {"error_code": self.error_code, "error": self.message}
        if self.details:
            payload["details"] = self.details
        return payload


class ConfigurationError(BaseCustomsError):
    """Raised when there's a configuration error."""

    error_code = "configuration_error"
    status_code = 500


class ValidationError(BaseCustomsError):
    """Raised when input validation fails."""

    error_code = "validation_error"
    status_code = 422


class AuthenticationError(BaseCustomsError):
    """Raised when a request is missing or presents an invalid API key."""

    error_code = "authentication_error"
    status_code = 401


class LLMError(BaseCustomsError):
    """Raised when there's an LLM-related error (e.g. the model service is unreachable).

    ``retryable`` marks transient failures (timeouts, connection errors, empty
    responses) that are worth retrying, as opposed to deterministic ones like an
    unparseable response, which a retry would not fix. ``connection_error`` marks
    the subset where the server couldn't be reached at all, so a different base
    URL (the DNS fallback) is worth trying.
    """

    error_code = "llm_error"
    status_code = 502

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        retryable: bool = False,
        connection_error: bool = False,
    ):
        super().__init__(message, details)
        self.retryable = retryable
        self.connection_error = connection_error


class RateLimitError(LLMError):
    """Raised when the LLM service rate limit is exceeded."""

    error_code = "rate_limit_error"
    status_code = 429

    def __init__(
        self, message: str, details: Optional[Dict[str, Any]] = None, retryable: bool = True
    ):
        super().__init__(message, details, retryable)


class ProcessingError(BaseCustomsError):
    """Raised when processing fails."""

    error_code = "processing_error"
    status_code = 500


class PDFProcessingError(ProcessingError):
    """Raised when PDF processing fails."""

    error_code = "pdf_processing_error"
    status_code = 422


class DeclarationAnalysisError(ProcessingError):
    """Raised when declaration analysis fails."""

    error_code = "declaration_analysis_error"
    status_code = 502
