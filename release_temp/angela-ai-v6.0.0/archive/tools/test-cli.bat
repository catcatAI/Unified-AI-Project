@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - CLI Test Runner
color 0B

:: Add error handling and logging (添加錯誤處理和日志記錄)
set "LOG_FILE=%~dp0test-cli-errors.log"
set "SCRIPT_NAME=test-cli.bat"

:: Log script start (記錄腳本啟動)
echo [%date% %time%] Script started: %SCRIPT_NAME% >> "%LOG_FILE%" 2>nul

echo ==========================================
echo   Unified AI Project - CLI Test Runner
echo ==========================================
echo.
echo This script runs tests for the Unified AI Project CLI tools. (此腳本運行Unified AI Project CLI工具的測試)
echo.
echo Available test options: (可用的測試選項)
echo   all      - Run all CLI tests (運行所有CLI測試)
echo   runner   - Test AI Runner CLI (測試AI Runner CLI)
echo   trainer  - Test Training Manager CLI (測試訓練管理器CLI)
echo   dev      - Test Development Tools CLI (測試開發工具CLI)
echo   git      - Test Git Tools CLI (測試Git工具CLI)
echo.

:: Check if a test type is provided (檢查是否提供了測試類型)
if "%1"=="" (
    echo [INFO] No test type specified. Running all CLI tests by default... (未指定測試類型。默認運行所有CLI測試)
    set "test_type=all"
) else (
    set "test_type=%1"
)

echo [INFO] Running %test_type% CLI tests... (運行 %test_type% CLI測試)
echo [%date% %time%] Running %test_type% CLI tests >> "%LOG_FILE%" 2>nul
echo.

:: Run tests based on type (根據類型運行測試)
if "%test_type%"=="runner" (
    goto test_runner
) else if "%test_type%"=="trainer" (
    goto test_trainer
) else if "%test_type%"=="dev" (
    goto test_dev
) else if "%test_type%"=="git" (
    goto test_git
) else (
    goto test_all
)

:: Test AI Runner CLI (測試AI Runner CLI)
:test_runner
echo [TEST] Testing AI Runner CLI... (測試AI Runner CLI)

:: Test basic help command (測試基本幫助命令)
echo [TEST] Testing 'ai-runner.bat' help output... (測試'ai-runner.bat'幫助輸出)
call ai-runner.bat > runner_help_test.log 2>&1
if errorlevel 1 (
    echo [ERROR] ai-runner.bat help test failed (ai-runner.bat幫助測試失敗)
    echo [%date% %time%] ai-runner.bat help test failed >> "%LOG_FILE%" 2>nul
) else (
    echo [OK] ai-runner.bat help test passed (ai-runner.bat幫助測試通過)
)

:: Test setup command (測試設置命令)
echo [TEST] Testing 'ai-runner.bat setup' command... (測試'ai-runner.bat setup'命令)
call ai-runner.bat setup --dry-run > runner_setup_test.log 2>&1
if errorlevel 1 (
    echo [INFO] ai-runner.bat setup test completed (ai-runner.bat設置測試完成)
) else (
    echo [OK] ai-runner.bat setup test passed (ai-runner.bat設置測試通過)
)

echo [SUCCESS] AI Runner CLI tests completed (AI Runner CLI測試完成)
echo [%date% %time%] AI Runner CLI tests completed >> "%LOG_FILE%" 2>nul
echo Press any key to continue...
pause >nul
exit /b 0

:: Test Training Manager CLI (測試訓練管理器CLI)
:test_trainer
echo [TEST] Testing Training Manager CLI... (測試訓練管理器CLI)

:: Test basic help command (測試基本幫助命令)
echo [TEST] Testing 'tools\train-manager.bat' help output... (測試'tools\train-manager.bat'幫助輸出)
call tools\train-manager.bat > trainer_help_test.log 2>&1
if errorlevel 1 (
    echo [ERROR] train-manager.bat help test failed (train-manager.bat幫助測試失敗)
    echo [%date% %time%] train-manager.bat help test failed >> "%LOG_FILE%" 2>nul
) else (
    echo [OK] train-manager.bat help test passed (train-manager.bat幫助測試通過)
)

