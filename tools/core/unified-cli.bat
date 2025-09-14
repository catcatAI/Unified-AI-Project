@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Unified CLI
color 0F

:: Add error handling and logging
set "LOG_FILE=%~dp0..\logs\unified-cli.log"
set "SCRIPT_NAME=unified-cli.bat"

:: Log script start
echo [%date% %time%] Script started: %SCRIPT_NAME% >> "%LOG_FILE%" 2>nul

:: Create logs directory if it doesn't exist
if not exist "%~dp0..\logs" mkdir "%~dp0..\logs"

echo ==========================================
echo   Unified AI Project - Unified CLI
echo ==========================================
echo.

:: Parse command line arguments
set "COMMAND="
set "SUBCOMMAND="
set "VERBOSE=false"
set "HELP=false"

:parse_args
if "%1"=="" goto args_done
if "%1"=="--help" (
    set "HELP=true"
    shift
    goto parse_args
)
if "%1"=="--verbose" (
    set "VERBOSE=true"
    shift
    goto parse_args
)
if "%1"=="-v" (
    set "VERBOSE=true"
    shift
    goto parse_args
)
if "%COMMAND%"=="" (
    set "COMMAND=%1"
    shift
    goto parse_args
)
if "%SUBCOMMAND%"=="" (
    set "SUBCOMMAND=%1"
    shift
    goto parse_args
)
shift
goto parse_args

:args_done

:: Show help if requested
if "%HELP%"=="true" goto show_help

:: If no command provided, show interactive menu
if "%COMMAND%"=="" goto interactive_menu

:: Execute command
goto execute_command

:interactive_menu
cls
echo ==========================================
echo   Unified AI Project - CLI Menu
echo ==========================================
echo.
echo Available Commands:
echo.
echo 1. Health Check - Check system health (健康檢查)
echo 2. Development - Development tools (開發工具)
echo 3. Training - Training management (訓練管理)
echo 4. Data - Data management (數據管理)
echo 5. Model - Model management (模型管理)
echo 6. Git - Git operations (Git操作)
echo 7. Backup - Backup management (備份管理)
echo 8. System - System information (系統信息)
echo 9. Exit (退出)
echo.

:: Get user choice
:get_choice
set "choice="
set /p "choice=Enter your choice (1-9): "
if not defined choice (
    echo [ERROR] No input provided
    goto get_choice
)

:: Validate choice
for %%i in (1 2 3 4 5 6 7 8 9) do (
    if "%choice%"=="%%i" (
        goto choice_%%i
    )
)

echo [ERROR] Invalid choice '%choice%'. Please enter a valid option.
timeout /t 2 >nul
goto get_choice

:choice_1
set "COMMAND=health"
goto execute_command
:choice_2
set "COMMAND=dev"
goto execute_command
:choice_3
set "COMMAND=train"
goto execute_command
:choice_4
set "COMMAND=data"
goto execute_command
:choice_5
set "COMMAND=model"
goto execute_command
:choice_6
set "COMMAND=git"
goto execute_command
:choice_7
set "COMMAND=backup"
goto execute_command
:choice_8
set "COMMAND=system"
goto execute_command
:choice_9
goto end_script

:execute_command
:: Set project root
set "PROJECT_ROOT=%~dp0.."

:: Change to project root
cd /d "%PROJECT_ROOT%"

:: Execute command based on type
if "%COMMAND%"=="health" goto health_command
if "%COMMAND%"=="dev" goto dev_command
if "%COMMAND%"=="train" goto train_command
if "%COMMAND%"=="data" goto data_command
if "%COMMAND%"=="model" goto model_command
if "%COMMAND%"=="git" goto git_command
if "%COMMAND%"=="backup" goto backup_command
if "%COMMAND%"=="system" goto system_command

echo [ERROR] Unknown command: %COMMAND%
echo [%date% %time%] ERROR: Unknown command: %COMMAND% >> "%LOG_FILE%" 2>nul
exit /b 1

