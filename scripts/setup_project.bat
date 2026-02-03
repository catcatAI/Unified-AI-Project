@echo off
REM Unified AI Project Windows 设置脚本

echo Unified AI Project 设置脚本
echo ================================

REM 检查是否在项目根目录
if not exist "apps\backend" (
    echo 错误: 请在项目根目录运行此脚本
    pause
    exit /b 1
)

REM 检查Python
echo 检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python。请先安装Python 3.8或更高版本。
    pause
    exit /b 1
)

REM 检查pnpm
echo 检查pnpm...
pnpm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到pnpm。请先安装pnpm: npm install -g pnpm
    pause
    exit /b 1
)

REM 运行Python设置脚本
echo 运行自动化设置...
cd apps\backend
python ..\..\tools\tools\scripts\setup_project.py
if %errorlevel% neq 0 (
    echo 错误: 自动化设置失败
    pause
    exit /b 1
)

echo.
echo 设置脚本执行完成!
echo.
echo 请按以下步骤继续:
echo 1. 检查并修改 apps\backend\.env 文件中的配置
echo 2. 运行数据库初始化: cd apps\backend ^&^& python tools\tools\scripts\init_database.py
echo 3. 启动开发服务器: pnpm dev
echo 4. 查看详细配置指南: PROJECT_CONFIGURATION_AND_SETUP_GUIDE.md
echo.
pause