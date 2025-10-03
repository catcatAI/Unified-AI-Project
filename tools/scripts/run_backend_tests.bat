@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Backend Tests Runner
color 0B

:: Add error handling and logging (添加錯誤處理和日志記錄)
set "LOG_FILE=%~dp0run-backend-tests-errors.log"
set "SCRIPT_NAME=run-backend-tests.bat"

:: Log script start (記錄腳本啟動)
echo [%date% %time%] Script started: %SCRIPT_NAME% >> "%LOG_FILE%" 2>nul

echo ==========================================
echo   Unified AI Project - Backend Tests Runner
echo ==========================================
echo.
echo This script runs backend tests for the Unified AI Project. (此腳本運行Unified AI Project的後端測試)
echo.
echo Test options: (測試選項)
echo   all      - Run all backend tests (運行所有後端測試)
echo   unit     - Run unit tests only (僅運行單元測試)
echo   integration - Run integration tests only (僅運行集成測試)
echo   api      - Run API tests only (僅運行API測試)
echo   coverage - Run tests with coverage report (運行帶覆蓋率報告的測試)
echo.

:: Check if a test type is provided (檢查是否提供了測試類型)
if "%1"=="" (
    echo [INFO] No test type specified. Running all backend tests by default... (未指定測試類型。默認運行所有後端測試)
    set "test_type=all"
) else (
    set "test_type=%1"
)

echo [INFO] Running %test_type% backend tests... (運行 %test_type% 後端測試)
echo [%date% %time%] Running %test_type% backend tests >> "%LOG_FILE%" 2>nul
echo.

:: Change to backend directory (切換到後端目錄)
echo [INFO] Changing to backend directory... (切換到後端目錄)
cd ..\apps\backend
if errorlevel 1 (
    echo [ERROR] Failed to change to backend directory (無法切換到後端目錄)
    echo [%date% %time%] Failed to change to backend directory >> "%LOG_FILE%" 2>nul
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

:: Activate virtual environment (激活虛擬環境)
echo [INFO] Activating virtual environment... (激活虛擬環境)
call venv\Scripts\activate.bat >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment (無法激活虛擬環境)
    echo [%date% %time%] Failed to activate virtual environment >> "%LOG_FILE%" 2>nul
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

:: Run tests based on type (根據類型運行測試)
if "%test_type%"=="unit" (
    goto run_unit_tests
) else if "%test_type%"=="integration" (
    goto run_integration_tests
) else if "%test_type%"=="api" (
    goto run_api_tests
) else if "%test_type%"=="coverage" (
    goto run_coverage_tests
) else (
    goto run_all_tests
)

:: Run unit tests (運行單元測試)
:run_unit_tests
echo.
echo [TEST] Running unit tests... (運行單元測試)
echo [%date% %time%] Running unit tests >> "%LOG_FILE%" 2>nul

python -m pytest tests/unit/ --tb=short -v > unit_tests.log 2>&1
if errorlevel 1 (
    echo [ERROR] Unit tests failed (單元測試失敗)
    echo [INFO] Check unit_tests.log for details (檢查unit_tests.log獲取詳細信息)
    echo [%date% %time%] Unit tests failed >> "%LOG_FILE%" 2>nul
) else (
    echo [OK] Unit tests passed (單元測試通過)
    echo [%date% %time%] Unit tests passed >> "%LOG_FILE%" 2>nul
)

echo.
echo Press any key to continue...
pause >nul
exit /b 0

:: Run integration tests (運行集成測試)
:run_integration_tests
echo.
echo [TEST] Running integration tests... (運行集成測試)
echo [%date% %time%] Running integration tests >> "%LOG_FILE%" 2>nul

python -m pytest tests/integration/ --tb=short -v > integration_tests.log 2>&1
if errorlevel 1 (
    echo [ERROR] Integration tests failed (集成測試失敗)
    echo [INFO] Check integration_tests.log for details (檢查integration_tests.log獲取詳細信息)
    echo [%date% %time%] Integration tests failed >> "%LOG_FILE%" 2>nul
) else (
    echo [OK] Integration tests passed (集成測試通過)
    echo [%date% %time%] Integration tests passed >> "%LOG_FILE%" 2>nul
)

echo.
echo Press any key to continue...
pause >nul
exit /b 0

:: Run API tests (運行API測試)
:run_api_tests
echo.
echo [TEST] Running API tests... (運行API測試)
echo [%date% %time%] Running API tests >> "%LOG_FILE%" 2>nul

python -m pytest tests/api/ --tb=short -v > api_tests.log 2>&1
if errorlevel 1 (
    echo [ERROR] API tests failed (API測試失敗)
    echo [INFO] Check api_tests.log for details (檢查api_tests.log獲取詳細信息)
    echo [%date% %time%] API tests failed >> "%LOG_FILE%" 2>nul
) else (
    echo [OK] API tests passed (API測試通過)
    echo [%date% %time%] API tests passed >> "%LOG_FILE%" 2>nul
)

echo.
echo Press any key to continue...
pause >nul
exit /b 0

:: Run tests with coverage (運行帶覆蓋率的測試)
:run_coverage_tests
echo.
echo [TEST] Running tests with coverage... (運行帶覆蓋率的測試)
echo [%date% %time%] Running tests with coverage >> "%LOG_FILE%" 2>nul

python -m pytest --cov=src --cov-report=html --cov-report=term tests/ > coverage_tests.log 2>&1
if errorlevel 1 (
    echo [ERROR] Coverage tests failed (覆蓋率測試失敗)
    echo [INFO] Check coverage_tests.log for details (檢查coverage_tests.log獲取詳細信息)
    echo [%date% %time%] Coverage tests failed >> "%LOG_FILE%" 2>nul
) else (
    echo [OK] Coverage tests passed (覆蓋率測試通過)
    echo [%date% %time%] Coverage tests passed >> "%LOG_FILE%" 2>nul
    echo [INFO] Coverage report generated in htmlcov/ (覆蓋率報告生成在htmlcov/中)
)

echo.
echo Press any key to continue...
pause >nul
exit /b 0

:: Run all tests (運行所有測試)
:run_all_tests
echo.
echo [TEST] Running all backend tests... (運行所有後端測試)
echo [%date% %time%] Running all backend tests >> "%LOG_FILE%" 2>nul

python -m pytest tests/ --tb=short -v > all_tests.log 2>&1
if errorlevel 1 (
    echo [ERROR] Backend tests failed (後端測試失敗)
    echo [INFO] Check all_tests.log for details (檢查all_tests.log獲取詳細信息)
    echo [%date% %time%] Backend tests failed >> "%LOG_FILE%" 2>nul
) else (
    echo [OK] Backend tests passed (後端測試通過)
    echo [%date% %time%] Backend tests passed >> "%LOG_FILE%" 2>nul
)

echo.
echo [SUCCESS] All backend tests completed! (所有後端測試完成!)
echo [%date% %time%] All backend tests completed >> "%LOG_FILE%" 2>nul
echo.
echo Test results: (測試結果)
echo - Unit tests: unit_tests.log
echo - Integration tests: integration_tests.log
echo - API tests: api_tests.log
echo - Coverage tests: coverage_tests.log
echo - All tests: all_tests.log
echo.
echo Press any key to continue...
pause >nul
exit /b 0