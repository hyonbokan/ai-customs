from pydantic import BaseModel
from typing import Dict, Any, Optional


class CustomsDeclarationRequest(BaseModel):
    """Request model for customs declaration analysis."""
    declaration_data: Dict[str, Any]
    reference_data: Optional[Dict[str, Any]] = None


class AnalysisResult(BaseModel):
    """Result model for completed analysis."""
    task_id: str
    status: str
    discrepancies_found: int
    analysis_report: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None


class AnalysisStatus(BaseModel):
    """Status model for ongoing analysis."""
    task_id: str
    status: str  # "queued", "processing", "completed", "failed"
    progress: Optional[int] = None
    estimated_completion: Optional[str] = None 