"""
Flask wrapper for Ollama local inference integration.

This lightweight Flask application acts as a bridge between the main FastAPI
application and the local Ollama server, providing a clean API interface
for local model inference.
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional, Generator
from flask import Flask, request, jsonify, Response, stream_template_string
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class OllamaClient:
    """Client for interacting with local Ollama server."""
    
    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 300):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def health_check(self) -> Dict[str, Any]:
        """Check if Ollama server is running and accessible."""
        try:
            response = self.session.get(f"{self.base_url}/api/version", timeout=5)
            response.raise_for_status()
            return {
                "status": "healthy",
                "version": response.json(),
                "base_url": self.base_url
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "base_url": self.base_url
            }
    
    def list_models(self) -> Dict[str, Any]:
        """List available models on Ollama server."""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list models: {e}")
            raise Exception(f"Failed to list models: {e}")
    
    def generate_stream(self, model: str, prompt: str, **kwargs) -> Generator[str, None, None]:
        """Generate streaming response from Ollama model."""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            **kwargs
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                stream=True,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        if 'response' in data:
                            yield data['response']
                        
                        if data.get('done', False):
                            metadata = {
                                "done": True,
                                "total_duration": data.get('total_duration'),
                                "load_duration": data.get('load_duration'),
                                "prompt_eval_count": data.get('prompt_eval_count'),
                                "eval_count": data.get('eval_count'),
                                "eval_duration": data.get('eval_duration')
                            }
                            yield f"\n\n[METADATA]: {json.dumps(metadata)}"
                            break
                            
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSON response: {e}")
                        continue
                        
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama generation failed: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    def generate_complete(self, model: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate complete (non-streaming) response from Ollama model."""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            **kwargs
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama generation failed: {e}")
            raise Exception(f"Ollama generation failed: {e}")

ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
ollama_timeout = int(os.getenv("OLLAMA_TIMEOUT", "300"))
ollama_client = OllamaClient(ollama_base_url, ollama_timeout)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint for the wrapper and Ollama server."""
    wrapper_status = {
        "service": "ollama-wrapper",
        "status": "running",
        "timestamp": time.time()
    }
    
    ollama_status = ollama_client.health_check()
    
    return jsonify({
        "wrapper": wrapper_status,
        "ollama": ollama_status,
        "overall_status": "healthy" if ollama_status["status"] == "healthy" else "degraded"
    })

@app.route('/models', methods=['GET'])
def list_models():
    """List available models on Ollama server."""
    try:
        models = ollama_client.list_models()
        return jsonify({
            "status": "ok",
            "models": models.get("models", []),
            "count": len(models.get("models", []))
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/generate', methods=['POST'])
def generate():
    """
    Generate response from local Ollama model.
    
    Request body:
    {
        "model": "phi-3:mini-128k-instruct-q4_K_M",
        "prompt": "Your prompt here",
        "stream": true/false,
        "temperature": 0.7,
        "max_tokens": 2048,
        "top_p": 0.9,
        "top_k": 40
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        model = data.get("model")
        prompt = data.get("prompt")
        stream = data.get("stream", True)
        
        if not model or not prompt:
            return jsonify({"error": "Model and prompt are required"}), 400
        
        generation_params = {}
        param_mapping = {
            "temperature": "temperature",
            "max_tokens": "num_predict",
            "top_p": "top_p",
            "top_k": "top_k",
            "repeat_penalty": "repeat_penalty",
            "seed": "seed"
        }
        
        for param, ollama_param in param_mapping.items():
            if param in data:
                generation_params[ollama_param] = data[param]
        
        if stream:
            def generate_stream():
                yield "data: " + json.dumps({"status": "started", "model": model}) + "\n\n"
                
                try:
                    for chunk in ollama_client.generate_stream(model, prompt, **generation_params):
                        if chunk.startswith("[METADATA]:"):
                            metadata = json.loads(chunk.replace("[METADATA]: ", ""))
                            yield "data: " + json.dumps(metadata) + "\n\n"
                        else:
                            yield "data: " + json.dumps({"response": chunk}) + "\n\n"
                
                except Exception as e:
                    yield "data: " + json.dumps({"error": str(e)}) + "\n\n"
                
                yield "data: [DONE]\n\n"
            
            return Response(
                generate_stream(),
                mimetype='text/plain',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'X-Accel-Buffering': 'no'
                }
            )
        
        else:
            result = ollama_client.generate_complete(model, prompt, **generation_params)
            return jsonify({
                "status": "completed",
                "model": model,
                "response": result.get("response", ""),
                "metadata": {
                    "total_duration": result.get("total_duration"),
                    "load_duration": result.get("load_duration"),
                    "prompt_eval_count": result.get("prompt_eval_count"),
                    "eval_count": result.get("eval_count"),
                    "eval_duration": result.get("eval_duration")
                }
            })
    
    except Exception as e:
        logger.error(f"Generation error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    """
    Chat endpoint for conversational interactions.
    
    Request body:
    {
        "model": "phi-3:mini-128k-instruct-q4_K_M",
        "messages": [
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ],
        "stream": true/false
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        model = data.get("model")
        messages = data.get("messages", [])
        stream = data.get("stream", True)
        
        if not model or not messages:
            return jsonify({"error": "Model and messages are required"}), 400
        
        prompt_parts = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
            elif role == "system":
                prompt_parts.append(f"System: {content}")
        
        prompt_parts.append("Assistant:")
        prompt = "\n".join(prompt_parts)
        
        generation_params = {k: v for k, v in data.items() 
                           if k not in ["model", "messages", "stream"]}
        
        if stream:
            def chat_stream():
                yield "data: " + json.dumps({"status": "started", "model": model}) + "\n\n"
                
                try:
                    for chunk in ollama_client.generate_stream(model, prompt, **generation_params):
                        if chunk.startswith("[METADATA]:"):
                            metadata = json.loads(chunk.replace("[METADATA]: ", ""))
                            yield "data: " + json.dumps(metadata) + "\n\n"
                        else:
                            yield "data: " + json.dumps({"delta": {"content": chunk}}) + "\n\n"
                
                except Exception as e:
                    yield "data: " + json.dumps({"error": str(e)}) + "\n\n"
                
                yield "data: [DONE]\n\n"
            
            return Response(
                chat_stream(),
                mimetype='text/plain',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive'
                }
            )
        
        else:
            result = ollama_client.generate_complete(model, prompt, **generation_params)
            return jsonify({
                "status": "completed",
                "model": model,
                "message": {
                    "role": "assistant",
                    "content": result.get("response", "")
                },
                "metadata": {
                    "total_duration": result.get("total_duration"),
                    "load_duration": result.get("load_duration"),
                    "prompt_eval_count": result.get("prompt_eval_count"),
                    "eval_count": result.get("eval_count"),
                    "eval_duration": result.get("eval_duration")
                }
            })
    
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    host = os.getenv("WRAPPER_HOST", "127.0.0.1")
    port = int(os.getenv("WRAPPER_PORT", "5001"))
    debug = os.getenv("WRAPPER_DEBUG", "false").lower() == "true"
    
    logger.info(f"Starting Ollama wrapper on {host}:{port}")
    logger.info(f"Ollama server: {ollama_base_url}")
    
    health_status = ollama_client.health_check()
    if health_status["status"] == "healthy":
        logger.info("✅ Ollama server is accessible")
    else:
        logger.warning(f"⚠️  Ollama server not accessible: {health_status['error']}")
    
    app.run(host=host, port=port, debug=debug, threaded=True)
