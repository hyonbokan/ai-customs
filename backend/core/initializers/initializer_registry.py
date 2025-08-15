"""
Initializer Registry for managing and discovering initializers.
"""

import asyncio
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Type

from core.initializers.base_initializer import BaseInitializer
from core.utils.errors import ConfigurationError
from core.utils.logger import logger


class InitializerRegistry:
    """
    Registry for managing initializers with dependency resolution.

    Features:
    - Automatic dependency resolution
    - Parallel initialization where possible
    - Health monitoring
    - Graceful shutdown
    """

    def __init__(self):
        self._initializers: Dict[str, BaseInitializer] = {}
        self._initializer_classes: Dict[str, Type[BaseInitializer]] = {}
        self._dependency_graph: Dict[str, List[str]] = defaultdict(list)
        self._is_initialized = False

    def register_initializer_class(
        self, name: str, initializer_class: Type[BaseInitializer]
    ) -> None:
        """
        Register an initializer class that can be instantiated later.

        Args:
            name: Unique name for the initializer
            initializer_class: The initializer class to register
        """
        if not issubclass(initializer_class, BaseInitializer):
            raise ConfigurationError(
                f"Initializer class {initializer_class.__name__} must inherit from BaseInitializer"
            )

        self._initializer_classes[name] = initializer_class
        logger.debug(f"Registered initializer class '{name}': {initializer_class.__name__}")

    def register_initializer(self, initializer: BaseInitializer) -> None:
        """
        Register an initializer instance.

        Args:
            initializer: The initializer instance to register
        """
        name = initializer.name

        if name in self._initializers:
            logger.warning(f"Overriding existing initializer '{name}'")

        self._initializers[name] = initializer

        # Build dependency graph
        dependencies = initializer.dependencies
        self._dependency_graph[name] = dependencies

        logger.debug(f"Registered initializer '{name}' with dependencies: {dependencies}")

    def create_initializer(
        self, name: str, config: Optional[Dict[str, Any]] = None
    ) -> BaseInitializer:
        """
        Create an initializer instance from a registered class.

        Args:
            name: Name of the initializer class to create
            config: Configuration for the initializer

        Returns:
            Created initializer instance
        """
        if name not in self._initializer_classes:
            raise ConfigurationError(f"Initializer class '{name}' not registered")

        initializer_class = self._initializer_classes[name]
        initializer = initializer_class(name=name, config=config or {})

        # Register the instance
        self.register_initializer(initializer)

        return initializer

    def get_initializer(self, name: str) -> Optional[BaseInitializer]:
        """Get an initializer by name."""
        return self._initializers.get(name)

    def list_initializers(self) -> List[str]:
        """Get list of all registered initializer names."""
        return list(self._initializers.keys())

    def _resolve_dependencies(self) -> List[List[str]]:
        """
        Resolve dependencies and return initialization order in batches.

        Returns:
            List of batches, where each batch contains initializers that can run in parallel
        """
        # Topological sort with batching
        in_degree = defaultdict(int)
        graph = defaultdict(list)

        # Build the graph
        for name, deps in self._dependency_graph.items():
            for dep in deps:
                if dep not in self._initializers:
                    raise ConfigurationError(
                        f"Initializer '{name}' depends on '{dep}' which is not registered"
                    )
                graph[dep].append(name)
                in_degree[name] += 1

        # Initialize in_degree for all nodes
        for name in self._initializers:
            if name not in in_degree:
                in_degree[name] = 0

        # Process in batches
        batches = []
        remaining = set(self._initializers.keys())

        while remaining:
            # Find all nodes with in_degree 0 in remaining set
            batch = [name for name in remaining if in_degree[name] == 0]

            if not batch:
                # Circular dependency detected
                raise ConfigurationError(
                    f"Circular dependency detected among initializers: {remaining}"
                )

            batches.append(batch)

            # Remove batch from remaining and update in_degrees
            for name in batch:
                remaining.remove(name)
                for neighbor in graph[name]:
                    in_degree[neighbor] -= 1

        return batches

    async def initialize_all(self, force: bool = False) -> bool:
        """
        Initialize all registered initializers in dependency order.

        Args:
            force: Force re-initialization even if already initialized

        Returns:
            True if all initializations succeeded
        """
        if self._is_initialized and not force:
            logger.info("All initializers already initialized")
            return True

        logger.info("Starting initialization of all registered initializers")

        try:
            # Resolve dependencies into batches
            batches = self._resolve_dependencies()

            # Initialize each batch in parallel
            for batch_idx, batch in enumerate(batches):
                logger.info(f"Initializing batch {batch_idx + 1}/{len(batches)}: {batch}")

                # Create tasks for this batch
                tasks = []
                for name in batch:
                    initializer = self._initializers[name]
                    task = asyncio.create_task(
                        initializer.initialize(force=force), name=f"init_{name}"
                    )
                    tasks.append((name, task))

                # Wait for all tasks in this batch to complete
                results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)

                # Check results
                failed_initializers = []
                for (name, task), result in zip(tasks, results):
                    if isinstance(result, Exception):
                        logger.error(f"Initializer '{name}' failed with exception: {result}")
                        failed_initializers.append(name)
                    elif not result:
                        logger.error(f"Initializer '{name}' failed")
                        failed_initializers.append(name)
                    else:
                        logger.info(f"Initializer '{name}' completed successfully")

                if failed_initializers:
                    raise ConfigurationError(f"Failed to initialize: {failed_initializers}")

            self._is_initialized = True
            logger.info("All initializers completed successfully")
            return True

        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            return False

    async def health_check_all(self) -> Dict[str, Any]:
        """
        Perform health check on all initializers.

        Returns:
            Overall health status and individual initializer health
        """
        if not self._initializers:
            return {
                "overall_status": "healthy",
                "message": "No initializers registered",
                "initializers": {},
            }

        health_results = {}
        unhealthy_count = 0

        # Run health checks in parallel
        tasks = []
        for name, initializer in self._initializers.items():
            task = asyncio.create_task(initializer.health_check(), name=f"health_{name}")
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
            "message": f"{len(self._initializers) - unhealthy_count}/{len(self._initializers)} initializers healthy",
            "unhealthy_count": unhealthy_count,
            "initializers": health_results,
        }

    async def cleanup_all(self) -> None:
        """
        Clean up all initializers in reverse dependency order.
        """
        if not self._initializers:
            return

        logger.info("Starting cleanup of all initializers")

        try:
            # Get dependency order and reverse it for cleanup
            batches = self._resolve_dependencies()
            cleanup_batches = list(reversed(batches))

            # Cleanup each batch
            for batch_idx, batch in enumerate(cleanup_batches):
                logger.info(f"Cleaning up batch {batch_idx + 1}/{len(cleanup_batches)}: {batch}")

                # Create cleanup tasks for this batch
                tasks = []
                for name in batch:
                    initializer = self._initializers[name]
                    task = asyncio.create_task(initializer.cleanup(), name=f"cleanup_{name}")
                    tasks.append((name, task))

                # Wait for all cleanup tasks in this batch
                results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)

                # Log cleanup results
                for (name, task), result in zip(tasks, results):
                    if isinstance(result, Exception):
                        logger.error(f"Cleanup failed for '{name}': {result}")
                    else:
                        logger.debug(f"Cleanup completed for '{name}'")

            self._is_initialized = False
            logger.info("All initializers cleaned up")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}", exc_info=True)

    def get_status_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all initializer statuses.

        Returns:
            Status summary dictionary
        """
        if not self._initializers:
            return {"total_count": 0, "ready_count": 0, "status_breakdown": {}, "initializers": {}}

        status_breakdown = defaultdict(int)
        initializers_status = {}

        for name, initializer in self._initializers.items():
            status = initializer.state.status
            status_breakdown[status] += 1

            initializers_status[name] = {
                "status": status,
                "initialized_at": (
                    initializer.state.initialized_at.isoformat()
                    if initializer.state.initialized_at
                    else None
                ),
                "error_message": initializer.state.error_message,
                "dependencies": initializer.dependencies,
            }

        return {
            "total_count": len(self._initializers),
            "ready_count": status_breakdown.get("ready", 0),
            "status_breakdown": dict(status_breakdown),
            "initializers": initializers_status,
        }


# Global registry instance
registry = InitializerRegistry()
