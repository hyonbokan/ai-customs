"""
Pydantic models for structured LLM output.

Each model mirrors the JSON shape requested by the corresponding prompt in
``core/llm/pipeline_prompts.py`` / ``prompt_templates.py``. They are passed to
``send_prompt_to_llm_async(response_model=...)``, which forwards the JSON schema
to the inference server (guided decoding) and validates the response.

Conventions for LLM-facing schemas:
- Plain ``BaseModel`` subclasses (supported by both self-hosted guided decoding
  and proprietary structured-output APIs).
- ``model_config = ConfigDict(extra="forbid")`` so the schema emits
  ``additionalProperties: false`` (required for OpenAI strict mode).
- Every field is required with NO default. A default would drop the field from
  the schema's ``required`` list, which breaks strict extraction. Note that
  ``Field(description=...)`` is metadata, not a default — the field stays required.
"""

from typing import List

from pydantic import BaseModel, ConfigDict, Field

_STRICT = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Single-shot declaration analysis (used by /analyze-declaration)
# ---------------------------------------------------------------------------
class CustomsAnalysisIssue(BaseModel):
    """A single customs analysis issue."""

    model_config = _STRICT

    category: str = Field(description="Issue category (e.g. 'value', 'classification')")
    severity: str = Field(description="Severity: 'low', 'medium', or 'high'")
    description: str = Field(description="Detailed description of the issue")
    recommendation: str = Field(description="Recommended action to address the issue")


class CustomsAnalysisResponse(BaseModel):
    """Structured response for single-shot customs declaration analysis."""

    model_config = _STRICT

    discrepancies_found: int = Field(description="Number of discrepancies found")
    issues: List[CustomsAnalysisIssue] = Field(description="List of identified issues")
    recommendations: List[str] = Field(description="Overall recommendations")
    risk_level: str = Field(description="Overall risk level: 'low', 'medium', or 'high'")
    requires_inspection: bool = Field(description="Whether manual inspection is required")


# ---------------------------------------------------------------------------
# Pipeline stage 1: field extraction
# ---------------------------------------------------------------------------
class DocumentInfo(BaseModel):
    model_config = _STRICT

    type: str
    number: str
    date: str
    validity: str


class Party(BaseModel):
    model_config = _STRICT

    name: str
    address: str
    contact: str
    country: str


class Parties(BaseModel):
    model_config = _STRICT

    seller: Party
    buyer: Party
    consignee: Party


class ExtractedGoodsItem(BaseModel):
    model_config = _STRICT

    description: str
    hs_code: str
    quantity: str
    unit: str
    unit_price: str
    total_value: str
    currency: str
    origin_country: str
    brand: str
    model: str


class TradeTerms(BaseModel):
    model_config = _STRICT

    incoterms: str
    payment_terms: str
    delivery_terms: str
    port_of_loading: str
    port_of_discharge: str


class Financial(BaseModel):
    model_config = _STRICT

    total_invoice_value: str
    currency: str
    freight_cost: str
    insurance_cost: str
    other_charges: str


class AdditionalInfo(BaseModel):
    model_config = _STRICT

    certificates: List[str]
    special_notes: List[str]
    regulatory_info: List[str]
    transportation: str


class ExtractionMetadata(BaseModel):
    model_config = _STRICT

    extraction_method: str
    language_detected: str
    document_layout: str
    extraction_notes: List[str]


class FieldExtractionResponse(BaseModel):
    """Structured output of the field-extraction stage."""

    model_config = _STRICT

    document_info: DocumentInfo
    parties: Parties
    goods: List[ExtractedGoodsItem]
    trade_terms: TradeTerms
    financial: Financial
    additional_info: AdditionalInfo
    extraction_metadata: ExtractionMetadata


# ---------------------------------------------------------------------------
# Pipeline stage 2: discrepancy analysis
# ---------------------------------------------------------------------------
class AnalysisSummary(BaseModel):
    model_config = _STRICT

    total_discrepancies: int
    risk_level: str
    requires_inspection: bool
    automated_clearance_eligible: bool


