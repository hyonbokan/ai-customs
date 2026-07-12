import os


class PipelineConfig:
    """Configuration for pipeline services and execution."""

    # PDF Parsing Service Config
    PDF_MAX_FILE_SIZE_MB = int(os.getenv("PDF_MAX_FILE_SIZE_MB", 50))
    PDF_TIMEOUT_SECONDS = int(os.getenv("PDF_TIMEOUT_SECONDS", 300))
    PDF_SUPPORTED_FORMATS = os.getenv("PDF_SUPPORTED_FORMATS", "pdf,jpg,png").split(",")

    # Docling PDF Processing Features
    PDF_ENABLE_OCR = os.getenv("PDF_ENABLE_OCR", "true").lower() == "true"
    PDF_ENABLE_TABLES = os.getenv("PDF_ENABLE_TABLES", "true").lower() == "true"
    PDF_OCR_LANGUAGES = os.getenv("PDF_OCR_LANGUAGES", "en,es,fr").split(",")
    PDF_FORCE_FULL_PAGE_OCR = os.getenv("PDF_FORCE_FULL_PAGE_OCR", "false").lower() == "true"

    # LLM retry policy (used by core/llm/llm_request_handler.py)
    LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", 3))
    RETRY_EXPONENTIAL_BASE = int(os.getenv("RETRY_EXPONENTIAL_BASE", 2))

    # Value analysis: an assessed value exceeding the declared value by more than this
    # ratio is reported as a potential under-declaration.
    VALUE_GAP_RATIO = float(os.getenv("VALUE_GAP_RATIO", 1.1))

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
