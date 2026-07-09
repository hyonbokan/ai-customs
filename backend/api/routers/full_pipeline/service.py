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
from typing import Any, Dict, Optional

from api.routers.declaration_analyzer.service import DeclarationAnalyzerService
from api.routers.pdf_parser.service import PDFParserService
from core.utils.logger import logger


def _failed(task_id: str, stage: str, error: str) -> Dict[str, Any]:
    """Build a failure response for a given pipeline stage."""
    return {
        "success": False,
        "task_id": task_id,
        "status": "failed",
        "message": f"Pipeline processing failed at stage: {stage}",
        "error": error,
    }


def _build_report(pdf_result: Dict[str, Any], analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """Combine PDF and LLM results into a final summary report."""
    analysis = analysis_result.get("analysis_result", {})
    return {
        "report_id": f"RPT-{uuid.uuid4().hex[:12]}",
        "generation_date": datetime.now().isoformat(),
        "executive_summary": {
            "pdf_processing": "completed" if pdf_result.get("success") else "failed",
            "llm_analysis": "completed" if analysis_result.get("success") else "failed",
        },
        "processing_details": {
            "pdf_extraction": {
                "text_extracted": bool(pdf_result.get("text_content")),
                "tables_found": len(pdf_result.get("tables", [])),
                "pages_processed": pdf_result.get("metadata", {}).get("pages_count", 0),
            },
            "llm_analysis": {
                "discrepancies_found": analysis.get("discrepancies_found", 0),
                "confidence_score": analysis.get("confidence_score", 0.0),
            },
        },
    }


class FullPipelineService:
    """Synchronous orchestrator for the complete customs analysis pipeline."""

    @staticmethod
    async def process(
        file_url: Optional[str] = None,
        file_content: Optional[str] = None,
        reference_data: Optional[Dict[str, Any]] = None,
        processing_options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run the full pipeline synchronously and return the complete result.

        Raises:
            ValueError: if neither ``file_url`` nor ``file_content`` is provided.
        """
        if not file_url and not file_content:
            raise ValueError("Either file_url or file_content must be provided")

        task_id = f"pipeline_{uuid.uuid4().hex[:12]}"
        start_time = datetime.now()
        logger.info(f"Starting full pipeline processing: {task_id}")

        # Step 1: PDF parsing -> clean content
        pdf_result = await PDFParserService.parse_document_sync(
            file_url=file_url, file_content=file_content
        )
        if not pdf_result.get("success"):
            return _failed(
                task_id, "pdf_extraction", pdf_result.get("error", "PDF processing failed")
            )

        # Step 2: LLM field extraction + discrepancy analysis
        analysis_result = await DeclarationAnalyzerService.analyze_document_sync(
            pdf_content=pdf_result.get("text_content", ""),
            tables=pdf_result.get("tables", []),
            page_content=pdf_result.get("page_content", []),
            metadata=pdf_result.get("metadata", {}),
            reference_data=reference_data or {},
        )
        if not analysis_result.get("success"):
            return _failed(
                task_id, "llm_analysis", analysis_result.get("error", "LLM analysis failed")
            )

        # Step 3: Final report
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Full pipeline processing completed: {task_id} ({processing_time:.1f}s)")

        return {
            "success": True,
            "task_id": task_id,
            "status": "completed",
            "message": "Pipeline processing completed successfully",
            "complete_result": {
                "task_id": task_id,
                "overall_status": "completed",
                "processing_time": f"{processing_time:.1f} seconds",
                "pdf_extraction": pdf_result,
                "llm_analysis": analysis_result,
                "final_report": _build_report(pdf_result, analysis_result),
            },
        }
