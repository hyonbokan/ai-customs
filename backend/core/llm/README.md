# TGI Client with Structured Output

This directory contains the TGI (Text Generation Interface) client implementation for the AI Customs project, with support for structured output using Pydantic models.

## Files Overview

- `send_prompt_to_llm.py` - Main TGI client with structured output support
- `llm_client.py` - High-level client for customs AI operations
- `prompt_templates.py` - Templates for generating prompts
- `response_models.py` - Pydantic models for structured responses
- `tgi_example.py` - Usage examples

## Quick Start

### 1. Basic Usage

```python
from core.llm.send_prompt_to_llm import handle_tgi_request

# Simple text completion
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the capital of France?"}
]

response = await handle_tgi_request(
    model_type="tgi",
    messages=messages,
    temperature=0.7,
    max_tokens=100
)
print(response)
```

### 2. Structured Output

```python
from core.llm.send_prompt_to_llm import handle_tgi_request
from core.llm.response_models import CityInfo

# Structured output with Pydantic model
messages = [
    {"role": "system", "content": "You are a geography expert."},
    {"role": "user", "content": "Tell me about Paris, France."}
]

response = await handle_tgi_request(
    model_type="tgi",
    messages=messages,
    response_model=CityInfo,  # This enforces structured output
    temperature=0.7,
    max_tokens=200
)

# Response will be a CityInfo object
print(f"City: {response.city}")
print(f"Country: {response.country}")
print(f"Population: {response.population}")
```

### 3. Customs Analysis

```python
from core.llm.llm_client import LLMClient

# High-level customs analysis
declaration_data = {
    "declaration_number": "CD-2024-001234",
    "importer": "ABC Trading Company",
    "goods": [
        {
            "description": "Electronic Components",
            "hs_code": "8542.31",
            "quantity": "100",
            "unit": "units",
            "value": "5000",
            "currency": "USD"
        }
    ],
    "total_value": "5000",
    "currency": "USD"
}

result = await LLMClient.analyze_customs_declaration(declaration_data)
print(f"Discrepancies found: {result['discrepancies_found']}")
```

## Configuration

### TGI Server Setup

Make sure your TGI server is running:

```bash
# Default TGI server URL
http://localhost:8080/v1/
```

### Model Configuration

The client uses the following defaults:
- Model: `"tgi"`
- Temperature: `0.7`
- Max tokens: `1000`
- Base URL: `"http://localhost:8080/v1/"`

## Features

### Structured Output Support

The client automatically handles structured output by:
1. Adding JSON schema instructions to prompts
2. Parsing responses with Pydantic models
3. Robust JSON extraction from various response formats

### Error Handling

- Comprehensive error handling for TGI API issues
- Fallback mechanisms for failed requests
- Detailed logging for debugging

### Async Support

All operations are async for better performance:
- Non-blocking API calls
- Concurrent request handling
- Proper event loop management

## Response Models

### Available Models

- `CustomsAnalysisResponse` - For customs declaration analysis
- `PDFExtractionResponse` - For PDF data extraction
- `CityInfo` - Example model for testing

### Creating Custom Models

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class YourCustomModel(BaseModel):
    field1: str = Field(description="Description of field1")
    field2: Optional[int] = Field(description="Optional integer field")
    field3: List[str] = Field(description="List of strings")
```

## Integration with Services

The TGI client integrates with your services:

```python
# In your service class
class YourService:
    @staticmethod
    async def analyze_data(data: Dict[str, Any]) -> CustomsAnalysisResponse:
        messages = [
            {"role": "system", "content": "You are an expert analyst."},
            {"role": "user", "content": f"Analyze this data: {data}"}
        ]
        
        return await handle_tgi_request(
            model_type="tgi",
            messages=messages,
            response_model=CustomsAnalysisResponse,
            temperature=0.3,
            max_tokens=1000
        )
```

## Best Practices

### Temperature Settings

- **Analysis tasks**: Use low temperature (0.1-0.3) for consistent results
- **Creative tasks**: Use higher temperature (0.7-0.9) for variety
- **Extraction tasks**: Use very low temperature (0.1) for precision

### Token Management

- **Simple responses**: 100-200 tokens
- **Analysis reports**: 500-1000 tokens
- **Detailed extraction**: 1000-2000 tokens

### Error Handling

Always wrap TGI calls in try-catch blocks:

```python
try:
    response = await handle_tgi_request(...)
except LLMError as e:
    # Handle API errors
    logger.error(f"TGI API error: {e.message}")
    # Implement fallback logic
except Exception as e:
    # Handle unexpected errors
    logger.error(f"Unexpected error: {e}")
```

## Testing

To test the TGI client:

```bash
# Run the example file
python backend/core/llm/tgi_example.py

# Or run individual tests
python -c "import asyncio; from core.llm.tgi_example import example_simple_text_completion; asyncio.run(example_simple_text_completion())"
```

## Dependencies

Required packages:
- `huggingface_hub` - For TGI client
- `pydantic` - For structured output models
- `asyncio` - For async operations

Install with:
```bash
pip install huggingface_hub pydantic
```

## Troubleshooting

### Common Issues

1. **TGI server not running**: Make sure TGI is running on `localhost:8080`
2. **Import errors**: Check that all dependencies are installed
3. **JSON parsing errors**: Ensure prompts are clear about JSON format requirements
4. **Rate limiting**: Add delays between requests if needed

### Debugging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This will show detailed request/response information. 