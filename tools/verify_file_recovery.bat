@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ================================
echo Unified-AI-Project 文件恢复验证脚本
echo ================================
echo.

set error_count=0

:: 检查根目录下的批处理文件
echo 检查根目录下的批处理文件...
echo.

set batch_files=ai-runner.bat comprehensive-test.bat health-check.bat quick-dev.bat run-script-tests.bat run-tests.bat safe-git-cleanup.bat setup-training.bat start-dev.bat syntax-check.bat test-all-scripts.bat test-runner.bat unified-ai.bat

for %%f in (%batch_files%) do (
    if exist "%%f" (
        for %%A in ("%%f") do set size=%%~zA
        if !size! GTR 100 (
            echo [✓] %%f - 大小: !size! 字节
        ) else (
            echo [✗] %%f - 文件过小 (!size! 字节)
            set /a error_count+=1
        )
    ) else (
        echo [✗] %%f - 文件不存在
        set /a error_count+=1
    )
)

echo.
echo 检查 scripts 目录下的批处理文件...
echo.

set script_files=scripts\dev.bat scripts\run_backend_tests.bat scripts\setup_env.bat

for %%f in (%script_files%) do (
    if exist "%%f" (
        for %%A in ("%%f") do set size=%%~zA
        if !size! GTR 100 (
            echo [✓] %%f - 大小: !size! 字节
        ) else (
            echo [✗] %%f - 文件过小 (!size! 字节)
            set /a error_count+=1
        )
    ) else (
        echo [✗] %%f - 文件不存在
        set /a error_count+=1
    )
)

echo.
echo ================================
if %error_count% == 0 (
    echo 所有文件均已成功恢复！
    echo ================================
    echo.
    echo 验证完成：所有批处理文件都已正确恢复且大小正常。
) else (
    echo 发现 %error_count% 个问题需要处理。
    echo ================================
    echo.
    echo 请检查上述标记为 [✗] 的文件并手动修复。
)

echo.
pause