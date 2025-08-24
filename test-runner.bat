@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Quick Test Runner
color 0B

echo ==========================================
echo    Quick Test Runner
echo ==========================================

where pnpm >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pnpm not found. Install with: npm install -g pnpm
    pause
    exit /b 1
)
echo [OK] Environment ready
echo.

:menu
echo Select test type:
echo 1. Quick Tests
echo 2. Full Tests
echo 3. Coverage
echo 4. Exit
echo.
set "choice="
set /p "choice=Choose (1-4): "
if defined choice set "choice=%choice: =%"
if not defined choice (
    echo [ERROR] No input provided
    timeout /t 2 >nul
    goto menu
)

if "%choice%"=="1" goto quick
if "%choice%"=="2" goto full
if "%choice%"=="3" goto coverage
if "%choice%"=="4" exit /b 0
echo [ERROR] Invalid choice
timeout /t 2 >nul
goto menu

:quick
echo [INFO] Running quick tests...
cd apps\backend
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat >nul 2>&1
    pytest -m "not slow" --tb=short -x --maxfail=3
) else (
    echo [ERROR] Python venv not found
)
cd ..\..
echo [SUCCESS] Quick tests completed
pause
goto menu

:full
echo [INFO] Running full test suite...
set "results=0"
cd apps\backend
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat >nul 2>&1
    pytest --tb=short -v
    set /a "results+=!errorlevel!"
) else (
    set /a "results+=1"
)
cd ..\..
pnpm --filter frontend-dashboard test --passWithNoTests
set /a "results+=!errorlevel!"
pnpm --filter desktop-app test --passWithNoTests
set /a "results+=!errorlevel!"
if !results!==0 (
    echo [SUCCESS] All tests passed!
) else (
    echo [WARNING] !results! component(s) failed
)
pause
goto menu

:coverage
echo [INFO] Generating coverage reports...
cd apps\backend
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat >nul 2>&1
    pytest --cov=src --cov-report=html
    echo [INFO] Backend: apps\backend\htmlcov\index.html
)
cd ..\..
pnpm --filter frontend-dashboard test:coverage >nul 2>&1
echo [INFO] Frontend: apps\frontend-dashboard\coverage\index.html
echo [SUCCESS] Reports generated
pause
goto menu