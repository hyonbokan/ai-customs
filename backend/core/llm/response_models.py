from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class CustomsAnalysisIssue(BaseModel):
    """Model for a single customs analysis issue."""
    category: str = Field(description="Category of the issue (e.g., 'value', 'classification', 'documentation')")
    severity: str = Field(description="Severity level: 'low', 'medium', or 'high'")
    description: str = Field(description="Detailed description of the issue")
    recommendation: str = Field(description="Recommended action to address the issue")


class CustomsAnalysisResponse(BaseModel):
    """Structured response model for customs declaration analysis."""
    discrepancies_found: int = Field(description="Number of discrepancies found")
    issues: List[CustomsAnalysisIssue] = Field(description="List of identified issues")
    confidence_score: float = Field(description="Confidence score between 0.0 and 1.0")
    recommendations: List[str] = Field(description="Overall recommendations")
    risk_level: str = Field(description="Overall risk level: 'low', 'medium', or 'high'")
    requires_inspection: bool = Field(description="Whether manual inspection is required")


class PDFExtractionResponse(BaseModel):
    """Structured response model for PDF data extraction."""
    
    class ImporterInfo(BaseModel):
        name: str
        address: str
        contact: Optional[str] = None
    
    class ExporterInfo(BaseModel):
        name: str
        address: str
        contact: Optional[str] = None
    
    class GoodsItem(BaseModel):
        description: str
        hs_code: str
        quantity: str
        unit: str
        value: str
        currency: str
        origin: Optional[str] = None
    
    declaration_number: str
    declaration_date: str
    importer: ImporterInfo
    exporter: ExporterInfo
    goods: List[GoodsItem]
    total_value: str
    currency: str
    transportation: Optional[str] = None
    extraction_confidence: float = Field(description="Confidence score for extraction quality")


class CityInfo(BaseModel):
    """Example response model for testing."""
    
    class LocationInfo(BaseModel):
        coordinates: Optional[List[float]] = None
        continent: Optional[str] = None
        region: Optional[str] = None
        description: Optional[str] = None
    
    class PopulationInfo(BaseModel):
        city_proper: Optional[int] = None
        urban_area: Optional[int] = None
        metropolitan_area: Optional[int] = None
        year: Optional[int] = None
        note: Optional[str] = None
    
    class GeographyInfo(BaseModel):
        river: Optional[str] = None
        elevation: Optional[str] = None
        climate: Optional[str] = None
        parks: Optional[List[str]] = None
    
    class EconomyInfo(BaseModel):
        sectors: Optional[List[str]] = None
        description: Optional[str] = None
    
    class TransportationInfo(BaseModel):
        airports: Optional[List[str]] = None
        rail: Optional[str] = None
        metro: Optional[str] = None
        road: Optional[str] = None
    
    city: str
    country: str
    location: Optional[LocationInfo] = None
    population: Optional[PopulationInfo] = None
    geography: Optional[GeographyInfo] = None
    key_features: Optional[List[str]] = None
    economy: Optional[EconomyInfo] = None
    transportation: Optional[TransportationInfo] = None 