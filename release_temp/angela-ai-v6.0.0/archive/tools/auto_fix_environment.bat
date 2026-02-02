@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Auto Fix Environment

echo ==========================================
echo   Unified AI Project 一键式环境修复工具
echo ==========================================
echo.

cd /d "%~dp0.."

echo 正在修复开发环境...
echo.

python tools\auto_fix_environment.py

if %errorlevel% equ 0 (
    echo.
    echo 🎉 环境修复完成，所有修复已应用！
) else (
    echo.
    echo ⚠️ 环境修复完成，但存在一些问题。
    echo 请查看上面的警告和错误信息。
)

echo.
echo 按任意键退出...
pause >nul