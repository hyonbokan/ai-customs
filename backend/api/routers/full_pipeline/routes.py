"""
Full Pipeline Router for Customs Analysis.

Exposes a single synchronous endpoint that runs the complete pipeline:
PDF parsing -> LLM analysis -> final report.
"""

from fastapi import APIRouter, HTTPException

from api.routers.full_pipeline.schema import FullPipelineRequest, FullPipelineResponse
from api.routers.full_pipeline.service import FullPipelineService

router = APIRouter(tags=["full-pipeline"], prefix="/full-pipeline")


@router.post(
    "/process", response_model=FullPipelineResponse, summary="Complete Pipeline Processing"
)
async def process_full_pipeline(request: FullPipelineRequest) -> FullPipelineResponse:
    """
    Process a complete customs analysis pipeline from document to final report.

    **Workflow (synchronous):**
    1. **PDF Parsing** — extract clean content using Docling (no field extraction)
    2. **LLM Analysis** — intelligent field extraction and discrepancy detection
    3. **Final Report** — comprehensive analysis report

    Returns when processing is complete, with the full pipeline result.
    """
    try:
        return await FullPipelineService.process(
            file_url=request.file_url,
            file_content=request.file_content,
            reference_data=request.reference_data,
            processing_options=(
                request.processing_options.model_dump() if request.processing_options else None
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
