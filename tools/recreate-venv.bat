@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Recreate Virtual Environment
color 0C

:: Add error handling and logging (添加錯誤處理和日志記錄)
set "LOG_FILE=%~dp0recreate-venv-errors.log"
set "SCRIPT_NAME=recreate-venv.bat"

:: Log script start (記錄腳本啟動)
echo [%date% %time%] Script started: %SCRIPT_NAME% >> "%LOG_FILE%" 2>nul

echo ==========================================
echo   Unified AI Project - Recreate Virtual Environment
echo ==========================================
echo.
echo This script will recreate the Python virtual environment for the backend. (此腳本將重新創建後端的Python虛擬環境)
echo.
echo Process: (過程)
echo 1. 🗑️  Delete existing virtual environment (刪除現有的虛擬環境)
echo 2. 🐍 Create new virtual environment (創建新的虛擬環境)
echo 3. 📦 Install required packages (安裝所需的包)
echo 4. ✅ Verify installation (驗證安裝)
echo.

:: Confirm action (確認操作)
echo [CONFIRM] Are you sure you want to recreate the virtual environment? (您確定要重新創建虛擬環境嗎?)
echo.
echo This will: (這將:)
echo - Delete the existing 'venv' folder (刪除現有的'venv'文件夾)
echo - Create a new virtual environment (創建新的虛擬環境)
echo - Reinstall all Python packages (重新安裝所有Python包)
echo.

:: 使用 set /p 替代 choice 命令
:get_user_choice
set "user_choice="
set /p "user_choice=Continue with virtual environment recreation (y/N)? "
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
echo.
echo [STEP 1/4] Deleting existing virtual environment... (刪除現有的虛擬環境)
echo [%date% %time%] Deleting existing virtual environment >> "%LOG_FILE%" 2>nul

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
echo.
echo [STEP 2/4] Creating new virtual environment... (創建新的虛擬環境)
echo [%date% %time%] Creating new virtual environment >> "%LOG_FILE%" 2>nul

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
echo.
echo [STEP 3/4] Installing Python packages... (安裝Python包)
echo [%date% %time%] Installing Python packages >> "%LOG_FILE%" 2>nul

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

echo [OK] Python packages installed successfully (Python包安裝成功)

:: Verify installation (驗證安裝)
echo.
echo [STEP 4/4] Verifying installation... (驗證安裝)
echo [%date% %time%] Verifying installation >> "%LOG_FILE%" 2>nul

:: Check key packages (檢查關鍵包)
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

:: Deactivate virtual environment (停用虛擬環境)
call venv\Scripts\deactivate.bat >nul 2>&1

echo.
echo [SUCCESS] Virtual environment recreated successfully! (虛擬環境重新創建成功!)
echo [%date% %time%] Virtual environment recreated successfully >> "%LOG_FILE%" 2>nul
echo.
echo Next steps: (下一步)
echo 1. Run start-dev.bat to start development (運行start-dev.bat開始開發)
echo 2. Run run-tests.bat to verify installation (運行run-tests.bat驗證安裝)
echo 3. Run health-check.bat to verify environment (運行health-check.bat驗證環境)
echo.

cd ..\..

:end_script
echo.
echo Press any key to exit...
pause >nul
exit /b 0