@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Test Runner
color 0B

echo ==========================================
echo    Unified AI Project - Test Runner
echo ==========================================
echo.

:: Environment check
echo [INFO] Checking environment...
where pnpm >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pnpm not found. Please install it first:
    echo   npm install -g pnpm
    echo.
    pause
    exit /b 1
)
echo [OK] Environment is ready
echo.

:main_menu
echo Select test operation:
echo.
echo 1. Run All Tests
echo 2. Backend Tests Only
echo 3. Frontend Tests Only
echo 4. Desktop App Tests Only
echo 5. Generate Coverage Reports
echo 6. Quick Tests
echo 7. Watch Mode
echo 8. Health Check
echo 9. Exit
echo.

set "choice="
set /p "choice=Enter your choice (1-9): "
if defined choice set "choice=%choice: =%"
if not defined choice goto invalid_choice

if "%choice%"=="1" goto run_all_tests
if "%choice%"=="2" goto run_backend_tests
if "%choice%"=="3" goto run_frontend_tests
if "%choice%"=="4" goto run_desktop_tests
if "%choice%"=="5" goto run_coverage_tests
if "%choice%"=="6" goto run_quick_tests
if "%choice%"=="7" goto run_watch_mode
if "%choice%"=="8" goto run_health_check
if "%choice%"=="9" goto exit_script

:invalid_choice
echo.
echo [ERROR] Invalid choice '%choice%'. Please select 1-9.
echo.
timeout /t 2 >nul
goto main_menu

:run_all_tests
echo.
echo Running all tests...
echo.

set "backend_result=0"
set "frontend_result=0"
set "desktop_result=0"

:: Backend tests
echo [1/3] Backend Tests
cd apps\backend
if exist venv\Scripts\activate.bat (
    echo [INFO] Running Python tests...
    call venv\Scripts\activate.bat >nul 2>&1
    pytest --tb=short -v --maxfail=5
    set "backend_result=!errorlevel!"
) else (
    echo [ERROR] Python virtual environment not found
    set "backend_result=1"
)
cd ..\..

:: Frontend tests
echo.
echo [2/3] Frontend Tests
echo [INFO] Running frontend tests...
pnpm --filter frontend-dashboard test --passWithNoTests
set "frontend_result=!errorlevel!"
if !frontend_result! neq 0 (
    echo [WARN] pnpm failed, trying npm...
    cd apps\frontend-dashboard
    npm test --passWithNoTests
    set "frontend_result=!errorlevel!"
    cd ..\..
)

:: Desktop tests
echo.
echo [3/3] Desktop App Tests
echo [INFO] Running desktop app tests...
pnpm --filter desktop-app test --passWithNoTests
set "desktop_result=!errorlevel!"
if !desktop_result! neq 0 (
    echo [WARN] pnpm failed, trying npm...
    cd apps\desktop-app
    npm test --passWithNoTests
    set "desktop_result=!errorlevel!"
    cd ..\..
)

:: Results
echo.
echo === Test Results ===
if !backend_result!==0 (echo [PASS] Backend Tests) else (echo [FAIL] Backend Tests)
if !frontend_result!==0 (echo [PASS] Frontend Tests) else (echo [FAIL] Frontend Tests)
if !desktop_result!==0 (echo [PASS] Desktop Tests) else (echo [FAIL] Desktop Tests)
echo.
pause
goto main_menu

:run_backend_tests
echo.
echo ==========================================
echo    Backend Tests Only
echo ==========================================
echo.
echo [INFO] Starting backend tests...
cd apps\backend

if exist venv\Scripts\activate.bat (
    echo [INFO] Activating Python virtual environment...
    call venv\Scripts\activate.bat >nul 2>&1
    echo [INFO] Environment activated
    echo [INFO] Running pytest with verbose output...
    pytest --tb=short -v
    set "test_result=!errorlevel!"
    
    echo [INFO] Backend tests completed
    
    if !test_result!==0 (
        echo [SUCCESS] Backend tests passed!
    ) else (
        echo [FAIL] Backend tests failed with exit code: !test_result!
        echo [HINT] Check error messages above for details
    )
) else (
    echo [ERROR] Python virtual environment not found
    echo.
    echo Setup instructions:
    echo 1. Run start-dev.bat for automatic setup, OR
    echo 2. Manual setup:
    echo    cd apps\backend
    echo    python -m venv venv
    echo    call venv\Scripts\activate.bat
    echo    pip install -r requirements.txt
    echo    pip install -r requirements-dev.txt
)
cd ..\..
echo.
pause
goto main_menu

