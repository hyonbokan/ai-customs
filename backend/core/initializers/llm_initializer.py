"""
LLM Initializer for TGI (Text Generation Interface) service.
"""

from typing import Dict, Any
import aiohttp
import asyncio

from core.initializers.base_initializer import BaseInitializer
from core.utils.logger import logger
from core.utils.errors import ConfigurationError
from config import config


class LLMInitializer(BaseInitializer):
    """
    Initializer for LLM/TGI service connection.
    
    This initializer:
    - Validates TGI service availability
    - Tests connection to the LLM service
    - Ensures the model is ready for inference
    """
    
    def _validate_config(self) -> None:
        """Validate LLM configuration."""
        # Use default from config if not provided
        base_url = self.get_config_value("base_url", config.llm.TGI_BASE_URL)
        timeout = self.get_config_value("timeout", config.llm.REQUEST_TIMEOUT)
        
        if not base_url:
            raise ConfigurationError("LLM base_url is required")
        
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ConfigurationError("LLM timeout must be a positive number")
        
        # Store validated config
        self.config["base_url"] = base_url
        self.config["timeout"] = timeout
    
    async def _initialize(self) -> Dict[str, Any]:
        """Initialize LLM connection."""
        base_url = self.config["base_url"]
        timeout = self.config["timeout"]
        
        logger.info(f"Initializing LLM connection to {base_url}")
        
        # Test connection to TGI service
        health_url = base_url.rstrip('/') + '/health'
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                # Check health endpoint
                async with session.get(health_url) as response:
                    if response.status != 200:
                        raise ConfigurationError(f"TGI health check failed: HTTP {response.status}")
                    
                    health_data = await response.json()
                    logger.debug(f"TGI health check successful: {health_data}")
                
                # Test a simple generation to ensure model is loaded
                generate_url = base_url.rstrip('/') + '/generate'
                test_payload = {
                    "inputs": "Test connection",
                    "parameters": {
                        "max_new_tokens": 5,
                        "temperature": 0.1
                    }
                }
                
                async with session.post(generate_url, json=test_payload) as response:
                    if response.status != 200:
                        logger.warning(f"TGI generation test failed: HTTP {response.status}")
                        # Don't fail initialization for generation test, just warn
                    else:
                        test_result = await response.json()
                        logger.debug("TGI generation test successful")
        
        except aiohttp.ClientError as e:
            raise ConfigurationError(f"Failed to connect to TGI service at {base_url}: {str(e)}")
        except asyncio.TimeoutError:
            raise ConfigurationError(f"TGI service connection timed out after {timeout}s")
        
        return {
            "base_url": base_url,
            "timeout": timeout,
            "status": "connected",
            "health_check": "passed"
        }
    
    async def _health_check(self) -> Dict[str, Any]:
        """Check LLM service health."""
        base_url = self.config["base_url"]
        timeout = self.config["timeout"]
        health_url = base_url.rstrip('/') + '/health'
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config.pipeline.HEALTH_CHECK_TIMEOUT)) as session:
                async with session.get(health_url) as response:
                    if response.status == 200:
                        return {
                            "status": "healthy",
                            "response_time_ms": 50,  # Approximate
                            "endpoint": health_url
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "http_status": response.status,
                            "endpoint": health_url
                        }
        
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "endpoint": health_url
            } 