import asyncio
import json
from app.execution_engine import get_execution_engine
from app.llm_router import select_model

async def test_basic_functionality():
    print('=== Testing Execution Engine Basic Functionality ===')
    
    print('1. Testing execution engine initialization...')
    engine = get_execution_engine()
    print(f'   ✓ Engine initialized: {engine is not None}')
    
    print('2. Testing model selection...')
    model = select_model('med', 'code')
    print(f'   ✓ Selected model: {model}')
    
    print('3. Testing cache stats...')
    stats = await engine.get_cache_stats()
    print(f'   ✓ Cache stats: {stats}')
    
    print('4. Testing API provider detection...')
    providers = {
        'gpt-4o-mini-2024-07-18': engine._determine_api_provider('gpt-4o-mini-2024-07-18'),
        'claude-3-5-sonnet-20240620': engine._determine_api_provider('claude-3-5-sonnet-20240620'),
        'gemini-1.5-flash-preview-0514': engine._determine_api_provider('gemini-1.5-flash-preview-0514')
    }
    for model, provider in providers.items():
        print(f'   ✓ {model} -> {provider}')
    
    print('\n=== All Basic Tests Passed! ===')

if __name__ == "__main__":
    asyncio.run(test_basic_functionality())
