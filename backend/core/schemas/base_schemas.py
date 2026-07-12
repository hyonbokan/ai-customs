from pydantic import BaseModel, Field


class BaseRequest(BaseModel):
    """Base request model with common fields."""

    file_url: str | None = Field(None, description="URL to the file")
    file_content: str | None = Field(None, description="Base64 encoded file content")


class BaseResponse(BaseModel):
    """Base response model with common fields."""

    success: bool = Field(description="Whether the operation was successful")
    message: str | None = Field(None, description="Response message")
    error: str | None = Field(None, description="Error message if failed")
