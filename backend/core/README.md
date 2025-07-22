# Pipeline Foundation System

This directory contains the foundational architecture for the AI Customs pipeline system, providing a scalable framework for initializers, services, and pipeline orchestration.

## Overview

The pipeline foundation consists of:

- **Initializers**: Common initialization functionality for system components
- **Services**: Service lifecycle management and orchestration
- **Pipeline Manager**: Structured workflow execution with dependencies
- **Service Factory**: Configuration-driven system setup

## Architecture

```
core/
├── initializers/           # Initialization framework
│   ├── base_initializer.py # Base initializer class
│   └── initializer_registry.py # Dependency resolution
├── services/              # Service framework  
│   ├── base_service.py    # Base service class
│   ├── service_registry.py # Service management
│   ├── pipeline_manager.py # Workflow orchestration
│   ├── service_factory.py # Configuration-driven setup
│   └── examples/          # Usage examples
└── utils/                 # Utilities (logger, errors)
```

## Key Features

### 🚀 **Initializers**

- **Dependency Resolution**: Automatic initialization order based on dependencies
- **Parallel Initialization**: Run independent initializers simultaneously  
- **Health Monitoring**: Built-in health checks for all components
- **Error Handling**: Comprehensive error tracking and recovery
- **State Management**: Track initialization state and metadata

### 🔧 **Services**

- **Lifecycle Management**: Start, stop, restart with proper cleanup
- **Configuration Validation**: Validate service configurations
- **Event System**: Extensible event hooks for service events
- **Metrics Collection**: Built-in service metrics and monitoring
- **Health Checks**: Service-specific health validation

### 🚀 **Pipeline Manager**

- **Stage-based Execution**: Define pipelines as sequences of stages
- **Dependency Resolution**: Automatic stage ordering based on dependencies
- **Parallel Execution**: Run independent stages simultaneously
- **Retry Logic**: Configurable retry and timeout for each stage
- **Error Recovery**: Graceful error handling and rollback

### ⚙️ **Service Factory**

- **Configuration-driven**: Define entire system via configuration
- **Dynamic Loading**: Load classes by module path
- **Auto-discovery**: Automatic service and initializer registration
- **Health Monitoring**: Comprehensive system health checking

## Quick Start

### 1. Basic Service Creation

```python
from core.foundation import BaseService

class MyService(BaseService):
    def _validate_config(self):
        # Validate configuration
        self.get_config_value("required_setting", required=True)
    
    async def _start(self):
        # Service startup logic
        return {"status": "started"}
    
    async def _stop(self):
        # Service cleanup logic
        pass
    
    async def _health_check(self):
        # Health check logic
        return {"status": "healthy"}

# Create and use the service
service = MyService("my_service", {"required_setting": "value"})
await service.start()
```

### 2. Configuration-driven Setup

```python
from core.foundation import ServiceFactory

# Define system configuration
config = {
    "initializers": [
        {
            "name": "llm_initializer",
            "class": "core.initializers.LLMInitializer",
            "config": {"base_url": "http://localhost:8080/v1/"}
        }
    ],
    "services": [
        {
            "name": "analysis_service",
            "class": "my.module.AnalysisService",
            "config": {"confidence_threshold": 0.8},
            "initializers": ["llm_initializer"]
        }
    ],
    "pipelines": [
        {
            "name": "analysis_pipeline",
            "stages": [
                {
                    "name": "analyze",
                    "service": "analysis_service",
                    "retry": {"max_retries": 3}
                }
            ]
        }
    ]
}

# Set up and run the system
factory = ServiceFactory()
factory.setup_from_config(config)
await factory.initialize_all()
await factory.start_all_services()

# Execute pipeline
result = await factory.pipeline_manager.execute_pipeline(
    "analysis_pipeline", 
    {"input": "data"}
)
```

### 3. Creating Initializers

```python
from core.initializers import BaseInitializer

class DatabaseInitializer(BaseInitializer):
    def _validate_config(self):
        # Validate database configuration
        self.get_config_value("connection_string", required=True)
    
    async def _initialize(self):
        # Initialize database connection
        conn_str = self.get_config_value("connection_string")
        # ... database initialization logic
        return {"status": "connected", "tables": 5}
    
    async def _health_check(self):
        # Check database health
        return {"connection": "active", "response_time_ms": 50}
```

## Configuration Schema

### Initializer Configuration

```yaml
initializers:
  - name: "unique_name"              # Required: Unique identifier
    class: "module.path.ClassName"   # Required: Full class path
    config:                          # Optional: Initializer configuration
      setting1: value1
      setting2: value2
    dependencies: ["other_init"]     # Optional: Dependencies
```

### Service Configuration

```yaml
services:
  - name: "service_name"             # Required: Unique identifier
    class: "module.path.ServiceClass" # Required: Full class path
    config:                          # Optional: Service configuration
      timeout: 30
      max_workers: 5
    dependencies: ["other_service"]  # Optional: Service dependencies
    initializers: ["init_name"]      # Optional: Required initializers
```

### Pipeline Configuration

