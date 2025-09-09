@echo off
setlocal enabledelayedexpansion

echo ===================================
echo 專案文件更新工具
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
set DOC_PLAN_SCRIPT=%PROJECT_ROOT%\scripts\document_update_plan.py
set DOC_STATUS_SCRIPT=%PROJECT_ROOT%\scripts\update_doc_status.py

:: 檢查腳本是否存在
if not exist "%DOC_PLAN_SCRIPT%" (
    echo 錯誤: 未找到文檔更新計畫腳本: %DOC_PLAN_SCRIPT%
    exit /b 1
)

if not exist "%DOC_STATUS_SCRIPT%" (
    echo 錯誤: 未找到文檔狀態管理腳本: %DOC_STATUS_SCRIPT%
    exit /b 1
)

:: 顯示菜單
:menu
cls
echo ===================================
echo 專案文件更新工具
echo ===================================
echo.
echo 請選擇操作:
echo 1. 掃描專案並生成文檔更新計畫
echo 2. 列出所有文檔及其狀態
echo 3. 列出待更新的文檔
echo 4. 列出更新中的文檔
echo 5. 列出已更新的文檔
echo 6. 查看文檔詳細信息
echo 7. 更新文檔狀態
echo 8. 生成更新報告
echo 9. 打開文檔更新指南
echo 0. 退出
echo.

set /p choice=請輸入選項 (0-9): 

if "%choice%"=="1" goto scan_project
if "%choice%"=="2" goto list_all_docs
if "%choice%"=="3" goto list_pending_docs
if "%choice%"=="4" goto list_in_progress_docs
if "%choice%"=="5" goto list_completed_docs
if "%choice%"=="6" goto show_doc_details
if "%choice%"=="7" goto update_doc_status
if "%choice%"=="8" goto generate_report
if "%choice%"=="9" goto open_guide
if "%choice%"=="0" goto end

echo 無效的選項，請重新選擇。
timeout /t 2 >nul
goto menu

:scan_project
echo.
echo 正在掃描專案並生成文檔更新計畫...
python "%DOC_PLAN_SCRIPT%"
echo.
echo 操作完成。
pause
goto menu

:list_all_docs
echo.
echo 列出所有文檔及其狀態...
python "%DOC_STATUS_SCRIPT%" list
echo.
echo 操作完成。
pause
goto menu

:list_pending_docs
echo.
echo 列出待更新的文檔...
python "%DOC_STATUS_SCRIPT%" list --status "待更新"
echo.
echo 操作完成。
pause
goto menu

:list_in_progress_docs
echo.
echo 列出更新中的文檔...
python "%DOC_STATUS_SCRIPT%" list --status "更新中"
echo.
echo 操作完成。
pause
goto menu

:list_completed_docs
echo.
echo 列出已更新的文檔...
python "%DOC_STATUS_SCRIPT%" list --status "已更新"
echo.
echo 操作完成。
pause
goto menu

:show_doc_details
echo.
set /p doc_path=請輸入文檔路徑: 
echo.
echo 顯示文檔詳細信息...
python "%DOC_STATUS_SCRIPT%" show "%doc_path%"
echo.
echo 操作完成。
pause
goto menu

:update_doc_status
echo.
set /p doc_path=請輸入文檔路徑: 
echo.
echo 可用狀態: 待更新, 更新中, 已更新, 需審查, 無需更新
set /p status=請輸入新狀態: 
set /p notes=請輸入註釋 (可選): 

if "%notes%"=="" (
    python "%DOC_STATUS_SCRIPT%" update "%doc_path%" "%status%"
) else (
    python "%DOC_STATUS_SCRIPT%" update "%doc_path%" "%status%" --notes "%notes%"
)

echo.
echo 操作完成。
pause
goto menu

:generate_report
echo.
echo 生成更新報告...
python "%DOC_STATUS_SCRIPT%" report
echo.
echo 報告已生成: %PROJECT_ROOT%\doc_update_report.md
echo.
set /p open_report=是否打開報告? (y/n): 
if /i "%open_report%"=="y" (
    start "" "%PROJECT_ROOT%\doc_update_report.md"
)
echo 操作完成。
pause
goto menu

:open_guide
echo.
echo 打開文檔更新指南...
start "" "%PROJECT_ROOT%\DOCUMENT_UPDATE_GUIDE.md"
echo.
echo 操作完成。
pause
goto menu

:end
echo.
echo 感謝使用專案文件更新工具！
echo.
exit /b 0