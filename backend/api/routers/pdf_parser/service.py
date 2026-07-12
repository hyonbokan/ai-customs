"""
PDF Parser Service using Docling for clean content extraction.

Provides comprehensive PDF processing and serves as the business-service
implementation for PDF parsing. It can be used independently (sync endpoint)
or as the first stage of the full pipeline.

Architecture principle: the PDF parser extracts content, the LLM extracts
intelligence.
"""

import asyncio
import base64
import uuid
from datetime import datetime
from typing import Any

from api.routers.pdf_parser.helpers.pdf_extractor import TradePDFExtractor
from api.routers.pdf_parser.schema import PDFProcessingResult
from core.utils.logger import logger


class PDFParserService:
    """Complete PDF Parser Service for clean content extraction."""

    def __init__(self):
        self.service_name = "pdf_parser_service"
        self.extractor = TradePDFExtractor()
        self.initialized = False

    async def initialize(self) -> bool:
        """Mark the service ready. The extractor is built in __init__."""
        self.initialized = True
        return True

    async def health_check(self) -> dict[str, Any]:
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
        file_url: str | None = None,
        file_content: str | None = None,
        processing_options: dict[str, Any] | None = None,
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
    async def parse_document_sync(
        file_url: str | None = None, file_content: str | None = None
    ) -> PDFProcessingResult:
        """Synchronous parsing (used by the pipeline and for testing)."""
        service = PDFParserService()
        await service.initialize()
        return await service.process_document_comprehensive(file_url, file_content)
