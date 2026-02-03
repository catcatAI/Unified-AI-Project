@echo off
REM 自动更新自动修复工具脚本
REM 在完成其他任务后运行此脚本以确保自动修复工具与项目结构保持同步

echo === 自动修复工具自动更新 ===
echo.

REM 激活虚拟环境（如果存在）
if exist "..\venv\Scripts\activate.bat" (
    call ..\venv\Scripts\activate.bat
    echo 已激活虚拟环境
) else (
    echo 未找到虚拟环境，使用系统Python
)

REM 运行自动修复工具更新检查
echo 正在检查自动修复工具更新...
python check_auto_fix_updates.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✓ 自动修复工具更新检查完成
) else (
    echo.
    echo ✗ 自动修复工具更新检查失败
    exit /b 1
)

REM 运行增强版自动修复工具
echo.
echo 正在运行增强版自动修复工具...
python enhanced_auto_fix.py --all

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✓ 增强版自动修复工具运行完成
) else (
    echo.
    echo ✗ 增强版自动修复工具运行失败
    exit /b 1
)

echo.
echo === 所有操作完成 ===
pause