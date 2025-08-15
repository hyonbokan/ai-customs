"""
Base Service class providing common service functionality and orchestration.
"""

import abc
import asyncio
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type

from core.initializers.base_initializer import BaseInitializer
from core.utils.errors import ConfigurationError
from core.utils.logger import logger


class ServiceStatus(Enum):
    """Service status enumeration."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class ServiceState:
    """Tracks the state of a service."""

    def __init__(self, name: str):
        self.name = name
        self.status = ServiceStatus.STOPPED
        self.started_at: Optional[datetime] = None
        self.stopped_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.metadata: Dict[str, Any] = {}
        self.metrics: Dict[str, Any] = {}

    def mark_starting(self):
        """Mark service as starting."""
        self.status = ServiceStatus.STARTING
        logger.info(f"Service '{self.name}' starting")

    def mark_running(self, metadata: Optional[Dict[str, Any]] = None):
        """Mark service as running."""
        self.status = ServiceStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.stopped_at = None
        self.error_message = None
        if metadata:
            self.metadata.update(metadata)
        logger.info(f"Service '{self.name}' is now running")

    def mark_stopping(self):
        """Mark service as stopping."""
        self.status = ServiceStatus.STOPPING
        logger.info(f"Service '{self.name}' stopping")

    def mark_stopped(self):
        """Mark service as stopped."""
        self.status = ServiceStatus.STOPPED
        self.stopped_at = datetime.utcnow()
        logger.info(f"Service '{self.name}' stopped")

    def mark_error(self, error: str):
        """Mark service as having an error."""
        self.status = ServiceStatus.ERROR
        self.error_message = error
        logger.error(f"Service '{self.name}' error: {error}")

    def update_metrics(self, metrics: Dict[str, Any]):
        """Update service metrics."""
        self.metrics.update(metrics)


class BaseService(abc.ABC):
    """
    Base class for all services providing common functionality.

    This class provides:
    - Service lifecycle management (start, stop, restart)
    - Configuration management
    - Health checking and monitoring
    - Error handling and recovery
    - Metrics collection
    - Event hooks for extensibility
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base service.

        Args:
            name: Unique name for this service
            config: Configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self.state = ServiceState(name)
        self._initializers: List[BaseInitializer] = []
        self._event_handlers: Dict[str, List[Callable]] = {}

        # Validate configuration
        self._validate_config()

    @property
    def is_running(self) -> bool:
        """Check if service is running."""
        return self.state.status == ServiceStatus.RUNNING

    @property
    def is_healthy(self) -> bool:
        """Quick health check."""
        return self.is_running and self.state.status != ServiceStatus.ERROR

    @abc.abstractmethod
    async def _start(self) -> Dict[str, Any]:
        """
        Perform the actual service start work.

        Returns:
            Metadata dictionary about the service startup
        """
        pass

    @abc.abstractmethod
    async def _stop(self) -> None:
        """
        Perform the actual service stop work.
        """
        pass

    @abc.abstractmethod
    def _validate_config(self) -> None:
        """
        Validate the configuration for this service.

        Raises:
            ConfigurationError: If configuration is invalid
        """
        pass

    def add_initializer(self, initializer: BaseInitializer) -> None:
        """
        Add an initializer that must complete before this service starts.

        Args:
            initializer: The initializer to add
        """
        self._initializers.append(initializer)
        logger.debug(f"Added initializer '{initializer.name}' to service '{self.name}'")

    def add_event_handler(self, event: str, handler: Callable) -> None:
        """
        Add an event handler for service events.

        Args:
            event: Event name (start, stop, error, health_check)
            handler: Callable to handle the event
        """
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)
        logger.debug(f"Added event handler for '{event}' to service '{self.name}'")

    async def _emit_event(self, event: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Emit an event to all registered handlers."""
        if event in self._event_handlers:
            for handler in self._event_handlers[event]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(self, event, data or {})
                    else:
                        handler(self, event, data or {})
                except Exception as e:
                    logger.error(f"Error in event handler for '{event}': {e}", exc_info=True)

    async def start(self, force: bool = False) -> bool:
        """
        Start the service.

        Args:
            force: Force start even if already running

        Returns:
            True if successful, False otherwise
        """
        if self.is_running and not force:
            logger.debug(f"Service '{self.name}' already running")
            return True

        try:
            self.state.mark_starting()
            await self._emit_event("starting")

            # Wait for all initializers to be ready
            await self._wait_for_initializers()

            # Pre-start hook
            await self._pre_start()

            # Main service start
            metadata = await self._start()

            # Post-start hook
            await self._post_start(metadata)

            # Mark as running
            self.state.mark_running(metadata)
            await self._emit_event("started", metadata)

            return True

        except Exception as e:
            error_msg = f"Service start failed: {str(e)}"
            self.state.mark_error(error_msg)
            await self._emit_event("error", {"error": str(e)})
            logger.error(f"Service '{self.name}' start failed", exc_info=True)
            return False

    async def stop(self, force: bool = False) -> bool:
        """
        Stop the service.

        Args:
            force: Force stop even if not running

        Returns:
            True if successful, False otherwise
        """
        if not self.is_running and not force:
            logger.debug(f"Service '{self.name}' not running")
            return True

        try:
            self.state.mark_stopping()
            await self._emit_event("stopping")

            # Pre-stop hook
            await self._pre_stop()

            # Main service stop
            await self._stop()

            # Post-stop hook
            await self._post_stop()

            # Mark as stopped
            self.state.mark_stopped()
            await self._emit_event("stopped")

            return True

        except Exception as e:
            error_msg = f"Service stop failed: {str(e)}"
            self.state.mark_error(error_msg)
            await self._emit_event("error", {"error": str(e)})
            logger.error(f"Service '{self.name}' stop failed", exc_info=True)
            return False

    async def restart(self) -> bool:
        """
        Restart the service.

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Restarting service '{self.name}'")

        if self.is_running:
            if not await self.stop():
                return False

        return await self.start()

    async def _wait_for_initializers(self) -> None:
        """Wait for all required initializers to be ready."""
        if not self._initializers:
            return

        logger.debug(
            f"Waiting for {len(self._initializers)} initializers for service '{self.name}'"
        )

        # Check each initializer
        for initializer in self._initializers:
            max_wait = 60  # seconds
            wait_time = 0

            while not initializer.is_initialized and wait_time < max_wait:
                await asyncio.sleep(1)
                wait_time += 1

            if not initializer.is_initialized:
                raise ConfigurationError(
                    f"Initializer '{initializer.name}' not ready after {max_wait}s for service '{self.name}'"
                )

        logger.debug(f"All initializers ready for service '{self.name}'")

    async def _pre_start(self) -> None:
        """Hook called before service start. Override in subclasses."""
        pass

    async def _post_start(self, metadata: Dict[str, Any]) -> None:
        """Hook called after successful service start. Override in subclasses."""
        pass

    async def _pre_stop(self) -> None:
        """Hook called before service stop. Override in subclasses."""
        pass

    async def _post_stop(self) -> None:
        """Hook called after service stop. Override in subclasses."""
        pass

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the service.

        Returns:
            Health status dictionary
        """
        if not self.is_running:
            return {
                "status": "unhealthy",
                "message": "Service not running",
                "details": {"service_status": self.state.status.value},
            }

        try:
            # Perform service-specific health check
            service_health = await self._health_check()

            # Emit health check event
            await self._emit_event("health_check", service_health)

            return {
                "status": "healthy",
                "message": "Service is healthy",
                "details": {
                    "started_at": (
                        self.state.started_at.isoformat() if self.state.started_at else None
                    ),
                    "service_details": service_health,
                    "metrics": self.state.metrics,
                },
            }

        except Exception as e:
            error_result = {
                "status": "unhealthy",
                "message": f"Health check failed: {str(e)}",
                "details": {"error": str(e)},
            }
            await self._emit_event("health_check_failed", error_result)
            return error_result

    async def _health_check(self) -> Dict[str, Any]:
        """
        Service-specific health check. Override in subclasses.

        Returns:
            Service health details
        """
        return {"status": "ok"}

    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get service metrics.

        Returns:
            Service metrics dictionary
        """
        # Default metrics
        base_metrics = {
            "service_name": self.name,
            "status": self.state.status.value,
            "uptime_seconds": (
                (datetime.utcnow() - self.state.started_at).total_seconds()
                if self.state.started_at
                else 0
            ),
            "is_healthy": self.is_healthy,
        }

        # Get service-specific metrics
        try:
            service_metrics = await self._get_metrics()
            base_metrics.update(service_metrics)
        except Exception as e:
            logger.error(f"Error getting metrics for service '{self.name}': {e}")
            base_metrics["metrics_error"] = str(e)

        # Update stored metrics
        self.state.update_metrics(base_metrics)

        return base_metrics

    async def _get_metrics(self) -> Dict[str, Any]:
        """
        Service-specific metrics collection. Override in subclasses.

        Returns:
            Service-specific metrics
        """
        return {}

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
                f"Required configuration key '{key}' missing for service '{self.name}'"
            )

        return default

    def get_status_info(self) -> Dict[str, Any]:
        """
        Get detailed status information about the service.

        Returns:
            Status information dictionary
        """
        return {
            "name": self.name,
            "status": self.state.status.value,
            "started_at": self.state.started_at.isoformat() if self.state.started_at else None,
            "stopped_at": self.state.stopped_at.isoformat() if self.state.stopped_at else None,
            "error_message": self.state.error_message,
            "is_running": self.is_running,
            "is_healthy": self.is_healthy,
            "initializers_count": len(self._initializers),
            "metadata": self.state.metadata,
        }

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', status='{self.state.status.value}')"

    def __repr__(self) -> str:
        return self.__str__()
