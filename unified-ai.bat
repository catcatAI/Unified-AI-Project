@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Unified Management Tool
color 0A

echo ==========================================
echo   Unified AI Project - Unified Management
echo ==========================================
echo.

:: Main menu
:main_menu
cls
echo ==========================================
echo   Unified AI Project - Unified Management
echo ==========================================
echo.
echo Available Actions:
echo.
echo 1. Health Check - Check development environment
echo 2. Setup Environment - Install dependencies and setup
echo 3. Start Development - Launch development servers
echo 4. Run Tests - Execute test suite
echo 5. Git Management - Git status and cleanup
echo 6. Training Setup - Prepare for AI training
echo 7. Training Manager - Manage training data and processes
echo 8. CLI Tools - Access Unified AI CLI tools
echo 9. Emergency Git Fix - Recover from Git issues
echo 10. Fix Dependencies - Resolve dependency issues
echo 11. Exit
echo.

set "choice="
set /p "choice=Enter your choice (1-11): "
if defined choice set "choice=%choice: =%"
if not defined choice (
    echo [ERROR] No input provided
    timeout /t 2 >nul
    goto main_menu
)

if "%choice%"=="1" goto health_check
if "%choice%"=="2" goto setup_env
if "%choice%"=="3" goto start_dev
if "%choice%"=="4" goto run_tests
if "%choice%"=="5" goto git_management
if "%choice%"=="6" goto training_setup
if "%choice%"=="7" goto training_manager
if "%choice%"=="8" goto cli_tools
if "%choice%"=="9" goto emergency_git_fix
if "%choice%"=="10" goto fix_dependencies
if "%choice%"=="11" goto end_script

echo [ERROR] Invalid choice '%choice%'. Please enter 1-11.
timeout /t 2 >nul
goto main_menu

:: CLI Tools Function
:cli_tools
echo.
echo [INFO] Unified AI CLI Tools
echo.
echo Available CLI Tools:
echo.
echo 1. Unified CLI - General AI interactions
echo 2. AI Models CLI - Model management and interactions
echo 3. HSP CLI - Hyper-Structure Protocol tools
echo 4. CLI Runner - Dedicated CLI tool launcher
echo 5. Back to Main Menu
echo.

set "cli_choice="
set /p "cli_choice=Enter your choice (1-5): "
if defined cli_choice set "cli_choice=%cli_choice: =%"
if not defined cli_choice (
    echo [ERROR] No input provided
    timeout /t 2 >nul
    goto cli_tools
)

if "%cli_choice%"=="1" goto unified_cli
if "%cli_choice%"=="2" goto ai_models_cli
if "%cli_choice%"=="3" goto hsp_cli
if "%cli_choice%"=="4" goto cli_runner
if "%cli_choice%"=="5" goto main_menu

echo [ERROR] Invalid choice '%cli_choice%'. Please enter 1-5.
timeout /t 2 >nul
goto cli_tools

:: CLI Runner Function
:cli_runner
echo.
echo [INFO] Starting CLI Runner...
echo.
if exist "tools\cli-runner.bat" (
    call tools\cli-runner.bat
) else (
    echo [ERROR] CLI Runner script not found
    echo.
    echo Press any key to return to CLI tools menu...
    pause >nul
)
goto cli_tools

:: Unified CLI Function
:unified_cli
echo.
echo [INFO] Starting Unified CLI...
echo.
cd /d %~dp0packages\cli
if exist "cli/unified_cli.py" (
    echo Running: python cli/unified_cli.py --help
    echo.
    python cli/unified_cli.py --help
    echo.
    echo Enter CLI command (or press Enter to return to menu):
    echo Example: health, chat "Hello", analyze --code "def x(): pass"
    echo.
    set /p "cli_cmd=Command: "
    if defined cli_cmd (
        echo.
        echo Running: python cli/unified_cli.py %cli_cmd%
        echo.
        python cli/unified_cli.py %cli_cmd%
    )
) else (
    echo [ERROR] Unified CLI script not found
)
cd ..\..\..
echo.
echo Press any key to return to CLI tools menu...
pause >nul
goto cli_tools

