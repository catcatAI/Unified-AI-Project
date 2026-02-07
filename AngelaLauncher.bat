@echo off
TITLE Angela AI Launcher
SETLOCAL EnableDelayedExpansion

echo ======================================================
echo 🌟 Angela AI One-Click Launcher v6.1.0
echo ======================================================

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.9+ 
    echo Visit: https://www.python.org/
    pause
    exit /b 1
)

:: Check if already installed (simplistic check)
if not exist "apps\backend\src\services\main_api_server.py" (
    echo [INFO] First time setup detected. Running installer...
    python install_angela.py --launch
    if %errorlevel% neq 0 (
        echo [ERROR] Installation failed.
        pause
        exit /b 1
    )
    exit /b 0
)

:: Run Angela in User Mode by default
echo [INFO] Starting Angela AI in User Mode...
python run_angela.py --mode user

if %errorlevel% neq 0 (
    echo [WARNING] Run failed. Trying to fix dependencies...
    python install_angela.py --skip-clone
    echo [INFO] Retrying...
    python run_angela.py --mode user
)

pause
