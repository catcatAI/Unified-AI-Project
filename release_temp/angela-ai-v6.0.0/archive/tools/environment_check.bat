@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Environment Check

echo ==========================================
echo   Unified AI Project 环境检查工具
echo ==========================================
echo.

cd /d "%~dp0.."

echo 正在检查开发环境...
echo.

python tools\environment_check.py

if %errorlevel% equ 0 (
    echo.
    echo 🎉 环境检查完成，所有检查通过！
) else (
    echo.
    echo ⚠️ 环境检查完成，但存在一些问题。
    echo 请查看上面的警告和错误信息。
)

echo.
echo 按任意键退出...
pause >nul