class DiscrepancyItem(BaseModel):
    model_config = _STRICT

    category: str
    severity: str
    type: str
    description: str
    evidence: str
    recommendation: str


class ComplianceCheck(BaseModel):
    model_config = _STRICT

    documentation_complete: bool
    regulatory_compliant: bool
    licensing_required: bool
    restricted_goods: bool
    certificate_valid: bool


class ValueAnalysis(BaseModel):
    model_config = _STRICT

    total_declared_value: str
    expected_value_range: str
    value_variance: str
    pricing_concerns: List[str]
    currency_issues: List[str]


class RecommendationItem(BaseModel):
    model_config = _STRICT

    priority: str
    action: str
    rationale: str
    timeline: str


class InspectionRequirements(BaseModel):
    model_config = _STRICT

    physical_inspection: bool
    document_review: bool
    laboratory_testing: bool
    additional_documentation: bool
    special_procedures: List[str]


class AnalysisMetadata(BaseModel):
    model_config = _STRICT

    analysis_date: str
    data_quality: str
    analysis_method: str
    processing_notes: List[str]


class DiscrepancyAnalysisResponse(BaseModel):
    """Structured output of the discrepancy-analysis stage."""

    model_config = _STRICT

    analysis_summary: AnalysisSummary
    discrepancies: List[DiscrepancyItem]
    compliance_check: ComplianceCheck
    value_analysis: ValueAnalysis
    recommendations: List[RecommendationItem]
    inspection_requirements: InspectionRequirements
    analysis_metadata: AnalysisMetadata


# ---------------------------------------------------------------------------
# Pipeline stage 3: final report
# ---------------------------------------------------------------------------
class ReportHeader(BaseModel):
    model_config = _STRICT

    report_id: str
    generation_date: str
    report_type: str
    version: str


class ExecutiveSummary(BaseModel):
    model_config = _STRICT

    overall_assessment: str
    key_findings: List[str]
    risk_level: str
    clearance_recommendation: str


class DocumentOverview(BaseModel):
    model_config = _STRICT

    document_type: str
    document_number: str
    transaction_value: str
    parties_summary: str
    goods_summary: str
    origin_destination: str


class IssueDetail(BaseModel):
    model_config = _STRICT

    issue_id: str
    category: str
    severity: str
    description: str
    evidence: str
    impact: str
    recommendation: str


class DetailedFindings(BaseModel):
    model_config = _STRICT

    total_issues: int
    critical_issues: int
    high_priority_issues: int
    medium_priority_issues: int
    low_priority_issues: int
    issues_detail: List[IssueDetail]


class ComplianceStatus(BaseModel):
    model_config = _STRICT

    overall_compliance: str
    documentation_status: str
    regulatory_compliance: str
    licensing_status: str
    restricted_goods_check: str
    compliance_notes: List[str]


class ReportRecommendations(BaseModel):
    model_config = _STRICT

    immediate_actions: List[str]
    investigation_required: List[str]
    processing_recommendation: str
    follow_up_requirements: List[str]
    risk_mitigation: List[str]


class ProcessingDecision(BaseModel):
    model_config = _STRICT

    recommended_action: str
    justification: str
    required_procedures: List[str]
    timeline: str
    responsible_authority: str


class ReportMetadata(BaseModel):
    model_config = _STRICT

    processing_time: str
    data_sources: List[str]
    analysis_method: str
    quality_score: float
    reviewer_required: bool


class LLMFinalReport(BaseModel):
    """Structured final report produced by the reporting stage."""

    model_config = _STRICT

    report_header: ReportHeader
    executive_summary: ExecutiveSummary
    document_overview: DocumentOverview
    detailed_findings: DetailedFindings
    compliance_status: ComplianceStatus
    recommendations: ReportRecommendations
    processing_decision: ProcessingDecision
    report_metadata: ReportMetadata
