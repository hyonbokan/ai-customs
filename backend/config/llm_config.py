import os


class LLMConfig:
    """Configuration for LLM settings."""

    # TGI Configuration
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://host.docker.internal:8080/v1/")
    # Optional fallback for Linux containers where host.docker.internal doesn't resolve
    LLM_BASE_URL_FALLBACK = os.getenv("LLM_BASE_URL_FALLBACK", "http://172.17.0.1:8080/v1/")
    LLM_SERVICE_TYPE = os.getenv("LLM_SERVICE_TYPE", "tgi")

    # General LLM parameters
    TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0))
    MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", 8000))
    TOP_P = float(os.getenv("LLM_TOP_P", 1.0))

    # Request settings
    REQUEST_TIMEOUT = int(os.getenv("LLM_REQUEST_TIMEOUT", 120))
    CONNECT_TIMEOUT = int(os.getenv("LLM_CONNECT_TIMEOUT", 30))
    REQUEST_DELAY = float(os.getenv("LLM_REQUEST_DELAY", 0.1))
