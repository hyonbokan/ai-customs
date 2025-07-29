"""
PDF Parser API Routes using Docling for clean content extraction.

These routes provide clean, structured content preparation for LLM analysis
without regex-based field extraction (that's the LLM's job).
"""

from fastapi import APIRouter, HTTPException  # type: ignore
from fastapi.responses import JSONResponse  # type: ignore

from core.schemas.api_response_schema import SuccessResponse, ErrorResponse
from api.routers.pdf_parser.schema import (
    PDFParseRequest, 
    PDFParseResult, 
    PDFParseStatus,
    DirectParseRequest,
    DirectParseResponse
)
from api.routers.pdf_parser.service import PDFParserService

router = APIRouter(tags=["pdf-parser"], prefix="/pdf-parser")


@router.post("/parse-pdf", response_model=PDFParseResult, summary="Parse PDF (Background Task)")
async def submit_pdf_parse(request: PDFParseRequest):
    """
    Submit a PDF document for parsing using Docling.
    
    **Processing Approach:**
    - PDF Parser: Extracts clean text, tables, and document structure
    - LLM Service: Handles intelligent field extraction and analysis
    - No Regex: Language agnostic, format flexible, LLM-powered
    
    **Returns immediately** while processing happens in background.
    Use the returned task_id to check status and retrieve results.
    """
    try:
        task_id = PDFParserService.submit_parse_request(
            request.file_url,
            request.file_content,
            request.parse_options
        )
        
        return SuccessResponse(
            data={
                "task_id": task_id,
                "status": "queued",
                "message": "PDF parsing started using Docling for clean content extraction",
                "approach": "PDF extracts content, LLM extracts intelligence"
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit parsing request: {str(e)}")


@router.get("/parse-status/{task_id}", response_model=PDFParseStatus, summary="Check Parse Status")
async def get_parse_status(task_id: str):
    """Check the status of a PDF parsing task."""
    try:
        status = PDFParserService.get_parse_status(task_id)
        return SuccessResponse(data=status.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get("/parse-result/{task_id}", response_model=PDFParseResult, summary="Get Parse Result")
async def get_parse_result(task_id: str):
    """
    Get the result of a completed PDF parsing.
    
    **Returns clean content structure ready for LLM consumption:**
    - Clean extracted text
    - Structured table data  
    - Page-organized content
    - Document metadata
    - No extracted fields (that's for the LLM to handle)
    """
    try:
        result = PDFParserService.get_parse_result(task_id)
        
        if result:
            return SuccessResponse(
                data=result.dict(),
                message="Clean content ready for LLM field extraction and analysis"
            )
        else:
            return SuccessResponse(
                data={"message": "PDF parsing not found or still processing"}
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get result: {str(e)}")


@router.post("/parse-direct", response_model=DirectParseResponse, summary="Parse PDF (Direct/Sync)")
async def parse_pdf_direct(request: DirectParseRequest):
    """
    Parse PDF document directly (synchronous) using Docling.
    
    **Use this for:**
    - Immediate results needed
    - Single document processing
    - Development and testing
    
    **Processing Philosophy:**
    1. **PDF Parser Role**: Extract clean text, tables, document structure
    2. **LLM Role**: Intelligent field extraction, analysis, discrepancy detection  
    3. **No Field Extraction**: Avoids brittle regex patterns, handles any language/format
    
    **Returns immediately** with clean content ready for LLM consumption.
    """
    try:
        result = await PDFParserService.parse_document_sync(
            request.file_url, 
            request.file_content
        )
        
        if result["success"]:
            return DirectParseResponse(
                success=True,
                text_content=result["text_content"],
                tables=result["tables"],
                page_content=result["page_content"],
                metadata=result["metadata"],
                ready_for_llm=result["ready_for_llm"],
                error=None
            )
        else:
            # Return HTTP 422 on parser failure so client code can rely on HTTP semantics
            raise HTTPException(status_code=422, detail=result.get("error", "PDF parsing failed"))
            
    except Exception as e:
        # Return HTTP 500 for unexpected errors
        raise HTTPException(status_code=500, detail=f"PDF parsing error: {str(e)}")


@router.get("/capabilities", response_model=SuccessResponse, summary="Get Parser Capabilities")
async def get_parser_capabilities():
    """
    Get information about PDF parser capabilities and configuration.
    """
    from config import config
    
    capabilities = {
        "extraction_method": "docling",
        "approach": "clean_content_for_llm_consumption",
        "features": {
            "ocr_enabled": config.pipeline.PDF_ENABLE_OCR,
            "table_extraction": config.pipeline.PDF_ENABLE_TABLES,
            "supported_languages": config.pipeline.PDF_OCR_LANGUAGES,
            "supported_formats": config.pipeline.PDF_SUPPORTED_FORMATS,
            "max_file_size_mb": config.pipeline.PDF_MAX_FILE_SIZE_MB
        },
        "processing_philosophy": {
            "pdf_parser_role": "Extract clean text, tables, and document structure",
            "llm_role": "Intelligent field extraction, analysis, and discrepancy detection",
            "no_regex_extraction": "Field extraction delegated to LLM for accuracy and flexibility"
        },
        "output_structure": {
            "text_content": "Clean extracted text ready for LLM analysis",
            "tables": "Structured table data with cells and positioning",
            "page_content": "Content organized by pages preserving document structure",
            "metadata": "Document information and extraction statistics"
        },
        "integration_flow": [
            "1. PDF Parser: Downloads → Docling processing → Clean content extraction",
            "2. LLM Service: Structured content → Field extraction → Discrepancy analysis",
            "3. No field extraction in PDF: Avoids brittle patterns, handles any language"
        ]
    }
    
    return SuccessResponse(
        data=capabilities,
        message="PDF parser uses Docling for clean content preparation, LLM handles intelligence"
    )


@router.post("/example-llm-input", response_model=SuccessResponse, summary="Example: LLM Input Format")
async def show_example_llm_input():
    """
    Show example of how parsed PDF content should be consumed by LLM services.
    
    **Demonstrates the clean handoff from PDF parser to LLM:**
    - PDF Parser provides structured, clean content
    - LLM extracts fields intelligently without regex patterns
    - Language agnostic, format flexible approach
    """
    
    example_pdf_output = {
        "text_content": """COMMERCIAL INVOICE
        
Invoice No: INV-2024-0012
Date: January 15, 2024

From: ABC Electronics Ltd
      123 Industrial Park
      Shenzhen, China

To: XYZ Importers Inc
    456 Business Ave
    Los Angeles, CA, USA

Description          Qty    Unit Price    Total
Electronic Components 100   $150.00      $15,000.00

Total Amount: $15,000.00 USD
Payment Terms: Net 30
Origin: China""",
        "tables": [
            {
                "table_id": 0,
                "page": 1,
                "data": [
                    ["Description", "Qty", "Unit Price", "Total"],
                    ["Electronic Components", "100", "$150.00", "$15,000.00"]
                ]
            }
        ],
        "metadata": {
            "pages_count": 1,
            "tables_count": 1,
            "extraction_method": "docling",
            "ready_for_llm": True
        }
    }
    
    example_llm_extraction = {
        "fields_extracted_by_llm": {
            "invoice_number": "INV-2024-0012",
            "invoice_date": "January 15, 2024", 
            "seller": "ABC Electronics Ltd, Shenzhen, China",
            "buyer": "XYZ Importers Inc, Los Angeles, CA, USA",
            "total_amount": 15000.00,
            "currency": "USD",
            "items": [
                {
                    "description": "Electronic Components",
                    "quantity": 100,
                    "unit_price": 150.00,
                    "total": 15000.00
                }
            ],
            "origin_country": "China"
        },
        "extraction_confidence": 0.95,
        "note": "LLM extracts fields intelligently without regex patterns"
    }
    
    return SuccessResponse(
        data={
            "pdf_parser_output": example_pdf_output,
            "llm_consumption_example": example_llm_extraction,
            "benefits": [
                "Language agnostic - no hardcoded patterns",
                "Format flexible - LLM handles any layout",
                "Maintainable - no brittle regex to update",
                "Intelligent - LLM understands context and relationships",
                "Scalable - works with documents from any country"
            ],
            "workflow": "PDF Parser (clean content) → LLM Service (intelligent analysis)"
        },
        message="This shows the clean handoff from PDF extraction to LLM intelligence"
    ) 