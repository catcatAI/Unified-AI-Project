@echo off
:: Smart Fix Batch Script
:: Used to execute complete smart fix process

setlocal enabledelayedexpansion

:: Set project root directory
set "PROJECT_ROOT=%~dp0.."
set "PYTHON_SCRIPT=%PROJECT_ROOT%\apps\backend\scripts\execute_smart_fix.py"

echo ================================
echo   Unified AI Project Smart Fix Tool
echo ================================

:: Check Python environment
echo Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python environment not found, please install Python 3.8 or higher
    pause
    exit /b 1
)

:: Check virtual environment
echo Checking virtual environment...
if exist "%PROJECT_ROOT%\apps\backend\venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call "%PROJECT_ROOT%\apps\backend\venv\Scripts\activate.bat"
) else (
    echo Warning: Virtual environment not found, using system Python
)

:: Check if execution script exists
if not exist "%PYTHON_SCRIPT%" (
    echo Error: Execution script does not exist - %PYTHON_SCRIPT%
    pause
    exit /b 1
)

:: Run smart fix executor
echo Starting smart fix process...
echo.

python "%PYTHON_SCRIPT%"

if errorlevel 1 (
    echo.
    echo Smart fix process execution failed
    pause
    exit /b 1
) else (
    echo.
    echo Smart fix process completed successfully
)

echo.
echo Press any key to exit...
pause >nul