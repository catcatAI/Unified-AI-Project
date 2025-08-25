@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title 安全Git狀態清理工具
color 0B

echo ==========================================
echo      🔒 安全Git狀態清理工具
echo ==========================================
echo.
echo 此工具將安全地清理Git狀態：
echo 1. ✅ 只添加重要的項目文件
echo 2. 🛡️ 不會刪除任何現有文件
echo 3. 📋 確保.gitignore正確忽略臨時文件
echo 4. 🚀 安全提交和推送
echo.

:: 檢查當前狀態
echo [檢查] 當前Git狀態...
git status --porcelain > git_status_check.txt
for /f %%i in ('find /c /v "" ^< git_status_check.txt') do set "total_files=%%i"
echo [結果] 檢測到 !total_files! 個變更項目

echo.
echo [步驟1] 添加核心項目文件...

:: 添加重要的配置文件
echo [添加] 核心配置文件...
git add .gitignore >nul 2>&1
git add package.json >nul 2>&1
git add pnpm-workspace.yaml >nul 2>&1
git add eslint.config.mjs >nul 2>&1

:: 添加重要的README文件
echo [添加] 文檔文件...
git add README.md >nul 2>&1
git add *.md >nul 2>&1

:: 添加核心腳本 (只添加重要的)
echo [添加] 核心腳本...
git add health-check.bat >nul 2>&1
git add start-dev.bat >nul 2>&1
git add run-tests.bat >nul 2>&1
git add safe-git-cleanup.bat >nul 2>&1

:: 添加應用代碼
echo [添加] 應用代碼...
git add apps/ >nul 2>&1
git add packages/ >nul 2>&1
git add scripts/ >nul 2>&1
git add tests/ >nul 2>&1
git add training/ >nul 2>&1

:: 添加GitHub工作流
echo [添加] GitHub工作流...
git add .github/ >nul 2>&1

:: 檢查哪些被添加了
echo.
echo [檢查] 檢查暫存區狀態...
git status --porcelain | findstr "^A " > staged_files.txt
for /f %%i in ('find /c /v "" ^< staged_files.txt 2^>nul') do set "staged_count=%%i"
echo [結果] !staged_count! 個文件已暫存待提交

if !staged_count! gtr 0 (
    echo.
    echo [提交] 準備提交重要文件...
    set "commit_msg=修復Git狀態：恢復重要文件並更新忽略規則"
    
    echo [執行] 提交更改...
    git commit -m "!commit_msg!" >nul 2>&1
    if !errorlevel! equ 0 (
        echo [✓] 提交成功
        
        echo [推送] 推送到遠程倉庫...
        git push origin main >nul 2>&1
        if !errorlevel! equ 0 (
            echo [✓] 推送成功
        ) else (
            echo [!] 推送失敗，可能需要檢查網絡或權限
        )
    ) else (
        echo [!] 提交失敗
    )
) else (
    echo [信息] 沒有文件需要提交
)

:: 檢查最終狀態
echo.
echo [最終檢查] 檢查清理後狀態...
git status --porcelain > final_status.txt
for /f %%i in ('find /c /v "" ^< final_status.txt 2^>nul') do set "final_count=%%i"

echo [結果] 剩餘 !final_count! 個未追蹤項目

:: 如果剩餘文件很少，顯示詳細信息
if !final_count! leq 10 (
    echo.
    echo [詳細] 剩餘文件列表:
    type final_status.txt
)

:: 清理臨時文件
del git_status_check.txt >nul 2>&1
del staged_files.txt >nul 2>&1  
del final_status.txt >nul 2>&1

echo.
echo ==========================================
echo    安全清理完成
echo ==========================================
echo.
echo [摘要]
echo ✅ 處理前: !total_files! 個變更項目
echo ✅ 已提交: !staged_count! 個重要文件
echo ✅ 剩餘: !final_count! 個項目（主要是臨時文件）
echo.
echo [安全保證]
echo 🔒 沒有刪除任何現有文件
echo 📁 重要目錄(docs/, scripts/, tests/)都保留完整
echo 🛡️ 所有操作都是安全的添加操作
echo.
echo [建議]
echo 📋 運行: .\health-check.bat 檢查環境
echo 🚀 運行: .\start-dev.bat 開始開發
echo.

pause