:health_command
echo [INFO] Running health check...
if exist "tools\core\health-check.bat" (
    call "tools\core\health-check.bat"
) else if exist "tools\health-check.bat" (
    call "tools\health-check.bat"
) else (
    echo [ERROR] Health check script not found
    exit /b 1
)
goto end_script

:dev_command
echo [INFO] Development tools...
if "%SUBCOMMAND%"=="" (
    echo Available subcommands:
    echo   start - Start development environment
    echo   stop  - Stop development environment
    echo   test  - Run tests
    echo   build - Build project
    echo.
    set /p "SUBCOMMAND=Enter subcommand: "
)

if "%SUBCOMMAND%"=="start" (
    if exist "tools\core\start-dev.bat" (
        call "tools\core\start-dev.bat"
    ) else if exist "tools\start-dev.bat" (
        call "tools\start-dev.bat"
    ) else (
        echo [ERROR] Start dev script not found
        exit /b 1
    )
) else if "%SUBCOMMAND%"=="stop" (
    echo [INFO] Stopping development environment...
    taskkill /f /im node.exe 2>nul
    taskkill /f /im python.exe 2>nul
    echo [SUCCESS] Development environment stopped
) else if "%SUBCOMMAND%"=="test" (
    if exist "tools\core\run-tests.bat" (
        call "tools\core\run-tests.bat" --all
    ) else if exist "tools\run-tests.bat" (
        call "tools\run-tests.bat"
    ) else (
        echo [ERROR] Test script not found
        exit /b 1
    )
) else if "%SUBCOMMAND%"=="build" (
    echo [INFO] Building project...
    if exist "package.json" (
        pnpm build
    ) else (
        echo [ERROR] No build script found
        exit /b 1
    )
) else (
    echo [ERROR] Unknown subcommand: %SUBCOMMAND%
    exit /b 1
)
goto end_script

:train_command
echo [INFO] Training management...
if "%SUBCOMMAND%"=="" (
    echo Available subcommands:
    echo   setup - Setup training environment
    echo   start - Start training
    echo   stop  - Stop training
    echo   status - Show training status
    echo.
    set /p "SUBCOMMAND=Enter subcommand: "
)

if "%SUBCOMMAND%"=="setup" (
    if exist "tools\training\setup-training.bat" (
        call "tools\training\setup-training.bat"
    ) else if exist "tools\setup-training.bat" (
        call "tools\setup-training.bat"
    ) else (
        echo [ERROR] Setup training script not found
        exit /b 1
    )
) else if "%SUBCOMMAND%"=="start" (
    if exist "tools\training\train-manager.bat" (
        call "tools\training\train-manager.bat"
    ) else if exist "tools\train-manager.bat" (
        call "tools\train-manager.bat"
    ) else (
        echo [ERROR] Train manager script not found
        exit /b 1
    )
) else if "%SUBCOMMAND%"=="stop" (
    echo [INFO] Stopping training...
    taskkill /f /im python.exe 2>nul
    echo [SUCCESS] Training stopped
) else if "%SUBCOMMAND%"=="status" (
    echo [INFO] Training status...
    if exist "training\status.json" (
        type "training\status.json"
    ) else (
        echo [INFO] No training status found
    )
) else (
    echo [ERROR] Unknown subcommand: %SUBCOMMAND%
    exit /b 1
)
goto end_script

:data_command
echo [INFO] Data management...
if "%SUBCOMMAND%"=="" (
    echo Available subcommands:
    echo   process - Process data
    echo   analyze - Analyze data
    echo   backup  - Backup data
    echo   restore - Restore data
    echo.
    set /p "SUBCOMMAND=Enter subcommand: "
)

