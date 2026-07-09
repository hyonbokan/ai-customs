import asyncio
import json
from functools import lru_cache
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, overload

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
)
from openai import RateLimitError as OpenAIRateLimitError
from pydantic import BaseModel

from config import config
from core.utils.errors import LLMError, RateLimitError
from core.utils.logger import logger

# Type variable for structured responses
T = TypeVar("T", bound=BaseModel)

# Message type for chat completions
Message = Dict[str, str]


@lru_cache(maxsize=4)
def _async_client(base_url: str) -> AsyncOpenAI:
    """Return a cached AsyncOpenAI client for a base URL (pools connections).

    max_retries=0 because retries and backoff are handled in
    send_prompt_to_llm_async, not by the SDK.
    """
    return AsyncOpenAI(
        base_url=base_url,
        api_key=config.llm.LLM_API_KEY,
        timeout=config.llm.REQUEST_TIMEOUT,
        max_retries=0,
    )


class OpenAICompatibleClient:
    """Client for OpenAI-compatible LLM services (vLLM, TGI)."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = _async_client(base_url)

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

            # Structured output via the OpenAI-standard json_schema response
            # format, which both vLLM (primary) and TGI honor for guided decoding.
            if response_model:
                try:
                    schema = response_model.model_json_schema()  # type: ignore[attr-defined]
                    params["response_format"] = {
                        "type": "json_schema",
                        "json_schema": {
                            "name": response_model.__name__,
                            "schema": schema,
                            "strict": True,
                        },
                    }
                except Exception:
                    # Fallback: ask for JSON only via prompt tweak
                    last = messages[-1] if messages else None
                    if last and last.get("role") == "user":
                        last["content"] += "\n\nPlease respond with valid JSON only."

            response = await self.client.chat.completions.create(**params)

            if stream:
                content_parts: List[str] = []
                async for chunk in response:  # type: ignore[union-attr]
                    delta = chunk.choices[0].delta if chunk.choices else None
                    piece = getattr(delta, "content", None) if delta else None
                    if piece:
                        content_parts.append(piece)
                content = "".join(content_parts).strip()
            else:
                content = ""
                if response.choices and response.choices[0].message:
                    content = (response.choices[0].message.content or "").strip()

            if not content:
                # An empty body is usually a transient server hiccup, so retry it.
                raise LLMError("Empty response content from LLM", retryable=True)

            if response_model:
                return self._parse_structured_response(content, response_model)
            return content

        except LLMError:
            # Already-classified errors (e.g. unparseable response) pass through
            # with their retryable flag intact.
            raise
        except APITimeoutError as e:
            raise LLMError(
                message="LLM request timed out",
                details={"model": model, "error": str(e)},
                retryable=True,
            ) from e
        except APIConnectionError as e:
            raise LLMError(
                message="Cannot reach LLM server",
                details={"model": model, "error": str(e)},
                retryable=True,
                connection_error=True,
            ) from e
        except OpenAIRateLimitError as e:
            raise RateLimitError(
                message="LLM rate limit exceeded", details={"model": model, "error": str(e)}
            ) from e
        except APIStatusError as e:
            # 5xx is transient and worth retrying; 4xx is a client/request error.
            raise LLMError(
                message="LLM API error",
                details={"model": model, "status_code": e.status_code, "error": str(e)},
                retryable=e.status_code >= 500,
            ) from e
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            raise LLMError(
                message="LLM API error",
                details={"model": model, "error": str(e)},
                retryable=True,
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

    # Try the primary base URL first, then the fallback (for Linux containers
    # where host.docker.internal doesn't resolve).
    try_urls = [base_url]
    if config.llm.LLM_BASE_URL_FALLBACK and config.llm.LLM_BASE_URL_FALLBACK not in try_urls:
        try_urls.append(config.llm.LLM_BASE_URL_FALLBACK)

    async def attempt() -> Union[T, str]:
        last: Optional[LLMError] = None
        for url in try_urls:
            try:
                client = OpenAICompatibleClient(base_url=url)
                return await client.chat_completions_create(
                    model=model_type,
                    messages=messages,
                    response_model=response_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
            except LLMError as e:
                last = e
                # Only try the next base URL when this one was unreachable. If the
                # server responded (parse error, rate limit, timeout), the fallback
                # points at the same server and won't help.
                if not e.connection_error:
                    raise
                logger.warning(f"Could not reach {url}; trying next base URL")
                continue
        raise last or LLMError(
            message="LLM request produced no response", details={"model": model_type}
        )

    max_retries = config.pipeline.LLM_MAX_RETRIES
    backoff_base = config.pipeline.RETRY_EXPONENTIAL_BASE

    last_error: Optional[LLMError] = None
    for attempt_no in range(max_retries + 1):
        try:
            return await attempt()
        except LLMError as e:
            last_error = e
            if not e.retryable or attempt_no == max_retries:
                logger.error(f"LLM API error for {model_type}: {e.message}")
                raise
            delay = backoff_base**attempt_no
            logger.warning(
                f"LLM call for {model_type} failed "
                f"(attempt {attempt_no + 1}/{max_retries + 1}), retrying in {delay}s: {e.message}"
            )
            await asyncio.sleep(delay)

    # Unreachable: the loop always returns or raises.
    raise last_error or LLMError(
        message="LLM request produced no response", details={"model": model_type}
    )
