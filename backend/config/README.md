# Configuration Documentation

This directory contains the centralized configuration system for the AI Customs backend.

## Configuration Structure

```
config/
├── __init__.py          # Central configuration registry
├── app_config.py        # General application settings
├── llm_config.py        # LLM/TGI specific settings
├── pipeline_config.py   # Pipeline services configuration
└── README.md           # This documentation
```

## Usage

```python
from config import config

# Access application settings
app_name = config.app.TITLE
environment = config.app.ENVIRONMENT

# Access LLM settings
llm_url = config.llm.LLM_BASE_URL
temperature = config.llm.TEMPERATURE

# Access pipeline settings
max_concurrent = config.pipeline.MAX_CONCURRENT_PIPELINES
confidence_threshold = config.pipeline.LLM_CONFIDENCE_THRESHOLD

# PDF processing features (Docling)
ocr_enabled = config.pipeline.PDF_ENABLE_OCR
tables_enabled = config.pipeline.PDF_ENABLE_TABLES
```

## Pipeline Processing Flow

```python
# 1. PDF Parser (Docling) - Clean content extraction
pdf_result = await pdf_service.parse_document_group({
    "documents": [...]
})
# Returns: clean text, tables, document structure

# 2. LLM Service - Intelligent analysis
llm_result = await llm_service.analyze_discrepancies({
    "parsed_content": pdf_result["documents"]
})
# Returns: extracted fields, discrepancies, analysis
```

## Environment Variables

### Application Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | Environment name (development, production, test) |
| `ADMIN_API_KEY` | - | Admin API key for secure endpoints |
| `FRONTEND_URL` | `http://localhost:3000` | Frontend application URL |
| `BACKEND_URL` | `http://localhost:8000` | Backend API URL |
| `COOKIE_DOMAIN` | `localhost` | Cookie domain for authentication |
| `HOST` | `0.0.0.0` | Server host address |
| `PORT` | `8000` | Server port number |

### LLM Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_BASE_URL` | `http://localhost:8080/v1/` | LLM service base URL |
| `LLM_SERVICE_TYPE` | `tgi` | LLM service type identifier |
| `LLM_TEMPERATURE` | `0.7` | LLM sampling temperature |
| `LLM_MAX_TOKENS` | `1500` | Maximum tokens per request |
| `LLM_TOP_P` | `1.0` | Top-p sampling parameter |
| `LLM_REQUEST_TIMEOUT` | `120` | Request timeout in seconds |
| `LLM_CONNECT_TIMEOUT` | `30` | Connection timeout in seconds |
| `LLM_REQUEST_DELAY` | `0.1` | Delay between requests |

### Pipeline Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PIPELINE_MAX_CONCURRENT` | `2` | Maximum concurrent pipeline executions |
| `PIPELINE_QUEUE_SIZE` | `10` | Pipeline queue size |
| `PDF_MAX_FILE_SIZE_MB` | `50` | Maximum PDF file size in MB |
| `PDF_TIMEOUT_SECONDS` | `300` | PDF processing timeout |
| `PDF_MIN_DOCUMENTS` | `3` | Minimum documents in a group |
| `PDF_MAX_DOCUMENTS` | `10` | Maximum documents in a group |
| `PDF_SUPPORTED_FORMATS` | `pdf,jpg,png` | Supported file formats (comma-separated) |
| `PDF_ENABLE_OCR` | `true` | Enable OCR for text extraction |
| `PDF_ENABLE_TABLES` | `true` | Enable table structure extraction |
| `PDF_OCR_LANGUAGES` | `en,es,fr` | OCR languages (comma-separated) |
| `PDF_FORCE_FULL_PAGE_OCR` | `false` | Force OCR on entire pages |
| `LLM_CONFIDENCE_THRESHOLD` | `0.75` | Minimum confidence threshold for analysis |
| `LLM_ANALYSIS_TIMEOUT` | `180` | LLM analysis timeout in seconds |
| `LLM_MAX_RETRIES` | `3` | Maximum retry attempts for LLM calls |
| `LLM_DEEP_ANALYSIS` | `true` | Enable deep analysis mode |
| `HEALTH_CHECK_TIMEOUT` | `5` | Health check timeout in seconds |
| `RETRY_EXPONENTIAL_BASE` | `2` | Exponential backoff base for retries |

## Environment-Specific Overrides

### Development Environment

The following overrides are automatically applied in development:

```python
{
    "MAX_CONCURRENT_PIPELINES": 1,      # Reduced concurrency
    "PDF_TIMEOUT_SECONDS": 60,          # Shorter timeouts
    "LLM_ANALYSIS_TIMEOUT": 60,         # Shorter timeouts
    "LLM_MAX_RETRIES": 1,               # Fewer retries
    "PDF_ENABLE_OCR": False,            # Disable OCR for faster processing
    "PDF_FORCE_FULL_PAGE_OCR": False    # Disable full page OCR
}
```

### Production Environment

The following overrides are automatically applied in production:

```python
{
    "PIPELINE_QUEUE_SIZE": 50,          # Larger queue
    "PDF_MAX_FILE_SIZE_MB": 100,        # Larger files
    "LLM_CONFIDENCE_THRESHOLD": 0.8,    # Higher threshold
    "LLM_MAX_RETRIES": 5,               # More retries
    "PDF_ENABLE_OCR": True,             # Enable full OCR
    "PDF_ENABLE_TABLES": True           # Enable table extraction
}
```

### Test Environment

The following overrides are automatically applied in test:

