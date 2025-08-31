@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Training Setup
color 0A

echo ==========================================
echo   Unified AI Project - Training Setup
echo ==========================================
echo.

:: Check environment (檢查環境)
echo [INFO] Checking environment...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not installed
    echo [INFO] Download from: https://python.org/
    echo.
    echo Press any key to continue...
    pause >nul
    goto end_script
)

where pnpm >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing pnpm...
    npm install -g pnpm
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install pnpm
        echo Press any key to continue...
        pause >nul
        goto end_script
    )
)

echo [OK] Environment ready
echo.

:: Install dependencies (安裝依賴)
echo [INFO] Installing dependencies...
pnpm install
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    echo Press any key to continue...
    pause >nul
    goto end_script
)

cd apps\backend
if not exist "venv" (
    echo [INFO] Creating Python virtual environment... (創建Python虛擬環境)
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        cd ..\..
        echo Press any key to continue...
        pause >nul
        goto end_script
    )
)

echo [INFO] Installing Python packages... (安裝Python包)
call venv\Scripts\activate.bat
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt >nul 2>&1
pip install -r requirements-dev.txt >nul 2>&1
cd ..\..

:: Enhance project structure (完善項目結構)
echo.
echo [INFO] Enhancing project structure...
python ..\..\scripts\enhance_project.py
if %errorlevel% neq 0 (
    echo [ERROR] Failed to enhance project structure
    echo Press any key to continue...
    pause >nul
    goto end_script
)

:: Generate mock data (生成模擬數據)
echo.
echo [INFO] Generating mock training data... (生成模擬訓練數據)
python ..\..\scripts\generate_mock_data.py
if %errorlevel% neq 0 (
    echo [ERROR] Failed to generate mock data
    echo Press any key to continue...
    pause >nul
    goto end_script
)

:: Run integration tests (運行集成測試)
echo.
echo [INFO] Running training integration tests...
cd apps\backend
call venv\Scripts\activate.bat
python ..\..\scripts\training_integration.py
if %errorlevel% neq 0 (
    echo [ERROR] Training integration tests failed
    cd ..\..
    echo Press any key to continue...
    pause >nul
    goto end_script
)
cd ..\..

echo.
echo ==========================================
echo    Training Setup Complete (訓練設置完成)
echo ==========================================
echo.
echo [SUCCESS] Your Unified-AI-Project is now ready for training! (您的Unified-AI-Project現在已準備好進行訓練!)
echo.
echo Next steps: (下一步)
echo 1. Check the generated mock data in the data/ directory (檢查data/目錄中生成的模擬數據)
echo 2. Review the training configuration in training/configs/ (查看training/configs/中的訓練配置)
echo 3. Run the training script when you're ready (準備好時運行訓練腳本)
echo.
echo For real training data: (對於真實的訓練數據)
echo - Run scripts/download_training_data.py
echo - Or manually download datasets to data/ directory (或手動下載數據集到data/目錄)
echo.
echo For training: (對於訓練)
echo - Use the training scripts in the training/ directory (使用training/目錄中的訓練腳本)
echo.

:end_script
echo.
echo Press any key to return to main menu... (按任意鍵返回主菜單)
pause >nul