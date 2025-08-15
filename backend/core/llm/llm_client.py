import asyncio
import json
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from config import config
from core.llm.prompt_templates import PromptTemplates
from core.llm.response_models import CustomsAnalysisResponse
from core.llm.send_prompt_to_llm import handle_tgi_request
from core.llm.system_messages import SystemPrompts
from core.utils.errors import LLMError
from core.utils.logger import logger


class LLMClient:
    """Client for handling LLM interactions."""

    @staticmethod
    async def analyze_customs_declaration(
        declaration_data: Dict[str, Any], reference_data: Optional[Dict[str, Any]] = None
    ) -> CustomsAnalysisResponse:
        """
        Send customs declaration to LLM for analysis and get a structured response.
        """
        messages = [
            {"role": "system", "content": SystemPrompts.general_customs_analysis()},
            {
                "role": "user",
                "content": PromptTemplates.get_customs_analysis_prompt(
                    declaration_data, reference_data
                ),
            },
        ]

        try:
            # Request a structured response directly from the TGI handler
            response = await handle_tgi_request(
                model_type=config.llm.TGI_MODEL_TYPE,
                messages=messages,
                response_model=CustomsAnalysisResponse,
                temperature=config.llm.TEMPERATURE,
                max_tokens=config.llm.MAX_TOKENS,
            )

            # The handler now returns a Pydantic model instance if successful
            if isinstance(response, CustomsAnalysisResponse):
                return response

            # If we get a string, something went wrong with parsing inside the handler
            raise LLMError(
                message="LLM did not return a valid structured response.",
                details={"response": str(response)},
            )

        except (ValidationError, LLMError) as e:
            logger.error(f"LLM response validation failed: {e}")
            raise LLMError(
                message="LLM response validation failed.", details={"error": str(e)}
            ) from e
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            # Propagate so upstream API can return success: false
            raise

    @staticmethod
    def process_llm_response(response: str) -> Dict[str, Any]:
        """
        Process and validate LLM response.
        DEPRECATED in favor of direct Pydantic model validation.
        """
        try:
            # This is a fallback parser if we are not using response_model
            if response.strip().startswith("{"):
                return json.loads(response)

            # If not JSON, create a structured-like error response
            return {
                "discrepancies_found": 1,
                "issues": [
                    {
                        "category": "parsing",
                        "severity": "high",
                        "description": "Failed to parse LLM text response.",
                        "recommendation": "Check LLM logs.",
                    }
                ],
                "recommendations": ["Manual review required"],
                "risk_level": "high",
                "requires_inspection": True,
            }
        except Exception as e:
            return {
                "discrepancies_found": 1,
                "issues": [
                    {
                        "category": "parsing",
                        "severity": "critical",
                        "description": f"Error processing LLM response: {str(e)}",
                        "recommendation": "Check LLM logs.",
                    }
                ],
                "recommendations": ["Manual review required"],
                "risk_level": "critical",
                "requires_inspection": True,
            }

    @staticmethod
    def generate_summary_report(analysis_result: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary report.
        """
        discrepancies = analysis_result.get("discrepancies_found", 0)
        issues = analysis_result.get("issues", [])

        if discrepancies == 0:
            return f"No discrepancies found."
        else:
            summary = f"{discrepancies} discrepancies found:\n"
            for issue in issues:
                desc = issue.get("description", "No description provided.")
                summary += f"- {desc}\n"
            return summary
