"""
Workflow Configuration for Customs Analysis Pipeline.

This configuration references API router services rather than core services,
following the correct architecture where core contains only foundational classes.
"""

from typing import Any, Dict

from config import config


class CustomsWorkflowConfig:
    """Configuration for the customs analysis workflow using API router services."""

    @staticmethod
    def get_pipeline_config() -> Dict[str, Any]:
        """
        Get the complete pipeline configuration for customs analysis.

        This defines the actual workflow using API router services:
        1. PDF Parser API: Clean content extraction with Docling
        2. Declaration Analyzer API: LLM-based field extraction and analysis
        """
        return {
            "api_services": [
                {
                    "name": "pdf_parser",
                    "endpoint": "/api/v1/pdf-parser",
                    "description": "Docling-based PDF parsing for clean content extraction",
                    "methods": ["parse-pdf", "parse-direct", "parse-status", "parse-result"],
                    "config": {
                        "enable_ocr": config.pipeline.PDF_ENABLE_OCR,
                        "enable_tables": config.pipeline.PDF_ENABLE_TABLES,
                        "max_file_size_mb": config.pipeline.PDF_MAX_FILE_SIZE_MB,
                        "timeout_seconds": config.pipeline.PDF_TIMEOUT_SECONDS,
                        "supported_formats": config.pipeline.PDF_SUPPORTED_FORMATS,
                    },
                    "role": "Extract clean content for LLM consumption",
                },
                {
                    "name": "declaration_analyzer",
                    "endpoint": "/api/v1/analyze-declaration",
                    "description": "LLM-based customs declaration analysis",
                    "methods": ["analyze-declaration", "analysis-status", "analysis-result"],
                    "config": {
                        "confidence_threshold": config.pipeline.LLM_CONFIDENCE_THRESHOLD,
                        "analysis_timeout": config.pipeline.LLM_ANALYSIS_TIMEOUT,
                        "max_retries": config.pipeline.LLM_MAX_RETRIES,
                        "deep_analysis": config.pipeline.LLM_DEEP_ANALYSIS,
                    },
                    "role": "Intelligent field extraction and discrepancy analysis",
                },
            ],
            "workflow_steps": [
                {
                    "step": 1,
                    "name": "pdf_content_extraction",
                    "service": "pdf_parser",
                    "endpoint": "/api/v1/pdf-parser/parse-direct",
                    "input": "PDF documents (URLs or base64)",
                    "output": "Clean text, tables, document structure",
                    "description": "Extract clean content using Docling without field extraction",
                },
                {
                    "step": 2,
                    "name": "llm_field_extraction_and_analysis",
                    "service": "declaration_analyzer",
                    "endpoint": "/api/v1/analyze-declaration",
                    "input": "Clean content from PDF parser",
                    "output": "Extracted fields, discrepancies, analysis",
                    "description": "Intelligent field extraction and cross-document analysis",
                },
            ],
            "architecture_principles": {
                "separation_of_concerns": "PDF parser extracts content, LLM extracts intelligence",
                "no_regex_extraction": "Field extraction delegated to LLM for accuracy",
                "language_agnostic": "Works with documents in any language",
                "format_flexible": "LLM handles any document layout or structure",
            },
        }

    @staticmethod
    def get_development_config() -> Dict[str, Any]:
        """Get configuration for development environment."""
        config_base = CustomsWorkflowConfig.get_pipeline_config()

        # Apply development overrides
        dev_overrides = config.pipeline.get_development_overrides()

        # Update API service configurations
        for service in config_base["api_services"]:
            if service["name"] == "pdf_parser":
                service["config"]["enable_ocr"] = dev_overrides.get("PDF_ENABLE_OCR", False)
                service["config"]["timeout_seconds"] = dev_overrides.get("PDF_TIMEOUT_SECONDS", 60)
            elif service["name"] == "declaration_analyzer":
                service["config"]["analysis_timeout"] = dev_overrides.get(
                    "LLM_ANALYSIS_TIMEOUT", 60
                )
                service["config"]["max_retries"] = dev_overrides.get("LLM_MAX_RETRIES", 1)

        return config_base

    @staticmethod
    def get_production_config() -> Dict[str, Any]:
        """Get configuration for production environment."""
        config_base = CustomsWorkflowConfig.get_pipeline_config()

        # Apply production overrides
        prod_overrides = config.pipeline.get_production_overrides()

        # Update API service configurations
        for service in config_base["api_services"]:
            if service["name"] == "pdf_parser":
                service["config"]["enable_ocr"] = prod_overrides.get("PDF_ENABLE_OCR", True)
                service["config"]["enable_tables"] = prod_overrides.get("PDF_ENABLE_TABLES", True)
                service["config"]["max_file_size_mb"] = prod_overrides.get(
                    "PDF_MAX_FILE_SIZE_MB", 100
                )
            elif service["name"] == "declaration_analyzer":
                service["config"]["confidence_threshold"] = prod_overrides.get(
                    "LLM_CONFIDENCE_THRESHOLD", 0.8
                )
                service["config"]["max_retries"] = prod_overrides.get("LLM_MAX_RETRIES", 5)

        return config_base


def get_workflow_config_for_environment(environment: str = "development") -> Dict[str, Any]:
    """
    Get workflow configuration for a specific environment.

    Args:
        environment: Environment name (development, production, test)

    Returns:
        Workflow configuration dictionary with API service references
    """
    if environment.lower() == "production":
        return CustomsWorkflowConfig.get_production_config()
    elif environment.lower() in ["development", "dev"]:
        return CustomsWorkflowConfig.get_development_config()
    elif environment.lower() == "test":
        return CustomsWorkflowConfig.get_development_config()  # Use dev config for tests
    else:
        return CustomsWorkflowConfig.get_pipeline_config()


# Example usage data structures for the API-based pipeline

EXAMPLE_API_WORKFLOW_INPUT = {
    "step_1_pdf_parsing": {
        "endpoint": "/api/v1/pdf-parser/parse-direct",
        "method": "POST",
        "payload": {"file_url": "https://example.com/invoice.pdf"},
        "expected_output": {
            "success": True,
            "text_content": "Clean extracted text...",
            "tables": [{"table_id": 0, "data": [...]}],
            "ready_for_llm": True,
        },
    },
    "step_2_llm_analysis": {
        "endpoint": "/api/v1/analyze-declaration",
        "method": "POST",
        "payload": {
            "declaration_data": "Output from step 1",
            "reference_data": {"additional_context": "..."},
        },
        "expected_output": {"task_id": "analysis_123", "status": "queued"},
    },
}

EXAMPLE_API_WORKFLOW_OUTPUT = {
    "pdf_parsing_result": {
        "success": True,
        "extraction_method": "docling",
        "content_quality": "clean_for_llm_consumption",
    },
    "llm_analysis_result": {
        "status": "completed",
        "fields_extracted": "intelligent_extraction_without_regex",
        "discrepancies_found": 2,
        "confidence_score": 0.85,
    },
    "workflow_summary": {
        "architecture": "API-based microservices",
        "pdf_parser_role": "Clean content extraction",
        "llm_role": "Intelligent field extraction and analysis",
        "benefits": "Language agnostic, format flexible, maintainable",
    },
}
