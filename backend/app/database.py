"""
Database configuration and SQLAlchemy models for the Synapse AI application.
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, CheckConstraint, Index, Float, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON
from sqlalchemy.sql import func
from pydantic import BaseModel

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./synapse_ai.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    is_active: bool
    subscription_tier: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None

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

def create_billing_record(db: Session, user_id: int, record_type: str, amount: float, **kwargs) -> BillingRecord:
    """Create a billing record."""
    db_billing = BillingRecord(
        user_id=user_id,
        record_type=record_type,
        amount=amount,
        **kwargs
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
