@echo off
echo ===================================================
echo Unified AI Project 自動修復系統
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
echo 1. 執行語法錯誤修復...
python repair_scripts\syntax_repair.py --target . --verbose
if %ERRORLEVEL% NEQ 0 (
    echo 語法錯誤修復過程中出現錯誤，但將繼續執行其他修復。
)

echo.
echo 2. 執行路徑計算問題修復...
if exist repair_scripts\path_repair.py (
    python repair_scripts\path_repair.py --target . --verbose
)

echo.
echo 3. 執行文件結構修復...
if exist repair_scripts\structure_repair.py (
    python repair_scripts\structure_repair.py --target . --verbose
)

echo.
echo 4. 執行重複開發問題修復...
if exist repair_scripts\duplicate_fix.py (
    python repair_scripts\duplicate_fix.py --target . --verbose
)

echo.
echo 5. 執行未實作功能修復...
if exist repair_scripts\implementation_fix.py (
    python repair_scripts\implementation_fix.py --target . --verbose
)

echo.
echo 6. 執行配置文件修復...
if exist repair_scripts\config_repair.py (
    python repair_scripts\config_repair.py --target . --verbose
)

echo.
echo 7. 執行驗證測試...
if exist repair_scripts\quick_validate.py (
    python repair_scripts\quick_validate.py --target . --verbose
)

echo.
echo ===================================================
echo 修復完成！
echo ===================================================
echo.
echo 如果您發現任何問題，請查看日誌文件。
echo.

:end
pause