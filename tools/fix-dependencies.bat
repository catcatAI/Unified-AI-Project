@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Fix Dependencies
color 0A

echo ==========================================
echo   Unified AI Project - Fix Dependencies  
echo ==========================================
echo.

:: Setup Python environment
cd apps\backend
if not exist "venv" (
    echo [INFO] Creating Python virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        cd ..\..
        pause
        exit /b 1
    )
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
if %errorlevel% neq 0 (
    echo [ERROR] openai module not available, trying direct install...
    pip install openai
)

python -c "import msgpack; print('[OK] msgpack module available')"
if %errorlevel% neq 0 (
    echo [ERROR] msgpack module not available, trying direct install...
    pip install msgpack
)

echo [INFO] Installing any missing dependencies...
pip install setuptools
pip install wheel

echo.
echo [SUCCESS] Dependency installation completed!
echo.
echo Please run your tests again to verify the fix.
echo.
pause
cd ..\..
exit /b 0