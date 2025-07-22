"""
Base Initializer class providing common initialization functionality.
"""

import abc
import asyncio
from typing import Dict, Any, Optional, List, Type
from datetime import datetime

from core.utils.logger import logger
from core.utils.errors import ConfigurationError


class InitializerState:
    """Tracks the state of an initializer."""
    
    def __init__(self, name: str):
        self.name = name
        self.status = "pending"  # pending, initializing, ready, error
        self.initialized_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.dependencies: List[str] = []
        self.metadata: Dict[str, Any] = {}
    
    def mark_initializing(self):
        """Mark initializer as currently initializing."""
        self.status = "initializing"
        logger.info(f"Initializer '{self.name}' starting initialization")
    
    def mark_ready(self, metadata: Optional[Dict[str, Any]] = None):
        """Mark initializer as ready."""
        self.status = "ready"
        self.initialized_at = datetime.utcnow()
        if metadata:
            self.metadata.update(metadata)
        logger.info(f"Initializer '{self.name}' completed initialization")
    
    def mark_error(self, error: str):
        """Mark initializer as having an error."""
        self.status = "error"
        self.error_message = error
        logger.error(f"Initializer '{self.name}' failed: {error}")


class BaseInitializer(abc.ABC):
    """
    Base class for all initializers providing common functionality.
    
    This class provides:
    - Configuration loading and validation
    - Dependency management
    - Error handling and logging
    - State tracking
    - Health checking
    - Cleanup functionality
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base initializer.
        
        Args:
            name: Unique name for this initializer
            config: Configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self.state = InitializerState(name)
        self._is_initialized = False
        
        # Validate required configuration
        self._validate_config()
    
    @property
    def is_initialized(self) -> bool:
        """Check if initializer is ready."""
        return self._is_initialized and self.state.status == "ready"
    
    @property
    def dependencies(self) -> List[str]:
        """Get list of dependency names that must be initialized first."""
        return self.state.dependencies
    
    @abc.abstractmethod
    async def _initialize(self) -> Dict[str, Any]:
        """
        Perform the actual initialization work.
        
        Returns:
            Metadata dictionary about the initialization
        """
        pass
    
    @abc.abstractmethod
    def _validate_config(self) -> None:
        """
        Validate the configuration for this initializer.
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        pass
    
    async def initialize(self, force: bool = False) -> bool:
        """
        Initialize the component.
        
        Args:
            force: Force re-initialization even if already initialized
            
        Returns:
            True if successful, False otherwise
        """
        if self.is_initialized and not force:
            logger.debug(f"Initializer '{self.name}' already initialized")
            return True
        
        try:
            self.state.mark_initializing()
            
            # Pre-initialization hook
            await self._pre_initialize()
            
            # Main initialization
            metadata = await self._initialize()
            
            # Post-initialization hook
            await self._post_initialize(metadata)
            
            # Mark as ready
            self.state.mark_ready(metadata)
            self._is_initialized = True
            
            return True
            
        except Exception as e:
            error_msg = f"Initialization failed: {str(e)}"
            self.state.mark_error(error_msg)
            logger.error(f"Initializer '{self.name}' failed", exc_info=True)
            return False
    
    async def _pre_initialize(self) -> None:
        """Hook called before initialization. Override in subclasses."""
        pass
    
    async def _post_initialize(self, metadata: Dict[str, Any]) -> None:
        """Hook called after successful initialization. Override in subclasses."""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the initialized component.
        
        Returns:
            Health status dictionary
        """
        if not self.is_initialized:
            return {
                "status": "unhealthy",
                "message": "Component not initialized",
                "details": {"initializer_status": self.state.status}
            }
        
        try:
            # Perform component-specific health check
            component_health = await self._health_check()
            
            return {
                "status": "healthy",
                "message": "Component is healthy",
                "details": {
                    "initialized_at": self.state.initialized_at.isoformat() if self.state.initialized_at else None,
                    "component_details": component_health
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Health check failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def _health_check(self) -> Dict[str, Any]:
        """
        Component-specific health check. Override in subclasses.
        
        Returns:
            Component health details
        """
        return {"status": "ok"}
    
    async def cleanup(self) -> None:
        """
        Clean up resources used by this initializer.
        """
        try:
            await self._cleanup()
            logger.info(f"Initializer '{self.name}' cleaned up successfully")
        except Exception as e:
            logger.error(f"Error cleaning up initializer '{self.name}': {e}", exc_info=True)
    
    async def _cleanup(self) -> None:
        """Component-specific cleanup. Override in subclasses."""
        pass
    
    def get_config_value(self, key: str, default: Any = None, required: bool = False) -> Any:
        """
        Get a configuration value with validation.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            required: Whether the key is required
            
        Returns:
            Configuration value
            
        Raises:
            ConfigurationError: If required key is missing
        """
        if key in self.config:
            return self.config[key]
        
        if required:
            raise ConfigurationError(
                f"Required configuration key '{key}' missing for initializer '{self.name}'"
            )
        
        return default
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', status='{self.state.status}')"
    
    def __repr__(self) -> str:
        return self.__str__() 