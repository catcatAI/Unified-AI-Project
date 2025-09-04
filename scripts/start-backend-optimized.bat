@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

:: 优化的后端服务启动脚本
:: 使用并行启动和资源监控提升性能

echo === 启动优化的后端服务 ===

:: 激活虚拟环境
cd /d "%~dp0..\apps\backend"
call venv\Scripts\activate.bat

:: 并行启动服务
echo 并行启动后端服务...

:: 启动ChromaDB服务器（在后台）
start "ChromaDB Server" /min cmd /c "python start_chroma_server.py"

:: 等待ChromaDB启动
timeout /t 3 /nobreak >nul

:: 启动API服务器
echo 启动API服务器...
uvicorn src.services.main_api_server:app --reload --host 0.0.0.0 --port 8000

:: 停止服务时的清理工作
:cleanup
call venv\Scripts\deactivate.bat
cd ..\..
exit /b 0