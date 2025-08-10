"""
Authentication utilities for JWT token management and password hashing.
"""

import os
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from .database import get_db, get_user_by_email, get_user_by_id, User
from .logging_config import get_logger, security_logger

# Load environment variables
load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Initialize loggers
auth_logger = get_logger('authentication')

def hash_password(password: str) -> str:
    """Hash a password using bcrypt with logging."""
    start_time = time.time()
    
    auth_logger.debug("Starting password hashing", extra={
        "event_type": "password_hash_start",
        "password_length": len(password) if password else 0
    })
    
    try:
        hashed = pwd_context.hash(password)
        hash_time = time.time() - start_time
        
        auth_logger.debug("Password hashed successfully", extra={
            "event_type": "password_hash_success",
            "hash_time_seconds": hash_time
        })
        
        return hashed
    except Exception as e:
        hash_time = time.time() - start_time
        
        auth_logger.error(f"Password hashing failed: {str(e)}", extra={
            "event_type": "password_hash_failed",
            "error": str(e),
            "error_type": type(e).__name__,
            "hash_time_seconds": hash_time
        })
        
        raise

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash with logging."""
    start_time = time.time()
    
    auth_logger.debug("Starting password verification", extra={
        "event_type": "password_verify_start",
        "password_length": len(plain_password) if plain_password else 0,
        "has_hash": bool(hashed_password)
    })
    
    try:
        is_valid = pwd_context.verify(plain_password, hashed_password)
        verify_time = time.time() - start_time
        
        auth_logger.debug(f"Password verification completed: {is_valid}", extra={
            "event_type": "password_verify_complete",
            "is_valid": is_valid,
            "verify_time_seconds": verify_time
        })
        
        if not is_valid:
            auth_logger.warning("Password verification failed", extra={
                "event_type": "password_verify_failed",
                "verify_time_seconds": verify_time
            })
        
        return is_valid
    except Exception as e:
        verify_time = time.time() - start_time
        
        auth_logger.error(f"Password verification error: {str(e)}", extra={
            "event_type": "password_verify_error",
            "error": str(e),
            "error_type": type(e).__name__,
            "verify_time_seconds": verify_time
        })
        
        return False

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token with logging."""
    start_time = time.time()
    to_encode = data.copy()
    
    user_id = data.get('sub', 'unknown')
    token_type = data.get('type', 'access')
    
    auth_logger.debug(f"Creating {token_type} token", extra={
        "event_type": "token_create_start",
        "token_type": token_type,
        "user_id": str(user_id),
        "custom_expiration": expires_delta is not None
    })
    
    try:
        # Ensure 'sub' is a string (JWT requirement)
        if 'sub' in to_encode and not isinstance(to_encode['sub'], str):
            to_encode['sub'] = str(to_encode['sub'])
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        
        token_time = time.time() - start_time
        
        auth_logger.info(f"JWT token created successfully", extra={
            "event_type": "token_create_success",
            "token_type": token_type,
            "user_id": str(user_id),
            "expires_at": expire.isoformat(),
            "token_length": len(encoded_jwt),
            "creation_time_seconds": token_time
        })
        
        return encoded_jwt
    
    except Exception as e:
        token_time = time.time() - start_time
        
        auth_logger.error(f"JWT token creation failed: {str(e)}", extra={
            "event_type": "token_create_failed",
            "token_type": token_type,
            "user_id": str(user_id),
            "error": str(e),
            "error_type": type(e).__name__,
            "creation_time_seconds": token_time
        })
        
        raise

