"""
Comprehensive logging configuration for Synapse AI backend.

This module provides structured logging with different log levels and formats
to help debug issues throughout the application.
"""

import logging
import logging.config
import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import contextmanager
import threading
from functools import wraps

# Thread-local storage for request context
_local = threading.local()

class RequestContextFilter(logging.Filter):
    """Filter to add request context to log records."""
    
    def filter(self, record):
        record.request_id = getattr(_local, 'request_id', 'unknown')
        record.user_id = getattr(_local, 'user_id', 'anonymous')
        record.user_email = getattr(_local, 'user_email', 'unknown')
        record.endpoint = getattr(_local, 'endpoint', 'unknown')
        record.method = getattr(_local, 'method', 'unknown')
        record.ip_address = getattr(_local, 'ip_address', 'unknown')
        return True

class StructuredJSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record):
        # Create base log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "thread_name": record.threadName,
            "process": record.process
        }
        
        # Add request context if available
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
            log_entry["user_id"] = record.user_id
            log_entry["user_email"] = record.user_email
            log_entry["endpoint"] = record.endpoint
            log_entry["method"] = record.method
            log_entry["ip_address"] = record.ip_address
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info) if record.exc_info else None
            }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                          'module', 'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName',
                          'created', 'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage', 'request_id', 'user_id',
                          'user_email', 'endpoint', 'method', 'ip_address']:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str, separators=(',', ':'))

def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration dictionary."""
    
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_format = os.getenv('LOG_FORMAT', 'json')  # 'json' or 'text'
    log_file = os.getenv('LOG_FILE', 'synapse_ai.log')
    
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                '()': StructuredJSONFormatter,
            },
            'text': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] [%(user_email)s] [%(method)s %(endpoint)s] - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - [%(request_id)s] [%(user_email)s] [%(method)s %(endpoint)s] - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'filters': {
            'request_context': {
                '()': RequestContextFilter
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': log_format if log_format in ['json', 'text'] else 'text',
                'filters': ['request_context'],
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': log_level,
                'formatter': 'json',
                'filters': ['request_context'],
                'filename': log_file,
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'json',
                'filters': ['request_context'],
                'filename': 'error.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5
            }
        },
        'loggers': {
            'synapse_ai': {
                'level': log_level,
                'handlers': ['console', 'file', 'error_file'],
                'propagate': False
            },
            'uvicorn': {
                'level': 'INFO',
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'uvicorn.error': {
                'level': 'INFO',
                'handlers': ['console', 'file', 'error_file'],
                'propagate': False
            },
            'uvicorn.access': {
                'level': 'INFO',
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'sqlalchemy': {
                'level': 'WARNING',
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'httpx': {
                'level': 'WARNING',
                'handlers': ['console', 'file'],
                'propagate': False
            }
        },
        'root': {
            'level': log_level,
            'handlers': ['console', 'file']
        }
    }
    
    return config

def setup_logging():
    """Initialize the logging configuration."""
    config = get_logging_config()
    logging.config.dictConfig(config)
    
    # Get logger and log initialization
    logger = logging.getLogger('synapse_ai.init')
    logger.info("Logging system initialized", extra={
        "log_level": os.getenv('LOG_LEVEL', 'INFO'),
        "log_format": os.getenv('LOG_FORMAT', 'json'),
        "handlers": ["console", "file", "error_file"]
    })

@contextmanager
def request_context(request_id: str = None, user_id: str = None, user_email: str = None, 
                   endpoint: str = None, method: str = None, ip_address: str = None):
    """Context manager to set request context for logging."""
    
    # Store previous values
    old_request_id = getattr(_local, 'request_id', None)
    old_user_id = getattr(_local, 'user_id', None)
    old_user_email = getattr(_local, 'user_email', None)
    old_endpoint = getattr(_local, 'endpoint', None)
    old_method = getattr(_local, 'method', None)
    old_ip_address = getattr(_local, 'ip_address', None)
    
    # Set new values
    _local.request_id = request_id or str(uuid.uuid4())
    _local.user_id = user_id or 'anonymous'
    _local.user_email = user_email or 'unknown'
    _local.endpoint = endpoint or 'unknown'
    _local.method = method or 'unknown'
    _local.ip_address = ip_address or 'unknown'
    
    try:
        yield
    finally:
        # Restore previous values
        _local.request_id = old_request_id
        _local.user_id = old_user_id
        _local.user_email = old_user_email
        _local.endpoint = old_endpoint
        _local.method = old_method
        _local.ip_address = old_ip_address

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the synapse_ai prefix."""
    return logging.getLogger(f'synapse_ai.{name}')

def log_execution_time(func):
    """Decorator to log function execution time."""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = datetime.utcnow()
        logger = get_logger('performance')
        
        try:
            result = await func(*args, **kwargs)
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            
            logger.info(f"Function {func.__name__} executed successfully", extra={
                "function": func.__name__,
                "execution_time_seconds": execution_time,
                "status": "success"
            })
            
            return result
        except Exception as e:
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            
            logger.error(f"Function {func.__name__} failed", extra={
                "function": func.__name__,
                "execution_time_seconds": execution_time,
                "status": "error",
                "error": str(e)
            })
            
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = datetime.utcnow()
        logger = get_logger('performance')
        
        try:
            result = func(*args, **kwargs)
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            
            logger.info(f"Function {func.__name__} executed successfully", extra={
                "function": func.__name__,
                "execution_time_seconds": execution_time,
                "status": "success"
            })
            
            return result
        except Exception as e:
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            
            logger.error(f"Function {func.__name__} failed", extra={
                "function": func.__name__,
                "execution_time_seconds": execution_time,
                "status": "error",
                "error": str(e)
            })
            
            raise
    
    if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
        return async_wrapper
    else:
        return sync_wrapper

