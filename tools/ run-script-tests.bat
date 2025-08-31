@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Script Tests Runner
color 0E

:: Add error handling and logging (添加錯誤處理和日志記錄)
set "LOG_FILE=%~dp0run-script-tests-errors.log"
set "SCRIPT_NAME=run-script-tests.bat"

:: Log script start (記錄腳本啟動)
echo [%date% %time%] Script started: %SCRIPT_NAME% >> "%LOG_FILE%" 2>nul

echo ==========================================
echo   Unified AI Project - Script Tests Runner
echo ==========================================
echo.
echo This script runs tests for all batch scripts in the project. (此腳本運行項目中所有批處理腳本的測試)
echo.
echo Test process: (測試過程)
echo 1. 🧪 Test individual batch scripts (測試單個批處理腳本)
echo 2. 🔄 Test script interactions (測試腳本交互)
echo 3. 📊 Generate test report (生成測試報告)
echo 4. ✅ Verify results (驗證結果)
echo.

:: Confirm action (確認操作)
echo [CONFIRM] Are you sure you want to run script tests? (您確定要運行腳本測試嗎?)
echo.

:: 使用 set /p 替代 choice 命令
:get_user_choice
set "user_choice="
set /p "user_choice=Continue with script tests (y/N)? "
if not defined user_choice (
    set "user_choice=N"
)

:: 验证用户输入
if /i "%user_choice%"=="Y" (
    goto continue_tests
) else if /i "%user_choice%"=="N" (
    echo [INFO] Operation cancelled by user (操作被用戶取消)
    echo [%date% %time%] Operation cancelled by user >> "%LOG_FILE%" 2>nul
    echo Press any key to exit...
    pause >nul
    exit /b 0
) else (
    echo [ERROR] Invalid choice '%user_choice%'. Please enter 'Y' or 'N'.
    echo [%date% %time%] Invalid choice: %user_choice% >> "%LOG_FILE%" 2>nul
    goto get_user_choice
)

:continue_tests

:: Test individual batch scripts (測試單個批處理腳本)
echo.
echo [STEP 1/4] Testing individual batch scripts... (測試單個批處理腳本)
echo [%date% %time%] Testing individual batch scripts >> "%LOG_FILE%" 2>nul

:: Test ai-runner.bat (測試ai-runner.bat)
echo [TEST] Testing ai-runner.bat... (測試ai-runner.bat)
call ai-runner.bat > ai_runner_test.log 2>&1
if errorlevel 1 (
    echo [ERROR] ai-runner.bat test failed (ai-runner.bat測試失敗)
    echo [%date% %time%] ai-runner.bat test failed >> "%LOG_FILE%" 2>nul
) else (
    echo [OK] ai-runner.bat test passed (ai-runner.bat測試通過)
    echo [%date% %time%] ai-runner.bat test passed >> "%LOG_FILE%" 2>nul
)

:: Test unified-ai.bat (測試unified-ai.bat)
echo [TEST] Testing unified-ai.bat... (測試unified-ai.bat)
call unified-ai.bat > unified_ai_test.log 2>&1
if errorlevel 1 (
    echo [ERROR] unified-ai.bat test failed (unified-ai.bat測試失敗)
    echo [%date% %time%] unified-ai.bat test failed >> "%LOG_FILE%" 2>nul
) else (
    echo [OK] unified-ai.bat test passed (unified-ai.bat測試通過)
    echo [%date% %time%] unified-ai.bat test passed >> "%LOG_FILE%" 2>nul
)

:: Test tools scripts (測試工具腳本)
echo [TEST] Testing tools scripts... (測試工具腳本)
cd tools

:: Test start-dev.bat (測試start-dev.bat)
echo [TEST] Testing start-dev.bat... (測試start-dev.bat)
call start-dev.bat > start_dev_test.log 2>&1
if errorlevel 1 (
    echo [ERROR] start-dev.bat test failed (start-dev.bat測試失敗)
    echo [%date% %time%] start-dev.bat test failed >> "%LOG_FILE%" 2>nul
) else (
    echo [OK] start-dev.bat test passed (start-dev.bat測試通過)
    echo [%date% %time%] start-dev.bat test passed >> "%LOG_FILE%" 2>nul
)

:: Test run-tests.bat (測試run-tests.bat)
echo [TEST] Testing run-tests.bat... (測試run-tests.bat)
call run-tests.bat > run_tests_test.log 2>&1
if errorlevel 1 (
    echo [ERROR] run-tests.bat test failed (run-tests.bat測試失敗)
    echo [%date% %time%] run-tests.bat test failed >> "%LOG_FILE%" 2>nul
) else (
    echo [OK] run-tests.bat test passed (run-tests.bat測試通過)
    echo [%date% %time%] run-tests.bat test passed >> "%LOG_FILE%" 2>nul
)

