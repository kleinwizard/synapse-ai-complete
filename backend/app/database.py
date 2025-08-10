"""
Database configuration and SQLAlchemy models for the Synapse AI application.
"""

import os
import time
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, CheckConstraint, Index, Float, func, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON
from sqlalchemy.sql import func
from pydantic import BaseModel, validator

from .logging_config import get_logger, database_logger

# Import validation functions (will be added after validator creation to avoid circular import)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./synapse_ai.db")

# Production database configuration
def create_database_engine():
    """Create database engine with production-ready configuration."""
    if DATABASE_URL.startswith("postgresql://"):
        # PostgreSQL production configuration
        engine_args = {
            "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
            "pool_pre_ping": True,  # Validate connections before use
            "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),  # Recycle connections after 1 hour
            "connect_args": {
                "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "10")),
                "command_timeout": int(os.getenv("DB_COMMAND_TIMEOUT", "30")),
                "application_name": "synapse_ai"
            }
        }
        
        # Add SSL configuration for production
        if os.getenv("DB_REQUIRE_SSL", "false").lower() == "true":
            engine_args["connect_args"]["sslmode"] = "require"
            
    elif DATABASE_URL.startswith("sqlite"):
        # SQLite development configuration
        engine_args = {
            "connect_args": {
                "check_same_thread": False,
                "timeout": int(os.getenv("DB_SQLITE_TIMEOUT", "30"))
            }
        }
    else:
        # Generic configuration
        engine_args = {}
    
    return create_engine(DATABASE_URL, **engine_args)

engine = create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Set up SQLAlchemy event listeners for comprehensive query logging
query_logger = get_logger('database_queries')

