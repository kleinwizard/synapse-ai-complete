import os
import time
import hmac
import hashlib
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
import psycopg
import stripe
import sendgrid
from sendgrid.helpers.mail import Mail
from .prompt_builder import SynapsePromptBuilder, PromptData
from .llm_router import select_model, get_model_info, validate_routing_request
from .execution_engine import get_execution_engine, initialize_execution_engine
from .auth import (
    hash_password, verify_password, create_access_token, authenticate_user, 
    get_current_user, generate_api_key
)
from .database import (
    get_db, create_tables, 
    PromptCreate, PromptResponse, ResponseCreate, ResponseResponse, 
    FeedbackCreate, FeedbackResponse, UserCreate, UserLogin, UserResponse,
    UserProfileUpdate, PasswordChange, ApiKeyCreate, ApiKeyResponse, BillingRecordResponse,
    create_prompt, create_response, create_feedback, 
    get_user_prompts, get_prompt_responses, update_prompt_status,
    get_user_by_email, get_user_by_username, create_user, update_user_profile,
    update_user_password, delete_user, create_api_key, get_user_api_keys,
    revoke_api_key, create_billing_record, get_user_billing_history, User,
    add_user_credits
)

async def collect_streaming_response(streaming_response) -> str:
    """Helper function to collect full response from streaming response."""
    full_response = ""
    try:
        # Handle StreamingResponse body_iterator
        async for chunk in streaming_response.body_iterator:
            chunk_str = chunk.decode() if isinstance(chunk, bytes) else str(chunk)
            
            # Split by lines and process each line
            for line in chunk_str.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    # Try to parse as JSON (for SSE format)
                    if line.startswith('data: '):
                        json_str = line[6:]  # Remove 'data: ' prefix
                        if json_str.strip() in ['[DONE]', '']:
                            continue
                        data = json.loads(json_str)
                    else:
                        # Try to parse as plain JSON
                        data = json.loads(line)
                    
                    # Extract text content from different response formats
                    text_content = ""
                    
                    # Ollama format
                    if 'response' in data:
                        text_content = data['response']
                    # OpenAI streaming format
                    elif 'choices' in data and len(data['choices']) > 0:
                        choice = data['choices'][0]
                        if 'delta' in choice and 'content' in choice['delta']:
                            text_content = choice['delta']['content']
                        elif 'text' in choice:
                            text_content = choice['text']
                    # Anthropic format
                    elif 'content' in data:
                        if isinstance(data['content'], list):
                            text_content = ''.join([item.get('text', '') for item in data['content']])
                        else:
                            text_content = data['content']
                    # Generic text field
                    elif 'text' in data:
                        text_content = data['text']
                    
                    if text_content:
                        full_response += text_content
                        
                except (json.JSONDecodeError, KeyError, TypeError):
                    # If not JSON, might be plain text
                    if line and not line.startswith('data:'):
                        full_response += line + ' '
                    continue
                    
        return full_response.strip()
        
    except Exception as e:
        print(f"Error collecting streaming response: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return ""

app = FastAPI(title="SaaS Boilerplate API", version="1.0.0")

cors_origins = os.getenv("CORS_ORIGIN_URL", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize execution engine and database on startup."""
    create_tables()
    print("Database tables initialized successfully.")
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    stripe_secret_key = os.getenv("STRIPE_SECRET_KEY")
    sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
    
    if openai_api_key or anthropic_api_key:
        await initialize_execution_engine(openai_api_key, anthropic_api_key)
    else:
        print("Warning: No API keys found in environment variables. LLM execution will be limited to Ollama only.")
    
    if stripe_secret_key:
        stripe.api_key = stripe_secret_key
        print("Stripe initialized successfully.")
    else:
        print("Warning: No Stripe secret key found. Billing functionality will be limited.")
    
    if sendgrid_api_key:
        print("SendGrid initialized successfully.")
    else:
        print("Warning: No SendGrid API key found. Email functionality will be limited.")

class OptimizeRequest(BaseModel):
    prompt: str
    parameters: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    domain_knowledge: Optional[str] = None
    role: Optional[str] = "professional assistant"
    tone: Optional[str] = "helpful and analytical"
    task_description: Optional[str] = None
    deliverable_format: Optional[str] = "markdown"
    available_tools: Optional[List[str]] = None
    constraints: Optional[List[str]] = None
    word_limit: Optional[int] = None

class ExecuteRequest(BaseModel):
    task_id: str
    action: str
    prompt: str
    power_level: str
    task_type: Optional[str] = "default"
    payload: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None

class FeedbackRequest(BaseModel):
    response_id: int
    rating: int
    comments: Optional[str] = None
    user_id: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class StripeCheckoutRequest(BaseModel):
    plan_id: str
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None

class CreditCheckoutRequest(BaseModel):
    credits: int
    amount: float
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    existing_username = get_user_by_username(db, user_data.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    password_hash = hash_password(user_data.password)
    user = create_user(db, user_data, password_hash)
    
    # Give new users 1000 test credits - set directly
    user.credits = (user.credits or 0) + 1000
    db.commit()
    db.refresh(user)
    
    await send_welcome_email(user.email, user.first_name or user.username)
    
    access_token = create_access_token(data={"sub": user.id})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )

@app.post("/auth/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user and return JWT token."""
    user = authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.id})
    
    user.last_login = datetime.utcnow()
    db.commit()
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )

