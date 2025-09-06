@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Test Runner
color 0B

:: Add error handling and logging
set "LOG_FILE=%~dp0..\logs\test-runner.log"
set "SCRIPT_NAME=run-tests.bat"

:: Log script start
echo [%date% %time%] Script started: %SCRIPT_NAME% >> "%LOG_FILE%" 2>nul

:: Create logs directory if it doesn't exist
if not exist "%~dp0..\logs" mkdir "%~dp0..\logs"

echo ==========================================
echo   Unified AI Project - Test Runner
echo ==========================================
echo.

:: Parse command line arguments
set "TEST_TYPE=all"
set "VERBOSE=false"
set "COVERAGE=false"
set "PARALLEL=false"

:parse_args
if "%1"=="" goto args_done
if "%1"=="--unit" (
    set "TEST_TYPE=unit"
    shift
    goto parse_args
)
if "%1"=="--integration" (
    set "TEST_TYPE=integration"
    shift
    goto parse_args
)
if "%1"=="--e2e" (
    set "TEST_TYPE=e2e"
    shift
    goto parse_args
)
if "%1"=="--all" (
    set "TEST_TYPE=all"
    shift
    goto parse_args
)
if "%1"=="--verbose" (
    set "VERBOSE=true"
    shift
    goto parse_args
)
if "%1"=="--coverage" (
    set "COVERAGE=true"
    shift
    goto parse_args
)
if "%1"=="--parallel" (
    set "PARALLEL=true"
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

echo [INFO] Running %TEST_TYPE% tests...
echo [INFO] Verbose: %VERBOSE%, Coverage: %COVERAGE%, Parallel: %PARALLEL%
echo.

:: Check Python environment
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8 or higher.
    echo [%date% %time%] ERROR: Python not found >> "%LOG_FILE%" 2>nul
    exit /b 1
)

:: Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call "venv\Scripts\activate.bat"
) else (
    echo [WARNING] Virtual environment not found, using system Python
)

:: Run tests based on type
if "%TEST_TYPE%"=="unit" goto run_unit_tests
if "%TEST_TYPE%"=="integration" goto run_integration_tests
if "%TEST_TYPE%"=="e2e" goto run_e2e_tests
if "%TEST_TYPE%"=="all" goto run_all_tests

:run_unit_tests
echo [INFO] Running unit tests...
if "%COVERAGE%"=="true" (
    if "%VERBOSE%"=="true" (
        python -m pytest tests/unit/ --cov=apps --cov-report=html --cov-report=term -v
    ) else (
        python -m pytest tests/unit/ --cov=apps --cov-report=html --cov-report=term
    )
) else (
    if "%VERBOSE%"=="true" (
        python -m pytest tests/unit/ -v
    ) else (
        python -m pytest tests/unit/
    )
)
goto test_complete

:run_integration_tests
echo [INFO] Running integration tests...
if "%COVERAGE%"=="true" (
    if "%VERBOSE%"=="true" (
        python -m pytest tests/integration/ --cov=apps --cov-report=html --cov-report=term -v
    ) else (
        python -m pytest tests/integration/ --cov=apps --cov-report=html --cov-report=term
    )
) else (
    if "%VERBOSE%"=="true" (
        python -m pytest tests/integration/ -v
    ) else (
        python -m pytest tests/integration/
    )
)
goto test_complete

:run_e2e_tests
echo [INFO] Running end-to-end tests...
if "%COVERAGE%"=="true" (
    if "%VERBOSE%"=="true" (
        python -m pytest tests/e2e/ --cov=apps --cov-report=html --cov-report=term -v
    ) else (
        python -m pytest tests/e2e/ --cov=apps --cov-report=html --cov-report=term
    )
) else (
    if "%VERBOSE%"=="true" (
        python -m pytest tests/e2e/ -v
    ) else (
        python -m pytest tests/e2e/
    )
)
goto test_complete

:run_all_tests
echo [INFO] Running all tests...
if "%COVERAGE%"=="true" (
    if "%VERBOSE%"=="true" (
        python -m pytest tests/ --cov=apps --cov-report=html --cov-report=term -v
    ) else (
        python -m pytest tests/ --cov=apps --cov-report=html --cov-report=term
    )
) else (
    if "%VERBOSE%"=="true" (
        python -m pytest tests/ -v
    ) else (
        python -m pytest tests/
    )
)
goto test_complete

:test_complete
if errorlevel 1 (
    echo [ERROR] Tests failed
    echo [%date% %time%] Tests failed >> "%LOG_FILE%" 2>nul
    exit /b 1
) else (
    echo [SUCCESS] All tests passed
    echo [%date% %time%] All tests passed >> "%LOG_FILE%" 2>nul
    exit /b 0
)

:show_help
echo.
echo Usage: run-tests.bat [options]
echo.
echo Options:
echo   --unit         Run unit tests only
echo   --integration  Run integration tests only
echo   --e2e          Run end-to-end tests only
echo   --all          Run all tests (default)
echo   --verbose      Verbose output
echo   --coverage     Generate coverage report
echo   --parallel     Run tests in parallel
echo   --help         Show this help message
echo.
echo Examples:
echo   run-tests.bat --unit --verbose
echo   run-tests.bat --all --coverage
echo   run-tests.bat --integration --parallel
echo.
pause
exit /b 0
