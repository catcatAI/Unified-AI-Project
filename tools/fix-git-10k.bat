@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Git 10K+ 問題解決工具 - 安全版本
color 0D

echo ==========================================
echo      Git 10K+ 問題解決工具
echo ==========================================
echo.
echo 此工具將安全地處理：
echo 1. 提交應該追蹤的項目本體文件
echo 2. 忽略大型數據集和臨時文件
echo 3. 清理不必要的追蹤
echo.
echo [安全提示] 操作前將創建備份分支
echo.

:: 預檢查Git狀態和環境
echo [預檢] 檢查Git倉庫狀態...
if not exist ".git" (
    echo [錯誤] 當前目錄不是Git倉庫
    pause
    exit /b 1
)

:: 檢查是否有未提交的重要變更
git diff --name-only HEAD > pending_changes.txt
for /f %%i in ('find /c /v "" ^< pending_changes.txt') do set "pending_count=%%i"
if !pending_count! gtr 0 (
    echo [警告] 檢測到 !pending_count! 個未提交的變更
    echo [建議] 建議先備份當前工作
    echo [選項] 是否繼續？ (y/N)
    set /p "continue_choice="
    if /i "!continue_choice!" neq "y" (
        echo [取消] 操作已取消
        del pending_changes.txt >nul 2>&1
        pause
        exit /b 0
    )
)

:: 獲取當前分支名稱
for /f "tokens=2 delims= " %%a in ('git branch --show-current 2^>nul') do set "current_branch=%%a"
if "!current_branch!"=="" (
    for /f "tokens=*" %%a in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set "current_branch=%%a"
)
echo [INFO] 當前分支: !current_branch!

:: 創建安全備份分支
echo [安全] 創建備份分支...
set "backup_branch=backup-before-10k-fix-%date:~0,4%%date:~5,2%%date:~8,2%-%time:~0,2%%time:~3,2%%time:~6,2%"
set "backup_branch=!backup_branch: =0!"
git branch "!backup_branch!" >nul 2>&1
if !errorlevel! equ 0 (
    echo [成功] 備份分支已創建: !backup_branch!
) else (
    echo [警告] 無法創建備份分支，但可以繼續
)

:: 檢查Git狀態
echo [步驟 1] 檢查當前Git狀態...
git status --porcelain > git_status_temp.txt
if %errorlevel% neq 0 (
    echo [錯誤] Git命令執行失敗
    del pending_changes.txt >nul 2>&1
    pause
    exit /b 1
)

:: 統計文件數量
for /f %%i in ('find /c /v "" ^< git_status_temp.txt') do set "total_files=%%i"
echo [INFO] 檢測到 !total_files! 個未追蹤文件

if !total_files! gtr 10000 (
    echo [警告] 文件數量超過10K，需要特殊處理
) else (
    echo [INFO] 文件數量在可控範圍內
)

echo.
echo [步驟 2] 處理項目本體文件...

:: 添加應該提交的項目本體文件
echo [添加] 核心組件和腳本...
git add apps/backend/diagnose_components.py >nul 2>&1

:: 添加小型示例數據的README和配置文件
echo [添加] 數據配置文件...
if exist "data\README.md" git add data/README.md >nul 2>&1
if exist "data\TRAINING_DATA_GUIDE.md" git add data/TRAINING_DATA_GUIDE.md >nul 2>&1
if exist "data\data_config.json" git add data/data_config.json >nul 2>&1

:: 添加文檔和配置文件
echo [添加] 文檔和配置...
git add *.md >nul 2>&1
git add *.bat >nul 2>&1
git add .gitignore >nul 2>&1

echo.
echo [步驟 3] 排除大型數據集...

:: 安全地確保.gitignore生效
echo [INFO] 安全更新.gitignore排除規則...
:: 只對大型數據目錄執行緩存清理
if exist "data\common_voice_zh" (
    echo [清理] 移除Common Voice數據緩存...
    git rm -r --cached data/common_voice_zh >nul 2>&1
)
if exist "data\visual_genome_sample" (
    echo [清理] 移除Visual Genome數據緩存...
    git rm -r --cached data/visual_genome_sample >nul 2>&1
)
if exist "data\coco_captions" (
    echo [清理] 移除COCO數據緩存...
    git rm -r --cached data/coco_captions >nul 2>&1
)
if exist "data\flickr30k_sample" (
    echo [清理] 移除Flickr30K數據緩存...
    git rm -r --cached data/flickr30k_sample >nul 2>&1
)
:: 重新添加項目文件
echo [添加] 重新添加項目核心文件...
git add . >nul 2>&1

echo.
echo [步驟 4] 檢查清理後狀態...
git status --porcelain > git_status_after.txt
for /f %%i in ('find /c /v "" ^< git_status_after.txt') do set "remaining_files=%%i"

echo [結果] 清理前: !total_files! 個文件
echo [結果] 清理後: !remaining_files! 個文件

if !remaining_files! lss 100 (
    echo [成功] 文件數量已控制在合理範圍內
    echo.
    echo [提交] 準備提交項目本體文件...
    
    set /p "commit_msg=請輸入提交訊息 (回車使用默認): "
    if "!commit_msg!"=="" set "commit_msg=整合批處理腳本系統並清理大型數據集"
    
    git commit -m "!commit_msg!"
    if !errorlevel! equ 0 (
        echo [成功] 提交完成
        echo.
        echo [推送] 推送到遠程倉庫...
        echo [INFO] 推送到分支: !current_branch!
        git push origin "!current_branch!"
        if !errorlevel! equ 0 (
            echo [成功] 推送完成到分支 !current_branch!
        ) else (
            echo [警告] 推送失敗，請檢查網絡連接或權限
            echo [恢復] 可以使用備份分支恢復: git checkout !backup_branch!
        )
    ) else (
        echo [INFO] 沒有新的變更需要提交
    )
) else (
    echo [警告] 仍有 !remaining_files! 個文件，可能需要手動處理
    echo.
    echo [建議] 檢查以下文件：
    type git_status_after.txt | findstr /v "^$"
)

:: 清理臨時文件
del git_status_temp.txt >nul 2>&1
del git_status_after.txt >nul 2>&1
del pending_changes.txt >nul 2>&1

echo.
echo ==========================================
echo    10K+ 問題解決完成
echo ==========================================
echo.
echo [摘要] 處理完成，大型數據集已排除，項目本體已提交
echo [數據] Common Voice (57GB)、Visual Genome (18GB)、MS COCO (1GB) 已忽略
echo [狀態] Git倉庫已清理，準備好用於開發
echo [備份] 如需恢復，使用: git checkout !backup_branch!
echo [清理] 如不需要備份，可刪除: git branch -d !backup_branch!
echo.

pause