```yaml
pipelines:
  - name: "pipeline_name"            # Required: Unique identifier
    stages:                          # Required: Pipeline stages
      - name: "stage_name"           # Required: Stage identifier
        service: "service_name"      # Required: Service to execute
        config:                      # Optional: Stage-specific config
          stage_setting: value
        dependencies: ["prev_stage"] # Optional: Stage dependencies
        parallel: false              # Optional: Parallel execution
        retry:                       # Optional: Retry configuration
          max_retries: 3
          timeout_seconds: 60
```

## Advanced Usage

### Custom Event Handlers

```python
# Add event handlers to services
async def on_service_started(service, event, data):
    logger.info(f"Service {service.name} started with data: {data}")

service.add_event_handler("started", on_service_started)

# Add event handlers to pipelines
async def on_pipeline_completed(event, data):
    logger.info(f"Pipeline completed: {data}")

pipeline_manager.add_event_handler("pipeline_completed", on_pipeline_completed)
```

### Health Monitoring

```python
# Check individual service health
health = await service.health_check()

# Check all services health
all_health = await service_registry.health_check_all()

# Check entire system health
system_health = await service_factory.health_check_all()
```

### Metrics Collection

```python
# Get service metrics
metrics = await service.get_metrics()

# Get all service metrics
all_metrics = await service_registry.get_metrics_all()

# Get system status
status = service_factory.get_system_status()
```

## Integration with Existing Code

### Migrating Existing Services

To migrate existing services to the new foundation:

1. **Inherit from BaseService**:
   ```python
   # Before
   class MyService:
       def __init__(self, config):
           self.config = config
   
   # After
   class MyService(BaseService):
       def _validate_config(self):
           # Validate configuration
           pass
       
       async def _start(self):
           # Move initialization here
           pass
   ```

2. **Add Health Checks**:
   ```python
   async def _health_check(self):
       # Service-specific health logic
       return {"status": "healthy"}
   ```

3. **Add Metrics**:
   ```python
   async def _get_metrics(self):
       return {
           "requests_processed": self.request_count,
           "average_response_time": self.avg_response_time
       }
   ```

### Adding to Existing Routes

```python
# In your FastAPI routes
from core.foundation import ServiceRegistry

# Get global service registry
registry = ServiceRegistry()

@router.post("/analyze")
async def analyze_document(request: DocumentRequest):
    # Get service from registry
    analysis_service = registry.get_service("analysis_service")
    
    if not analysis_service or not analysis_service.is_running:
        raise HTTPException(500, "Analysis service not available")
    
    # Use the service
    result = await analysis_service.analyze(request.data)
    return result
```

## Error Handling

The foundation provides comprehensive error handling:

```python
from core.utils.errors import ConfigurationError

try:
    await service.start()
except ConfigurationError as e:
    logger.error(f"Configuration error: {e.message}")
    # Handle configuration issues
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    # Handle other errors
```

## Best Practices

### 1. Service Design
- Keep services focused on single responsibilities
- Use configuration for environment-specific settings
- Implement proper health checks and metrics
- Handle errors gracefully with proper logging

### 2. Pipeline Design
- Break complex workflows into simple stages
- Use dependencies to ensure proper execution order
- Configure appropriate timeouts and retries
- Design for idempotency where possible

### 3. Configuration Management
- Use environment variables for sensitive data
- Validate all configuration at startup
- Document configuration schema
- Provide sensible defaults

### 4. Monitoring and Observability
- Implement comprehensive health checks
- Collect meaningful metrics
- Use structured logging
- Monitor service dependencies

## Actual Pipeline Implementation

The system now includes the complete customs analysis pipeline:

### Pipeline Components

1. **LLM Initializer** (`core/initializers/llm_initializer.py`)
   - Connects to TGI service
   - Validates model availability
   - Tests LLM connectivity

2. **Pipeline Services**:
   - **Pipeline Init Service** - Manages concurrency (max 2 concurrent pipelines)
   - **PDF Parsing Service** - Processes document groups (5-7 docs: invoice, declaration, cert of origin, etc.)
   - **LLM Discrepancy Service** - Analyzes parsed text and returns JSON

3. **Pipeline Configuration** (`core/pipeline_config.py`)
   - Environment-specific configurations
   - Complete workflow definition
   - Example data structures

### Usage Example

```python
from core.customs_pipeline_example import run_customs_analysis_pipeline

# Run the complete pipeline
result = await run_customs_analysis_pipeline(document_group)

# Result includes:
# - Discrepancy analysis
# - Risk assessment  
# - Confidence scores
# - Recommendations
```

### Quick Test

```bash
# Test the complete pipeline
python backend/core/customs_pipeline_example.py

# Test individual services
python backend/core/customs_pipeline_example.py test
```

## Testing

The foundation includes comprehensive testing support:

```python
# Test service lifecycle
service = MyService("test", config)
assert await service.start()
assert service.is_running
assert await service.stop()

# Test pipeline execution
result = await pipeline_manager.execute_pipeline("test_pipeline", data)
assert result.status == PipelineStatus.COMPLETED
```

## Future Extensions

The foundation is designed for extensibility:

- **Plugin System**: Load services dynamically from plugins
- **Distributed Execution**: Run services across multiple nodes
- **Persistent State**: Store service and pipeline state
- **Advanced Scheduling**: Cron-like pipeline scheduling
- **Circuit Breakers**: Automatic failure isolation
- **Rate Limiting**: Service request throttling

This foundation provides a solid base for building scalable, maintainable pipeline systems that can grow with your needs. 