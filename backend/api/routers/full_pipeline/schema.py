"""
Schema definitions for the Full Pipeline API.

Defines the request/response structure for the complete customs analysis
pipeline (PDF parsing -> LLM analysis -> final report).
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from api.routers.declaration_analyzer.schema import ComprehensiveAnalysisResult
from api.routers.pdf_parser.schema import PDFProcessingResult
from core.schemas.base_schemas import BaseRequest, BaseResponse


class ProcessingOptions(BaseModel):
    """Optional processing configuration for the pipeline."""

    enable_ocr: Optional[bool] = Field(None, description="Enable OCR processing for PDF")
    enable_tables: Optional[bool] = Field(None, description="Enable table extraction")
    ocr_languages: Optional[List[str]] = Field(None, description="OCR languages to use")
    deep_analysis: Optional[bool] = Field(None, description="Enable deep analysis mode")
    generate_report: Optional[bool] = Field(True, description="Generate final report")


class FullPipelineRequest(BaseRequest):
    """Pipeline request model (inherits file_url / file_content from BaseRequest)."""

    reference_data: Optional[Dict[str, Any]] = None
    processing_options: Optional[ProcessingOptions] = None


class PipelineReport(BaseModel):
    """Summary report combining the PDF and LLM stages."""

    report_id: str
    generation_date: str
    pdf_processing: str
    llm_analysis: str
    text_extracted: bool
    tables_found: int
    pages_processed: int
    discrepancies_found: int


class PipelineCompleteResult(BaseModel):
    """Full typed result of a successful pipeline run."""

    task_id: str
    overall_status: str
    processing_time: str
    pdf_extraction: PDFProcessingResult
    llm_analysis: ComprehensiveAnalysisResult
    final_report: PipelineReport


class FullPipelineResponse(BaseResponse):
    """Pipeline response with the complete result of a synchronous run."""

    task_id: Optional[str] = None
    status: str
    complete_result: Optional[PipelineCompleteResult] = None
