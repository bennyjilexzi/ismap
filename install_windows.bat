@echo off
echo.
echo ==========================================
echo    ISMAP Windows Setup Script
echo ==========================================
echo.

:: 1. Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.9+ from python.org
    pause
    exit /b 1
)

:: 2. Create Virtual Environment
echo [1/4] Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create venv.
    pause
    exit /b 1
)

:: 3. Install Backend Dependencies
echo [2/4] Installing backend dependencies...
call venv\Scripts\activate
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install requirements.
    pause
    exit /b 1
)

:: 4. Check for Node.js (Optional but recommended for dev)
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [SKIP] Node.js not found. Skipping frontend build.
    echo        (Note: The tool will use the pre-built frontend if available)
) else (
    echo [3/4] Installing frontend dependencies...
    cd frontend
    npm install
    echo [4/4] Building frontend...
    npm run build
    cd ..
)

echo.
echo ==========================================
echo    Setup Complete! 
echo    Run 'run_windows.bat' to start ISMAP.
echo ==========================================
pause
