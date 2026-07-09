"""
Schema definitions for the Declaration Analyzer API.

Covers the request models, the validator result, and the service-layer result
envelopes for the multi-stage (comprehensive) analysis pipeline.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from core.llm.response_models import (
    DiscrepancyAnalysisResponse,
    FieldExtractionResponse,
    LLMFinalReport,
)
from core.schemas.base_schemas import BaseRequest


class DeclarationGoodsItem(BaseModel):
    """A single line item in a declaration. Extra fields are preserved."""

    model_config = ConfigDict(extra="allow")

    description: str = Field(description="Goods description")
    quantity: Optional[float] = Field(None, description="Quantity")
    value: Optional[float] = Field(None, description="Line value")


class DeclarationData(BaseModel):
    """Structured declaration data."""

    declaration_number: str = Field(description="Declaration number")
    importer: str = Field(description="Importer name")
    goods: List[DeclarationGoodsItem] = Field(description="List of goods")
    total_value: float = Field(description="Total value")


class CustomsDeclarationRequest(BaseRequest):
    """Request for declaration analysis."""

    declaration_data: DeclarationData
    reference_data: Optional[Dict[str, Any]] = None


class ValidationResult(BaseModel):
    """Result of validating raw declaration data."""

    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    normalized_data: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Service-layer result envelopes for the comprehensive analysis pipeline
# ---------------------------------------------------------------------------
class FieldExtractionOutcome(BaseModel):
    """Envelope around the field-extraction stage."""

    success: bool
    extracted_fields: Optional[FieldExtractionResponse] = None
    extraction_method: str
    content_processed: int = 0
    error: Optional[str] = None


class DiscrepancyOutcome(BaseModel):
    """Envelope around the discrepancy-analysis stage."""

    success: bool
    analysis_result: Optional[DiscrepancyAnalysisResponse] = None
    total_discrepancies: int = 0
    risk_level: str = "medium"
    analysis_method: str
    error: Optional[str] = None


class ReportOutcome(BaseModel):
    """Envelope around the report-generation stage."""

    success: bool
    final_report: Optional[LLMFinalReport] = None
    report_generation_method: str
    report_id: Optional[str] = None
    generation_date: Optional[str] = None
    error: Optional[str] = None


class PipelineLogEntry(BaseModel):
    """A single step recorded during comprehensive analysis."""

    timestamp: str
    stage: str
    message: str
    meta: Dict[str, Any] = Field(default_factory=dict)


class ProcessingSummary(BaseModel):
    fields_extracted: int = 0
    discrepancies_found: int = 0
    analysis_approach: str = "intelligent_llm_processing"


class ComprehensiveAnalysisResult(BaseModel):
    """Complete result of ``DeclarationAnalyzerService.analyze_comprehensive``."""

    success: bool
    analysis_id: str
    field_extraction: Optional[FieldExtractionOutcome] = None
    discrepancy_analysis: Optional[DiscrepancyOutcome] = None
    final_report: Optional[ReportOutcome] = None
    pipeline_log: List[PipelineLogEntry] = Field(default_factory=list)
    processing_summary: Optional[ProcessingSummary] = None
    processing_time_seconds: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
