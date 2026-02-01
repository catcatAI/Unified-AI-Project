@echo off
REM Unified AI Project - WSL2 Backend Launcher for Windows
REM This script starts the full backend in WSL2 with all issues fixed

echo ========================================
echo Unified AI Project - WSL2 Backend Launcher
echo ========================================
echo.

REM Set environment variable to force Non-Ray mode (fixes actor issues)
set UNIFIED_AI_NONRAY=true

REM Navigate to project
cd /d %~dp0
cd ..

echo [1/4] Setting environment variables...
echo    UNIFIED_AI_NONRAY=true

echo.
echo [2/4] Starting WSL2 backend...
echo    This will take a few moments to initialize...
echo.

REM Run the backend in WSL2
wsl -e bash -c "cd /mnt/d/Projects/Unified-AI-Project && export UNIFIED_AI_NONRAY=true && source myenv/bin/activate && cd apps/backend && python main.py"

echo.
echo ========================================
echo Backend stopped
echo ========================================