:run_frontend_tests
echo.
echo ==========================================
echo    Frontend Tests Only
echo ==========================================
echo.
echo [INFO] Starting frontend tests...
echo [INFO] Running frontend tests with pnpm...
pnpm --filter frontend-dashboard test --passWithNoTests
set "test_result=!errorlevel!"

if !test_result! neq 0 (
    echo [WARN] pnpm failed, trying npm fallback...
    cd apps\frontend-dashboard
    npm test --passWithNoTests
    set "test_result=!errorlevel!"
    cd ..\..
)

echo [INFO] Frontend tests completed

if !test_result!==0 (
    echo [SUCCESS] Frontend tests passed!
) else (
    echo [FAIL] Frontend tests failed with exit code: !test_result!
    echo.
    echo Troubleshooting checklist:
    echo - Node.js dependencies installed?
    echo - Jest configuration correct?
    echo - Test files exist?
    echo - Package.json scripts configured?
)
echo.
pause
goto main_menu

:run_desktop_tests
echo.
echo ==========================================
echo    Desktop App Tests Only
echo ==========================================
echo.
echo [INFO] Starting desktop app tests...
echo [INFO] Running desktop app tests with pnpm...
pnpm --filter desktop-app test --passWithNoTests
set "test_result=!errorlevel!"

if !test_result! neq 0 (
    echo [WARN] pnpm failed, trying npm fallback...
    cd apps\desktop-app
    npm test --passWithNoTests
    set "test_result=!errorlevel!"
    cd ..\..
)

echo [INFO] Desktop tests completed

if !test_result!==0 (
    echo [SUCCESS] Desktop app tests passed!
) else (
    echo [FAIL] Desktop app tests failed with exit code: !test_result!
    echo.
    echo Troubleshooting checklist:
    echo - Electron properly installed?
    echo - Jest configured for Electron environment?
    echo - Test files exist and accessible?
)
echo.
pause
goto main_menu

:run_coverage_tests
echo.
echo ==========================================
echo    Test Coverage Reports
echo ==========================================
echo.

echo [STEP 1/3] Backend Coverage
echo [INFO] Generating backend coverage...
cd apps\backend
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat >nul 2>&1
    echo [INFO] Running pytest with coverage...
    pytest --cov=src --cov-report=html --cov-report=term-missing
    echo [INFO] Backend coverage report: apps\backend\htmlcov\index.html
) else (
    echo [ERROR] Python virtual environment not found
)
cd ..\..

echo.
echo [STEP 2/3] Frontend Coverage
echo [INFO] Generating frontend coverage...
pnpm --filter frontend-dashboard test:coverage >nul 2>&1 || (
    echo [WARN] pnpm failed, trying npm...
    cd apps\frontend-dashboard
    npm run test:coverage >nul 2>&1
    cd ..\..
)
echo [INFO] Frontend coverage report: apps\frontend-dashboard\coverage\index.html

echo.
echo [STEP 3/3] Desktop App Coverage
echo [INFO] Generating desktop coverage...
pnpm --filter desktop-app test:coverage >nul 2>&1 || (
    echo [WARN] pnpm failed, trying npm...
    cd apps\desktop-app
    npm run test:coverage >nul 2>&1
    cd ..\..
)
echo [INFO] Desktop coverage report: apps\desktop-app\coverage\index.html

echo [INFO] Coverage reports completed

echo.
echo ==========================================
echo    Coverage Reports Generated
echo ==========================================
echo.
echo You can open these HTML files in your browser:
echo - Backend:    apps\backend\htmlcov\index.html
echo - Frontend:   apps\frontend-dashboard\coverage\index.html
echo - Desktop:    apps\desktop-app\coverage\index.html
echo.
pause
goto main_menu

:run_quick_tests
echo.
echo ==========================================
echo    Quick Tests (Skip Slow Tests)
echo ==========================================
echo.
echo This mode skips tests marked as 'slow' for faster feedback.
echo.

