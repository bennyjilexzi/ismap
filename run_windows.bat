@echo off
echo.
echo ==========================================
echo    ISMAP Starter Script
echo ==========================================
echo.

:: 1. Check for Virtual Environment
if not exist venv\Scripts\activate (
    echo [ERROR] Virtual environment not found. Please run 'install_windows.bat' first.
    pause
    exit /b 1
)

:: 2. Activate venv
echo [1/2] Activating environment...
call venv\Scripts\activate

:: 3. Set Environment Variables
echo [2/2] Loading configuration...
set FLASK_APP=app.py
set PORT=5000
set JWT_SECRET_KEY=supersecretkey-please-change-it-for-production-use

:: 4. Run Backend
echo.
echo [STATUS] Starting ISMAP Backend...
echo          Accessible at: http://localhost:5000
echo.
python app.py
pause
