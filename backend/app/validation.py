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

from .logging_config import get_logger, security_logger

class InputValidator:
    """
    Centralized input validation and sanitization.
    
    Updated to reduce false positives on legitimate AI research prompts while
    maintaining protection against actual security threats.
    """
    
    def __init__(self):
        self.logger = get_logger('validation')
    
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
    
    # SQL injection patterns - Made more specific to avoid false positives on legitimate AI prompts
    SQL_INJECTION_PATTERNS = [
        # Only flag SQL keywords when they appear in suspicious contexts
        r'(?i)\b(union\s+select|select\s+\*\s+from|drop\s+table|truncate\s+table)\b',
        r'(?i)\b(exec\s*\(|execute\s*\(|sp_executesql)\b',
        # SQL injection specific patterns with quotes and operators
        r'[\'"]\s*(union|select|insert|update|delete|drop)\s+.*[\'"]\s*(;|\-\-)',
        r'[\'"]\s*;\s*(drop|delete|update|insert)\s+.*[\'"]\s*',
        # Classic SQL injection patterns
        r'[\'"]\s*or\s+[\'"]\w*[\'"]\s*=\s*[\'"]\w*[\'"]\s*',
        r'[\'"]\s*and\s+[\'"]\w*[\'"]\s*=\s*[\'"]\w*[\'"]\s*',
        r'[\'"]\s*(or|and)\s+1\s*=\s*1\s*[\'"]*',
        r'[\'"]\s*(or|and)\s+[\'"]*\d+[\'"]*\s*=\s*[\'"]*\d+[\'"]*',
    ]
    
    # Command injection patterns - Made more specific to avoid false positives
    COMMAND_INJECTION_PATTERNS = [
        # Only flag shell metacharacters in suspicious contexts  
        r'[;&|`]\s*(rm|del|format|curl|wget|nc|sh|bash|cmd|powershell)',
        r'\$\(.*\)\s*[;&|]',  # Command substitution patterns
        # Network tools in suspicious contexts
        r'(?i)(curl|wget|nc|netcat)\s+.*[;&|]',
        # Destructive commands with paths
        r'(?i)(rm\s+\-rf|del\s+/[sqf]|format\s+[a-z]:)',
        # File access with system paths
        r'(?i)(cat|type|more|less)\s+(/etc/passwd|/etc/shadow|c:\\windows\\system32)',
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
    
    def detect_malicious_content(self, text: str, content_type: str = "general") -> List[str]:
        """Detect potentially malicious content in text."""
        if not text:
            return []
            
        threats = []
        text_lower = text.lower()
        
        # Log the validation attempt
        self.logger.debug(f"Starting content validation", extra={
            "event_type": "validation_start",
            "content_type": content_type,
            "content_length": len(text),
            "content_preview": text[:100] + "..." if len(text) > 100 else text
        })
        
        # Check for dangerous patterns
        for i, pattern in enumerate(self.DANGEROUS_PATTERNS):
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                threat = f"XSS/Script injection pattern detected"
                threats.append(threat)
                
                # Log the specific threat detection
                security_logger.log_validation_failure(
                    content=text,
                    validation_type="xss_detection",
                    reason=f"Pattern {i+1}: {pattern} matched: {match.group()[:100]}"
                )
                
                self.logger.warning(f"Malicious content detected: XSS pattern", extra={
                    "event_type": "threat_detected",
                    "threat_type": "xss",
                    "pattern_index": i,
                    "pattern": pattern,
                    "matched_content": match.group()[:200],
                    "content_type": content_type,
                    "full_content_length": len(text)
                })
        
        # Check for SQL injection
        for i, pattern in enumerate(self.SQL_INJECTION_PATTERNS):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                threat = f"SQL injection pattern detected"
                threats.append(threat)
                
                # Log the specific threat detection
                security_logger.log_validation_failure(
                    content=text,
                    validation_type="sql_injection_detection",
                    reason=f"SQL Pattern {i+1}: {pattern} matched: {match.group()[:100]}"
                )
                
                self.logger.warning(f"Malicious content detected: SQL injection pattern", extra={
                    "event_type": "threat_detected",
                    "threat_type": "sql_injection",
                    "pattern_index": i,
                    "pattern": pattern,
                    "matched_content": match.group()[:200],
                    "content_type": content_type,
                    "full_content_length": len(text)
                })
        
        # Check for command injection
        for i, pattern in enumerate(self.COMMAND_INJECTION_PATTERNS):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                threat = f"Command injection pattern detected"
                threats.append(threat)
                
                # Log the specific threat detection
                security_logger.log_validation_failure(
                    content=text,
                    validation_type="command_injection_detection",
                    reason=f"Command Pattern {i+1}: {pattern} matched: {match.group()[:100]}"
                )
                
                self.logger.warning(f"Malicious content detected: Command injection pattern", extra={
                    "event_type": "threat_detected",
                    "threat_type": "command_injection",
                    "pattern_index": i,
                    "pattern": pattern,
                    "matched_content": match.group()[:200],
                    "content_type": content_type,
                    "full_content_length": len(text)
                })
        
        # Log validation completion
        if threats:
            self.logger.error(f"Content validation failed with {len(threats)} threats", extra={
                "event_type": "validation_failed",
                "content_type": content_type,
                "threat_count": len(threats),
                "threats": threats,
                "content_length": len(text)
            })
        else:
            self.logger.debug(f"Content validation passed", extra={
                "event_type": "validation_passed",
                "content_type": content_type,
                "content_length": len(text)
            })
        
        return threats
    
    def validate_prompt_content(self, prompt: str) -> str:
        """Validate and sanitize prompt content for LLM processing."""
        if not prompt:
            self.logger.warning("Empty prompt validation attempted", extra={
                "event_type": "validation_error",
                "error_type": "empty_prompt"
            })
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prompt content cannot be empty"
            )
        
        self.logger.info("Validating prompt content", extra={
            "event_type": "prompt_validation",
            "prompt_length": len(prompt),
            "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt
        })
        
        # Check for malicious content
        threats = self.detect_malicious_content(prompt, content_type="prompt")
        if threats:
            self.logger.error("Prompt validation failed due to malicious content", extra={
                "event_type": "prompt_validation_failed",
                "threats": threats,
                "prompt_length": len(prompt),
                "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt
            })
            
            # Also log as security event
            security_logger.log_validation_failure(
                content=prompt,
                validation_type="prompt_validation",
                reason=f"Threats detected: {', '.join(threats)}"
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Potentially malicious content detected: {threats[0]}"
            )
        
        # Sanitize the prompt
        try:
            sanitized = self.sanitize_text(prompt, max_length=50000)  # Larger limit for prompts
        except HTTPException as e:
            self.logger.error("Prompt sanitization failed", extra={
                "event_type": "sanitization_error",
                "error": str(e.detail),
                "prompt_length": len(prompt)
            })
            raise
        
        # Additional validation for prompts
        if len(sanitized.strip()) < 10:
            self.logger.warning("Prompt too short after sanitization", extra={
                "event_type": "validation_error",
                "error_type": "prompt_too_short",
                "sanitized_length": len(sanitized.strip())
            })
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prompt too short. Minimum 10 characters required."
            )
        
        self.logger.info("Prompt validation successful", extra={
            "event_type": "prompt_validation_success",
            "original_length": len(prompt),
            "sanitized_length": len(sanitized)
        })
        
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