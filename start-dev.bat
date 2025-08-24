@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Development Environment
color 0A

echo ==========================================
echo   Unified AI Project - Dev Environment  
echo ==========================================
echo.

:: Basic environment check
echo [INFO] Checking environment...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not installed
    echo [INFO] Download from: https://nodejs.org/
    echo.
    pause
    exit /b 1
)

where python >nul 2>&1  
if %errorlevel% neq 0 (
    echo [ERROR] Python not installed
    echo [INFO] Download from: https://python.org/
    echo.
    pause
    exit /b 1
)

echo [OK] Environment ready
echo.

:: Check pnpm
where pnpm >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing pnpm...
    npm install -g pnpm
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install pnpm
        pause
        exit /b 1
    )
)

:: Install dependencies if needed
if not exist "node_modules" (
    echo [INFO] Installing Node.js dependencies...
    pnpm install
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
)

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

echo [INFO] Installing Python packages...
call venv\Scripts\activate.bat
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt >nul 2>&1
pip install -r requirements-dev.txt >nul 2>&1
cd ..\..

echo.
echo [SUCCESS] Setup completed!
echo.

:menu
echo Choose an action:
echo.
echo 1. Start Full Development Environment
echo 2. Start Backend Only  
echo 3. Start Frontend Only
echo 4. Run Tests
echo 5. Clean Git Status
echo 6. Exit
echo.

set "choice="
set /p "choice=Enter your choice (1-6): "
if defined choice set "choice=%choice: =%"
if not defined choice goto invalid_choice

if "%choice%"=="1" goto start_all
if "%choice%"=="2" goto start_backend
if "%choice%"=="3" goto start_frontend  
if "%choice%"=="4" goto run_tests
if "%choice%"=="5" goto clean_git
if "%choice%"=="6" goto end

:invalid_choice
echo [ERROR] Invalid choice. Please enter 1-6.
echo.
timeout /t 2 >nul
goto menu

:start_all
echo.
echo Starting full development environment...
echo.
echo Services will be available at:
echo - Backend API: http://localhost:8000
echo - Frontend Dashboard: http://localhost:3000
echo.

start "Backend API" cmd /k "cd /d apps\backend && call venv\Scripts\activate.bat && uvicorn src.services.main_api_server:app --reload --host 0.0.0.0 --port 8000"
start "Frontend" cmd /k "pnpm --filter frontend-dashboard dev"

echo [SUCCESS] Development environment started!
echo Check the opened windows for service status.
echo.
pause
goto menu

:start_backend
echo.
echo Starting backend services only...
echo.
start "Backend API" cmd /k "cd /d apps\backend && call venv\Scripts\activate.bat && uvicorn src.services.main_api_server:app --reload --host 0.0.0.0 --port 8000"

echo [SUCCESS] Backend services started!
echo - API Server: http://localhost:8000
echo.
pause
goto menu

:start_frontend
echo.
echo Starting frontend service only...
echo.
start "Frontend" cmd /k "pnpm --filter frontend-dashboard dev"

echo [SUCCESS] Frontend service started!
echo - Dashboard: http://localhost:3000
echo.
pause
goto menu

:run_tests
echo.
echo Running test suite...
echo.
cd apps\backend
call venv\Scripts\activate.bat
pytest --tb=short -v
cd ..\..
pnpm --filter frontend-dashboard test --passWithNoTests
echo.
echo Tests completed.
pause
goto menu

:clean_git
echo.
echo Cleaning Git status...
echo.
call safe-git-cleanup.bat
echo.
echo Git status cleaned.
pause
goto menu

:end
echo.
echo Thank you for using Unified AI Project!
echo.
pause
exit /b 0