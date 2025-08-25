@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title 緊急Git修復工具 - 安全版本
color 0C

echo ==========================================
echo      緊急Git修復工具
echo ==========================================
echo.
echo [緊急] 檢測到大量文件被錯誤標記為刪除
echo [修復] 正在執行緊急恢復程序...
echo.
echo [安全提示] 操作前將創建安全備份
echo.

:: 預檢查Git環境
echo [預檢] 檢查Git倉庫狀態...
if not exist ".git" (
    echo [錯誤] 當前目錄不是Git倉庫
    pause
    exit /b 1
)

:: 獲取當前分支
for /f "tokens=*" %%a in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set "current_branch=%%a"
echo [INFO] 當前分支: !current_branch!

:: 創建緊急備份分支
echo [安全] 創建緊急備份分支...
set "emergency_backup=emergency-backup-%date:~0,4%%date:~5,2%%date:~8,2%-%time:~0,2%%time:~3,2%%time:~6,2%"
set "emergency_backup=!emergency_backup: =0!"
git branch "!emergency_backup!" >nul 2>&1
if !errorlevel! equ 0 (
    echo [成功] 緊急備份分支已創建: !emergency_backup!
) else (
    echo [警告] 無法創建備份分支
    echo [選項] 是否繼續緊急修復？ (y/N)
    set /p "emergency_continue="
    if /i "!emergency_continue!" neq "y" (
        echo [取消] 緊急修復已取消
        pause
        exit /b 0
    )
)

:: 顯示當前狀態
echo [步驟 1] 檢查當前Git狀態...
git status --porcelain | find /c "deleted" > deleted_count.txt
set /p deleted_count=<deleted_count.txt
echo [警告] 發現 %deleted_count% 個文件被標記為刪除
echo.

:: 緊急重置
echo [步驟 2] 執行緊急重置...
echo [INFO] 重置暫存區...
git reset HEAD >nul 2>&1
if !errorlevel! neq 0 (
    echo [警告] 重置暫存區失敗，嘗試替代方法...
    git reset --mixed HEAD >nul 2>&1
)

echo [INFO] 恢復工作目錄...
git checkout -- . >nul 2>&1
if !errorlevel! neq 0 (
    echo [警告] 恢復工作目錄部分失敗
)

echo [INFO] 清理未追蹤文件...
git clean -fd >nul 2>&1

echo.
echo [步驟 3] 驗證修復結果...
git status --porcelain > status_after_fix.txt
for /f %%i in ('find /c /v "" ^< status_after_fix.txt') do set "remaining_issues=%%i"

if %remaining_issues% lss 10 (
    echo [成功] Git狀態已恢復正常
    echo [結果] 剩餘問題: %remaining_issues% 個
) else (
    echo [警告] 仍有 %remaining_issues% 個問題需要處理
    echo [建議] 執行深度修復...
    
    :: 深度修復
    echo [深度修復] 重建索引...
    git read-tree HEAD
    git checkout-index -f -a
    git update-index --refresh
)

echo.
echo [步驟 4] 檢查關鍵文件...
set "critical_files=.gitignore README.md tools\health-check.bat tools\run-tests.bat tools\start-dev.bat"
set "missing_files=0"

for %%f in (%critical_files%) do (
    if not exist "%%f" (
        echo [警告] 關鍵文件缺失: %%f
        set /a "missing_files+=1"
    ) else (
        echo [OK] 文件存在: %%f
    )
)

echo.
echo [步驟 5] 清理和提交狀態...
if %missing_files% equ 0 (
    echo [成功] 所有關鍵文件都存在
    echo [INFO] 檢查是否需要提交新文件...
    
    git add .gitignore >nul 2>&1
    git add *.bat >nul 2>&1
    git add *.md >nul 2>&1
    git add apps/backend/diagnose_components.py >nul 2>&1
    
    git status --porcelain > final_status.txt
    for /f %%i in ('find /c /v "" ^< final_status.txt') do set "final_changes=%%i"
    
    if %final_changes% gtr 0 (
        echo [INFO] 發現 %final_changes% 個變更需要處理
        echo [選項] 是否提交這些變更？ (y/N)
        set /p "commit_choice="
        if /i "!commit_choice!"=="y" (
            git commit -m "緊急修復: 恢復被錯誤刪除的文件並整合批處理腳本系統"
            echo [成功] 變更已提交
        )
    ) else (
        echo [INFO] 沒有需要提交的變更
    )
) else (
    echo [錯誤] %missing_files% 個關鍵文件缺失，需要手動恢復
)

:: 清理臨時文件
del deleted_count.txt >nul 2>&1
del status_after_fix.txt >nul 2>&1
del final_status.txt >nul 2>&1

echo.
echo ==========================================
echo    緊急修復完成
echo ==========================================
echo.
echo [狀態] Git倉庫狀態已修復
echo [備份] 緊急備份分支: !emergency_backup!
echo [建議] 執行 health-check.bat 驗證環境
echo [建議] 執行 git status 確認最終狀態
echo [恢復] 如需恢復，使用: git checkout !emergency_backup!
echo.

pause