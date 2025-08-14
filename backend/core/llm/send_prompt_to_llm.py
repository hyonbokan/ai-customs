from typing import List, Dict, Any, Optional, Type, TypeVar, Union
import asyncio
import json
from pydantic import BaseModel
from huggingface_hub import AsyncInferenceClient

from config import config
from core.utils.logger import logger
from core.utils.errors import LLMError, RateLimitError

# Type variable for structured responses
T = TypeVar('T', bound=BaseModel)

# Message type for chat completions
Message = Dict[str, str]

class TGIClient:
    """Client for Text Generation Interface (TGI) with OpenAI-compatible API."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = AsyncInferenceClient(model=base_url)
    
    async def chat_completions_create(
        self,
        model: str,
        messages: List[Message],
        response_model: Optional[Type[T]] = None,
        temperature: float = config.llm.TEMPERATURE,
        max_tokens: int = config.llm.MAX_TOKENS,
        stream: bool = False,
        **kwargs
    ) -> Union[T, str]:
        """
        Create chat completions with TGI using HuggingFace AsyncInferenceClient API.
        """
        try:
            # Prepare parameters for TGI
            params = {
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": stream,
                **kwargs
            }
            
            # If we need structured output, we'll handle it via prompt engineering
            # since TGI may not support response_format parameter
            if response_model:
                # Add JSON output instruction to the last message
                if messages:
                    last_message = messages[-1]
                    if last_message.get("role") == "user":
                        last_message["content"] += "\n\nPlease provide your response in valid JSON format only."
            
            # Make the API call using HuggingFace AsyncInferenceClient
            response = await self.client.chat_completion(
                messages=messages,
                **params
            )
            
            # Process the response
            if hasattr(response, 'choices') and response.choices:
                content = response.choices[0].message.content.strip()
                
                if response_model:
                    # The response content should be a valid JSON string
                    return self._parse_structured_response(content, response_model)
                else:
                    return content
            else:
                raise LLMError("Invalid response format from TGI")
                
        except Exception as e:
            logger.error(f"TGI API error: {e}")
            raise LLMError(
                message="TGI API error",
                details={"model": model, "error": str(e)}
            ) from e
    
    def _parse_structured_response(self, content: str, response_model: Type[T]) -> T:
        """Parse structured response from TGI."""
        try:
            # First try to parse the content as-is
            json_content = json.loads(content)
            return response_model.model_validate(json_content)
            
        except (json.JSONDecodeError, ValueError):
            # If that fails, try to extract JSON from the content
            try:
                # Look for JSON in the content (between { and })
                start = content.find('{')
                end = content.rfind('}') + 1
                
                if start != -1 and end > start:
                    json_str = content[start:end]
                    json_content = json.loads(json_str)
                    return response_model.model_validate(json_content)
                
                # If no JSON found, raise an error
                raise LLMError(
                    message="No valid JSON found in response",
                    details={"content": content}
                )
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse structured response: {e}")
                logger.error(f"Content: {content}")
                raise LLMError(
                    message="Failed to parse structured response",
                    details={"content": content, "error": str(e)}
                ) from e

async def handle_tgi_request(
    model_type: str = config.llm.TGI_MODEL_TYPE,
    messages: Optional[List[Message]] = None,
    response_model: Optional[Type[T]] = None,
    temperature: float = config.llm.TEMPERATURE,
    max_tokens: int = config.llm.MAX_TOKENS,
    base_url: str = config.llm.TGI_BASE_URL,
    **kwargs
) -> Union[T, str]:
    """
    Handle TGI API requests with structured output support.
    """
    if messages is None:
        messages = []
    
    await asyncio.sleep(config.llm.REQUEST_DELAY)
    
    try:
        tgi_client = TGIClient(base_url=base_url)
        
        response = await tgi_client.chat_completions_create(
            model=model_type,
            messages=messages,
            response_model=response_model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        return response
        
    except Exception as e:
        if "rate_limit" in str(e).lower() or "429" in str(e):
            logger.error(f"Rate limit hit for {model_type}: {e}")
            raise RateLimitError(
                message="TGI rate limit exceeded",
                details={"model": model_type, "error": str(e)},
            ) from e
        
        logger.error(f"TGI API error for {model_type}: {e}")
        raise LLMError(
            message="TGI API error",
            details={"model": model_type, "error": str(e)},
        ) from e


def parse_model_response(content: str, response_model: Optional[Type[T]] = None) -> Union[T, str]:
    """
    Parse model response with optional structured output.
    """
    if not response_model:
        return content
    
    try:
        if content.strip().startswith('{'):
            data = json.loads(content)
            return response_model.model_validate(data)
        
        return content
        
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse response as structured output: {e}")
        return content

# Example usage and testing
async def test_tgi_client():
    """Test the TGI client with various scenarios."""
    from core.llm.response_models import CityInfo
    
    # Example 1: Simple text completion
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"}
    ]
    
    try:
        response = await handle_tgi_request(messages=messages, max_tokens=100)
        print(f"Simple response: {response}")
        
    except Exception as e:
        print(f"Error in simple test: {e}")
    
    # Example 2: Structured output
    try:
        structured_response = await handle_tgi_request(
            messages=messages,
            response_model=CityInfo,
        )
        print(f"Structured response: {structured_response}")
        
    except Exception as e:
        print(f"Error in structured test: {e}")


if __name__ == "__main__":
    import asyncio
    
    asyncio.run(test_tgi_client()) 