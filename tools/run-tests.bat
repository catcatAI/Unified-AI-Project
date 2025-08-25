@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Test Suite
color 0B

echo ==========================================
echo    Unified AI Project - Test Suite
echo ==========================================
echo.

:: Check environment
where pnpm >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pnpm not installed. Install with: npm install -g pnpm
    echo.
    pause
    exit /b 1
)
echo [OK] Environment ready
echo.

:: Main menu with clear exit condition
:main_loop
echo Select test type:
echo.
echo 1. All Tests
echo 2. Backend Only  
echo 3. Frontend Only
echo 4. Desktop Only
echo 5. Coverage Reports
echo 6. Quick Tests
echo 7. Watch Mode
echo 8. Check Git Status
echo 9. Exit
echo.

:: Get user input with validation
set "choice="
set /p "choice=Choose (1-9): "

:: Remove spaces and validate
if defined choice set "choice=%choice: =%"
if not defined choice (
    echo [ERROR] No input provided
    timeout /t 2 >nul
    goto main_loop
)

:: Process choice
if "%choice%"=="1" call :test_all
if "%choice%"=="2" call :test_backend
if "%choice%"=="3" call :test_frontend
if "%choice%"=="4" call :test_desktop
if "%choice%"=="5" call :test_coverage
if "%choice%"=="6" call :test_quick
if "%choice%"=="7" call :test_watch
if "%choice%"=="8" call :check_git
if "%choice%"=="9" goto exit_script

:: Invalid input handling
echo [ERROR] Invalid choice '%choice%'. Please enter 1-9.
timeout /t 2 >nul
goto main_loop

:: Test functions
:test_all
echo.
echo [INFO] Running all tests...
echo.

set "backend_result=0"
set "frontend_result=0"
set "desktop_result=0"

:: Backend
echo [1/3] Backend tests...
cd apps\backend
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat >nul 2>&1
    set PYTHONPATH=%PYTHONPATH%;%cd%\src
    pytest --tb=short -v -x --maxfail=5
    set "backend_result=!errorlevel!"
) else (
    echo [ERROR] Python venv not found
    set "backend_result=1"
)
cd ..\..

:: Frontend
echo [2/3] Frontend tests...
pnpm --filter frontend-dashboard test --passWithNoTests >nul 2>&1
set "frontend_result=!errorlevel!"
if !frontend_result! neq 0 (
    cd apps\frontend-dashboard
    npm test --passWithNoTests >nul 2>&1
    set "frontend_result=!errorlevel!"
    cd ..\..
)

:: Desktop
echo [3/3] Desktop tests...
pnpm --filter desktop-app test --passWithNoTests >nul 2>&1
set "desktop_result=!errorlevel!"
if !desktop_result! neq 0 (
    cd apps\desktop-app
    npm test --passWithNoTests >nul 2>&1
    set "desktop_result=!errorlevel!"
    cd ..\..
)

:: Results
echo.
echo ==========================================
echo    Test Results Summary
echo ==========================================
if !backend_result!==0 (
    echo [PASS] Backend Tests: All tests passed
) else (
    echo [FAIL] Backend Tests: Failed with exit code !backend_result!
    echo        Suggestion: Check Python environment and test files
)

if !frontend_result!==0 (
    echo [PASS] Frontend Tests: All tests passed
) else (
    echo [FAIL] Frontend Tests: Failed with exit code !frontend_result!
    echo        Suggestion: Check Node.js dependencies and Jest config
)

if !desktop_result!==0 (
    echo [PASS] Desktop Tests: All tests passed
) else (
    echo [FAIL] Desktop Tests: Failed with exit code !desktop_result!
    echo        Suggestion: Check Electron setup and test environment
)

set /a "total_failures=!backend_result!+!frontend_result!+!desktop_result!"
echo.
if !total_failures!==0 (
    echo [SUCCESS] All tests completed successfully!
    echo [INFO] Your code is ready for deployment.
) else (
    echo [WARNING] !total_failures! component(s) failed testing
    echo [INFO] Review the suggestions above to fix issues
)
echo ==========================================
echo.
pause
goto main_loop

:test_backend
echo.
echo [INFO] Backend tests only...
echo.
cd apps\backend
if exist venv\Scripts\activate.bat (
    echo [INFO] Activating Python virtual environment...
    call venv\Scripts\activate.bat >nul 2>&1
    
    echo [INFO] Running pytest...
    set PYTHONPATH=%PYTHONPATH%;%cd%\src
    pytest --tb=short -v
    set "test_result=!errorlevel!"
    
    if !test_result!==0 (
        echo [SUCCESS] Backend tests passed
    ) else (
        echo [FAIL] Backend tests failed with exit code: !test_result!
        echo.
        echo [TROUBLESHOOTING]
        echo - Check if all Python dependencies are installed
        echo - Verify test files exist in tests/ directory
        echo - Check pytest configuration in pytest.ini
        echo - Run start-dev.bat to refresh environment
    )
) else (
    echo [ERROR] Python virtual environment not found
    echo.
    echo [SOLUTION]
    echo 1. Run start-dev.bat to automatically set up environment
    echo 2. Or manually create:
    echo    cd apps\backend
    echo    python -m venv venv
    echo    call venv\Scripts\activate.bat
    echo    pip install -r requirements.txt
)
cd ..\..
echo.
pause
goto main_loop

:test_frontend
echo.
echo [INFO] Frontend tests only...
pnpm --filter frontend-dashboard test --passWithNoTests
pause
goto main_loop

:test_desktop
echo.
echo [INFO] Desktop tests only...
pnpm --filter desktop-app test --passWithNoTests
pause
goto main_loop

:test_coverage
echo.
echo [INFO] Generating coverage reports...
echo.
cd apps\backend
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat >nul 2>&1
    set PYTHONPATH=%PYTHONPATH%;%cd%\src
    pytest --tb=short --cov=. --cov-report=html
    echo [SUCCESS] Backend coverage report generated in htmlcov/
) else (
    echo [ERROR] Python venv not found
)
cd ..\..
pnpm --filter frontend-dashboard test:coverage
echo.
echo [INFO] Coverage reports completed.
pause
goto main_loop

:test_quick
echo.
echo [INFO] Running quick tests...
echo.
cd apps\backend
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat >nul 2>&1
    set PYTHONPATH=%PYTHONPATH%;%cd%\src
    pytest --tb=short -v -x --maxfail=1
) else (
    echo [ERROR] Python venv not found
)
cd ..\..
echo.
echo [INFO] Quick tests completed.
pause
goto main_loop

:test_watch
echo.
echo [INFO] Starting test watch mode...
echo.
cd apps\backend
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat >nul 2>&1
    set PYTHONPATH=%PYTHONPATH%;%cd%\src
    pytest --tb=short -v --watch
) else (
    echo [ERROR] Python venv not found
)
cd ..\..
echo.
echo [INFO] Watch mode completed.
pause
goto main_loop

:check_git
echo.
echo [INFO] Checking Git status...
echo.
git status
echo.
echo [INFO] For detailed Git cleanup, run safe-git-cleanup.bat
pause
goto main_loop

:exit_script
echo.
echo Thank you for using Unified AI Project Test Suite!
echo.
pause
exit /b 0