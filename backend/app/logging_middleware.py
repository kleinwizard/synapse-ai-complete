"""
Logging middleware for FastAPI to capture comprehensive request/response data.

This middleware logs all incoming requests and outgoing responses to help
debug issues throughout the application.
"""

import time
import json
import uuid
from typing import Callable, Dict, Any
from fastapi import Request, Response
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from .logging_config import get_logger, request_context, security_logger

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses."""
    
    def __init__(self, app, logger_name: str = "http"):
        super().__init__(app)
        self.logger = get_logger(logger_name)
        
        # Sensitive headers that should not be logged
        self.sensitive_headers = {
            'authorization', 'cookie', 'x-api-key', 'x-auth-token',
            'stripe-signature', 'x-webhook-secret'
        }
        
        # Endpoints that should have minimal body logging (for performance/security)
        self.minimal_body_endpoints = {
            '/webhooks/stripe', '/auth/login', '/auth/register',
            '/users/password', '/auth/reset-password'
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Get user info from request if available
        user_email = "unknown"
        user_id = "anonymous"
        
        # Try to extract user info from Authorization header
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                # This is a simplified extraction - in production you'd decode the JWT
                user_email = self._extract_user_from_token(auth_header[7:])
            except Exception:
                pass
        
        # Set request context for logging
        with request_context(
            request_id=request_id,
            user_id=user_id,
            user_email=user_email,
            endpoint=str(request.url.path),
            method=request.method,
            ip_address=client_ip
        ):
            # Log incoming request
            await self._log_request(request, request_id, client_ip, user_email)
            
            try:
                # Process request
                response = await call_next(request)
                
                # Calculate processing time
                process_time = time.time() - start_time
                
                # Log outgoing response
                await self._log_response(request, response, request_id, process_time)
                
                # Add headers for tracing
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Process-Time"] = str(process_time)
                
                return response
                
            except Exception as e:
                # Log error
                process_time = time.time() - start_time
                self.logger.error(f"Request processing failed: {str(e)}", extra={
                    "request_id": request_id,
                    "endpoint": str(request.url.path),
                    "method": request.method,
                    "error": str(e),
                    "process_time_seconds": process_time,
                    "client_ip": client_ip,
                    "user_email": user_email,
                    "event_type": "request_error"
                })
                
                # Log security event if this looks suspicious
                if self._is_suspicious_error(e, request):
                    security_logger.log_suspicious_activity(
                        activity_type="request_processing_error",
                        details={
                            "endpoint": str(request.url.path),
                            "method": request.method,
                            "error": str(e),
                            "user_agent": request.headers.get("user-agent", ""),
                            "query_params": dict(request.query_params)
                        },
                        user_email=user_email
                    )
                
                raise
    
    async def _log_request(self, request: Request, request_id: str, client_ip: str, user_email: str):
        """Log incoming request details."""
        
        # Get request body if applicable
        body_data = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    # Try to parse as JSON
                    try:
                        body_data = json.loads(body.decode())
                        # Remove sensitive data from logs
                        body_data = self._sanitize_body_data(body_data, str(request.url.path))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        # If not JSON, log as string (truncated)
                        body_str = body.decode('utf-8', errors='ignore')
                        body_data = body_str[:500] + "..." if len(body_str) > 500 else body_str
            except Exception as e:
                self.logger.warning(f"Could not read request body: {e}")
        
        # Get headers (excluding sensitive ones)
        headers = {
            k.lower(): v for k, v in request.headers.items()
            if k.lower() not in self.sensitive_headers
        }
        
        # Log the request
        self.logger.info(f"Incoming request: {request.method} {request.url.path}", extra={
            "event_type": "incoming_request",
            "request_id": request_id,
            "method": request.method,
            "endpoint": str(request.url.path),
            "query_params": dict(request.query_params),
            "headers": headers,
            "body_data": body_data,
            "client_ip": client_ip,
            "user_agent": request.headers.get("user-agent", ""),
            "user_email": user_email,
            "content_type": request.headers.get("content-type", ""),
            "content_length": request.headers.get("content-length", 0)
        })
        
        # Log rate limiting info
        if hasattr(request.state, 'rate_limit_remaining'):
            self.logger.debug("Rate limit status", extra={
                "event_type": "rate_limit_status",
                "remaining_requests": request.state.rate_limit_remaining,
                "reset_time": getattr(request.state, 'rate_limit_reset', None)
            })
    
    async def _log_response(self, request: Request, response: Response, request_id: str, process_time: float):
        """Log outgoing response details."""
        
        # Get response headers (excluding sensitive ones)
        response_headers = {
            k.lower(): v for k, v in response.headers.items()
            if k.lower() not in self.sensitive_headers
        }
        
        # Try to get response body for non-streaming responses
        response_body = None
        if not isinstance(response, StreamingResponse):
            try:
                if hasattr(response, 'body') and response.body:
                    body_str = response.body.decode('utf-8', errors='ignore')
                    try:
                        response_body = json.loads(body_str)
                        # Sanitize response body
                        response_body = self._sanitize_response_data(response_body, str(request.url.path))
                    except json.JSONDecodeError:
                        # If not JSON, truncate for logging
                        response_body = body_str[:1000] + "..." if len(body_str) > 1000 else body_str
            except Exception as e:
                self.logger.debug(f"Could not read response body: {e}")
        
        # Determine log level based on status code
        if response.status_code >= 500:
            log_level = self.logger.error
        elif response.status_code >= 400:
            log_level = self.logger.warning
        else:
            log_level = self.logger.info
        
        # Log the response
        log_level(f"Outgoing response: {response.status_code} for {request.method} {request.url.path}", extra={
            "event_type": "outgoing_response",
            "request_id": request_id,
            "method": request.method,
            "endpoint": str(request.url.path),
            "status_code": response.status_code,
            "headers": response_headers,
            "response_body": response_body,
            "process_time_seconds": process_time,
            "is_streaming": isinstance(response, StreamingResponse),
            "content_type": response.headers.get("content-type", ""),
            "content_length": response.headers.get("content-length", 0)
        })
        
        # Log slow requests
        if process_time > 5.0:  # More than 5 seconds
            self.logger.warning(f"Slow request detected: {process_time:.2f}s", extra={
                "event_type": "slow_request",
                "process_time_seconds": process_time,
                "endpoint": str(request.url.path),
                "method": request.method,
                "status_code": response.status_code
            })
        
        # Log errors in detail
        if response.status_code >= 400:
            error_details = {
                "status_code": response.status_code,
                "endpoint": str(request.url.path),
                "method": request.method,
                "query_params": dict(request.query_params),
                "user_agent": request.headers.get("user-agent", ""),
                "response_body": response_body
            }
            
            if response.status_code >= 500:
                self.logger.error("Server error occurred", extra={
                    "event_type": "server_error",
                    **error_details
                })
            else:
                self.logger.warning("Client error occurred", extra={
                    "event_type": "client_error",
                    **error_details
                })
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers first (for reverse proxy setups)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        if hasattr(request.client, 'host'):
            return request.client.host
        
        return "unknown"
    
    def _extract_user_from_token(self, token: str) -> str:
        """Extract user email from JWT token (simplified version)."""
        try:
            # In a real implementation, you'd decode the JWT properly
            # This is a simplified version for demonstration
            import jwt
            from app.auth import get_jwt_secret
            
            payload = jwt.decode(token, get_jwt_secret(), algorithms=["HS256"])
            user_id = payload.get("sub")
            
            # You'd typically look up the user by ID here
            return f"user_{user_id}"
            
        except Exception:
            return "unknown"
    
    def _sanitize_body_data(self, body_data: Any, endpoint: str) -> Any:
        """Remove sensitive data from request body for logging."""
        if not isinstance(body_data, dict):
            return body_data
        
        # Copy the data to avoid modifying original
        sanitized = body_data.copy()
        
        # Remove sensitive fields
        sensitive_fields = {
            'password', 'old_password', 'new_password', 'current_password',
            'api_key', 'secret', 'token', 'authorization'
        }
        
        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = "[REDACTED]"
        
        # For certain endpoints, limit the content size
        if endpoint in self.minimal_body_endpoints:
            # Only keep essential fields for these endpoints
            if 'email' in sanitized:
                sanitized = {'email': sanitized['email'], '[OTHER_FIELDS]': '[REDACTED]'}
        
        # Truncate long prompts
        if 'prompt' in sanitized and isinstance(sanitized['prompt'], str):
            if len(sanitized['prompt']) > 1000:
                sanitized['prompt'] = sanitized['prompt'][:1000] + "... [TRUNCATED]"
        
        return sanitized
    
    def _sanitize_response_data(self, response_data: Any, endpoint: str) -> Any:
        """Remove sensitive data from response body for logging."""
        if not isinstance(response_data, dict):
            return response_data
        
        sanitized = response_data.copy()
        
        # Remove sensitive fields from responses
        sensitive_response_fields = {
            'access_token', 'refresh_token', 'api_key', 'secret'
        }
        
        for field in sensitive_response_fields:
            if field in sanitized:
                sanitized[field] = "[REDACTED]"
        
        # Truncate long responses
        if 'final_output' in sanitized and isinstance(sanitized['final_output'], str):
            if len(sanitized['final_output']) > 2000:
                sanitized['final_output'] = sanitized['final_output'][:2000] + "... [TRUNCATED]"
        
        if 'synapse_prompt' in sanitized and isinstance(sanitized['synapse_prompt'], str):
            if len(sanitized['synapse_prompt']) > 1000:
                sanitized['synapse_prompt'] = sanitized['synapse_prompt'][:1000] + "... [TRUNCATED]"
        
        return sanitized
    
    def _is_suspicious_error(self, error: Exception, request: Request) -> bool:
        """Determine if an error indicates suspicious activity."""
        error_str = str(error).lower()
        
        # Check for common attack patterns
        suspicious_patterns = [
            'sql injection', 'xss', 'script', 'malicious',
            'unauthorized', 'forbidden', 'invalid token',
            'rate limit', 'too many requests'
        ]
        
        for pattern in suspicious_patterns:
            if pattern in error_str:
                return True
        
        # Check for unusual request patterns
        user_agent = request.headers.get("user-agent", "").lower()
        if any(bot in user_agent for bot in ['bot', 'crawler', 'spider', 'scraper']):
            return True
        
        return False

class StreamingResponseLogger:
    """Logger for streaming responses to capture the final output."""
    
    def __init__(self, original_response: StreamingResponse, request_id: str, endpoint: str):
        self.original_response = original_response
        self.request_id = request_id
        self.endpoint = endpoint
        self.logger = get_logger('streaming')
        self.collected_content = []
    
    async def __call__(self, scope, receive, send):
        """ASGI callable to intercept streaming response."""
        
        async def send_wrapper(message):
            if message['type'] == 'http.response.body':
                body = message.get('body', b'')
                if body:
                    try:
                        content = body.decode('utf-8', errors='ignore')
                        self.collected_content.append(content)
                        
                        # Log chunk (truncated for performance)
                        if len(content) > 100:
                            content_preview = content[:100] + "..."
                        else:
                            content_preview = content
                        
                        self.logger.debug(f"Streaming chunk for {self.endpoint}", extra={
                            "event_type": "streaming_chunk",
                            "request_id": self.request_id,
                            "endpoint": self.endpoint,
                            "chunk_size": len(body),
                            "chunk_preview": content_preview
                        })
                        
                    except Exception as e:
                        self.logger.warning(f"Could not decode streaming chunk: {e}")
                
                # If this is the last chunk, log the complete response
                if not message.get('more_body', False):
                    full_content = ''.join(self.collected_content)
                    if full_content:
                        # Truncate for logging
                        if len(full_content) > 2000:
                            logged_content = full_content[:2000] + "... [TRUNCATED]"
                        else:
                            logged_content = full_content
                        
                        self.logger.info(f"Streaming response completed for {self.endpoint}", extra={
                            "event_type": "streaming_complete",
                            "request_id": self.request_id,
                            "endpoint": self.endpoint,
                            "total_length": len(full_content),
                            "content": logged_content
                        })
            
            await send(message)
        
        await self.original_response(scope, receive, send_wrapper)