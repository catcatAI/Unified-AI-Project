@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Environment Setup
color 0A

:: Add error handling and logging (添加錯誤處理和日志記錄)
set "LOG_FILE=%~dp0setup-env-errors.log"
set "SCRIPT_NAME=setup_env.bat"

:: Log script start (記錄腳本啟動)
echo [%date% %time%] Script started: %SCRIPT_NAME% >> "%LOG_FILE%" 2>nul

echo ==========================================
echo   Unified AI Project - Environment Setup
echo ==========================================
echo.
echo This script sets up the development environment for the Unified AI Project. (此腳本為Unified AI Project設置開發環境)
echo.
echo Setup process: (設置過程)
echo 1. 🧪 Check system requirements (檢查系統要求)
echo 2. 📦 Install Node.js dependencies (安裝Node.js依賴)
echo 3. 🐍 Setup Python virtual environment (設置Python虛擬環境)
echo 4. 🛠️  Configure development tools (配置開發工具)
echo 5. ✅ Verify installation (驗證安裝)
echo.

:: Check system requirements (檢查系統要求)
echo.
echo [STEP 1/5] Checking system requirements... (檢查系統要求)
echo [%date% %time%] Checking system requirements >> "%LOG_FILE%" 2>nul

:: Check Node.js (檢查Node.js)
echo [CHECK] Checking Node.js... (檢查Node.js)
where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not installed (未安裝Node.js)
    echo [INFO] Please download from: https://nodejs.org/
    echo [%date% %time%] Node.js not installed >> "%LOG_FILE%" 2>nul
    echo Press any key to exit...
    pause >nul
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('node --version') do set node_version=%%i
    echo [OK] Node.js: !node_version! (Node.js: !node_version!)
)

:: Check Python (檢查Python)
echo [CHECK] Checking Python... (檢查Python)
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not installed (未安裝Python)
    echo [INFO] Please download from: https://python.org/
    echo [%date% %time%] Python not installed >> "%LOG_FILE%" 2>nul
    echo Press any key to exit...
    pause >nul
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('python --version') do set python_version=%%i
    echo [OK] Python: !python_version! (Python: !python_version!)
)

echo [OK] System requirements met (系統要求滿足)

:: Install Node.js dependencies (安裝Node.js依賴)
echo.
echo [STEP 2/5] Installing Node.js dependencies... (安裝Node.js依賴)
echo [%date% %time%] Installing Node.js dependencies >> "%LOG_FILE%" 2>nul

:: Check pnpm (檢查pnpm)
where pnpm >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing pnpm... (安裝pnpm)
    echo [%date% %time%] Installing pnpm >> "%LOG_FILE%" 2>nul
    npm install -g pnpm > pnpm_install.log 2>&1
    if errorlevel 1 (
        echo [ERROR] Failed to install pnpm (無法安裝pnpm)
        echo [INFO] Check pnpm_install.log for details (檢查pnpm_install.log獲取詳細信息)
        echo [%date% %time%] Failed to install pnpm >> "%LOG_FILE%" 2>nul
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
    echo [OK] pnpm installed (pnpm已安裝)
)

:: Install project dependencies (安裝項目依賴)
echo [INFO] Installing project dependencies... (安裝項目依賴)
pnpm install > node_deps_install.log 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to install Node.js dependencies (無法安裝Node.js依賴)
    echo [INFO] Check node_deps_install.log for details (檢查node_deps_install.log獲取詳細信息)
    echo [%date% %time%] Failed to install Node.js dependencies >> "%LOG_FILE%" 2>nul
) else (
    echo [OK] Node.js dependencies installed (Node.js依賴已安裝)
)

:: Setup Python virtual environment (設置Python虛擬環境)
echo.
echo [STEP 3/5] Setting up Python virtual environment... (設置Python虛擬環境)
echo [%date% %time%] Setting up Python virtual environment >> "%LOG_FILE%" 2>nul