```python
{
    "MAX_CONCURRENT_PIPELINES": 1,      # Single concurrency
    "PDF_TIMEOUT_SECONDS": 10,          # Very short timeouts
    "LLM_ANALYSIS_TIMEOUT": 10,         # Very short timeouts
    "LLM_MAX_RETRIES": 1,               # Minimal retries
    "HEALTH_CHECK_TIMEOUT": 2,          # Fast health checks
    "PDF_ENABLE_OCR": False,            # Disable OCR in tests
    "PDF_ENABLE_TABLES": False          # Disable table extraction in tests
}
```

## Docling PDF Processing Integration

The PDF parsing service uses Docling for clean document content extraction and preparation for LLM analysis:

### Core Philosophy
- **PDF Parser Role**: Extract clean text, tables, and document structure
- **LLM Role**: Intelligent field extraction, analysis, and discrepancy detection
- **No Regex/Pattern Matching**: Field extraction is delegated to the LLM for accuracy and flexibility

### Features
- **Advanced OCR**: Multi-language text extraction with EasyOCR support
- **Table Extraction**: Accurate table structure recognition and cell matching
- **Document Structure**: Preserves page layout, headers, and document organization
- **Multi-format Support**: Handles PDF, JPG, PNG formats with orientation detection
- **Clean Content Preparation**: Structured data ready for LLM consumption

### Document Processing Flow
1. **PDF Parser**: Downloads → Docling processing → Clean text/tables/structure
2. **LLM Service**: Structured content → Field extraction → Discrepancy analysis
3. **No Field Extraction in PDF**: Avoids brittle regex patterns, handles any language/format

### Supported Document Types for LLM Analysis
- **Commercial Invoice**: Clean text and tables for LLM to extract invoice details
- **Customs Declaration**: Structured content for LLM to identify declaration fields
- **Certificate of Origin**: Document text for LLM to parse origin information
- **Packing List**: Table data for LLM to analyze items and quantities
- **Bill of Lading**: Text content for LLM to extract shipping details
- **Insurance Certificate**: Document structure for LLM to identify coverage
- **Other Permits**: Clean content for LLM to analyze any trade documentation

### Installation Requirements

To use Docling features, install additional dependencies:

```bash
pip install -r requirements-docling.txt
```

System dependencies may be required:
- Ubuntu/Debian: `apt-get install libgl1-mesa-glx libglib2.0-0`
- macOS: `brew install opencv`

### Configuration Examples

**High Accuracy (Production)**:
```bash
PDF_ENABLE_OCR=true
PDF_ENABLE_TABLES=true
PDF_OCR_LANGUAGES=en,es,fr,de
PDF_FORCE_FULL_PAGE_OCR=false
```

**Fast Processing (Development)**:
```bash
PDF_ENABLE_OCR=false
PDF_ENABLE_TABLES=true
PDF_OCR_LANGUAGES=en
```

**Testing (Minimal)**:
```bash
PDF_ENABLE_OCR=false
PDF_ENABLE_TABLES=false
```

### Performance Considerations

- **OCR**: Adds ~2-5 seconds per page but improves text extraction quality
- **Table Extraction**: Adds ~1-2 seconds per table but provides structured data
- **Language Models**: Multiple OCR languages increase processing time
- **Memory Usage**: OCR and table models require additional RAM (2-4GB)

## Document Types Configuration

### Expected Document Types

The system expects the following document types in a customs declaration:

- `commercial_invoice`
- `customs_declaration`
- `certificate_of_origin`
- `packing_list`
- `bill_of_lading`
- `insurance_certificate`
- `other_permits`

### Critical Document Types

These documents are required for minimal compliance:

- `commercial_invoice`
- `customs_declaration`

### Recommended Document Types

These documents are recommended for complete analysis:

- `certificate_of_origin`
- `packing_list`
- `bill_of_lading`

## Analysis Focus Areas

The LLM analysis can focus on these areas:

- `valuation` - Value and pricing analysis
- `classification` - HS code and product classification
- `origin` - Country of origin verification
- `compliance` - Trade compliance and regulations

## Setting Environment Variables

### Development (.env file)

Create a `.env` file in the backend directory:

```bash
# Application
ENVIRONMENT=development
PORT=8000

# LLM
LLM_BASE_URL=http://localhost:8080/v1/
LLM_TEMPERATURE=0.7

# Pipeline
PIPELINE_MAX_CONCURRENT=1
LLM_CONFIDENCE_THRESHOLD=0.75
```

### Production (Environment Variables)

Set environment variables directly:

```bash
export ENVIRONMENT=production
export PIPELINE_MAX_CONCURRENT=2
export LLM_CONFIDENCE_THRESHOLD=0.8
export PDF_MAX_FILE_SIZE_MB=100
```

### Docker

Use environment variables in docker-compose.yml:

```yaml
services:
  customs-ai:
    environment:
      - ENVIRONMENT=production
      - LLM_BASE_URL=http://tgi:8080/v1/
      - PIPELINE_MAX_CONCURRENT=2
```

## Adding New Configuration

To add new configuration options:

1. **Add to the appropriate config class** (app_config.py, llm_config.py, or pipeline_config.py)
2. **Use environment variables** with sensible defaults
3. **Update this documentation**
4. **Add to environment-specific overrides** if needed

Example:

```python
# In pipeline_config.py
NEW_FEATURE_ENABLED = os.getenv("NEW_FEATURE_ENABLED", "true").lower() == "true"
NEW_FEATURE_TIMEOUT = int(os.getenv("NEW_FEATURE_TIMEOUT", 60))
```

## Validation

Configuration values are validated when services start. Invalid values will raise `ConfigurationError` with descriptive messages.

## Best Practices

1. **Use environment variables** for all configurable values
2. **Provide sensible defaults** for development
3. **Validate configuration** in service `_validate_config()` methods
4. **Document new options** in this README
5. **Use type conversion** (int, float, bool) for non-string values
6. **Group related settings** in the same config class
7. **Use environment-specific overrides** for different deployment scenarios 