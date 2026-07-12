"""
Schema definitions for PDF Parser API using Docling.

These schemas define the structure for clean content extraction
that prepares documents for LLM consumption without field extraction.
"""

from typing import Any

from pydantic import BaseModel, Field

from core.schemas.base_schemas import BaseRequest, BaseResponse


class ParseOptions(BaseModel):
    """Typed options for PDF parsing."""

    enable_ocr: bool = Field(True, description="Enable OCR processing")
    enable_tables: bool = Field(True, description="Enable table extraction")
    ocr_languages: list[str] | None = Field(None, description="Languages for OCR")
    force_full_page_ocr: bool = Field(False, description="Force OCR on full pages")


class DirectParseRequest(BaseRequest):
    """Request for direct PDF parsing."""

    parse_options: ParseOptions | None = Field(None, description="Parsing configuration")


class DirectParseResponse(BaseResponse):
    """Response for direct PDF parsing."""

    text_content: str | None = Field(None, description="Extracted text")
    tables: list[dict[str, Any]] = Field(default_factory=list, description="Extracted tables")
    page_content: list[dict[str, Any]] = Field(default_factory=list, description="Page content")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Document metadata")
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
    processing_id: str | None = None
    text_content: str | None = None
    tables: list[dict[str, Any]] = Field(default_factory=list)
    page_content: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    ready_for_llm: bool = False
    processing_summary: dict[str, Any] | None = None
    processing_time_seconds: float | None = None
    error: str | None = None
