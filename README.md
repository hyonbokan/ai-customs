# AI Customs

A self-hosted, open-source LLM system for detecting discrepancies in customs
declarations. It ingests trade documents (commercial invoices, customs
declarations, packing lists, certificates of origin, …), extracts structured
fields, and cross-checks them for valuation, classification, origin, and
compliance issues — all running **entirely on local hardware**, with no data
leaving the environment.

> **Status:** Prototype / proof-of-concept. This project was built as an
> exploration of running a fully self-hosted document-analysis pipeline for
> customs use cases and is shared here as a portfolio/reference project. It is
> not production-hardened.

---

## Why self-hosted?

Customs and trade data is highly sensitive and often subject to legal
restrictions on where it may be processed. Rather than sending documents to a
hosted API, this system runs an open-weight model (Google **Gemma-3-27B-IT**)
on local GPUs behind an OpenAI-compatible inference server, so declarations
never leave the operator's infrastructure.

## Architecture

```
                +------------------------------------------------------+
                |                    AI Customs Backend                |
                |                   (FastAPI, port 8000)               |
                |                                                      |
  PDF / images  |   /pdf-parser        Docling + OCR                   |
  ------------> |      |               (clean text + tables)          |
                |      v                                               |
                |   /analyze-declaration   structured LLM analysis     |
                |      |                                               |
                |      v                                               |
                |   /full-pipeline      parse -> extract -> report     |
                +----------------------------|-------------------------+
                                             | OpenAI-compatible /v1
                                             v
                +------------------------------------------------------+
                |          LLM Inference Server (port 8080)            |
                |     TGI or vLLM  ·  Gemma-3-27B-IT  ·  2x GPU        |
                +------------------------------------------------------+
```

Two independently deployable pieces:

1. **`backend/`** — a FastAPI application that orchestrates document parsing and
   LLM analysis. It talks to the model over an OpenAI-compatible `/v1` endpoint,
   so it works with either TGI or vLLM (or any compatible server).
2. **`llm_service_manual/`** — a self-contained, field-tested Docker deployment
   for serving Gemma-3 with **Text Generation Inference (TGI)**, including a
   model downloader, GPU auto-detection entrypoint, and troubleshooting guide.

## Pipeline

| Stage | Component | What it does |
|-------|-----------|--------------|
| 1. Parse | `pdf_parser` (Docling) | Extract clean text + tables from PDFs/images. OCR for scanned docs, no regex field extraction. |
| 2. Extract & Analyze | `declaration_analyzer` (LLM) | Language-agnostic field extraction and discrepancy detection via structured (JSON-schema) output. |
| 3. Report | `full_pipeline` | Chains parsing → analysis → a comprehensive final report in one call. |

The design principle is **"clean content extraction vs. intelligent
extraction"**: Docling is responsible only for turning documents into clean
text, and the LLM is responsible for all field interpretation and reasoning.
This keeps the system language- and layout-agnostic.

## Hardware

Developed and tested on a workstation with:

- **2× NVIDIA RTX A6000 (48 GB VRAM each, 96 GB total)**
- Gemma-3-27B-IT served with tensor parallelism across both GPUs
  (`--num-shard 2` for TGI / `--tensor-parallel-size 2` for vLLM)

96 GB of aggregate VRAM comfortably fits the 27B model in `float16` with room
for KV cache. Smaller GPUs can run smaller models by changing the model ID and
sharding settings (see `llm_service_manual/env.template`).

## Tech stack

