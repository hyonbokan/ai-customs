from typing import Any, Optional

from pydantic import BaseModel


class SuccessResponse(BaseModel):
    """Standard success response schema."""

    success: bool = True
    data: Optional[Any] = None
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    success: bool = False
    error: str
    message: Optional[str] = None