echo [INFO] Running quick backend tests...
cd apps\backend
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat >nul 2>&1
    echo [INFO] Running quick tests (excluding slow tests)...
    pytest --tb=short -v -m "not slow" --maxfail=3 -x
    set "backend_result=!errorlevel!"
) else (
    echo [ERROR] Python virtual environment not found
    set "backend_result=1"
)
cd ..\..

echo [INFO] Running quick frontend tests...
pnpm --filter frontend-dashboard test --passWithNoTests --maxWorkers=50%% >nul 2>&1
set "frontend_result=!errorlevel!"

echo [INFO] Running quick desktop tests...
pnpm --filter desktop-app test --passWithNoTests --maxWorkers=50%% >nul 2>&1
set "desktop_result=!errorlevel!"

echo [INFO] Quick tests completed

echo.
echo === Quick Test Results ===
if !backend_result!==0 (echo [PASS] Backend quick tests) else (echo [FAIL] Backend quick tests)
if !frontend_result!==0 (echo [PASS] Frontend quick tests) else (echo [FAIL] Frontend quick tests)
if !desktop_result!==0 (echo [PASS] Desktop quick tests) else (echo [FAIL] Desktop quick tests)

set /a "total_failures=!backend_result!+!frontend_result!+!desktop_result!"
if !total_failures!==0 (
    echo.
    echo [SUCCESS] Quick tests passed!
    echo [INFO] For complete testing, run 'All Tests' option
) else (
    echo.
    echo [WARNING] !total_failures! component(s) failed quick tests
    echo [RECOMMENDATION] Run full test suite for detailed analysis
)
echo.
pause
goto main_menu

:run_watch_mode
echo.
echo ==========================================
echo    Watch Mode (Continuous Testing)
echo ==========================================
echo.
echo This will start multiple windows for continuous testing.
echo Tests will re-run automatically when files change.
echo.

echo Starting test watchers...
start "Backend Test Watch" cmd /k "cd /d apps\backend && call venv\Scripts\activate.bat && pytest --tb=short -v -f"
start "Frontend Test Watch" cmd /k "pnpm --filter frontend-dashboard test --watch"
start "Desktop Test Watch" cmd /k "pnpm --filter desktop-app test --watch"

echo.
echo [SUCCESS] Test monitoring started!
echo.
echo Watch windows opened:
echo - Backend Test Watch: Monitors Python files
echo - Frontend Test Watch: Monitors React/TS files  
echo - Desktop Test Watch: Monitors Electron files
echo.
echo Tests will automatically re-run when you modify code files.
echo Close the watch windows when you're done developing.
echo.
pause
goto main_menu

:run_health_check
echo.
echo ==========================================
echo    Health Check
echo ==========================================
echo.
echo Running basic validation tests...
echo.

echo [INFO] Checking Python environment...
cd apps\backend
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat >nul 2>&1
    python -c "import sys; print(f'Python {sys.version}')" 2>nul && (
        echo [OK] Python environment working
    ) || (
        echo [FAIL] Python environment has issues
    )
) else (
    echo [FAIL] Python virtual environment not found
)
cd ..\..

echo [INFO] Checking Node.js environment...
node --version >nul 2>&1 && (
    echo [OK] Node.js available
) || (
    echo [FAIL] Node.js not found
)

echo [INFO] Checking pnpm...
pnpm --version >nul 2>&1 && (
    echo [OK] pnpm available
) || (
    echo [FAIL] pnpm not found
)

echo [INFO] Checking project structure...
if exist "package.json" (
    echo [OK] Root package.json exists
) else (
    echo [FAIL] Root package.json missing
)

if exist "apps\backend\requirements.txt" (
    echo [OK] Backend requirements.txt exists
) else (
    echo [FAIL] Backend requirements.txt missing
)

echo [INFO] Health check completed

echo.
echo [INFO] Health check completed
echo [INFO] For detailed environment setup, run start-dev.bat
echo.
pause
goto main_menu

:exit_script
echo.
echo ==========================================
echo    Thank you for using Test Runner!
echo ==========================================
echo.
echo For troubleshooting help, see:
echo - TESTING_TROUBLESHOOTING.md
echo - QUICK_START.md
echo.
pause
exit /b 0