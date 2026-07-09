import asyncio
import json
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, overload

from huggingface_hub import AsyncInferenceClient, InferenceClient
from pydantic import BaseModel

from config import config
from core.utils.errors import LLMError, RateLimitError
from core.utils.logger import logger

# Type variable for structured responses
T = TypeVar("T", bound=BaseModel)

# Message type for chat completions
Message = Dict[str, str]


class OpenAICompatibleClient:
    """Client for OpenAI-compatible LLM services like vLLM."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.async_client = AsyncInferenceClient(base_url=base_url)
        self.client = InferenceClient(base_url=base_url)

    async def chat_completions_create(
        self,
        model: str,
        messages: List[Message],
        response_model: Optional[Type[T]] = None,
        temperature: float = config.llm.TEMPERATURE,
        max_tokens: int = config.llm.MAX_TOKENS,
        stream: bool = False,
        **kwargs,
    ) -> Union[T, str]:
        """
        Create chat completions using OpenAI-compatible API.
        """
        try:
            # Prepare parameters for OpenAI-compatible endpoint
            params: Dict[str, Any] = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": stream,
            }

            # Structured output support using response_format + JSON Schema
            if response_model:
                try:
                    schema = response_model.model_json_schema()  # type: ignore[attr-defined]
                    params["response_format"] = {"type": "json", "value": schema}
                except Exception:
                    # Fallback: ask for JSON only via prompt tweak
                    last = messages[-1] if messages else None
                    if last and last.get("role") == "user":
                        last["content"] += "\n\nPlease respond with valid JSON only."

            # Use sync client in a thread for better compatibility with HF hub
            response = await asyncio.to_thread(self.client.chat.completions.create, **params)

            # If streaming, aggregate chunks into a single string
            if stream:
                content_parts: List[str] = []
                for chunk in response:  # type: ignore[assignment]
                    try:
                        delta = chunk.choices[0].delta  # type: ignore[index]
                        piece = getattr(delta, "content", None)
                        if piece:
                            content_parts.append(piece)
                    except Exception:
                        continue
                content = "".join(content_parts).strip()
            else:
                # Non-streaming response: extract first choice content
                content = ""
                try:
                    if hasattr(response, "choices") and response.choices:
                        first_choice = response.choices[0]
                        if hasattr(first_choice, "message") and first_choice.message:
                            content = (first_choice.message.content or "").strip()
                except Exception:
                    content = ""

            if not content:
                raise LLMError("Empty response content from LLM")

            if response_model:
                return self._parse_structured_response(content, response_model)
            return content

        except Exception as e:
            logger.error(f"LLM API error: {e}")
            raise LLMError(
                message="LLM API error", details={"model": model, "error": str(e)}
            ) from e

    def _parse_structured_response(self, content: str, response_model: Type[T]) -> T:
        """Parse structured response from LLM."""
        try:
            # First try to parse the content as-is
            json_content = json.loads(content)
            return response_model.model_validate(json_content)

        except (json.JSONDecodeError, ValueError):
            # If that fails, try to extract JSON from the content
            try:
                # Look for JSON in the content (between { and })
                start = content.find("{")
                end = content.rfind("}") + 1

                if start != -1 and end > start:
                    json_str = content[start:end]
                    json_content = json.loads(json_str)
                    return response_model.model_validate(json_content)

                # If no JSON found, raise an error
                raise LLMError(
                    message="No valid JSON found in response", details={"content": content}
                )

            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse structured response: {e}")
                logger.error(f"Content: {content}")
                raise LLMError(
                    message="Failed to parse structured response",
                    details={"content": content, "error": str(e)},
                ) from e


@overload
async def send_prompt_to_llm_async(
    model_type: str = ...,
    messages: Optional[List[Message]] = ...,
    *,
    response_model: Type[T],
    temperature: float = ...,
    max_tokens: int = ...,
    base_url: str = ...,
    **kwargs: Any,
) -> T: ...


@overload
async def send_prompt_to_llm_async(
    model_type: str = ...,
    messages: Optional[List[Message]] = ...,
    response_model: None = ...,
    temperature: float = ...,
    max_tokens: int = ...,
    base_url: str = ...,
    **kwargs: Any,
) -> str: ...


async def send_prompt_to_llm_async(
    model_type: str = config.llm.LLM_SERVICE_TYPE,
    messages: Optional[List[Message]] = None,
    response_model: Optional[Type[T]] = None,
    temperature: float = config.llm.TEMPERATURE,
    max_tokens: int = config.llm.MAX_TOKENS,
    base_url: str = config.llm.LLM_BASE_URL,
    **kwargs,
) -> Union[T, str]:
    """
    Handle LLM API requests with structured output support.
    """
    if messages is None:
        messages = []

    await asyncio.sleep(config.llm.REQUEST_DELAY)

    try:
        # Try primary base URL first; fallback if DNS fails
        try_urls = [base_url]
        if config.llm.LLM_BASE_URL_FALLBACK and config.llm.LLM_BASE_URL_FALLBACK not in try_urls:
            try_urls.append(config.llm.LLM_BASE_URL_FALLBACK)

        last_error: Optional[Exception] = None
        for url in try_urls:
            try:
                llm_client = OpenAICompatibleClient(base_url=url)
                response = await llm_client.chat_completions_create(
                    model=model_type,
                    messages=messages,
                    response_model=response_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                return response
            except Exception as e:
                last_error = e
                continue

        # If all attempts failed, raise the last error
        if last_error:
            raise last_error

    except Exception as e:
        if "rate_limit" in str(e).lower() or "429" in str(e):
            logger.error(f"Rate limit hit for {model_type}: {e}")
            raise RateLimitError(
                message="LLM rate limit exceeded",
                details={"model": model_type, "error": str(e)},
            ) from e

        logger.error(f"LLM API error for {model_type}: {e}")
        raise LLMError(
            message="LLM API error",
            details={"model": model_type, "error": str(e)},
        ) from e

    # Defensive: the loop above always returns or raises; this guards against
    # an empty URL list and satisfies the return-type contract.
    raise LLMError(message="LLM request produced no response", details={"model": model_type})
