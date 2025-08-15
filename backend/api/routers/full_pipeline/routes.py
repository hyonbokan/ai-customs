"""
Full Pipeline Router for Customs Analysis.

This router orchestrates the complete pipeline from PDF parsing to LLM analysis
to final report generation in a single endpoint.
"""

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from api.routers.full_pipeline.schema import FullPipelineRequest, FullPipelineResponse
from api.routers.full_pipeline.service import FullPipelineService
from core.schemas.api_response_schema import SuccessResponse

router = APIRouter(tags=["full-pipeline"], prefix="/full-pipeline")


@router.post(
    "/process", response_model=FullPipelineResponse, summary="Complete Pipeline Processing"
)
async def process_full_pipeline(request: FullPipelineRequest):
    """
    Process a complete customs analysis pipeline from PDF to final report.

    **Complete Workflow:**
    1. **PDF Parsing**: Extract clean content using Docling
    2. **LLM Analysis**: Extract fields and analyze discrepancies
    3. **Final Report**: Generate comprehensive analysis report

    **Processing Philosophy:**
    - PDF Parser: Clean content extraction (no field extraction)
    - LLM Service: Intelligent field extraction and analysis
    - No Regex: Language agnostic, format flexible approach

    **Returns immediately** with processing status and task ID for tracking.
    """
    try:
        result = await FullPipelineService.process_pipeline(
            request.file_url,
            request.file_content,
            request.reference_data,
            request.processing_options,
        )

        return FullPipelineResponse(
            success=True,
            task_id=result["task_id"],
            status=result["status"],
            message=result["message"],
            pipeline_stages=result["pipeline_stages"],
            error=None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline processing failed: {str(e)}")


@router.get("/status/{task_id}", response_model=SuccessResponse, summary="Check Pipeline Status")
async def get_pipeline_status(task_id: str):
    """
    Check the status of a full pipeline processing task.

    **Status Information:**
    - Overall pipeline progress
    - Current stage being processed
    - Individual service statuses
    - Estimated completion time
    """
    try:
        status = FullPipelineService.get_pipeline_status(task_id)
        return SuccessResponse(data=status.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pipeline status: {str(e)}")


@router.get("/result/{task_id}", response_model=SuccessResponse, summary="Get Pipeline Result")
async def get_pipeline_result(task_id: str):
    """
    Get the complete result of a finished pipeline processing.

    **Complete Results Include:**
    - PDF extraction results (clean content)
    - LLM analysis results (fields and discrepancies)
    - Final comprehensive report
    - Processing metadata and statistics
    """
    try:
        result = FullPipelineService.get_pipeline_result(task_id)

        if result:
            return SuccessResponse(
                data=result.dict(), message="Complete pipeline processing result with final report"
            )
        else:
            return SuccessResponse(
                data={"message": "Pipeline processing not found or still in progress"}
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pipeline result: {str(e)}")


@router.post(
    "/process-sync", response_model=FullPipelineResponse, summary="Synchronous Pipeline Processing"
)
async def process_pipeline_sync(request: FullPipelineRequest):
    """
    Process the complete pipeline synchronously (wait for completion).

    **Use for:**
    - Immediate results needed
    - Single document processing
    - Development and testing
    - When waiting for completion is acceptable

    **Complete Workflow (Synchronous):**
    1. PDF Parsing → Clean content extraction
    2. LLM Analysis → Field extraction and discrepancy analysis
    3. Final Report → Comprehensive analysis report

    **Returns when complete** with full pipeline results.
    """
    try:
        result = await FullPipelineService.process_pipeline_sync(
            request.file_url,
            request.file_content,
            request.reference_data,
            request.processing_options,
        )

        return FullPipelineResponse(
            success=result["success"],
            task_id=result.get("task_id"),
            status=result["status"],
            message=result["message"],
            pipeline_stages=result.get("pipeline_stages"),
            complete_result=result.get("complete_result"),
            error=result.get("error"),
        )
    except Exception as e:
        return FullPipelineResponse(
            success=False,
            task_id=None,
            status="failed",
            message="Pipeline processing failed",
            pipeline_stages=None,
            complete_result=None,
            error=str(e),
        )


@router.get("/capabilities", response_model=SuccessResponse, summary="Get Pipeline Capabilities")
async def get_pipeline_capabilities():
    """
    Get information about the full pipeline capabilities and configuration.
    """
    from config import config

    examples_dir = Path(__file__).parent.parent.parent / "examples"
    file_path = examples_dir / "full_pipeline_capabilities.json"
    capabilities = json.load(file_path.open())

    # Update with dynamic config values
    capabilities["configuration"]["pdf_parsing"]["ocr_enabled"] = config.pipeline.PDF_ENABLE_OCR
    capabilities["configuration"]["pdf_parsing"][
        "table_extraction"
    ] = config.pipeline.PDF_ENABLE_TABLES
    capabilities["configuration"]["pdf_parsing"][
        "supported_languages"
    ] = config.pipeline.PDF_OCR_LANGUAGES
    capabilities["configuration"]["pdf_parsing"][
        "max_file_size_mb"
    ] = config.pipeline.PDF_MAX_FILE_SIZE_MB
    capabilities["configuration"]["llm_analysis"][
        "confidence_threshold"
    ] = config.pipeline.LLM_CONFIDENCE_THRESHOLD
    capabilities["configuration"]["llm_analysis"][
        "timeout_seconds"
    ] = config.pipeline.LLM_ANALYSIS_TIMEOUT
    capabilities["configuration"]["llm_analysis"]["max_retries"] = config.pipeline.LLM_MAX_RETRIES

    return SuccessResponse(
        data=capabilities,
        message="Full pipeline orchestrates PDF parsing, LLM analysis, and report generation",
    )
