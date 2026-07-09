import os


class LLMConfig:
    """Configuration for LLM settings."""

    # Inference server (OpenAI-compatible endpoint; vLLM by default, TGI supported)
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://host.docker.internal:8080/v1/")
    # Optional fallback for Linux containers where host.docker.internal doesn't resolve
    LLM_BASE_URL_FALLBACK = os.getenv("LLM_BASE_URL_FALLBACK", "http://172.17.0.1:8080/v1/")
    LLM_SERVICE_TYPE = os.getenv("LLM_SERVICE_TYPE", "gemma-3-27b-it")

    # General LLM parameters
    TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0))
    MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", 8000))

    # Per-stage temperatures for the comprehensive analysis pipeline. Extraction
    # and reporting stay near-deterministic; discrepancy analysis allows a little
    # more variation for reasoning.
    EXTRACTION_TEMPERATURE = float(os.getenv("LLM_EXTRACTION_TEMPERATURE", 0.1))
    DISCREPANCY_TEMPERATURE = float(os.getenv("LLM_DISCREPANCY_TEMPERATURE", 0.2))
    REPORT_TEMPERATURE = float(os.getenv("LLM_REPORT_TEMPERATURE", 0.1))

    # Request settings
    REQUEST_TIMEOUT = int(os.getenv("LLM_REQUEST_TIMEOUT", 120))
    REQUEST_DELAY = float(os.getenv("LLM_REQUEST_DELAY", 0.1))
