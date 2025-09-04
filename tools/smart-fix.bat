@echo off
:: 智能修复批处理脚本
:: 用于执行完整的智能修复流程

setlocal enabledelayedexpansion

:: 设置项目根目录
set "PROJECT_ROOT=%~dp0.."
set "PYTHON_SCRIPT=%PROJECT_ROOT%\apps\backend\scripts\execute_smart_fix.py"

echo ================================
echo   Unified AI Project 智能修复工具
echo ================================

:: 检查Python环境
echo 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python环境，请先安装Python 3.8或更高版本
    pause
    exit /b 1
)

:: 检查虚拟环境
echo 检查虚拟环境...
if exist "%PROJECT_ROOT%\apps\backend\venv\Scripts\activate.bat" (
    echo 激活虚拟环境...
    call "%PROJECT_ROOT%\apps\backend\venv\Scripts\activate.bat"
) else (
    echo 警告: 未找到虚拟环境，将使用系统Python环境
)

:: 检查执行脚本是否存在
if not exist "%PYTHON_SCRIPT%" (
    echo 错误: 执行脚本不存在 - %PYTHON_SCRIPT%
    pause
    exit /b 1
)

:: 运行智能修复执行器
echo 开始执行智能修复流程...
echo.

python "%PYTHON_SCRIPT%"

if errorlevel 1 (
    echo.
    echo 智能修复流程执行失败
    pause
    exit /b 1
) else (
    echo.
    echo 智能修复流程执行成功完成
)

echo.
echo 按任意键退出...
pause >nul