@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Recreate Virtual Environment
color 0A

echo ==========================================
echo   Unified AI Project - Recreate Venv  
echo ==========================================
echo.

:: Setup Python environment
cd apps\backend

echo [INFO] Removing existing virtual environment...
if exist "venv" (
    rmdir /s /q venv
    echo [INFO] Existing venv removed
) else (
    echo [INFO] No existing venv found
)

echo [INFO] Creating new Python virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment
    cd ..\..
    pause
    exit /b 1
)

echo [INFO] Activating Python virtual environment...
call venv\Scripts\activate.bat

echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

echo [INFO] Installing core dependencies from requirements.txt...
pip install -r requirements.txt

echo [INFO] Installing development dependencies from requirements-dev.txt...
pip install -r requirements-dev.txt

echo [INFO] Verifying key dependencies...
python -c "import openai; print('[OK] openai module available')"
python -c "import msgpack; print('[OK] msgpack module available')"

echo.
echo [SUCCESS] Virtual environment recreated and dependencies installed!
echo.
echo Please run your tests again to verify the fix.
echo.
pause
cd ..\..
exit /b 0