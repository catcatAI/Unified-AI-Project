@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Test Runner
color 0B

:: Add error handling and logging (添加錯誤處理和日志記錄)
set "LOG_FILE=%~dp0test-runner-errors.log"
set "SCRIPT_NAME=run-tests.bat"

:: Log script start (記錄腳本啟動)
echo [%date% %time%] Script started: %SCRIPT_NAME% >> "%LOG_FILE%" 2>nul

echo ==========================================
echo   Unified AI Project - Test Runner
echo ==========================================
echo.
echo This script runs automated tests for the Unified AI Project. (此腳本運行Unified AI Project的自動化測試)
echo.
echo Available test options: (可用的測試選項)
echo   all      - Run all tests (frontend and backend) (運行所有測試（前端和後端）)
echo   frontend - Run frontend tests only (僅運行前端測試)
echo   backend  - Run backend tests only (僅運行後端測試)
echo   unit     - Run unit tests only (僅運行單元測試)
echo   integration - Run integration tests only (僅運行集成測試)
echo.

:: Check if a test type is provided (檢查是否提供了測試類型)
if "%1"=="" (
    echo Available test options:
    echo   all      - Run all tests
    echo   backend  - Run backend tests only
    echo   frontend - Run frontend tests only
    echo   unit     - Run unit tests only
    echo   integration - Run integration tests only
    echo.
    set "test_type="
    set /p "test_type=Enter test type (or press Enter for all): "
    if not defined test_type set "test_type=all"
) else (
    set "test_type=%1"
)

echo [INFO] Running %test_type% tests... (運行 %test_type% 測試)
echo.

:: Run tests based on type (根據類型運行測試)
if "%test_type%"=="frontend" (
    goto run_frontend_tests
) else if "%test_type%"=="backend" (
    goto run_backend_tests
) else if "%test_type%"=="unit" (
    goto run_unit_tests
) else if "%test_type%"=="integration" (
    goto run_integration_tests
) else (
    goto run_all_tests
)

:: Run frontend tests (運行前端測試)
:run_frontend_tests
echo [TEST] Running frontend tests... (運行前端測試)
echo [%date% %time%] Running frontend tests >> "%LOG_FILE%" 2>nul

pnpm --filter frontend-dashboard test --passWithNoTests
if %errorlevel% neq 0 (
    echo [ERROR] Frontend tests failed
    echo [%date% %time%] Frontend tests failed >> "%LOG_FILE%" 2>nul
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

echo [SUCCESS] Frontend tests completed successfully (前端測試成功完成)
echo [%date% %time%] Frontend tests completed >> "%LOG_FILE%" 2>nul
echo Press any key to continue...
pause >nul
exit /b 0

:: Run backend tests (運行後端測試)
:run_backend_tests
echo [TEST] Running backend tests... (運行後端測試)
echo [%date% %time%] Running backend tests >> "%LOG_FILE%" 2>nul

cd apps\backend
call venv\Scripts\activate.bat >nul 2>&1
pytest --tb=short -v
if %errorlevel% neq 0 (
    echo [ERROR] Backend tests failed
    echo [%date% %time%] Backend tests failed >> "%LOG_FILE%" 2>nul
    cd ..\..
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

cd ..\..
echo [SUCCESS] Backend tests completed successfully (後端測試成功完成)
echo [%date% %time%] Backend tests completed >> "%LOG_FILE%" 2>nul
echo Press any key to continue...
pause >nul
exit /b 0

:: Run unit tests (運行單元測試)
:run_unit_tests
echo [TEST] Running unit tests... (運行單元測試)
echo [%date% %time%] Running unit tests >> "%LOG_FILE%" 2>nul

:: Run frontend unit tests (運行前端單元測試)
echo [INFO] Running frontend unit tests... (運行前端單元測試)
pnpm --filter frontend-dashboard test:unit --passWithNoTests

:: Run backend unit tests (運行後端單元測試)
echo [INFO] Running backend unit tests... (運行後端單元測試)
cd apps\backend
call venv\Scripts\activate.bat >nul 2>&1
pytest --tb=short -v -m "not integration"
cd ..\..

echo [SUCCESS] Unit tests completed successfully (單元測試成功完成)
echo [%date% %time%] Unit tests completed >> "%LOG_FILE%" 2>nul
echo Press any key to continue...
pause >nul
exit /b 0

:: Run integration tests (運行集成測試)
:run_integration_tests
echo [TEST] Running integration tests... (運行集成測試)
echo [%date% %time%] Running integration tests >> "%LOG_FILE%" 2>nul

:: Run frontend integration tests (運行前端集成測試)
echo [INFO] Running frontend integration tests... (運行前端集成測試)
pnpm --filter frontend-dashboard test:integration --passWithNoTests

:: Run backend integration tests (運行後端集成測試)
echo [INFO] Running backend integration tests... (運行後端集成測試)
cd apps\backend
call venv\Scripts\activate.bat >nul 2>&1
pytest --tb=short -v -m "integration"
cd ..\..

echo [SUCCESS] Integration tests completed successfully (集成測試成功完成)
echo [%date% %time%] Integration tests completed >> "%LOG_FILE%" 2>nul
echo Press any key to continue...
pause >nul
exit /b 0

:: Run all tests (運行所有測試)
:run_all_tests
echo [TEST] Running all tests... (運行所有測試)
echo [%date% %time%] Running all tests >> "%LOG_FILE%" 2>nul

:: Run frontend tests (運行前端測試)
echo [INFO] Running frontend tests... (運行前端測試)
pnpm --filter frontend-dashboard test --passWithNoTests > frontend_tests.log 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Frontend tests failed. Check frontend_tests.log for details (前端測試失敗。檢查frontend_tests.log獲取詳細信息)
    echo [%date% %time%] Frontend tests failed >> "%LOG_FILE%" 2>nul
) else (
    echo [OK] Frontend tests passed (前端測試通過)
)

:: Run backend tests (運行後端測試)
echo [INFO] Running backend tests... (運行後端測試)
cd apps\backend
call venv\Scripts\activate.bat >nul 2>&1
pytest --tb=short -v > backend_tests.log 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Backend tests failed. Check backend_tests.log for details (後端測試失敗。檢查backend_tests.log獲取詳細信息)
    echo [%date% %time%] Backend tests failed >> "%LOG_FILE%" 2>nul
) else (
    echo [OK] Backend tests passed (後端測試通過)
)
cd ..\..

echo.
echo [SUCCESS] All tests completed! (所有測試完成!)
echo [%date% %time%] All tests completed >> "%LOG_FILE%" 2>nul
echo.
echo Test results: (測試結果)
echo - Frontend tests: frontend_tests.log
echo - Backend tests: backend_tests.log
echo.
echo Press any key to continue...
pause >nul
exit /b 0