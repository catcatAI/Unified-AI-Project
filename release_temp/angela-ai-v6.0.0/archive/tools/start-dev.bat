@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
cd D:\Projects\Unified-AI-Project
title Unified AI Project - Development Environment
color 0A

:: Add error handling and logging (添加錯誤處理和日志記錄)
set "LOG_FILE=%~dp0dev-env-errors.log"
set "SCRIPT_NAME=start-dev.bat"

:: Log script start (記錄腳本啟動)
echo [%date% %time%] Script started: %SCRIPT_NAME% >> "%LOG_FILE%" 2>nul

echo ==========================================
echo   Unified AI Project - Development Environment
echo ==========================================
echo.
echo Welcome to the Unified AI Project development environment! (歡迎來到Unified AI Project開發環境!)
echo.
echo This script will automatically: (此腳本將自動:)
echo 1. ✅ Check your development environment (檢查您的開發環境)
echo 2. 📦 Install required dependencies (安裝所需的依賴)
echo 3. 🐍 Setup Python virtual environment (設置Python虛擬環境)
echo 4. 🚀 Start development servers (啟動開發服務器)
echo.

:: Check environment (檢查環境)
echo [CHECK] Checking development environment... (檢查開發環境)
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not installed
    echo [INFO] Please download from: https://nodejs.org/
    echo [%date% %time%] Node.js not installed >> "%LOG_FILE%" 2>nul
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not installed
    echo [INFO] Please download from: https://python.org/
    echo [%date% %time%] Python not installed >> "%LOG_FILE%" 2>nul
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

echo [OK] Development environment ready (開發環境準備就緒)
echo.

:: Check pnpm (檢查pnpm)
echo [CHECK] Checking package manager... (檢查包管理器)
where pnpm >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing pnpm...
    echo [%date% %time%] Installing pnpm >> "%LOG_FILE%" 2>nul
    npm install -g pnpm >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install pnpm
        echo [%date% %time%] Failed to install pnpm >> "%LOG_FILE%" 2>nul
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
)

:: Install dependencies (安裝依賴)
echo.
echo [INSTALL] Installing project dependencies... (安裝項目依賴)
python tools\install_dependencies.py
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    echo [%date% %time%] Failed to install dependencies >> "%LOG_FILE%" 2>nul
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

echo [OK] Dependencies installed successfully (依賴安裝成功)
echo.

:: Setup Python environment (設置Python環境)
echo [SETUP] Setting up Python environment... (設置Python環境)
echo Current directory before cd apps\backend: %cd%
cd apps\backend

if not exist "venv" (
    echo [INFO] Creating Python virtual environment... (創建Python虛擬環境)
    echo [%date% %time%] Creating Python virtual environment >> "%LOG_FILE%" 2>nul
    python -m venv venv > venv_setup.log 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        echo [INFO] Check venv_setup.log for details
        echo [%date% %time%] Failed to create virtual environment >> "%LOG_FILE%" 2>nul
        cd ..\..
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
)

echo [INFO] Installing Python packages... (安裝Python包)
call venv\Scripts\activate.bat >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    echo [%date% %time%] Failed to activate virtual environment >> "%LOG_FILE%" 2>nul
    cd ..\..
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

pip install --upgrade pip > pip_upgrade.log 2>&1
pip install -r requirements.txt > pip_install.log 2>&1
pip install -r requirements-dev.txt >> pip_install.log 2>&1

:: Deactivate virtual environment (停用虛擬環境)
call venv\Scripts\deactivate.bat >nul 2>&1
cd ..\..

echo [OK] Python environment setup completed (Python環境設置完成)
echo.

:: Start development servers (啟動開發服務器)
echo [START] Starting development servers... (啟動開發服務器)
echo.

:: Start backend API server (啟動後端API服務器)
cd apps\backend
call venv\Scripts\activate.bat >nul 2>&1
:: Use start command with /b parameter to avoid creating new window causing flash (使用start命令時添加/b參數避免創建新窗口導致閃退)
start "Backend API" /min cmd /c "cd /d %~dp0apps\backend && call venv\Scripts\activate.bat >nul 2>&1 && set PYTHONPATH=%PYTHONPATH%;%~dp0apps\backend\src && uvicorn src.services.main_api_server:app --reload --host 0.0.0.0 --port 8000"
cd ..\..

:: Start frontend dashboard (啟動前端儀表板)
:: Use start command with /b parameter to avoid creating new window causing flash (使用start命令時添加/b參數時避免創建新窗口導致閃退)
start "Frontend Dashboard" /min cmd /c "cd /d %~dp0 && pnpm --filter frontend-dashboard dev"

echo [SUCCESS] Development environment started successfully! (開發環境啟動成功!)
echo.
echo ==========================================
echo    Development Environment Status
echo ==========================================
echo.
echo 🚀 Backend API: http://localhost:8000 (後端API)
echo 📊 Frontend Dashboard: http://localhost:3000 (前端儀表板)
echo 📚 API Documentation: http://localhost:8000/docs (API文檔)
echo 🗃️  ChromaDB Database: http://localhost:8001 (ChromaDB數據庫)
echo.
echo [INFO] Press Ctrl+C to stop servers (按Ctrl+C停止服務器)
echo.
echo [TIPS] (提示)
echo 🔧 Run health-check.bat to verify environment (運行health-check.bat驗證環境)
echo 🧪 Run run-tests.bat to execute test suite (運行run-tests.bat執行測試套件)
echo 🧹 Run safe-git-cleanup.bat to clean Git status (運行safe-git-cleanup.bat清理Git狀態)
echo.

echo [%date% %time%] Development environment started successfully >> "%LOG_FILE%" 2>nul

:end_script
echo.
echo Press Ctrl+C to stop servers, or close this window... (按Ctrl+C停止服務器，或關閉此窗口)
echo.

:: Keep the script running to maintain servers (保持腳本運行以維持服務器)
:keep_running
timeout /t 60 >nul
goto keep_running