:: AI Models CLI Function
:ai_models_cli
echo.
echo [INFO] Starting AI Models CLI...
echo.
cd /d %~dp0packages\cli
if exist "cli/ai_models_cli.py" (
    echo Running: python cli/ai_models_cli.py --help
    echo.
    python cli/ai_models_cli.py --help
    echo.
    echo Enter AI Models CLI command (or press Enter to return to menu):
    echo Example: list, health, query "Explain quantum computing"
    echo.
    set /p "ai_cmd=Command: "
    if defined ai_cmd (
        echo.
        echo Running: python cli/ai_models_cli.py %ai_cmd%
        echo.
        python cli/ai_models_cli.py %ai_cmd%
    )
) else (
    echo [ERROR] AI Models CLI script not found
)
cd ..\..\..
echo.
echo Press any key to return to CLI tools menu...
pause >nul
goto cli_tools

:: HSP CLI Function
:hsp_cli
echo.
echo [INFO] Starting HSP CLI...
echo.
cd /d %~dp0packages\cli
if exist "cli/main.py" (
    echo Running: python cli/main.py --help
    echo.
    python cli/main.py --help
    echo.
    echo Enter HSP CLI command (or press Enter to return to menu):
    echo Example: query "Hello", publish_fact "The sky is blue" --confidence 0.9
    echo.
    set /p "hsp_cmd=Command: "
    if defined hsp_cmd (
        echo.
        echo Running: python cli/main.py %hsp_cmd%
        echo.
        python cli/main.py %hsp_cmd%
    )
) else (
    echo [ERROR] HSP CLI script not found
)
cd ..\..\..
echo.
echo Press any key to return to CLI tools menu...
pause >nul
goto cli_tools

:: Health Check Function
:health_check
echo.
echo [INFO] Running Health Check...
echo.
if exist "tools\health-check.bat" (
    call tools\health-check.bat
) else (
    echo [ERROR] Health check script not found
)
echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu

:: Setup Environment Function
:setup_env
echo.
echo [INFO] Setting up environment...
echo.

:: Check environment
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not installed
    echo [INFO] Download from: https://nodejs.org/
    echo.
    pause
    goto main_menu
)

where python >nul 2>&1  
if %errorlevel% neq 0 (
    echo [ERROR] Python not installed
    echo [INFO] Download from: https://python.org/
    echo.
    pause
    goto main_menu
)

echo [OK] Environment ready
echo.

:: Check pnpm
where pnpm >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing pnpm...
    npm install -g pnpm
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install pnpm
        pause
        goto main_menu
    )
)

:: Install dependencies if needed
if not exist "node_modules" (
    echo [INFO] Installing Node.js dependencies...
    pnpm install
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies
        pause
        goto main_menu
    )
)

:: Setup Python environment
cd apps\backend
if not exist "venv" (
    echo [INFO] Creating Python virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        cd ..\..
        pause
        goto main_menu
    )
)

echo [INFO] Installing Python packages...
call venv\Scripts\activate.bat
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt >nul 2>&1
pip install -r requirements-dev.txt >nul 2>&1
cd ..\..

echo.
echo [SUCCESS] Environment setup completed!
echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu

:: Start Development Function
:start_dev
echo.
echo [INFO] Starting development environment...
echo.

:start_dev_menu
echo Choose an action:
echo.
echo 1. Start Full Development Environment
echo 2. Start Backend Only  
echo 3. Start Frontend Only
echo 4. Run Tests
echo 5. Clean Git Status
echo 6. Back to Main Menu
echo.

set "dev_choice="
set /p "dev_choice=Enter your choice (1-6): "
if defined dev_choice set "dev_choice=%dev_choice: =%"
if not defined dev_choice (
    echo [ERROR] No input provided
    timeout /t 2 >nul
    goto start_dev_menu
)

if "%dev_choice%"=="1" goto start_all
if "%dev_choice%"=="2" goto start_backend
if "%dev_choice%"=="3" goto start_frontend  
if "%dev_choice%"=="4" goto run_tests_dev
if "%dev_choice%"=="5" goto clean_git_dev
if "%dev_choice%"=="6" goto main_menu

echo [ERROR] Invalid choice '%dev_choice%'. Please enter 1-6.
timeout /t 2 >nul
goto start_dev_menu

