"""
PDF Parser Service using Docling for clean content extraction.

This service provides comprehensive PDF processing capabilities and serves as
the actual business service implementation for PDF parsing in the customs pipeline.
It can be used independently for testing and modularity.
"""

import asyncio

# stdlib
import base64
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from api.routers.pdf_parser.helpers.pdf_extractor import TradePDFExtractor
from api.routers.pdf_parser.schema import PDFParseResult, PDFParseStatus
from core.utils.logger import logger
from task_queue import huey


@huey.task(results=True)
def parse_pdf_document(
    file_url: Optional[str] = None,
    file_content: Optional[str] = None,
    parse_options: Optional[Dict[str, Any]] = None,
):
    """
    Background task to parse PDF document using Docling.
    Focuses on clean content extraction for LLM consumption.
    """
    import asyncio

    try:
        # Define asynchronous processing coroutine
        async def process_document():
            extractor = TradePDFExtractor()

            if file_url:
                # Async extraction from URL
                return await extractor.from_url(file_url)
            elif file_content:
                # Decode base64 and run blocking extraction in thread
                pdf_bytes = base64.b64decode(file_content)
                return await asyncio.to_thread(extractor.from_bytes, pdf_bytes)
            else:
                raise ValueError("Either file_url or file_content must be provided")

        # Run the async processing in a fresh loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(process_document())
        finally:
            loop.close()

        meta = result.metadata or {}

        if result.success:
            return {
                "status": "completed",
                "extracted_text": result.text_content,
                "structured_data": {
                    "text_content": result.text_content,
                    "tables": result.tables or [],
                    "page_content": result.page_content or [],
                    "metadata": meta,
                    "extraction_approach": "docling_clean_content_for_llm",
                },
                "metadata": {
                    "pages_count": meta.get("pages_count", 0),
                    "tables_count": meta.get("tables_count", 0),
                    "text_blocks_count": meta.get("text_blocks_count", 0),
                    "extraction_method": "docling",
                    "ready_for_llm": True,
                },
            }
        else:
            return {
                "status": "failed",
                "extracted_text": "",
                "structured_data": {},
                "metadata": {"errors": [result.error_message], "ready_for_llm": False},
            }

    except Exception as e:
        logger.error(f"Error in PDF parsing task: {e}")
        return {
            "status": "failed",
            "extracted_text": "",
            "structured_data": {},
            "metadata": {"errors": [str(e)], "ready_for_llm": False},
        }


