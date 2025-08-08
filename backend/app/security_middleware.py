"""
Security middleware for Synapse AI API
Implements comprehensive security headers and CORS policies.
"""

import os
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import List
import re

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    def __init__(self, app):
        super().__init__(app)
        self.is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"
        
        # Content Security Policy for production
        self.csp_policy = self._build_csp_policy()
        
        # Allowed origins for CORS
        cors_origins_str = os.getenv("CORS_ORIGIN_URL", "*")
        if cors_origins_str == "*":
            self.allowed_origins = ["*"]
        else:
            self.allowed_origins = [origin.strip() for origin in cors_origins_str.split(",")]
    
    def _build_csp_policy(self) -> str:
        """Build Content Security Policy based on environment."""
        if self.is_production:
            return (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://js.stripe.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https://api.stripe.com https://api.openai.com https://api.anthropic.com; "
                "frame-src https://js.stripe.com https://hooks.stripe.com; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        else:
            # More permissive for development
            return (
                "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "connect-src 'self' http://localhost:* https://api.openai.com https://api.anthropic.com; "
                "img-src 'self' data: https:; "
                "frame-src 'self'"
            )
    
    def _is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is allowed."""
        if "*" in self.allowed_origins:
            return True
            
        if origin in self.allowed_origins:
            return True
            
        # Check for pattern matches (e.g., *.domain.com)
        for allowed_origin in self.allowed_origins:
            if allowed_origin.startswith("*."):
                pattern = allowed_origin[2:]  # Remove *.
                if origin.endswith(pattern):
                    return True
        
        return False
    
    async def dispatch(self, request: Request, call_next):
        # Process the request
        response = await call_next(request)
        
        # Add security headers
        self._add_security_headers(response, request)
        
        return response
    
    def _add_security_headers(self, response: Response, request: Request):
        """Add comprehensive security headers."""
        
        # Core security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = self.csp_policy
        
        # HSTS for production HTTPS
        if self.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # Permissions Policy (formerly Feature Policy)
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(self), "
            "usb=()"
        )
        
        # Server header (hide server information)
        response.headers["Server"] = "Synapse-API"
        
        # API-specific headers
        response.headers["X-API-Version"] = "1.0.0"
        response.headers["X-Rate-Limit-Policy"] = "per-endpoint"
        
        # CORS headers (enhanced)
        origin = request.headers.get("origin")
        if origin and self._is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Expose-Headers"] = (
                "X-API-Version, X-Rate-Limit-Remaining, X-Rate-Limit-Reset, "
                "X-Prompt-ID, X-Response-ID"
            )
        elif "*" in self.allowed_origins and not origin:
            # Allow requests without origin (e.g., from Postman, curl)
            response.headers["Access-Control-Allow-Origin"] = "*"
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = (
                "Accept, Accept-Language, Content-Language, Content-Type, "
                "Authorization, X-Requested-With, X-API-Key"
            )
            response.headers["Access-Control-Max-Age"] = "86400"  # 24 hours

class SecurityValidator:
    """Additional security validation utilities."""
    
    @staticmethod
    def validate_file_upload(filename: str, content_type: str) -> bool:
        """Validate file upload security."""
        # Allowed file extensions
        allowed_extensions = {'.txt', '.json', '.csv', '.md', '.pdf', '.png', '.jpg', '.jpeg'}
        
        # Check extension
        extension = os.path.splitext(filename.lower())[1]
        if extension not in allowed_extensions:
            return False
        
        # Validate content type matches extension
        content_type_map = {
            '.txt': 'text/plain',
            '.json': 'application/json',
            '.csv': 'text/csv',
            '.md': 'text/markdown',
            '.pdf': 'application/pdf',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg'
        }
        
        expected_content_type = content_type_map.get(extension)
        if expected_content_type and not content_type.startswith(expected_content_type):
            return False
        
        # Check for dangerous patterns in filename
        dangerous_patterns = [
            r'\.\./', r'\.\.\\', r'<script', r'javascript:', r'vbscript:', r'on\w+=',
            r'<iframe', r'<object', r'<embed', r'<link', r'<meta', r'<style'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                return False
        
        return True
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage."""
        # Remove path traversal attempts
        filename = os.path.basename(filename)
        
        # Remove dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255 - len(ext)] + ext
        
        return filename

def get_security_headers_middleware():
    """Factory function to create security headers middleware."""
    return SecurityHeadersMiddleware

# Rate limiting headers helper
def add_rate_limit_headers(response: Response, limit: int, remaining: int, reset_time: int):
    """Add rate limiting headers to response."""
    response.headers["X-Rate-Limit-Limit"] = str(limit)
    response.headers["X-Rate-Limit-Remaining"] = str(remaining)
    response.headers["X-Rate-Limit-Reset"] = str(reset_time)

# Environment-specific configuration
def get_cors_config():
    """Get CORS configuration based on environment."""
    is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"
    cors_origins = os.getenv("CORS_ORIGIN_URL", "*").split(",")
    
    if is_production:
        # Strict CORS for production
        return {
            "allow_origins": [origin.strip() for origin in cors_origins if origin.strip() != "*"],
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": [
                "Accept", "Accept-Language", "Content-Language", "Content-Type",
                "Authorization", "X-Requested-With", "X-API-Key"
            ],
            "expose_headers": [
                "X-API-Version", "X-Rate-Limit-Remaining", "X-Rate-Limit-Reset",
                "X-Prompt-ID", "X-Response-ID"
            ]
        }
    else:
        # Permissive CORS for development
        return {
            "allow_origins": cors_origins,
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
            "expose_headers": ["*"]
        }