:: Test health-check.bat (測試health-check.bat)
echo [TEST] Testing health-check.bat... (測試health-check.bat)
call health-check.bat > health_check_test.log 2>&1
if errorlevel 1 (
    echo [ERROR] health-check.bat test failed (health-check.bat測試失敗)
    echo [%date% %time%] health-check.bat test failed >> "%LOG_FILE%" 2>nul
) else (
    echo [OK] health-check.bat test passed (health-check.bat測試通過)
    echo [%date% %time%] health-check.bat test passed >> "%LOG_FILE%" 2>nul
)

cd ..

:: Test script interactions (測試腳本交互)
echo.
echo [STEP 2/4] Testing script interactions... (測試腳本交互)
echo [%date% %time%] Testing script interactions >> "%LOG_FILE%" 2>nul

:: Test setup and start sequence (測試設置和啟動序列)
echo [TEST] Testing setup and start sequence... (測試設置和啟動序列)
call ai-runner.bat setup > setup_test.log 2>&1
if errorlevel 1 (
    echo [ERROR] Setup test failed (設置測試失敗)
    echo [%date% %time%] Setup test failed >> "%LOG_FILE%" 2>nul
) else (
    echo [OK] Setup test passed (設置測試通過)
    echo [%date% %time%] Setup test passed >> "%LOG_FILE%" 2>nul
)

:: Test health check after setup (設置後測試健康檢查)
echo [TEST] Testing health check after setup... (設置後測試健康檢查)
call tools\health-check.bat > health_after_setup_test.log 2>&1
if errorlevel 1 (
    echo [ERROR] Health check after setup failed (設置後健康檢查失敗)
    echo [%date% %time%] Health check after setup failed >> "%LOG_FILE%" 2>nul
) else (
    echo [OK] Health check after setup passed (設置後健康檢查通過)
    echo [%date% %time%] Health check after setup passed >> "%LOG_FILE%" 2>nul
)

:: Generate test report (生成測試報告)
echo.
echo [STEP 3/4] Generating test report... (生成測試報告)
echo [%date% %time%] Generating test report >> "%LOG_FILE%" 2>nul

:: Create test report (創建測試報告)
echo === Script Test Report === > script_test_report.log
echo Generated on: %date% %time% >> script_test_report.log
echo. >> script_test_report.log

:: Count passed and failed tests (計算通過和失敗的測試)
set "passed_count=0"
set "failed_count=0"

for /f "delims=" %%f in ('dir /s /b *_test.log') do (
    findstr /c:"ERROR" "%%f" >nul 2>&1
    if errorlevel 1 (
        set /a "passed_count+=1"
        echo [PASS] %%f >> script_test_report.log
    ) else (
        set /a "failed_count+=1"
        echo [FAIL] %%f >> script_test_report.log
    )
)

echo. >> script_test_report.log
echo === Summary === >> script_test_report.log
echo Passed: !passed_count! >> script_test_report.log
echo Failed: !failed_count! >> script_test_report.log
echo Total: !passed_count! + !failed_count! = %%passed_count + failed_count%% >> script_test_report.log

echo [OK] Test report generated (測試報告已生成)

:: Verify results (驗證結果)
echo.
echo [STEP 4/4] Verifying results... (驗證結果)
echo [%date% %time%] Verifying results >> "%LOG_FILE%" 2>nul

if !failed_count! gtr 0 (
    echo [WARNING] !failed_count! script test(s) failed ( !failed_count! 個腳本測試失敗)
    echo [INFO] Check script_test_report.log for details (檢查script_test_report.log獲取詳細信息)
    echo [%date% %time%] Script tests completed with failures >> "%LOG_FILE%" 2>nul
) else (
    echo [SUCCESS] All script tests passed (所有腳本測試通過)
    echo [%date% %time%] All script tests passed >> "%LOG_FILE%" 2>nul
)

echo.
echo [SUCCESS] Script tests completed! (腳本測試完成!)
echo [%date% %time%] Script tests completed >> "%LOG_FILE%" 2>nul
echo.
echo Test results: (測試結果)
echo - Individual script tests: See individual log files
echo - Script interactions: See interaction test logs
echo - Test report: script_test_report.log
echo.
echo Next steps: (下一步)
echo 1. Review script_test_report.log for any failures (檢查script_test_report.log中的任何失敗)
echo 2. Fix any identified issues (修復任何發現的問題)
echo 3. Re-run this script to verify fixes (重新運行此腳本以驗證修復)
echo.

:end_script
echo.
echo Press any key to exit...
pause >nul
exit /b 0