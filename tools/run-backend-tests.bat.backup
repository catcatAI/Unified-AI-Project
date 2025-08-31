@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Run Backend Tests
color 0A

echo ==========================================
echo   Unified AI Project - Run Backend Tests  
echo ==========================================
echo.

:: Setup Python environment
cd apps\backend

echo [INFO] Activating Python virtual environment...
call venv\Scripts\activate.bat

echo [INFO] Setting PYTHONPATH...
set PYTHONPATH=%cd%\src;%PYTHONPATH%

echo [INFO] Running backend tests...
pytest --tb=short -v

echo.
echo [INFO] Backend tests completed.
pause
cd ..\..
exit /b 0