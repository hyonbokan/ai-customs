"""
Custom exception classes for the AI Customs backend.
"""

from typing import Any, Dict, Optional


class BaseCustomsError(Exception):
    """Base exception class for all custom errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(BaseCustomsError):
    """Raised when there's a configuration error."""

    pass


class LLMError(BaseCustomsError):
    """Raised when there's an LLM-related error."""

    pass


class RateLimitError(BaseCustomsError):
    """Raised when rate limits are exceeded."""

    pass


class ValidationError(BaseCustomsError):
    """Raised when validation fails."""

    pass


class ProcessingError(BaseCustomsError):
    """Raised when processing fails."""

    pass


class PDFProcessingError(ProcessingError):
    """Raised when PDF processing fails."""

    pass


class DeclarationAnalysisError(ProcessingError):
    """Raised when declaration analysis fails."""

    pass
