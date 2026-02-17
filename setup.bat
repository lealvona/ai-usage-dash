@echo off
REM Setup script for AI Usage Dashboard (Windows)

echo 🤖 AI Usage Dashboard - Setup Script
echo ====================================

REM Check Python version
echo Checking Python version...
python --version
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)
echo.

REM Create necessary directories
echo Creating directories...
if not exist storage mkdir storage
if not exist templates mkdir templates
echo.

REM Copy environment file if it doesn't exist
if not exist .env (
    echo.
    echo Creating .env file...
    copy .env.example .env
    echo.
    echo ⚠️  Please edit .env file with your API keys before running the application.
) else (
    echo.
    echo ✓ .env file already exists
)
echo.

echo ====================================
echo Setup complete!
echo.
echo Next steps:
echo 1. Edit .env file with your API keys
echo 2. Run: python app.py
echo 3. Open: http://localhost:5000
echo.
echo Or run the demo: python demo/demo_usage.py
echo.

pause
