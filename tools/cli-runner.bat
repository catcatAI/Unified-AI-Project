@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - CLI Runner
color 0A

echo ==========================================
echo   Unified AI Project - CLI Runner
echo ==========================================
echo.

:main_menu
cls
echo ==========================================
echo   Unified AI Project - CLI Runner
echo ==========================================
echo.
echo Available CLI Tools:
echo.
echo 1. Unified CLI - General AI interactions
echo 2. AI Models CLI - Model management and interactions
echo 3. HSP CLI - Hyper-Structure Protocol tools
echo 4. Install CLI as system command
echo 5. Exit
echo.

set "choice="
set /p "choice=Enter your choice (1-5): "
if defined choice set "choice=%choice: =%"
if not defined choice (
    echo [ERROR] No input provided
    timeout /t 2 >nul
    goto main_menu
)

if "%choice%"=="1" goto unified_cli
if "%choice%"=="2" goto ai_models_cli
if "%choice%"=="3" goto hsp_cli
if "%choice%"=="4" goto install_cli
if "%choice%"=="5" goto end_script

echo [ERROR] Invalid choice '%choice%'. Please enter 1-5.
timeout /t 2 >nul
goto main_menu

:: Unified CLI Function
:unified_cli
echo.
echo [INFO] Starting Unified CLI...
echo.
cd /d %~dp0..\packages\cli
if exist "cli/unified_cli.py" (
    if "%~1"=="" (
        echo Usage: cli-runner.bat unified-cli [command] [options]
        echo.
        echo Running: python cli/unified_cli.py --help
        echo.
        python cli/unified_cli.py --help
        echo.
        echo Examples:
        echo   cli-runner.bat unified-cli health
        echo   cli-runner.bat unified-cli chat "Hello, how are you?"
        echo   cli-runner.bat unified-cli analyze --code "def hello(): print('Hello')"
        echo.
        echo For interactive mode, run without parameters
    ) else (
        echo Running: python cli/unified_cli.py %*
        echo.
        python cli/unified_cli.py %*
    )
) else (
    echo [ERROR] Unified CLI script not found
)
cd ..\..\tools
echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu

:: AI Models CLI Function
:ai_models_cli
echo.
echo [INFO] Starting AI Models CLI...
echo.
cd /d %~dp0..\packages\cli
if exist "cli/ai_models_cli.py" (
    if "%~1"=="" (
        echo Usage: cli-runner.bat ai-models-cli [command] [options]
        echo.
        echo Running: python cli/ai_models_cli.py --help
        echo.
        python cli/ai_models_cli.py --help
        echo.
        echo Examples:
        echo   cli-runner.bat ai-models-cli list
        echo   cli-runner.bat ai-models-cli health
        echo   cli-runner.bat ai-models-cli query "Explain quantum computing"
        echo   cli-runner.bat ai-models-cli chat --model gpt-4
        echo.
        echo For interactive mode, run without parameters
    ) else (
        echo Running: python cli/ai_models_cli.py %*
        echo.
        python cli/ai_models_cli.py %*
    )
) else (
    echo [ERROR] AI Models CLI script not found
)
cd ..\..\tools
echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu

:: HSP CLI Function
:hsp_cli
echo.
echo [INFO] Starting HSP CLI...
echo.
cd /d %~dp0..\packages\cli
if exist "cli/main.py" (
    if "%~1"=="" (
        echo Usage: cli-runner.bat hsp-cli [command] [options]
        echo.
        echo Running: python cli/main.py --help
        echo.
        python cli/main.py --help
        echo.
        echo Examples:
        echo   cli-runner.bat hsp-cli query "Hello"
        echo   cli-runner.bat hsp-cli publish_fact "The sky is blue" --confidence 0.9
        echo.
        echo For interactive mode, run without parameters
    ) else (
        echo Running: python cli/main.py %*
        echo.
        python cli/main.py %*
    )
) else (
    echo [ERROR] HSP CLI script not found
)
cd ..\..\tools
echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu

:: Install CLI as system command
:install_cli
echo.
echo [INFO] Installing CLI as system command...
echo.
cd /d %~dp0..\packages\cli
if exist "setup.py" (
    echo Installing CLI package...
    pip install -e .
    if %errorlevel% equ 0 (
        echo.
        echo [SUCCESS] CLI installed as system command!
        echo You can now use 'unified-ai' command from anywhere
        echo.
        echo Example usage:
        echo   unified-ai --help
        echo   unified-ai health
        echo   unified-ai chat "Hello"
    ) else (
        echo.
        echo [ERROR] Failed to install CLI package
    )
) else (
    echo [ERROR] setup.py not found
)
cd ..\..\tools
echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu

:: End Script Function
:end_script
echo.
echo Thank you for using Unified AI Project CLI Runner!
echo.
pause
exit /b 0