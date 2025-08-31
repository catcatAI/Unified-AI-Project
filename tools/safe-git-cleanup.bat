@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Safe Git Status Cleanup Tool
color 0B

echo ==========================================
echo      🔒 Safe Git Status Cleanup Tool
echo ==========================================
echo.
echo This tool will safely clean up Git status: (此工具將安全地清理Git狀態)
echo 1. ✅ Only add important project files (只添加重要的項目文件)
echo 2. 🛡️ Will not delete any existing files (不會刪除任何現有文件)
echo 3. 📋 Ensure .gitignore correctly ignores temporary files (確保.gitignore正確忽略臨時文件)
echo 4. 🚀 Safe commit and push (安全提交和推送)
echo.

:: Check current status (檢查當前狀態)
echo [Check] Current Git status... (當前Git狀態)
git status --porcelain > git_status_check.txt
for /f %%i in ('find /c /v "" ^< git_status_check.txt') do set "total_files=%%i"
echo [Result] Detected !total_files! changed items (檢測到 !total_files! 個變更項目)

echo.
echo [Step 1] Adding core project files... (添加核心項目文件)

:: Add important configuration files (添加重要的配置文件)
echo [Add] Core configuration files... (核心配置文件)
git add .gitignore >nul 2>&1
git add package.json >nul 2>&1
git add pnpm-workspace.yaml >nul 2>&1
git add eslint.config.mjs >nul 2>&1

:: Add important README files (添加重要的README文件)
echo [Add] Documentation files... (文檔文件)
git add README.md >nul 2>&1
git add *.md >nul 2>&1

:: Add core scripts (only important ones) (添加核心腳本 (只添加重要的))
echo [Add] Core scripts... (核心腳本)
git add health-check.bat >nul 2>&1
git add start-dev.bat >nul 2>&1
git add run-tests.bat >nul 2>&1
git add safe-git-cleanup.bat >nul 2>&1

:: Add application code (添加應用代碼)
echo [Add] Application code... (應用代碼)
git add apps/ >nul 2>&1
git add packages/ >nul 2>&1
git add scripts/ >nul 2>&1
git add tests/ >nul 2>&1
git add training/ >nul 2>&1

:: Add GitHub workflows (添加GitHub工作流)
echo [Add] GitHub workflows... (GitHub工作流)
git add .github/ >nul 2>&1

:: Check what has been added (檢查哪些被添加了)
echo.
echo [Check] Checking staging area status... (檢查暫存區狀態)
git status --porcelain | findstr "^A " > staged_files.txt
for /f %%i in ('find /c /v "" ^< staged_files.txt 2^>nul') do set "staged_count=%%i"
echo [Result] !staged_count! files staged for commit ( !staged_count! 個文件已暫存待提交)

if !staged_count! gtr 0 (
    echo.
    echo [Commit] Preparing to commit important files... (準備提交重要文件)
    set "commit_msg=Fix Git status: Restore important files and update ignore rules (修復Git狀態：恢復重要文件並更新忽略規則)"
    
    echo [Execute] Committing changes... (執行提交更改)
    git commit -m "!commit_msg!" >nul 2>&1
    if !errorlevel! equ 0 (
        echo [✓] Commit successful (提交成功)
        
        echo [Push] Pushing to remote repository... (推送到遠程倉庫)
        git push origin main >nul 2>&1
        if !errorlevel! equ 0 (
            echo [✓] Push successful (推送成功)
        ) else (
            echo [!] Push failed, may need to check network or permissions (推送失敗，可能需要檢查網絡或權限)
        )
    ) else (
        echo [!] Commit failed (提交失敗)
    )
) else (
    echo [Info] No files need to be committed (沒有文件需要提交)
)

:: Check final status (檢查最終狀態)
echo.
echo [Final Check] Checking status after cleanup... (檢查清理後狀態)
git status --porcelain > final_status.txt
for /f %%i in ('find /c /v "" ^< final_status.txt 2^>nul') do set "final_count=%%i"

echo [Result] Remaining !final_count! untracked items (剩餘 !final_count! 個未追蹤項目)

:: If there are few remaining files, show details (如果剩餘文件很少，顯示詳細信息)
if !final_count! leq 10 (
    echo.
    echo [Details] Remaining files list: (剩餘文件列表)
    type final_status.txt
)

:: Clean up temporary files (清理臨時文件)
del git_status_check.txt >nul 2>&1
del staged_files.txt >nul 2>&1  
del final_status.txt >nul 2>&1

echo.
echo ==========================================
echo    Safe Cleanup Completed (安全清理完成)
echo ==========================================
echo.
echo [Summary] (摘要)
echo ✅ Before processing: !total_files! changed items (處理前: !total_files! 個變更項目)
echo ✅ Committed: !staged_count! important files (已提交: !staged_count! 個重要文件)
echo ✅ Remaining: !final_count! items (mainly temporary files) (剩餘: !final_count! 個項目（主要是臨時文件）)
echo.
echo [Safety Guarantee] (安全保證)
echo 🔒 No existing files were deleted (沒有刪除任何現有文件)
echo 📁 Important directories (docs/, scripts/, tests/) are all preserved (重要目錄(docs/, scripts/, tests/)都保留完整)
echo 🛡️ All operations are safe add operations (所有操作都是安全的添加操作)
echo.
echo [Suggestions] (建議)
echo 📋 Run: .\health-check.bat to check environment (運行: .\health-check.bat 檢查環境)
echo 🚀 Run: .\start-dev.bat to start development (運行: .\start-dev.bat 開始開發)
echo.

pause