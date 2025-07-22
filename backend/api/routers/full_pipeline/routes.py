"""
Full Pipeline Router for Customs Analysis.

This router orchestrates the complete pipeline from PDF parsing to LLM analysis
to final report generation in a single endpoint.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from core.schemas.api_response_schema import SuccessResponse, ErrorResponse
from api.routers.full_pipeline.schema import (
    FullPipelineRequest,
    FullPipelineResponse,
    PipelineStatus,
    PipelineResult
)
from api.routers.full_pipeline.service import FullPipelineService

router = APIRouter(tags=["full-pipeline"], prefix="/full-pipeline")


@router.post("/process", response_model=FullPipelineResponse, summary="Complete Pipeline Processing")
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
            request.processing_options
        )
        
        return FullPipelineResponse(
            success=True,
            task_id=result["task_id"],
            status=result["status"],
            message=result["message"],
            pipeline_stages=result["pipeline_stages"],
            error=None
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
                data=result.dict(),
                message="Complete pipeline processing result with final report"
            )
        else:
            return SuccessResponse(
                data={"message": "Pipeline processing not found or still in progress"}
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pipeline result: {str(e)}")


@router.post("/process-sync", response_model=FullPipelineResponse, summary="Synchronous Pipeline Processing")
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
            request.processing_options
        )
        
        return FullPipelineResponse(
            success=result["success"],
            task_id=result.get("task_id"),
            status=result["status"],
            message=result["message"],
            pipeline_stages=result.get("pipeline_stages"),
            complete_result=result.get("complete_result"),
            error=result.get("error")
        )
    except Exception as e:
        return FullPipelineResponse(
            success=False,
            task_id=None,
            status="failed",
            message="Pipeline processing failed",
            pipeline_stages=None,
            complete_result=None,
            error=str(e)
        )


@router.get("/capabilities", response_model=SuccessResponse, summary="Get Pipeline Capabilities")
async def get_pipeline_capabilities():
    """
    Get information about the full pipeline capabilities and configuration.
    """
    from config import config
    
    capabilities = {
        "pipeline_overview": {
            "name": "AI Customs Analysis Pipeline",
            "version": "1.0",
            "description": "Complete automation from PDF parsing to analysis reporting",
            "architecture": "microservices_orchestration"
        },
        "processing_stages": [
            {
                "stage": 1,
                "name": "PDF Content Extraction",
                "service": "pdf_parser",
                "method": "docling_based_extraction",
                "output": "clean_content_for_llm",
                "features": [
                    "OCR support",
                    "Table extraction",
                    "Multi-language",
                    "Format detection"
                ]
            },
            {
                "stage": 2,
                "name": "LLM Field Extraction",
                "service": "declaration_analyzer",
                "method": "intelligent_field_extraction",
                "output": "structured_fields_and_analysis",
                "features": [
                    "Language agnostic",
                    "Format flexible",
                    "Intelligent extraction",
                    "Discrepancy detection"
                ]
            },
            {
                "stage": 3,
                "name": "Final Report Generation",
                "service": "full_pipeline",
                "method": "comprehensive_report_generation",
                "output": "complete_analysis_report",
                "features": [
                    "Executive summary",
                    "Detailed findings",
                    "Compliance assessment",
                    "Actionable recommendations"
                ]
            }
        ],
        "configuration": {
            "pdf_parsing": {
                "ocr_enabled": config.pipeline.PDF_ENABLE_OCR,
                "table_extraction": config.pipeline.PDF_ENABLE_TABLES,
                "supported_languages": config.pipeline.PDF_OCR_LANGUAGES,
                "max_file_size_mb": config.pipeline.PDF_MAX_FILE_SIZE_MB
            },
            "llm_analysis": {
                "confidence_threshold": config.pipeline.LLM_CONFIDENCE_THRESHOLD,
                "timeout_seconds": config.pipeline.LLM_ANALYSIS_TIMEOUT,
                "max_retries": config.pipeline.LLM_MAX_RETRIES
            }
        },
        "benefits": {
            "automation": "Complete end-to-end automation",
            "accuracy": "AI-powered intelligent processing",
            "flexibility": "Handles any document format or language",
            "scalability": "Microservices architecture",
            "maintainability": "No brittle regex patterns"
        },
        "use_cases": [
            "Commercial invoice analysis",
            "Customs declaration review",
            "Certificate of origin verification",
            "Packing list validation",
            "Bill of lading analysis"
        ]
    }
    
    return SuccessResponse(
        data=capabilities,
        message="Full pipeline orchestrates PDF parsing, LLM analysis, and report generation"
    ) 