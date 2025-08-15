"""
Service Registry for managing and discovering services.
"""

import asyncio
from collections import defaultdict
from typing import Any, Dict, List, Optional, Type

from core.foundation.base_service import BaseService, ServiceStatus
from core.utils.errors import ConfigurationError
from core.utils.logger import logger


class ServiceRegistry:
    """
    Registry for managing services with dependency resolution.

    Features:
    - Service registration and discovery
    - Dependency resolution
    - Parallel service management
    - Health monitoring
    - Graceful shutdown
    """

    def __init__(self):
        self._services: Dict[str, BaseService] = {}
        self._service_classes: Dict[str, Type[BaseService]] = {}
        self._dependency_graph: Dict[str, List[str]] = defaultdict(list)
        self._running_services: set = set()

    def register_service_class(self, name: str, service_class: Type[BaseService]) -> None:
        """
        Register a service class that can be instantiated later.

        Args:
            name: Unique name for the service
            service_class: The service class to register
        """
        if not issubclass(service_class, BaseService):
            raise ConfigurationError(
                f"Service class {service_class.__name__} must inherit from BaseService"
            )

        self._service_classes[name] = service_class
        logger.debug(f"Registered service class '{name}': {service_class.__name__}")

    def register_service(
        self, service: BaseService, dependencies: Optional[List[str]] = None
    ) -> None:
        """
        Register a service instance.

        Args:
            service: The service instance to register
            dependencies: List of service names this service depends on
        """
        name = service.name

        if name in self._services:
            logger.warning(f"Overriding existing service '{name}'")

        self._services[name] = service

        # Build dependency graph
        dependencies = dependencies or []
        self._dependency_graph[name] = dependencies

        logger.debug(f"Registered service '{name}' with dependencies: {dependencies}")

    def create_service(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        dependencies: Optional[List[str]] = None,
    ) -> BaseService:
        """
        Create a service instance from a registered class.

        Args:
            name: Name of the service class to create
            config: Configuration for the service
            dependencies: List of service names this service depends on

        Returns:
            Created service instance
        """
        if name not in self._service_classes:
            raise ConfigurationError(f"Service class '{name}' not registered")

        service_class = self._service_classes[name]
        service = service_class(name=name, config=config or {})

        # Register the instance
        self.register_service(service, dependencies)

        return service

    def get_service(self, name: str) -> Optional[BaseService]:
        """Get a service by name."""
        return self._services.get(name)

    def list_services(self) -> List[str]:
        """Get list of all registered service names."""
        return list(self._services.keys())

    def list_running_services(self) -> List[str]:
        """Get list of currently running service names."""
        return [name for name, service in self._services.items() if service.is_running]

    def _resolve_dependencies(
        self, services_to_start: Optional[List[str]] = None
    ) -> List[List[str]]:
        """
        Resolve dependencies and return start order in batches.

        Args:
            services_to_start: List of service names to start (default: all services)

        Returns:
            List of batches, where each batch contains services that can start in parallel
        """
        if services_to_start is None:
            services_to_start = list(self._services.keys())

        # Validate that all requested services exist
        for service_name in services_to_start:
            if service_name not in self._services:
                raise ConfigurationError(f"Service '{service_name}' not registered")

        # Topological sort with batching
        in_degree = defaultdict(int)
        graph = defaultdict(list)

        # Build the graph for requested services
        for name in services_to_start:
            deps = self._dependency_graph.get(name, [])
            for dep in deps:
                if dep not in self._services:
                    raise ConfigurationError(
                        f"Service '{name}' depends on '{dep}' which is not registered"
                    )
                if dep in services_to_start:  # Only consider dependencies within the requested set
                    graph[dep].append(name)
                    in_degree[name] += 1

        # Initialize in_degree for all requested services
        for name in services_to_start:
            if name not in in_degree:
                in_degree[name] = 0

        # Process in batches
        batches = []
        remaining = set(services_to_start)

        while remaining:
            # Find all services with in_degree 0 in remaining set
            batch = [name for name in remaining if in_degree[name] == 0]

            if not batch:
                # Circular dependency detected
                raise ConfigurationError(
                    f"Circular dependency detected among services: {remaining}"
                )

            batches.append(batch)

            # Remove batch from remaining and update in_degrees
            for name in batch:
                remaining.remove(name)
                for neighbor in graph[name]:
                    in_degree[neighbor] -= 1

        return batches

    async def start_service(self, name: str, force: bool = False) -> bool:
        """
        Start a single service.

        Args:
            name: Name of the service to start
            force: Force start even if already running

        Returns:
            True if successful
        """
        if name not in self._services:
            raise ConfigurationError(f"Service '{name}' not registered")

        service = self._services[name]

        if service.is_running and not force:
            logger.debug(f"Service '{name}' already running")
            return True

        success = await service.start(force=force)
        if success:
            self._running_services.add(name)

        return success

    async def stop_service(self, name: str, force: bool = False) -> bool:
        """
        Stop a single service.

        Args:
            name: Name of the service to stop
            force: Force stop even if not running

        Returns:
            True if successful
        """
        if name not in self._services:
            raise ConfigurationError(f"Service '{name}' not registered")

        service = self._services[name]

        success = await service.stop(force=force)
        if success:
            self._running_services.discard(name)

        return success

    async def restart_service(self, name: str) -> bool:
        """
        Restart a single service.

        Args:
            name: Name of the service to restart

        Returns:
            True if successful
        """
        if name not in self._services:
            raise ConfigurationError(f"Service '{name}' not registered")

        service = self._services[name]
        success = await service.restart()

        if success:
            self._running_services.add(name)
        else:
            self._running_services.discard(name)

        return success

    async def start_services(
        self, service_names: Optional[List[str]] = None, force: bool = False
    ) -> bool:
        """
        Start multiple services in dependency order.

        Args:
            service_names: List of service names to start (default: all services)
            force: Force start even if already running

        Returns:
            True if all services started successfully
        """
        services_to_start = service_names or list(self._services.keys())

        if not services_to_start:
            logger.info("No services to start")
            return True

        logger.info(f"Starting services: {services_to_start}")

        try:
            # Resolve dependencies into batches
            batches = self._resolve_dependencies(services_to_start)

            # Start each batch in parallel
            for batch_idx, batch in enumerate(batches):
                logger.info(f"Starting service batch {batch_idx + 1}/{len(batches)}: {batch}")

                # Create tasks for this batch
                tasks = []
                for name in batch:
                    service = self._services[name]
                    task = asyncio.create_task(service.start(force=force), name=f"start_{name}")
                    tasks.append((name, task))

                # Wait for all tasks in this batch to complete
                results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)

                # Check results
                failed_services = []
                for (name, task), result in zip(tasks, results):
                    if isinstance(result, Exception):
                        logger.error(f"Service '{name}' failed with exception: {result}")
                        failed_services.append(name)
                    elif not result:
                        logger.error(f"Service '{name}' failed to start")
                        failed_services.append(name)
                    else:
                        logger.info(f"Service '{name}' started successfully")
                        self._running_services.add(name)

                if failed_services:
                    raise ConfigurationError(f"Failed to start services: {failed_services}")

            logger.info("All services started successfully")
            return True

        except Exception as e:
            logger.error(f"Service startup failed: {e}", exc_info=True)
            return False

    async def stop_services(
        self, service_names: Optional[List[str]] = None, force: bool = False
    ) -> bool:
        """
        Stop multiple services in reverse dependency order.

        Args:
            service_names: List of service names to stop (default: all running services)
            force: Force stop even if not running

        Returns:
            True if all services stopped successfully
        """
        if service_names is None:
            services_to_stop = self.list_running_services()
        else:
            services_to_stop = service_names

        if not services_to_stop:
            logger.info("No services to stop")
            return True

        logger.info(f"Stopping services: {services_to_stop}")

        try:
            # Get dependency order and reverse it for shutdown
            batches = self._resolve_dependencies(services_to_stop)
            stop_batches = list(reversed(batches))

            # Stop each batch
            for batch_idx, batch in enumerate(stop_batches):
                logger.info(f"Stopping service batch {batch_idx + 1}/{len(stop_batches)}: {batch}")

                # Create stop tasks for this batch
                tasks = []
                for name in batch:
                    if name in services_to_stop:  # Only stop requested services
                        service = self._services[name]
                        task = asyncio.create_task(service.stop(force=force), name=f"stop_{name}")
                        tasks.append((name, task))

                # Wait for all stop tasks in this batch
                results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)

                # Log stop results
                for (name, task), result in zip(tasks, results):
                    if isinstance(result, Exception):
                        logger.error(f"Stop failed for service '{name}': {result}")
                    elif not result:
                        logger.error(f"Failed to stop service '{name}'")
                    else:
                        logger.info(f"Service '{name}' stopped successfully")
                        self._running_services.discard(name)

            logger.info("All services stopped")
            return True

        except Exception as e:
            logger.error(f"Error during service shutdown: {e}", exc_info=True)
            return False

    async def health_check_all(self) -> Dict[str, Any]:
        """
        Perform health check on all services.

        Returns:
            Overall health status and individual service health
        """
        if not self._services:
            return {
                "overall_status": "healthy",
                "message": "No services registered",
                "services": {},
            }

        health_results = {}
        unhealthy_count = 0

        # Run health checks in parallel
        tasks = []
        for name, service in self._services.items():
            task = asyncio.create_task(service.health_check(), name=f"health_{name}")
            tasks.append((name, task))

        results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)

        for (name, task), result in zip(tasks, results):
            if isinstance(result, Exception):
                health_results[name] = {
                    "status": "unhealthy",
                    "message": f"Health check failed: {result}",
                    "details": {"error": str(result)},
                }
                unhealthy_count += 1
            else:
                health_results[name] = result
                if isinstance(result, dict) and result.get("status") != "healthy":
                    unhealthy_count += 1

        overall_status = "healthy" if unhealthy_count == 0 else "unhealthy"

        return {
            "overall_status": overall_status,
            "message": f"{len(self._services) - unhealthy_count}/{len(self._services)} services healthy",
            "unhealthy_count": unhealthy_count,
            "running_count": len(self._running_services),
            "services": health_results,
        }

    async def get_metrics_all(self) -> Dict[str, Any]:
        """
        Get metrics from all services.

        Returns:
            Combined metrics from all services
        """
        if not self._services:
            return {"overall_metrics": {"total_services": 0, "running_services": 0}, "services": {}}

        service_metrics = {}

        # Get metrics from all services in parallel
        tasks = []
        for name, service in self._services.items():
            task = asyncio.create_task(service.get_metrics(), name=f"metrics_{name}")
            tasks.append((name, task))

        results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)

        for (name, task), result in zip(tasks, results):
            if isinstance(result, Exception):
                service_metrics[name] = {"error": f"Metrics collection failed: {result}"}
            else:
                service_metrics[name] = result

        overall_metrics = {
            "total_services": len(self._services),
            "running_services": len(self._running_services),
            "healthy_services": sum(
                1
                for metrics in service_metrics.values()
                if isinstance(metrics, dict) and metrics.get("is_healthy", False)
            ),
        }

        return {"overall_metrics": overall_metrics, "services": service_metrics}

    def get_status_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all service statuses.

        Returns:
            Status summary dictionary
        """
        if not self._services:
            return {"total_count": 0, "running_count": 0, "status_breakdown": {}, "services": {}}

        status_breakdown = defaultdict(int)
        services_status = {}

        for name, service in self._services.items():
            status = service.state.status.value
            status_breakdown[status] += 1

            services_status[name] = service.get_status_info()

        return {
            "total_count": len(self._services),
            "running_count": len(self._running_services),
            "status_breakdown": dict(status_breakdown),
            "services": services_status,
        }

    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """
        Get the current dependency graph.

        Returns:
            Dependency graph dictionary
        """
        return dict(self._dependency_graph)


# Global registry instance
registry = ServiceRegistry()
