"""
Schema definitions for Full Pipeline API.

These schemas define the structure for the complete customs analysis pipeline
orchestrating PDF parsing, LLM analysis, and final report generation.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from api.routers.pdf_parser.schema import PDFParseResult
from api.routers.declaration_analyzer.schema import AnalysisResult
from core.schemas.base_schemas import BaseRequest, BaseResponse, BaseStatus


class ProcessingOptions(BaseModel):
    """Optional processing configuration for the pipeline."""
    enable_ocr: Optional[bool] = Field(None, description="Enable OCR processing for PDF")
    enable_tables: Optional[bool] = Field(None, description="Enable table extraction")
    ocr_languages: Optional[List[str]] = Field(None, description="OCR languages to use")
    confidence_threshold: Optional[float] = Field(None, description="LLM confidence threshold")
    deep_analysis: Optional[bool] = Field(None, description="Enable deep analysis mode")
    generate_report: Optional[bool] = Field(True, description="Generate final report")


class FullPipelineRequest(BaseRequest):
    """Pipeline request model."""
    reference_data: Optional[Dict[str, Any]] = None
    processing_options: Optional[ProcessingOptions] = None


class PipelineStageStatus(BaseModel):
    """Status of individual pipeline stage."""
    stage: int = Field(description="Stage number")
    name: str = Field(description="Stage name")
    status: str = Field(description="Stage status (pending, processing, completed, failed)")
    progress: Optional[int] = Field(None, description="Progress percentage (0-100)")
    start_time: Optional[str] = Field(None, description="Stage start timestamp")
    end_time: Optional[str] = Field(None, description="Stage end timestamp")
    output_ready: Optional[bool] = Field(None, description="Whether stage output is ready")
    error_message: Optional[str] = Field(None, description="Error message if stage failed")


class PipelineStages(BaseModel):
    """Status of all pipeline stages."""
    pdf_extraction: PipelineStageStatus = Field(description="PDF extraction stage status")
    llm_analysis: PipelineStageStatus = Field(description="LLM analysis stage status")
    report_generation: PipelineStageStatus = Field(description="Report generation stage status")


class FullPipelineResponse(BaseResponse):
    task_id: Optional[str] = None
    status: str
    pipeline_stages: Optional[PipelineStages] = None
    complete_result: Optional[Dict[str, Any]] = None  # TODO: Type further


class PipelineStatus(BaseStatus):
    overall_progress: int
    current_stage: str
    estimated_completion: Optional[str] = None
    stages: PipelineStages
    processing_time: Optional[str] = None


class FinalReport(BaseModel):
    """Final comprehensive report."""
    report_id: str = Field(description="Unique report identifier")
    generation_date: str = Field(description="Report generation timestamp")
    executive_summary: str = Field(description="Executive summary")
    document_overview: Dict[str, Any] = Field(description="Document overview")
    detailed_findings: List[Dict[str, Any]] = Field(description="Detailed analysis findings")
    compliance_status: Dict[str, Any] = Field(description="Compliance assessment")
    recommendations: Dict[str, Any] = Field(description="Actionable recommendations")
    processing_decision: Dict[str, Any] = Field(description="Processing decision")
    report_metadata: Dict[str, Any] = Field(description="Report metadata")

class PipelineResult(BaseModel):
    """Complete pipeline result."""
    task_id: str = Field(description="Task identifier")
    overall_status: str = Field(description="Overall processing status")
    processing_time: str = Field(description="Total processing time")
    pdf_extraction: PDFParseResult = Field(description="PDF extraction results (reused from pdf_parser)")
    llm_analysis: AnalysisResult = Field(description="LLM analysis results (reused from declaration_analyzer)")
    final_report: Optional[FinalReport] = Field(None, description="Final comprehensive report")
    pipeline_metadata: Dict[str, Any] = Field(description="Pipeline processing metadata") 