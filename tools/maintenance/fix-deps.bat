@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Dependency Fixer
color 0C

:: Add error handling and logging
set "LOG_FILE=%~dp0..\logs\fix-deps.log"
set "SCRIPT_NAME=fix-deps.bat"

:: Log script start
echo [%date% %time%] Script started: %SCRIPT_NAME% >> "%LOG_FILE%" 2>nul

:: Create logs directory if it doesn't exist
if not exist "%~dp0..\logs" mkdir "%~dp0..\logs"

echo ==========================================
echo   Unified AI Project - Dependency Fixer
echo ==========================================
echo.

:: Parse command line arguments
set "FIX_TYPE=all"
set "FORCE=false"
set "VERBOSE=false"
set "RECREATE_VENV=false"

:parse_args
if "%1"=="" goto args_done
if "%1"=="--python" (
    set "FIX_TYPE=python"
    shift
    goto parse_args
)
if "%1"=="--node" (
    set "FIX_TYPE=node"
    shift
    goto parse_args
)
if "%1"=="--all" (
    set "FIX_TYPE=all"
    shift
    goto parse_args
)
if "%1"=="--force" (
    set "FORCE=true"
    shift
    goto parse_args
)
if "%1"=="--verbose" (
    set "VERBOSE=true"
    shift
    goto parse_args
)
if "%1"=="--recreate-venv" (
    set "RECREATE_VENV=true"
    shift
    goto parse_args
)
if "%1"=="--help" (
    goto show_help
)
shift
goto parse_args

:args_done

:: Set project root
set "PROJECT_ROOT=%~dp0.."

:: Change to project root
cd /d "%PROJECT_ROOT%"

echo [INFO] Fixing %FIX_TYPE% dependencies...
echo [INFO] Force: %FORCE%, Verbose: %VERBOSE%, Recreate venv: %RECREATE_VENV%
echo.

:: Check Python environment
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8 or higher.
    echo [%date% %time%] ERROR: Python not found >> "%LOG_FILE%" 2>nul
    exit /b 1
)

:: Check Node.js environment
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Please install Node.js 16 or higher.
    echo [%date% %time%] ERROR: Node.js not found >> "%LOG_FILE%" 2>nul
    exit /b 1
)

:: Check pnpm
pnpm --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] pnpm not found. Installing pnpm...
    npm install -g pnpm
    if errorlevel 1 (
        echo [ERROR] Failed to install pnpm
        echo [%date% %time%] ERROR: Failed to install pnpm >> "%LOG_FILE%" 2>nul
        exit /b 1
    )
)

:: Fix Python dependencies
if "%FIX_TYPE%"=="python" goto fix_python_deps
if "%FIX_TYPE%"=="all" goto fix_python_deps

:fix_python_deps
echo [INFO] Fixing Python dependencies...

:: Recreate virtual environment if requested
if "%RECREATE_VENV%"=="true" (
    echo [INFO] Recreating virtual environment...
    if exist "venv" (
        echo [INFO] Removing existing virtual environment...
        rmdir /s /q "venv"
    )
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        echo [%date% %time%] ERROR: Failed to create virtual environment >> "%LOG_FILE%" 2>nul
        exit /b 1
    )
)

:: Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call "venv\Scripts\activate.bat"
) else (
    echo [WARNING] Virtual environment not found, using system Python
)

:: Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [WARNING] Failed to upgrade pip
)

:: Install Python dependencies
echo [INFO] Installing Python dependencies...
if exist "requirements.txt" (
    if "%FORCE%"=="true" (
        python -m pip install -r requirements.txt --force-reinstall
    ) else (
        python -m pip install -r requirements.txt
    )
    if errorlevel 1 (
        echo [ERROR] Failed to install Python dependencies
        echo [%date% %time%] ERROR: Failed to install Python dependencies >> "%LOG_FILE%" 2>nul
        exit /b 1
    )
) else (
    echo [WARNING] requirements.txt not found
)

:: Install backend dependencies
if exist "apps\backend\requirements.txt" (
    echo [INFO] Installing backend dependencies...
    if "%FORCE%"=="true" (
        python -m pip install -r apps\backend\requirements.txt --force-reinstall
    ) else (
        python -m pip install -r apps\backend\requirements.txt
    )
    if errorlevel 1 (
        echo [WARNING] Failed to install backend dependencies
    )
)

:: Install CLI dependencies
if exist "packages\cli\requirements.txt" (
    echo [INFO] Installing CLI dependencies...
    if "%FORCE%"=="true" (
        python -m pip install -r packages\cli\requirements.txt --force-reinstall
    ) else (
        python -m pip install -r packages\cli\requirements.txt
    )
    if errorlevel 1 (
        echo [WARNING] Failed to install CLI dependencies
    )
)

echo [SUCCESS] Python dependencies fixed
goto check_node_deps

:check_node_deps
if "%FIX_TYPE%"=="node" goto fix_node_deps
if "%FIX_TYPE%"=="all" goto fix_node_deps
goto fix_complete

:fix_node_deps
echo [INFO] Fixing Node.js dependencies...

:: Install pnpm dependencies
echo [INFO] Installing pnpm dependencies...
if exist "package.json" (
    if "%FORCE%"=="true" (
        pnpm install --force
    ) else (
        pnpm install
    )
    if errorlevel 1 (
        echo [ERROR] Failed to install pnpm dependencies
        echo [%date% %time%] ERROR: Failed to install pnpm dependencies >> "%LOG_FILE%" 2>nul
        exit /b 1
    )
) else (
    echo [WARNING] package.json not found
)

:: Install app dependencies
for /d %%i in (apps\*) do (
    if exist "%%i\package.json" (
        echo [INFO] Installing dependencies for %%i...
        cd /d "%%i"
        if "%FORCE%"=="true" (
            pnpm install --force
        ) else (
            pnpm install
        )
        if errorlevel 1 (
            echo [WARNING] Failed to install dependencies for %%i
        )
        cd /d "%PROJECT_ROOT%"
    )
)

:: Install package dependencies
for /d %%i in (packages\*) do (
    if exist "%%i\package.json" (
        echo [INFO] Installing dependencies for %%i...
        cd /d "%%i"
        if "%FORCE%"=="true" (
            pnpm install --force
        ) else (
            pnpm install
        )
        if errorlevel 1 (
            echo [WARNING] Failed to install dependencies for %%i
        )
        cd /d "%PROJECT_ROOT%"
    )
)

echo [SUCCESS] Node.js dependencies fixed

:fix_complete
echo.
echo [SUCCESS] All dependencies fixed successfully
echo [%date% %time%] All dependencies fixed successfully >> "%LOG_FILE%" 2>nul
exit /b 0

:show_help
echo.
echo Usage: fix-deps.bat [options]
echo.
echo Options:
echo   --python         Fix Python dependencies only
echo   --node           Fix Node.js dependencies only
echo   --all            Fix all dependencies (default)
echo   --force          Force reinstall all packages
echo   --verbose        Verbose output
echo   --recreate-venv  Recreate virtual environment
echo   --help           Show this help message
echo.
echo Examples:
echo   fix-deps.bat --python --force
echo   fix-deps.bat --node --verbose
echo   fix-deps.bat --all --recreate-venv
echo.
pause
exit /b 0
