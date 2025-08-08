#!/bin/bash

# Production startup script for Synapse AI Backend
echo "Starting Synapse AI Backend..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "Please copy .env.example to .env and configure your environment variables."
    exit 1
fi

# Check if API keys are configured
source .env
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your_openai_api_key_here" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not configured in .env file"
    echo "Cloud optimization mode requires valid API keys"
fi

# Initialize database if needed
echo "Initializing database..."
python -c "from app.database import engine, Base; Base.metadata.create_all(bind=engine); print('✅ Database initialized')"

# Start the server
echo "🚀 Starting server on http://0.0.0.0:8000"
echo "📚 API docs will be available at http://localhost:8000/docs"
echo ""

if command -v poetry &> /dev/null; then
    echo "Using Poetry..."
    poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
else
    echo "Using direct Python..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000
fi