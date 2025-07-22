"""
Service Factory for configuration-driven service creation and management.
"""

from typing import Dict, List, Any, Optional, Type
import importlib
import inspect

from core.utils.logger import logger
from core.utils.errors import ConfigurationError
from core.foundation.base_service import BaseService
from core.foundation.service_registry import ServiceRegistry
from core.foundation.pipeline_manager import PipelineManager, PipelineStage
from core.initializers.base_initializer import BaseInitializer
from core.initializers.initializer_registry import InitializerRegistry


class ServiceFactory:
    """
    Factory for creating and configuring services from configuration.
    
    Features:
    - Configuration-driven service creation
    - Automatic dependency injection
    - Pipeline setup from configuration
    - Service discovery and registration
    """
    
    def __init__(self, service_registry: Optional[ServiceRegistry] = None,
                 initializer_registry: Optional[InitializerRegistry] = None):
        self.service_registry = service_registry or ServiceRegistry()
        self.initializer_registry = initializer_registry or InitializerRegistry()
        self.pipeline_manager = PipelineManager(self.service_registry)
        self._class_cache: Dict[str, Type] = {}
    
    def load_class_by_name(self, class_path: str) -> Type:
        """
        Load a class by its full module path.
        
        Args:
            class_path: Full path to the class (e.g., 'core.foundation.MyService')
            
        Returns:
            The loaded class
        """
        if class_path in self._class_cache:
            return self._class_cache[class_path]
        
        try:
            # Split module and class name
            if '.' not in class_path:
                raise ConfigurationError(f"Invalid class path '{class_path}': must include module")
            
            module_path, class_name = class_path.rsplit('.', 1)
            
            # Import the module
            module = importlib.import_module(module_path)
            
            # Get the class
            if not hasattr(module, class_name):
                raise ConfigurationError(f"Class '{class_name}' not found in module '{module_path}'")
            
            cls = getattr(module, class_name)
            
            # Cache the class
            self._class_cache[class_path] = cls
            
            return cls
            
        except ImportError as e:
            raise ConfigurationError(f"Failed to import module '{module_path}': {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load class '{class_path}': {e}")
    
    def create_initializer_from_config(self, config: Dict[str, Any]) -> BaseInitializer:
        """
        Create an initializer from configuration.
        
        Args:
            config: Initializer configuration
            
        Returns:
            Created initializer instance
        """
        required_fields = ['name', 'class']
        for field in required_fields:
            if field not in config:
                raise ConfigurationError(f"Missing required field '{field}' in initializer config")
        
        name = config['name']
        class_path = config['class']
        initializer_config = config.get('config', {})
        
        # Load the initializer class
        initializer_class = self.load_class_by_name(class_path)
        
        # Validate it's an initializer
        if not issubclass(initializer_class, BaseInitializer):
            raise ConfigurationError(f"Class '{class_path}' is not a BaseInitializer")
        
        # Create the initializer
        initializer = initializer_class(name=name, config=initializer_config)
        
        # Set dependencies if specified
        if 'dependencies' in config:
            initializer.state.dependencies = config['dependencies']
        
        logger.debug(f"Created initializer '{name}' from config")
        return initializer
    
    def create_service_from_config(self, config: Dict[str, Any]) -> BaseService:
        """
        Create a service from configuration.
        
        Args:
            config: Service configuration
            
        Returns:
            Created service instance
        """
        required_fields = ['name', 'class']
        for field in required_fields:
            if field not in config:
                raise ConfigurationError(f"Missing required field '{field}' in service config")
        
        name = config['name']
        class_path = config['class']
        service_config = config.get('config', {})
        
        # Load the service class
        service_class = self.load_class_by_name(class_path)
        
        # Validate it's a service
        if not issubclass(service_class, BaseService):
            raise ConfigurationError(f"Class '{class_path}' is not a BaseService")
        
        # Create the service
        service = service_class(name=name, config=service_config)
        
        # Add initializer dependencies
        if 'initializers' in config:
            for init_name in config['initializers']:
                initializer = self.initializer_registry.get_initializer(init_name)
                if not initializer:
                    raise ConfigurationError(f"Initializer '{init_name}' not found for service '{name}'")
                service.add_initializer(initializer)
        
        logger.debug(f"Created service '{name}' from config")
        return service
    
    def setup_from_config(self, config: Dict[str, Any]) -> None:
        """
        Set up services and pipelines from configuration.
        
        Args:
            config: Complete system configuration
        """
        logger.info("Setting up services from configuration")
        
        # 1. Create initializers
        if 'initializers' in config:
            logger.info(f"Creating {len(config['initializers'])} initializers")
            for init_config in config['initializers']:
                initializer = self.create_initializer_from_config(init_config)
                self.initializer_registry.register_initializer(initializer)
        
        # 2. Create services
        if 'services' in config:
            logger.info(f"Creating {len(config['services'])} services")
            for service_config in config['services']:
                service = self.create_service_from_config(service_config)
                dependencies = service_config.get('dependencies', [])
                self.service_registry.register_service(service, dependencies)
        
        # 3. Set up pipelines
        if 'pipelines' in config:
            logger.info(f"Creating {len(config['pipelines'])} pipelines")
            for pipeline_config in config['pipelines']:
                self.create_pipeline_from_config(pipeline_config)
        
        logger.info("Service setup from configuration completed")
    
    def create_pipeline_from_config(self, config: Dict[str, Any]) -> None:
        """
        Create a pipeline from configuration.
        
        Args:
            config: Pipeline configuration
        """
        required_fields = ['name', 'stages']
        for field in required_fields:
            if field not in config:
                raise ConfigurationError(f"Missing required field '{field}' in pipeline config")
        
        pipeline_name = config['name']
        stages_config = config['stages']
        
        # Create the pipeline
        self.pipeline_manager.create_pipeline(pipeline_name)
        
        # Add stages
        for stage_config in stages_config:
            stage = self.create_stage_from_config(stage_config)
            self.pipeline_manager.add_stage(pipeline_name, stage)
        
        logger.debug(f"Created pipeline '{pipeline_name}' with {len(stages_config)} stages")
    
    def create_stage_from_config(self, config: Dict[str, Any]) -> PipelineStage:
        """
        Create a pipeline stage from configuration.
        
        Args:
            config: Stage configuration
            
        Returns:
            Created pipeline stage
        """
        required_fields = ['name', 'service']
        for field in required_fields:
            if field not in config:
                raise ConfigurationError(f"Missing required field '{field}' in stage config")
        
        name = config['name']
        service_name = config['service']
        stage_config = config.get('config', {})
        
        # Create the stage
        stage = PipelineStage(name, service_name, stage_config)
        
        # Set dependencies
        if 'dependencies' in config:
            for dep in config['dependencies']:
                stage.add_dependency(dep)
        
        # Set parallel execution
        if 'parallel' in config:
            stage.set_parallel(config['parallel'])
        
        # Set retry configuration
        if 'retry' in config:
            retry_config = config['retry']
            max_retries = retry_config.get('max_retries', 3)
            timeout_seconds = retry_config.get('timeout_seconds')
            stage.set_retry_config(max_retries, timeout_seconds)
        
        return stage
    
    async def initialize_all(self, force: bool = False) -> bool:
        """
        Initialize all registered initializers.
        
        Args:
            force: Force re-initialization
            
        Returns:
            True if all initializations succeeded
        """
        logger.info("Initializing all components")
        success = await self.initializer_registry.initialize_all(force=force)
        if success:
            logger.info("All initializers completed successfully")
        else:
            logger.error("Some initializers failed")
        return success
    
    async def start_all_services(self, force: bool = False) -> bool:
        """
        Start all registered services.
        
        Args:
            force: Force start even if already running
            
        Returns:
            True if all services started successfully
        """
        logger.info("Starting all services")
        success = await self.service_registry.start_services(force=force)
        if success:
            logger.info("All services started successfully")
        else:
            logger.error("Some services failed to start")
        return success
    
    async def stop_all_services(self, force: bool = False) -> bool:
        """
        Stop all running services.
        
        Args:
            force: Force stop even if not running
            
        Returns:
            True if all services stopped successfully
        """
        logger.info("Stopping all services")
        success = await self.service_registry.stop_services(force=force)
        if success:
            logger.info("All services stopped successfully")
        else:
            logger.error("Some services failed to stop")
        return success
    
    async def health_check_all(self) -> Dict[str, Any]:
        """
        Perform health check on all components.
        
        Returns:
            Combined health status
        """
        # Get initializer health
        initializer_health = await self.initializer_registry.health_check_all()
        
        # Get service health
        service_health = await self.service_registry.health_check_all()
        
        # Combine results
        overall_healthy = (
            initializer_health.get("overall_status") == "healthy" and
            service_health.get("overall_status") == "healthy"
        )
        
        return {
            "overall_status": "healthy" if overall_healthy else "unhealthy",
            "initializers": initializer_health,
            "services": service_health,
            "timestamp": "2024-01-01T00:00:00Z"  # Use actual timestamp
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status.
        
        Returns:
            System status summary
        """
        initializer_status = self.initializer_registry.get_status_summary()
        service_status = self.service_registry.get_status_summary()
        
        return {
            "initializers": {
                "total": initializer_status["total_count"],
                "ready": initializer_status["ready_count"],
                "status_breakdown": initializer_status["status_breakdown"]
            },
            "services": {
                "total": service_status["total_count"],
                "running": service_status["running_count"],
                "status_breakdown": service_status["status_breakdown"]
            },
            "pipelines": {
                "total": len(self.pipeline_manager.list_pipelines()),
                "available": self.pipeline_manager.list_pipelines()
            }
        }
    
    def create_example_config(self) -> Dict[str, Any]:
        """
        Create an example configuration for reference.
        
        Returns:
            Example configuration dictionary
        """
        return {
            "initializers": [
                {
                    "name": "llm_initializer",
                    "class": "core.initializers.LLMInitializer",
                    "config": {
                        "base_url": "http://localhost:8080/v1/",
                        "timeout": 30
                    },
                    "dependencies": []
                },
                {
                    "name": "database_initializer",
                    "class": "core.initializers.DatabaseInitializer",
                    "config": {
                        "connection_string": "sqlite:///./database/app.db"
                    },
                    "dependencies": []
                }
            ],
            "services": [
                {
                    "name": "pdf_parser_service",
                    "class": "api.routers.pdf_parser.service.PDFParserService",
                    "config": {
                        "max_file_size_mb": 50,
                        "supported_formats": ["pdf"]
                    },
                    "dependencies": [],
                    "initializers": ["llm_initializer"]
                },
                {
                    "name": "declaration_analyzer_service",
                    "class": "api.routers.declaration_analyzer.service.DeclarationAnalyzerService", 
                    "config": {
                        "analysis_timeout": 300,
                        "confidence_threshold": 0.8
                    },
                    "dependencies": ["pdf_parser_service"],
                    "initializers": ["llm_initializer", "database_initializer"]
                }
            ],
            "pipelines": [
                {
                    "name": "customs_analysis_pipeline",
                    "stages": [
                        {
                            "name": "parse_document",
                            "service": "pdf_parser_service",
                            "config": {
                                "extract_structured_data": True
                            },
                            "dependencies": [],
                            "parallel": False,
                            "retry": {
                                "max_retries": 2,
                                "timeout_seconds": 60
                            }
                        },
                        {
                            "name": "analyze_declaration",
                            "service": "declaration_analyzer_service",
                            "config": {
                                "deep_analysis": True
                            },
                            "dependencies": ["parse_document"],
                            "parallel": False,
                            "retry": {
                                "max_retries": 3,
                                "timeout_seconds": 180
                            }
                        }
                    ]
                }
            ]
        } 