"""
Core Foundation Package

This package contains the foundational architecture for the AI customs pipeline system:
- Base classes for services and orchestrators
- Service registry and factory for dependency management  
- Pipeline manager for workflow orchestration
- Core orchestrators like CustomsPipelineService

Business logic services are located in api/routers/ for modularity and independent testing.
"""

from core.foundation.base_service import BaseService, ServiceStatus, ServiceState
from core.foundation.service_registry import ServiceRegistry
from core.foundation.service_factory import ServiceFactory
from core.foundation.pipeline_manager import PipelineManager

# Core orchestrators (not business logic services)
from core.foundation.customs_pipeline_service import CustomsPipelineService

__all__ = [
    # Base classes
    'BaseService',
    'ServiceStatus', 
    'ServiceState',
    
    # Core infrastructure
    'ServiceRegistry',
    'ServiceFactory',
    'PipelineManager',
    
    # Core orchestrators
    'CustomsPipelineService',
] 