@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Backend Component Tests
color 0B

:: Add error handling and logging (添加錯誤處理和日志記錄)
set "LOG_FILE=%~dp0run-component-tests-errors.log"
set "SCRIPT_NAME=run-component-tests.bat"

:: Log script start (記錄腳本啟動)
echo [%date% %time%] Script started: %SCRIPT_NAME% >> "%LOG_FILE%" 2>nul

echo ==========================================
echo   Unified AI Project - Backend Component Tests
echo ==========================================
echo.
echo This script runs component tests for the backend services. (此腳本運行後端服務的組件測試)
echo.
echo Available test options: (可用的測試選項)
echo   all      - Run all component tests (運行所有組件測試)
echo   api      - Test API endpoints (測試API端點)
echo   services - Test core services (測試核心服務)
echo   utils    - Test utility functions (測試工具函數)
echo   models   - Test data models (測試數據模型)
echo   database - Test database operations (測試數據庫操作)
echo.

:: Check if a test type is provided (檢查是否提供了測試類型)
if "%1"=="" (
    echo [INFO] No test type specified. Running all component tests by default... (未指定測試類型。默認運行所有組件測試)
    set "test_type=all"
) else (
    set "test_type=%1"
)

echo [INFO] Running %test_type% component tests... (運行 %test_type% 組件測試)
echo [%date% %time%] Running %test_type% component tests >> "%LOG_FILE%" 2>nul
echo.

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
if "%test_type%"=="api" (
    goto test_api
) else if "%test_type%"=="services" (
    goto test_services
) else if "%test_type%"=="utils" (
    goto test_utils
) else if "%test_type%"=="models" (
    goto test_models
) else if "%test_type%"=="database" (
    goto test_database
) else (
    goto test_all
)

:: Test API endpoints (測試API端點)
:test_api
echo [TEST] Running API endpoint tests... (運行API端點測試)

python -m pytest tests/test_api_endpoints.py --tb=short -v > api_tests.log 2>&1
if errorlevel 1 (
    echo [ERROR] API endpoint tests failed (API端點測試失敗)
    echo [INFO] Check api_tests.log for details (檢查api_tests.log獲取詳細信息)
    echo [%date% %time%] API endpoint tests failed >> "%LOG_FILE%" 2>nul
) else (
    echo [OK] API endpoint tests passed (API端點測試通過)
    echo [%date% %time%] API endpoint tests passed >> "%LOG_FILE%" 2>nul
)

echo.
echo Press any key to continue...
pause >nul
exit /b 0

:: Test core services (測試核心服務)
:test_services
echo [TEST] Running core services tests... (運行核心服務測試)

python -m pytest tests/test_core_services.py --tb=short -v > services_tests.log 2>&1
if errorlevel 1 (
    echo [ERROR] Core services tests failed (核心服務測試失敗)
    echo [INFO] Check services_tests.log for details (檢查services_tests.log獲取詳細信息)
    echo [%date% %time%] Core services tests failed >> "%LOG_FILE%" 2>nul
) else (
    echo [OK] Core services tests passed (核心服務測試通過)
    echo [%date% %time%] Core services tests passed >> "%LOG_FILE%" 2>nul
)

echo.
echo Press any key to continue...
pause >nul
exit /b 0

:: Test utility functions (測試工具函數)
:test_utils
echo [TEST] Running utility functions tests... (運行工具函數測試)

python -m pytest tests/test_utils.py --tb=short -v > utils_tests.log 2>&1
if errorlevel 1 (
    echo [ERROR] Utility functions tests failed (工具函數測試失敗)
    echo [INFO] Check utils_tests.log for details (檢查utils_tests.log獲取詳細信息)
    echo [%date% %time%] Utility functions tests failed >> "%LOG_FILE%" 2>nul
) else (
    echo [OK] Utility functions tests passed (工具函數測試通過)
    echo [%date% %time%] Utility functions tests passed >> "%LOG_FILE%" 2>nul
)

echo.
echo Press any key to continue...
pause >nul
exit /b 0

:: Test data models (測試數據模型)
:test_models
echo [TEST] Running data models tests... (運行數據模型測試)

python -m pytest tests/test_data_models.py --tb=short -v > models_tests.log 2>&1
if errorlevel 1 (
    echo [ERROR] Data models tests failed (數據模型測試失敗)
    echo [INFO] Check models_tests.log for details (檢查models_tests.log獲取詳細信息)
    echo [%date% %time%] Data models tests failed >> "%LOG_FILE%" 2>nul
) else (
    echo [OK] Data models tests passed (數據模型測試通過)
    echo [%date% %time%] Data models tests passed >> "%LOG_FILE%" 2>nul
)

echo.
echo Press any key to continue...
pause >nul
exit /b 0

:: Test database operations (測試數據庫操作)
:test_database
echo [TEST] Running database operations tests... (運行數據庫操作測試)

python -m pytest tests/test_database_ops.py --tb=short -v > database_tests.log 2>&1
if errorlevel 1 (
    echo [ERROR] Database operations tests failed (數據庫操作測試失敗)
    echo [INFO] Check database_tests.log for details (檢查database_tests.log獲取詳細信息)
    echo [%date% %time%] Database operations tests failed >> "%LOG_FILE%" 2>nul
) else (
    echo [OK] Database operations tests passed (數據庫操作測試通過)
    echo [%date% %time%] Database operations tests passed >> "%LOG_FILE%" 2>nul
)

echo.
echo Press any key to continue...
pause >nul
exit /b 0

:: Run all component tests (運行所有組件測試)
:test_all
echo [TEST] Running all component tests... (運行所有組件測試)
echo [%date% %time%] Running all component tests >> "%LOG_FILE%" 2>nul

:: Run each test suite (運行每個測試套件)
call :test_api
call :test_services
call :test_utils
call :test_models
call :test_database

echo.
echo [SUCCESS] All component tests completed! (所有組件測試完成!)
echo [%date% %time%] All component tests completed >> "%LOG_FILE%" 2>nul
echo.
echo Test results: (測試結果)
echo - API tests: api_tests.log
echo - Services tests: services_tests.log
echo - Utils tests: utils_tests.log
echo - Models tests: models_tests.log
echo - Database tests: database_tests.log
echo.
echo Press any key to continue...
pause >nul
exit /b 0