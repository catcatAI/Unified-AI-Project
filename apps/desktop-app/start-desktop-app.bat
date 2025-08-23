@echo off
chcp 65001 >nul 2>&1
echo [INFO] Starting Unified AI Desktop Application...
echo.

cd /d "%~dp0"

echo [INFO] Installing dependencies...
call pnpm install

echo.
echo [INFO] Starting development server...
call pnpm dev

pause