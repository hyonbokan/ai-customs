from fastapi import APIRouter, Depends

from api.routers.declaration_analyzer.routes import router as declaration_analyzer_router
from api.routers.full_pipeline.routes import router as full_pipeline_router
from api.routers.health_check import router as health_check_router
from api.routers.pdf_parser.routes import router as pdf_parser_router
from config import config
from core.utils.auth import require_api_key

# Create the main v1 router
router = APIRouter(prefix="/v1")

# Health check is unauthenticated so liveness/readiness probes work without a key.
router.include_router(health_check_router)

# Data endpoints require an API key when ADMIN_API_KEY is configured.
protected = [Depends(require_api_key)]
router.include_router(declaration_analyzer_router, dependencies=protected)
router.include_router(pdf_parser_router, dependencies=protected)
router.include_router(full_pipeline_router, dependencies=protected)

# Register development-only routers
if config.app.ENVIRONMENT in ["development", "test"]:
    # Add development-only routers here when needed
    pass
