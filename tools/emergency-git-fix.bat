@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Emergency Git Fix
color 0C

:: Add error handling and logging (添加錯誤處理和日志記錄)
set "LOG_FILE=%~dp0emergency-git-fix-errors.log"
set "SCRIPT_NAME=emergency-git-fix.bat"

:: Log script start (記錄腳本啟動)
echo [%date% %time%] Script started: %SCRIPT_NAME% >> "%LOG_FILE%" 2>nul

echo ==========================================
echo   🔴 Unified AI Project - Emergency Git Fix
echo ==========================================
echo.
echo This script performs emergency Git operations to recover from critical issues. (此腳本執行緊急Git操作以從嚴重問題中恢復)
echo.
echo ⚠️  WARNING: This script performs destructive operations! (警告：此腳本執行破壞性操作!)
echo.
echo Process: (過程)
echo 1. 🆘 Reset to last known good commit (重置到最後一個已知的良好提交)
echo 2. 🧹 Clean untracked files (清理未跟踪的文件)
echo 3. 📦 Restore important files (恢復重要文件)
echo 4. ✅ Verify repository status (驗證倉庫狀態)
echo.

:: Confirm action (確認操作)
echo [CONFIRM] Are you sure you want to perform emergency Git fix? (您確定要執行緊急Git修復嗎?)
echo.
echo This will: (這將:)
echo - Reset your working directory to the last commit (將您的工作目錄重置到最後一次提交)
echo - Delete all uncommitted changes (刪除所有未提交的更改)
echo - Delete all untracked files (刪除所有未跟踪的文件)
echo.

:: 使用 set /p 替代 choice 命令
:get_user_choice
set "user_choice="
set /p "user_choice=Continue with emergency Git fix (y/N)? "
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

:: Backup current state (備份當前狀態)
echo.
echo [STEP 1/5] Creating backup of current state... (創建當前狀態的備份)
echo [%date% %time%] Creating backup of current state >> "%LOG_FILE%" 2>nul

:: Create a backup branch (創建備份分支)
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "backup_branch=emergency-backup-%dt:~0,8%-%dt:~8,6%"
git checkout -b %backup_branch% > backup_create.log 2>&1
if errorlevel 1 (
    echo [WARNING] Failed to create backup branch (無法創建備份分支)
    echo [INFO] Check backup_create.log for details (檢查backup_create.log獲取詳細信息)
) else (
    echo [OK] Backup branch created: %backup_branch% (備份分支已創建: %backup_branch%)
)

:: Reset to last known good commit (重置到最後一個已知的良好提交)
echo.
echo [STEP 2/5] Resetting to last known good commit... (重置到最後一個已知的良好提交)
echo [%date% %time%] Resetting to last known good commit >> "%LOG_FILE%" 2>nul

git reset --hard HEAD > reset_hard.log 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to reset to last commit (無法重置到最後一次提交)
    echo [INFO] Check reset_hard.log for details (檢查reset_hard.log獲取詳細信息)
    echo [%date% %time%] Failed to reset to last commit >> "%LOG_FILE%" 2>nul
    echo Press any key to exit...
    pause >nul
    exit /b 1
)
echo [OK] Repository reset to last commit (倉庫重置到最後一次提交)

:: Clean untracked files (清理未跟踪的文件)
echo.
echo [STEP 3/5] Cleaning untracked files... (清理未跟踪的文件)
echo [%date% %time%] Cleaning untracked files >> "%LOG_FILE%" 2>nul

git clean -fd > clean_untracked.log 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to clean untracked files (無法清理未跟踪的文件)
    echo [INFO] Check clean_untracked.log for details (檢查clean_untracked.log獲取詳細信息)
    echo [%date% %time%] Failed to clean untracked files >> "%LOG_FILE%" 2>nul
) else (
    echo [OK] Untracked files cleaned (未跟踪的文件已清理)
)

:: Restore important files (恢復重要文件)
echo.
echo [STEP 4/5] Restoring important files... (恢復重要文件)
echo [%date% %time%] Restoring important files >> "%LOG_FILE%" 2>nul

:: Restore configuration files (恢復配置文件)
if exist ".gitignore.bak" (
    copy ".gitignore.bak" ".gitignore" >nul 2>&1
    echo [OK] .gitignore restored (已恢復.gitignore)
) else if not exist ".gitignore" (
    echo [INFO] Creating default .gitignore (創建默認.gitignore)
    echo node_modules/ > .gitignore
    echo *.log >> .gitignore
    echo venv/ >> .gitignore
    echo .env >> .gitignore
    echo dist/ >> .gitignore
    echo build/ >> .gitignore
    echo __pycache__/ >> .gitignore
    echo *.pyc >> .gitignore
)

:: Restore package.json if missing (如果缺失則恢復package.json)
if not exist "package.json" (
    echo [INFO] package.json not found, creating minimal version (未找到package.json，創建最小版本)
    echo { > package.json
    echo   "name": "unified-ai-project", >> package.json
    echo   "version": "1.0.0", >> package.json
    echo   "description": "Unified AI Project", >> package.json
    echo   "scripts": { >> package.json
    echo     "dev": "pnpm --filter frontend-dashboard dev" >> package.json
    echo   } >> package.json
    echo } >> package.json
    echo [OK] Minimal package.json created (已創建最小package.json)
)

:: Verify repository status (驗證倉庫狀態)
echo.
echo [STEP 5/5] Verifying repository status... (驗證倉庫狀態)
echo [%date% %time%] Verifying repository status >> "%LOG_FILE%" 2>nul

git status > final_status.log 2>&1
echo [OK] Repository status verified (倉庫狀態已驗證)

:: Check for critical directories (檢查關鍵目錄)
set "missing_critical=0"
if not exist "apps\" (
    echo [WARNING] Critical directory 'apps' missing (關鍵目錄'apps'缺失)
    set /a "missing_critical+=1"
)
if not exist "packages\" (
    echo [WARNING] Critical directory 'packages' missing (關鍵目錄'packages'缺失)
    set /a "missing_critical+=1"
)
if not exist "scripts\" (
    echo [WARNING] Critical directory 'scripts' missing (關鍵目錄'scripts'缺失)
    set /a "missing_critical+=1"
)

if %missing_critical% gtr 0 (
    echo [INFO] %missing_critical% critical directories missing ( %missing_critical% 個關鍵目錄缺失)
    echo [SUGGESTION] Consider cloning the repository again (建議再次克隆倉庫)
) else (
    echo [OK] All critical directories present (所有關鍵目錄都存在)
)

echo.
echo [SUCCESS] Emergency Git fix completed! (緊急Git修復完成!)
echo [%date% %time%] Emergency Git fix completed >> "%LOG_FILE%" 2>nul
echo.
echo Summary: (摘要)
echo 🔴 Backup branch: %backup_branch% (備份分支: %backup_branch%)
echo 🔄 Repository reset to last commit (倉庫重置到最後一次提交)
echo 🧹 Untracked files cleaned (未跟踪的文件已清理)
echo 📄 Critical files restored (關鍵文件已恢復)
echo.
echo Next steps: (下一步)
echo 1. Review changes in backup branch if needed (如果需要，請查看備份分支中的更改)
echo 2. Run health-check.bat to verify environment (運行health-check.bat驗證環境)
echo 3. Run start-dev.bat to resume development (運行start-dev.bat恢復開發)
echo.

:end_script
echo.
echo Press any key to exit...
pause >nul
exit /b 0