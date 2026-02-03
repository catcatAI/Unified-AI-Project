@echo off
echo ===================================================
echo 自動修復系統整合工具
echo ===================================================
echo.

cd /d "%~dp0"

echo 正在檢查Python是否可用...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo Python未安裝或不在PATH中，請安裝Python後再試。
    goto :end
)

echo.
echo 正在執行自動修復系統整合...
python auto_repair_integration.py --fix --backup --verbose
if %ERRORLEVEL% NEQ 0 (
    echo 整合過程中出現錯誤，請檢查日誌。
    goto :end
)

echo.
echo 整合完成！
echo.
echo 現在可以使用以下命令執行整合後的自動修復系統：
echo   run_integrated_repair.bat
echo.

:end
pause