"""
PDF Processing Configuration

This module contains optimized PDF processing configurations for different environments.
These configurations are designed to address common extraction issues like missing dashes,
incorrect text positioning, and poor table recognition.
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class PDFProcessingConfig:
    """PDF processing configuration settings."""

    # Core Docling settings
    enable_ocr: bool
    enable_tables: bool
    force_full_page_ocr: bool
    ocr_languages: List[str]

    # Table extraction settings
    enable_cell_matching: bool
    table_mode: str  # "FAST", "ACCURATE", "FAST_ACCURATE"

    # File processing limits
    max_file_size_mb: int
    timeout_seconds: int

    # Text cleaning and validation
    enable_text_cleaning: bool
    enable_pattern_fixes: bool
    validate_extraction_quality: bool

    # Performance settings
    max_concurrent_extractions: int
    use_thread_pool: bool


class PDFConfigurations:
    """Predefined PDF processing configurations for different environments."""

    @staticmethod
    def get_production_config() -> PDFProcessingConfig:
        """
        Production configuration optimized for accuracy and reliability.
        Addresses issues like:
        - Missing dashes in invoice numbers (WHJT-J-200904421 → WHJT-J-200904-21)
        - Incorrect text extraction (SECURITY PACKING → SECURITY JACKET)
        - Missing weight information (N.W./G.W. detection)
        """
        return PDFProcessingConfig(
            # Enable OCR for maximum accuracy
            enable_ocr=True,
            enable_tables=True,
            force_full_page_ocr=True,  # Critical for complex layouts
            ocr_languages=["en", "es", "fr", "zh", "ar"],  # International trade languages
            # Advanced table processing
            enable_cell_matching=True,
            table_mode="ACCURATE",
            # Production limits
            max_file_size_mb=100,
            timeout_seconds=300,
            # Enhanced text processing
            enable_text_cleaning=True,
            enable_pattern_fixes=True,
            validate_extraction_quality=True,
            # Performance for production
            max_concurrent_extractions=3,
            use_thread_pool=True,
        )

    @staticmethod
    def get_development_config() -> PDFProcessingConfig:
        """
        Development configuration balanced for speed and accuracy.
        Still enables OCR but with faster settings.
        """
        return PDFProcessingConfig(
            # Enable OCR but optimize for speed
            enable_ocr=True,
            enable_tables=True,
            force_full_page_ocr=False,  # Faster processing
            ocr_languages=["en"],  # Reduced language set
            # Balanced table processing
            enable_cell_matching=True,
            table_mode="FAST_ACCURATE",  # If available, otherwise "ACCURATE"
            # Development limits
            max_file_size_mb=50,
            timeout_seconds=120,
            # Text processing enabled
            enable_text_cleaning=True,
            enable_pattern_fixes=True,
            validate_extraction_quality=True,
            # Development performance
            max_concurrent_extractions=2,
            use_thread_pool=True,
        )

    @staticmethod
    def get_test_config() -> PDFProcessingConfig:
        """
        Test configuration optimized for fast execution.
        Minimal but functional settings for testing.
        """
        return PDFProcessingConfig(
            # Minimal OCR for testing
            enable_ocr=True,  # Still enable for integration tests
            enable_tables=True,
            force_full_page_ocr=False,
            ocr_languages=["en"],
            # Basic table processing
            enable_cell_matching=True,
            table_mode="FAST",
            # Test limits
            max_file_size_mb=10,
            timeout_seconds=30,
            # Essential text processing
            enable_text_cleaning=True,
            enable_pattern_fixes=True,
            validate_extraction_quality=False,  # Skip validation in tests
            # Test performance
            max_concurrent_extractions=1,
            use_thread_pool=False,
        )

    @staticmethod
    def get_high_accuracy_config() -> PDFProcessingConfig:
        """
        High accuracy configuration for critical documents.
        Maximum quality settings regardless of performance impact.
        """
        return PDFProcessingConfig(
            # Maximum OCR accuracy
            enable_ocr=True,
            enable_tables=True,
            force_full_page_ocr=True,
            ocr_languages=["en", "es", "fr", "de", "zh", "ar", "ja", "ko"],
            # Maximum table accuracy
            enable_cell_matching=True,
            table_mode="ACCURATE",
            # Extended limits
            max_file_size_mb=200,
            timeout_seconds=600,
            # Maximum text processing
            enable_text_cleaning=True,
            enable_pattern_fixes=True,
            validate_extraction_quality=True,
            # Quality over speed
            max_concurrent_extractions=1,
            use_thread_pool=True,
        )

    @staticmethod
    def get_config_by_environment(environment: Optional[str] = None) -> PDFProcessingConfig:
        """
        Get configuration based on environment.

        Args:
            environment: Environment name (development, production, test, high_accuracy)
                        If None, reads from ENVIRONMENT env var, defaults to development

        Returns:
            Appropriate PDFProcessingConfig for the environment
        """
        if environment is None:
            environment = os.getenv("ENVIRONMENT", "development")

        config_map = {
            "production": PDFConfigurations.get_production_config,
            "development": PDFConfigurations.get_development_config,
            "test": PDFConfigurations.get_test_config,
            "high_accuracy": PDFConfigurations.get_high_accuracy_config,
        }

        config_func = config_map.get(environment.lower(), PDFConfigurations.get_development_config)
        return config_func()

    @staticmethod
    def get_docling_pipeline_options(config: PDFProcessingConfig) -> Dict[str, Any]:
        """
        Convert our config to Docling pipeline options.

        Args:
            config: PDFProcessingConfig instance

        Returns:
            Dictionary of options for Docling DocumentConverter
        """
        return {
            "do_ocr": config.enable_ocr,
            "force_full_page_ocr": config.force_full_page_ocr,
            "ocr_languages": config.ocr_languages,
            "do_table_structure": config.enable_tables,
            "do_cell_matching": config.enable_cell_matching,
            "table_mode": config.table_mode,
            "timeout_seconds": config.timeout_seconds,
            "max_file_size_mb": config.max_file_size_mb,
        }


class PDFConfigManager:
    """Manager class for PDF configuration with runtime overrides."""

    def __init__(self, environment: Optional[str] = None):
        self.environment = environment or os.getenv("ENVIRONMENT", "development")
        self._config = PDFConfigurations.get_config_by_environment(self.environment)
        self._overrides: Dict[str, Any] = {}

    @property
    def config(self) -> PDFProcessingConfig:
        """Get current configuration with any applied overrides."""
        if not self._overrides:
            return self._config

        # Apply overrides
        config_dict = self._config.__dict__.copy()
        config_dict.update(self._overrides)
        return PDFProcessingConfig(**config_dict)

    def set_override(self, key: str, value: Any) -> None:
        """Set a runtime override for a configuration value."""
        if hasattr(self._config, key):
            self._overrides[key] = value
        else:
            raise ValueError(f"Invalid configuration key: {key}")

    def clear_overrides(self) -> None:
        """Clear all runtime overrides."""
        self._overrides.clear()

    def get_docling_options(self) -> Dict[str, Any]:
        """Get Docling pipeline options for current configuration."""
        return PDFConfigurations.get_docling_pipeline_options(self.config)


# Default global configuration manager
pdf_config = PDFConfigManager()
