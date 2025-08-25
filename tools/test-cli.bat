@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - CLI Test
color 0A

echo ==========================================
echo   Unified AI Project - CLI Test
echo ==========================================
echo.

echo [INFO] Testing CLI tools...
echo.

:: Test 1: Check if Python is available
echo [TEST 1] Checking Python availability...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [PASS] Python is available
) else (
    echo [FAIL] Python is not available
    goto end_script
)

:: Test 2: Check if CLI tools exist
echo.
echo [TEST 2] Checking CLI tools existence...
cd /d %~dp0..\packages\cli
if exist "cli/unified_cli.py" (
    echo [PASS] Unified CLI tool exists
) else (
    echo [FAIL] Unified CLI tool not found
)

if exist "cli/ai_models_cli.py" (
    echo [PASS] AI Models CLI tool exists
) else (
    echo [FAIL] AI Models CLI tool not found
)

if exist "cli/main.py" (
    echo [PASS] HSP CLI tool exists
) else (
    echo [FAIL] HSP CLI tool not found
)
cd ..\..\tools

:: Test 3: Test CLI Runner
echo.
echo [TEST 3] Testing CLI Runner...
if exist "cli-runner.bat" (
    echo [PASS] CLI Runner exists
    echo [INFO] CLI Runner can be executed with: tools\cli-runner.bat
) else (
    echo [FAIL] CLI Runner not found
)

:: Test 4: Test Unified CLI Help
echo.
echo [TEST 4] Testing Unified CLI Help...
cd /d %~dp0..\packages\cli
python -c "import cli.unified_cli; help(cli.unified_cli)" >nul 2>&1
if %errorlevel% equ 0 (
    echo [PASS] Unified CLI module can be imported
) else (
    echo [FAIL] Unified CLI module cannot be imported
)
cd ..\..\tools

:: Test 5: Test AI Models CLI Help
echo.
echo [TEST 5] Testing AI Models CLI Help...
cd /d %~dp0..\packages\cli
python -c "import cli.ai_models_cli; help(cli.ai_models_cli)" >nul 2>&1
if %errorlevel% equ 0 (
    echo [PASS] AI Models CLI module can be imported
) else (
    echo [FAIL] AI Models CLI module cannot be imported
)
cd ..\..\tools

echo.
echo [SUMMARY] CLI tools test completed!
echo.

:end_script
echo Press any key to exit...
pause >nul
exit /b 0