@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - AI Runner
color 0E

echo ==========================================
echo   Unified AI Project - AI Runner
echo ==========================================
echo.

:: This script is designed for AI agents to run automated tasks
:: It provides headless execution of common development operations

:: Check if a command is provided
if "%1"=="" (
    echo [ERROR] No command provided
    echo.
    echo Usage: ai-runner.bat [command] [options]
    echo.
    echo Available commands:
    echo   setup     - Setup development environment
    echo   start     - Start development servers
    echo   test      - Run tests
    echo   train     - Setup training environment
    echo   health    - Run health check
    echo   clean     - Clean git status
    echo.
    exit /b 1
)

:: Process commands
if "%1"=="setup" goto setup_env
if "%1"=="start" goto start_dev
if "%1"=="test" goto run_tests
if "%1"=="train" goto setup_training
if "%1"=="health" goto health_check
if "%1"=="clean" goto clean_git

echo [ERROR] Unknown command '%1'
exit /b 1

:: Setup Environment Function
:setup_env
echo [INFO] Setting up environment...
echo.

:: Check environment
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not installed
    exit /b 1
)

where python >nul 2>&1  
if %errorlevel% neq 0 (
    echo [ERROR] Python not installed
    exit /b 1
)

echo [OK] Environment ready

:: Check pnpm
where pnpm >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing pnpm...
    npm install -g pnpm >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install pnpm
        exit /b 1
    )
)

:: Install dependencies if needed
if not exist "node_modules" (
    echo [INFO] Installing Node.js dependencies...
    pnpm install >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies
        exit /b 1
    )
)

:: Setup Python environment
cd apps\backend
if not exist "venv" (
    echo [INFO] Creating Python virtual environment...
    python -m venv venv >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        cd ..\..
        exit /b 1
    )
)

echo [INFO] Installing Python packages...
call venv\Scripts\activate.bat >nul 2>&1
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt >nul 2>&1
pip install -r requirements-dev.txt >nul 2>&1
cd ..\..

echo [SUCCESS] Environment setup completed!
exit /b 0

:: Start Development Function
:start_dev
echo [INFO] Starting development environment...
echo.

if "%2"=="backend" (
    :: Start backend only
    cd apps\backend
    call venv\Scripts\activate.bat >nul 2>&1
    start "Backend API" /min cmd /c "uvicorn src.services.main_api_server:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1"
    cd ..\..
    echo [SUCCESS] Backend services started in background
    exit /b 0
) else if "%2"=="frontend" (
    :: Start frontend only
    start "Frontend" /min cmd /c "pnpm --filter frontend-dashboard dev > frontend.log 2>&1"
    echo [SUCCESS] Frontend service started in background
    exit /b 0
) else (
    :: Start both
    cd apps\backend
    call venv\Scripts\activate.bat >nul 2>&1
    start "Backend API" /min cmd /c "uvicorn src.services.main_api_server:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1"
    cd ..\..
    start "Frontend" /min cmd /c "pnpm --filter frontend-dashboard dev > frontend.log 2>&1"
    echo [SUCCESS] Full development environment started in background
    exit /b 0
)

:: Run Tests Function
:run_tests
echo [INFO] Running tests...
echo.

if "%2"=="backend" (
    cd apps\backend
    call venv\Scripts\activate.bat >nul 2>&1
    pytest --tb=short -v > test_results.log 2>&1
    cd ..\..
    echo [SUCCESS] Backend tests completed. Results in test_results.log
    exit /b 0
) else if "%2"=="frontend" (
    pnpm --filter frontend-dashboard test --passWithNoTests > test_results.log 2>&1
    echo [SUCCESS] Frontend tests completed. Results in test_results.log
    exit /b 0
) else (
    :: Run all tests
    cd apps\backend
    call venv\Scripts\activate.bat >nul 2>&1
    pytest --tb=short -v > backend_test_results.log 2>&1
    cd ..\..
    pnpm --filter frontend-dashboard test --passWithNoTests > frontend_test_results.log 2>&1
    echo [SUCCESS] All tests completed. Results in backend_test_results.log and frontend_test_results.log
    exit /b 0
)

:: Setup Training Function
:setup_training
echo [INFO] Setting up training environment...
echo.

if exist "tools\setup-training.bat" (
    call tools\setup-training.bat > training_setup.log 2>&1
    echo [SUCCESS] Training environment setup completed. Log in training_setup.log
    exit /b 0
) else (
    echo [ERROR] setup-training.bat not found
    exit /b 1
)

:: Health Check Function
:health_check
echo [INFO] Running health check...
echo.

if exist "tools\health-check.bat" (
    call tools\health-check.bat > health_check.log 2>&1
    echo [SUCCESS] Health check completed. Results in health_check.log
    exit /b 0
) else (
    echo [ERROR] health-check.bat not found
    exit /b 1
)

:: Clean Git Function
:clean_git
echo [INFO] Cleaning git status...
echo.

if exist "tools\safe-git-cleanup.bat" (
    call tools\safe-git-cleanup.bat > git_clean.log 2>&1
    echo [SUCCESS] Git status cleaned. Log in git_clean.log
    exit /b 0
) else (
    echo [ERROR] safe-git-cleanup.bat not found
    exit /b 1
)