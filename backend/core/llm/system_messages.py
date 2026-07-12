"""
Centralized system messages for LLM interactions in the customs analysis pipeline.

This module provides a single source of truth for all system-level prompts used
across field extraction, discrepancy analysis, and report generation.
"""


class SystemPrompts:
    """System messages used by the pipeline for different stages."""

    @staticmethod
    def field_extraction() -> str:
        return (
            "You are an expert customs document processor with deep knowledge of "
            "international trade documentation."
        )

    @staticmethod
    def discrepancy_analysis() -> str:
        return (
            "You are an expert customs analyst with extensive experience in trade "
            "compliance and fraud detection."
        )

    @staticmethod
    def reporting() -> str:
        return "You are an expert customs reporting specialist."
