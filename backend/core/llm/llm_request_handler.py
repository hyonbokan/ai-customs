"""Async chat requests to an OpenAI-compatible LLM server.

One public entry point, send_prompt_to_llm_async: sends the messages, retries
transient failures with exponential backoff, falls back to a second base URL
when the first is unreachable, and — when a response model is given — requests
schema-guided decoding and returns the validated instance.
"""

import asyncio
import json
from functools import lru_cache
from typing import Any, overload

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

# Message type for chat completions
Message = dict[str, str]


@overload
async def send_prompt_to_llm_async[T: BaseModel](
    messages: list[Message],
    *,
    response_model: type[T],
    model_type: str | None = ...,
    temperature: float | None = ...,
    max_tokens: int | None = ...,
) -> T: ...


@overload
async def send_prompt_to_llm_async(
    messages: list[Message],
    *,
    response_model: None = ...,
    model_type: str | None = ...,
    temperature: float | None = ...,
    max_tokens: int | None = ...,
) -> str: ...


async def send_prompt_to_llm_async[T: BaseModel](
    messages: list[Message],
    *,
    response_model: type[T] | None = None,
    model_type: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> T | str:
    """Send a chat request and return the response text or validated model instance.

    Retries transient failures (timeouts, connection errors, 5xx, empty bodies)
    with exponential backoff. Arguments left as None fall back to the configured
    defaults at call time.
    """
    model = model_type or config.llm.LLM_SERVICE_TYPE
    if temperature is None:
        temperature = config.llm.TEMPERATURE
    if max_tokens is None:
        max_tokens = config.llm.MAX_TOKENS

    await asyncio.sleep(config.llm.REQUEST_DELAY)

    max_retries = config.pipeline.LLM_MAX_RETRIES
    backoff_base = config.pipeline.RETRY_EXPONENTIAL_BASE

    for attempt_no in range(max_retries + 1):
        try:
            return await _attempt_with_fallback(
                model, messages, response_model, temperature, max_tokens
            )
        except LLMError as e:
            if not e.retryable or attempt_no == max_retries:
                logger.error(f"LLM API error for {model}: {e.message}")
                raise
            delay = backoff_base**attempt_no
            logger.warning(
                f"LLM call for {model} failed "
                f"(attempt {attempt_no + 1}/{max_retries + 1}), retrying in {delay}s: {e.message}"
            )
            await asyncio.sleep(delay)

    raise AssertionError("unreachable: the retry loop always returns or raises")


@lru_cache(maxsize=4)
def _async_client(base_url: str) -> AsyncOpenAI:
    """Return a cached AsyncOpenAI client for a base URL (pools connections).

    max_retries=0 because retries and backoff are handled by the caller, not
    the SDK.
    """
    return AsyncOpenAI(
        base_url=base_url,
        api_key=config.llm.LLM_API_KEY,
        timeout=config.llm.REQUEST_TIMEOUT,
        max_retries=0,
    )


async def _attempt_with_fallback[T: BaseModel](
    model: str,
    messages: list[Message],
    response_model: type[T] | None,
    temperature: float,
    max_tokens: int,
) -> T | str:
    """Try the primary base URL, then the configured fallback.

    Only an unreachable server moves on to the next URL; if the server
    responded (parse error, rate limit, timeout), the fallback points at the
    same server and won't help.
    """
    urls = [config.llm.LLM_BASE_URL]
    if config.llm.LLM_BASE_URL_FALLBACK and config.llm.LLM_BASE_URL_FALLBACK not in urls:
        urls.append(config.llm.LLM_BASE_URL_FALLBACK)

    last_error: LLMError | None = None
    for url in urls:
        try:
            return await _chat_completion(
                url, model, messages, response_model, temperature, max_tokens
            )
        except LLMError as e:
            last_error = e
            if not e.connection_error:
                raise
            logger.warning(f"Could not reach {url}; trying next base URL")

    assert last_error is not None
    raise last_error


async def _chat_completion[T: BaseModel](
    base_url: str,
    model: str,
    messages: list[Message],
    response_model: type[T] | None,
    temperature: float,
    max_tokens: int,
) -> T | str:
    """One chat-completion request; API failures raise a classified LLMError."""
    params = _request_params(model, messages, response_model, temperature, max_tokens)
    try:
        response = await _async_client(base_url).chat.completions.create(**params)
        content = ""
        if response.choices and response.choices[0].message:
            content = (response.choices[0].message.content or "").strip()
    except Exception as e:
        raise _classified_error(e, model) from e

    if not content:
        # An empty body is usually a transient server hiccup, so retry it.
        raise LLMError("Empty response content from LLM", retryable=True)

    if response_model:
        return _parse_structured_response(content, response_model)
    return content


def _request_params(
    model: str,
    messages: list[Message],
    response_model: type[BaseModel] | None,
    temperature: float,
    max_tokens: int,
) -> dict[str, Any]:
    """Build the request body for an OpenAI-compatible chat completion.

    OpenAI's gpt-5 family renamed max_tokens to max_completion_tokens and
    rejects non-default temperatures; self-hosted models (vLLM/TGI) and older
    OpenAI models keep the original parameters. Structured output uses the
    OpenAI-standard json_schema response format, which both vLLM and TGI honor
    for guided decoding.
    """
    params: dict[str, Any] = {"model": model, "messages": messages}
    if model.startswith("gpt-5"):
        params["max_completion_tokens"] = max_tokens
    else:
        params["max_tokens"] = max_tokens
        params["temperature"] = temperature
    if response_model:
        params["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": response_model.__name__,
                "schema": response_model.model_json_schema(),
                "strict": True,
            },
        }
    return params


def _classified_error(error: Exception, model: str) -> LLMError:
    """Map an exception from the request to an LLMError with retry semantics."""
    if isinstance(error, LLMError):
        # Already classified (e.g. empty response) — keep its retryable flag.
        return error
    if isinstance(error, APITimeoutError):
        return LLMError(
            message="LLM request timed out",
            details={"model": model, "error": str(error)},
            retryable=True,
        )
    if isinstance(error, APIConnectionError):
        return LLMError(
            message="Cannot reach LLM server",
            details={"model": model, "error": str(error)},
            retryable=True,
            connection_error=True,
        )
    if isinstance(error, OpenAIRateLimitError):
        return RateLimitError(
            message="LLM rate limit exceeded", details={"model": model, "error": str(error)}
        )
    if isinstance(error, APIStatusError):
        # 5xx is transient and worth retrying; 4xx is a client/request error.
        return LLMError(
            message="LLM API error",
            details={"model": model, "status_code": error.status_code, "error": str(error)},
            retryable=error.status_code >= 500,
        )
    logger.error(f"LLM API error: {error}")
    return LLMError(
        message="LLM API error",
        details={"model": model, "error": str(error)},
        retryable=True,
    )


def _parse_structured_response[T: BaseModel](content: str, response_model: type[T]) -> T:
    """Validate the response content against the model, tolerating prose
    around the JSON body."""
    try:
        return response_model.model_validate(json.loads(content))
    except (json.JSONDecodeError, ValueError):
        pass

    # Fall back to the outermost {...} span in the content.
    start = content.find("{")
    end = content.rfind("}") + 1
    if start == -1 or end <= start:
        raise LLMError(message="No valid JSON found in response", details={"content": content})

    try:
        return response_model.model_validate(json.loads(content[start:end]))
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse structured response: {e}")
        logger.error(f"Content: {content}")
        raise LLMError(
            message="Failed to parse structured response",
            details={"content": content, "error": str(e)},
        ) from e
