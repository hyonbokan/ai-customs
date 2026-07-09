from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from config import config
from core.llm.llm_request_handler import send_prompt_to_llm_async
from core.llm.prompt_templates import PromptTemplates
from core.llm.response_models import CustomsAnalysisResponse
from core.llm.system_messages import SystemPrompts
from core.utils.errors import LLMError
from core.utils.logger import logger


class LLMClient:
    """Client for handling LLM interactions."""

    @staticmethod
    def create_messages(
        user_content: str,
        system_content: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = []
        if system_content:
            messages.append({"role": "system", "content": system_content})
        messages.append({"role": "user", "content": user_content})
        return messages

    @staticmethod
    async def analyze_customs_declaration(
        declaration_data: Dict[str, Any], reference_data: Optional[Dict[str, Any]] = None
    ) -> CustomsAnalysisResponse:
        """
        Send customs declaration to LLM for analysis and get a structured response.
        """
        user_content = PromptTemplates.get_customs_analysis_prompt(declaration_data, reference_data)
        system_content = SystemPrompts.general_customs_analysis()

        messages = LLMClient.create_messages(
            user_content=user_content,
            system_content=system_content,
        )

        try:
            response = await send_prompt_to_llm_async(
                messages=messages,
                response_model=CustomsAnalysisResponse,
                temperature=config.llm.TEMPERATURE,
                max_tokens=config.llm.MAX_TOKENS,
            )

            if isinstance(response, CustomsAnalysisResponse):
                return response

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
            raise
