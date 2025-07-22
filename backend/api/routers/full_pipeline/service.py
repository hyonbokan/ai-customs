"""
Full Pipeline Service for Customs Analysis.

This service uses the core CustomsPipelineService to orchestrate
the complete pipeline from PDF parsing to LLM analysis.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from task_queue import huey
from api.routers.full_pipeline.schema import (
    PipelineStatus, 
    PipelineResult, 
    PDFExtractionResult, 
    LLMAnalysisResult, 
    FinalReport,
    PipelineStages,
    PipelineStageStatus
)

# Import core services
from core.foundation.customs_pipeline_service import CustomsPipelineService
from core.utils.logger import logger


@huey.task()
def process_full_pipeline_task(
    file_url: Optional[str] = None,
    file_content: Optional[str] = None,
    reference_data: Optional[Dict[str, Any]] = None,
    processing_options: Optional[Dict[str, Any]] = None
):
    """
    Background task to process the complete pipeline using core services.
    
    This task orchestrates:
    1. PDF parsing for clean content extraction
    2. LLM analysis for field extraction and discrepancy detection
    3. Final report generation
    """
    import asyncio
    
    try:
        # Run the async pipeline processing
        async def run_pipeline():
            # Initialize the core pipeline service
            pipeline_service = CustomsPipelineService()
            await pipeline_service.initialize()
            await pipeline_service.start()
            
            try:
                # Process the document
                context = {
                    "file_url": file_url,
                    "file_content": file_content,
                    "reference_data": reference_data,
                    "processing_options": processing_options
                }
                
                result = await pipeline_service.process_document(context)
                return result
                
            finally:
                await pipeline_service.stop()
        
        # Execute the pipeline
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_pipeline())
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in full pipeline task: {e}")
        return {
            "success": False,
            "error": str(e),
            "processing_time": datetime.now().isoformat()
        }


class FullPipelineService:
    """
    Full Pipeline Service that uses core services for orchestration.
    
    This service provides a simplified interface to the core CustomsPipelineService
    for the API layer.
    """
    
    @staticmethod
    async def process_pipeline(
        file_url: Optional[str] = None,
        file_content: Optional[str] = None,
        reference_data: Optional[Dict[str, Any]] = None,
        processing_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Submit a complete pipeline for processing.
        Returns task ID for tracking.
        """
        # Validate input
        if not file_url and not file_content:
            raise ValueError("Either file_url or file_content must be provided")
        
        # Generate task ID
        task_id = f"pipeline_{uuid.uuid4().hex[:12]}"
        
        # Submit background task
        task = process_full_pipeline_task(file_url, file_content, reference_data, processing_options)
        
        # Initialize pipeline stages
        pipeline_stages = PipelineStages(
            pdf_extraction=PipelineStageStatus(
                stage=1,
                name="PDF Content Extraction",
                status="queued",
                progress=0,
                start_time=datetime.now().isoformat(),
                end_time=None,
                output_ready=False,
                error_message=None
            ),
            llm_analysis=PipelineStageStatus(
                stage=2,
                name="LLM Analysis",
                status="pending",
                progress=0,
                start_time=None,
                end_time=None,
                output_ready=False,
                error_message=None
            ),
            report_generation=PipelineStageStatus(
                stage=3,
                name="Report Generation",
                status="pending",
                progress=0,
                start_time=None,
                end_time=None,
                output_ready=False,
                error_message=None
            )
        )
        
        return {
            "task_id": task_id,
            "status": "queued",
            "message": "Full pipeline processing started using core services",
            "pipeline_stages": pipeline_stages
        }
    
    @staticmethod
    async def process_pipeline_sync(
        file_url: Optional[str] = None,
        file_content: Optional[str] = None,
        reference_data: Optional[Dict[str, Any]] = None,
        processing_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process the complete pipeline synchronously using core services.
        Returns complete results when finished.
        """
        try:
            # Validate input
            if not file_url and not file_content:
                raise ValueError("Either file_url or file_content must be provided")
            
            # Generate task ID
            task_id = f"pipeline_sync_{uuid.uuid4().hex[:12]}"
            
            # Initialize the core pipeline service
            pipeline_service = CustomsPipelineService()
            await pipeline_service.initialize()
            await pipeline_service.start()
            
            try:
                # Process the document
                context = {
                    "file_url": file_url,
                    "file_content": file_content,
                    "reference_data": reference_data,
                    "processing_options": processing_options
                }
                
                result = await pipeline_service.process_document(context)
                
                # Transform the result to match expected API format
                if result.get("success"):
                    return {
                        "success": True,
                        "task_id": task_id,
                        "status": "completed",
                        "message": "Pipeline processing completed successfully",
                        "complete_result": {
                            "task_id": task_id,
                            "overall_status": "completed",
                            "processing_time": f"{result.get('processing_time_seconds', 0):.1f} seconds",
                            "pdf_extraction": result.get("results", {}).get("pdf_processing", {}),
                            "llm_analysis": result.get("results", {}).get("llm_analysis", {}),
                            "final_report": result.get("results", {}).get("final_report", {}),
                            "pipeline_metadata": {
                                "processing_id": result.get("processing_id"),
                                "completed_at": result.get("completed_at"),
                                "pipeline_stages": result.get("pipeline_stages", [])
                            }
                        }
                    }
                else:
                    return {
                        "success": False,
                        "task_id": task_id,
                        "status": "failed",
                        "message": f"Pipeline processing failed at stage: {result.get('stage', 'unknown')}",
                        "error": result.get("error", "Unknown error")
                    }
                
            finally:
                await pipeline_service.stop()
            
        except Exception as e:
            return {
                "success": False,
                "task_id": task_id if 'task_id' in locals() else None,
                "status": "failed",
                "message": "Pipeline processing failed",
                "error": str(e)
            }
    
    @staticmethod
    def get_pipeline_status(task_id: str) -> PipelineStatus:
        """
        Get the status of a pipeline processing task.
        """
        # TODO: Implement actual task status checking with Huey
        return PipelineStatus(
            task_id=task_id,
            overall_status="processing",
            overall_progress=65,
            current_stage="LLM Analysis",
            estimated_completion="2 minutes",
            stages=PipelineStages(
                pdf_extraction=PipelineStageStatus(
                    stage=1,
                    name="PDF Content Extraction",
                    status="completed",
                    progress=100,
                    start_time=None,
                    end_time=None,
                    output_ready=True,
                    error_message=None
                ),
                llm_analysis=PipelineStageStatus(
                    stage=2,
                    name="LLM Analysis",
                    status="processing",
                    progress=70,
                    start_time=None,
                    end_time=None,
                    output_ready=False,
                    error_message=None
                ),
                report_generation=PipelineStageStatus(
                    stage=3,
                    name="Report Generation",
                    status="pending",
                    progress=0,
                    start_time=None,
                    end_time=None,
                    output_ready=False,
                    error_message=None
                )
            ),
            processing_time="1 minute 30 seconds"
        )
    
    @staticmethod
    def get_pipeline_result(task_id: str) -> Optional[PipelineResult]:
        """
        Get the result of a completed pipeline processing.
        """
        # TODO: Implement actual result retrieval from Huey
        # For now, return mock result showing the expected structure
        return PipelineResult(
            task_id=task_id,
            overall_status="completed",
            processing_time="2 minutes 45 seconds",
            pdf_extraction=PDFExtractionResult(
                success=True,
                text_content="COMMERCIAL INVOICE\nInvoice No: INV-2024-0012...",
                tables=[
                    {
                        "table_id": 0,
                        "page": 1,
                        "data": [
                            ["Description", "HS Code", "Qty", "Unit", "Unit Price", "Total Price"],
                            ["Electronic Components", "8542.31", "100", "PCS", "$150.00", "$15,000.00"],
                            ["Semiconductor Devices", "8541.10", "50", "PCS", "$200.00", "$10,000.00"]
                        ]
                    }
                ],
                page_content=[{"page": 1, "content": {"texts": [], "tables": [{"table_id": 0}]}}],
                metadata={"pages_count": 1, "extraction_method": "docling", "ready_for_llm": True},
                extraction_time="45 seconds"
            ),
            llm_analysis=LLMAnalysisResult(
                success=True,
                extracted_fields={"invoice_number": "INV-2024-0012", "total_value": 34325.00},
                discrepancies=[
                    {
                        "category": "value_assessment",
                        "severity": "medium",
                        "type": "pricing_variance",
                        "description": "Unit price for electronic components appears higher than market average"
                    }
                ],
                analysis_summary={"confidence": 0.85, "issues_found": 1},
                confidence_score=0.85,
                analysis_time="1 minute 30 seconds"
            ),
            final_report=FinalReport(
                report_id=f"RPT-{task_id}",
                generation_date=datetime.now().isoformat(),
                executive_summary={
                    "overall_assessment": "Medium risk transaction requiring inspection",
                    "risk_level": "medium",
                    "clearance_recommendation": "require_inspection",
                    "confidence_score": 0.85
                },
                document_overview={
                    "document_type": "commercial_invoice",
                    "document_number": "INV-2024-0012",
                    "transaction_value": "$34,325.00 USD"
                },
                detailed_findings={
                    "total_issues": 1,
                    "medium_priority_issues": 1,
                    "issues_detail": [
                        {
                            "issue_id": "ISS-001",
                            "category": "value_assessment",
                            "severity": "medium",
                            "description": "Unit price variance detected"
                        }
                    ]
                },
                compliance_status={
                    "overall_compliance": "requires_review",
                    "documentation_status": "complete",
                    "regulatory_compliance": "compliant"
                },
                recommendations={
                    "immediate_actions": ["Request pricing justification documentation"],
                    "processing_recommendation": "inspect"
                },
                processing_decision={
                    "recommended_action": "inspect",
                    "justification": "Pricing variance requires verification before clearance"
                },
                report_metadata={
                    "processing_time": "2 minutes 45 seconds",
                    "analysis_method": "core_services_orchestration",
                    "quality_score": 0.92
                }
            ),
            pipeline_metadata={
                "total_processing_time": "2 minutes 45 seconds",
                "services_used": ["customs_pipeline_service", "pdf_processing_service", "llm_analysis_service"],
                "data_quality_score": 0.92,
                "processing_method": "core_services_orchestration",
                "architecture": "microservices_coordination"
            }
        ) 