:start_all
echo.
echo Starting full development environment...
echo.
echo Services will be available at:
echo - Backend API: http://localhost:8000
echo - Frontend Dashboard: http://localhost:3000
echo.

start "Backend API" cmd /k "cd /d apps\backend && call venv\Scripts\activate.bat && uvicorn src.services.main_api_server:app --reload --host 0.0.0.0 --port 8000"
start "Frontend" cmd /k "pnpm --filter frontend-dashboard dev"

echo [SUCCESS] Development environment started!
echo Check the opened windows for service status.
echo.
pause
goto start_dev_menu

:start_backend
echo.
echo Starting backend services only...
echo.
start "Backend API" cmd /k "cd /d apps\backend && call venv\Scripts\activate.bat && uvicorn src.services.main_api_server:app --reload --host 0.0.0.0 --port 8000"

echo [SUCCESS] Backend services started!
echo - API Server: http://localhost:8000
echo.
pause
goto start_dev_menu

:start_frontend
echo.
echo Starting frontend service only...
echo.
start "Frontend" cmd /k "pnpm --filter frontend-dashboard dev"

echo [SUCCESS] Frontend service started!
echo - Dashboard: http://localhost:3000
echo.
pause
goto start_dev_menu

:run_tests_dev
echo.
echo Running test suite...
echo.
if exist "tools\run-tests.bat" (
    call tools\run-tests.bat
) else (
    echo [ERROR] Test script not found
)
echo.
pause
goto start_dev_menu

:clean_git_dev
echo.
echo Cleaning Git status...
echo.
if exist "tools\safe-git-cleanup.bat" (
    call tools\safe-git-cleanup.bat
) else (
    echo [ERROR] Git cleanup script not found
)
echo.
pause
goto start_dev_menu

:: Run Tests Function
:run_tests
echo.
echo [INFO] Running test suite...
echo.
if exist "tools\run-tests.bat" (
    call tools\run-tests.bat
) else (
    echo [ERROR] Test script not found
)
echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu

:: Git Management Function
:git_management
echo.
echo [INFO] Git Management...
echo.
echo 1. Clean Git Status
echo 2. Emergency Git Fix
echo 3. Back to Main Menu
echo.

set "git_choice="
set /p "git_choice=Enter your choice (1-3): "
if defined git_choice set "git_choice=%git_choice: =%"
if not defined git_choice (
    echo [ERROR] No input provided
    timeout /t 2 >nul
    goto git_management
)

if "%git_choice%"=="1" goto clean_git
if "%git_choice%"=="2" goto emergency_git_fix
if "%git_choice%"=="3" goto main_menu

echo [ERROR] Invalid choice '%git_choice%'. Please enter 1-3.
timeout /t 2 >nul
goto git_management

:clean_git
echo.
echo Cleaning Git status...
echo.
if exist "tools\safe-git-cleanup.bat" (
    call tools\safe-git-cleanup.bat
) else (
    echo [ERROR] Git cleanup script not found
)
echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu

:: Training Setup Function
:training_setup
echo.
echo [INFO] Setting up training environment...
echo.
if exist "tools\setup-training.bat" (
    call tools\setup-training.bat
) else (
    echo [ERROR] Training setup script not found
)
echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu

:: Training Manager Function
:training_manager
echo.
echo [INFO] Launching Training Manager...
echo.
if exist "tools\train-manager.bat" (
    call tools\train-manager.bat
) else (
    echo [ERROR] Training manager script not found
)
echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu

:: Emergency Git Fix Function
:emergency_git_fix
echo.
echo [INFO] Running emergency Git fix...
echo.
if exist "tools\emergency-git-fix.bat" (
    call tools\emergency-git-fix.bat
) else (
    echo [ERROR] Emergency Git fix script not found
)
echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu

:: Fix Dependencies Function
:fix_dependencies
echo.
echo [INFO] Fixing dependencies...
echo.
if exist "tools\fix-dependencies.bat" (
    call tools\fix-dependencies.bat
) else (
    echo [ERROR] Fix dependencies script not found
)
echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu

:: End Script Function
:end_script
echo.
echo Thank you for using Unified AI Project!
echo.
pause
exit /b 0