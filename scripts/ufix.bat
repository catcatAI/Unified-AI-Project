@echo off
setlocal enabledelayedexpansion

:: 简化版统一自动修复工具
:: 快速命令行接口

:: 设置项目根目录
set PROJECT_ROOT=%~dp0..
set SCRIPT_PATH=%~dp0unified_auto_fix.py

:: 检查参数
if "%~1"=="" (
    echo 用法: ufix.bat [模式] [范围] [目标]
    echo.
    echo 模式:
    echo   test    - 單純測試
    echo   tfix    - 測試後自動修復
    echo   fix     - 單純自動修復
    echo   ftest   - 自動修復後自動測試
    echo.
    echo 范围:
    echo   all     - 整个项目
    echo   back    - 仅后端
    echo   front   - 仅前端
    echo   mod     - 特定模块
    echo   test    - 特定测试
    echo.
    echo 示例:
    echo   ufix.bat test all
    echo   ufix.bat tfix back
    echo   ufix.bat fix all
    echo   ufix.bat ftest mod agents
    echo   ufix.bat test test tests\test_example.py
    pause
    exit /b 1
)

:: 解析模式
set MODE=%~1
if "%MODE%"=="test" set OPERATION_MODE=pure_test
if "%MODE%"=="tfix" set OPERATION_MODE=test_then_fix
if "%MODE%"=="fix" set OPERATION_MODE=pure_fix
if "%MODE%"=="ftest" set OPERATION_MODE=fix_then_test

if not defined OPERATION_MODE (
    echo [错误] 无效的模式: %MODE%
    pause
    exit /b 1
)

:: 解析范围
set SCOPE=%~2
if "%SCOPE%"=="all" set EXECUTION_SCOPE=project_wide
if "%SCOPE%"=="back" set EXECUTION_SCOPE=backend_only
if "%SCOPE%"=="front" set EXECUTION_SCOPE=frontend_only
if "%SCOPE%"=="mod" set EXECUTION_SCOPE=specific_module
if "%SCOPE%"=="test" set EXECUTION_SCOPE=specific_test

if not defined EXECUTION_SCOPE (
    echo [错误] 无效的范围: %SCOPE%
    pause
    exit /b 1
)

:: 解析目标
set TARGET=%~3

:: 构建命令
set COMMAND=python "%SCRIPT_PATH%" %OPERATION_MODE% %EXECUTION_SCOPE%
if defined TARGET set COMMAND=%COMMAND% --target "%TARGET%"
set COMMAND=%COMMAND% --report unified_auto_fix_quick_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.json

:: 执行命令
cd /d "%PROJECT_ROOT%"
echo 正在执行: %COMMAND%
echo.
%COMMAND%

if errorlevel 1 (
    echo.
    echo [结果] 执行失败
) else (
    echo.
    echo [结果] 执行成功
)

pause