@event.listens_for(engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log database query before execution."""
    context._query_start_time = time.time()
    
    # Truncate long queries for logging
    safe_statement = statement.replace('\n', ' ').replace('\t', ' ')
    if len(safe_statement) > 1000:
        safe_statement = safe_statement[:1000] + "..."
    
    # Count parameters but don't log sensitive data
    param_info = {}
    if parameters:
        if isinstance(parameters, (list, tuple)):
            param_info = {"parameter_count": len(parameters), "parameter_type": "positional"}
        elif isinstance(parameters, dict):
            param_info = {"parameter_count": len(parameters), "parameter_type": "named"}
        else:
            param_info = {"parameter_type": type(parameters).__name__}
    
    query_logger.debug(f"Executing database query", extra={
        "event_type": "db_query_start",
        "query": safe_statement,
        "executemany": executemany,
        **param_info
    })

@event.listens_for(engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log database query after execution."""
    execution_time = time.time() - context._query_start_time
    
    # Truncate long queries for logging
    safe_statement = statement.replace('\n', ' ').replace('\t', ' ')
    if len(safe_statement) > 1000:
        safe_statement = safe_statement[:1000] + "..."
    
    # Get row count if available
    row_count = cursor.rowcount if hasattr(cursor, 'rowcount') else None
    
    query_logger.debug(f"Database query completed", extra={
        "event_type": "db_query_complete",
        "query": safe_statement,
        "execution_time_seconds": execution_time,
        "row_count": row_count,
        "executemany": executemany
    })
    
    # Log slow queries as warnings
    if execution_time > 1.0:  # More than 1 second
        query_logger.warning(f"Slow database query detected: {execution_time:.2f}s", extra={
            "event_type": "db_slow_query",
            "query": safe_statement,
            "execution_time_seconds": execution_time,
            "row_count": row_count
        })
    
    # Also log to database logger
    database_logger.log_query(
        query=safe_statement,
        execution_time=execution_time
    )

@event.listens_for(engine, "handle_error")
def receive_handle_error(exception_context):
    """Log database errors."""
    query_logger.error(f"Database error occurred: {exception_context.original_exception}", extra={
        "event_type": "db_query_error",
        "error": str(exception_context.original_exception),
        "error_type": type(exception_context.original_exception).__name__,
        "statement": str(exception_context.statement)[:1000] if exception_context.statement else None,
        "connection_invalidated": exception_context.connection_invalidated
    })

@event.listens_for(engine, "connect")
def receive_connect(dbapi_connection, connection_record):
    """Log database connections."""
    query_logger.info("Database connection established", extra={
        "event_type": "db_connection_established",
        "connection_id": id(dbapi_connection)
    })
    
    database_logger.log_connection_event("connection_established", {
        "connection_id": id(dbapi_connection)
    })

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Log connection pool checkout."""
    query_logger.debug("Connection checked out from pool", extra={
        "event_type": "db_connection_checkout",
        "connection_id": id(dbapi_connection),
        "pool_size": engine.pool.size() if hasattr(engine.pool, 'size') else None,
        "checked_out": engine.pool.checkedout() if hasattr(engine.pool, 'checkedout') else None
    })

@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """Log connection pool checkin."""
    query_logger.debug("Connection checked in to pool", extra={
        "event_type": "db_connection_checkin",
        "connection_id": id(dbapi_connection),
        "pool_size": engine.pool.size() if hasattr(engine.pool, 'size') else None,
        "checked_out": engine.pool.checkedout() if hasattr(engine.pool, 'checkedout') else None
    })

def get_db():
    """Get database session with comprehensive error handling and logging."""
    logger = get_logger('database_session')
    start_time = time.time()
    db = SessionLocal()
    
    try:
        logger.debug("Database session created", extra={
            "event_type": "db_session_created",
            "connection_pool_size": engine.pool.size() if hasattr(engine.pool, 'size') else None,
            "checked_in_connections": engine.pool.checkedin() if hasattr(engine.pool, 'checkedin') else None,
            "checked_out_connections": engine.pool.checkedout() if hasattr(engine.pool, 'checkedout') else None
        })
        
        yield db
        
        # Log successful session completion
        session_time = time.time() - start_time
        logger.debug("Database session completed successfully", extra={
            "event_type": "db_session_completed",
            "session_duration_seconds": session_time
        })
        
    except Exception as e:
        session_time = time.time() - start_time
        
        # Log detailed error information
        logger.error(f"Database session error: {str(e)}", extra={
            "event_type": "db_session_error",
            "error": str(e),
            "error_type": type(e).__name__,
            "session_duration_seconds": session_time
        })
        
        # Log rollback attempt
        try:
            db.rollback()
            logger.info("Database transaction rolled back successfully", extra={
                "event_type": "db_rollback_success"
            })
        except Exception as rollback_error:
            logger.error(f"Database rollback failed: {str(rollback_error)}", extra={
                "event_type": "db_rollback_error",
                "rollback_error": str(rollback_error)
            })
        
        # Also log to database logger
        database_logger.log_connection_event("session_error", {
            "error": str(e),
            "duration_seconds": session_time
        })
        
        raise
    finally:
        try:
            db.close()
            logger.debug("Database session closed", extra={
                "event_type": "db_session_closed"
            })
        except Exception as close_error:
            logger.warning(f"Error closing database session: {str(close_error)}", extra={
                "event_type": "db_session_close_error",
                "error": str(close_error)
            })

def check_database_health() -> dict:
    """Check database connectivity and health with comprehensive logging."""
    logger = get_logger('database_health')
    start_time = time.time()
    
    try:
        logger.debug("Starting database health check", extra={
            "event_type": "db_health_check_start",
            "database_url_type": "postgresql" if DATABASE_URL.startswith("postgresql") else "sqlite"
        })
        
        db = SessionLocal()
        
        # Test basic connectivity
        query = func.now() if DATABASE_URL.startswith("postgresql") else "SELECT 1"
        query_start = time.time()
        result_set = db.execute(query)
        query_time = time.time() - query_start
        
        # Log the query execution
        database_logger.log_query(
            query=str(query),
            execution_time=query_time
        )
        
        logger.debug("Database connectivity test passed", extra={
            "event_type": "db_connectivity_test_passed",
            "query_execution_time_seconds": query_time
        })
        
        # Get connection pool info
        pool_info = {}
        if hasattr(engine.pool, 'size'):
            pool_info.update({
                "pool_size": engine.pool.size(),
                "pool_checked_in": engine.pool.checkedin() if hasattr(engine.pool, 'checkedin') else None,
                "pool_checked_out": engine.pool.checkedout() if hasattr(engine.pool, 'checkedout') else None,
            })
        
        # Get connection info
        health_check_time = time.time() - start_time
        result = {
            "status": "healthy",
            "database_type": "postgresql" if DATABASE_URL.startswith("postgresql") else "sqlite",
            "health_check_duration_seconds": health_check_time,
            "connectivity_test_duration_seconds": query_time,
            **pool_info
        }
        
        logger.info("Database health check completed successfully", extra={
            "event_type": "db_health_check_success",
            "health_check_duration_seconds": health_check_time,
            **pool_info
        })
        
        # Log to database logger
        database_logger.log_connection_event("health_check_success", {
            "duration_seconds": health_check_time,
            "pool_info": pool_info
        })
        
        db.close()
        return result
        
    except Exception as e:
        health_check_time = time.time() - start_time
        
        logger.error(f"Database health check failed: {str(e)}", extra={
            "event_type": "db_health_check_failed",
            "error": str(e),
            "error_type": type(e).__name__,
            "health_check_duration_seconds": health_check_time
        })
        
        # Log to database logger
        database_logger.log_connection_event("health_check_failed", {
            "error": str(e),
            "duration_seconds": health_check_time
        })
        
        return {
            "status": "unhealthy",
            "error": str(e),
            "error_type": type(e).__name__,
            "database_type": "postgresql" if DATABASE_URL.startswith("postgresql") else "sqlite",
            "health_check_duration_seconds": health_check_time
        }

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    subscription_tier = Column(String(50), default='free')
    credits = Column(Integer, default=100)
    use_local_ollama = Column(Boolean, default=False)  # User preference for Ollama optimization mode
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    prompts = relationship("Prompt", back_populates="user", cascade="all, delete-orphan")
    responses = relationship("Response", back_populates="user", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    billing_records = relationship("BillingRecord", back_populates="user", cascade="all, delete-orphan")

class Prompt(Base):
    __tablename__ = "prompts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    prompt_type = Column(String(50), nullable=False, index=True)  # 'optimize', 'execute', etc.
    content = Column(Text, nullable=False)
    parameters = Column(JSON)
    status = Column(String(50), default='pending', index=True)  # 'pending', 'processing', 'completed', 'failed'
    priority = Column(Integer, default=5)  # 1-10 scale
    estimated_time_minutes = Column(Integer)
    actual_time_minutes = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    user = relationship("User", back_populates="prompts")
    responses = relationship("Response", back_populates="prompt", cascade="all, delete-orphan")

class Response(Base):
    __tablename__ = "responses"
    
    id = Column(Integer, primary_key=True, index=True)
    prompt_id = Column(Integer, ForeignKey("prompts.id", ondelete="CASCADE"), index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    response_type = Column(String(50), nullable=False, index=True)  # 'optimization', 'execution', 'error'
    content = Column(JSON, nullable=False)
    response_metadata = Column(JSON)
    execution_time_ms = Column(Integer)
    status_code = Column(Integer, default=200)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    prompt = relationship("Prompt", back_populates="responses")
    user = relationship("User", back_populates="responses")
    feedback = relationship("Feedback", back_populates="response", cascade="all, delete-orphan")

class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    response_id = Column(Integer, ForeignKey("responses.id", ondelete="CASCADE"), index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    rating = Column(Integer, CheckConstraint('rating >= 1 AND rating <= 5'), index=True)
    comments = Column(Text)
    feedback_type = Column(String(50), default='general')  # 'general', 'bug_report', 'feature_request'
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    response = relationship("Response", back_populates="feedback")
    user = relationship("User", back_populates="feedback")

class ApiKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    key_prefix = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    user = relationship("User", back_populates="api_keys")

class BillingRecord(Base):
    __tablename__ = "billing_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    stripe_session_id = Column(String(255), unique=True, index=True)
    stripe_payment_intent_id = Column(String(255), index=True)
    record_type = Column(String(50), nullable=False, index=True)  # 'subscription', 'credits', 'refund'
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default='usd')
    credits_purchased = Column(Integer)
    subscription_plan = Column(String(50))
    status = Column(String(50), default='pending', index=True)  # 'pending', 'completed', 'failed', 'refunded'
    billing_metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user = relationship("User", back_populates="billing_records")

class UserCreate(BaseModel):
    email: str
    username: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    @validator('email')
    def validate_email(cls, v):
        from .validation import validate_email_field
        return validate_email_field(v)
    
    @validator('username')
    def validate_username(cls, v):
        from .validation import validate_username_field
        return validate_username_field(v)
    
    @validator('password')
    def validate_password(cls, v):
        from .validation import validate_password_field
        return validate_password_field(v)
    
    @validator('first_name')
    def validate_first_name(cls, v):
        from .validation import validate_name_field
        return validate_name_field(v) if v else v
    
    @validator('last_name')
    def validate_last_name(cls, v):
        from .validation import validate_name_field
        return validate_name_field(v) if v else v

class UserLogin(BaseModel):
    email: str
    password: str
    
    @validator('email')
    def validate_email(cls, v):
        from .validation import validate_email_field
        return validate_email_field(v)

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    is_active: bool
    subscription_tier: str
    use_local_ollama: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    
    @validator('email')
    def validate_email(cls, v):
        from .validation import validate_email_field
        return validate_email_field(v) if v else v
    
    @validator('first_name')
    def validate_first_name(cls, v):
        from .validation import validate_name_field
        return validate_name_field(v) if v else v
    
    @validator('last_name')
    def validate_last_name(cls, v):
        from .validation import validate_name_field
        return validate_name_field(v) if v else v

class UserSettingsUpdate(BaseModel):
    use_local_ollama: Optional[bool] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class ApiKeyCreate(BaseModel):
    name: str

class ApiKeyResponse(BaseModel):
    id: int
    name: str
    key_prefix: str
    is_active: bool
    last_used: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class BillingRecordResponse(BaseModel):
    id: int
    record_type: str
    amount: float
    currency: str
    credits_purchased: Optional[int]
    subscription_plan: Optional[str]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class PromptCreate(BaseModel):
    user_id: Optional[int] = None
    prompt_type: str
    content: str
    parameters: Optional[Dict[str, Any]] = None
    priority: Optional[int] = 5
    
    @validator('content')
    def validate_content(cls, v):
        from .validation import validate_prompt_field
        return validate_prompt_field(v)
    
    @validator('parameters')
    def validate_parameters(cls, v):
        from .validation import validator
        return validator.sanitize_dict(v) if v else v

class PromptResponse(BaseModel):
    id: int
    user_id: Optional[int]
    prompt_type: str
    content: str
    parameters: Optional[Dict[str, Any]]
    status: str
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class ResponseCreate(BaseModel):
    prompt_id: int
    user_id: Optional[int] = None
    response_type: str
    content: Dict[str, Any]
    response_metadata: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[int] = None
    status_code: Optional[int] = 200
    error_message: Optional[str] = None

class ResponseResponse(BaseModel):
    id: int
    prompt_id: int
    user_id: Optional[int]
    response_type: str
    content: Dict[str, Any]
    response_metadata: Optional[Dict[str, Any]]
    execution_time_ms: Optional[int]
    status_code: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class FeedbackCreate(BaseModel):
    response_id: int
    user_id: Optional[int] = None
    rating: int
    comments: Optional[str] = None
    feedback_type: Optional[str] = 'general'

class FeedbackResponse(BaseModel):
    id: int
    response_id: int
    user_id: Optional[int]
    rating: int
    comments: Optional[str]
    feedback_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True

def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username."""
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user: UserCreate, password_hash: str) -> User:
    """Create a new user."""
    db_user = User(
        email=user.email,
        username=user.username,
        password_hash=password_hash,
        first_name=user.first_name,
        last_name=user.last_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_profile(db: Session, user_id: int, profile_data: UserProfileUpdate) -> Optional[User]:
    """Update user profile."""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        for field, value in profile_data.dict(exclude_unset=True).items():
            setattr(user, field, value)
        user.updated_at = func.now()
        db.commit()
        db.refresh(user)
    return user

def update_user_password(db: Session, user_id: int, password_hash: str) -> Optional[User]:
    """Update user password."""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.password_hash = password_hash
        user.updated_at = func.now()
        db.commit()
        db.refresh(user)
    return user

def delete_user(db: Session, user_id: int) -> bool:
    """Delete a user and all associated data."""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False

def create_api_key(db: Session, user_id: int, name: str, key_hash: str, key_prefix: str) -> ApiKey:
    """Create a new API key."""
    db_api_key = ApiKey(
        user_id=user_id,
        name=name,
        key_hash=key_hash,
        key_prefix=key_prefix
    )
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)
    return db_api_key

