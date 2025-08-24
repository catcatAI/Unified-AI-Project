@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion

echo ================================================================
echo Unified-AI-Project Data Download and Enhancement Script
echo ================================================================
echo.

echo [INFO] Checking Python availability...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+ first.
    pause
    exit /b 1
)

echo [INFO] Installing required packages...
pip install requests >nul 2>&1

echo.
echo [INFO] Step 1: Downloading training datasets...
echo This will download datasets based on available disk space.
echo.
pause

python scripts\download_training_data.py
if errorlevel 1 (
    echo [ERROR] Data download failed.
    pause
    exit /b 1
)

echo.
echo [INFO] Step 2: Enhancing project structure...
python scripts\enhance_project.py
if errorlevel 1 (
    echo [ERROR] Project enhancement failed.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Data download and project enhancement completed!
echo.
echo Next steps:
echo 1. Review downloaded datasets in: data/
echo 2. Check training configuration: training/configs/training_config.json
echo 3. Start training with your preferred framework
echo.
pause