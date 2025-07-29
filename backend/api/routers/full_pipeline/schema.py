"""
Schema definitions for Full Pipeline API.

These schemas define the structure for the complete customs analysis pipeline
orchestrating PDF parsing, LLM analysis, and final report generation.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from core.schemas.base_schemas import BaseRequest, BaseResponse, BaseStatus, Metadata, TableData


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

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "file_url": "https://example.com/commercial_invoice.pdf",
                    "reference_data": {
                        "expected_goods": ["electronics", "components"],
                        "supplier_database": {"known_suppliers": ["ABC Electronics Ltd"]},
                        "market_prices": {"electronics": {"min": 100, "max": 200}}
                    },
                    "processing_options": {
                        "enable_ocr": True,
                        "enable_tables": True,
                        "ocr_languages": ["en", "es"],
                        "confidence_threshold": 0.8,
                        "deep_analysis": True,
                        "generate_report": True
                    }
                }
            ]
        }
    }


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

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "task_id": "pipeline_task_123",
                    "status": "processing",
                    "message": "Pipeline processing started successfully",
                    "pipeline_stages": {
                        "pdf_extraction": {
                            "stage": 1,
                            "name": "PDF Content Extraction",
                            "status": "completed",
                            "progress": 100,
                            "output_ready": True
                        },
                        "llm_analysis": {
                            "stage": 2,
                            "name": "LLM Analysis",
                            "status": "processing",
                            "progress": 60,
                            "output_ready": False
                        },
                        "report_generation": {
                            "stage": 3,
                            "name": "Report Generation",
                            "status": "pending",
                            "progress": 0,
                            "output_ready": False
                        }
                    },
                    "error": None
                }
            ]
        }
    }


class PipelineStatus(BaseStatus):
    overall_progress: int
    current_stage: str
    estimated_completion: Optional[str] = None
    stages: PipelineStages
    processing_time: Optional[str] = None


class PDFExtractionResult(BaseModel):
    """Results from PDF extraction stage."""
    success: bool = Field(description="Whether extraction was successful")
    text_content: Optional[str] = Field(None, description="Extracted text content")
    tables: Optional[List[Dict[str, Any]]] = Field(None, description="Extracted table data")
    page_content: Optional[List[Dict[str, Any]]] = Field(None, description="Page-organized content")
    metadata: Metadata
    extraction_time: Optional[str] = Field(None, description="Time taken for extraction")


class LLMAnalysisResult(BaseModel):
    """Results from LLM analysis stage."""
    success: bool = Field(description="Whether analysis was successful")
    extracted_fields: Optional[Dict[str, Any]] = Field(None, description="Extracted structured fields")
    discrepancies: Optional[List[Dict[str, Any]]] = Field(None, description="Found discrepancies")
    analysis_summary: Optional[Dict[str, Any]] = Field(None, description="Analysis summary")
    confidence_score: Optional[float] = Field(None, description="Overall confidence score")
    analysis_time: Optional[str] = Field(None, description="Time taken for analysis")


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
    pdf_extraction: PDFExtractionResult = Field(description="PDF extraction results")
    llm_analysis: LLMAnalysisResult = Field(description="LLM analysis results")
    final_report: Optional[FinalReport] = Field(None, description="Final comprehensive report")
    pipeline_metadata: Dict[str, Any] = Field(description="Pipeline processing metadata")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "task_id": "pipeline_task_123",
                    "overall_status": "completed",
                    "processing_time": "2 minutes 30 seconds",
                    "pdf_extraction": {
                        "success": True,
                        "text_content": "COMMERCIAL INVOICE\nInvoice No: INV-2024-0012...",
                        "tables": [{"table_id": 0, "data": [...]}],
                        "extraction_time": "45 seconds"
                    },
                    "llm_analysis": {
                        "success": True,
                        "extracted_fields": {"invoice_number": "INV-2024-0012", "total_value": 34325.00},
                        "discrepancies": [{"category": "value_assessment", "severity": "medium"}],
                        "confidence_score": 0.85,
                        "analysis_time": "1 minute 20 seconds"
                    },
                    "final_report": {
                        "report_id": "RPT-2024-0012",
                        "generation_date": "2024-01-15T10:30:00Z",
                        "executive_summary": {"risk_level": "medium", "clearance_recommendation": "inspect"},
                        "recommendations": {"immediate_actions": ["Verify pricing documentation"]}
                    },
                    "pipeline_metadata": {
                        "total_processing_time": "2 minutes 30 seconds",
                        "services_used": ["pdf_parser", "declaration_analyzer", "full_pipeline"],
                        "data_quality_score": 0.92
                    }
                }
            ]
        }
    } 