@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Fix Dependencies
color 0E

:: Add error handling and logging (添加錯誤處理和日志記錄)
set "LOG_FILE=%~dp0fix-dependencies-errors.log"
set "SCRIPT_NAME=fix-dependencies.bat"

:: Log script start (記錄腳本啟動)
echo [%date% %time%] Script started: %SCRIPT_NAME% >> "%LOG_FILE%" 2>nul

echo ==========================================
echo   Unified AI Project - Fix Dependencies
echo ==========================================
echo.
echo This script will fix common dependency issues in the project. (此腳本將修復項目中的常見依賴問題)
echo.
echo Process: (過程)
echo 1. 🧹 Clean existing dependencies (清理現有依賴)
echo 2. 📦 Reinstall Node.js dependencies (重新安裝Node.js依賴)
echo 3. 🐍 Reinstall Python dependencies (重新安裝Python依賴)
echo 4. ✅ Verify installation (驗證安裝)
echo.

:: Confirm action (確認操作)
echo [CONFIRM] Are you sure you want to fix dependencies? (您確定要修復依賴嗎?)
echo.
echo This will: (這將:)
echo - Delete node_modules folder (刪除node_modules文件夾)
echo - Delete Python venv folder (刪除Python venv文件夾)
echo - Reinstall all dependencies (重新安裝所有依賴)
echo.

:: 使用 set /p 替代 choice 命令
:get_user_choice
set "user_choice="
set /p "user_choice=Continue with dependency fix (y/N)? "
if not defined user_choice (
    set "user_choice=N"
)

:: 验证用户输入
if /i "%user_choice%"=="Y" (
    goto continue_fix
) else if /i "%user_choice%"=="N" (
    echo [INFO] Operation cancelled by user (操作被用戶取消)
    echo [%date% %time%] Operation cancelled by user >> "%LOG_FILE%" 2>nul
    echo Press any key to exit...
    pause >nul
    exit /b 0
) else (
    echo [ERROR] Invalid choice '%user_choice%'. Please enter 'Y' or 'N'.
    echo [%date% %time%] Invalid choice: %user_choice% >> "%LOG_FILE%" 2>nul
    goto get_user_choice
)

:continue_fix

:: Fix Node.js dependencies (修復Node.js依賴)
echo.
echo [STEP 1/4] Fixing Node.js dependencies... (修復Node.js依賴)
echo [%date% %time%] Fixing Node.js dependencies >> "%LOG_FILE%" 2>nul

:: Delete node_modules (刪除node_modules)
if exist "node_modules" (
    echo [INFO] Removing node_modules folder... (刪除node_modules文件夾)
    rmdir /s /q "node_modules" > node_modules_delete.log 2>&1
    if errorlevel 1 (
        echo [ERROR] Failed to delete node_modules (無法刪除node_modules)
        echo [INFO] Check node_modules_delete.log for details (檢查node_modules_delete.log獲取詳細信息)
        echo [%date% %time%] Failed to delete node_modules >> "%LOG_FILE%" 2>nul
    ) else (
        echo [OK] node_modules folder deleted (node_modules文件夾已刪除)
    )
) else (
    echo [INFO] No node_modules folder found (未找到node_modules文件夾)
)

:: Check pnpm (檢查pnpm)
where pnpm >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing pnpm... (安裝pnpm)
    npm install -g pnpm > pnpm_install.log 2>&1
    if errorlevel 1 (
        echo [ERROR] Failed to install pnpm (無法安裝pnpm)
        echo [INFO] Check pnpm_install.log for details (檢查pnpm_install.log獲取詳細信息)
        echo [%date% %time%] Failed to install pnpm >> "%LOG_FILE%" 2>nul
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
    echo [OK] pnpm installed successfully (pnpm安裝成功)
)

:: Install Node.js dependencies (安裝Node.js依賴)
echo [INFO] Installing Node.js dependencies... (安裝Node.js依賴)
pnpm install > node_install.log 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to install Node.js dependencies (無法安裝Node.js依賴)
    echo [INFO] Check node_install.log for details (檢查node_install.log獲取詳細信息)
    echo [%date% %time%] Failed to install Node.js dependencies >> "%LOG_FILE%" 2>nul
) else (
    echo [OK] Node.js dependencies installed successfully (Node.js依賴安裝成功)
)

