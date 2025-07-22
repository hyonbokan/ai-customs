import os

class LLMConfig:
    """Configuration for LLM settings."""

    # TGI Configuration
    TGI_BASE_URL = os.getenv("TGI_BASE_URL", "http://localhost:8080/v1/")
    TGI_MODEL_TYPE = os.getenv("TGI_MODEL_TYPE", "tgi")
    
    # General LLM parameters
    TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0))
    MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", 8000))
    TOP_P = float(os.getenv("LLM_TOP_P", 1.0))
    
    # Request settings
    REQUEST_TIMEOUT = int(os.getenv("LLM_REQUEST_TIMEOUT", 120))
    CONNECT_TIMEOUT = int(os.getenv("LLM_CONNECT_TIMEOUT", 30))
    REQUEST_DELAY = float(os.getenv("LLM_REQUEST_DELAY", 0.1)) 