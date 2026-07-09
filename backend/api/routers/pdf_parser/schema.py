"""
Schema definitions for PDF Parser API using Docling.

These schemas define the structure for clean content extraction
that prepares documents for LLM consumption without field extraction.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from core.schemas.base_schemas import BaseRequest, BaseResponse, BaseStatus, Metadata, TableData


class ParseOptions(BaseModel):
    """Typed options for PDF parsing."""

    enable_ocr: bool = Field(True, description="Enable OCR processing")
    enable_tables: bool = Field(True, description="Enable table extraction")
    ocr_languages: Optional[List[str]] = Field(None, description="Languages for OCR")
    force_full_page_ocr: bool = Field(False, description="Force OCR on full pages")


class PDFParseRequest(BaseRequest):
    """Request model for PDF parsing."""

    parse_options: Optional[ParseOptions] = Field(None, description="Parsing configuration")


class PageContent(BaseModel):
    """Content organized by page."""

    page: int = Field(description="Page number")
    texts: List[Dict[str, str]] = Field(description="Extracted text blocks")
    tables: List[Dict[str, int]] = Field(description="Table references")


class PDFParseResult(BaseResponse):
    """Result model for PDF parsing."""

    task_id: str = Field(description="Task identifier")
    status: str = Field(description="Parsing status")
    extracted_text: Optional[str] = Field(None, description="Clean extracted text")
    tables: Optional[List[TableData]] = Field(None, description="Extracted tables")
    page_content: Optional[List[PageContent]] = Field(None, description="Page-organized content")
    metadata: Optional[Metadata] = Field(None, description="Document metadata")


class PDFParseStatus(BaseStatus):
    """Status model for PDF parsing tasks."""

    pages_processed: Optional[int] = Field(None, description="Pages processed")
    total_pages: Optional[int] = Field(None, description="Total pages")


class DirectParseRequest(BaseRequest):
    """Request for direct PDF parsing."""

    parse_options: Optional[ParseOptions] = Field(None, description="Parsing configuration")


class DirectParseResponse(BaseResponse):
    """Response for direct PDF parsing."""

    text_content: Optional[str] = Field(None, description="Extracted text")
    tables: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted tables")
    page_content: List[Dict[str, Any]] = Field(default_factory=list, description="Page content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    ready_for_llm: bool = Field(False, description="Ready for LLM analysis")


# ---------------------------------------------------------------------------
# Service-layer result envelopes (returned by PDFParserService)
# ---------------------------------------------------------------------------
class PDFProcessingResult(BaseModel):
    """Result envelope returned by ``PDFParserService`` methods.

    ``tables``/``page_content``/``metadata`` stay as loose structures because
    they mirror the extractor's heterogeneous output, which is passed straight
    through to the LLM.
    """

    success: bool
    processing_id: Optional[str] = None
    text_content: Optional[str] = None
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    page_content: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    ready_for_llm: bool = False
    processing_summary: Optional[Dict[str, Any]] = None
    processing_time_seconds: Optional[float] = None
    error: Optional[str] = None


class PDFTaskResult(BaseModel):
    """Result stored by the background (Huey) PDF parsing task."""

    status: str
    extracted_text: str = ""
    structured_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
