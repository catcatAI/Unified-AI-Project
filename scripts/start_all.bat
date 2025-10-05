@echo off
echo 正在启动Unified AI Project完整服务...
echo 当前目录: %cd%
echo.

echo 启动后端服务...
start "后端服务" /D "d:\Projects\Unified-AI-Project\apps\backend" python -m uvicorn src.services.main_api_server:app --host 127.0.0.1 --port 8000

timeout /t 5 /nobreak >nul

echo.
echo 启动前端服务...
cd /d "d:\Projects\Unified-AI-Project"
start "前端服务" pnpm --filter frontend-dashboard dev

echo.
echo 服务启动完成!
echo 后端API: http://localhost:8000
echo 前端界面: http://localhost:3000
echo.
echo 按任意键关闭此窗口...
pause >nul