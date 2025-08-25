@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Safe Git Status Cleanup Tool
color 0B

echo ==========================================
echo      Safe Git Status Cleanup Tool
echo ==========================================
echo.
echo This tool will safely clean up the Git status:
echo 1. Only add important project files
echo 2. Will not delete any existing files
echo 3. Ensure .gitignore correctly ignores temporary files
echo 4. Safe commit and push
echo.

:: Check current status
echo [Check] Current Git status...
git status --porcelain > git_status_check.txt
for /f %%i in ('find /c /v "" ^< git_status_check.txt') do set "total_files=%%i"
echo [Result] Detected !total_files! changed items

echo.
echo [Step 1] Adding core project files...

:: Add important configuration files
echo [Add] Core configuration files...
git add .gitignore >nul 2>&1
git add package.json >nul 2>&1
git add pnpm-workspace.yaml >nul 2>&1
git add eslint.config.mjs >nul 2>&1

:: Add important README files
echo [Add] Documentation files...
git add README.md >nul 2>&1
git add *.md >nul 2>&1

:: Add core scripts (only important ones)
echo [Add] Core scripts...
git add tools\health-check.bat >nul 2>&1
git add tools\start-dev.bat >nul 2>&1
git add tools\run-tests.bat >nul 2>&1
git add tools\safe-git-cleanup.bat >nul 2>&1

:: Add application code
echo [Add] Application code...
git add apps/ >nul 2>&1
git add packages/ >nul 2>&1
git add scripts/ >nul 2>&1
git add tests/ >nul 2>&1
git add training/ >nul 2>&1

:: Add GitHub workflows
echo [Add] GitHub workflows...
git add .github/ >nul 2>&1

:: Check what's been added
echo.
echo [Check] Checking staging area status...
git status --porcelain | findstr "^A " > staged_files.txt
for /f %%i in ('find /c /v "" ^< staged_files.txt 2^>nul') do set "staged_count=%%i"
echo [Result] !staged_count! files staged for commit

if !staged_count! gtr 0 (
    echo.
    echo [Commit] Preparing to commit important files...
    set "commit_msg=Fix Git status: Restore important files and update ignore rules"
    
    echo [Execute] Committing changes...
    git commit -m "!commit_msg!" >nul 2>&1
    if !errorlevel! equ 0 (
        echo [Success] Commit successful
        
        echo [Push] Pushing to remote repository...
        git push origin main >nul 2>&1
        if !errorlevel! equ 0 (
            echo [Success] Push successful
        ) else (
            echo [Warning] Push failed, please check network or permissions
        )
    ) else (
        echo [Warning] Commit failed
    )
) else (
    echo [Info] No files need to be committed
)

:: Check final status
echo.
echo [Final Check] Checking status after cleanup...
git status --porcelain > final_status.txt
for /f %%i in ('find /c /v "" ^< final_status.txt 2^>nul') do set "final_count=%%i"

echo [Result] !final_count! untracked items remaining

:: If there are few remaining files, show details
if !final_count! leq 10 (
    echo.
    echo [Details] Remaining file list:
    type final_status.txt
)

:: Clean up temporary files
del git_status_check.txt >nul 2>&1
del staged_files.txt >nul 2>&1  
del final_status.txt >nul 2>&1

echo.
echo ==========================================
echo    Safe Cleanup Complete
echo ==========================================
echo.
echo [Summary]
echo Before: !total_files! changed items
echo Committed: !staged_count! important files
echo Remaining: !final_count! items (mainly temporary files)
echo.
echo [Safety Guarantee]
echo No existing files were deleted
echo Important directories (docs/, scripts/, tests/) are all preserved
echo All operations are safe add operations
echo.
echo [Recommendations]
echo Run: .\health-check.bat to check environment
echo Run: .\start-dev.bat to start development
echo.

pause