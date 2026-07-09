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
from typing import Any, Dict, List, Optional
from uuid import uuid4

from api.routers.declaration_analyzer.helpers.data_validator import validate_declaration_data
from api.routers.declaration_analyzer.schema import (
    ComprehensiveAnalysisResult,
    DiscrepancyOutcome,
    FieldExtractionOutcome,
    PipelineLogEntry,
    ProcessingSummary,
    ReportOutcome,
)
from core.llm.llm_client import LLMClient, send_prompt_to_llm_async
from core.llm.pipeline_prompts import PipelinePrompts
from core.llm.response_models import (
    CustomsAnalysisResponse,
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

    @staticmethod
    async def initialize() -> bool:
        """Initialize the service dependencies."""
        try:
            LLMClient()  # Test LLM connectivity
            logger.info("Declaration analyzer service initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize declaration analyzer service: {e}")
            return False

    async def analyze_comprehensive(
        self,
        pdf_content: str,
        tables: Optional[list] = None,
        page_content: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None,
        reference_data: Optional[Dict[str, Any]] = None,
    ) -> ComprehensiveAnalysisResult:
        """Run the multi-stage analysis: field extraction -> discrepancies -> report."""
        analysis_id = f"analysis_{uuid4().hex[:12]}"
        start_time = datetime.now()
        pipeline_log: List[PipelineLogEntry] = []

        try:
            if not await self.initialize():
                raise ValueError("Service initialization failed")
            if not pdf_content:
                raise ValueError("PDF content is required for analysis")

            logger.info(f"Starting comprehensive analysis: {analysis_id}")
            pipeline_log.append(
                _log("start", "Initialized service and validated input", analysis_id=analysis_id)
            )

            # Step 1: field extraction
            field_extraction = await self._extract_fields_intelligently(
                pdf_content, tables, page_content, metadata
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
        tables: Optional[list] = None,
        page_content: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FieldExtractionOutcome:
        """Extract structured fields via the LLM (validated to FieldExtractionResponse)."""
        combined_content = pdf_content
        if tables:
            combined_content += f"\n\nTABLE DATA:\n{tables}"
        if page_content:
            combined_content += f"\n\nPAGE STRUCTURE:\n{page_content}"

        try:
            messages = LLMClient.create_messages(
                user_content=PipelinePrompts.get_field_extraction_prompt(
                    clean_content=combined_content, document_type="customs_document"
                ),
                system_content=SystemPrompts.field_extraction(),
            )
            extracted = await send_prompt_to_llm_async(
                messages=messages,
                response_model=FieldExtractionResponse,
                temperature=0.1,
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
        reference_data: Optional[Dict[str, Any]] = None,
    ) -> DiscrepancyOutcome:
        """Analyze discrepancies via the LLM (validated to DiscrepancyAnalysisResponse)."""
        extracted_data = (
            field_extraction.extracted_fields.model_dump()
            if field_extraction.extracted_fields
            else {}
        )
        try:
            messages = LLMClient.create_messages(
                user_content=PipelinePrompts.get_discrepancy_analysis_prompt(
                    extracted_data=extracted_data, reference_data=reference_data
                ),
                system_content=SystemPrompts.discrepancy_analysis(),
            )
            analysis = await send_prompt_to_llm_async(
                messages=messages,
                response_model=DiscrepancyAnalysisResponse,
                temperature=0.2,
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
                user_content=PipelinePrompts.get_final_report_prompt(
                    extraction_result=field_extraction.model_dump(),
                    analysis_result=discrepancy_analysis.model_dump(),
                ),
                system_content=SystemPrompts.reporting(),
            )
            report = await send_prompt_to_llm_async(
                messages=messages,
                response_model=LLMFinalReport,
                temperature=0.1,
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
    async def perform_analysis(
        declaration_data: Dict[str, Any], reference_data: Optional[Dict[str, Any]] = None
    ) -> CustomsAnalysisResponse:
        """Single-shot analysis for the synchronous /analyze-declaration endpoint."""
        validation = validate_declaration_data(declaration_data)
        if not validation.is_valid:
            # Raise a specific error the route maps to a 422 response.
            raise ValueError(f"Invalid declaration data: {'; '.join(validation.errors)}")

        normalized_data = validation.normalized_data or {}
        logger.info(
            f"Processing customs declaration for {normalized_data.get('declaration_number')}"
        )

        try:
            analysis_report = await LLMClient.analyze_customs_declaration(
                normalized_data, reference_data
            )
            logger.info(f"LLM analysis completed for {normalized_data.get('declaration_number')}")
            return analysis_report
        except Exception as e:
            logger.error(f"Error in LLM call for {normalized_data.get('declaration_number')}: {e}")
            raise

    @staticmethod
    async def analyze_document_sync(
        pdf_content: str,
        tables: Optional[list] = None,
        page_content: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None,
        reference_data: Optional[Dict[str, Any]] = None,
    ) -> ComprehensiveAnalysisResult:
        """Synchronous comprehensive analysis (used by the pipeline and for testing)."""
        service = DeclarationAnalyzerService()
        return await service.analyze_comprehensive(
            pdf_content, tables, page_content, metadata, reference_data
        )
