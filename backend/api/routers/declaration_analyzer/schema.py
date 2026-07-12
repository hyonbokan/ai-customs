"""
Schema definitions for the Declaration Analyzer service.

Service-layer result envelopes for the multi-stage (comprehensive) analysis
pipeline.
"""

from typing import Any

from pydantic import BaseModel, Field

from core.llm.response_models import (
    DiscrepancyAnalysisResponse,
    FieldExtractionResponse,
    LLMFinalReport,
)


class FieldExtractionOutcome(BaseModel):
    """Envelope around the field-extraction stage."""

    success: bool
    extracted_fields: FieldExtractionResponse | None = None
    extraction_method: str
    content_processed: int = 0
    error: str | None = None


class DiscrepancyOutcome(BaseModel):
    """Envelope around the discrepancy-analysis stage."""

    success: bool
    analysis_result: DiscrepancyAnalysisResponse | None = None
    total_discrepancies: int = 0
    risk_level: str = "medium"
    analysis_method: str
    error: str | None = None


class ReportOutcome(BaseModel):
    """Envelope around the report-generation stage."""

    success: bool
    final_report: LLMFinalReport | None = None
    report_generation_method: str
    report_id: str | None = None
    generation_date: str | None = None
    error: str | None = None


class PipelineLogEntry(BaseModel):
    """A single step recorded during comprehensive analysis."""

    timestamp: str
    stage: str
    message: str
    meta: dict[str, Any] = Field(default_factory=dict)


class ProcessingSummary(BaseModel):
    fields_extracted: int = 0
    discrepancies_found: int = 0
    analysis_approach: str = "intelligent_llm_processing"


class ComprehensiveAnalysisResult(BaseModel):
    """Complete result of ``DeclarationAnalyzerService.analyze_comprehensive``."""

    success: bool
    analysis_id: str
    field_extraction: FieldExtractionOutcome | None = None
    discrepancy_analysis: DiscrepancyOutcome | None = None
    final_report: ReportOutcome | None = None
    pipeline_log: list[PipelineLogEntry] = Field(default_factory=list)
    processing_summary: ProcessingSummary | None = None
    processing_time_seconds: float = 0.0
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