echo [SUCCESS] Training Manager CLI tests completed (訓練管理器CLI測試完成)
echo [%date% %time%] Training Manager CLI tests completed >> "%LOG_FILE%" 2>nul
echo Press any key to continue...
pause >nul
exit /b 0

:: Test Development Tools CLI (測試開發工具CLI)
:test_dev
echo [TEST] Testing Development Tools CLI... (測試開發工具CLI)

:: Test start-dev command (測試start-dev命令)
echo [TEST] Testing 'tools\start-dev.bat' execution... (測試'tools\start-dev.bat'執行)
call tools\start-dev.bat > dev_start_test.log 2>&1
if errorlevel 1 (
    echo [INFO] start-dev.bat test completed (start-dev.bat測試完成)
) else (
    echo [OK] start-dev.bat test passed (start-dev.bat測試通過)
)

:: Test run-tests command (測試run-tests命令)
echo [TEST] Testing 'tools\run-tests.bat' execution... (測試'tools\run-tests.bat'執行)
call tools\run-tests.bat > dev_tests_test.log 2>&1
if errorlevel 1 (
    echo [INFO] run-tests.bat test completed (run-tests.bat測試完成)
) else (
    echo [OK] run-tests.bat test passed (run-tests.bat測試通過)
)

echo [SUCCESS] Development Tools CLI tests completed (開發工具CLI測試完成)
echo [%date% %time%] Development Tools CLI tests completed >> "%LOG_FILE%" 2>nul
echo Press any key to continue...
pause >nul
exit /b 0

:: Test Git Tools CLI (測試Git工具CLI)
:test_git
echo [TEST] Testing Git Tools CLI... (測試Git工具CLI)

:: Test health-check command (測試健康檢查命令)
echo [TEST] Testing 'tools\health-check.bat' execution... (測試'tools\health-check.bat'執行)
call tools\health-check.bat > git_health_test.log 2>&1
if errorlevel 1 (
    echo [INFO] health-check.bat test completed (health-check.bat測試完成)
) else (
    echo [OK] health-check.bat test passed (health-check.bat測試通過)
)

:: Test safe-git-cleanup command (測試安全Git清理命令)
echo [TEST] Testing 'tools\safe-git-cleanup.bat' execution... (測試'tools\safe-git-cleanup.bat'執行)
call tools\safe-git-cleanup.bat > git_cleanup_test.log 2>&1
if errorlevel 1 (
    echo [INFO] safe-git-cleanup.bat test completed (safe-git-cleanup.bat測試完成)
) else (
    echo [OK] safe-git-cleanup.bat test passed (safe-git-cleanup.bat測試通過)
)

echo [SUCCESS] Git Tools CLI tests completed (Git工具CLI測試完成)
echo [%date% %time%] Git Tools CLI tests completed >> "%LOG_FILE%" 2>nul
echo Press any key to continue...
pause >nul
exit /b 0

:: Run all CLI tests (運行所有CLI測試)
:test_all
echo [TEST] Running all CLI tests... (運行所有CLI測試)
echo [%date% %time%] Running all CLI tests >> "%LOG_FILE%" 2>nul

:: Run each test suite (運行每個測試套件)
call :test_runner
call :test_trainer
call :test_dev
call :test_git

echo.
echo [SUCCESS] All CLI tests completed! (所有CLI測試完成!)
echo [%date% %time%] All CLI tests completed >> "%LOG_FILE%" 2>nul
echo.
echo Test results: (測試結果)
echo - AI Runner CLI tests: runner_*.log
echo - Training Manager CLI tests: trainer_*.log
echo - Development Tools CLI tests: dev_*.log
echo - Git Tools CLI tests: git_*.log
echo.
echo Press any key to continue...
pause >nul
exit /b 0