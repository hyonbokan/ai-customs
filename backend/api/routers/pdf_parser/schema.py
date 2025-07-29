"""
Schema definitions for PDF Parser API using Docling.

These schemas define the structure for clean content extraction
that prepares documents for LLM consumption without field extraction.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
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
    tables: Optional[List[TableData]] = Field(None, description="Extracted tables")
    page_content: Optional[List[PageContent]] = Field(None, description="Page content")
    metadata: Optional[Metadata] = Field(None, description="Document metadata")
    ready_for_llm: bool = Field(False, description="Ready for LLM analysis") 