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


class LLMError(BaseCustomsError):
    """Raised when there's an LLM-related error (e.g. the model service is unreachable)."""

    error_code = "llm_error"
    status_code = 502


class RateLimitError(LLMError):
    """Raised when the LLM service rate limit is exceeded."""

    error_code = "rate_limit_error"
    status_code = 429


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
