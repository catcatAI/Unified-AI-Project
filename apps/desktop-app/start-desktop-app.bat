@echo off
echo 🖥️ 启动统一AI桌面应用...
echo.

cd /d "%~dp0"

echo 📦 安装依赖...
call pnpm install

echo.
echo 🚀 启动开发服务器...
call pnpm dev

pause