class PDFParserService:
    """
    Complete PDF Parser Service for clean content extraction.

    This is the actual business service implementation that can be used independently
    for testing and modularity. It uses Docling to extract clean text, tables, and
    document structure that can be consumed by LLM services for intelligent analysis.

    Architecture principle: PDF parser extracts content, LLM extracts intelligence.
    """

    def __init__(self):
        """Initialize the PDF parser service."""
        self.service_name = "pdf_parser_service"
        # Use TradePDFExtractor as the concrete implementation
        self.extractor = TradePDFExtractor()
        self.initialized = False

    async def initialize(self) -> bool:
        """Initialize the service."""
        try:
            # Test the extractor
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
    ) -> Dict[str, Any]:
        """
        Comprehensive document processing with full metadata and error handling.

        Args:
            file_url: URL to PDF file
            file_content: Base64-encoded PDF content
            processing_options: Optional processing configuration

        Returns:
            Comprehensive processing result
        """
        processing_id = f"pdf_{uuid.uuid4().hex[:12]}"
        start_time = datetime.now()

        try:
            if not self.initialized:
                await self.initialize()

            # Validate input
            if not file_url and not file_content:
                raise ValueError("Either file_url or file_content must be provided")

            logger.info(f"Starting PDF processing: {processing_id}")

            # Extract content using TradePDFExtractor methods
            if file_url:
                result = await self.extractor.from_url(file_url)
            elif file_content:
                pdf_bytes = base64.b64decode(file_content)
                result = await asyncio.to_thread(self.extractor.from_bytes, pdf_bytes)
            else:
                raise ValueError("Either file_url or file_content must be provided")

            processing_time = (datetime.now() - start_time).total_seconds()

            meta = result.metadata or {}

            if result.success:
                return {
                    "success": True,
                    "processing_id": processing_id,
                    "text_content": result.text_content,
                    "tables": result.tables,
                    "page_content": result.page_content,
                    "metadata": {
                        **meta,
                        "processing_time_seconds": processing_time,
                        "processing_method": "comprehensive_docling_extraction",
                        "service": self.service_name,
                    },
                    "ready_for_llm": True,
                    "processing_summary": {
                        "pages_processed": meta.get("pages_count", 0),
                        "tables_extracted": len(result.tables or []),
                        "content_quality": "high" if result.text_content else "low",
                        "extraction_approach": "clean_content_for_llm_consumption",
                    },
                }
            else:
                return {
                    "success": False,
                    "processing_id": processing_id,
                    "error": result.error_message,
                    "ready_for_llm": False,
                    "processing_time_seconds": processing_time,
                    "metadata": {"service": self.service_name, "extraction_failed": True},
                }

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"PDF processing failed for {processing_id}: {e}")
            return {
                "success": False,
                "processing_id": processing_id,
                "error": str(e),
                "ready_for_llm": False,
                "processing_time_seconds": processing_time,
                "metadata": {"service": self.service_name, "exception_occurred": True},
            }

    @staticmethod
    def submit_parse_request(
        file_url: Optional[str] = None,
        file_content: Optional[str] = None,
        parse_options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Submit a PDF for parsing using Docling.
        Returns task ID for tracking.

        Args:
            file_url: URL to PDF file
            file_content: Base64-encoded PDF content
            parse_options: Optional parsing configuration

        Returns:
            Task ID for status tracking
        """
        # Validate input
        if not file_url and not file_content:
            raise ValueError("Either file_url or file_content must be provided")

        # Apply parse options (OCR, tables, etc.)
        effective_options = parse_options or {}

        # Submit background task
        task = parse_pdf_document(file_url, file_content, effective_options)
        return str(task)

    @staticmethod
    def get_parse_status(task_id: str) -> PDFParseStatus:
        from task_queue import huey  # Assume huey is imported or accessible

        task = huey.find_task(task_id)
        if task is None:
            return PDFParseStatus(task_id=task_id, status="not_found")
        if task.status == "pending":
            status = "queued"
            progress = 0
        elif task.status == "running":
            status = "processing"
            progress = 50  # Placeholder, implement real progress if needed
        elif task.status == "finished":
            status = "completed"
            progress = 100
        else:
            status = task.status
            progress = 0
        return PDFParseStatus(
            task_id=task_id,
            status=status,
            progress=progress,
            # Add pages if available from metadata
        )

    @staticmethod
    def get_parse_result(task_id: str) -> Optional[PDFParseResult]:
        from task_queue import huey

        result = huey.result(task_id)
        if result is None:
            return None
        if result.get("status") == "failed":
            # Handle error
            return PDFParseResult(
                task_id=task_id, status="failed", metadata={"error": result.get("error")}
            )
        return PDFParseResult(
            task_id=task_id,
            status=result["status"],
            extracted_text=result["extracted_text"],
            structured_data=result["structured_data"],
            metadata=result["metadata"],
        )

    @staticmethod
    async def parse_document_sync(
        file_url: Optional[str] = None, file_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synchronous parsing method for direct use (not background task).

        This is the main method used by the pipeline orchestrator and for independent testing.

        Args:
            file_url: URL to PDF file
            file_content: Base64-encoded PDF content

        Returns:
            Direct parsing result with clean content
        """
        try:
            # Create service instance for processing
            service = PDFParserService()
            await service.initialize()

            # Use comprehensive processing
            result = await service.process_document_comprehensive(file_url, file_content)

            return result

        except Exception as e:
            logger.error(f"Synchronous PDF parsing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "ready_for_llm": False,
                "processing_time_seconds": 0.0,
                "metadata": {"service": "pdf_parser_service", "sync_processing_failed": True},
            }
