## Project Overview

AI Customs is a self-hosted, open-source LLM system that detects discrepancies in
customs declarations. It parses trade documents (invoices, declarations, packing
lists, …), extracts structured fields, and cross-checks them for valuation,
classification, origin, and compliance issues — running entirely on local GPUs so
data never leaves the environment.

> **Status: prototype / portfolio project.** It is not production-hardened. There
> is no CI, no automated test suite, and a single `main` branch. Prefer small,
> honest changes; don't invent infrastructure that isn't here.

Two independently deployable components:

- **`backend/`** — a FastAPI app (Python 3.12) that orchestrates document parsing
  and LLM analysis. Talks to the model over an OpenAI-compatible `/v1` endpoint.
- **model serving** — vLLM is the primary engine (OpenAI-compatible); TGI is
  supported as an alternative and kept for comparison in `llm_service_manual/`
  (a Dockerized TGI deployment) and `llm_test_runs/`. Model: Gemma-3-27B-IT,
  developed on 2× RTX A6000 (48 GB each).

## Architecture (the live request path)

```
main.py  →  api/router.py  →  api/routers/<feature>/routes.py
                                     │
                                     ▼
                            api/routers/<feature>/service.py
                                     │
                                     ▼
                            core/llm/llm_client.py  →  llm_request_handler.py  →  LLM server
```

Feature routers (each is self-contained: `routes.py` + `service.py` + `schema.py`):

- **`health_check`** — `GET /api/v1/health-check`
- **`declaration_analyzer`** — `POST /api/v1/analyze-declaration` (the flagship: synchronous, structured LLM analysis)
- **`pdf_parser`** — Docling-based extraction (`/parse-direct` sync, `/parse-pdf` background via Huey, `/capabilities`)
- **`full_pipeline`** — `POST /api/v1/full-pipeline/process`: chains pdf_parser → declaration_analyzer → report, synchronously

`core/` holds framework-agnostic building blocks (no FastAPI imports): `llm/`,
`schemas/`, `utils/`. See [backend/core/README.md](backend/core/README.md).
`config/` centralizes all env-driven configuration.

## Common Commands

Run everything from `backend/` unless noted. Use a project virtualenv
(`.venv/bin/python`), never a system Python.

```bash
# --- Setup ---
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # then set LLM_BASE_URL to your model server

# --- Run the backend (needs an LLM server reachable at LLM_BASE_URL) ---
python main.py                  # http://localhost:8000 , docs at /docs

# --- Run the full stack in Docker (model server + backend, wired together) ---
./run_stack.bash                # vLLM by default; or: ./run_stack.bash tgi

# --- Serve the model standalone ---
# vLLM is primary. For the TGI alternative, see llm_service_manual/README.md
# and llm_service_manual/TROUBLESHOOTING.md
```

Linting / formatting / type-checking (from the repo root):

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files      # ruff (lint+fix), ruff-format, mypy
```

There is **no automated test suite**. `llm_test_runs/` holds ad-hoc API
experiment scripts, not a formal test harness. When adding tests, create
`backend/tests/` and wire pytest in.

## Code Style

- **Ruff** for linting + formatting: line length **100**, target **py3.12**,
  rules `E, F, I` (Pyflakes `F` catches dead imports/vars). `E501` is delegated
  to the formatter. Config: [`backend/pyproject.toml`](backend/pyproject.toml).
- **mypy** with pragmatic prototype defaults (`ignore_missing_imports`), same file.
- Do not introduce Black/isort/flake8 — Ruff replaces all three.

### Docstrings & comments

Keep them short. Type hints already document types — don't repeat them.

- **Docstrings**: one line stating what the function does, in plain language.
  No `Args:`/`Returns:` blocks that just restate the typed signature, and no
  cross-references to other modules/files inside a docstring. Add a second line
  only for genuinely non-obvious behavior — a side effect, or a `Raises:` the
  caller must handle. If the name and signature already say it, a docstring is
  optional.
- **Comments**: explain *why*, not *what*. Skip comments that narrate the next
  line. Delete section-divider and step-by-step ("Step 1:", "# --- setup ---")
  comments unless they aid navigation in a long file.
- Prefer no comment over a redundant one. Terse and clear beats thorough.

```python
# Avoid — restates the signature, lists args, references files
def parse_document_sync(file_url, file_content):
    """
    Synchronous parsing method for direct use (not background task).

    Args:
        file_url: URL to PDF file
        file_content: Base64-encoded PDF content
    Returns:
        A PDFProcessingResult (see api/routers/pdf_parser/schema.py)
    """

# Prefer
def parse_document_sync(file_url, file_content):
    """Parse a PDF synchronously and return the extracted content."""
```

## Development Guidelines

1. **Read existing code first** — match surrounding patterns, naming, and idiom.
2. **Reuse existing helpers** — check `core/utils/`, `core/llm/`, and `config/`
   before adding new utilities.
3. **Keep it simple** — this is a prototype; avoid re-introducing the
   "enterprise" service-registry/factory scaffolding that was removed. The
   pipeline is deliberately just services called in order.
4. **Configuration is env-driven** — read/add settings via `config/` (which reads
   env vars), never hardcode URLs, ports, model names, or thresholds. The single
   source for the model endpoint is `config.llm.LLM_BASE_URL`.
5. **Errors** — raise the typed exceptions in `core/utils/errors.py`
   (`BaseCustomsError` subclasses carry `error_code` + HTTP `status_code`). The
   global handler in `main.py` maps them to `ErrorResponse` JSON. Don't return
   ad-hoc error dicts from routes.
6. **Logging, not `print`** — use the shared `logger` from `core/utils/logger.py`.
7. **LLM output** — validate against a Pydantic model in
   `core/llm/response_models.py` rather than parsing raw text ad hoc.
8. **Services should work standalone** — routers call services directly, so keep
   service methods usable without the FastAPI layer.

## Configuration & Secrets

- All settings live under `backend/config/` and are documented in
  [`backend/.env.example`](backend/.env.example). Copy it to `backend/.env`.
- Key variable: **`LLM_BASE_URL`** — the OpenAI-compatible endpoint of the model
  server (e.g. `http://host.docker.internal:8080/v1/`, or `http://vllm:80/v1/`
  when co-located on a Docker network).
- Never commit `.env` or model weights (both git-ignored). `.env.example`
  templates are the only env files that should be tracked.
- **API-key auth is opt-in**: when `ADMIN_API_KEY` is set, all data endpoints
  require it in the `X-API-Key` header (`/health-check` stays open); when unset,
  auth is disabled. Enforced by the `require_api_key` dependency in
  `core/utils/auth.py`, wired in `api/router.py`.

## Deployment & DevOps

- Docker-based; no CI/CD is configured. `backend/Dockerfile` builds the API;
  `backend/run_stack.bash [vllm|tgi]` (vLLM by default) brings up model server +
  backend on a private network and waits for health.
- Background work uses Huey (in-memory in dev, SQLite in production via
  `ENVIRONMENT=production`).
- pre-commit hooks keep the tree clean and formatted.