class SecurityLogger:
    """Specialized logger for security events."""
    
    def __init__(self):
        self.logger = get_logger('security')
    
    def log_auth_attempt(self, email: str, success: bool, ip_address: str = None, reason: str = None):
        """Log authentication attempt."""
        self.logger.info(f"Authentication attempt: {email}", extra={
            "event_type": "auth_attempt",
            "email": email,
            "success": success,
            "ip_address": ip_address,
            "reason": reason,
            "security_event": True
        })
    
    def log_validation_failure(self, content: str, validation_type: str, reason: str, user_email: str = None):
        """Log content validation failure (potential malicious content)."""
        # Truncate content for logging (don't log full potentially malicious content)
        safe_content = content[:200] + "..." if len(content) > 200 else content
        
        self.logger.warning(f"Content validation failed: {validation_type}", extra={
            "event_type": "validation_failure",
            "validation_type": validation_type,
            "reason": reason,
            "content_preview": safe_content,
            "content_length": len(content),
            "user_email": user_email,
            "security_event": True
        })
    
    def log_rate_limit_exceeded(self, endpoint: str, user_email: str = None, ip_address: str = None):
        """Log rate limit exceeded."""
        self.logger.warning(f"Rate limit exceeded: {endpoint}", extra={
            "event_type": "rate_limit_exceeded",
            "endpoint": endpoint,
            "user_email": user_email,
            "ip_address": ip_address,
            "security_event": True
        })
    
    def log_suspicious_activity(self, activity_type: str, details: Dict[str, Any], user_email: str = None):
        """Log suspicious activity."""
        self.logger.warning(f"Suspicious activity detected: {activity_type}", extra={
            "event_type": "suspicious_activity",
            "activity_type": activity_type,
            "details": details,
            "user_email": user_email,
            "security_event": True
        })

class DatabaseLogger:
    """Specialized logger for database operations."""
    
    def __init__(self):
        self.logger = get_logger('database')
    
    def log_query(self, query: str, parameters: Dict[str, Any] = None, execution_time: float = None):
        """Log database query."""
        # Sanitize query for logging (remove sensitive data)
        safe_query = query.replace('\n', ' ').replace('\t', ' ')
        if len(safe_query) > 500:
            safe_query = safe_query[:500] + "..."
        
        self.logger.debug(f"Database query executed", extra={
            "event_type": "db_query",
            "query": safe_query,
            "parameter_count": len(parameters) if parameters else 0,
            "execution_time_seconds": execution_time
        })
    
    def log_connection_event(self, event_type: str, details: Dict[str, Any] = None):
        """Log database connection events."""
        self.logger.info(f"Database connection event: {event_type}", extra={
            "event_type": "db_connection",
            "connection_event": event_type,
            "details": details or {}
        })
    
    def log_migration(self, migration_name: str, success: bool, error: str = None):
        """Log database migration."""
        level = self.logger.info if success else self.logger.error
        level(f"Database migration: {migration_name}", extra={
            "event_type": "db_migration",
            "migration": migration_name,
            "success": success,
            "error": error
        })

class APILogger:
    """Specialized logger for external API calls."""
    
    def __init__(self):
        self.logger = get_logger('api_calls')
    
    def log_api_call(self, provider: str, model: str, endpoint: str, 
                    request_data: Dict[str, Any] = None, 
                    response_data: Dict[str, Any] = None,
                    execution_time: float = None,
                    success: bool = True,
                    error: str = None):
        """Log external API call."""
        
        # Sanitize request data (remove sensitive information)
        safe_request = {}
        if request_data:
            safe_request = {k: v for k, v in request_data.items() 
                           if k not in ['api_key', 'authorization', 'token']}
            # Truncate long prompts
            if 'prompt' in safe_request and len(str(safe_request['prompt'])) > 500:
                safe_request['prompt'] = str(safe_request['prompt'])[:500] + "..."
            if 'messages' in safe_request:
                # Truncate message content
                for msg in safe_request.get('messages', []):
                    if isinstance(msg, dict) and 'content' in msg:
                        if len(str(msg['content'])) > 200:
                            msg['content'] = str(msg['content'])[:200] + "..."
        
        # Sanitize response data
        safe_response = {}
        if response_data:
            safe_response = response_data.copy()
            # Truncate long responses
            if 'content' in safe_response and len(str(safe_response['content'])) > 500:
                safe_response['content'] = str(safe_response['content'])[:500] + "..."
            if 'choices' in safe_response:
                for choice in safe_response.get('choices', []):
                    if isinstance(choice, dict) and 'message' in choice:
                        if 'content' in choice['message'] and len(str(choice['message']['content'])) > 200:
                            choice['message']['content'] = str(choice['message']['content'])[:200] + "..."
        
        log_level = self.logger.info if success else self.logger.error
        log_level(f"External API call: {provider}/{model}", extra={
            "event_type": "api_call",
            "provider": provider,
            "model": model,
            "endpoint": endpoint,
            "request_data": safe_request,
            "response_data": safe_response,
            "execution_time_seconds": execution_time,
            "success": success,
            "error": error
        })

# Initialize loggers
security_logger = SecurityLogger()
database_logger = DatabaseLogger()
api_logger = APILogger()