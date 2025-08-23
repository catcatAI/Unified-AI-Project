@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Health Check
color 0C

echo ==========================================
echo   Unified AI Project - Health Check
echo ==========================================
echo.
echo Checking development environment status...
echo.

set "error_count=0"

:: Check Node.js
echo [CHECK 1/6] Node.js Environment
where node >nul 2>&1
if %errorlevel%==0 (
    for /f "tokens=*" %%i in ('node --version') do set node_version=%%i
    echo [OK] Node.js: !node_version!
) else (
    echo [FAIL] Node.js not installed
    echo [INFO] Download from: https://nodejs.org/
    set /a "error_count+=1"
)

:: Check Python
echo.
echo [CHECK 2/6] Python Environment
where python >nul 2>&1
if %errorlevel%==0 (
    for /f "tokens=*" %%i in ('python --version') do set python_version=%%i
    echo [OK] Python: !python_version!
) else (
    echo [FAIL] Python not installed
    echo [INFO] Download from: https://python.org/
    set /a "error_count+=1"
)

:: Check pnpm
echo.
echo [CHECK 3/6] Package Manager
where pnpm >nul 2>&1
if %errorlevel%==0 (
    for /f "tokens=*" %%i in ('pnpm --version') do set pnpm_version=%%i
    echo [OK] pnpm: v!pnpm_version!
) else (
    echo [FAIL] pnpm not installed
    echo [SUGGESTION] Run: npm install -g pnpm
    set /a "error_count+=1"
)

:: Check project dependencies
echo.
echo [CHECK 4/6] Project Dependencies
if exist "node_modules" (
    echo [OK] Node.js dependencies installed
) else (
    echo [FAIL] Node.js dependencies not installed
    echo [SUGGESTION] Run: pnpm install
    set /a "error_count+=1"
)

:: Check Python virtual environment
echo.
echo [CHECK 5/6] Python Environment
if exist "apps\backend\venv" (
    echo [OK] Python virtual environment created
    
    :: Check if Python packages are installed
    echo [INFO] Checking essential Python packages...
    cd apps\backend
    call venv\Scripts\activate.bat >nul 2>&1
    
    :: Check for key packages
    python -c "import fastapi" >nul 2>&1
    if !errorlevel!==0 (
        echo [OK] FastAPI available
    ) else (
        echo [WARNING] FastAPI not found
        set /a "error_count+=1"
    )
    
    python -c "import pytest" >nul 2>&1
    if !errorlevel!==0 (
        echo [OK] pytest available
    ) else (
        echo [WARNING] pytest not found
        set /a "error_count+=1"
    )
    
    if !error_count! gtr 0 (
        echo [SUGGESTION] Run start-dev.bat to install missing packages
    )
    
    cd ..\..
) else (
    echo [FAIL] Python virtual environment not created
    echo [SUGGESTION] Run start-dev.bat for automatic setup
    set /a "error_count+=1"
)

:: Check configuration files
echo.
echo [CHECK 6/6] Configuration Files
if exist "apps\backend\configs\config.yaml" (
    echo [OK] Backend configuration file exists
) else (
    echo [WARNING] Backend configuration file missing
    echo [SUGGESTION] Run start-dev.bat to create default config
)

if exist "package.json" (
    echo [OK] Root package.json exists
) else (
    echo [FAIL] Root package.json missing
    echo [CRITICAL] Project structure may be corrupted
    set /a "error_count+=1"
)

echo.
echo ==========================================
echo    Health Check Results
echo ==========================================
echo.

if !error_count! gtr 0 (
    echo [WARNING] Found !error_count! issue^(s^) that need attention
    echo.
    echo [NEXT STEPS]
    echo 1. Follow the suggestions above to resolve issues
    echo 2. Run start-dev.bat for automatic environment setup
    echo 3. Re-run this health check to verify fixes
    echo.
    echo [COMMON SOLUTIONS]
    echo - Missing Node.js: Download from https://nodejs.org/
    echo - Missing Python: Download from https://python.org/
    echo - Missing pnpm: Run 'npm install -g pnpm'
    echo - Missing dependencies: Run start-dev.bat
) else (
    echo [SUCCESS] All checks passed! Environment is ready
    echo.
    echo [READY TO START DEVELOPMENT]
    echo - Run start-dev.bat to launch development environment
    echo - Run run-tests.bat to execute test suite
    echo - Run test-runner.bat for advanced testing features
    echo.
    echo [AVAILABLE SERVICES]
    echo - Backend API will run on: http://localhost:8000
    echo - Frontend Dashboard: http://localhost:3000
    echo - ChromaDB Database: http://localhost:8001
    echo - API Documentation: http://localhost:8000/docs
)

echo ==========================================
echo.

echo [INFO] For troubleshooting help:
echo - Read: TESTING_TROUBLESHOOTING.md
echo - Read: QUICK_START.md
echo - Check: docs/README.md
echo.

if !error_count! gtr 0 (
    echo Press any key to exit and fix the issues...
) else (
    echo Press any key to start developing...
)
pause >nul
exit /b !error_count!