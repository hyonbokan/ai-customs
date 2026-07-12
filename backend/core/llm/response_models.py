"""
Pydantic models for structured LLM output.

Each model mirrors the JSON shape requested by the corresponding prompt
template in ``core/llm/prompts/``. They are passed to
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
- A field the document may not state is ``X | None`` — still without a default,
  which keeps it required while letting the model emit null for absent values
  (strict mode supports the nullable union).
"""

from pydantic import BaseModel, ConfigDict, Field

_STRICT = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Pipeline stage 1: field extraction
#
# Field descriptions are part of the JSON schema the model decodes against, so
# they are extraction instructions, not documentation. Values are copied as
# written in the document; null means the document does not state the field.
# ---------------------------------------------------------------------------
class DocumentInfo(BaseModel):
    model_config = _STRICT

    type: str = Field(description="Document type as titled, e.g. 'invoice', 'valuation report'")
    number: str | None = Field(description="Document number/reference")
    date: str | None = Field(description="Issue date as written")
    validity: str | None = Field(description="Validity period as written")


class Party(BaseModel):
    model_config = _STRICT

    name: str | None = Field(description="Full name as written")
    address: str | None = Field(description="Address as written")
    contact: str | None = Field(description="Phone/email as written")
    country: str | None = Field(description="Country")


class Parties(BaseModel):
    """seller = exporter; buyer = importer; consignee only if different from the buyer."""

    model_config = _STRICT

    seller: Party
    buyer: Party
    consignee: Party


class ExtractedGoodsItem(BaseModel):
    model_config = _STRICT

    description: str = Field(description="Goods description as written")
    hs_code: str | None = Field(description="HS / tariff code as written")
    quantity: str | None = Field(description="Quantity as written")
    unit: str | None = Field(description="Unit of measure")
    unit_price: str | None = Field(description="Unit price as written")
    total_value: str | None = Field(description="Line total value as written")
    currency: str | None = Field(description="Currency of the line values")
    origin_country: str | None = Field(description="Country of origin")
    brand: str | None = Field(description="Brand/make")
    model: str | None = Field(description="Model/version")


class TradeTerms(BaseModel):
    model_config = _STRICT

    incoterms: str | None = Field(description="Incoterm, e.g. 'FOB', 'CIF', 'CFR'")
    payment_terms: str | None = Field(description="Payment terms as written")
    delivery_terms: str | None = Field(description="Delivery terms as written")
    port_of_loading: str | None = Field(description="Port/country of loading")
    port_of_discharge: str | None = Field(description="Port/country of discharge")


class ValueSet(BaseModel):
    """One valuation basis: its cost components and the total the document states for it."""

    model_config = _STRICT

    fob_value: str | None = Field(description="FOB/goods value of THIS basis as written")
    freight_cost: str | None = Field(description="Freight of THIS basis as written")
    insurance_cost: str | None = Field(description="Insurance of THIS basis as written")
    other_charges: str | None = Field(description="Other charges of THIS basis as written")
    total: str | None = Field(description="Total the document states for THIS basis")


class DeclaredValues(ValueSet):
    """Values stated by the seller or importer: invoice amounts, or the section where the
    document restates what the trader's own paperwork presented. Never put values set by
    an authority here. All null if the document has no declared set."""


class AssessedValues(ValueSet):
    """Values determined by an authority (customs or an inspection company): a valuation
    opinion, an official taxable-value breakdown, or any figure the document attributes to
    the assessor rather than the trader. Never put the trader's own invoice figures here.
    All null if the document has no assessed set."""


class Financial(BaseModel):
    """Monetary values, split by valuation basis.

    Inspection documents often carry TWO value sets side by side: what the
    seller/importer declared and what the inspection company assessed. Mixing
    figures across the two sets corrupts every downstream arithmetic check, so
    each set is extracted into its own group. (The per-basis guidance lives in
    the DeclaredValues/AssessedValues docstrings: OpenAI strict mode rejects a
    description alongside a $ref, so it must sit on the referenced model.)
    """

    model_config = _STRICT

    currency: str | None = Field(description="Currency of the values, e.g. 'USD', 'XAF'")
    declared: DeclaredValues
    assessed: AssessedValues


class AdditionalInfo(BaseModel):
    model_config = _STRICT

    certificates: list[str] = Field(description="Certificates mentioned (origin, quality, …)")
    special_notes: list[str] = Field(
        description="Special notes, observations, or remarks stated on the document"
    )
    regulatory_info: list[str] = Field(description="Regulatory references/requirements mentioned")
    transportation: str | None = Field(description="Transport details (mode, vessel, container)")


class ExtractionMetadata(BaseModel):
    model_config = _STRICT

    extraction_method: str
    language_detected: str
    document_layout: str
    extraction_notes: list[str]


class FieldExtractionResponse(BaseModel):
    """Structured output of the field-extraction stage."""

    model_config = _STRICT

    document_info: DocumentInfo
    parties: Parties
    goods: list[ExtractedGoodsItem]
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
    pricing_concerns: list[str]
    currency_issues: list[str]


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
    special_procedures: list[str]


class AnalysisMetadata(BaseModel):
    model_config = _STRICT

    analysis_date: str
    data_quality: str
    analysis_method: str
    processing_notes: list[str]


class DiscrepancyAnalysisResponse(BaseModel):
    """Structured output of the discrepancy-analysis stage."""

    model_config = _STRICT

    analysis_summary: AnalysisSummary
    discrepancies: list[DiscrepancyItem]
    compliance_check: ComplianceCheck
    value_analysis: ValueAnalysis
    recommendations: list[RecommendationItem]
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
    key_findings: list[str]
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
    issues_detail: list[IssueDetail]


class ComplianceStatus(BaseModel):
    model_config = _STRICT

    overall_compliance: str
    documentation_status: str
    regulatory_compliance: str
    licensing_status: str
    restricted_goods_check: str
    compliance_notes: list[str]


class ReportRecommendations(BaseModel):
    model_config = _STRICT

    immediate_actions: list[str]
    investigation_required: list[str]
    processing_recommendation: str
    follow_up_requirements: list[str]
    risk_mitigation: list[str]


class ProcessingDecision(BaseModel):
    model_config = _STRICT

    recommended_action: str
    justification: str
    required_procedures: list[str]
    timeline: str
    responsible_authority: str


class ReportMetadata(BaseModel):
    model_config = _STRICT

    processing_time: str
    data_sources: list[str]
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
