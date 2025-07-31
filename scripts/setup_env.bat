@echo off
setlocal

:: Check if venv directory exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo Error: Failed to create virtual environment. Make sure Python is installed and in your PATH.
        goto :eof
    )
)

echo Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Error: Failed to activate virtual environment.
    goto :eof
)

echo Installing dependencies from requirements.txt...
pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies.
    goto :eof
)

echo Virtual environment setup complete.
echo To activate it in the future, run: .\venv\Scripts\activate.bat
endlocal
