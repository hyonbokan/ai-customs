# Core

Shared building blocks used by the API routers. Everything here is
framework-agnostic (no FastAPI imports) so it can be reused and unit-tested
independently.

```
core/
├── llm/          # LLM integration
│   ├── llm_client.py           # High-level analysis calls (build messages, validate response)
│   ├── llm_request_handler.py  # OpenAI-compatible transport + structured-output parsing
│   ├── prompt_templates.py     # Prompts for single-shot declaration analysis
│   ├── pipeline_prompts.py     # Prompts for the multi-stage pipeline analysis
│   ├── system_messages.py      # System prompts
│   └── response_models.py      # Pydantic models for structured LLM output
├── schemas/      # Shared request/response schemas
│   ├── api_response_schema.py  # SuccessResponse / ErrorResponse
│   └── base_schemas.py         # BaseRequest / BaseResponse / common models
└── utils/        # Cross-cutting utilities
    ├── errors.py               # Typed exception hierarchy (BaseCustomsError + subclasses)
    ├── logger.py               # Configured "CustomsAI" logger
    └── throttling.py           # Rate-limiting decorator (placeholder)
```

## Conventions

- **Errors** raised in services/clients come from `core/utils/errors.py`. They
  carry a `message`, an `error_code`, an HTTP `status_code`, and optional
  `details`, and are mapped to `ErrorResponse` JSON by the global exception
  handler registered in `main.py`.
- **Logging** goes through the shared `logger` from `core/utils/logger.py`
  (never `print`).
- **LLM output** is always validated against a Pydantic model in
  `response_models.py` rather than parsed ad hoc.
