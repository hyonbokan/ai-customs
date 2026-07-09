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

# Exception class names and message fragments that indicate the server could not
# be reached (DNS/connection failure), as opposed to a server that responded with
# an error. Matched by name so we don't have to import requests/httpx/urllib3.
_CONNECTION_ERROR_NAMES = {
    "ConnectionError",
    "ConnectError",
    "ConnectTimeout",
    "ConnectTimeoutError",
    "NewConnectionError",
    "MaxRetryError",
    "gaierror",
}
_CONNECTION_ERROR_FRAGMENTS = (
    "failed to resolve",
    "name or service not known",
    "nodename nor servname",
    "getaddrinfo",
    "connection refused",
    "max retries exceeded",
    "cannot connect",
    "connection aborted",
)


def _is_connection_error(exc: Exception) -> bool:
    """True if the exception (or any cause) indicates the server was unreachable."""
    names = set()
    messages = []
    current: Optional[BaseException] = exc
    while current is not None:
        names.add(type(current).__name__)
        messages.append(str(current).lower())
        current = current.__cause__ or current.__context__
    if names & _CONNECTION_ERROR_NAMES:
        return True
    return any(frag in msg for msg in messages for frag in _CONNECTION_ERROR_FRAGMENTS)


class OpenAICompatibleClient:
    """Client for OpenAI-compatible LLM services like vLLM."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.async_client = AsyncInferenceClient(
            base_url=base_url, timeout=config.llm.REQUEST_TIMEOUT
        )
        self.client = InferenceClient(base_url=base_url, timeout=config.llm.REQUEST_TIMEOUT)

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
                # An empty body is usually a transient server hiccup, so retry it.
                raise LLMError("Empty response content from LLM", retryable=True)

            if response_model:
                return self._parse_structured_response(content, response_model)
            return content

        except LLMError:
            # Already-classified errors (e.g. unparseable response) pass through
            # with their retryable flag intact.
            raise
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            err = str(e)
            if "rate_limit" in err.lower() or "429" in err:
                raise RateLimitError(
                    message="LLM rate limit exceeded", details={"model": model, "error": err}
                ) from e
            # Transport-level failures (timeout, connection reset, 5xx) are transient.
            raise LLMError(
                message="LLM API error",
                details={"model": model, "error": err},
                retryable=True,
                connection_error=_is_connection_error(e),
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
