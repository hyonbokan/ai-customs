# Configuration Documentation

This directory contains the centralized configuration system for the AI Customs backend.

## Configuration Structure

```
config/
├── __init__.py          # Central configuration registry
├── app_config.py        # General application settings
├── llm_config.py        # LLM inference-server settings (vLLM / TGI)
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
max_retries = config.pipeline.LLM_MAX_RETRIES

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
| `LLM_BASE_URL` | `http://host.docker.internal:8080/v1/` | LLM service base URL |
| `LLM_BASE_URL_FALLBACK` | `http://172.17.0.1:8080/v1/` | Fallback URL if the primary can't be resolved |
| `LLM_SERVICE_TYPE` | `gemma-3-27b-it` | Model identifier registered with the server |
| `LLM_TEMPERATURE` | `0` | LLM sampling temperature |
| `LLM_MAX_TOKENS` | `8000` | Maximum tokens per request |
| `LLM_EXTRACTION_TEMPERATURE` | `0.1` | Temperature for the field-extraction stage |
| `LLM_DISCREPANCY_TEMPERATURE` | `0.2` | Temperature for the discrepancy-analysis stage |
| `LLM_REPORT_TEMPERATURE` | `0.1` | Temperature for the report stage |
| `LLM_REQUEST_TIMEOUT` | `120` | Request timeout in seconds |
| `LLM_REQUEST_DELAY` | `0.1` | Delay between requests |

### Pipeline Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PDF_MAX_FILE_SIZE_MB` | `50` | Maximum PDF file size in MB |
| `PDF_TIMEOUT_SECONDS` | `300` | PDF processing timeout |
| `PDF_SUPPORTED_FORMATS` | `pdf,jpg,png` | Supported file formats (comma-separated) |
| `PDF_ENABLE_OCR` | `true` | Enable OCR for text extraction |
| `PDF_ENABLE_TABLES` | `true` | Enable table structure extraction |
| `PDF_OCR_LANGUAGES` | `en,es,fr` | OCR languages (comma-separated) |
| `PDF_FORCE_FULL_PAGE_OCR` | `false` | Force OCR on entire pages |
| `LLM_MAX_RETRIES` | `3` | Maximum retry attempts for LLM calls |
| `RETRY_EXPONENTIAL_BASE` | `2` | Exponential backoff base for retries |
| `HEALTH_CHECK_TIMEOUT` | `5` | Health check LLM probe timeout in seconds |

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
LLM_TEMPERATURE=0

# Pipeline
LLM_MAX_RETRIES=3
```

### Production (Environment Variables)

Set environment variables directly:

```bash
export ENVIRONMENT=production
export LLM_MAX_RETRIES=5
export PDF_MAX_FILE_SIZE_MB=100
```

### Docker

Use environment variables in docker-compose.yml:

```yaml
services:
  customs-ai:
    environment:
      - ENVIRONMENT=production
      - LLM_BASE_URL=http://vllm:80/v1/
      - LLM_MAX_RETRIES=5
```

## Adding New Configuration

To add new configuration options:

1. **Add to the appropriate config class** (app_config.py, llm_config.py, or pipeline_config.py)
2. **Use environment variables** with sensible defaults
3. **Update this documentation** and `.env.example`

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