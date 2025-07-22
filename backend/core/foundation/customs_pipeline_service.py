"""
Core Customs Pipeline Service.

This service orchestrates the complete customs analysis pipeline by coordinating
calls to the router services (pdf_parser and declaration_analyzer).
"""

import asyncio
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from core.foundation.base_service import BaseService, ServiceStatus
from core.foundation.pipeline_manager import PipelineManager
from core.foundation.service_registry import ServiceRegistry
from core.utils.logger import logger


class CustomsPipelineService(BaseService):
    """
    Core Customs Pipeline Service for complete document analysis.
    
    This service orchestrates the complete pipeline by coordinating calls
    to the individual router services for modularity and independent testing.
    """
    
    def __init__(self, name: str = "customs_pipeline_service", config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.pipeline_manager = None
        self.service_registry = None
        self.pipeline_name = "customs_analysis_pipeline"
    
    async def initialize(self) -> bool:
        """Initialize the customs pipeline service."""
        try:
            # Initialize service registry for orchestration
            self.service_registry = ServiceRegistry()
            
            # Initialize pipeline manager
            self.pipeline_manager = PipelineManager(self.service_registry)
            
            # Note: We don't register router services here since they're independent
            # The pipeline will call them via their API interfaces
            
            logger.info(f"Customs pipeline service '{self.name}' initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize customs pipeline service: {e}")
            return False
    
    async def _start(self) -> Dict[str, Any]:
        """Start the customs pipeline service."""
        try:
            self.state.status = ServiceStatus.RUNNING
            logger.info(f"Customs pipeline service '{self.name}' started")
            return {"status": "started", "orchestrator": "ready"}
        except Exception as e:
            logger.error(f"Failed to start customs pipeline service: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def _stop(self) -> None:
        """Stop the customs pipeline service."""
        try:
            self.state.status = ServiceStatus.STOPPED
            logger.info(f"Customs pipeline service '{self.name}' stopped")
        except Exception as e:
            logger.error(f"Failed to stop customs pipeline service: {e}")
            raise
    
    def _validate_config(self) -> None:
        """Validate service configuration."""
        # Basic validation for orchestrator
        logger.debug(f"Validating config for {self.name}")
    
    async def process_document(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a document through the complete customs analysis pipeline.
        
        This orchestrates calls to:
        1. PDF Parser router service
        2. Declaration Analyzer router service  
        3. Report generation
        
        Args:
            context: Processing context with document and reference data
            
        Returns:
            Dictionary with complete pipeline results
        """
        try:
            if self.state.status != ServiceStatus.RUNNING:
                raise RuntimeError(f"Service {self.name} is not running")
            
            # Generate processing ID
            processing_id = f"proc_{uuid.uuid4().hex[:12]}"
            start_time = datetime.now()
            
            logger.info(f"Starting complete pipeline processing: {processing_id}")
            
            # Step 1: PDF Processing via router service
            pdf_result = await self._call_pdf_parser_service(context)
            if not pdf_result.get("success"):
                return {
                    "success": False,
                    "stage": "pdf_processing",
                    "error": pdf_result.get("error", "PDF processing failed"),
                    "processing_id": processing_id
                }
            
            # Step 2: LLM Analysis via router service  
            analysis_context = {
                **context,
                "pdf_content": pdf_result.get("text_content"),
                "tables": pdf_result.get("tables"),
                "page_content": pdf_result.get("page_content"),
                "metadata": pdf_result.get("metadata")
            }
            
            analysis_result = await self._call_declaration_analyzer_service(analysis_context)
            if not analysis_result.get("success"):
                return {
                    "success": False,
                    "stage": "llm_analysis", 
                    "error": analysis_result.get("error", "LLM analysis failed"),
                    "processing_id": processing_id,
                    "pdf_result": pdf_result
                }
            
            # Step 3: Generate final report
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": True,
                "processing_id": processing_id,
                "status": "completed",
                "results": {
                    "pdf_processing": pdf_result,
                    "llm_analysis": analysis_result,
                    "final_report": self._generate_pipeline_report(pdf_result, analysis_result)
                },
                "processing_time_seconds": processing_time,
                "completed_at": datetime.now().isoformat(),
                "pipeline_stages": ["pdf_processing", "llm_analysis", "report_generation"]
            }
            
        except Exception as e:
            logger.error(f"Pipeline processing failed: {e}")
            return {
                "success": False,
                "processing_id": processing_id,
                "error": str(e),
                "processing_time_seconds": (datetime.now() - start_time).total_seconds() if 'start_time' in locals() else 0
            }
    
    async def _call_pdf_parser_service(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Call the PDF parser router service."""
        try:
            from api.routers.pdf_parser.service import PDFParserService
            
            # Use the router service directly for orchestration
            result = await PDFParserService.parse_document_sync(
                file_url=context.get("file_url"),
                file_content=context.get("file_content")
            )
            
            logger.info("PDF parsing completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"PDF parser service call failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _call_declaration_analyzer_service(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Call the declaration analyzer router service."""
        try:
            from api.routers.declaration_analyzer.service import DeclarationAnalyzerService
            
            # Extract data for analysis
            pdf_content = context.get("pdf_content", "")
            tables = context.get("tables", [])
            page_content = context.get("page_content", [])
            metadata = context.get("metadata", {})
            reference_data = context.get("reference_data", {})
            
            # Call the comprehensive analysis method
            analysis_result = await DeclarationAnalyzerService.analyze_document_sync(
                pdf_content=pdf_content,
                tables=tables,
                page_content=page_content,
                metadata=metadata,
                reference_data=reference_data
            )
            
            logger.info("Declaration analysis completed successfully")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Declaration analyzer service call failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_pipeline_report(self, pdf_result: Dict[str, Any], analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a final pipeline report combining all results."""
        return {
            "report_id": f"RPT-{uuid.uuid4().hex[:12]}",
            "generation_date": datetime.now().isoformat(),
            "executive_summary": {
                "pdf_processing": "completed" if pdf_result.get("success") else "failed",
                "llm_analysis": "completed" if analysis_result.get("success") else "failed",
                "overall_status": "completed" if pdf_result.get("success") and analysis_result.get("success") else "failed"
            },
            "processing_details": {
                "pdf_extraction": {
                    "text_extracted": bool(pdf_result.get("text_content")),
                    "tables_found": len(pdf_result.get("tables", [])),
                    "pages_processed": pdf_result.get("metadata", {}).get("pages_count", 0)
                },
                "llm_analysis": {
                    "analysis_completed": analysis_result.get("success", False),
                    "discrepancies_found": analysis_result.get("analysis_result", {}).get("discrepancies_found", 0),
                    "confidence_score": analysis_result.get("analysis_result", {}).get("confidence_score", 0.0)
                }
            },
            "architecture_note": "Pipeline orchestrates independent router services for modularity and testing"
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the customs pipeline service."""
        try:
            status = {
                "service": self.name,
                "status": self.state.status.value,
                "healthy": self.state.status == ServiceStatus.RUNNING,
                "last_heartbeat": datetime.now().isoformat(),
                "architecture": "orchestrator_of_router_services"
            }
            
            # Check if router services are available (basic import check)
            try:
                from api.routers.pdf_parser.service import PDFParserService
                from api.routers.declaration_analyzer.service import DeclarationAnalyzerService
                status["router_services"] = {
                    "pdf_parser": "available",
                    "declaration_analyzer": "available"
                }
            except ImportError as e:
                status["router_services"] = {
                    "error": f"Router service import failed: {e}"
                }
                status["healthy"] = False
            
            return status
        except Exception as e:
            return {
                "service": self.name,
                "status": "error",
                "healthy": False,
                "error": str(e),
                "last_heartbeat": datetime.now().isoformat()
            } 