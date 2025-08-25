@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Training Setup
color 0A

echo ==========================================
echo   Unified AI Project - Training Setup
echo ==========================================
echo.

:: 检查环境
echo [INFO] Checking environment...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not installed
    echo [INFO] Download from: https://python.org/
    echo.
    pause
    exit /b 1
)

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

echo [OK] Environment ready
echo.

:: 安装依赖
echo [INFO] Installing dependencies...
pnpm install
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

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

:: 完善项目结构
echo.
echo [INFO] Enhancing project structure...
python scripts\enhance_project.py
if %errorlevel% neq 0 (
    echo [ERROR] Failed to enhance project structure
    pause
    exit /b 1
)

:: 生成模拟数据
echo.
echo [INFO] Generating mock training data...
python scripts\generate_mock_data.py
if %errorlevel% neq 0 (
    echo [ERROR] Failed to generate mock data
    pause
    exit /b 1
)

:: 运行集成测试
echo.
echo [INFO] Running training integration tests...
cd apps\backend
call venv\Scripts\activate.bat
python ..\..\scripts\training_integration.py
if %errorlevel% neq 0 (
    echo [ERROR] Training integration tests failed
    cd ..\..
    pause
    exit /b 1
)
cd ..\..

echo.
echo ==========================================
echo    Training Setup Complete
echo ==========================================
echo.
echo [SUCCESS] Your Unified-AI-Project is now ready for training!
echo.
echo Next steps:
echo 1. Check the generated mock data in the data/ directory
echo 2. Review the training configuration in training/configs/
echo 3. Run the training script when you're ready
echo.
echo For real training data:
echo - Run scripts/download_training_data.py
echo - Or manually download datasets to data/ directory
echo.
echo For training:
echo - Use the training scripts in the training/ directory
echo.
pause