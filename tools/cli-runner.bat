@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - CLI Runner
color 0E

:: Add error handling and logging (添加錯誤處理和日志記錄)
set "LOG_FILE=%~dp0cli-runner-errors.log"
set "SCRIPT_NAME=cli-runner.bat"

:: Log script start (記錄腳本啟動)
echo [%date% %time%] Script started: %SCRIPT_NAME% >> "%LOG_FILE%" 2>nul

echo ==========================================
echo   🤖 Unified AI Project - CLI Runner
echo ==========================================
echo.
echo Run CLI commands for the Unified AI Project. (運行Unified AI Project的CLI命令)
echo.
echo Available commands: (可用命令)
echo.
echo   setup     - Setup development environment (設置開發環境)
echo   start     - Start development servers (啟動開發服務器)
echo   test      - Run tests (運行測試)
echo   train     - Setup training environment (設置訓練環境)
echo   health    - Run health check (運行健康檢查)
echo   clean     - Clean git status (清理git狀態)
echo   logs      - View error logs (查看錯誤日志)
echo   fix       - Fix dependencies (修復依賴)
echo   venv      - Recreate virtual environment (重新創建虛擬環境)
echo   emergency - Emergency git fix (緊急git修復)
echo.
echo Usage: cli-runner.bat [command] [options] (用法: cli-runner.bat [命令] [選項])
echo.

:: Check if a command is provided (檢查是否提供了命令)
if "%1"=="" (
    echo [ERROR] No command provided (未提供命令)
    echo [%date% %time%] No command provided >> "%LOG_FILE%" 2>nul
    echo.
    echo Use 'cli-runner.bat help' for available commands (使用'cli-runner.bat help'查看可用命令)
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

:: Process commands (處理命令)
echo [INFO] Running command: %1 (運行命令: %1)
echo [%date% %time%] Running command: %1 >> "%LOG_FILE%" 2>nul

if "%1"=="setup" (
    if exist "ai-runner.bat" (
        call ai-runner.bat setup
    ) else (
        echo [ERROR] ai-runner.bat not found (未找到ai-runner.bat)
        echo [%date% %time%] ai-runner.bat not found >> "%LOG_FILE%" 2>nul
    )
) else if "%1"=="start" (
    if exist "tools\start-dev.bat" (
        call tools\start-dev.bat
    ) else (
        echo [ERROR] start-dev.bat not found (未找到start-dev.bat)
        echo [%date% %time%] start-dev.bat not found >> "%LOG_FILE%" 2>nul
    )
) else if "%1"=="test" (
    if exist "tools\run-tests.bat" (
        call tools\run-tests.bat
    ) else (
        echo [ERROR] run-tests.bat not found (未找到run-tests.bat)
        echo [%date% %time%] run-tests.bat not found >> "%LOG_FILE%" 2>nul
    )
) else if "%1"=="train" (
    if exist "setup-training.bat" (
        call setup-training.bat
    ) else (
        echo [ERROR] setup-training.bat not found (未找到setup-training.bat)
        echo [%date% %time%] setup-training.bat not found >> "%LOG_FILE%" 2>nul
    )
) else if "%1"=="health" (
    if exist "tools\health-check.bat" (
        call tools\health-check.bat
    ) else (
        echo [ERROR] health-check.bat not found (未找到health-check.bat)
        echo [%date% %time%] health-check.bat not found >> "%LOG_FILE%" 2>nul
    )
) else if "%1"=="clean" (
    if exist "tools\safe-git-cleanup.bat" (
        call tools\safe-git-cleanup.bat
    ) else (
        echo [ERROR] safe-git-cleanup.bat not found (未找到safe-git-cleanup.bat)
        echo [%date% %time%] safe-git-cleanup.bat not found >> "%LOG_FILE%" 2>nul
    )
) else if "%1"=="logs" (
    if exist "tools\view-error-logs.bat" (
        call tools\view-error-logs.bat
    ) else (
        echo [ERROR] view-error-logs.bat not found (未找到view-error-logs.bat)
        echo [%date% %time%] view-error-logs.bat not found >> "%LOG_FILE%" 2>nul
    )
) else if "%1"=="fix" (
    if exist "tools\fix-dependencies.bat" (
        call tools\fix-dependencies.bat
    ) else (
        echo [ERROR] fix-dependencies.bat not found (未找到fix-dependencies.bat)
        echo [%date% %time%] fix-dependencies.bat not found >> "%LOG_FILE%" 2>nul
    )
) else if "%1"=="venv" (
    if exist "tools\recreate-venv.bat" (
        call tools\recreate-venv.bat
    ) else (
        echo [ERROR] recreate-venv.bat not found (未找到recreate-venv.bat)
        echo [%date% %time%] recreate-venv.bat not found >> "%LOG_FILE%" 2>nul
    )
) else if "%1"=="emergency" (
    if exist "tools\emergency-git-fix.bat" (
        call tools\emergency-git-fix.bat
    ) else (
        echo [ERROR] emergency-git-fix.bat not found (未找到emergency-git-fix.bat)
        echo [%date% %time%] emergency-git-fix.bat not found >> "%LOG_FILE%" 2>nul
    )
) else if "%1"=="help" (
    echo Available commands: (可用命令)
    echo   setup     - Setup development environment (設置開發環境)
    echo   start     - Start development servers (啟動開發服務器)
    echo   test      - Run tests (運行測試)
    echo   train     - Setup training environment (設置訓練環境)
    echo   health    - Run health check (運行健康檢查)
    echo   clean     - Clean git status (清理git狀態)
    echo   logs      - View error logs (查看錯誤日志)
    echo   fix       - Fix dependencies (修復依賴)
    echo   venv      - Recreate virtual environment (重新創建虛擬環境)
    echo   emergency - Emergency git fix (緊急git修復)
    echo   help      - Show this help message (顯示此幫助消息)
) else (
    echo [ERROR] Unknown command '%1' (未知命令'%1')
    echo [%date% %time%] Unknown command: %1 >> "%LOG_FILE%" 2>nul
    echo.
    echo Use 'cli-runner.bat help' for available commands (使用'cli-runner.bat help'查看可用命令)
)

echo.
echo [%date% %time%] Command %1 completed >> "%LOG_FILE%" 2>nul
echo.
echo Press any key to exit...
pause >nul
exit /b 0