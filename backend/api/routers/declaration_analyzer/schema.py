from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from core.schemas.base_schemas import BaseRequest, BaseResponse


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
    """Analysis result model."""
    task_id: str
    status: str
    discrepancies_found: int
    analysis_report: Optional[Dict[str, Any]] = None  # TODO: Type this further 