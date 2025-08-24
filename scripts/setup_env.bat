@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

:: Check if venv directory exists
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment. Make sure Python is installed and in your PATH.
        echo [SOLUTION] Download Python from: https://python.org/
        goto :eof
    )
)

echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment.
    goto :eof
)

echo [INFO] Installing dependencies from requirements.txt...
pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    echo [TROUBLESHOOTING]
    echo - Check if requirements.txt exists
    echo - Verify internet connection
    echo - Try running: pip install --upgrade pip
    goto :eof
)

echo [SUCCESS] Virtual environment setup complete.
echo [INFO] To activate it in the future, run: .\venv\Scripts\activate.bat
endlocal
