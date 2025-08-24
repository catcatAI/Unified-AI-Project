@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title 批處理腳本語法檢查器
color 0F

echo ==========================================
echo    批處理腳本語法檢查器
echo ==========================================
echo.

set "total_files=0"
set "syntax_ok=0"
set "syntax_errors=0"

:: 檢查核心腳本
echo [檢查] 核心腳本語法...
echo.

set "core_scripts=health-check.bat run-tests.bat start-dev.bat quick-dev.bat test-runner.bat setup-training.bat"

for %%f in (%core_scripts%) do (
    if exist "%%f" (
        set /a "total_files+=1"
        echo 測試: %%f
        
        :: 語法檢查
        cmd /c "%%f" /?  >nul 2>&1
        set "result=!errorlevel!"
        
        :: 檢查基本結構
        findstr /m "@echo off" "%%f" >nul
        set "structure1=!errorlevel!"
        
        findstr /m "chcp 65001" "%%f" >nul
        set "structure2=!errorlevel!"
        
        if !structure1! equ 0 if !structure2! equ 0 (
            echo   ✅ 語法結構正確
            set /a "syntax_ok+=1"
        ) else (
            echo   ⚠️  結構問題
            if !structure1! neq 0 echo     - 缺少 @echo off
            if !structure2! neq 0 echo     - 缺少 UTF-8 編碼設置
            set /a "syntax_errors+=1"
        )
        
        :: 檢查行數
        for /f %%c in ('find /c /v "" ^< "%%f"') do (
            echo   📄 行數: %%c
            if %%c gtr 250 echo     ⚠️  腳本較長，考慮簡化
        )
        echo.
    ) else (
        echo ❌ 文件不存在: %%f
        set /a "syntax_errors+=1"
        echo.
    )
)

:: 檢查子目錄腳本
echo [檢查] 子目錄腳本語法...
echo.

if exist "apps\desktop-app\start-desktop-app.bat" (
    set /a "total_files+=1"
    echo 測試: apps\desktop-app\start-desktop-app.bat
    
    findstr /m "@echo off" "apps\desktop-app\start-desktop-app.bat" >nul
    set "structure1=!errorlevel!"
    
    findstr /m "chcp 65001" "apps\desktop-app\start-desktop-app.bat" >nul
    set "structure2=!errorlevel!"
    
    if !structure1! equ 0 if !structure2! equ 0 (
        echo   ✅ 語法結構正確
        set /a "syntax_ok+=1"
    ) else (
        echo   ⚠️  結構問題
        set /a "syntax_errors+=1"
    )
    echo.
)

if exist "scripts\setup_env.bat" (
    set /a "total_files+=1"
    echo 測試: scripts\setup_env.bat
    
    findstr /m "@echo off" "scripts\setup_env.bat" >nul
    set "structure1=!errorlevel!"
    
    findstr /m "chcp 65001" "scripts\setup_env.bat" >nul
    set "structure2=!errorlevel!"
    
    if !structure1! equ 0 if !structure2! equ 0 (
        echo   ✅ 語法結構正確
        set /a "syntax_ok+=1"
    ) else (
        echo   ⚠️  結構問題
        set /a "syntax_errors+=1"
    )
    echo.
)

if exist "comprehensive-test.bat" (
    set /a "total_files+=1"
    echo 測試: comprehensive-test.bat
    
    findstr /m "@echo off" "comprehensive-test.bat" >nul
    set "structure1=!errorlevel!"
    
    findstr /m "chcp 65001" "comprehensive-test.bat" >nul
    set "structure2=!errorlevel!"
    
    if !structure1! equ 0 if !structure2! equ 0 (
        echo   ✅ 語法結構正確
        set /a "syntax_ok+=1"
    ) else (
        echo   ⚠️  結構問題
        set /a "syntax_errors+=1"
    )
    echo.
)

echo ==========================================
echo    語法檢查總結
echo ==========================================
echo.
echo 總文件數: !total_files!
echo 語法正確: !syntax_ok!
echo 有問題的: !syntax_errors!
echo.

if !syntax_errors! equ 0 (
    echo ✅ 所有腳本語法檢查通過！
    echo.
    echo [建議] 所有腳本符合基本規範：
    echo - 包含 @echo off
    echo - 支持 UTF-8 編碼 (chcp 65001)
    echo - 基本結構完整
) else (
    echo ⚠️  發現 !syntax_errors! 個腳本需要改進
    echo.
    echo [建議] 確保所有腳本包含：
    echo - @echo off (開頭)
    echo - chcp 65001 ^>nul 2^>^&1 (UTF-8 支持)
    echo - setlocal enabledelayedexpansion (變量展開)
)

echo.
echo 檢查完成！
pause