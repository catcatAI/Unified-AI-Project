@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Quick Dev
color 0A

echo ==========================================
echo   Unified AI Project - Quick Dev Tool
echo ==========================================
echo.

:: Check basic environment
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not installed. Download from: https://nodejs.org/
    pause
    exit /b 1
)

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not installed. Download from: https://python.org/
    pause
    exit /b 1
)

echo [OK] Environment ready
echo.

:menu
echo Quick Actions:
echo.
echo 1. Install Dependencies
echo 2. Start Backend Only
echo 3. Start Frontend Only  
echo 4. Start Full Dev Environment
echo 5. Run Quick Tests
echo 6. Exit
echo.

set "choice="
set /p "choice=Choose (1-6): "
if defined choice set "choice=%choice: =%"
if not defined choice (
    echo [ERROR] No input provided
    timeout /t 2 >nul
    goto menu
)

if "%choice%"=="1" goto install_deps
if "%choice%"=="2" goto start_backend
if "%choice%"=="3" goto start_frontend
if "%choice%"=="4" goto start_all
if "%choice%"=="5" goto quick_test
if "%choice%"=="6" goto exit

echo [ERROR] Invalid choice. Please enter 1-6.
timeout /t 2 >nul
goto menu

:install_deps
echo.
echo [INFO] Installing all dependencies...
echo.

:: Install pnpm if needed
where pnpm >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing pnpm...
    npm install -g pnpm
)

:: Install Node.js dependencies
echo [INFO] Installing Node.js dependencies...
pnpm install

:: Setup Python environment
cd apps\backend
if not exist "venv" (
    echo [INFO] Creating Python virtual environment...
    python -m venv venv
)

echo [INFO] Installing Python dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt >nul 2>&1
pip install -r requirements-dev.txt >nul 2>&1
cd ..\..

echo [SUCCESS] Dependencies installed!
pause
goto menu

:start_backend
echo.
echo [INFO] Starting backend services...
echo - API Server: http://localhost:8000
echo.

start "Backend API" cmd /k "cd /d apps\backend && call venv\Scripts\activate.bat && uvicorn src.services.main_api_server:app --reload --host 0.0.0.0 --port 8000"
echo [SUCCESS] Backend started! Check the opened window.
pause
goto menu

:start_frontend
echo.
echo [INFO] Starting frontend service...
echo - Dashboard: http://localhost:3000
echo.

start "Frontend" cmd /k "pnpm --filter frontend-dashboard dev"
echo [SUCCESS] Frontend started! Check the opened window.
pause
goto menu

:start_all
echo.
echo [INFO] Starting full development environment...
echo.
echo Services will be available at:
echo - Backend API: http://localhost:8000
echo - Frontend Dashboard: http://localhost:3000
echo.

start "Backend API" cmd /k "cd /d apps\backend && call venv\Scripts\activate.bat && uvicorn src.services.main_api_server:app --reload --host 0.0.0.0 --port 8000"
timeout /t 3 >nul
start "Frontend" cmd /k "pnpm --filter frontend-dashboard dev"

echo [SUCCESS] Full environment started! Check the opened windows.
pause
goto menu

:quick_test
echo.
echo [INFO] Running quick component tests...
echo.

cd apps\backend
call venv\Scripts\activate.bat >nul 2>&1
python diagnose_components.py
cd ..\..

echo [SUCCESS] Quick tests completed!
pause
goto menu

:exit
echo.
echo Thank you for using Quick Dev Tool!
exit /b 0