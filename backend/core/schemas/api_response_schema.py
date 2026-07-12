from typing import Any

from pydantic import BaseModel


class SuccessResponse(BaseModel):
    """Standard success response schema."""

    success: bool = True
    data: Any | None = None
    message: str | None = None


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    success: bool = False
    error: str
    message: str | None = None
