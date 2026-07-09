"""
PDF Parser Service using Docling for clean content extraction.

Provides comprehensive PDF processing and serves as the business-service
implementation for PDF parsing. It can be used independently (sync endpoint),
via a background task, or as the first stage of the full pipeline.

Architecture principle: the PDF parser extracts content, the LLM extracts
intelligence.
"""

import asyncio
import base64
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from api.routers.pdf_parser.helpers.pdf_extractor import TradePDFExtractor
from api.routers.pdf_parser.schema import (
    PDFParseResult,
    PDFParseStatus,
    PDFProcessingResult,
    PDFTaskResult,
)
from core.utils.logger import logger
from task_queue import huey


@huey.task(results=True)
def parse_pdf_document(
    file_url: Optional[str] = None,
    file_content: Optional[str] = None,
    parse_options: Optional[Dict[str, Any]] = None,
) -> PDFTaskResult:
    """
    Background task to parse a PDF using Docling for clean content extraction.
    """
    try:

        async def process_document():
            extractor = TradePDFExtractor()
            if file_url:
                return await extractor.from_url(file_url)
            elif file_content:
                pdf_bytes = base64.b64decode(file_content)
                return await asyncio.to_thread(extractor.from_bytes, pdf_bytes)
            raise ValueError("Either file_url or file_content must be provided")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(process_document())
        finally:
            loop.close()

        meta = result.metadata or {}

        if result.success:
            return PDFTaskResult(
                status="completed",
                extracted_text=result.text_content,
                structured_data={
                    "text_content": result.text_content,
                    "tables": result.tables or [],
                    "page_content": result.page_content or [],
                    "metadata": meta,
                    "extraction_approach": "docling_clean_content_for_llm",
                },
                metadata={
                    "pages_count": meta.get("pages_count", 0),
                    "tables_count": meta.get("tables_count", 0),
                    "text_blocks_count": meta.get("text_blocks_count", 0),
                    "extraction_method": "docling",
                    "ready_for_llm": True,
                },
            )
        return PDFTaskResult(
            status="failed",
            metadata={"errors": [result.error_message], "ready_for_llm": False},
        )

    except Exception as e:
        logger.error(f"Error in PDF parsing task: {e}")
        return PDFTaskResult(
            status="failed",
            metadata={"errors": [str(e)], "ready_for_llm": False},
        )


class PDFParserService:
    """Complete PDF Parser Service for clean content extraction."""

    def __init__(self):
        self.service_name = "pdf_parser_service"
        self.extractor = TradePDFExtractor()
        self.initialized = False

    async def initialize(self) -> bool:
        """Initialize the service."""
        try:
            self.extractor = TradePDFExtractor()
            self.initialized = True
            logger.info("PDF parser service initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize PDF parser service: {e}")
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the PDF parser service."""
        return {
            "service": self.service_name,
            "status": "healthy" if self.initialized else "unhealthy",
            "initialized": self.initialized,
            "extractor_type": "docling",
            "capabilities": ["ocr", "table_extraction", "clean_content_preparation"],
            "last_check": datetime.now().isoformat(),
        }

    async def process_document_comprehensive(
        self,
        file_url: Optional[str] = None,
        file_content: Optional[str] = None,
        processing_options: Optional[Dict[str, Any]] = None,
    ) -> PDFProcessingResult:
        """Process a document with full metadata and error handling."""
        processing_id = f"pdf_{uuid.uuid4().hex[:12]}"
        start_time = datetime.now()

        try:
            if not self.initialized:
                await self.initialize()
            if not file_url and not file_content:
                raise ValueError("Either file_url or file_content must be provided")

            logger.info(f"Starting PDF processing: {processing_id}")

            if file_url:
                result = await self.extractor.from_url(file_url)
            else:
                pdf_bytes = base64.b64decode(file_content)  # type: ignore[arg-type]
                result = await asyncio.to_thread(self.extractor.from_bytes, pdf_bytes)

            processing_time = (datetime.now() - start_time).total_seconds()
            meta = result.metadata or {}

            if result.success:
                return PDFProcessingResult(
                    success=True,
                    processing_id=processing_id,
                    text_content=result.text_content,
                    tables=result.tables or [],
                    page_content=result.page_content or [],
                    metadata={
                        **meta,
                        "processing_time_seconds": processing_time,
                        "processing_method": "comprehensive_docling_extraction",
                        "service": self.service_name,
                    },
                    ready_for_llm=True,
                    processing_summary={
                        "pages_processed": meta.get("pages_count", 0),
                        "tables_extracted": len(result.tables or []),
                        "content_quality": "high" if result.text_content else "low",
                        "extraction_approach": "clean_content_for_llm_consumption",
                    },
                    processing_time_seconds=processing_time,
                )
            return PDFProcessingResult(
                success=False,
                processing_id=processing_id,
                error=result.error_message,
                processing_time_seconds=processing_time,
                metadata={"service": self.service_name, "extraction_failed": True},
            )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"PDF processing failed for {processing_id}: {e}")
            return PDFProcessingResult(
                success=False,
                processing_id=processing_id,
                error=str(e),
                processing_time_seconds=processing_time,
                metadata={"service": self.service_name, "exception_occurred": True},
            )

    @staticmethod
    def submit_parse_request(
        file_url: Optional[str] = None,
        file_content: Optional[str] = None,
        parse_options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Submit a PDF for background parsing. Returns a task ID for tracking."""
        if not file_url and not file_content:
            raise ValueError("Either file_url or file_content must be provided")
        task = parse_pdf_document(file_url, file_content, parse_options or {})
        return str(task)

    @staticmethod
    def get_parse_status(task_id: str) -> PDFParseStatus:
        task = huey.find_task(task_id)
        if task is None:
            return PDFParseStatus(task_id=task_id, status="not_found")
        if task.status == "pending":
            status, progress = "queued", 0
        elif task.status == "running":
            status, progress = "processing", 50
        elif task.status == "finished":
            status, progress = "completed", 100
        else:
            status, progress = task.status, 0
        return PDFParseStatus(task_id=task_id, status=status, progress=progress)

    @staticmethod
    def get_parse_result(task_id: str) -> Optional[PDFParseResult]:
        result: Optional[PDFTaskResult] = huey.result(task_id)
        if result is None:
            return None
        if result.status == "failed":
            return PDFParseResult(
                success=False,
                task_id=task_id,
                status="failed",
                metadata=result.metadata,  # type: ignore[arg-type]
            )
        return PDFParseResult(
            success=True,
            task_id=task_id,
            status=result.status,
            extracted_text=result.extracted_text,
            metadata=result.metadata,  # type: ignore[arg-type]
        )

    @staticmethod
    async def parse_document_sync(
        file_url: Optional[str] = None, file_content: Optional[str] = None
    ) -> PDFProcessingResult:
        """Synchronous parsing (used by the pipeline and for testing)."""
        service = PDFParserService()
        await service.initialize()
        return await service.process_document_comprehensive(file_url, file_content)
