@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Health Check
color 0C

:: Add error handling and logging (添加錯誤處理和日志記錄)
set "LOG_FILE=%~dp0health-check-errors.log"
set "SCRIPT_NAME=health-check.bat"

:: Log script start (記錄腳本啟動)
echo [%date% %time%] Script started: %SCRIPT_NAME% >> "%LOG_FILE%" 2>nul

echo ==========================================
echo   Unified AI Project - Health Check
echo ==========================================
echo.
echo Checking development environment status... (檢查開發環境狀態)
echo.

set "error_count=0"

:: Check Node.js
echo [CHECK 1/7] Node.js Environment
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
echo [CHECK 2/7] Python Environment
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
echo [CHECK 3/7] Package Manager
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
echo [CHECK 4/7] Project Dependencies
if exist "node_modules" (
    echo [OK] Node.js dependencies installed
) else (
    echo [FAIL] Node.js dependencies not installed
    echo [SUGGESTION] Run: pnpm install
    set /a "error_count+=1"
)

:: Check Python virtual environment
echo.
echo [CHECK 5/7] Python Environment
if exist "apps\backend\venv" (
    echo [OK] Python virtual environment created (Python虛擬環境已創建)
    
    :: Check if Python packages are installed
    echo [INFO] Checking essential Python packages... (檢查必要的Python包)
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
    
    python -c "import uvicorn" >nul 2>&1
    if !errorlevel!==0 (
        echo [OK] uvicorn available
    ) else (
        echo [WARNING] uvicorn not found
        set /a "error_count+=1"
    )
    
    python -c "import torch" >nul 2>&1
    if !errorlevel!==0 (
        echo [INFO] PyTorch not found (optional for some modules)
    ) else (
        echo [OK] PyTorch available
    )
    
    if !error_count! gtr 0 (
        echo [SUGGESTION] Run start-dev.bat to install missing packages (運行start-dev.bat安裝缺失的包)
    )
    
    call venv\Scripts\deactivate.bat >nul 2>&1
    cd ..\..
) else (
    echo [FAIL] Python virtual environment not created
    echo [SUGGESTION] Run start-dev.bat for automatic setup
    set /a "error_count+=1"
)

:: Check configuration files
echo.
echo [CHECK 6/7] Configuration Files
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

:: Check directory structure
echo.
echo [CHECK 7/7] Directory Structure
set "missing_dirs=0"
if not exist "apps" (
    echo [WARNING] apps directory missing
    set /a "missing_dirs+=1"
)
if not exist "packages" (
    echo [WARNING] packages directory missing
    set /a "missing_dirs+=1"
)
if not exist "scripts" (
    echo [WARNING] scripts directory missing
    set /a "missing_dirs+=1"
)
if not exist "tests" (
    echo [WARNING] tests directory missing
    set /a "missing_dirs+=1"
)
if not exist "docs" (
    echo [WARNING] docs directory missing
    set /a "missing_dirs+=1"
)
if not exist "training" (
    echo [WARNING] training directory missing
    set /a "missing_dirs+=1"
)

if !missing_dirs! equ 0 (
    echo [OK] All required directories present
) else (
    echo [INFO] Some directories missing, but not critical
)

:: Detailed system information
echo.
echo [SYSTEM INFO] Detailed System Information
echo ==========================================
systeminfo | findstr /C:"OS Name" /C:"OS Version" /C:"System Type" /C:"Total Physical Memory" /C:"Available Physical Memory"
echo ==========================================

echo.
echo ==========================================
echo    Health Check Results
echo ==========================================
echo.

if !error_count! gtr 0 (
    echo [WARNING] Found !error_count! issue^(s^) that need attention (找到 !error_count! 個需要注意的問題)
    echo.
    echo [NEXT STEPS] (下一步)
    echo 1. Follow the suggestions above to resolve issues (按照上述建議解決問題)
    echo 2. Run start-dev.bat for automatic environment setup (運行start-dev.bat進行自動環境設置)
    echo 3. Re-run this health check to verify fixes (重新運行此健康檢查以驗證修復)
    echo.
    echo [COMMON SOLUTIONS] (常見解決方案)
    echo - Missing Node.js: Download from https://nodejs.org/
    echo - Missing Python: Download from https://python.org/
    echo - Missing pnpm: Run 'npm install -g pnpm'
    echo - Missing dependencies: Run start-dev.bat
) else (
    echo [SUCCESS] All checks passed! Environment is ready (所有檢查通過！環境已準備就緒)
    echo.
    echo [READY TO START DEVELOPMENT] (準備開始開發)
    echo - Run start-dev.bat to launch development environment (運行start-dev.bat啟動開發環境)
    echo - Run run-tests.bat to execute test suite (運行run-tests.bat執行測試套件)
    echo - Run safe-git-cleanup.bat to clean Git status (運行safe-git-cleanup.bat清理Git狀態)
    echo.
    echo [AVAILABLE SERVICES] (可用服務)
    echo - Backend API will run on: http://localhost:8000
    echo - Frontend Dashboard: http://localhost:3000
    echo - ChromaDB Database: http://localhost:8001
    echo - API Documentation: http://localhost:8000/docs
)

echo ==========================================
echo.

echo [INFO] For troubleshooting help: (故障排除幫助)
echo - Read: docs/TESTING_TROUBLESHOOTING.md
echo - Read: docs/QUICK_START.md
echo - Check: docs/README.md
echo.

:end_script
if !error_count! gtr 0 (
    echo Press any key to return to main menu... (按任意鍵返回主菜單)
) else (
    echo Press any key to start developing... (按任意鍵開始開發)
)
echo [%date% %time%] Health check completed with !error_count! errors >> "%LOG_FILE%" 2>nul
pause >nul
exit /b !error_count!