from uuid import uuid4
from fastapi import APIRouter

from api.routers.declaration_analyzer.schema import CustomsDeclarationRequest, AnalysisResult
from api.routers.declaration_analyzer.service import DeclarationAnalyzerService

router = APIRouter(tags=["declaration-analyzer"])


@router.post("/analyze-declaration", response_model=AnalysisResult)
async def analyze_declaration(request: CustomsDeclarationRequest):
    """
    Analyze a customs declaration synchronously using AI.
    Returns the analysis result immediately.
    """
    result_dict = await DeclarationAnalyzerService.perform_analysis(
        request.declaration_data.dict(), 
        request.reference_data
    )
    
    return AnalysisResult(
        success=True,
        task_id=str(uuid4()),
        **result_dict
    ) 