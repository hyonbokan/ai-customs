from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from core.schemas.base_schemas import BaseRequest


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