if "%SUBCOMMAND%"=="process" (
    if exist "tools\run_data_pipeline.bat" (
        call "tools\run_data_pipeline.bat"
    ) else (
        echo [ERROR] Data pipeline script not found
        exit /b 1
    )
) else if "%SUBCOMMAND%"=="analyze" (
    echo [INFO] Analyzing data...
    python -c "import sys; sys.path.append('apps/backend'); from data_analysis import analyze_data; analyze_data()"
) else if "%SUBCOMMAND%"=="backup" (
    if exist "tools\utilities\backup.bat" (
        call "tools\utilities\backup.bat" --data
    ) else (
        echo [ERROR] Backup script not found
        exit /b 1
    )
) else if "%SUBCOMMAND%"=="restore" (
    echo [INFO] Data restore not implemented yet
) else (
    echo [ERROR] Unknown subcommand: %SUBCOMMAND%
    exit /b 1
)
goto end_script

:model_command
echo [INFO] Model management...
if exist "packages\cli\cli\main.py" (
    python "packages\cli\cli\main.py" model %SUBCOMMAND%
) else (
    echo [ERROR] Model CLI not found
    exit /b 1
)
goto end_script

:git_command
echo [INFO] Git operations...
if "%SUBCOMMAND%"=="" (
    echo Available subcommands:
    echo   status - Show git status
    echo   clean  - Clean git repository
    echo   fix    - Fix git issues
    echo   emergency - Emergency git fix
    echo.
    set /p "SUBCOMMAND=Enter subcommand: "
)

if "%SUBCOMMAND%"=="status" (
    if exist "tools\maintenance\git-cleanup.bat" (
        call "tools\maintenance\git-cleanup.bat" --status
    ) else (
        git status
    )
) else if "%SUBCOMMAND%"=="clean" (
    if exist "tools\maintenance\git-cleanup.bat" (
        call "tools\maintenance\git-cleanup.bat" --clean --force
    ) else (
        echo [ERROR] Git cleanup script not found
        exit /b 1
    )
) else if "%SUBCOMMAND%"=="fix" (
    if exist "tools\maintenance\git-cleanup.bat" (
        call "tools\maintenance\git-cleanup.bat" --fix-10k
    ) else (
        echo [ERROR] Git fix script not found
        exit /b 1
    )
) else if "%SUBCOMMAND%"=="emergency" (
    if exist "tools\maintenance\git-cleanup.bat" (
        call "tools\maintenance\git-cleanup.bat" --emergency --force
    ) else (
        echo [ERROR] Emergency git fix script not found
        exit /b 1
    )
) else (
    echo [ERROR] Unknown subcommand: %SUBCOMMAND%
    exit /b 1
)
goto end_script

:backup_command
echo [INFO] Backup management...
if exist "tools\utilities\backup.bat" (
    call "tools\utilities\backup.bat" --full --compress
) else (
    echo [ERROR] Backup script not found
    exit /b 1
)
goto end_script

:system_command
echo [INFO] System information...
echo.
echo Project Information:
echo   Project Root: %PROJECT_ROOT%
echo   Current Directory: %CD%
echo   Script Name: %SCRIPT_NAME%
echo   Log File: %LOG_FILE%
echo.
echo System Information:
systeminfo | findstr /C:"OS Name" /C:"OS Version" /C:"Total Physical Memory"
echo.
echo Python Information:
python --version 2>nul || echo Python not found
echo.
echo Node.js Information:
node --version 2>nul || echo Node.js not found
echo.
echo pnpm Information:
pnpm --version 2>nul || echo pnpm not found
goto end_script

:show_help
echo.
echo Usage: unified-cli.bat [command] [subcommand] [options]
echo.
echo Commands:
echo   health          Health check
echo   dev             Development tools
echo   train           Training management
echo   data            Data management
echo   model           Model management
echo   git             Git operations
echo   backup          Backup management
echo   system          System information
echo.
echo Options:
echo   --verbose, -v   Verbose output
echo   --help          Show this help message
echo.
echo Examples:
echo   unified-cli.bat health
echo   unified-cli.bat dev start
echo   unified-cli.bat train setup
echo   unified-cli.bat git status
echo   unified-cli.bat backup --compress
echo.
pause
exit /b 0

:end_script
echo.
echo [SUCCESS] Command completed successfully
echo [%date% %time%] Command completed successfully >> "%LOG_FILE%" 2>nul
exit /b 0
