@echo off
setlocal enabledelayedexpansion
title Unified AI Project - CLI

:: Set project path
set "PROJECT_ROOT=%~dp0"
set "CLI_PATH=%PROJECT_ROOT%cli\main.py"

:: Check if Python is installed
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not installed
    echo [INFO] Please download from: https://python.org/
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

:: Check if click library is installed
python -c "import click" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing required dependencies...
    pip install click >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Failed to install required dependencies
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
)

:: Run CLI
python "%CLI_PATH%" %*

:end_script
endlocal