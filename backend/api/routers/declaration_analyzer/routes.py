from fastapi import APIRouter

from core.schemas.api_response_schema import SuccessResponse
from api.routers.declaration_analyzer.schema import CustomsDeclarationRequest
from api.routers.declaration_analyzer.service import DeclarationAnalyzerService

router = APIRouter(tags=["declaration-analyzer"])


@router.post("/analyze-declaration", response_model=SuccessResponse)
async def submit_declaration_analysis(request: CustomsDeclarationRequest):
    """
    Submit a customs declaration for AI analysis.
    Returns immediately while processing happens in background.
    """
    task_id = DeclarationAnalyzerService.submit_analysis(
        request.declaration_data, 
        request.reference_data
    )
    
    return SuccessResponse(
        data={
            "task_id": task_id,
            "status": "queued",
            "message": "Declaration analysis started"
        }
    )


@router.get("/analysis-status/{task_id}", response_model=SuccessResponse)
async def get_analysis_status(task_id: str):
    """Check the status of a customs declaration analysis."""
    status = DeclarationAnalyzerService.get_analysis_status(task_id)
    
    return SuccessResponse(data=status.dict())


@router.get("/analysis-result/{task_id}", response_model=SuccessResponse)
async def get_analysis_result(task_id: str):
    """Get the result of a completed analysis."""
    result = DeclarationAnalyzerService.get_analysis_result(task_id)
    
    if result:
        return SuccessResponse(data=result.dict())
    else:
        return SuccessResponse(
            data={"message": "Analysis not found or still processing"}
        ) 