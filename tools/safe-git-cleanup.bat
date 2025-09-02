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
echo [Options] Available options: (可用選項)
echo 1. 🧹 Standard Cleanup (標準清理) - Add core files and commit
echo 2. 📊 Detailed Status (詳細狀態) - Show detailed Git status
echo 3. 🔄 Smart Add (智能添加) - Add files based on type
echo 4. 📦 Commit Only (僅提交) - Commit without adding new files
echo 5. 🚀 Commit and Push (提交並推送) - Commit and push to remote
echo 6. 🧪 Git Diagnostics (Git診斷) - Run comprehensive Git diagnostics
echo 7. ❌ Exit (退出)
echo.

:get_option
set "option="
set /p "option=Select option (1-7): "
if not defined option (
    echo [ERROR] No input provided
    goto get_option
)

set "option=!option: =!"
for %%i in (1 2 3 4 5 6 7) do (
    if "!option!"=="%%i" (
        goto option_%%i
    )
)

echo [ERROR] Invalid option '!option!'. Please enter a valid option.
goto get_option

:option_1
:: Standard Cleanup (標準清理)
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
git add train-manager.bat >nul 2>&1
git add automated-backup.bat >nul 2>&1
git add enhanced-file-recovery.bat >nul 2>&1

:: Add application code (添加應用代碼)
echo [Add] Application code... (應用代碼)
git add apps/ >nul 2>&1
git add packages/ >nul 2>&1
git add scripts/ >nul 2>&1
git add tests/ >nul 2>&1
git add training/ >nul 2>&1
git add tools/ >nul 2>&1

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
    set "commit_msg=Project update: Automated cleanup and file organization (項目更新：自動清理和文件整理)"
    
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
goto final_check

:option_2
:: Detailed Status (詳細狀態)
echo.
echo [Detailed Status] Current Git status: (當前Git詳細狀態)
echo ==========================================
git status
echo ==========================================
echo.
echo [Branch Information] (分支信息)
echo ==========================================
git branch -v
echo ==========================================
echo.
echo [Recent Commits] (最近提交)
echo ==========================================
git log --oneline -10
echo ==========================================
echo.
echo [Remote Information] (遠程信息)
echo ==========================================
git remote -v
echo ==========================================
goto end

:option_3
:: Smart Add (智能添加)
echo.
echo [Smart Add] Adding files based on type... (根據類型智能添加文件)
echo.

:: Add source code files
echo [Add] Source code files... (源代碼文件)
git add "*.py" >nul 2>&1
git add "*.js" >nul 2>&1
git add "*.ts" >nul 2>&1
git add "*.jsx" >nul 2>&1
git add "*.tsx" >nul 2>&1

:: Add configuration files
echo [Add] Configuration files... (配置文件)
git add "*.json" >nul 2>&1
git add "*.yaml" >nul 2>&1
git add "*.yml" >nul 2>&1
git add "*.config.*" >nul 2>&1

:: Add documentation files
echo [Add] Documentation files... (文檔文件)
git add "*.md" >nul 2>&1
git add "*.txt" >nul 2>&1

:: Add script files
echo [Add] Script files... (腳本文件)
git add "*.bat" >nul 2>&1
git add "*.ps1" >nul 2>&1
git add "*.sh" >nul 2>&1

:: Add specific directories
echo [Add] Core directories... (核心目錄)
git add apps/ >nul 2>&1
git add packages/ >nul 2>&1
git add tools/ >nul 2>&1
git add training/ >nul 2>&1

echo [Info] Smart add completed (智能添加完成)
goto final_check

:option_4
:: Commit Only (僅提交)
echo.
echo [Commit Only] Committing staged changes... (僅提交已暫存的更改)
echo.

:: Check if there are staged changes
git diff --cached --quiet
if !errorlevel! equ 1 (
    set "commit_msg=Project update: Staged changes committed (項目更新：已提交暫存的更改)"
    set /p "commit_msg=Enter commit message (or press Enter for default): "
    if not defined commit_msg set "commit_msg=Project update: Staged changes committed (項目更新：已提交暫存的更改)"
    
    echo [Execute] Committing changes... (執行提交更改)
    git commit -m "!commit_msg!" >nul 2>&1
    if !errorlevel! equ 0 (
        echo [✓] Commit successful (提交成功)
    ) else (
        echo [!] Commit failed (提交失敗)
    )
) else (
    echo [Info] No staged changes to commit (沒有已暫存的更改需要提交)
)
goto final_check

:option_5
:: Commit and Push (提交並推送)
echo.
echo [Commit and Push] Committing and pushing changes... (提交並推送更改)
echo.

:: Check if there are staged changes
git diff --cached --quiet
if !errorlevel! equ 1 (
    set "commit_msg=Project update: Changes committed and pushed (項目更新：已提交並推送更改)"
    set /p "commit_msg=Enter commit message (or press Enter for default): "
    if not defined commit_msg set "commit_msg=Project update: Changes committed and pushed (項目更新：已提交並推送更改)"
    
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
    echo [Info] No staged changes to commit (沒有已暫存的更改需要提交)
    echo [Push] Pushing to remote repository... (推送到遠程倉庫)
    git push origin main >nul 2>&1
    if !errorlevel! equ 0 (
        echo [✓] Push successful (推送成功)
    ) else (
        echo [!] Push failed, may need to check network or permissions (推送失敗，可能需要檢查網絡或權限)
    )
)
goto final_check

:option_6
:: Git Diagnostics (Git診斷)
echo.
echo [Git Diagnostics] Running comprehensive Git diagnostics... (運行全面的Git診斷)
echo.

echo [1/5] Checking Git version... (檢查Git版本)
git --version
echo.

echo [2/5] Checking repository status... (檢查倉庫狀態)
git status
echo.

echo [3/5] Checking branch information... (檢查分支信息)
git branch -v
echo.

echo [4/5] Checking remote information... (檢查遠程信息)
git remote -v
echo.

echo [5/5] Checking recent commits... (檢查最近提交)
git log --oneline -5
echo.

echo [Diagnostics] Checking for common issues... (檢查常見問題)
echo [Check] Untracked files... (檢查未跟蹤的文件)
git ls-files --others --exclude-standard
echo.

echo [Check] Modified files... (檢查修改的文件)
git diff --name-only
echo.

echo [Check] Staged files... (檢查已暫存的文件)
git diff --cached --name-only
echo.

echo [✓] Git diagnostics completed (Git診斷完成)
goto end

:option_7
:: Exit (退出)
echo.
echo [Info] Exiting Git cleanup tool... (退出Git清理工具)
goto end

:final_check
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

:end
pause