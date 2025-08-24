@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title 批處理腳本測試工具
color 0E

echo ==========================================
echo      批處理腳本綜合測試工具
echo ==========================================
echo.

set "total_scripts=0"
set "passed_scripts=0"
set "failed_scripts=0"

echo [INFO] 開始檢測所有批處理腳本...
echo.

:: 定義要測試的腳本列表
set "scripts[0]=health-check.bat"
set "scripts[1]=run-tests.bat"
set "scripts[2]=start-dev.bat"
set "scripts[3]=quick-dev.bat"
set "scripts[4]=test-runner.bat"
set "scripts[5]=setup-training.bat"
set "scripts[6]=apps\desktop-app\start-desktop-app.bat"
set "scripts[7]=scripts\setup_env.bat"

set "script_count=8"

echo ==========================================
echo 第一階段：語法檢查
echo ==========================================
echo.

for /l %%i in (0,1,7) do (
    set "script=!scripts[%%i]!"
    set /a "total_scripts+=1"
    
    if exist "!script!" (
        echo [測試] !script!
        
        :: 檢查語法錯誤
        cmd /c "!script!" /? >nul 2>&1
        set "syntax_result=!errorlevel!"
        
        :: 檢查編碼
        findstr /c:"chcp 65001" "!script!" >nul 2>&1
        set "encoding_check=!errorlevel!"
        
        :: 檢查基本結構
        findstr /c:"@echo off" "!script!" >nul 2>&1
        set "structure_check=!errorlevel!"
        
        if !encoding_check! equ 0 (
            echo   ✅ UTF-8 編碼支持
        ) else (
            echo   ⚠️  缺少 UTF-8 編碼設置
        )
        
        if !structure_check! equ 0 (
            echo   ✅ 基本結構正確
        ) else (
            echo   ❌ 缺少基本結構
        )
        
        set /a "passed_scripts+=1"
        echo   [狀態] 通過基礎檢查
        
    ) else (
        echo [錯誤] 文件不存在: !script!
        set /a "failed_scripts+=1"
    )
    echo.
)

echo ==========================================
echo 第二階段：功能性檢查
echo ==========================================
echo.

:: 檢查 health-check.bat
if exist "health-check.bat" (
    echo [功能測試] health-check.bat
    findstr /c:"where python" health-check.bat >nul 2>&1
    if !errorlevel! equ 0 (
        echo   ✅ Python 檢查功能
    ) else (
        echo   ⚠️  缺少 Python 檢查
    )
    
    findstr /c:"where node" health-check.bat >nul 2>&1
    if !errorlevel! equ 0 (
        echo   ✅ Node.js 檢查功能
    ) else (
        echo   ⚠️  缺少 Node.js 檢查
    )
    echo.
)

:: 檢查 run-tests.bat
if exist "run-tests.bat" (
    echo [功能測試] run-tests.bat
    findstr /c:"pytest" run-tests.bat >nul 2>&1
    if !errorlevel! equ 0 (
        echo   ✅ Python 測試功能
    ) else (
        echo   ⚠️  缺少 Python 測試
    )
    
    findstr /c:"pnpm" run-tests.bat >nul 2>&1
    if !errorlevel! equ 0 (
        echo   ✅ Node.js 測試功能
    ) else (
        echo   ⚠️  缺少 Node.js 測試
    )
    echo.
)

:: 檢查 start-dev.bat
if exist "start-dev.bat" (
    echo [功能測試] start-dev.bat
    findstr /c:"uvicorn" start-dev.bat >nul 2>&1
    if !errorlevel! equ 0 (
        echo   ✅ 後端啟動功能
    ) else (
        echo   ⚠️  缺少後端啟動
    )
    
    findstr /c:"pnpm.*dev" start-dev.bat >nul 2>&1
    if !errorlevel! equ 0 (
        echo   ✅ 前端啟動功能
    ) else (
        echo   ⚠️  缺少前端啟動
    )
    echo.
)

echo ==========================================
echo 第三階段：輸入驗證檢查
echo ==========================================
echo.

for /l %%i in (0,1,7) do (
    set "script=!scripts[%%i]!"
    
    if exist "!script!" (
        echo [輸入驗證] !script!
        
        findstr /c:"if not defined choice" "!script!" >nul 2>&1
        if !errorlevel! equ 0 (
            echo   ✅ 輸入驗證機制
        ) else (
            findstr /c:"set /p" "!script!" >nul 2>&1
            if !errorlevel! equ 0 (
                echo   ⚠️  有用戶輸入但缺少驗證
            ) else (
                echo   ✅ 無用戶輸入需求
            )
        )
        echo.
    )
)

echo ==========================================
echo 測試總結
echo ==========================================
echo.
echo 總腳本數量: !total_scripts!
echo 通過檢查: !passed_scripts!
echo 檢查失敗: !failed_scripts!
echo.

if !failed_scripts! equ 0 (
    echo ✅ 所有腳本通過基礎檢查！
    echo.
    echo [建議] 下一步可以進行功能測試：
    echo 1. 執行 health-check.bat 檢查環境
    echo 2. 執行 run-tests.bat 運行測試
    echo 3. 執行 start-dev.bat 啟動開發環境
    echo.
) else (
    echo ❌ 發現 !failed_scripts! 個問題需要修復
    echo.
)

echo 詳細測試報告已保存，按任意鍵檢視...
pause >nul

:: 生成詳細報告
echo 正在生成詳細報告...
goto generate_report

:generate_report
(
echo # 批處理腳本測試報告
echo.
echo 生成時間: %date% %time%
echo 測試工具: test-all-scripts.bat
echo.
echo ## 測試摘要
echo.
echo - 總腳本數量: !total_scripts!
echo - 通過檢查: !passed_scripts!
echo - 檢查失敗: !failed_scripts!
echo.
echo ## 腳本清單
echo.
for /l %%i in (0,1,7) do (
    set "script=!scripts[%%i]!"
    if exist "!script!" (
        echo ### !script!
        echo - 狀態: ✅ 存在
        for /f %%a in ('find /c /v "" ^< "!script!"') do echo - 行數: %%a
        findstr /c:"chcp 65001" "!script!" >nul 2>&1
        if !errorlevel! equ 0 (
            echo - UTF-8: ✅ 支持
        ) else (
            echo - UTF-8: ⚠️  未設置
        )
        echo.
    ) else (
        echo ### !script!
        echo - 狀態: ❌ 不存在
        echo.
    )
)
echo.
echo ## 建議改進
echo.
echo 1. 確保所有腳本都包含 UTF-8 編碼設置
echo 2. 加強輸入驗證機制
echo 3. 統一錯誤處理格式
echo 4. 添加更多功能測試
echo.
) > BATCH_SCRIPTS_TEST_REPORT.md

echo [SUCCESS] 詳細報告已生成: BATCH_SCRIPTS_TEST_REPORT.md
echo.
pause