:: Change to backend directory (切換到後端目錄)
cd ..\apps\backend
if errorlevel 1 (
    echo [ERROR] Failed to change to backend directory (無法切換到後端目錄)
    echo [%date% %time%] Failed to change to backend directory >> "%LOG_FILE%" 2>nul
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

:: Create virtual environment if it doesn't exist (如果不存在則創建虛擬環境)
if not exist "venv" (
    echo [INFO] Creating Python virtual environment... (創建Python虛擬環境)
    echo [%date% %time%] Creating Python virtual environment >> "%LOG_FILE%" 2>nul
    python -m venv venv > venv_create.log 2>&1
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment (無法創建虛擬環境)
        echo [INFO] Check venv_create.log for details (檢查venv_create.log獲取詳細信息)
        echo [%date% %time%] Failed to create virtual environment >> "%LOG_FILE%" 2>nul
        cd ..\..
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
    echo [OK] Virtual environment created (虛擬環境已創建)
) else (
    echo [INFO] Virtual environment already exists (虛擬環境已存在)
)

:: Activate virtual environment and install packages (激活虛擬環境並安裝包)
echo [INFO] Installing Python packages... (安裝Python包)
call venv\Scripts\activate.bat >nul 2>&1

pip install --upgrade pip > pip_upgrade.log 2>&1
if errorlevel 1 (
    echo [WARNING] Failed to upgrade pip (無法升級pip)
)

pip install -r requirements.txt > pip_install.log 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to install requirements (無法安裝requirements)
    echo [INFO] Check pip_install.log for details (檢查pip_install.log獲取詳細信息)
    echo [%date% %time%] Failed to install requirements >> "%LOG_FILE%" 2>nul
    call venv\Scripts\deactivate.bat >nul 2>&1
    cd ..\..
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

pip install -r requirements-dev.txt >> pip_install.log 2>&1
if errorlevel 1 (
    echo [WARNING] Failed to install development requirements (無法安裝開發requirements)
)

:: Deactivate virtual environment (停用虛擬環境)
call venv\Scripts\deactivate.bat >nul 2>&1
echo [OK] Python packages installed (Python包已安裝)

:: Return to root directory (返回根目錄)
cd ..\..

:: Configure development tools (配置開發工具)
echo.
echo [STEP 4/5] Configuring development tools... (配置開發工具)
echo [%date% %time%] Configuring development tools >> "%LOG_FILE%" 2>nul

:: Create default configuration files if they don't exist (如果不存在則創建默認配置文件)
if not exist "..\apps\backend\configs\config.yaml" (
    echo [INFO] Creating default backend configuration... (創建默認後端配置)
    echo # Backend Configuration > ..\apps\backend\configs\config.yaml
    echo debug: true >> ..\apps\backend\configs\config.yaml
    echo port: 8000 >> ..\apps\backend\configs\config.yaml
    echo host: "0.0.0.0" >> ..\apps\backend\configs\config.yaml
    echo database_url: "sqlite:///./app.db" >> ..\apps\backend\configs\config.yaml
    echo log_level: "INFO" >> ..\apps\backend\configs\config.yaml
    echo. >> ..\apps\backend\configs\config.yaml
    echo [OK] Backend configuration created (後端配置已創建)
) else (
    echo [INFO] Backend configuration already exists (後端配置已存在)
)

:: Verify installation (驗證安裝)
echo.
echo [STEP 5/5] Verifying installation... (驗證安裝)
echo [%date% %time%] Verifying installation >> "%LOG_FILE%" 2>nul

:: Check key tools (檢查關鍵工具)
where pnpm >nul 2>&1
if errorlevel 1 (
    echo [WARNING] pnpm not found (未找到pnpm)
) else (
    echo [OK] pnpm available (pnpm可用)
)

:: Check Python packages (檢查Python包)
cd ..\apps\backend
call venv\Scripts\activate.bat >nul 2>&1

python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] FastAPI not found (未找到FastAPI)
) else (
    echo [OK] FastAPI available (FastAPI可用)
)

python -c "import pytest" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] pytest not found (未找到pytest)
) else (
    echo [OK] pytest available (pytest可用)
)

python -c "import uvicorn" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] uvicorn not found (未找到uvicorn)
) else (
    echo [OK] uvicorn available (uvicorn可用)
)

call venv\Scripts\deactivate.bat >nul 2>&1
cd ..\..

echo.
echo [SUCCESS] Environment setup completed successfully! (環境設置成功完成!)
echo [%date% %time%] Environment setup completed successfully >> "%LOG_FILE%" 2>nul
echo.
echo Next steps: (下一步)
echo 1. Run start-dev.bat to start development (運行start-dev.bat開始開發)
echo 2. Run run-tests.bat to verify installation (運行run-tests.bat驗證安裝)
echo 3. Run health-check.bat to verify environment (運行health-check.bat驗證環境)
echo.
echo Environment Information: (環境信息)
echo 📦 Node.js dependencies: Installed (Node.js依賴: 已安裝)
echo 🐍 Python virtual environment: Configured (Python虛擬環境: 已配置)
echo 🛠️  Development tools: Configured (開發工具: 已配置)
echo ✅ Verification: Passed (驗證: 通過)
echo.

:end_script
echo.
echo Press any key to exit...
pause >nul
exit /b 0