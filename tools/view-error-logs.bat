@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Error Log Viewer
color 0C

:: Add error handling and logging (添加錯誤處理和日志記錄)
set "LOG_FILE=%~dp0log-viewer-errors.log"
set "SCRIPT_NAME=view-error-logs.bat"

:: Log script start (記錄腳本啟動)
echo [%date% %time%] Script started: %SCRIPT_NAME% >> "%LOG_FILE%" 2>nul

echo ==========================================
echo   Unified AI Project - Error Log Viewer
echo ==========================================
echo.
echo This tool displays error logs from various Unified AI Project components. (此工具顯示來自各種Unified AI Project組件的錯誤日志)
echo.

:: Define log files to check (定義要檢查的日志文件)
set "log_files=ai-runner-errors.log health-check-errors.log dev-env-errors.log test-runner-errors.log log-viewer-errors.log"

echo [INFO] Checking for error logs... (檢查錯誤日志)
echo.

set "found_logs=0"

:: Check each log file (檢查每個日志文件)
for %%f in (%log_files%) do (
    if exist "%~dp0%%f" (
        echo === %%f ===
        type "%~dp0%%f"
        echo.
        echo ==========================================
        echo.
        set /a "found_logs+=1"
    )
)

:: Check for any other .log files in the directory (檢查目錄中的其他.log文件)
echo [INFO] Checking for additional log files... (檢查其他日志文件)
for %%f in ("%~dp0*.log") do (
    echo %%~nxf | findstr /i "error" >nul
    if errorlevel 1 (
        echo === %%~nxf ===
        type "%%f"
        echo.
        echo ==========================================
        echo.
        set /a "found_logs+=1"
    )
)

if %found_logs% equ 0 (
    echo [INFO] No error logs found. (未找到錯誤日志)
    echo.
    echo This is good! It means your Unified AI Project is running smoothly. (這很好！這意味著您的Unified AI Project運行順利)
    echo.
) else (
    echo [INFO] Found %found_logs% log file(s) with content. (找到 %found_logs% 個包含內容的日志文件)
    echo.
)

echo.
echo [TIPS] (提示)
echo 📋 To clear logs, manually delete the .log files (要清除日志，請手動刪除.log文件)
echo 🛠️  Run health-check.bat to verify system status (運行health-check.bat驗證系統狀態)
echo 🚀 Run start-dev.bat to begin development (運行start-dev.bat開始開發)
echo.

echo [%date% %time%] Log viewing completed >> "%LOG_FILE%" 2>nul

:end_script
echo.
echo Press any key to return to main menu... (按任意鍵返回主菜單)
pause >nul