"""
Pipeline Manager for orchestrating multiple services in structured workflows.
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime
from enum import Enum

from core.utils.logger import logger
from core.utils.errors import ConfigurationError
from core.foundation.base_service import BaseService
from core.foundation.service_registry import ServiceRegistry


class PipelineStatus(Enum):
    """Pipeline execution status."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineStage:
    """Represents a single stage in the pipeline."""
    
    def __init__(self, name: str, service_name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.service_name = service_name
        self.config = config or {}
        self.dependencies: List[str] = []
        self.is_parallel = False
        self.retry_count = 0
        self.max_retries = 3
        self.timeout_seconds: Optional[float] = None
    
    def add_dependency(self, stage_name: str) -> None:
        """Add a dependency stage that must complete before this stage."""
        if stage_name not in self.dependencies:
            self.dependencies.append(stage_name)
    
    def set_parallel(self, parallel: bool = True) -> None:
        """Set whether this stage can run in parallel with other stages."""
        self.is_parallel = parallel
    
    def set_retry_config(self, max_retries: int, timeout_seconds: Optional[float] = None) -> None:
        """Configure retry and timeout settings."""
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds


class PipelineResult:
    """Represents the result of a pipeline execution."""
    
    def __init__(self, pipeline_name: str):
        self.pipeline_name = pipeline_name
        self.status = PipelineStatus.IDLE
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.stage_results: Dict[str, Any] = {}
        self.errors: Dict[str, str] = {}
        self.metadata: Dict[str, Any] = {}
    
    def mark_started(self):
        """Mark pipeline as started."""
        self.status = PipelineStatus.RUNNING
        self.started_at = datetime.utcnow()
    
    def mark_completed(self):
        """Mark pipeline as completed."""
        self.status = PipelineStatus.COMPLETED
        self.completed_at = datetime.utcnow()
    
    def mark_failed(self, error: str):
        """Mark pipeline as failed."""
        self.status = PipelineStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.errors["pipeline"] = error
    
    def add_stage_result(self, stage_name: str, result: Any):
        """Add result from a completed stage."""
        self.stage_results[stage_name] = result
    
    def add_stage_error(self, stage_name: str, error: str):
        """Add error from a failed stage."""
        self.errors[stage_name] = error
    
    @property
    def duration_seconds(self) -> float:
        """Get pipeline execution duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            return (datetime.utcnow() - self.started_at).total_seconds()
        return 0.0


class PipelineManager:
    """
    Manager for creating and executing structured service pipelines.
    
    Features:
    - Stage-based pipeline definition
    - Dependency resolution between stages
    - Parallel and sequential execution
    - Error handling and recovery
    - Pipeline monitoring and metrics
    """
    
    def __init__(self, service_registry: Optional[ServiceRegistry] = None):
        self.service_registry = service_registry or ServiceRegistry()
        self._pipelines: Dict[str, Dict[str, PipelineStage]] = {}
        self._pipeline_results: Dict[str, PipelineResult] = {}
        self._event_handlers: Dict[str, List[Callable]] = {}
    
    def create_pipeline(self, name: str) -> None:
        """
        Create a new pipeline.
        
        Args:
            name: Unique name for the pipeline
        """
        if name in self._pipelines:
            logger.warning(f"Overriding existing pipeline '{name}'")
        
        self._pipelines[name] = {}
        logger.debug(f"Created pipeline '{name}'")
    
    def add_stage(self, pipeline_name: str, stage: PipelineStage) -> None:
        """
        Add a stage to a pipeline.
        
        Args:
            pipeline_name: Name of the pipeline
            stage: The stage to add
        """
        if pipeline_name not in self._pipelines:
            raise ConfigurationError(f"Pipeline '{pipeline_name}' does not exist")
        
        self._pipelines[pipeline_name][stage.name] = stage
        logger.debug(f"Added stage '{stage.name}' to pipeline '{pipeline_name}'")
    
    def add_simple_stage(self, pipeline_name: str, stage_name: str, service_name: str,
                         dependencies: Optional[List[str]] = None,
                         config: Optional[Dict[str, Any]] = None,
                         parallel: bool = False) -> PipelineStage:
        """
        Add a simple stage to a pipeline.
        
        Args:
            pipeline_name: Name of the pipeline
            stage_name: Name of the stage
            service_name: Name of the service to run
            dependencies: List of stage names this stage depends on
            config: Configuration for the stage
            parallel: Whether this stage can run in parallel
            
        Returns:
            The created stage
        """
        stage = PipelineStage(stage_name, service_name, config)
        
        if dependencies:
            for dep in dependencies:
                stage.add_dependency(dep)
        
        stage.set_parallel(parallel)
        self.add_stage(pipeline_name, stage)
        
        return stage
    
    def get_pipeline_stages(self, pipeline_name: str) -> Dict[str, PipelineStage]:
        """Get all stages for a pipeline."""
        if pipeline_name not in self._pipelines:
            raise ConfigurationError(f"Pipeline '{pipeline_name}' does not exist")
        return self._pipelines[pipeline_name].copy()
    
    def _resolve_stage_dependencies(self, pipeline_name: str) -> List[List[str]]:
        """
        Resolve stage dependencies and return execution order in batches.
        
        Args:
            pipeline_name: Name of the pipeline
        
        Returns:
            List of batches, where each batch contains stages that can run in parallel
        """
        if pipeline_name not in self._pipelines:
            raise ConfigurationError(f"Pipeline '{pipeline_name}' does not exist")
        
        stages = self._pipelines[pipeline_name]
        
        # Build dependency graph
        from collections import defaultdict
        in_degree = defaultdict(int)
        graph = defaultdict(list)
        
        for stage_name, stage in stages.items():
            for dep in stage.dependencies:
                if dep not in stages:
                    raise ConfigurationError(
                        f"Stage '{stage_name}' depends on '{dep}' which does not exist in pipeline '{pipeline_name}'"
                    )
                graph[dep].append(stage_name)
                in_degree[stage_name] += 1
        
        # Initialize in_degree for all stages
        for stage_name in stages:
            if stage_name not in in_degree:
                in_degree[stage_name] = 0
        
        # Resolve dependencies in batches
        batches = []
        remaining = set(stages.keys())
        
        while remaining:
            # Find stages with no dependencies in remaining set
            batch = [name for name in remaining if in_degree[name] == 0]
            
            if not batch:
                raise ConfigurationError(
                    f"Circular dependency detected in pipeline '{pipeline_name}': {remaining}"
                )
            
            batches.append(batch)
            
            # Remove batch from remaining and update in_degrees
            for stage_name in batch:
                remaining.remove(stage_name)
                for neighbor in graph[stage_name]:
                    in_degree[neighbor] -= 1
        
        return batches
    
    async def execute_stage(self, pipeline_name: str, stage_name: str, 
                           input_data: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a single stage.
        
        Args:
            pipeline_name: Name of the pipeline
            stage_name: Name of the stage to execute
            input_data: Input data for the stage
            
        Returns:
            Stage execution result
        """
        if pipeline_name not in self._pipelines:
            raise ConfigurationError(f"Pipeline '{pipeline_name}' does not exist")
        
        stage = self._pipelines[pipeline_name].get(stage_name)
        if not stage:
            raise ConfigurationError(f"Stage '{stage_name}' not found in pipeline '{pipeline_name}'")
        
        # Get the service
        service = self.service_registry.get_service(stage.service_name)
        if not service:
            raise ConfigurationError(f"Service '{stage.service_name}' not found for stage '{stage_name}'")
        
        # Ensure service is running
        if not service.is_running:
            success = await self.service_registry.start_service(stage.service_name)
            if not success:
                raise ConfigurationError(f"Failed to start service '{stage.service_name}' for stage '{stage_name}'")
        
        # Execute stage with retry logic
        for attempt in range(stage.max_retries + 1):
            try:
                logger.info(f"Executing stage '{stage_name}' (attempt {attempt + 1}/{stage.max_retries + 1})")
                
                # Create execution context
                context = {
                    "pipeline_name": pipeline_name,
                    "stage_name": stage_name,
                    "attempt": attempt + 1,
                    "config": stage.config,
                    "input_data": input_data or {}
                }
                
                # Execute with timeout if specified
                if stage.timeout_seconds:
                    result = await asyncio.wait_for(
                        self._execute_stage_with_service(service, context),
                        timeout=stage.timeout_seconds
                    )
                else:
                    result = await self._execute_stage_with_service(service, context)
                
                logger.info(f"Stage '{stage_name}' completed successfully")
                return result
                
            except asyncio.TimeoutError:
                error_msg = f"Stage '{stage_name}' timed out after {stage.timeout_seconds}s"
                if attempt == stage.max_retries:
                    raise ConfigurationError(error_msg)
                logger.warning(f"{error_msg}, retrying...")
                
            except Exception as e:
                error_msg = f"Stage '{stage_name}' failed: {str(e)}"
                if attempt == stage.max_retries:
                    raise ConfigurationError(error_msg)
                logger.warning(f"{error_msg}, retrying...")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        raise ConfigurationError(f"Stage '{stage_name}' failed after {stage.max_retries + 1} attempts")
    
    async def _execute_stage_with_service(self, service: BaseService, context: Dict[str, Any]) -> Any:
        """
        Execute a stage with its service.
        This is a placeholder - implement based on your service interface.
        
        Args:
            service: The service to execute
            context: Execution context
            
        Returns:
            Stage execution result
        """
        # This is a placeholder implementation
        # In a real implementation, you would define how services are executed within stages
        # For example, services might have an `execute` method or specific operation methods
        
        # For now, return a placeholder result
        return {
            "stage_name": context["stage_name"],
            "service_name": service.name,
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def execute_pipeline(self, pipeline_name: str, 
                              input_data: Optional[Dict[str, Any]] = None) -> PipelineResult:
        """
        Execute a complete pipeline.
        
        Args:
            pipeline_name: Name of the pipeline to execute
            input_data: Initial input data for the pipeline
            
        Returns:
            Pipeline execution result
        """
        if pipeline_name not in self._pipelines:
            raise ConfigurationError(f"Pipeline '{pipeline_name}' does not exist")
        
        # Create result tracker
        result = PipelineResult(pipeline_name)
        self._pipeline_results[pipeline_name] = result
        
        try:
            result.mark_started()
            await self._emit_event("pipeline_started", {"pipeline_name": pipeline_name})
            
            logger.info(f"Starting pipeline '{pipeline_name}'")
            
            # Resolve stage execution order
            stage_batches = self._resolve_stage_dependencies(pipeline_name)
            
            # Execute stages in batches
            current_data = input_data or {}
            
            for batch_idx, batch in enumerate(stage_batches):
                logger.info(f"Executing pipeline batch {batch_idx + 1}/{len(stage_batches)}: {batch}")
                
                # Execute stages in this batch (potentially in parallel)
                if len(batch) == 1:
                    # Single stage - execute sequentially
                    stage_name = batch[0]
                    try:
                        stage_result = await self.execute_stage(pipeline_name, stage_name, current_data)
                        result.add_stage_result(stage_name, stage_result)
                        current_data = stage_result  # Pass result to next stage
                    except Exception as e:
                        result.add_stage_error(stage_name, str(e))
                        raise
                else:
                    # Multiple stages - execute in parallel
                    tasks = []
                    for stage_name in batch:
                        task = asyncio.create_task(
                            self.execute_stage(pipeline_name, stage_name, current_data),
                            name=f"stage_{stage_name}"
                        )
                        tasks.append((stage_name, task))
                    
                    # Wait for all stages in batch to complete
                    results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
                    
                    # Process results
                    batch_results = {}
                    for (stage_name, task), stage_result in zip(tasks, results):
                        if isinstance(stage_result, Exception):
                            result.add_stage_error(stage_name, str(stage_result))
                            raise stage_result
                        else:
                            result.add_stage_result(stage_name, stage_result)
                            batch_results[stage_name] = stage_result
                    
                    # Combine batch results for next stage
                    current_data = {"batch_results": batch_results, "input_data": current_data}
            
            result.mark_completed()
            await self._emit_event("pipeline_completed", {"pipeline_name": pipeline_name, "result": result})
            
            logger.info(f"Pipeline '{pipeline_name}' completed successfully in {result.duration_seconds:.2f}s")
            return result
            
        except Exception as e:
            error_msg = f"Pipeline '{pipeline_name}' failed: {str(e)}"
            result.mark_failed(error_msg)
            await self._emit_event("pipeline_failed", {"pipeline_name": pipeline_name, "error": str(e)})
            logger.error(error_msg, exc_info=True)
            return result
    
    def add_event_handler(self, event: str, handler: Callable) -> None:
        """
        Add an event handler for pipeline events.
        
        Args:
            event: Event name (pipeline_started, pipeline_completed, pipeline_failed, stage_completed, stage_failed)
            handler: Callable to handle the event
        """
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)
        logger.debug(f"Added event handler for '{event}'")
    
    async def _emit_event(self, event: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Emit an event to all registered handlers."""
        if event in self._event_handlers:
            for handler in self._event_handlers[event]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event, data or {})
                    else:
                        handler(event, data or {})
                except Exception as e:
                    logger.error(f"Error in event handler for '{event}': {e}", exc_info=True)
    
    def get_pipeline_result(self, pipeline_name: str) -> Optional[PipelineResult]:
        """Get the result of a pipeline execution."""
        return self._pipeline_results.get(pipeline_name)
    
    def list_pipelines(self) -> List[str]:
        """Get list of all registered pipeline names."""
        return list(self._pipelines.keys())
    
    def get_pipeline_status(self, pipeline_name: str) -> Dict[str, Any]:
        """
        Get status information for a pipeline.
        
        Args:
            pipeline_name: Name of the pipeline
            
        Returns:
            Pipeline status dictionary
        """
        if pipeline_name not in self._pipelines:
            raise ConfigurationError(f"Pipeline '{pipeline_name}' does not exist")
        
        stages = self._pipelines[pipeline_name]
        result = self._pipeline_results.get(pipeline_name)
        
        return {
            "name": pipeline_name,
            "stage_count": len(stages),
            "stages": list(stages.keys()),
            "status": result.status.value if result else "not_executed",
            "duration_seconds": result.duration_seconds if result else 0,
            "completed_stages": len(result.stage_results) if result else 0,
            "failed_stages": len(result.errors) if result else 0
        } 