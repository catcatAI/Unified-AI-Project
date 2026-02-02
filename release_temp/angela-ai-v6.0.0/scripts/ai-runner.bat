@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - AI Runner
color 0E

:: Add error handling and logging (添加錯誤處理和日志記錄)
set "LOG_FILE=%~dp0ai-runner-errors.log"
set "SCRIPT_NAME=ai-runner.bat"

:: Log script start (記錄腳本啟動)
echo [%date% %time%] Script started: %SCRIPT_NAME% with args: %* >> "%LOG_FILE%" 2>nul

:: This script is designed for AI agents to run automated tasks (此腳本是為AI代理設計的，用於運行自動化任務)
:: It provides headless execution of common development operations (它提供常見開發操作的無頭執行)

:: Check if a command is provided (檢查是否提供了命令)
if "%1"=="" (
    echo [ERROR] No command provided
    echo [%date% %time%] No command provided >> "%LOG_FILE%" 2>nul
    echo.
    echo Usage: ai-runner.bat [command] [options]
    echo.
    echo Available commands: (可用命令)
    echo   setup     - Setup development environment (設置開發環境)
    echo   start     - Start development servers (啟動開發服務器)
    echo   test      - Run tests (運行測試)
    echo   train     - Setup training environment (設置訓練環境)
    echo   health    - Run health check (運行健康檢查)
    echo   clean     - Clean git status (清理git狀態)
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

:: Process commands (處理命令)
if "%1"=="setup" goto setup_env
if "%1"=="start" goto start_dev
if "%1"=="test" goto run_tests
if "%1"=="train" goto setup_training
if "%1"=="health" goto health_check
if "%1"=="clean" goto clean_git

echo [ERROR] Unknown command '%1'
echo [%date% %time%] Unknown command: %1 >> "%LOG_FILE%" 2>nul
echo Press any key to exit...
pause >nul
exit /b 1

:: Setup Environment Function (設置環境功能)
:setup_env
echo [INFO] Setting up environment... (設置環境)
echo [%date% %time%] Setting up environment >> "%LOG_FILE%" 2>nul
echo.

:: Check environment (檢查環境)
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not installed
    echo [%date% %time%] Node.js not installed >> "%LOG_FILE%" 2>nul
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

where python >nul 2>&1  
if %errorlevel% neq 0 (
    echo [ERROR] Python not installed
    echo [%date% %time%] Python not installed >> "%LOG_FILE%" 2>nul
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

echo [OK] Environment ready

:: Check pnpm (檢查pnpm)
where pnpm >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing pnpm...
    echo [%date% %time%] Installing pnpm >> "%LOG_FILE%" 2>nul
    npm install -g pnpm > pnpm_install.log 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install pnpm
        echo [%date% %time%] Failed to install pnpm >> "%LOG_FILE%" 2>nul
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
)

:: Install dependencies if needed (如果需要則安裝依賴)
if not exist "node_modules" (
    echo [INFO] Installing Node.js dependencies... (安裝Node.js依賴)
    echo [%date% %time%] Installing Node.js dependencies >> "%LOG_FILE%" 2>nul
    pnpm install > node_install.log 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies
        echo [%date% %time%] Failed to install dependencies >> "%LOG_FILE%" 2>nul
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
)

:: Setup Python environment (設置Python環境)
cd apps\backend
if errorlevel 1 (
    echo [ERROR] Failed to change to backend directory
    echo [%date% %time%] Failed to change to backend directory >> "%LOG_FILE%" 2>nul
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

if not exist "venv" (
    echo [INFO] Creating Python virtual environment... (創建Python虛擬環境)
    echo [%date% %time%] Creating Python virtual environment >> "%LOG_FILE%" 2>nul
    python -m venv venv > venv_create.log 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        echo [%date% %time%] Failed to create virtual environment >> "%LOG_FILE%" 2>nul
        cd ..\..
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
)

echo [INFO] Installing Python packages... (安裝Python包)
echo [%date% %time%] Installing Python packages >> "%LOG_FILE%" 2>nul
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
if errorlevel 1 (
    echo [WARNING] Failed to upgrade pip
    echo [%date% %time%] Failed to upgrade pip >> "%LOG_FILE%" 2>nul
    echo [INFO] Continuing with package installation...
)

pip install -r requirements.txt > pip_install.log 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to install requirements
    echo [%date% %time%] Failed to install requirements >> "%LOG_FILE%" 2>nul
    call venv\Scripts\deactivate.bat >nul 2>&1
    cd ..\..
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

pip install -r requirements-dev.txt >> pip_install.log 2>&1
if errorlevel 1 (
    echo [WARNING] Failed to install development requirements
    echo [%date% %time%] Failed to install development requirements >> "%LOG_FILE%" 2>nul
    echo [INFO] This may not be critical for basic operation
)

:: Deactivate virtual environment (停用虛擬環境)
call venv\Scripts\deactivate.bat >nul 2>&1
echo [OK] Python packages installed successfully

cd ..\..

echo [SUCCESS] Environment setup completed! (環境設置完成)
echo [%date% %time%] Environment setup completed >> "%LOG_FILE%" 2>nul
echo Press any key to continue...
pause >nul
exit /b 0

:: Start Development Function (啟動開發功能)
:start_dev
echo [INFO] Starting development environment... (啟動開發環境)
echo [%date% %time%] Starting development environment >> "%LOG_FILE%" 2>nul
echo.

if "%2"=="backend" (
    :: Start backend only (僅啟動後端)
    cd apps\backend
    call venv\Scripts\activate.bat >nul 2>&1
    :: Use start command with /b parameter to avoid creating new window causing flash (使用start命令時添加/b參數避免創建新窗口導致閃退)
    start "Backend API" /min cmd /c "cd /d %~dp0apps\backend && call venv\Scripts\activate.bat >nul 2>&1 && set PYTHONPATH=%PYTHONPATH%;%~dp0apps\backend\src && uvicorn src.services.main_api_server:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1"
    call venv\Scripts\deactivate.bat >nul 2>&1
    cd ..\..
    echo [SUCCESS] Backend services started in background (後端服務已在後台啟動)
    echo [%date% %time%] Backend services started >> "%LOG_FILE%" 2>nul
    echo Press any key to continue...
    pause >nul
    exit /b 0
) else if "%2"=="frontend" (
    :: Start frontend only (僅啟動前端)
    :: Use start command with /b parameter to avoid creating new window causing flash (使用start命令時添加/b參數避免創建新窗口導致閃退)
    start "Frontend" /min cmd /c "cd /d %~dp0 && pnpm --filter frontend-dashboard dev > frontend.log 2>&1"
    echo [SUCCESS] Frontend service started in background (前端服務已在後台啟動)
    echo [%date% %time%] Frontend service started >> "%LOG_FILE%" 2>nul
    echo Press any key to continue...
    pause >nul
    exit /b 0
) else (
    :: Start both (啟動兩者)
    cd apps\backend
    call venv\Scripts\activate.bat >nul 2>&1
    :: Use start command with /b parameter to avoid creating new window causing flash (使用start命令時添加/b參數避免創建新窗口導致閃退)
    start "Backend API" /min cmd /c "cd /d %~dp0apps\backend && call venv\Scripts\activate.bat >nul 2>&1 && set PYTHONPATH=%PYTHONPATH%;%~dp0apps\backend\src && uvicorn src.services.main_api_server:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1"
    call venv\Scripts\deactivate.bat >nul 2>&1
    cd ..\..
    :: Use start command with /b parameter to avoid creating new window causing flash (使用start命令時添加/b參數避免創建新窗口導致閃退)
    start "Frontend" /min cmd /c "cd /d %~dp0 && pnpm --filter frontend-dashboard dev > frontend.log 2>&1"
    echo [SUCCESS] Full development environment started in background (完整的開發環境已在後台啟動)
    echo [%date% %time%] Full development environment started >> "%LOG_FILE%" 2>nul
    echo Press any key to continue...
    pause >nul
    exit /b 0
)

:: Run Tests Function (運行測試功能)
:run_tests
echo [INFO] Running tests... (運行測試)
echo [%date% %time%] Running tests >> "%LOG_FILE%" 2>nul
echo.

if "%2"=="backend" (
    cd apps\backend
    call venv\Scripts\activate.bat >nul 2>&1
    pytest --tb=short -v > test_results.log 2>&1
    if errorlevel 1 (
        echo [ERROR] Backend tests failed
        echo [%date% %time%] Backend tests failed >> "%LOG_FILE%" 2>nul
        call venv\Scripts\deactivate.bat >nul 2>&1
        cd ..\..
        echo Press any key to continue...
        pause >nul
        exit /b 1
    )
    call venv\Scripts\deactivate.bat >nul 2>&1
    cd ..\..
    echo [SUCCESS] Backend tests completed. Results in test_results.log (後端測試完成。結果在test_results.log中)
    echo [%date% %time%] Backend tests completed >> "%LOG_FILE%" 2>nul
    echo Press any key to continue...
    pause >nul
    exit /b 0
) else if "%2"=="frontend" (
    pnpm --filter frontend-dashboard test --passWithNoTests > test_results.log 2>&1
    if errorlevel 1 (
        echo [ERROR] Frontend tests failed
        echo [%date% %time%] Frontend tests failed >> "%LOG_FILE%" 2>nul
        echo Press any key to continue...
        pause >nul
        exit /b 1
    )
    echo [SUCCESS] Frontend tests completed. Results in test_results.log (前端測試完成。結果在test_results.log中)
    echo [%date% %time%] Frontend tests completed >> "%LOG_FILE%" 2>nul
    echo Press any key to continue...
    pause >nul
    exit /b 0
) else (
    :: Run all tests (運行所有測試)
    cd apps\backend
    call venv\Scripts\activate.bat >nul 2>&1
    pytest --tb=short -v > backend_test_results.log 2>&1
    if errorlevel 1 (
        echo [ERROR] Backend tests failed
        echo [%date% %time%] Backend tests failed >> "%LOG_FILE%" 2>nul
        call venv\Scripts\deactivate.bat >nul 2>&1
        cd ..\..
        echo Press any key to continue...
        pause >nul
        exit /b 1
    )
    call venv\Scripts\deactivate.bat >nul 2>&1
    cd ..\..
    pnpm --filter frontend-dashboard test --passWithNoTests > frontend_test_results.log 2>&1
    if errorlevel 1 (
        echo [ERROR] Frontend tests failed
        echo [%date% %time%] Frontend tests failed >> "%LOG_FILE%" 2>nul
        echo Press any key to continue...
        pause >nul
        exit /b 1
    )
    echo [SUCCESS] All tests completed. Results in backend_test_results.log and frontend_test_results.log (所有測試完成。結果在backend_test_results.log和frontend_test_results.log中)
    echo [%date% %time%] All tests completed >> "%LOG_FILE%" 2>nul
    echo Press any key to continue...
    pause >nul
    exit /b 0
)

:: Setup Training Function (設置訓練功能)
:setup_training
echo [INFO] Setting up training environment... (設置訓練環境)
echo [%date% %time%] Setting up training environment >> "%LOG_FILE%" 2>nul
echo.

if exist "tools\setup-training.bat" (
    call tools\setup-training.bat > training_setup.log 2>&1
    if errorlevel 1 (
        echo [ERROR] Training environment setup failed
        echo [%date% %time%] Training environment setup failed >> "%LOG_FILE%" 2>nul
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
    echo [SUCCESS] Training environment setup completed. Log in training_setup.log (訓練環境設置完成。日志在training_setup.log中)
    echo [%date% %time%] Training environment setup completed >> "%LOG_FILE%" 2>nul
    echo Press any key to continue...
    pause >nul
    exit /b 0
) else (
    echo [ERROR] setup-training.bat not found
    echo [%date% %time%] setup-training.bat not found >> "%LOG_FILE%" 2>nul
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

:: Health Check Function (健康檢查功能)
:health_check
echo [INFO] Running health check... (運行健康檢查)
echo [%date% %time%] Running health check >> "%LOG_FILE%" 2>nul
echo.

if exist "tools\health-check.bat" (
    call tools\health-check.bat > health_check.log 2>&1
    echo [SUCCESS] Health check completed. Results in health_check.log (健康檢查完成。結果在health_check.log中)
    echo [%date% %time%] Health check completed >> "%LOG_FILE%" 2>nul
    echo Press any key to continue...
    pause >nul
    exit /b 0
) else (
    echo [ERROR] health-check.bat not found
    echo [%date% %time%] health-check.bat not found >> "%LOG_FILE%" 2>nul
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

:: Clean Git Function (清理Git功能)
:clean_git
echo [INFO] Cleaning git status... (清理git狀態)
echo [%date% %time%] Cleaning git status >> "%LOG_FILE%" 2>nul
echo.

if exist "tools\safe-git-cleanup.bat" (
    call tools\safe-git-cleanup.bat > git_clean.log 2>&1
    if errorlevel 1 (
        echo [ERROR] Git cleanup failed
        echo [%date% %time%] Git cleanup failed >> "%LOG_FILE%" 2>nul
        echo Press any key to continue...
        pause >nul
        exit /b 1
    )
    echo [SUCCESS] Git status cleaned. Log in git_clean.log (Git狀態已清理。日志在git_clean.log中)
    echo [%date% %time%] Git status cleaned >> "%LOG_FILE%" 2>nul
    echo Press any key to continue...
    pause >nul
    exit /b 0
) else (
    echo [ERROR] safe-git-cleanup.bat not found
    echo [%date% %time%] safe-git-cleanup.bat not found >> "%LOG_FILE%" 2>nul
    echo Press any key to exit...
    pause >nul
    exit /b 1
)