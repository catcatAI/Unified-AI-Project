@echo off
setlocal enabledelayedexpansion

echo ===================================
echo 文檔更新工具測試
echo ===================================
echo.

:: 檢查Python環境
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 錯誤: 未找到Python環境，請確保Python已安裝並添加到PATH中。
    exit /b 1
)

:: 設置腳本路徑
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set TEST_SCRIPT=%PROJECT_ROOT%\scripts\test_doc_tools.py

:: 檢查測試腳本是否存在
if not exist "%TEST_SCRIPT%" (
    echo 錯誤: 未找到測試腳本: %TEST_SCRIPT%
    exit /b 1
)

echo 運行文檔更新工具測試...
echo.

python "%TEST_SCRIPT%"

if %ERRORLEVEL% neq 0 (
    echo.
    echo 測試失敗！請檢查錯誤信息。
    exit /b 1
) else (
    echo.
    echo 測試成功完成！文檔更新工具功能正常。
)

pause
exit /b 0