@echo off
REM Production startup script for Synapse AI Backend (Windows)
echo Starting Synapse AI Backend...

REM Check if .env file exists
if not exist ".env" (
    echo ❌ Error: .env file not found!
    echo Please copy .env.example to .env and configure your environment variables.
    pause
    exit /b 1
)

REM Initialize database if needed
echo Initializing database...
python -c "from app.database import engine, Base; Base.metadata.create_all(bind=engine); print('✅ Database initialized')"

REM Start the server
echo 🚀 Starting server on http://0.0.0.0:8000
echo 📚 API docs will be available at http://localhost:8000/docs
echo.

REM Check if poetry is available
poetry --version >nul 2>&1
if %errorlevel% == 0 (
    echo Using Poetry...
    poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
) else (
    echo Using direct Python...
    uvicorn app.main:app --host 0.0.0.0 --port 8000
)