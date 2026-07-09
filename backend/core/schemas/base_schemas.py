from typing import List, Optional

from pydantic import BaseModel, Field


class BaseRequest(BaseModel):
    """Base request model with common fields."""

    file_url: Optional[str] = Field(None, description="URL to the file")
    file_content: Optional[str] = Field(None, description="Base64 encoded file content")


class BaseResponse(BaseModel):
    """Base response model with common fields."""

    success: bool = Field(description="Whether the operation was successful")
    message: Optional[str] = Field(None, description="Response message")
    error: Optional[str] = Field(None, description="Error message if failed")


class BaseStatus(BaseModel):
    """Base status model for tasks."""

    task_id: str = Field(description="Task identifier")
    status: str = Field(description="Current status")
    progress: Optional[int] = Field(None, description="Progress percentage (0-100)")


class Metadata(BaseModel):
    """Common metadata model."""

    pages_count: Optional[int] = Field(None, description="Number of pages")
    tables_count: Optional[int] = Field(None, description="Number of tables")
    filename: Optional[str] = Field(None, description="Original filename")
    extraction_method: Optional[str] = Field(None, description="Extraction method used")


class TableData(BaseModel):
    """Common table data model."""

    table_id: int = Field(description="Unique table identifier")
    page: int = Field(description="Page number")
    rows: int = Field(description="Number of rows")
    cols: int = Field(description="Number of columns")
    data: List[List[str]] = Field(description="2D array of table contents")
