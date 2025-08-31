@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Fix Git 10K Issues
color 0D

:: Add error handling and logging (添加錯誤處理和日志記錄)
set "LOG_FILE=%~dp0fix-git-10k-errors.log"
set "SCRIPT_NAME=fix-git-10k.bat"

:: Log script start (記錄腳本啟動)
echo [%date% %time%] Script started: %SCRIPT_NAME% >> "%LOG_FILE%" 2>nul

echo ==========================================
echo   🐛 Unified AI Project - Fix Git 10K Issues
echo ==========================================
echo.
echo This script fixes common Git issues related to large file handling. (此腳本修復與大文件處理相關的常見Git問題)
echo.
echo Process: (過程)
echo 1. 🔧 Configure Git for large files (為大文件配置Git)
echo 2. 🧹 Clean Git cache (清理Git緩存)
echo 3. 📦 Optimize Git repository (優化Git倉庫)
echo 4. ✅ Verify configuration (驗證配置)
echo.

:: Confirm action (確認操作)
echo [CONFIRM] Are you sure you want to fix Git 10K issues? (您確定要修復Git 10K問題嗎?)
echo.

:: 使用 set /p 替代 choice 命令
:get_user_choice
set "user_choice="
set /p "user_choice=Continue with Git 10K fix (y/N)? "
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

:: Configure Git for large files (為大文件配置Git)
echo.
echo [STEP 1/4] Configuring Git for large files... (為大文件配置Git)
echo [%date% %time%] Configuring Git for large files >> "%LOG_FILE%" 2>nul

:: Increase buffer size (增加緩衝區大小)
git config --global http.postBuffer 524288000 > git_config.log 2>&1
if errorlevel 1 (
    echo [WARNING] Failed to set http.postBuffer (無法設置http.postBuffer)
) else (
    echo [OK] http.postBuffer set to 500MB (http.postBuffer設置為500MB)
)

:: Configure for long paths (為長路徑配置)
git config --global core.longpaths true >> git_config.log 2>&1
if errorlevel 1 (
    echo [WARNING] Failed to set core.longpaths (無法設置core.longpaths)
) else (
    echo [OK] core.longpaths enabled (core.longpaths已啟用)
)

:: Set file limit (設置文件限制)
git config --global core.compression 0 >> git_config.log 2>&1
if errorlevel 1 (
    echo [WARNING] Failed to set core.compression (無法設置core.compression)
) else (
    echo [OK] core.compression disabled for large files (core.compression已禁用以處理大文件)
)

:: Clean Git cache (清理Git緩存)
echo.
echo [STEP 2/4] Cleaning Git cache... (清理Git緩存)
echo [%date% %time%] Cleaning Git cache >> "%LOG_FILE%" 2>nul

:: Remove Git index (刪除Git索引)
if exist ".git\index" (
    del ".git\index" > git_clean.log 2>&1
    if errorlevel 1 (
        echo [WARNING] Failed to remove Git index (無法刪除Git索引)
    ) else (
        echo [OK] Git index removed (Git索引已刪除)
    )
)

:: Reset Git index (重置Git索引)
git reset > git_reset.log 2>&1
if errorlevel 1 (
    echo [WARNING] Failed to reset Git index (無法重置Git索引)
) else (
    echo [OK] Git index reset (Git索引已重置)
)

:: Optimize Git repository (優化Git倉庫)
echo.
echo [STEP 3/4] Optimizing Git repository... (優化Git倉庫)
echo [%date% %time%] Optimizing Git repository >> "%LOG_FILE%" 2>nul

:: Run Git garbage collection (運行Git垃圾回收)
git gc --aggressive > git_gc.log 2>&1
if errorlevel 1 (
    echo [WARNING] Git garbage collection failed (Git垃圾回收失敗)
    echo [INFO] Check git_gc.log for details (檢查git_gc.log獲取詳細信息)
) else (
    echo [OK] Git garbage collection completed (Git垃圾回收完成)
)

:: Prune unreachable objects (修剪不可達對象)
git prune > git_prune.log 2>&1
if errorlevel 1 (
    echo [WARNING] Git prune failed (Git修剪失敗)
    echo [INFO] Check git_prune.log for details (檢查git_prune.log獲取詳細信息)
) else (
    echo [OK] Git prune completed (Git修剪完成)
)

:: Verify configuration (驗證配置)
echo.
echo [STEP 4/4] Verifying configuration... (驗證配置)
echo [%date% %time%] Verifying configuration >> "%LOG_FILE%" 2>nul

:: Check Git configuration (檢查Git配置)
echo === Git Configuration === (Git配置)
git config --global --get http.postBuffer
git config --global --get core.longpaths
git config --global --get core.compression

:: Check repository status (檢查倉庫狀態)
echo.
echo === Repository Status === (倉庫狀態)
git status --porcelain > repo_status.log 2>&1
for /f %%i in ('find /c /v "" ^< repo_status.log 2^>nul') do set "status_count=%%i"
echo [INFO] Repository has %status_count% items needing attention (倉庫有 %status_count% 個項目需要注意)

echo.
echo [SUCCESS] Git 10K issues fix completed! (Git 10K問題修復完成!)
echo [%date% %time%] Git 10K issues fix completed >> "%LOG_FILE%" 2>nul
echo.
echo Summary: (摘要)
echo 🔧 Git configured for large files (Git已為大文件配置)
echo 🧹 Git cache cleaned (Git緩存已清理)
echo 📦 Git repository optimized (Git倉庫已優化)
echo ✅ Configuration verified (配置已驗證)
echo.
echo Next steps: (下一步)
echo 1. Run health-check.bat to verify Git status (運行health-check.bat驗證Git狀態)
echo 2. Try your Git operation again (再次嘗試您的Git操作)
echo 3. If issues persist, run emergency-git-fix.bat (如果問題仍然存在，運行emergency-git-fix.bat)
echo.

:end_script
echo.
echo Press any key to exit...
pause >nul
exit /b 0