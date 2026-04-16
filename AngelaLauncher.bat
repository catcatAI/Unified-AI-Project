@echo off
TITLE Angela AI Launcher
SETLOCAL EnableDelayedExpansion

echo ======================================================
echo 🌟 Angela AI One-Click Launcher v6.2.1
echo ======================================================

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.9+ 
    echo Visit: https://www.python.org/
    pause
    exit /b 1
)

:: Check if code is present
if not exist "apps\backend\src\services\main_api_server.py" (
    echo [INFO] First time setup or incomplete files detected.
    echo [INFO] Running installer to fix environment...
    python install_angela.py --launch
    if %errorlevel% neq 0 (
        echo [ERROR] Installation failed. Please check logs.
        pause
        exit /b 1
    )
    exit /b 0
)

:: Ensure dependencies are present
echo [INFO] Environment check...
python -c "import fastapi, uvicorn, psutil, yaml" >nul 2>&1
if !errorlevel! neq 0 (
    echo [WARNING] Missing dependencies detected. Running auto-repair...
    python install_angela.py --skip-clone
    if !errorlevel! neq 0 (
        echo [ERROR] Auto-repair failed.
        pause
        exit /b 1
    )
)

:: Run Angela in User Mode by default
echo [INFO] Starting Angela AI in User Mode...
python run_angela.py --mode user

if %errorlevel% neq 0 (
    echo [WARNING] Run failed. Trying a full repair...
    python install_angela.py --skip-clone
    echo [INFO] Retrying launch...
    python run_angela.py --mode user
)

if %errorlevel% neq 0 (
    echo [ERROR] Angela AI crashed. Please check logs/launcher.log
    pause
)

pause
