@echo off
echo ==========================================
echo   Unified Auto-Fix System
echo ==========================================
echo.

REM 设置Python路径
set "PYTHON_CMD=python"

REM 检查Python是否可用
%PYTHON_CMD% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: Python未安装或不在PATH中
    echo 请安装Python 3.8+并确保其在PATH中
    pause
    exit /b 1
)

REM 运行统一修复系统
%PYTHON_CMD% "%~dp0unified-fix.py" %*

REM 检查返回码
if %errorlevel% neq 0 (
    echo.
    echo 统一修复系统执行失败
    pause
    exit /b %errorlevel%
)

exit /b 0