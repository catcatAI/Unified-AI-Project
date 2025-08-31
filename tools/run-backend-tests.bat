@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Backend Tests
color 0B

:: Add error handling and logging (添加錯誤處理和日志記錄)
set "LOG_FILE=%~dp0run-backend-tests-errors.log"
set "SCRIPT_NAME=run-backend-tests.bat"

:: Log script start (記錄腳本啟動)
echo [%date% %time%] Script started: %SCRIPT_NAME% >> "%LOG_FILE%" 2>nul

echo ==========================================
echo   Unified AI Project - Backend Tests
echo ==========================================
echo.
echo This script runs backend tests for the Unified AI Project. (此腳本運行Unified AI Project的後端測試)
echo.
echo Test options: (測試選項)
echo   all      - Run all backend tests (運行所有後端測試)
echo   quick    - Run quick tests only (僅運行快速測試)
echo   slow     - Run slow tests only (僅運行慢速測試)
echo   parallel - Run tests in parallel (並行運行測試)
echo.

:: Check if a test type is provided (檢查是否提供了測試類型)
if "%1"=="" (
    echo [INFO] No test type specified. Running quick tests by default... (未指定測試類型。默認運行快速測試)
    set "test_type=quick"
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
if "%test_type%"=="all" (
    goto run_all_tests
) else if "%test_type%"=="slow" (
    goto run_slow_tests
) else if "%test_type%"=="parallel" (
    goto run_parallel_tests
) else (
    goto run_quick_tests
)

:: Run quick tests (運行快速測試)
:run_quick_tests
echo.
echo [TEST] Running quick backend tests... (運行快速後端測試)
echo [%date% %time%] Running quick backend tests >> "%LOG_FILE%" 2>nul

python -m pytest -m "not slow" --tb=short -v > quick_tests.log 2>&1
if errorlevel 1 (
    echo [ERROR] Quick backend tests failed (快速後端測試失敗)
    echo [INFO] Check quick_tests.log for details (檢查quick_tests.log獲取詳細信息)
    echo [%date% %time%] Quick backend tests failed >> "%LOG_FILE%" 2>nul
) else (
    echo [OK] Quick backend tests passed (快速後端測試通過)
    echo [%date% %time%] Quick backend tests passed >> "%LOG_FILE%" 2>nul
)

echo.
echo Press any key to continue...
pause >nul
exit /b 0

:: Run slow tests (運行慢速測試)
:run_slow_tests
echo.
echo [TEST] Running slow backend tests... (運行慢速後端測試)
echo [%date% %time%] Running slow backend tests >> "%LOG_FILE%" 2>nul

python -m pytest -m "slow" --tb=short -v > slow_tests.log 2>&1
if errorlevel 1 (
    echo [ERROR] Slow backend tests failed (慢速後端測試失敗)
    echo [INFO] Check slow_tests.log for details (檢查slow_tests.log獲取詳細信息)
    echo [%date% %time%] Slow backend tests failed >> "%LOG_FILE%" 2>nul
) else (
    echo [OK] Slow backend tests passed (慢速後端測試通過)
    echo [%date% %time%] Slow backend tests passed >> "%LOG_FILE%" 2>nul
)

echo.
echo Press any key to continue...
pause >nul
exit /b 0

:: Run tests in parallel (並行運行測試)
:run_parallel_tests
echo.
echo [TEST] Running backend tests in parallel... (並行運行後端測試)
echo [%date% %time%] Running backend tests in parallel >> "%LOG_FILE%" 2>nul

python -m pytest -n auto --tb=short -v > parallel_tests.log 2>&1
if errorlevel 1 (
    echo [ERROR] Parallel backend tests failed (並行後端測試失敗)
    echo [INFO] Check parallel_tests.log for details (檢查parallel_tests.log獲取詳細信息)
    echo [%date% %time%] Parallel backend tests failed >> "%LOG_FILE%" 2>nul
) else (
    echo [OK] Parallel backend tests passed (並行後端測試通過)
    echo [%date% %time%] Parallel backend tests passed >> "%LOG_FILE%" 2>nul
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

python -m pytest --tb=short -v > all_tests.log 2>&1
if errorlevel 1 (
    echo [ERROR] All backend tests failed (所有後端測試失敗)
    echo [INFO] Check all_tests.log for details (檢查all_tests.log獲取詳細信息)
    echo [%date% %time%] All backend tests failed >> "%LOG_FILE%" 2>nul
) else (
    echo [OK] All backend tests passed (所有後端測試通過)
    echo [%date% %time%] All backend tests passed >> "%LOG_FILE%" 2>nul
)

echo.
echo [SUCCESS] Backend tests completed! (後端測試完成!)
echo [%date% %time%] Backend tests completed >> "%LOG_FILE%" 2>nul
echo.
echo Test results: (測試結果)
echo - Quick tests: quick_tests.log
echo - Slow tests: slow_tests.log
echo - Parallel tests: parallel_tests.log
echo - All tests: all_tests.log
echo.
echo Press any key to continue...
pause >nul
exit /b 0