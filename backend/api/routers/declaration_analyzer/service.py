"""
Declaration Analyzer Service for comprehensive customs analysis.

Provides LLM-based analysis and serves as the business-service implementation
for declaration analysis. It can be used independently (for the sync endpoint)
or as a stage in the full pipeline.

Architecture principle: the PDF parser provides clean content, the LLM provides
intelligent analysis. All LLM output is validated against the strict models in
``core/llm/response_models.py``.
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

from price_parser import Price

from api.routers.declaration_analyzer.schema import (
    ComprehensiveAnalysisResult,
    DiscrepancyOutcome,
    FieldExtractionOutcome,
    PipelineLogEntry,
    ProcessingSummary,
    ReportOutcome,
)
from config import config
from core.llm.llm_client import LLMClient, send_prompt_to_llm_async
from core.llm.prompts import load_prompt
from core.llm.response_models import (
    DiscrepancyAnalysisResponse,
    FieldExtractionResponse,
    LLMFinalReport,
)
from core.llm.system_messages import SystemPrompts
from core.utils.logger import logger


def _log(stage: str, message: str, **meta: Any) -> PipelineLogEntry:
    return PipelineLogEntry(
        timestamp=datetime.now().isoformat(), stage=stage, message=message, meta=meta
    )


class DeclarationAnalyzerService:
    """Complete Declaration Analyzer Service for comprehensive customs analysis."""

    async def analyze_comprehensive(
        self,
        pdf_content: str,
        tables: list | None = None,
        page_content: list | None = None,
        reference_data: dict[str, Any] | None = None,
    ) -> ComprehensiveAnalysisResult:
        """Run the multi-stage analysis: field extraction -> discrepancies -> report."""
        analysis_id = f"analysis_{uuid4().hex[:12]}"
        start_time = datetime.now()
        pipeline_log: list[PipelineLogEntry] = []

        try:
            if not pdf_content:
                raise ValueError("PDF content is required for analysis")

            logger.info(f"Starting comprehensive analysis: {analysis_id}")
            pipeline_log.append(_log("start", "Validated input", analysis_id=analysis_id))

            # Step 1: field extraction
            field_extraction = await self._extract_fields_intelligently(
                pdf_content, tables, page_content
            )
            pipeline_log.append(
                _log(
                    "field_extraction",
                    "Completed field extraction",
                    content_processed=field_extraction.content_processed,
                )
            )

            # Step 2: discrepancy analysis
            discrepancy_analysis = await self._analyze_discrepancies(
                field_extraction, reference_data
            )
            pipeline_log.append(
                _log(
                    "discrepancy_analysis",
                    "Completed discrepancy analysis",
                    total_discrepancies=discrepancy_analysis.total_discrepancies,
                )
            )

            # Step 3: final report
            final_report = await self._generate_comprehensive_report(
                field_extraction, discrepancy_analysis
            )
            pipeline_log.append(
                _log(
                    "report_generation", "Generated final report", report_id=final_report.report_id
                )
            )

            fields_extracted = (
                len(field_extraction.extracted_fields.goods)
                if field_extraction.extracted_fields
                else 0
            )
            processing_time = (datetime.now() - start_time).total_seconds()

            return ComprehensiveAnalysisResult(
                success=True,
                analysis_id=analysis_id,
                field_extraction=field_extraction,
                discrepancy_analysis=discrepancy_analysis,
                final_report=final_report,
                pipeline_log=pipeline_log,
                processing_summary=ProcessingSummary(
                    fields_extracted=fields_extracted,
                    discrepancies_found=discrepancy_analysis.total_discrepancies,
                ),
                processing_time_seconds=processing_time,
                metadata={
                    "service": "declaration_analyzer_service",
                    "processing_method": "comprehensive_llm_analysis",
                },
            )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Analysis failed for {analysis_id}: {e}")
            pipeline_log.append(_log("error", "Analysis failed", error=str(e)))
            return ComprehensiveAnalysisResult(
                success=False,
                analysis_id=analysis_id,
                error=str(e),
                pipeline_log=pipeline_log,
                processing_time_seconds=processing_time,
                metadata={"service": "declaration_analyzer_service", "exception_occurred": True},
            )

    async def _extract_fields_intelligently(
        self,
        pdf_content: str,
        tables: list | None = None,
        page_content: list | None = None,
    ) -> FieldExtractionOutcome:
        """Extract structured fields via the LLM (validated to FieldExtractionResponse)."""
        combined_content = pdf_content
        if tables:
            combined_content += f"\n\nTABLE DATA:\n{tables}"
        if page_content:
            combined_content += f"\n\nPAGE STRUCTURE:\n{page_content}"

        try:
            messages = LLMClient.create_messages(
                user_content=load_prompt(
                    "field_extraction.j2",
                    clean_content=combined_content,
                    document_type="customs_document",
                ),
                system_content=SystemPrompts.field_extraction(),
            )
            extracted = await send_prompt_to_llm_async(
                messages=messages,
                response_model=FieldExtractionResponse,
                temperature=config.llm.EXTRACTION_TEMPERATURE,
            )
            return FieldExtractionOutcome(
                success=True,
                extracted_fields=extracted,
                extraction_method="intelligent_llm_processing",
                content_processed=len(combined_content),
            )
        except Exception as e:
            logger.error(f"Field extraction failed: {e}")
            return FieldExtractionOutcome(
                success=False, error=str(e), extraction_method="failed_llm_processing"
            )

    async def _analyze_discrepancies(
        self,
        field_extraction: FieldExtractionOutcome,
        reference_data: dict[str, Any] | None = None,
    ) -> DiscrepancyOutcome:
        """Analyze discrepancies via the LLM (validated to DiscrepancyAnalysisResponse)."""
        extracted_data = (
            field_extraction.extracted_fields.model_dump()
            if field_extraction.extracted_fields
            else {}
        )
        try:
            messages = LLMClient.create_messages(
                user_content=load_prompt(
                    "discrepancy_analysis.j2",
                    extracted_data=extracted_data,
                    reference_data=reference_data,
                    computed_checks=_computed_value_checks(extracted_data),
                ),
                system_content=SystemPrompts.discrepancy_analysis(),
            )
            analysis = await send_prompt_to_llm_async(
                messages=messages,
                response_model=DiscrepancyAnalysisResponse,
                temperature=config.llm.DISCREPANCY_TEMPERATURE,
            )
            return DiscrepancyOutcome(
                success=True,
                analysis_result=analysis,
                total_discrepancies=analysis.analysis_summary.total_discrepancies,
                risk_level=analysis.analysis_summary.risk_level,
                analysis_method="intelligent_llm_analysis",
            )
        except Exception as e:
            logger.error(f"Discrepancy analysis failed: {e}")
            return DiscrepancyOutcome(
                success=False, error=str(e), analysis_method="failed_llm_analysis"
            )

    async def _generate_comprehensive_report(
        self, field_extraction: FieldExtractionOutcome, discrepancy_analysis: DiscrepancyOutcome
    ) -> ReportOutcome:
        """Generate the final report via the LLM (validated to LLMFinalReport)."""
        try:
            messages = LLMClient.create_messages(
                user_content=load_prompt(
                    "final_report.j2",
                    extraction_result=field_extraction.model_dump(),
                    analysis_result=discrepancy_analysis.model_dump(),
                ),
                system_content=SystemPrompts.reporting(),
            )
            report = await send_prompt_to_llm_async(
                messages=messages,
                response_model=LLMFinalReport,
                temperature=config.llm.REPORT_TEMPERATURE,
            )
            return ReportOutcome(
                success=True,
                final_report=report,
                report_generation_method="intelligent_llm_reporting",
                report_id=f"RPT-{uuid4().hex[:12]}",
                generation_date=datetime.now().isoformat(),
            )
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return ReportOutcome(
                success=False, error=str(e), report_generation_method="failed_llm_reporting"
            )

    @staticmethod
    async def analyze_document_sync(
        pdf_content: str,
        tables: list | None = None,
        page_content: list | None = None,
        reference_data: dict[str, Any] | None = None,
    ) -> ComprehensiveAnalysisResult:
        """Synchronous comprehensive analysis (used by the pipeline and for testing)."""
        service = DeclarationAnalyzerService()
        return await service.analyze_comprehensive(
            pdf_content, tables, page_content, reference_data
        )


def _parse_amount(raw: str | None) -> float | None:
    """Parse the amount in a free-form value string, or None.

    Handles thousands grouping, decimal conventions, and surrounding text, e.g.
    '1 460 000 (VALEUR IMPOSABLE)' -> 1460000.0 and '27,371,980.00' -> 27371980.0.
    """
    if not raw:
        return None
    return Price.fromstring(raw).amount_float


def _computed_value_checks(extracted_data: dict[str, Any]) -> list[str]:
    """Arithmetic facts about the extracted values, verified in code.

    Returns prompt-ready lines (empty when too few values parse). Doing the
    sums here keeps the analysis stage from mis-adding the very numbers it is
    judging.
    """
    checks: list[str] = []
    financial = extracted_data.get("financial") or {}
    goods = extracted_data.get("goods") or []

    goods_values = [_parse_amount(item.get("total_value")) for item in goods]
    goods_total = sum(v for v in goods_values if v is not None) if any(goods_values) else None
    invoice_total = _parse_amount(financial.get("total_invoice_value"))

    components = [
        (label, amount)
        for label, amount in (
            ("freight", _parse_amount(financial.get("freight_cost"))),
            ("insurance", _parse_amount(financial.get("insurance_cost"))),
            ("other charges", _parse_amount(financial.get("other_charges"))),
        )
        if amount is not None
    ]
    component_sum = sum(amount for _, amount in components)
    breakdown = " + ".join(f"{label} ({_fmt(amount)})" for label, amount in components)

    if invoice_total is not None and goods_total is not None and components:
        # The usual CIF composition: line values plus cost components make the total.
        full_sum = goods_total + component_sum
        verdict = "RECONCILES with" if abs(full_sum - invoice_total) < 1.0 else "DIFFERS from"
        checks.append(
            f"goods line values ({_fmt(goods_total)}) + {breakdown} = {_fmt(full_sum)},"
            f" which {verdict} the total invoice value {_fmt(invoice_total)}"
            f" (difference {_fmt(full_sum - invoice_total)})."
        )
    elif invoice_total is not None and goods_total is not None:
        verdict = "MATCHES" if abs(invoice_total - goods_total) < 1.0 else "DIFFERS FROM"
        checks.append(
            f"Sum of goods line values ({_fmt(goods_total)}) {verdict} the total invoice"
            f" value ({_fmt(invoice_total)})."
        )
    elif (declared_total := invoice_total or goods_total) is not None and len(components) >= 2:
        # Only one total is available; test whether the cost components alone compose it.
        verdict = "RECONCILES with" if abs(component_sum - declared_total) < 1.0 else "DIFFERS from"
        checks.append(
            f"{breakdown} = {_fmt(component_sum)}, which {verdict} the declared total"
            f" {_fmt(declared_total)} (difference {_fmt(component_sum - declared_total)})."
            " Cost components may sit on top of a goods/FOB value, so a difference"
            " is only meaningful if the document says these lines compose the total."
        )

    return checks


def _fmt(amount: float) -> str:
    """Format an amount for prompt text: thousands commas, no scientific notation."""
    return f"{amount:,.2f}".rstrip("0").rstrip(".")