def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode a JWT token with logging."""
    start_time = time.time()
    token_preview = token[:20] + "..." if len(token) > 20 else token
    
    auth_logger.debug("Starting token verification", extra={
        "event_type": "token_verify_start",
        "token_preview": token_preview,
        "token_length": len(token)
    })
    
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        verify_time = time.time() - start_time
        
        user_id = payload.get('sub', 'unknown')
        token_type = payload.get('type', 'access')
        expires_at = payload.get('exp')
        
        auth_logger.info("Token verification successful", extra={
            "event_type": "token_verify_success",
            "token_type": token_type,
            "user_id": str(user_id),
            "expires_at": datetime.fromtimestamp(expires_at).isoformat() if expires_at else None,
            "verify_time_seconds": verify_time
        })
        
        return payload
    
    except JWTError as e:
        verify_time = time.time() - start_time
        
        auth_logger.warning(f"Token verification failed: {str(e)}", extra={
            "event_type": "token_verify_failed",
            "token_preview": token_preview,
            "error": str(e),
            "error_type": type(e).__name__,
            "verify_time_seconds": verify_time
        })
        
        # Log as security event
        security_logger.log_auth_attempt(
            email="unknown",
            success=False,
            reason=f"Invalid JWT token: {str(e)}"
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    except Exception as e:
        verify_time = time.time() - start_time
        
        auth_logger.error(f"Token verification error: {str(e)}", extra={
            "event_type": "token_verify_error",
            "token_preview": token_preview,
            "error": str(e),
            "error_type": type(e).__name__,
            "verify_time_seconds": verify_time
        })
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def authenticate_user(db: Session, email: str, password: str, ip_address: str = None) -> Optional[User]:
    """Authenticate a user with email and password with comprehensive logging."""
    start_time = time.time()
    
    auth_logger.info(f"Authentication attempt for email: {email}", extra={
        "event_type": "auth_attempt_start",
        "email": email,
        "ip_address": ip_address,
        "has_password": bool(password)
    })
    
    try:
        # Look up user
        user = get_user_by_email(db, email)
        
        if not user:
            auth_time = time.time() - start_time
            
            auth_logger.warning(f"Authentication failed: user not found for email {email}", extra={
                "event_type": "auth_failed_user_not_found",
                "email": email,
                "ip_address": ip_address,
                "auth_time_seconds": auth_time
            })
            
            # Log security event
            security_logger.log_auth_attempt(
                email=email,
                success=False,
                ip_address=ip_address,
                reason="User not found"
            )
            
            return None
        
        # Check if user is active
        if not user.is_active:
            auth_time = time.time() - start_time
            
            auth_logger.warning(f"Authentication failed: user account inactive for {email}", extra={
                "event_type": "auth_failed_inactive_account",
                "email": email,
                "user_id": user.id,
                "ip_address": ip_address,
                "auth_time_seconds": auth_time
            })
            
            # Log security event
            security_logger.log_auth_attempt(
                email=email,
                success=False,
                ip_address=ip_address,
                reason="Account inactive"
            )
            
            return None
        
        # Verify password
        if not verify_password(password, user.password_hash):
            auth_time = time.time() - start_time
            
            auth_logger.warning(f"Authentication failed: invalid password for {email}", extra={
                "event_type": "auth_failed_invalid_password",
                "email": email,
                "user_id": user.id,
                "ip_address": ip_address,
                "auth_time_seconds": auth_time
            })
            
            # Log security event
            security_logger.log_auth_attempt(
                email=email,
                success=False,
                ip_address=ip_address,
                reason="Invalid password"
            )
            
            return None
        
        # Successful authentication
        auth_time = time.time() - start_time
        
        auth_logger.info(f"Authentication successful for {email}", extra={
            "event_type": "auth_success",
            "email": email,
            "user_id": user.id,
            "username": user.username,
            "ip_address": ip_address,
            "auth_time_seconds": auth_time,
            "last_login": user.last_login.isoformat() if user.last_login else None
        })
        
        # Log security event
        security_logger.log_auth_attempt(
            email=email,
            success=True,
            ip_address=ip_address,
            reason="Valid credentials"
        )
        
        return user
    
    except Exception as e:
        auth_time = time.time() - start_time
        
        auth_logger.error(f"Authentication error for {email}: {str(e)}", extra={
            "event_type": "auth_error",
            "email": email,
            "ip_address": ip_address,
            "error": str(e),
            "error_type": type(e).__name__,
            "auth_time_seconds": auth_time
        })
        
        # Log security event
        security_logger.log_auth_attempt(
            email=email,
            success=False,
            ip_address=ip_address,
            reason=f"Authentication error: {str(e)}"
        )
        
        return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token."""
    token = credentials.credentials
    payload = verify_token(token)
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    
    # Convert user_id to int (it should be a string from JWT)
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
        )
    
    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user

def generate_api_key() -> str:
    """Generate a secure API key."""
    return f"sk-{secrets.token_urlsafe(32)}"

def get_jwt_secret() -> str:
    """Get JWT secret key for token operations."""
    return JWT_SECRET_KEY
