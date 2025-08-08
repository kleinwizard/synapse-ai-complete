"""
Input validation and sanitization utilities for Synapse AI
Provides comprehensive validation for user inputs, API parameters, and data integrity.
"""

import re
import html
import unicodedata
from typing import Any, Dict, List, Optional, Union
from fastapi import HTTPException, status
from pydantic import BaseModel, validator
import bleach

class InputValidator:
    """Centralized input validation and sanitization."""
    
    # Security patterns to detect potentially malicious content
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',  # JavaScript URLs
        r'on\w+\s*=',  # Event handlers
        r'<iframe[^>]*>.*?</iframe>',  # Iframe tags
        r'<object[^>]*>.*?</object>',  # Object tags
        r'<embed[^>]*>',  # Embed tags
        r'<link[^>]*>',  # Link tags (can be malicious)
        r'<meta[^>]*>',  # Meta tags
        r'<style[^>]*>.*?</style>',  # Style tags
        r'data:text/html',  # Data URLs
        r'vbscript:',  # VBScript URLs
        r'expression\(',  # CSS expressions
    ]
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r'(?i)\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b',
        r'(?i)(\bor\b|\band\b)\s+\w*\s*=\s*\w*',
        r'[\'";].*(\bor\b|\band\b).*[\'";]',
        r'(?i)\b(script|alert|confirm|prompt)\s*\(',
    ]
    
    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r'[;&|`$\(\){}]',  # Shell metacharacters
        r'(?i)(curl|wget|nc|netcat|telnet|ssh|ftp)',  # Network tools
        r'(?i)(rm|del|format|fdisk)',  # Destructive commands
        r'(?i)(cat|type|more|less).*(/etc/|c:\\)',  # File access
    ]
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Remove HTML tags and dangerous content."""
        if not text:
            return text
            
        # Use bleach to clean HTML
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li']
        allowed_attributes = {}
        
        cleaned = bleach.clean(text, tags=allowed_tags, attributes=allowed_attributes)
        return html.escape(cleaned)
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 10000) -> str:
        """Sanitize plain text input."""
        if not text:
            return text
            
        # Normalize unicode characters
        text = unicodedata.normalize('NFKC', text)
        
        # Remove control characters except common ones
        text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C' or char in '\n\r\t')
        
        # Limit length
        if len(text) > max_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Input too long. Maximum {max_length} characters allowed."
            )
        
        # HTML escape to prevent XSS
        text = html.escape(text)
        
        return text.strip()
    
    @classmethod
    def detect_malicious_content(cls, text: str) -> List[str]:
        """Detect potentially malicious content in text."""
        if not text:
            return []
            
        threats = []
        text_lower = text.lower()
        
        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
                threats.append(f"Dangerous pattern detected: {pattern}")
        
        # Check for SQL injection
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                threats.append(f"Potential SQL injection: {pattern}")
        
        # Check for command injection
        for pattern in cls.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                threats.append(f"Potential command injection: {pattern}")
        
        return threats
    
    @classmethod
    def validate_prompt_content(cls, prompt: str) -> str:
        """Validate and sanitize prompt content for LLM processing."""
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prompt content cannot be empty"
            )
        
        # Check for malicious content
        threats = cls.detect_malicious_content(prompt)
        if threats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Potentially malicious content detected: {threats[0]}"
            )
        
        # Sanitize the prompt
        sanitized = cls.sanitize_text(prompt, max_length=50000)  # Larger limit for prompts
        
        # Additional validation for prompts
        if len(sanitized.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prompt too short. Minimum 10 characters required."
            )
        
        return sanitized
    
    @classmethod
    def validate_email(cls, email: str) -> str:
        """Validate and sanitize email address."""
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address is required"
            )
        
        email = email.strip().lower()
        
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email address format"
            )
        
        # Check for malicious content
        threats = cls.detect_malicious_content(email)
        if threats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email address"
            )
        
        return email
    
    @classmethod
    def validate_username(cls, username: str) -> str:
        """Validate and sanitize username."""
        if not username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username is required"
            )
        
        username = username.strip()
        
        # Username validation
        if len(username) < 3 or len(username) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username must be between 3 and 50 characters"
            )
        
        # Only allow alphanumeric, underscore, dash
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username can only contain letters, numbers, underscore, and dash"
            )
        
        return username
    
    @classmethod
    def validate_name(cls, name: str) -> str:
        """Validate and sanitize name fields."""
        if not name:
            return name
        
        name = cls.sanitize_text(name, max_length=100)
        
        # Name validation
        if len(name.strip()) < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Name cannot be empty"
            )
        
        # Only allow letters, spaces, apostrophes, hyphens
        if not re.match(r"^[a-zA-Z\s\-']+$", name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Name can only contain letters, spaces, apostrophes, and hyphens"
            )
        
        return name.strip()
    
    @classmethod
    def validate_password(cls, password: str) -> str:
        """Validate password strength."""
        if not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is required"
            )
        
        if len(password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long"
            )
        
        if len(password) > 128:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password too long. Maximum 128 characters allowed"
            )
        
        # Check for at least one letter and one number
        if not re.search(r'[a-zA-Z]', password) or not re.search(r'\d', password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one letter and one number"
            )
        
        return password
    
    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize dictionary values."""
        if not isinstance(data, dict):
            return data
        
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = cls.sanitize_text(value)
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [cls.sanitize_text(item) if isinstance(item, str) else item for item in value]
            else:
                sanitized[key] = value
        
        return sanitized

# Create global validator instance
validator = InputValidator()

# Pydantic validators for model validation
def validate_email_field(v):
    """Pydantic validator for email fields."""
    return validator.validate_email(v) if v else v

def validate_username_field(v):
    """Pydantic validator for username fields."""
    return validator.validate_username(v) if v else v

def validate_name_field(v):
    """Pydantic validator for name fields."""
    return validator.validate_name(v) if v else v

def validate_password_field(v):
    """Pydantic validator for password fields."""
    return validator.validate_password(v) if v else v

def validate_prompt_field(v):
    """Pydantic validator for prompt content."""
    return validator.validate_prompt_content(v) if v else v