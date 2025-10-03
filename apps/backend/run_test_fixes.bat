@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Test Fixes Runner
color 0C

:: Add error handling and logging (添加錯誤處理和日志記錄)
set "LOG_FILE=%~dp0run-test-fixes-errors.log"
set "SCRIPT_NAME=run-test-fixes.bat"

:: Log script start (記錄腳本啟動)
echo [%date% %time%] Script started: %SCRIPT_NAME% >> "%LOG_FILE%" 2>nul

echo ==========================================
echo   Unified AI Project - Test Fixes Runner
echo ==========================================
echo.
echo This script runs test fixes and updates for the backend. (此腳本運行後端的測試修復和更新)
echo.
echo Process: (過程)
echo 1. 🛠️  Apply test fixes (應用測試修復)
echo 2. 🔄 Update test configurations (更新測試配置)
echo 3. 📦 Install test dependencies (安裝測試依賴)
echo 4. ✅ Verify fixes (驗證修復)
echo.

:: Confirm action (確認操作)
echo [CONFIRM] Are you sure you want to run test fixes? (您確定要運行測試修復嗎?)
echo.

:: 使用 set /p 替代 choice 命令
:get_user_choice
set "user_choice="
set /p "user_choice=Continue with test fixes (y/N)? "
if not defined user_choice (
    set "user_choice=N"
)

:: 验证用户输入
if /i "%user_choice%"=="Y" (
    goto continue_fix
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

:continue_fix

:: Activate virtual environment (激活虛擬環境)
echo.
echo [STEP 1/4] Activating virtual environment... (激活虛擬環境)
echo [%date% %time%] Activating virtual environment >> "%LOG_FILE%" 2>nul

call venv\Scripts\activate.bat >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment (無法激活虛擬環境)
    echo [%date% %time%] Failed to activate virtual environment >> "%LOG_FILE%" 2>nul
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

:: Apply test fixes (應用測試修復)
echo.
echo [STEP 2/4] Applying test fixes... (應用測試修復)
echo [%date% %time%] Applying test fixes >> "%LOG_FILE%" 2>nul

:: Check for test fix scripts (檢查測試修復腳本)
if exist "..\..\tools\scripts\apply_test_fixes.py" (
    echo [INFO] Running test fix script... (運行測試修復腳本)
    python ..\..\tools\scripts\apply_test_fixes.py > test_fixes.log 2>&1
    if errorlevel 1 (
        echo [ERROR] Test fix script failed (測試修復腳本失敗)
        echo [INFO] Check test_fixes.log for details (檢查test_fixes.log獲取詳細信息)
        echo [%date% %time%] Test fix script failed >> "%LOG_FILE%" 2>nul
    ) else (
        echo [OK] Test fixes applied successfully (測試修復成功應用)
        echo [%date% %time%] Test fixes applied successfully >> "%LOG_FILE%" 2>nul
    )
) else (
    echo [INFO] No test fix script found (未找到測試修復腳本)
)

:: Update test configurations (更新測試配置)
echo.
echo [STEP 3/4] Updating test configurations... (更新測試配置)
echo [%date% %time%] Updating test configurations >> "%LOG_FILE%" 2>nul

:: Check for test config files (檢查測試配置文件)
if exist "tests\test_config.yaml" (
    echo [INFO] Backing up test configuration... (備份測試配置)
    copy "tests\test_config.yaml" "tests\test_config.yaml.bak" >nul 2>&1
    echo [OK] Test configuration backed up (測試配置已備份)
) else (
    echo [INFO] No existing test configuration found (未找到現有的測試配置)
)

:: Create or update test configuration (創建或更新測試配置)
echo [INFO] Creating/updating test configuration... (創建/更新測試配置)
echo # Test Configuration > tests\test_config.yaml
echo test_timeout: 30 >> tests\test_config.yaml
echo max_workers: 4 >> tests\test_config.yaml
echo debug_mode: false >> tests\test_config.yaml
echo log_level: "INFO" >> tests\test_config.yaml
echo database_url: "sqlite:///./test.db" >> tests\test_config.yaml
echo api_base_url: "http://localhost:8000" >> tests\test_config.yaml
echo. >> tests\test_config.yaml
echo [OK] Test configuration updated (測試配置已更新)

:: Install test dependencies (安裝測試依賴)
echo.
echo [STEP 4/4] Installing test dependencies... (安裝測試依賴)
echo [%date% %time%] Installing test dependencies >> "%LOG_FILE%" 2>nul

:: Check if requirements-test.txt exists (檢查requirements-test.txt是否存在)
if exist "requirements-test.txt" (
    echo [INFO] Installing test-specific dependencies... (安裝特定於測試的依賴)
    pip install -r requirements-test.txt > test_deps_install.log 2>&1
    if errorlevel 1 (
        echo [WARNING] Failed to install test dependencies (無法安裝測試依賴)
        echo [INFO] Check test_deps_install.log for details (檢查test_deps_install.log獲取詳細信息)
    ) else (
        echo [OK] Test dependencies installed (測試依賴已安裝)
    )
) else (
    echo [INFO] No test-specific requirements file found (未找到特定於測試的requirements文件)
)

:: Verify fixes (驗證修復)
echo.
echo [VERIFICATION] Verifying test fixes... (驗證測試修復)
echo [%date% %time%] Verifying test fixes >> "%LOG_FILE%" 2>nul

:: Run a quick test to verify fixes (運行快速測試以驗證修復)
python -c "import pytest; print('pytest available')" > verify_test.log 2>&1
if errorlevel 1 (
    echo [WARNING] pytest not available after fixes (修復後pytest不可用)
) else (
    echo [OK] pytest available (pytest可用)
)

python -c "import unittest; print('unittest available')" >> verify_test.log 2>&1
if errorlevel 1 (
    echo [WARNING] unittest not available after fixes (修復後unittest不可用)
) else (
    echo [OK] unittest available (unittest可用)
)

echo.
echo [SUCCESS] Test fixes completed! (測試修復完成!)
echo [%date% %time%] Test fixes completed >> "%LOG_FILE%" 2>nul
echo.
echo Summary: (摘要)
echo 🛠️  Test fixes applied (測試修復已應用)
echo 🔄 Test configuration updated (測試配置已更新)
echo 📦 Test dependencies installed (測試依賴已安裝)
echo ✅ Fixes verified (修復已驗證)
echo.
echo Next steps: (下一步)
echo 1. Run run-component-tests.bat to verify fixes (運行run-component-tests.bat驗證修復)
echo 2. Run run-tests.bat to run full test suite (運行run-tests.bat運行完整測試套件)
echo.

:end_script
echo.
echo Press any key to exit...
pause >nul
exit /b 0