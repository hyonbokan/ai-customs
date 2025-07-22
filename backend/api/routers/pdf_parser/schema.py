"""
Schema definitions for PDF Parser API using Docling.

These schemas define the structure for clean content extraction
that prepares documents for LLM consumption without field extraction.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List


class PDFParseRequest(BaseModel):
    """Request model for PDF parsing using Docling."""
    file_url: Optional[str] = Field(None, description="URL to PDF file to parse")
    file_content: Optional[str] = Field(None, description="Base64 encoded PDF content")
    parse_options: Optional[Dict[str, Any]] = Field(
        None, 
        description="Optional parsing configuration (OCR settings, table extraction, etc.)"
    )

    class Config:
        schema_extra = {
            "example": {
                "file_url": "https://example.com/invoice.pdf",
                "parse_options": {
                    "enable_ocr": True,
                    "enable_tables": True,
                    "ocr_languages": ["en", "es"]
                }
            }
        }


class TableData(BaseModel):
    """Structured table data extracted from document."""
    table_id: int = Field(description="Unique identifier for the table")
    page: int = Field(description="Page number where table appears")
    rows: int = Field(description="Number of rows in table")
    cols: int = Field(description="Number of columns in table")
    data: List[List[str]] = Field(description="2D array of table cell contents")


class PageContent(BaseModel):
    """Content organized by page for document structure."""
    page: int = Field(description="Page number")
    content: Dict[str, List[Dict[str, Any]]] = Field(
        description="Page content organized by type (texts, tables, pictures)"
    )


class DocumentMetadata(BaseModel):
    """Metadata extracted from the document."""
    pages_count: Optional[int] = Field(None, description="Number of pages in document")
    tables_count: Optional[int] = Field(None, description="Number of tables found")
    text_blocks_count: Optional[int] = Field(None, description="Number of text blocks found")
    extraction_method: Optional[str] = Field(None, description="Method used for extraction")
    filename: Optional[str] = Field(None, description="Original filename")
    ready_for_llm: Optional[bool] = Field(None, description="Whether content is ready for LLM analysis")


class EnhancedStructuredData(BaseModel):
    """Enhanced structured data with clean content for LLM consumption."""
    text_content: str = Field(description="Clean extracted text content")
    tables: List[TableData] = Field(description="Structured table data")
    page_content: List[PageContent] = Field(description="Content organized by pages")
    metadata: DocumentMetadata = Field(description="Document metadata")
    extraction_approach: str = Field(
        description="Approach used for extraction",
        default="docling_clean_content_for_llm"
    )


class PDFParseResult(BaseModel):
    """Result model for PDF parsing with enhanced Docling output."""
    task_id: str = Field(description="Task identifier")
    status: str = Field(description="Parsing status (completed, failed, etc.)")
    extracted_text: Optional[str] = Field(None, description="Clean extracted text")
    structured_data: Optional[EnhancedStructuredData] = Field(
        None, 
        description="Enhanced structured data for LLM consumption"
    )
    metadata: Optional[Dict[str, str]] = Field(None, description="Basic parsing metadata")

    class Config:
        schema_extra = {
            "example": {
                "task_id": "parse_task_123",
                "status": "completed",
                "extracted_text": "COMMERCIAL INVOICE\nInvoice No: INV-2024-0012...",
                "structured_data": {
                    "text_content": "Clean extracted text content",
                    "tables": [
                        {
                            "table_id": 0,
                            "page": 1,
                            "rows": 2,
                            "cols": 4,
                            "data": [
                                ["Description", "Qty", "Unit Price", "Total"],
                                ["Electronic Components", "100", "$150.00", "$15,000.00"]
                            ]
                        }
                    ],
                    "page_content": [
                        {
                            "page": 1,
                            "content": {
                                "texts": [
                                    {"text": "COMMERCIAL INVOICE", "type": "title"}
                                ],
                                "tables": [{"table_id": 0}],
                                "pictures": []
                            }
                        }
                    ],
                    "metadata": {
                        "pages_count": 1,
                        "tables_count": 1,
                        "extraction_method": "docling",
                        "ready_for_llm": True
                    },
                    "extraction_approach": "docling_clean_content_for_llm"
                },
                "metadata": {
                    "pages": "1",
                    "extraction_method": "docling",
                    "ready_for_llm": "true"
                }
            }
        }


class PDFParseStatus(BaseModel):
    """Status model for PDF parsing tasks."""
    task_id: str = Field(description="Task identifier")
    status: str = Field(description="Current status: queued, processing, completed, failed")
    progress: Optional[int] = Field(None, description="Progress percentage (0-100)")
    pages_processed: Optional[int] = Field(None, description="Number of pages processed")
    total_pages: Optional[int] = Field(None, description="Total number of pages")

    class Config:
        schema_extra = {
            "example": {
                "task_id": "parse_task_123",
                "status": "processing",
                "progress": 75,
                "pages_processed": 3,
                "total_pages": 4
            }
        }


class DirectParseRequest(BaseModel):
    """Request model for direct (synchronous) PDF parsing."""
    file_url: Optional[str] = Field(None, description="URL to PDF file")
    file_content: Optional[str] = Field(None, description="Base64 encoded PDF content")
    
    class Config:
        schema_extra = {
            "example": {
                "file_url": "https://example.com/customs_declaration.pdf"
            }
        }


class DirectParseResponse(BaseModel):
    """Response model for direct PDF parsing."""
    success: bool = Field(description="Whether parsing was successful")
    text_content: Optional[str] = Field(None, description="Extracted text content")
    tables: Optional[List[TableData]] = Field(None, description="Extracted table data")
    page_content: Optional[List[PageContent]] = Field(None, description="Page-organized content")
    metadata: Optional[DocumentMetadata] = Field(None, description="Document metadata")
    ready_for_llm: bool = Field(description="Whether content is ready for LLM analysis")
    error: Optional[str] = Field(None, description="Error message if parsing failed")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "text_content": "COMMERCIAL INVOICE\nInvoice No: INV-2024-0012...",
                "tables": [
                    {
                        "table_id": 0,
                        "page": 1,
                        "rows": 2,
                        "cols": 4,
                        "data": [
                            ["Description", "Qty", "Unit Price", "Total"],
                            ["Electronic Components", "100", "$150.00", "$15,000.00"]
                        ]
                    }
                ],
                "ready_for_llm": True,
                "error": None
            }
        } 