import os


class PipelineConfig:
    """Configuration for pipeline services and execution."""

    # Pipeline Initialization Service Config
    MAX_CONCURRENT_PIPELINES = int(os.getenv("PIPELINE_MAX_CONCURRENT", 2))
    PIPELINE_QUEUE_SIZE = int(os.getenv("PIPELINE_QUEUE_SIZE", 10))

    # PDF Parsing Service Config
    PDF_MAX_FILE_SIZE_MB = int(os.getenv("PDF_MAX_FILE_SIZE_MB", 50))
    PDF_TIMEOUT_SECONDS = int(os.getenv("PDF_TIMEOUT_SECONDS", 300))
    PDF_MIN_DOCUMENTS = int(os.getenv("PDF_MIN_DOCUMENTS", 2))
    PDF_MAX_DOCUMENTS = int(os.getenv("PDF_MAX_DOCUMENTS", 5))
    PDF_SUPPORTED_FORMATS = os.getenv("PDF_SUPPORTED_FORMATS", "pdf,jpg,png").split(",")

    # Docling PDF Processing Features
    PDF_ENABLE_OCR = os.getenv("PDF_ENABLE_OCR", "true").lower() == "true"
    PDF_ENABLE_TABLES = os.getenv("PDF_ENABLE_TABLES", "true").lower() == "true"
    PDF_OCR_LANGUAGES = os.getenv("PDF_OCR_LANGUAGES", "en,es,fr").split(",")
    PDF_FORCE_FULL_PAGE_OCR = os.getenv("PDF_FORCE_FULL_PAGE_OCR", "false").lower() == "true"

    # LLM Discrepancy Service Config
    LLM_CONFIDENCE_THRESHOLD = float(os.getenv("LLM_CONFIDENCE_THRESHOLD", 0.75))
    LLM_ANALYSIS_TIMEOUT = int(os.getenv("LLM_ANALYSIS_TIMEOUT", 180))
    LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", 3))
    LLM_DEEP_ANALYSIS = os.getenv("LLM_DEEP_ANALYSIS", "true").lower() == "true"

    # Document Types Configuration
    EXPECTED_DOCUMENT_TYPES = [
        "commercial_invoice",
        "customs_declaration",
        "certificate_of_origin",
        "packing_list",
        "bill_of_lading",
        "insurance_certificate",
        "other_permits",
    ]

    CRITICAL_DOCUMENT_TYPES = ["commercial_invoice", "customs_declaration"]

    RECOMMENDED_DOCUMENT_TYPES = ["certificate_of_origin", "packing_list", "bill_of_lading"]

    # Analysis Focus Areas
    ANALYSIS_FOCUS_AREAS = ["valuation", "classification", "origin", "compliance"]

    # Health Check Configuration
    HEALTH_CHECK_TIMEOUT = int(os.getenv("HEALTH_CHECK_TIMEOUT", 5))

    # Retry Configuration
    RETRY_EXPONENTIAL_BASE = int(os.getenv("RETRY_EXPONENTIAL_BASE", 2))

    # Environment-specific overrides
    @classmethod
    def get_development_overrides(cls) -> dict:
        """Get configuration overrides for development environment."""
        return {
            "MAX_CONCURRENT_PIPELINES": 1,
            "PDF_TIMEOUT_SECONDS": 60,
            "LLM_ANALYSIS_TIMEOUT": 60,
            "LLM_MAX_RETRIES": 1,
            "PDF_ENABLE_OCR": False,  # Disable OCR in dev for faster processing
            "PDF_FORCE_FULL_PAGE_OCR": False,
        }

    @classmethod
    def get_production_overrides(cls) -> dict:
        """Get configuration overrides for production environment."""
        return {
            "PIPELINE_QUEUE_SIZE": 50,
            "PDF_MAX_FILE_SIZE_MB": 100,
            "LLM_CONFIDENCE_THRESHOLD": 0.8,
            "LLM_MAX_RETRIES": 5,
            "PDF_ENABLE_OCR": True,  # Enable full OCR in production
            "PDF_ENABLE_TABLES": True,
        }

    @classmethod
    def get_test_overrides(cls) -> dict:
        """Get configuration overrides for test environment."""
        return {
            "MAX_CONCURRENT_PIPELINES": 1,
            "PDF_TIMEOUT_SECONDS": 10,
            "LLM_ANALYSIS_TIMEOUT": 10,
            "LLM_MAX_RETRIES": 1,
            "HEALTH_CHECK_TIMEOUT": 2,
            "PDF_ENABLE_OCR": False,  # Disable OCR in tests
            "PDF_ENABLE_TABLES": False,  # Disable table extraction in tests
        }
