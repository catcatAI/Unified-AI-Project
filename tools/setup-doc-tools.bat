@echo off
setlocal enabledelayedexpansion

echo ===================================
echo 文檔更新工具安裝
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

echo 正在檢查並安裝必要的Python套件...

:: 安裝必要的Python套件
python -m pip install --upgrade pip
python -m pip install pyyaml colorama tqdm

if %ERRORLEVEL% neq 0 (
    echo.
    echo 錯誤: 安裝Python套件失敗。
    exit /b 1
)

echo.
echo 檢查文檔更新工具腳本...

:: 檢查文檔更新工具腳本是否存在
set DOC_PLAN_SCRIPT=%PROJECT_ROOT%\scripts\document_update_plan.py
set DOC_STATUS_SCRIPT=%PROJECT_ROOT%\scripts\update_doc_status.py

if not exist "%DOC_PLAN_SCRIPT%" (
    echo 錯誤: 未找到文檔更新計畫腳本: %DOC_PLAN_SCRIPT%
    exit /b 1
)

if not exist "%DOC_STATUS_SCRIPT%" (
    echo 錯誤: 未找到文檔狀態管理腳本: %DOC_STATUS_SCRIPT%
    exit /b 1
)

echo.
echo 運行測試以確保一切正常...

:: 運行測試腳本
set TEST_SCRIPT=%PROJECT_ROOT%\scripts\test_doc_tools.py

if exist "%TEST_SCRIPT%" (
    python "%TEST_SCRIPT%"
    
    if %ERRORLEVEL% neq 0 (
        echo.
        echo 警告: 測試失敗，但將繼續安裝。
    ) else (
        echo.
        echo 測試成功完成！
    )
) else (
    echo 警告: 未找到測試腳本，跳過測試步驟。
)

echo.
echo 創建快捷方式...

:: 創建桌面快捷方式
set SHORTCUT_VBS=%TEMP%\CreateShortcut.vbs
set DESKTOP_DIR=%USERPROFILE%\Desktop

echo Set oWS = WScript.CreateObject("WScript.Shell") > "%SHORTCUT_VBS%"
echo sLinkFile = "%DESKTOP_DIR%\文檔更新工具.lnk" >> "%SHORTCUT_VBS%"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%SHORTCUT_VBS%"
echo oLink.TargetPath = "%PROJECT_ROOT%\update-docs.bat" >> "%SHORTCUT_VBS%"
echo oLink.WorkingDirectory = "%PROJECT_ROOT%" >> "%SHORTCUT_VBS%"
echo oLink.Description = "專案文件更新工具" >> "%SHORTCUT_VBS%"
echo oLink.Save >> "%SHORTCUT_VBS%"

cscript //nologo "%SHORTCUT_VBS%"
del "%SHORTCUT_VBS%"

echo.
echo 安裝完成！
echo 您可以通過以下方式啟動文檔更新工具：
echo 1. 雙擊桌面上的「文檔更新工具」快捷方式
echo 2. 在專案根目錄執行 update-docs.bat
echo 3. 在tools目錄執行 update-docs.bat
echo.
echo 詳細使用說明請參考 %PROJECT_ROOT%\DOCUMENT_UPDATE_GUIDE.md

pause
exit /b 0