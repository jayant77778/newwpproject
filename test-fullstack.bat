@echo off
REM WhatsApp Order System - Full Stack Test Script
REM This script starts both backend and frontend for testing

echo.
echo ========================================
echo WhatsApp Order System - Full Stack Test
echo ========================================
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo [1/8] Checking prerequisites...
echo ✅ Node.js: 
node --version
echo ✅ Python: 
python --version

echo.
echo [2/8] Setting up backend environment...
cd backend

REM Activate virtual environment
if exist "venv" (
    call venv\Scripts\activate.bat
    echo ✅ Virtual environment activated
) else (
    echo ❌ Virtual environment not found. Run start.bat first.
    pause
    exit /b 1
)

REM Check if dependencies are installed
python -c "import fastapi" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing backend dependencies...
    pip install -r requirements.txt
)

echo.
echo [3/8] Testing backend database...
python -c "from app.database import test_connection; print('Database test:', test_connection())"

echo.
echo [4/8] Starting backend server...
start "Backend API" cmd /k "cd /d \"%CD%\" && python main.py"

REM Wait for backend to start
echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

echo.
echo [5/8] Testing backend API...
curl -s http://localhost:8000/ >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Backend API is running
) else (
    echo ❌ Backend API not responding
)

echo.
echo [6/8] Setting up frontend...
cd ..\frontend

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing frontend dependencies...
    npm install
)

echo.
echo [7/8] Starting frontend development server...
start "Frontend React App" cmd /k "cd /d \"%CD%\" && npm start"

echo.
echo [8/8] Opening applications in browser...
timeout /t 3 /nobreak >nul

REM Open applications in browser
start http://localhost:3000
timeout /t 2 /nobreak >nul
start http://localhost:8000/docs

echo.
echo ========================================
echo Full Stack System Started Successfully!
echo ========================================
echo.
echo Applications:
echo 🌐 Frontend (React): http://localhost:3000
echo 🔧 Backend API: http://localhost:8000
echo 📚 API Documentation: http://localhost:8000/docs
echo 💚 Health Check: http://localhost:8000/api/health
echo.
echo Testing URLs:
echo - Registration: http://localhost:3000 (register new user)
echo - Orders: http://localhost:3000/orders
echo - Summaries: http://localhost:3000/summaries  
echo - Export: http://localhost:3000/export
echo.
echo To stop the system:
echo 1. Close both command windows
echo 2. Or press Ctrl+C in each window
echo.
echo Happy testing! 🚀
echo.

pause
