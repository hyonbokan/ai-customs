from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from core.schemas.base_schemas import BaseRequest, BaseResponse
from core.llm.response_models import CustomsAnalysisResponse


class DeclarationData(BaseModel):
    """Structured declaration data."""
    declaration_number: str = Field(description="Declaration number")
    importer: str = Field(description="Importer name")
    goods: List[Dict[str, Any]] = Field(description="List of goods")
    total_value: float = Field(description="Total value")


class CustomsDeclarationRequest(BaseRequest):
    """Request for declaration analysis."""
    declaration_data: DeclarationData
    reference_data: Optional[Dict[str, Any]] = None


class AnalysisResult(BaseResponse):
    """Analysis result model for the declaration analyzer endpoint."""

    class PipelineLogEntry(BaseModel):
        timestamp: str = Field(description="Event timestamp (ISO format)")
        stage: str = Field(description="Pipeline stage name")
        message: str = Field(description="Human-readable message")
        meta: Optional[Dict[str, Any]] = Field(None, description="Optional structured metadata for the event")

    task_id: str
    status: str
    discrepancies_found: int
    # The main analysis report from the LLM, typed using our core response model
    analysis_report: Optional[CustomsAnalysisResponse] = None
    # Structured pipeline log for traceability
    pipeline_log: Optional[List[PipelineLogEntry]] = None