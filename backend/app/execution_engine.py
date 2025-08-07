"""
Execution Engine Module

This module provides the core execution logic for the Synapse AI application,
connecting to OpenAI, Anthropic, and Ollama APIs with streaming responses and caching.
"""

import asyncio
import hashlib
import json
import logging
import os
from typing import Dict, Any, AsyncGenerator, Optional, Union
from functools import lru_cache
import httpx
import openai
import anthropic
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

response_cache: Dict[str, str] = {}

openai_client: Optional[openai.AsyncOpenAI] = None
anthropic_client: Optional[anthropic.AsyncAnthropic] = None

OLLAMA_BASE_URL = "http://localhost:11434"


class ExecutionEngine:
    """
    Core execution engine for handling LLM API calls with streaming responses and caching.
    
    This class manages connections to OpenAI, Anthropic, and Ollama APIs,
    providing unified interface for model execution with real-time streaming.
    """
    
    def __init__(self):
        """Initialize the execution engine with API clients."""
        self.openai_client = None
        self.anthropic_client = None
        self.ollama_client = httpx.AsyncClient(base_url=OLLAMA_BASE_URL)
        
        self.local_mode_enabled = os.getenv("ENABLE_LOCAL_MODE", "false").lower() == "true"
        self.ollama_wrapper_url = os.getenv("OLLAMA_WRAPPER_URL", "http://localhost:5001")
        self.ollama_default_model = os.getenv("OLLAMA_DEFAULT_MODEL", "phi-3:mini-128k-instruct-q4_K_M")
        
    async def initialize_clients(self, openai_api_key: Optional[str] = None, 
                               anthropic_api_key: Optional[str] = None):
        """
        Initialize API clients with provided credentials.
        
        Args:
            openai_api_key: OpenAI API key
            anthropic_api_key: Anthropic API key
        """
        if openai_api_key:
            self.openai_client = openai.AsyncOpenAI(api_key=openai_api_key)
            logger.info("OpenAI client initialized")
        
        if anthropic_api_key:
            self.anthropic_client = anthropic.AsyncAnthropic(api_key=anthropic_api_key)
            logger.info("Anthropic client initialized")
    
    def _generate_cache_key(self, model: str, prompt: str, parameters: Dict[str, Any]) -> str:
        """
        Generate a unique cache key for the request.
        
        Args:
            model: Model identifier
            prompt: Input prompt
            parameters: Additional parameters
            
        Returns:
            str: Unique cache key
        """
        cache_data = {
            "model": model,
            "prompt": prompt,
            "parameters": parameters
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_string.encode()).hexdigest()
    
    def _get_cached_response(self, cache_key: str) -> Optional[str]:
        """
        Retrieve cached response if available.
        
        Args:
            cache_key: Cache key to lookup
            
        Returns:
            Optional[str]: Cached response or None
        """
        return response_cache.get(cache_key)
    
    def _cache_response(self, cache_key: str, response: str):
        """
        Cache the complete response.
        
        Args:
            cache_key: Cache key
            response: Complete response to cache
        """
        response_cache[cache_key] = response
        logger.info(f"Cached response for key: {cache_key[:16]}...")
    
    def _determine_api_provider(self, model: str) -> str:
        """
        Determine which API provider to use based on model identifier.
        
        Args:
            model: Model identifier from LLM router
            
        Returns:
            str: API provider ('openai', 'anthropic', or 'ollama')
        """
        model_lower = model.lower()
        
        if any(provider in model_lower for provider in ['gpt', 'openai']):
            return 'openai'
        elif any(provider in model_lower for provider in ['claude', 'anthropic']):
            return 'anthropic'
        elif any(provider in model_lower for provider in ['gemini', 'google']):
            return 'ollama'
        else:
            return 'ollama'
    
    async def _stream_openai_response(self, model: str, prompt: str, 
                                    parameters: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        Stream response from OpenAI API.
        
        Args:
            model: OpenAI model identifier
            prompt: Input prompt
            parameters: Additional parameters
            
        Yields:
            str: Response chunks
        """
        if not self.openai_client:
            raise HTTPException(status_code=500, detail="OpenAI client not initialized")
        
        try:
            messages = [{"role": "user", "content": prompt}]
            
            stream = await self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                max_tokens=parameters.get("max_tokens", 2000),
                temperature=parameters.get("temperature", 0.7)
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
    
    async def _stream_anthropic_response(self, model: str, prompt: str, 
                                       parameters: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        Stream response from Anthropic API.
        
        Args:
            model: Anthropic model identifier
            prompt: Input prompt
            parameters: Additional parameters
            
        Yields:
            str: Response chunks
        """
        if not self.anthropic_client:
            raise HTTPException(status_code=500, detail="Anthropic client not initialized")
        
        try:
            async with self.anthropic_client.messages.stream(
                model=model,
                max_tokens=parameters.get("max_tokens", 2000),
                temperature=parameters.get("temperature", 0.7),
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                async for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Anthropic API error: {str(e)}")
    
    async def _stream_ollama_response(self, model: str, prompt: str, 
                                    parameters: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        Stream response from Ollama API.
        
        Args:
            model: Ollama model identifier
            prompt: Input prompt
            parameters: Additional parameters
            
        Yields:
            str: Response chunks
        """
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": parameters.get("temperature", 0.7),
                    "num_predict": parameters.get("max_tokens", 2000)
                }
            }
            
            async with self.ollama_client.stream(
                "POST", "/api/generate", json=payload
            ) as response:
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code, 
                        detail=f"Ollama API error: {response.text}"
                    )
                
                async for line in response.aiter_lines():
                    if line:
                        try:
                            chunk_data = json.loads(line)
                            if "response" in chunk_data:
                                yield chunk_data["response"]
                        except json.JSONDecodeError:
                            continue
                            
        except httpx.RequestError as e:
            logger.error(f"Ollama connection error: {str(e)}")
            raise HTTPException(status_code=503, detail=f"Ollama service unavailable: {str(e)}")
        except Exception as e:
            logger.error(f"Ollama API error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Ollama API error: {str(e)}")
    
    async def execute_with_streaming(self, model: str, prompt: str, 
                                   parameters: Optional[Dict[str, Any]] = None) -> StreamingResponse:
        """
        Execute LLM request with streaming response and caching.
        
        Args:
            model: Model identifier from LLM router
            prompt: Input prompt
            parameters: Additional execution parameters
            
        Returns:
            StreamingResponse: Streaming response object
        """
        if parameters is None:
            parameters = {}
        
        if self.local_mode_enabled:
            return await self._execute_local_mode_streaming(model, prompt, parameters)
        
        cache_key = self._generate_cache_key(model, prompt, parameters)
        
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            logger.info(f"Returning cached response for key: {cache_key[:16]}...")
            
            async def cached_stream():
                chunk_size = 50
                for i in range(0, len(cached_response), chunk_size):
                    chunk = cached_response[i:i + chunk_size]
                    yield f"data: {json.dumps({'content': chunk, 'cached': True})}\n\n"
                    await asyncio.sleep(0.05)  # Small delay to simulate streaming
                yield f"data: {json.dumps({'done': True, 'cached': True})}\n\n"
            
            return StreamingResponse(
                cached_stream(),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
            )
        
        provider = self._determine_api_provider(model)
        logger.info(f"Routing model '{model}' to provider: {provider}")
        
        async def stream_generator():
            complete_response = ""
            
            try:
                if provider == 'openai':
                    stream = self._stream_openai_response(model, prompt, parameters)
                elif provider == 'anthropic':
                    stream = self._stream_anthropic_response(model, prompt, parameters)
                elif provider == 'ollama':
                    stream = self._stream_ollama_response(model, prompt, parameters)
                else:
                    raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
                
                async for chunk in stream:
                    complete_response += chunk
                    yield f"data: {json.dumps({'content': chunk, 'provider': provider})}\n\n"
                
                self._cache_response(cache_key, complete_response)
                
                yield f"data: {json.dumps({'done': True, 'provider': provider, 'total_length': len(complete_response)})}\n\n"
                
            except Exception as e:
                logger.error(f"Streaming error: {str(e)}")
                yield f"data: {json.dumps({'error': str(e), 'provider': provider})}\n\n"
        
        return StreamingResponse(
            stream_generator(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict[str, Any]: Cache statistics
        """
        total_size = sum(len(response) for response in response_cache.values())
        
        return {
            "cache_entries": len(response_cache),
            "total_cache_size_bytes": total_size,
            "total_cache_size_mb": round(total_size / (1024 * 1024), 2),
            "cache_keys": list(response_cache.keys())[:10]  # First 10 keys for debugging
        }
    
    def clear_cache(self):
        """Clear the response cache."""
        global response_cache
        cache_size = len(response_cache)
        response_cache.clear()
        logger.info(f"Cleared cache with {cache_size} entries")
    
    async def _execute_local_mode_streaming(self, model: str, prompt: str, 
                                          parameters: Optional[Dict[str, Any]] = None) -> StreamingResponse:
        """
        Execute prompt using local Ollama through Flask wrapper.
        
        Args:
            model: The model identifier
            prompt: The input prompt
            parameters: Optional parameters for the model
            
        Returns:
            StreamingResponse: Async streaming response from local model
        """
        if parameters is None:
            parameters = {}
        
        try:
            local_model = self.ollama_default_model
            if model and not (model.startswith("gpt-") or model.startswith("claude-")):
                local_model = model
            
            payload = {
                "model": local_model,
                "prompt": prompt,
                "stream": True
            }
            
            # Add generation parameters
            param_mapping = {
                "temperature": "temperature",
                "max_tokens": "max_tokens",
                "top_p": "top_p",
                "top_k": "top_k"
            }
            
            for param, wrapper_param in param_mapping.items():
                if param in parameters:
                    payload[wrapper_param] = parameters[param]
            
            logger.info(f"Local mode: routing to {local_model} via {self.ollama_wrapper_url}")
            
            async def local_stream():
                try:
                    yield f"data: {json.dumps({'status': 'started', 'model': local_model, 'mode': 'local'})}\n\n"
                    
                    async with httpx.AsyncClient(timeout=300.0) as client:
                        async with client.stream(
                            "POST",
                            f"{self.ollama_wrapper_url}/generate",
                            json=payload,
                            headers={"Content-Type": "application/json"}
                        ) as response:
                            if response.status_code != 200:
                                error_text = await response.aread()
                                yield f"data: {json.dumps({'error': f'Wrapper error: {response.status_code} - {error_text.decode()}'})}\n\n"
                                return
                            
                            async for line in response.aiter_lines():
                                if line.startswith("data: "):
                                    data_part = line[6:]  # Remove "data: " prefix
                                    
                                    if data_part == "[DONE]":
                                        yield "data: [DONE]\n\n"
                                        break
                                    
                                    try:
                                        data = json.loads(data_part)
                                        
                                        if "response" in data:
                                            yield f"data: {json.dumps({'content': data['response'], 'provider': 'local'})}\n\n"
                                        elif "error" in data:
                                            yield f"data: {json.dumps({'error': data['error'], 'provider': 'local'})}\n\n"
                                        elif data.get("done", False):
                                            yield f"data: {json.dumps({'done': True, 'provider': 'local', 'metadata': data})}\n\n"
                                            break
                                        else:
                                            yield f"data: {json.dumps(data)}\n\n"
                                            
                                    except json.JSONDecodeError:
                                        yield f"data: {json.dumps({'content': data_part, 'provider': 'local'})}\n\n"
                
                except httpx.RequestError as e:
                    yield f"data: {json.dumps({'error': f'Local mode connection failed: {str(e)}. Make sure Ollama wrapper is running on {self.ollama_wrapper_url}', 'provider': 'local'})}\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'error': f'Local mode execution failed: {str(e)}', 'provider': 'local'})}\n\n"
            
            return StreamingResponse(
                local_stream(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Execution-Mode": "local"
                }
            )
            
        except Exception as setup_error:
            error_msg = f"Local mode setup failed: {str(setup_error)}"
            async def error_stream():
                yield f"data: {json.dumps({'error': error_msg, 'provider': 'local'})}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                error_stream(),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache"}
            )
    
    def is_local_mode_enabled(self) -> bool:
        """Check if local mode is currently enabled."""
        return self.local_mode_enabled
    
    def get_local_mode_info(self) -> Dict[str, Any]:
        """Get information about local mode configuration."""
        return {
            "enabled": self.local_mode_enabled,
            "wrapper_url": self.ollama_wrapper_url,
            "ollama_url": OLLAMA_BASE_URL,
            "default_model": self.ollama_default_model
        }


execution_engine = ExecutionEngine()


async def initialize_execution_engine(openai_api_key: Optional[str] = None,
                                    anthropic_api_key: Optional[str] = None):
    """
    Initialize the global execution engine with API credentials.
    
    Args:
        openai_api_key: OpenAI API key
        anthropic_api_key: Anthropic API key
    """
    await execution_engine.initialize_clients(openai_api_key, anthropic_api_key)


def get_execution_engine() -> ExecutionEngine:
    """
    Get the global execution engine instance.
    
    Returns:
        ExecutionEngine: The global execution engine
    """
    return execution_engine
