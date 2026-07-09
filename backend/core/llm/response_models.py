from typing import List

from pydantic import BaseModel, Field


class CustomsAnalysisIssue(BaseModel):
    """Model for a single customs analysis issue."""

    category: str = Field(
        description="Category of the issue (e.g., 'value', 'classification', 'documentation')"
    )
    severity: str = Field(description="Severity level: 'low', 'medium', or 'high'")
    description: str = Field(description="Detailed description of the issue")
    recommendation: str = Field(description="Recommended action to address the issue")


class CustomsAnalysisResponse(BaseModel):
    """Structured response model for customs declaration analysis."""

    discrepancies_found: int = Field(description="Number of discrepancies found")
    issues: List[CustomsAnalysisIssue] = Field(description="List of identified issues")
    recommendations: List[str] = Field(description="Overall recommendations")
    risk_level: str = Field(description="Overall risk level: 'low', 'medium', or 'high'")
    requires_inspection: bool = Field(description="Whether manual inspection is required")
