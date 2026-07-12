"""
Full Pipeline Service for Customs Analysis.

Orchestrates the end-to-end flow synchronously by chaining the two independent
router services:

    1. PDF parsing (Docling)  -> clean text, tables, structure
    2. LLM analysis           -> field extraction + discrepancy detection
    3. Report generation      -> comprehensive report

There is no separate orchestration framework; the pipeline is just the two
services called in order, which keeps each stage independently testable.
"""

import uuid
from datetime import datetime
from typing import Any

from api.routers.declaration_analyzer.schema import ComprehensiveAnalysisResult
from api.routers.declaration_analyzer.service import DeclarationAnalyzerService
from api.routers.full_pipeline.schema import (
    FullPipelineResponse,
    PipelineCompleteResult,
    PipelineReport,
)
from api.routers.pdf_parser.schema import PDFProcessingResult
from api.routers.pdf_parser.service import PDFParserService
from core.utils.logger import logger


def _build_report(
    report_id: str, pdf_result: PDFProcessingResult, analysis: ComprehensiveAnalysisResult
) -> PipelineReport:
    """Combine the PDF and LLM stages into a summary report."""
    discrepancies = (
        analysis.processing_summary.discrepancies_found if analysis.processing_summary else 0
    )
    return PipelineReport(
        report_id=report_id,
        generation_date=datetime.now().isoformat(),
        pdf_processing="completed" if pdf_result.success else "failed",
        llm_analysis="completed" if analysis.success else "failed",
        text_extracted=bool(pdf_result.text_content),
        tables_found=len(pdf_result.tables),
        pages_processed=pdf_result.metadata.get("pages_count", 0),
        discrepancies_found=discrepancies,
    )


class FullPipelineService:
    """Synchronous orchestrator for the complete customs analysis pipeline."""

    @staticmethod
    async def process(
        file_url: str | None = None,
        file_content: str | None = None,
        reference_data: dict[str, Any] | None = None,
        processing_options: dict[str, Any] | None = None,
    ) -> FullPipelineResponse:
        """Run the full pipeline synchronously; raises ValueError if no file input is given."""
        if not file_url and not file_content:
            raise ValueError("Either file_url or file_content must be provided")

        task_id = f"pipeline_{uuid.uuid4().hex[:12]}"
        start_time = datetime.now()
        logger.info(f"Starting full pipeline processing: {task_id}")

        # Step 1: PDF parsing -> clean content
        pdf_result = await PDFParserService.parse_document_sync(
            file_url=file_url, file_content=file_content
        )
        if not pdf_result.success:
            return FullPipelineResponse(
                success=False,
                task_id=task_id,
                status="failed",
                message="Pipeline processing failed at stage: pdf_extraction",
                error=pdf_result.error or "PDF processing failed",
            )

        # Step 2: LLM field extraction + discrepancy analysis
        analysis = await DeclarationAnalyzerService.analyze_document_sync(
            pdf_content=pdf_result.text_content or "",
            tables=pdf_result.tables,
            page_content=pdf_result.page_content,
            reference_data=reference_data or {},
        )
        if not analysis.success:
            return FullPipelineResponse(
                success=False,
                task_id=task_id,
                status="failed",
                message="Pipeline processing failed at stage: llm_analysis",
                error=analysis.error or "LLM analysis failed",
            )

        # Step 3: Final report
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Full pipeline processing completed: {task_id} ({processing_time:.1f}s)")

        return FullPipelineResponse(
            success=True,
            task_id=task_id,
            status="completed",
            message="Pipeline processing completed successfully",
            complete_result=PipelineCompleteResult(
                task_id=task_id,
                overall_status="completed",
                processing_time=f"{processing_time:.1f} seconds",
                pdf_extraction=pdf_result,
                llm_analysis=analysis,
                final_report=_build_report(f"RPT-{uuid.uuid4().hex[:12]}", pdf_result, analysis),
            ),
        )