def get_user_api_keys(db: Session, user_id: int) -> list[ApiKey]:
    """Get all API keys for a user."""
    return db.query(ApiKey).filter(ApiKey.user_id == user_id, ApiKey.is_active == True).all()

def revoke_api_key(db: Session, user_id: int, key_id: int) -> bool:
    """Revoke an API key."""
    api_key = db.query(ApiKey).filter(ApiKey.id == key_id, ApiKey.user_id == user_id).first()
    if api_key:
        api_key.is_active = False
        db.commit()
        return True
    return False

def create_billing_record(db: Session, billing_data: dict) -> BillingRecord:
    """Create a billing record."""
    db_billing = BillingRecord(
        user_id=billing_data.get('user_id'),
        record_type=billing_data.get('description', 'payment'),
        amount=billing_data.get('amount'),
        currency=billing_data.get('currency', 'usd'),
        stripe_session_id=billing_data.get('stripe_session_id'),
        status=billing_data.get('status', 'completed')
    )
    db.add(db_billing)
    db.commit()
    db.refresh(db_billing)
    return db_billing

def get_user_billing_history(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> list[BillingRecord]:
    """Get user's billing history."""
    return db.query(BillingRecord).filter(BillingRecord.user_id == user_id).offset(skip).limit(limit).all()

def create_prompt(db: Session, prompt: PromptCreate) -> Prompt:
    """Create a new prompt record."""
    db_prompt = Prompt(**prompt.dict())
    db.add(db_prompt)
    db.commit()
    db.refresh(db_prompt)
    return db_prompt

def create_response(db: Session, response: ResponseCreate) -> Response:
    """Create a new response record."""
    db_response = Response(**response.dict())
    db.add(db_response)
    db.commit()
    db.refresh(db_response)
    return db_response

def create_feedback(db: Session, feedback: FeedbackCreate) -> Feedback:
    """Create a new feedback record."""
    db_feedback = Feedback(**feedback.dict())
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback

def get_user_prompts(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """Get user's prompt history."""
    return db.query(Prompt).filter(Prompt.user_id == user_id).offset(skip).limit(limit).all()

def get_prompt_responses(db: Session, prompt_id: int):
    """Get all responses for a prompt."""
    return db.query(Response).filter(Response.prompt_id == prompt_id).all()

def update_prompt_status(db: Session, prompt_id: int, status: str, completed_at: Optional[datetime] = None):
    """Update prompt status."""
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if prompt:
        prompt.status = status
        prompt.updated_at = func.now()
        if completed_at:
            prompt.completed_at = completed_at
        db.commit()
        db.refresh(prompt)
    return prompt

def add_user_credits(db: Session, user_id: int, credits: int):
    """Add credits to user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        current_credits = getattr(user, 'credits', 0) or 0
        user.credits = current_credits + credits
        db.commit()
        db.refresh(user)
    return user

def update_user_subscription(db: Session, user_id: int, plan_id: str):
    """Update user subscription plan."""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.subscription_tier = plan_id
        db.commit()
        db.refresh(user)
    return user