- **API:** FastAPI + Uvicorn
- **Document parsing:** [Docling](https://github.com/DS4SD/docling), Tesseract / EasyOCR, PyMuPDF
- **LLM serving:** [TGI](https://github.com/huggingface/text-generation-inference) or [vLLM](https://github.com/vllm-project/vllm) (OpenAI-compatible)
- **Model:** Google Gemma-3-27B-IT (open weights)
- **Background tasks:** Huey (SQLite-backed)
- **Structured output:** Pydantic v2 + JSON-schema-constrained generation

---

## Quick start

The system has two halves — the **LLM inference server** and the **backend**.
Start the model server first, then point the backend at it.

### 1. Serve the model

Fastest path — run TGI directly (matches the 2-GPU setup above):

```bash
docker run --gpus all \
  -v ~/models/gemma-3-27b-it:/models/gemma-3-27b-it \
  -p 8080:80 \
  ghcr.io/huggingface/text-generation-inference:latest \
  --model-id /models/gemma-3-27b-it --trust-remote-code --num-shard 2
```

For a more robust, configurable deployment (model downloader, GPU
auto-detection, health checks), use the packaged setup:

```bash
cd llm_service_manual
cp env.template .env      # customize model, GPUs, batch sizes
./install.sh              # downloads model, builds & starts TGI
```

See [`llm_service_manual/README.md`](llm_service_manual/README.md) and
[`llm_service_manual/TROUBLESHOOTING.md`](llm_service_manual/TROUBLESHOOTING.md)
for details.

### 2. Run the backend

The one-command script builds the backend image, starts the model server, wires
them together on a Docker network, waits for both to be healthy, and prints a
smoke-test command:

```bash
cd backend
./run_stack.bash tgi      # or: ./run_stack.bash vllm
```

Ports, GPU count, model path, and timeouts are all overridable via environment
variables — see the header of `run_stack.bash`.

Or run the two pieces manually — see [`backend/README.md`](backend/README.md).

To run the backend without Docker:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # set LLM_BASE_URL to your model server
python main.py
```

### 3. Call the API

```bash
# Health check
curl http://localhost:8000/api/v1/health-check

# Analyze a declaration
curl -X POST http://localhost:8000/api/v1/analyze-declaration \
  -H "Content-Type: application/json" \
  -d @backend/request_body_examples/declaration_analysis.json
```

Interactive API docs are available at `http://localhost:8000/docs`.

## API endpoints

All endpoints are under the `/api/v1` prefix.

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/health-check` | Liveness check |
| `POST` | `/analyze-declaration` | Analyze structured declaration data for discrepancies (synchronous) |
| `POST` | `/pdf-parser/parse-direct` | Parse a PDF and return clean content immediately |
| `POST` | `/pdf-parser/parse-pdf` | Parse a PDF as a background task |
| `GET`  | `/pdf-parser/parse-status/{task_id}` · `/parse-result/{task_id}` | Poll background parse jobs |
| `GET`  | `/pdf-parser/capabilities` | Parser feature/config introspection |
| `POST` | `/full-pipeline/process` | End-to-end (synchronous): parse → extract → analyze → report |

Example request bodies live in [`backend/request_body_examples/`](backend/request_body_examples/).

## Configuration

All runtime configuration is environment-driven and centralized under
[`backend/config/`](backend/config/). Copy [`backend/.env.example`](backend/.env.example)
to `backend/.env` and adjust. The most important variable is:

- **`LLM_BASE_URL`** — the OpenAI-compatible endpoint of your model server
  (e.g. `http://host.docker.internal:8080/v1/` when the backend runs in Docker
  alongside a host-served model).

See `backend/.env.example` for the full list (LLM parameters, PDF/OCR settings,
pipeline thresholds, timeouts).

## Project structure

```
ai-customs/
├── backend/                    # FastAPI application
│   ├── api/routers/            # Endpoints: health, pdf_parser, declaration_analyzer, full_pipeline
│   ├── core/
│   │   ├── foundation/         # Service registry, factory, pipeline manager
│   │   ├── initializers/       # LLM connection bootstrap + health checks
│   │   ├── llm/                # LLM client, request handler, prompts, response models
│   │   ├── schemas/            # Shared API response schemas
│   │   └── utils/              # Logging, errors, throttling
│   ├── config/                 # Centralized env-driven configuration
│   ├── request_body_examples/  # Sample request payloads
│   └── run_stack.bash          # One-command TGI/vLLM + backend bring-up
├── llm_service_manual/         # Packaged TGI Gemma-3 deployment
└── llm_test_runs/              # Ad-hoc TGI/vLLM API experiments & notes
```

## Development

Linting, formatting, and type-checking are enforced with pre-commit
([Ruff](https://docs.astral.sh/ruff/) for lint + format, and mypy). Ruff's
Pyflakes rules catch dead imports and unused variables and autofix them.

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files -v
```

Tooling configuration lives in [`backend/pyproject.toml`](backend/pyproject.toml)
(`[tool.ruff]`, `[tool.mypy]`); hook versions live in
[`.pre-commit-config.yaml`](.pre-commit-config.yaml).

## License

No license file is currently included. Note that the Gemma model weights are
subject to Google's [Gemma Terms of Use](https://ai.google.dev/gemma/terms).