:: Fix Python dependencies (修復Python依賴)
echo.
echo [STEP 2/4] Fixing Python dependencies... (修復Python依賴)
echo [%date% %time%] Fixing Python dependencies >> "%LOG_FILE%" 2>nul

:: Change to backend directory (切換到後端目錄)
cd apps\backend
if errorlevel 1 (
    echo [ERROR] Failed to change to backend directory (無法切換到後端目錄)
    echo [%date% %time%] Failed to change to backend directory >> "%LOG_FILE%" 2>nul
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

:: Delete existing virtual environment (刪除現有的虛擬環境)
if exist "venv" (
    echo [INFO] Removing existing venv folder... (刪除現有的venv文件夾)
    rmdir /s /q "venv" > venv_delete.log 2>&1
    if errorlevel 1 (
        echo [ERROR] Failed to delete existing virtual environment (無法刪除現有的虛擬環境)
        echo [INFO] Check venv_delete.log for details (檢查venv_delete.log獲取詳細信息)
        echo [%date% %time%] Failed to delete existing virtual environment >> "%LOG_FILE%" 2>nul
        cd ..\..
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
    echo [OK] Existing virtual environment deleted (現有的虛擬環境已刪除)
) else (
    echo [INFO] No existing virtual environment found (未找到現有的虛擬環境)
)

:: Create new virtual environment (創建新的虛擬環境)
echo [INFO] Creating new virtual environment... (創建新的虛擬環境)
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

echo [OK] Virtual environment created successfully (虛擬環境創建成功)

:: Activate virtual environment and install packages (激活虛擬環境並安裝包)
echo [INFO] Installing Python packages... (安裝Python包)
call venv\Scripts\activate.bat >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment (無法激活虛擬環境)
    echo [%date% %time%] Failed to activate virtual environment >> "%LOG_FILE%" 2>nul
    cd ..\..
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

pip install --upgrade pip > pip_upgrade.log 2>&1
if errorlevel 1 (
    echo [WARNING] Failed to upgrade pip (無法升級pip)
    echo [INFO] Continuing with package installation... (繼續安裝包)
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
    echo [INFO] This may not be critical for basic operation (這對基本操作可能不關鍵)
)

:: Deactivate virtual environment (停用虛擬環境)
call venv\Scripts\deactivate.bat >nul 2>&1
echo [OK] Python packages installed successfully (Python包安裝成功)

cd ..\..

:: Verify installation (驗證安裝)
echo.
echo [STEP 3/4] Verifying installation... (驗證安裝)
echo [%date% %time%] Verifying installation >> "%LOG_FILE%" 2>nul

:: Check Node.js packages (檢查Node.js包)
where pnpm >nul 2>&1
if errorlevel 1 (
    echo [WARNING] pnpm not found after installation (安裝後未找到pnpm)
) else (
    echo [OK] pnpm available (pnpm可用)
)

:: Check Python packages (檢查Python包)
cd apps\backend
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

call venv\Scripts\deactivate.bat >nul 2>&1
cd ..\..

echo.
echo [STEP 4/4] Running dependency health check... (運行依賴健康檢查)
echo [%date% %time%] Running dependency health check >> "%LOG_FILE%" 2>nul

:: Run a quick dependency check (運行快速依賴檢查)
if exist "tools\health-check.bat" (
    echo [INFO] Running health check... (運行健康檢查)
    call tools\health-check.bat > dependency_check.log 2>&1
    echo [OK] Dependency health check completed (依賴健康檢查完成)
) else (
    echo [INFO] Health check script not found (未找到健康檢查腳本)
)

echo.
echo [SUCCESS] Dependencies fixed successfully! (依賴修復成功!)
echo [%date% %time%] Dependencies fixed successfully >> "%LOG_FILE%" 2>nul
echo.
echo Next steps: (下一步)
echo 1. Run start-dev.bat to start development (運行start-dev.bat開始開發)
echo 2. Run run-tests.bat to verify installation (運行run-tests.bat驗證安裝)
echo.

:end_script
echo.
echo Press any key to exit...
pause >nul
exit /b 0