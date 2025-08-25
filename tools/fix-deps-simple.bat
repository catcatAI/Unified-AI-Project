@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Fix Dependencies (Simple)
color 0A

echo ==========================================
echo   Unified AI Project - Fix Dependencies  
echo ==========================================
echo.

:: Setup Python environment
cd apps\backend

echo [INFO] Activating Python virtual environment...
call venv\Scripts\activate.bat

echo [INFO] Installing core dependencies from requirements.txt...
pip install -r requirements.txt --force-reinstall

echo [INFO] Installing development dependencies from requirements-dev.txt...
pip install -r requirements-dev.txt --force-reinstall

echo [INFO] Verifying key dependencies...
python -c "import openai; print('[OK] openai module available')"

python -c "import msgpack; print('[OK] msgpack module available')"

echo.
echo [SUCCESS] Dependency installation completed!
echo.
echo Please run your tests again to verify the fix.
echo.
pause
cd ..\..
exit /b 0