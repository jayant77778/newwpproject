@echo off
REM WhatsApp Order Backend - Windows Quick Start Script
REM This script sets up the development environment on Windows

echo.
echo ========================================
echo WhatsApp Order Backend - Quick Start
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo [1/7] Checking Python installation...
python --version

REM Check if pip is available
echo [2/7] Checking pip...
pip --version

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo [3/7] Creating virtual environment...
    python -m venv venv
) else (
    echo [3/7] Virtual environment already exists
)

REM Activate virtual environment
echo [4/7] Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo [5/7] Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

REM Copy environment file if it doesn't exist
if not exist ".env" (
    echo [6/7] Creating environment file...
    copy .env.example .env
    echo.
    echo WARNING: Please edit .env file with your configuration
    echo.
) else (
    echo [6/7] Environment file already exists
)

REM Create necessary directories
echo [7/7] Creating directories...
if not exist "logs" mkdir logs
if not exist "exports" mkdir exports
if not exist "static" mkdir static
if not exist "whatsapp_sessions" mkdir whatsapp_sessions
if not exist "uploads" mkdir uploads

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file with your configuration
echo 2. Install and start Redis server
echo 3. Set up PostgreSQL (optional, SQLite works for development)
echo 4. Run: python startup.py --check-only
echo 5. Start the server: python main.py
echo.
echo Development URLs:
echo - API: http://localhost:8000
echo - Docs: http://localhost:8000/docs
echo - Health: http://localhost:8000/api/health
echo.
echo For production deployment, see DEPLOYMENT.md
echo.

pause
