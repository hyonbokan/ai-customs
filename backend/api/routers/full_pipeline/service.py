"""
Full Pipeline Service for Customs Analysis.

This service uses the core CustomsPipelineService to orchestrate
the complete pipeline from PDF parsing to LLM analysis.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from api.routers.full_pipeline.schema import (
    FinalReport,
    PipelineResult,
    PipelineStages,
    PipelineStageStatus,
    PipelineStatus,
)

# Import core services
from core.foundation.customs_pipeline_service import CustomsPipelineService
from core.utils.logger import logger
from task_queue import huey


@huey.task(results=True)
def process_full_pipeline_task(
    file_url: Optional[str] = None,
    file_content: Optional[str] = None,
    reference_data: Optional[Dict[str, Any]] = None,
    processing_options: Optional[Dict[str, Any]] = None,
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
                    "processing_options": processing_options,
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
        return {"success": False, "error": str(e), "processing_time": datetime.now().isoformat()}


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
        processing_options: Optional[Dict[str, Any]] = None,
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
        task = process_full_pipeline_task(
            file_url, file_content, reference_data, processing_options
        )

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
                error_message=None,
            ),
            llm_analysis=PipelineStageStatus(
                stage=2,
                name="LLM Analysis",
                status="pending",
                progress=0,
                start_time=None,
                end_time=None,
                output_ready=False,
                error_message=None,
            ),
            report_generation=PipelineStageStatus(
                stage=3,
                name="Report Generation",
                status="pending",
                progress=0,
                start_time=None,
                end_time=None,
                output_ready=False,
                error_message=None,
            ),
        )

        return {
            "task_id": task_id,
            "status": "queued",
            "message": "Full pipeline processing started using core services",
            "pipeline_stages": pipeline_stages,
        }

    @staticmethod
    async def process_pipeline_sync(
        file_url: Optional[str] = None,
        file_content: Optional[str] = None,
        reference_data: Optional[Dict[str, Any]] = None,
        processing_options: Optional[Dict[str, Any]] = None,
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
                    "processing_options": processing_options,
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
                                "pipeline_stages": result.get("pipeline_stages", []),
                            },
                        },
                    }
                else:
                    return {
                        "success": False,
                        "task_id": task_id,
                        "status": "failed",
                        "message": f"Pipeline processing failed at stage: {result.get('stage', 'unknown')}",
                        "error": result.get("error", "Unknown error"),
                    }

            finally:
                await pipeline_service.stop()

        except Exception as e:
            return {
                "success": False,
                "task_id": task_id if "task_id" in locals() else None,
                "status": "failed",
                "message": "Pipeline processing failed",
                "error": str(e),
            }

    @staticmethod
    def get_pipeline_status(task_id: str) -> PipelineStatus:
        from task_queue import huey

        task = huey.find_task(task_id)
        if task is None:
            status = "not_found"
            progress = 0
        elif task.status == "pending":
            status = "queued"
            progress = 0
        elif task.status == "running":
            status = "processing"
            progress = 50
        elif task.status == "finished":
            status = "completed"
            progress = 100
        else:
            status = task.status
            progress = 0

        # Simple stages based on overall status
        stages = PipelineStages(
            pdf_extraction=PipelineStageStatus(
                stage=1, name="PDF Content Extraction", status=status, progress=progress
            ),
            llm_analysis=PipelineStageStatus(
                stage=2, name="LLM Analysis", status=status, progress=progress
            ),
            report_generation=PipelineStageStatus(
                stage=3, name="Report Generation", status=status, progress=progress
            ),
        )

        return PipelineStatus(
            task_id=task_id,
            status=status,
            progress=progress,
            overall_progress=progress,
            current_stage=status,
            stages=stages,
        )

    @staticmethod
    def get_pipeline_result(task_id: str) -> Optional[PipelineResult]:
        from task_queue import huey

        result = huey.result(task_id)
        if result is None:
            return None

        try:
            report = result["results"]["final_report"]

            final_report = FinalReport(**report) if report else None

            pipeline_metadata = {
                "total_processing_time": f"{result['processing_time_seconds']:.1f} seconds",
                "services_used": ["pdf_parser", "declaration_analyzer", "full_pipeline"],
                "processing_method": "core_services_orchestration",
                "architecture": "microservices_coordination",
            }

            return PipelineResult(
                task_id=task_id,
                overall_status=result["status"],
                processing_time=f"{result['processing_time_seconds']:.1f} seconds",
                final_report=final_report,
                pipeline_metadata=pipeline_metadata,
            )
        except (KeyError, TypeError) as e:
            logger.error(f"Error mapping pipeline result: {e}")
            return None
