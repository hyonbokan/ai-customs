# API Router Architecture

This directory contains the API layer with the **actual business service implementations** for the AI Customs backend.

## ✅ **Corrected Architecture**

### 🏗️ **Clear Separation of Concerns**
- **`core/foundation/`**: Foundational classes, managers, and orchestrators
- **`api/routers/`**: Actual business service implementations with API endpoints
- **Each router service**: Complete, independent, testable business logic

### 🔄 **Foundation vs Router Services**
- **Foundation Services**: Base classes, orchestrators, pipeline managers
- **Router Services**: Complete business implementations (PDF parsing, LLM analysis)
- **Pipeline Orchestration**: Coordinates calls between router services

## Router Services (Business Implementations)

### 📄 **PDF Parser Service** (`/api/v1/pdf-parser`)

**Complete PDF processing business service**

```
api/routers/pdf_parser/
├── routes.py           # FastAPI endpoints
├── service.py          # Complete business service implementation
├── schema.py           # Pydantic models
└── helpers/
    └── pdf_extractor.py # Docling-based extraction
```

**Capabilities:**
- ✅ **Complete service implementation** - not just API wrapper
- ✅ **Independent testing** - can be tested without pipeline
- ✅ **Comprehensive processing** - full PDF parsing with Docling
- ✅ **Health checks** - service-level monitoring
- ✅ **Synchronous and async** - supports both use cases

**Endpoints:**
- `POST /parse-pdf` - Background parsing task
- `POST /parse-direct` - Synchronous parsing  
- `GET /parse-status/{task_id}` - Check task status
- `GET /parse-result/{task_id}` - Get parsing results

### 🤖 **Declaration Analyzer Service** (`/api/v1/analyze-declaration`)

**Complete LLM analysis business service**

```
api/routers/declaration_analyzer/
├── routes.py           # FastAPI endpoints  
├── service.py          # Complete business service implementation
├── schema.py           # Pydantic models
└── helpers/
    └── data_validator.py # Data validation
```

**Capabilities:**
- ✅ **Complete service implementation** - comprehensive LLM analysis
- ✅ **Independent testing** - can be tested without pipeline
- ✅ **Field extraction** - intelligent LLM-based processing
- ✅ **Discrepancy analysis** - cross-document validation
- ✅ **Report generation** - comprehensive reporting

**Endpoints:**
- `POST /analyze-declaration` - Submit for LLM analysis
- `GET /analysis-status/{task_id}` - Check analysis status
- `GET /analysis-result/{task_id}` - Get analysis results

### 🔄 **Full Pipeline Service** (`/api/v1/full-pipeline`)

**Complete workflow orchestration**

```
api/routers/full_pipeline/
├── routes.py           # FastAPI endpoints
├── service.py          # Pipeline orchestration service
├── schema.py           # Pydantic models
└── Uses CustomsPipelineService for orchestration
```

**Architecture:**
- ✅ **Orchestrates router services** - calls PDF parser and analyzer services
- ✅ **Independent testing** - complete end-to-end workflows
- ✅ **Modular design** - each component can be tested separately
- ✅ **Proper separation** - orchestration vs business logic

**Endpoints:**
- `POST /process` - Background complete pipeline
- `POST /process-sync` - Synchronous complete pipeline
- `GET /status/{task_id}` - Check pipeline status
- `GET /result/{task_id}` - Get complete results

## Foundation Classes (Core Orchestration)

### 🏗️ **CustomsPipelineService** (`core/foundation/customs_pipeline_service.py`)

**The main orchestrator that coordinates router services**

```
CustomsPipelineService
├── Calls → PDFParserService.parse_document_sync()
├── Calls → DeclarationAnalyzerService.analyze_document_sync()
└── Generates final comprehensive report
```

**Key Features:**
- ✅ **Orchestrates router services** - not duplicate business logic
- ✅ **Service coordination** - manages calls between services
- ✅ **Error handling** - comprehensive pipeline error management
- ✅ **Health monitoring** - checks router service availability

## Architecture Benefits

### 🎯 **Proper Separation of Concerns**
- **Foundation**: Base classes, managers, orchestrators
- **Router Services**: Complete business logic implementations
- **Pipeline**: Orchestrates calls between router services

### 🌍 **Independent Testing & Modularity**
- Each router service can be tested independently
- Pipeline can be tested by mocking router services
- Clear interfaces between components

### 📈 **Scalable & Maintainable**
- Router services are complete, self-contained implementations
- Foundation provides reusable orchestration patterns
- Clear separation reduces coupling

### 🔧 **Development Workflow**

```bash
# Test individual PDF parsing
curl -X POST /api/v1/pdf-parser/parse-direct -d '{"file_url": "..."}'

# Test individual LLM analysis  
curl -X POST /api/v1/analyze-declaration -d '{"declaration_data": {...}}'

# Test complete pipeline
curl -X POST /api/v1/full-pipeline/process-sync -d '{"file_url": "..."}'
```

## Foundation Architecture

### ✅ **Foundation Classes (`core/foundation/`)**
- `BaseService` - Base service class with lifecycle management
- `ServiceRegistry` - Service discovery and management
- `ServiceFactory` - Configuration-driven service creation
- `PipelineManager` - Workflow orchestration framework
- `CustomsPipelineService` - Main pipeline orchestrator

### ✅ **Router Services (`api/routers/`)**
- `PDFParserService` - Complete PDF processing implementation
- `DeclarationAnalyzerService` - Complete LLM analysis implementation
- `FullPipelineService` - Pipeline orchestration interface
- **All services are complete business implementations, not just API wrappers**

## Service Communication Flow

```
Full Pipeline Request
        ↓
CustomsPipelineService (orchestrator)
        ↓
┌─────────────────┬─────────────────┐
│  PDF Parser     │  Declaration    │
│  Service        │  Analyzer       │  
│  (router)       │  Service        │
│                 │  (router)       │
└─────────────────┴─────────────────┘
        ↓
Final Comprehensive Report
```

## Key Principles

### 1. **Foundation = Infrastructure**
- Base classes and orchestration
- No business logic duplication
- Reusable patterns and managers

### 2. **Router Services = Business Logic**
- Complete service implementations
- Independent and testable
- Self-contained with full capabilities

### 3. **Pipeline = Orchestration**
- Coordinates router services
- Manages workflow and error handling
- Provides unified interface

This architecture ensures proper separation of concerns, independent testing capabilities, and maintainable, scalable code organization. Each router service is a complete business service that can operate independently while the foundation provides orchestration and infrastructure support. 