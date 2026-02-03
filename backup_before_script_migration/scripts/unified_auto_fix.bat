@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 统一自动修复工具批处理脚本
:: 支持四种操作模式和范围执行

echo ========================================
echo   Unified AI Project 统一自动修复工具
echo ========================================
echo.

:: 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python环境，请确保Python已安装并添加到PATH
    pause
    exit /b 1
)

:: 设置项目根目录
set PROJECT_ROOT=%~dp0..
set SCRIPT_PATH=%~dp0unified_auto_fix.py

:: 检查脚本是否存在
if not exist "%SCRIPT_PATH%" (
    echo [错误] 未找到统一自动修复脚本: %SCRIPT_PATH%
    pause
    exit /b 1
)

:: 显示操作模式菜单
:show_mode_menu
echo 请选择操作模式:
echo 1. 單純測試 (pure_test) - 仅运行测试，不执行修复
echo 2. 測試後自動修復 (test_then_fix) - 先运行测试，如果失败则执行修复
echo 3. 單純自動修復 (pure_fix) - 仅执行修复，不运行测试
echo 4. 自動修復後自動測試 (fix_then_test) - 先执行修复，然后运行测试
echo.
set /p mode_choice="请输入选择 (1-4): "

:: 验证模式选择
if "%mode_choice%"=="1" set OPERATION_MODE=pure_test
if "%mode_choice%"=="2" set OPERATION_MODE=test_then_fix
if "%mode_choice%"=="3" set OPERATION_MODE=pure_fix
if "%mode_choice%"=="4" set OPERATION_MODE=fix_then_test

if not defined OPERATION_MODE (
    echo [错误] 无效的选择，请重新输入
    echo.
    goto show_mode_menu
)

:: 显示执行范围菜单
:show_scope_menu
echo.
echo 请选择执行范围:
echo 1. 整个项目 (project_wide) - 对整个项目执行操作
echo 2. 仅后端 (backend_only) - 仅对后端代码执行操作
echo 3. 仅前端 (frontend_only) - 仅对前端代码执行操作
echo 4. 特定模块 (specific_module) - 对指定模块执行操作
echo 5. 特定测试 (specific_test) - 对指定测试文件执行操作
echo.
set /p scope_choice="请输入选择 (1-5): "

:: 验证范围选择
if "%scope_choice%"=="1" (
    set EXECUTION_SCOPE=project_wide
    set SPECIFIC_TARGET=
)
if "%scope_choice%"=="2" (
    set EXECUTION_SCOPE=backend_only
    set SPECIFIC_TARGET=
)
if "%scope_choice%"=="3" (
    set EXECUTION_SCOPE=frontend_only
    set SPECIFIC_TARGET=
)
if "%scope_choice%"=="4" (
    set EXECUTION_SCOPE=specific_module
    set /p SPECIFIC_TARGET="请输入模块名称 (例如: agents, hsp, tools): "
)
if "%scope_choice%"=="5" (
    set EXECUTION_SCOPE=specific_test
    set /p SPECIFIC_TARGET="请输入测试文件路径 (例如: tests/test_example.py): "
)

if not defined EXECUTION_SCOPE (
    echo [错误] 无效的选择，请重新输入
    echo.
    goto show_scope_menu
)

:: 询问是否保存报告
:ask_report
echo.
set /p save_report="是否保存执行报告? (Y/n): "
if /i "%save_report%"=="n" set REPORT_OPTION=
if /i "%save_report%"=="y" set REPORT_OPTION=--report unified_auto_fix_report_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.json
if not defined save_report set REPORT_OPTION=--report unified_auto_fix_report_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.json

:: 构建命令
set COMMAND=python "%SCRIPT_PATH%" %OPERATION_MODE% %EXECUTION_SCOPE%
if defined SPECIFIC_TARGET set COMMAND=%COMMAND% --target "%SPECIFIC_TARGET%"
if defined REPORT_OPTION set COMMAND=%COMMAND% %REPORT_OPTION%

:: 显示执行信息
echo.
echo ========================================
echo   执行配置
echo ========================================
echo 操作模式: %OPERATION_MODE%
echo 执行范围: %EXECUTION_SCOPE%
if defined SPECIFIC_TARGET echo 特定目标: %SPECIFIC_TARGET%
if defined REPORT_OPTION echo 报告文件: %REPORT_OPTION:--report =%
echo ========================================
echo.

:: 确认执行
set /p confirm="确认执行? (Y/n): "
if /i "%confirm%"=="n" (
    echo 操作已取消
    pause
    exit /b 0
)

:: 执行命令
echo 正在执行...
echo 命令: %COMMAND%
echo.
cd /d "%PROJECT_ROOT%"
%COMMAND%

:: 显示结果
if errorlevel 1 (
    echo.
    echo [结果] 执行失败
) else (
    echo.
    echo [结果] 执行成功
)

:: 暂停
echo.
pause