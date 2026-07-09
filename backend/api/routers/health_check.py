from fastapi import APIRouter, Request

from core.schemas.api_response_schema import SuccessResponse
from core.utils.throttling import throttle

router = APIRouter(tags=["health"])


@router.get("/health-check", response_model=SuccessResponse)
@throttle(max_requests=50, use_ip=True)
async def health_check(request: Request):
    """Check if the API is operational."""
    return SuccessResponse(data={"details": "All systems operational"})
