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


class FieldExtractionResponse(BaseModel):
    """Structured response model for field extraction from clean content."""

    class DocumentInfo(BaseModel):
        type: Optional[str] = None
        number: Optional[str] = None
        date: Optional[str] = None
        validity: Optional[str] = None

    class Party(BaseModel):
        name: Optional[str] = None
        address: Optional[str] = None
        contact: Optional[str] = None
        country: Optional[str] = None

    class Parties(BaseModel):
        seller: Optional['FieldExtractionResponse.Party'] = None
        buyer: Optional['FieldExtractionResponse.Party'] = None
        consignee: Optional['FieldExtractionResponse.Party'] = None

    class GoodsItem(BaseModel):
        description: Optional[str] = None
        hs_code: Optional[str] = None
        quantity: Optional[str] = None
        unit: Optional[str] = None
        unit_price: Optional[str] = None
        total_value: Optional[str] = None
        currency: Optional[str] = None
        origin_country: Optional[str] = None
        brand: Optional[str] = None
        model: Optional[str] = None

    class TradeTerms(BaseModel):
        incoterms: Optional[str] = None
        payment_terms: Optional[str] = None
        delivery_terms: Optional[str] = None
        port_of_loading: Optional[str] = None
        port_of_discharge: Optional[str] = None

    class Financial(BaseModel):
        total_invoice_value: Optional[str] = None
        currency: Optional[str] = None
        freight_cost: Optional[str] = None
        insurance_cost: Optional[str] = None
        other_charges: Optional[str] = None

    class AdditionalInfo(BaseModel):
        certificates: Optional[List[str]] = None
        special_notes: Optional[List[str]] = None
        regulatory_info: Optional[List[str]] = None
        transportation: Optional[str] = None

    class ExtractionMetadata(BaseModel):
        confidence_score: Optional[float] = None
        extraction_method: Optional[str] = None
        language_detected: Optional[str] = None
        document_layout: Optional[str] = None
        extraction_notes: Optional[List[str]] = None

    document_info: Optional[DocumentInfo] = None
    parties: Optional[Parties] = None
    goods: Optional[List[GoodsItem]] = None
    trade_terms: Optional[TradeTerms] = None
    financial: Optional[Financial] = None
    additional_info: Optional[AdditionalInfo] = None
    extraction_metadata: Optional[ExtractionMetadata] = None

class DiscrepancyAnalysisResponse(BaseModel):
    """Structured response model for discrepancy analysis stage."""

    class AnalysisSummary(BaseModel):
        total_discrepancies: int = Field(description="Total number of discrepancies found")
        risk_level: str = Field(description="Overall risk level: 'low', 'medium', 'high', or 'critical'")
        requires_inspection: bool = Field(description="Whether inspection is required")
        automated_clearance_eligible: bool = Field(description="Eligibility for automated clearance")

    class DiscrepancyItem(BaseModel):
        category: str
        severity: str
        type: str
        description: str
        evidence: str
        recommendation: str

    class ComplianceCheck(BaseModel):
        documentation_complete: bool
        regulatory_compliant: bool
        licensing_required: bool
        restricted_goods: bool
        certificate_valid: bool

    class ValueAnalysis(BaseModel):
        total_declared_value: str
        expected_value_range: str
        value_variance: str
        pricing_concerns: List[str]
        currency_issues: List[str]

    class RecommendationItem(BaseModel):
        priority: str
        action: str
        rationale: str
        timeline: str

    class InspectionRequirements(BaseModel):
        physical_inspection: bool
        document_review: bool
        laboratory_testing: bool
        additional_documentation: bool
        special_procedures: List[str]

    class AnalysisMetadata(BaseModel):
        analysis_date: str
        data_quality: str
        analysis_method: str
        processing_notes: List[str]

    analysis_summary: AnalysisSummary
    discrepancies: List[DiscrepancyItem]
    compliance_check: ComplianceCheck
    value_analysis: ValueAnalysis
    recommendations: List[RecommendationItem]
    inspection_requirements: InspectionRequirements
    analysis_metadata: AnalysisMetadata


class LLMFinalReport(BaseModel):
    """Structured final report produced by the LLM reporting stage."""

    class ReportHeader(BaseModel):
        report_id: str
        generation_date: str
        report_type: str
        version: str

    class ExecutiveSummary(BaseModel):
        overall_assessment: str
        key_findings: List[str]
        risk_level: str
        clearance_recommendation: str

    class DocumentOverview(BaseModel):
        document_type: str
        document_number: str
        transaction_value: str
        parties_summary: str
        goods_summary: str
        origin_destination: str

    class IssueDetail(BaseModel):
        issue_id: str
        category: str
        severity: str
        description: str
        evidence: str
        impact: str
        recommendation: str

    class DetailedFindings(BaseModel):
        total_issues: int
        critical_issues: int
        high_priority_issues: int
        medium_priority_issues: int
        low_priority_issues: int
        issues_detail: List['LLMFinalReport.IssueDetail']

    class ComplianceStatus(BaseModel):
        overall_compliance: str
        documentation_status: str
        regulatory_compliance: str
        licensing_status: str
        restricted_goods_check: str
        compliance_notes: List[str]

    class Recommendations(BaseModel):
        immediate_actions: List[str]
        investigation_required: List[str]
        processing_recommendation: str
        follow_up_requirements: List[str]
        risk_mitigation: List[str]

    class ProcessingDecision(BaseModel):
        recommended_action: str
        justification: str
        required_procedures: List[str]
        timeline: str
        responsible_authority: str

    class ReportMetadata(BaseModel):
        processing_time: str
        data_sources: List[str]
        analysis_method: str
        reviewer_required: bool

    report_header: ReportHeader
    executive_summary: ExecutiveSummary
    document_overview: DocumentOverview
    detailed_findings: DetailedFindings
    compliance_status: ComplianceStatus
    recommendations: Recommendations
    processing_decision: ProcessingDecision
    report_metadata: ReportMetadata