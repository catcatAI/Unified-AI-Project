@echo off
echo 正在启动Unified AI Project后端服务...
echo 当前目录: %cd%
echo.

REM 使用相对路径，不硬编码
set "PROJECT_ROOT=%~dp0.."

cd /d "%PROJECT_ROOT%\apps\backend"
echo 切换到后端目录: %cd%
echo.

echo 启动Uvicorn服务器...
python -m uvicorn src.services.main_api_server:app --host 127.0.0.1 --port 8000

if %errorlevel% neq 0 (
    echo.
    echo 启动失败，错误代码: %errorlevel%
    echo 请确保已安装所有依赖:
    echo   cd apps/backend
    echo   pip install -r requirements.txt
    echo   pip install -r requirements-dev.txt
    echo.
    pause
)
