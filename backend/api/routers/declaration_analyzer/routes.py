from fastapi import APIRouter, HTTPException

from api.routers.declaration_analyzer.schema import CustomsDeclarationRequest
from api.routers.declaration_analyzer.service import DeclarationAnalyzerService
from core.llm.response_models import CustomsAnalysisResponse

router = APIRouter(tags=["declaration-analyzer"])


@router.post("/analyze-declaration", response_model=CustomsAnalysisResponse)
async def analyze_declaration(request: CustomsDeclarationRequest) -> CustomsAnalysisResponse:
    """
    Analyze a customs declaration synchronously using AI.
    Returns the analysis result immediately.
    """
    try:
        # The service now directly returns the Pydantic model we want for the response
        analysis_report = await DeclarationAnalyzerService.perform_analysis(
            request.declaration_data.model_dump(), request.reference_data
        )
        return analysis_report
    except ValueError as e:
        # Handle validation errors from the service
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        # Ensure HTTP error when analysis fails (e.g., TGI unreachable)
        raise HTTPException(status_code=502, detail=f"Analysis failed: {e}")
