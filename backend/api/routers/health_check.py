from typing import Any

from fastapi import APIRouter, Request

from config import config
from core.schemas.api_response_schema import SuccessResponse
from core.utils.logger import logger
from core.utils.throttling import throttle

router = APIRouter(tags=["health"])


async def _check_llm() -> dict[str, Any]:
    """Probe the configured LLM endpoint's /models route to confirm it's reachable."""
    base = config.llm.LLM_BASE_URL
    url = base.rstrip("/") + "/models"
    try:
        import aiohttp
    except ImportError:
        return {"reachable": None, "base_url": base, "detail": "aiohttp not installed"}

    timeout = aiohttp.ClientTimeout(total=config.pipeline.HEALTH_CHECK_TIMEOUT)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                return {
                    "reachable": resp.status < 500,
                    "base_url": base,
                    "status_code": resp.status,
                }
    except Exception as e:
        logger.warning(f"LLM health probe failed for {url}: {e}")
        return {"reachable": False, "base_url": base, "detail": str(e)}


@router.get("/health-check", response_model=SuccessResponse)
@throttle(max_requests=50, use_ip=True)
async def health_check(request: Request):
    """Report API liveness and whether the LLM server is reachable."""
    llm = await _check_llm()
    return SuccessResponse(
        data={
            "api": "ok",
            "llm": llm,
            "details": "All systems operational" if llm.get("reachable") else "LLM unreachable",
        }
    )
