from fastapi import APIRouter

from config import config
from api.routers.health_check import router as health_check_router
from api.routers.declaration_analyzer.routes import router as declaration_analyzer_router
from api.routers.pdf_parser.routes import router as pdf_parser_router
from api.routers.full_pipeline.routes import router as full_pipeline_router

# Create the main v1 router
router = APIRouter(prefix="/v1")

# Register all feature routers
router.include_router(health_check_router)
router.include_router(declaration_analyzer_router)
router.include_router(pdf_parser_router)
router.include_router(full_pipeline_router)

# Register development-only routers
if config.app.ENVIRONMENT in ["development", "test"]:
    # Add development-only routers here when needed
    pass 