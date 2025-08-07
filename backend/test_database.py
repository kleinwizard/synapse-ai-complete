import asyncio
import json
from app.database import (
    create_tables, get_db, 
    PromptCreate, ResponseCreate, FeedbackCreate,
    create_prompt, create_response, create_feedback,
    get_user_prompts, get_prompt_responses
)
from sqlalchemy.orm import Session

def test_database_operations():
    print('=== Testing Database Operations ===')
    
    print('1. Creating database tables...')
    create_tables()
    print('   ✓ Tables created successfully')
    
    print('2. Testing database session...')
    db_gen = get_db()
    db = next(db_gen)
    print(f'   ✓ Database session created: {db is not None}')
    
    print('3. Testing prompt creation...')
    prompt_data = PromptCreate(
        user_id=1,
        prompt_type="optimize",
        content="Test prompt for optimization",
        parameters={"test": "data"}
    )
    db_prompt = create_prompt(db, prompt_data)
    print(f'   ✓ Prompt created with ID: {db_prompt.id}')
    
    print('4. Testing response creation...')
    response_data = ResponseCreate(
        prompt_id=db_prompt.id,
        user_id=1,
        response_type="optimization",
        content={"result": "optimized prompt"},
        response_metadata={"processing_time": 150}
    )
    db_response = create_response(db, response_data)
    print(f'   ✓ Response created with ID: {db_response.id}')
    
    print('5. Testing feedback creation...')
    feedback_data = FeedbackCreate(
        response_id=db_response.id,
        user_id=1,
        rating=5,
        comments="Great optimization!"
    )
    db_feedback = create_feedback(db, feedback_data)
    print(f'   ✓ Feedback created with ID: {db_feedback.id}')
    
    print('6. Testing data retrieval...')
    user_prompts = get_user_prompts(db, 1)
    print(f'   ✓ Retrieved {len(user_prompts)} prompts for user 1')
    
    prompt_responses = get_prompt_responses(db, db_prompt.id)
    print(f'   ✓ Retrieved {len(prompt_responses)} responses for prompt {db_prompt.id}')
    
    db.close()
    print('\n=== All Database Tests Passed! ===')

if __name__ == "__main__":
    test_database_operations()