@app.post("/auth/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user (client should remove token)."""
    return {"message": "Successfully logged out"}

@app.get("/users/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return UserResponse.from_orm(current_user)

@app.put("/users/profile", response_model=UserResponse)
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile."""
    if profile_data.email and profile_data.email != current_user.email:
        existing_user = get_user_by_email(db, profile_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
    
    updated_user = update_user_profile(db, current_user.id, profile_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.from_orm(updated_user)

@app.put("/users/password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password."""
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    new_password_hash = hash_password(password_data.new_password)
    updated_user = update_user_password(db, current_user.id, new_password_hash)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "Password updated successfully"}

@app.delete("/users/account")
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete user account."""
    success = delete_user(db, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "Account deleted successfully"}

@app.get("/users/api-keys", response_model=List[ApiKeyResponse])
async def get_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's API keys."""
    api_keys = get_user_api_keys(db, current_user.id)
    return [ApiKeyResponse.from_orm(key) for key in api_keys]

@app.post("/users/api-keys")
async def create_new_api_key(
    key_data: ApiKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a new API key."""
    api_key = generate_api_key()
    key_hash = hash_password(api_key)
    key_prefix = api_key[:12] + "..."
    
    db_api_key = create_api_key(db, current_user.id, key_data.name, key_hash, key_prefix)
    
    return {
        "id": db_api_key.id,
        "name": db_api_key.name,
        "key": api_key,
        "key_prefix": key_prefix,
        "created_at": db_api_key.created_at
    }

@app.delete("/users/api-keys/{key_id}")
async def revoke_api_key_endpoint(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke an API key."""
    success = revoke_api_key(db, current_user.id, key_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return {"message": "API key revoked successfully"}

@app.get("/users/subscription")
async def get_user_subscription(current_user: User = Depends(get_current_user)):
    """Get user's current subscription details."""
    return {
        "current_plan": current_user.subscription_tier,
        "credits": 0,
        "subscription_tier": current_user.subscription_tier
    }

@app.post("/stripe/create-checkout")
async def create_stripe_checkout(
    checkout_data: StripeCheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create Stripe checkout session for subscription."""
    try:
        price_map = {
            "pro": "price_pro_monthly",
            "enterprise": "price_enterprise_monthly"
        }
        
        if checkout_data.plan_id not in price_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid plan ID"
            )
        
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_map[checkout_data.plan_id],
                'quantity': 1,
            }],
            mode='subscription',
            success_url=checkout_data.success_url or f"{os.getenv('CORS_ORIGIN_URL', 'http://localhost:5173')}/success",
            cancel_url=checkout_data.cancel_url or f"{os.getenv('CORS_ORIGIN_URL', 'http://localhost:5173')}/cancel",
            customer_email=current_user.email,
            metadata={
                'user_id': current_user.id,
                'plan_id': checkout_data.plan_id
            }
        )
        
        return {"checkout_url": session.url}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment processing error: {str(e)}"
        )

@app.post("/stripe/create-credit-checkout")
async def create_credit_checkout(
    checkout_data: CreditCheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create Stripe checkout session for credit purchase."""
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'{checkout_data.credits} Synapse Credits',
                    },
                    'unit_amount': int(checkout_data.amount * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=checkout_data.success_url or f"{os.getenv('CORS_ORIGIN_URL', 'http://localhost:5173')}/success",
            cancel_url=checkout_data.cancel_url or f"{os.getenv('CORS_ORIGIN_URL', 'http://localhost:5173')}/cancel",
            customer_email=current_user.email,
            metadata={
                'user_id': current_user.id,
                'credits': checkout_data.credits,
                'type': 'credits'
            }
        )
        
        return {"checkout_url": session.url}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment processing error: {str(e)}"
        )

@app.post("/stripe/customer-portal")
async def create_customer_portal(
    current_user: User = Depends(get_current_user)
):
    """Create Stripe customer portal session."""
    try:
        session = stripe.billing_portal.Session.create(
            customer=current_user.email,
            return_url=f"{os.getenv('CORS_ORIGIN_URL', 'http://localhost:5173')}/settings",
        )
        
        return {"portal_url": session.url}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment processing error: {str(e)}"
        )

@app.get("/users/billing-history", response_model=List[BillingRecordResponse])
async def get_billing_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Get user's billing history."""
    billing_records = get_user_billing_history(db, current_user.id, skip, limit)
    return [BillingRecordResponse.from_orm(record) for record in billing_records]

@app.get("/models")
async def get_models():
    """
    Get information about available models and routing structure.
    
    This endpoint provides transparency into the LLM routing system,
    showing available power levels, task types, and model mappings.
    """
    model_info = get_model_info()
    return {
        "status": "ok",
        "message": "Model catalog information retrieved successfully",
        "model_info": model_info
    }

@app.post("/optimize")
async def optimize(
    request: OptimizeRequest, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sophisticated optimization endpoint using Synapse Core prompt architecture
    """
    start_time = time.time()
    
    prompt_create = PromptCreate(
        user_id=current_user.id,
        prompt_type="optimize",
        content=request.prompt,
        parameters=request.parameters or {}
    )
    db_prompt = create_prompt(db, prompt_create)
    
    update_prompt_status(db, db_prompt.id, "processing")
    
    try:
        builder = SynapsePromptBuilder()
        
        prompt_data = PromptData(
            user_goal=request.prompt,
            domain_knowledge=request.domain_knowledge or "",
            role=request.role or "professional assistant",
            tone=request.tone or "helpful and analytical", 
            task_description=request.task_description or f"Address the following request: {request.prompt}",
            deliverable_format=request.deliverable_format or "markdown",
            available_tools=request.available_tools or [],
            constraints=request.constraints or [],
            word_limit=request.word_limit,
            additional_context=request.parameters or {}
        )
        
        # Step 1: Build Synapse Core prompt
        synapse_prompt = builder.build(prompt_data)
        stats = builder.get_prompt_stats(synapse_prompt)
        
        # Step 2: Execute Synapse Core prompt with local LLM to get optimized prompt
        engine = get_execution_engine()
        local_model = "phi3:mini"  # Use local model for optimization (matches installed model)
        
        # Create a simpler meta-prompt to instruct the local LLM
        optimization_instruction = f"""You are an expert prompt engineer. Create a detailed, optimized prompt for the following task:

Task: {request.prompt}
Role: {prompt_data.role}
Context: {request.task_description or 'General task enhancement'}

Create a specific, actionable prompt that will produce excellent results. Include clear instructions, context, and desired output format. Output only the optimized prompt, nothing else."""

        # Execute with local LLM (Ollama) to get optimized prompt
        optimized_prompt = ""
        try:
            print(f"Executing Synapse Core prompt with local model: {local_model}")
            
            # Use Ollama directly instead of the execution engine for better control
            import httpx
            async with httpx.AsyncClient(timeout=60.0) as client:  # Increase timeout
                payload = {
                    "model": local_model,
                    "prompt": optimization_instruction,
                    "stream": False  # Use non-streaming for simplicity and reliability
                }
                
                print(f"DEBUG: Sending request to Ollama with payload: {payload['model']}")
                response = await client.post("http://localhost:11434/api/generate", json=payload)
                
                print(f"DEBUG: Ollama response status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    optimized_prompt = result.get("response", "")
                    print(f"DEBUG: Raw Ollama response keys: {list(result.keys())}")
                    print(f"DEBUG: Full Ollama response: {result}")
                    print(f"DEBUG: Collected optimized prompt: '{optimized_prompt[:200]}...'")
                else:
                    error_text = await response.atext()
                    print(f"Ollama API error: {response.status_code} - {error_text}")
                    optimized_prompt = ""
            
            if not optimized_prompt.strip():
                print("Warning: Empty response from local LLM, using fallback")
                optimized_prompt = f"Create a detailed, specific prompt to {request.prompt.lower()}. Include clear instructions, context, and desired output format."
            else:
                print(f"Successfully generated optimized prompt ({len(optimized_prompt)} chars)")
            
        except Exception as e:
            print(f"Error: Local LLM optimization failed: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            optimized_prompt = f"Create a detailed, specific prompt to {request.prompt.lower()}. Include clear instructions, context, and desired output format."
        
        # Step 3: Route optimized prompt to appropriate API LLM for final execution
        # Determine target model based on task type and power level
        task_type = request.parameters.get("task_type", "default")
        power_level = request.parameters.get("power_level", "standard")
        
        # Map to actual model
        target_model = select_model(power_level, task_type)
        
        # Execute the optimized prompt with the target API LLM
        final_output = ""
        try:
            print(f"Executing optimized prompt with target model: {target_model}")
            print(f"DEBUG: optimized_prompt variable content: '{optimized_prompt[:300]}...'")
            
            final_streaming_response = await engine.execute_with_streaming(
                model=target_model,
                prompt=optimized_prompt,  # Use the optimized prompt from local LLM
                parameters={"temperature": 0.7, "max_tokens": 4000}
            )
            
            # Collect the full response from the target API LLM
            print(f"DEBUG: About to collect streaming response from {target_model}")
            print(f"DEBUG: Optimized prompt being sent: '{optimized_prompt[:200]}...')")
            final_output = await collect_streaming_response(final_streaming_response)
            print(f"DEBUG: Collected final output: '{final_output[:200]}...'")
            print(f"DEBUG: Final output length: {len(final_output)}")
            
            if not final_output.strip():
                print("Warning: Empty response from target API LLM")
                final_output = f"The API model {target_model} was unable to generate a response. This may be because the API keys are not configured or the model is not accessible."
            else:
                print(f"Successfully generated final output ({len(final_output)} chars)")
            
        except Exception as e:
            print(f"Error: API LLM execution failed: {e}")
            final_output = f"Unable to generate final output with {target_model}. Error: {str(e)}"
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        response_create = ResponseCreate(
            prompt_id=db_prompt.id,
            user_id=current_user.id,
            response_type="optimization",
            content={
                "synapse_core": synapse_prompt,
                "optimized_prompt": optimized_prompt,
                "final_output": final_output,
                "target_model": target_model,
                "optimization_model": local_model,
                "prompt_stats": stats,
                "original_request": request.prompt
            },
            response_metadata={
                "builder_version": "1.0",
                "processing_time_ms": execution_time_ms,
                "task_type": task_type,
                "power_level": power_level
            },
            execution_time_ms=execution_time_ms,
            status_code=200
        )
        db_response = create_response(db, response_create)
        
        update_prompt_status(db, db_prompt.id, "completed", datetime.utcnow())
        
        return {
            "status": "ok",
            "message": "Full optimization pipeline completed successfully",
            "task_id": f"opt_{db_prompt.id}",
            "prompt_id": db_prompt.id,
            "response_id": db_response.id,
            "synapse_core": synapse_prompt,
            "synapse_prompt": optimized_prompt,  # This is what frontend expects
            "final_output": final_output,
            "target_model": target_model,
            "optimization_model": local_model,
            "prompt_stats": stats,
            "original_request": request.prompt,
            "execution_time_ms": execution_time_ms
        }
        
    except Exception as e:
        update_prompt_status(db, db_prompt.id, "failed")
        
        response_create = ResponseCreate(
            prompt_id=db_prompt.id,
            user_id=current_user.id,
            response_type="error",
            content={"error": str(e)},
            status_code=500,
            error_message=str(e)
        )
        create_response(db, response_create)
        
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")

@app.post("/execute")
async def execute(
    request: ExecuteRequest, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Execute endpoint with sophisticated LLM routing and streaming responses.
    
    This endpoint implements the core execution logic for the Synapse AI application,
    intelligently selecting the optimal Large Language Model and streaming responses.
    """
    start_time = time.time()
    
    prompt_create = PromptCreate(
        user_id=current_user.id,
        prompt_type="execute",
        content=request.prompt,
        parameters={
            "action": request.action,
            "power_level": request.power_level,
            "task_type": request.task_type or "default",
            "payload": request.payload or {}
        }
    )
    db_prompt = create_prompt(db, prompt_create)
    
    update_prompt_status(db, db_prompt.id, "processing")
    
    try:
        validation = validate_routing_request(request.power_level, request.task_type or "default")
        selected_model = select_model(request.power_level, request.task_type or "default")
        
        engine = get_execution_engine()
        execution_params = request.payload or {}
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        response_create = ResponseCreate(
            prompt_id=db_prompt.id,
            user_id=current_user.id,
            response_type="execution",
            content={
                "model_used": selected_model,
                "task_id": request.task_id,
                "action": request.action,
                "streaming": True
            },
            response_metadata={
                "power_level": request.power_level,
                "task_type": request.task_type or "default",
                "validation": validation,
                "execution_params": execution_params
            },
            execution_time_ms=execution_time_ms,
            status_code=200
        )
        db_response = create_response(db, response_create)
        
        update_prompt_status(db, db_prompt.id, "completed", datetime.utcnow())
        
        streaming_response = await engine.execute_with_streaming(
            model=selected_model,
            prompt=request.prompt,
            parameters=execution_params
        )
        
        streaming_response.headers["X-Prompt-ID"] = str(db_prompt.id)
        streaming_response.headers["X-Response-ID"] = str(db_response.id)
        
        return streaming_response
        
    except Exception as e:
        update_prompt_status(db, db_prompt.id, "failed")
        
        response_create = ResponseCreate(
            prompt_id=db_prompt.id,
            user_id=current_user.id,
            response_type="error",
            content={"error": str(e)},
            status_code=500,
            error_message=str(e)
        )
        create_response(db, response_create)
        
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")

@app.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics for monitoring and debugging."""
    engine = get_execution_engine()
    stats = await engine.get_cache_stats()
    local_mode_info = engine.get_local_mode_info()
    return {
        "status": "ok",
        "message": "Cache statistics retrieved successfully",
        "cache_stats": stats,
        "local_mode": local_mode_info
    }

@app.post("/cache/clear")
async def clear_cache():
    """Clear the response cache."""
    engine = get_execution_engine()
    engine.clear_cache()
    return {
        "status": "ok",
        "message": "Cache cleared successfully"
    }

@app.get("/local-mode/status")
async def get_local_mode_status():
    """Get local mode status and configuration."""
    engine = get_execution_engine()
    local_mode_info = engine.get_local_mode_info()
    
    wrapper_status = "unknown"
    if local_mode_info["enabled"]:
        try:
            import requests
            response = requests.get(f"{local_mode_info['wrapper_url']}/health", timeout=5)
            if response.status_code == 200:
                wrapper_status = "healthy"
            else:
                wrapper_status = f"error_{response.status_code}"
        except Exception as e:
            wrapper_status = f"unreachable: {str(e)}"
    
    return {
        "status": "ok",
        "local_mode": {
            **local_mode_info,
            "wrapper_status": wrapper_status
        }
    }

@app.post("/local-mode/toggle")
async def toggle_local_mode():
    """Toggle local mode on/off (for development/testing)."""
    engine = get_execution_engine()
    current_status = engine.is_local_mode_enabled()
    
    engine.local_mode_enabled = not current_status
    
    return {
        "status": "ok",
        "message": f"Local mode {'enabled' if engine.local_mode_enabled else 'disabled'}",
        "local_mode": engine.get_local_mode_info()
    }

@app.post("/feedback")
async def feedback(
    request: FeedbackRequest, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Feedback endpoint for collecting user feedback
    """
    try:
        feedback_create = FeedbackCreate(
            response_id=int(request.response_id),
            user_id=current_user.id,
            rating=request.rating,
            comments=request.comments
        )
        db_feedback = create_feedback(db, feedback_create)
        
        return {
            "status": "ok",
            "message": "Feedback received and stored successfully",
            "response_id": request.response_id,
            "rating": request.rating,
            "feedback_id": db_feedback.id,
            "processed_at": db_feedback.created_at.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store feedback: {str(e)}")

@app.get("/users/{user_id}/prompts")
async def get_user_prompt_history(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get user's prompt history with pagination
    """
    try:
        prompts = get_user_prompts(db, user_id, skip, limit)
        return {
            "status": "ok",
            "message": f"Retrieved {len(prompts)} prompts for user {user_id}",
            "user_id": user_id,
            "prompts": [PromptResponse.from_orm(prompt) for prompt in prompts],
            "pagination": {
                "skip": skip,
                "limit": limit,
                "count": len(prompts)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve prompt history: {str(e)}")

@app.get("/prompts/{prompt_id}/responses")
async def get_prompt_responses_endpoint(prompt_id: int, db: Session = Depends(get_db)):
    """
    Get all responses for a specific prompt
    """
    try:
        responses = get_prompt_responses(db, prompt_id)
        return {
            "status": "ok",
            "message": f"Retrieved {len(responses)} responses for prompt {prompt_id}",
            "prompt_id": prompt_id,
            "responses": [ResponseResponse.from_orm(response) for response in responses]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve prompt responses: {str(e)}")

async def send_welcome_email(email: str, name: str):
    """Send welcome email to new user."""
    sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
    if not sendgrid_api_key:
        print(f"Warning: Cannot send welcome email to {email} - SendGrid API key not configured")
        return
    
    try:
        sg = sendgrid.SendGridAPIClient(api_key=sendgrid_api_key)
        
        message = Mail(
            from_email='noreply@synapse-ai.com',
            to_emails=email,
            subject='Welcome to Synapse AI!',
            html_content=f'''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h1 style="color: #6366f1;">Welcome to Synapse AI, {name}!</h1>
                <p>Thank you for joining Synapse AI. We're excited to help you transform your ideas into expert prompts.</p>
                <p>Here's what you can do with Synapse AI:</p>
                <ul>
                    <li>Use the power level selector to choose the right AI model for your task</li>
                    <li>Monitor your credit usage and upgrade your plan as needed</li>
                    <li>View your results in organized tabs for easy comparison</li>
                </ul>
                <p>Get started by logging into your workspace and exploring the features!</p>
                <p>Best regards,<br>The Synapse AI Team</p>
            </div>
            '''
        )
        
        response = sg.send(message)
        print(f"Welcome email sent to {email} - Status: {response.status_code}")
        
    except Exception as e:
        print(f"Error sending welcome email to {email}: {str(e)}")

async def send_password_reset_email(email: str, reset_token: str):
    """Send password reset email."""
    sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
    if not sendgrid_api_key:
        print(f"Warning: Cannot send password reset email to {email} - SendGrid API key not configured")
        return
    
    try:
        sg = sendgrid.SendGridAPIClient(api_key=sendgrid_api_key)
        
        reset_url = f"{os.getenv('CORS_ORIGIN_URL', 'http://localhost:5173')}/reset-password?token={reset_token}"
        
        message = Mail(
            from_email='noreply@synapse-ai.com',
            to_emails=email,
            subject='Reset Your Synapse AI Password',
            html_content=f'''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h1 style="color: #6366f1;">Reset Your Password</h1>
                <p>You requested to reset your password for your Synapse AI account.</p>
                <p>Click the link below to reset your password:</p>
                <p><a href="{reset_url}" style="background-color: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Reset Password</a></p>
                <p>This link will expire in 1 hour for security reasons.</p>
                <p>If you didn't request this password reset, please ignore this email.</p>
                <p>Best regards,<br>The Synapse AI Team</p>
            </div>
            '''
        )
        
        response = sg.send(message)
        print(f"Password reset email sent to {email} - Status: {response.status_code}")
        
    except Exception as e:
        print(f"Error sending password reset email to {email}: {str(e)}")

@app.post("/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Send password reset email."""
    user = get_user_by_email(db, request.email)
    if not user:
        return {"message": "If the email exists, a password reset link has been sent"}
    
    reset_token = create_access_token(
        data={"sub": user.id, "type": "password_reset"}, 
        expires_delta=timedelta(hours=1)
    )
    
    await send_password_reset_email(user.email, reset_token)
    
    return {"message": "If the email exists, a password reset link has been sent"}

@app.post("/auth/reset-password")
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using token."""
    try:
        from app.auth import verify_token
        payload = verify_token(request.token)
        
        if payload.get("type") != "password_reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )
        
        new_password_hash = hash_password(request.new_password)
        updated_user = update_user_password(db, user_id, new_password_hash)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {"message": "Password reset successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    if not webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook secret not configured"
        )
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload"
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature"
        )
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        user_id = session.get('metadata', {}).get('user_id')
        if not user_id:
            print(f"Warning: No user_id in session metadata: {session.get('id')}")
            return {"status": "ok"}
        
        if session.get('mode') == 'subscription':
            plan_id = session.get('metadata', {}).get('plan_id')
            if plan_id:
                from app.database import get_user_by_id, update_user_subscription
                user = get_user_by_id(db, user_id)
                if user:
                    update_user_subscription(db, user_id, plan_id)
                    print(f"Updated user {user_id} subscription to {plan_id}")
                    
                    create_billing_record(db, {
                        'user_id': user_id,
                        'amount': session.get('amount_total', 0) / 100,
                        'currency': session.get('currency', 'usd'),
                        'description': f'Subscription: {plan_id}',
                        'stripe_session_id': session.get('id'),
                        'status': 'completed'
                    })
        
        elif session.get('mode') == 'payment':
            credits = session.get('metadata', {}).get('credits')
            if credits:
                from app.database import get_user_by_id, add_user_credits
                user = get_user_by_id(db, user_id)
                if user:
                    add_user_credits(db, user_id, int(credits))
                    print(f"Added {credits} credits to user {user_id}")
                    
                    create_billing_record(db, {
                        'user_id': user_id,
                        'amount': session.get('amount_total', 0) / 100,
                        'currency': session.get('currency', 'usd'),
                        'description': f'Credits: {credits}',
                        'stripe_session_id': session.get('id'),
                        'status': 'completed'
                    })
    
    return {"status": "ok"}
