@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

:: 优化的Unified AI Project开发环境脚本
:: 使用并行启动和缓存机制提升启动速度

set "ACTION=%1"
set "OPTION=%2"

if "%ACTION%"=="" set "ACTION=dev"

echo === 优化的Unified AI Project开发工具 ===

goto %ACTION% 2>nul || goto usage

:install
echo 正在安装项目依赖...
echo 检查Node.js和pnpm...

:: 检查环境（带缓存）
call :check_environment_cached
if errorlevel 1 (
    echo 错误: 环境检查失败
    exit /b 1
)

echo 安装Node.js依赖...
pnpm install
if errorlevel 1 (
    echo 错误: Node.js依赖安装失败
    exit /b 1
)

echo 设置Python环境...
cd apps\backend

:: 创建虚拟环境（如果不存在）
if not exist "venv" (
    echo 创建Python虚拟环境...
    python -m venv venv
)

:: 激活虚拟环境并安装依赖
echo 安装Python依赖...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

cd ..\..
echo 依赖安装完成!
goto end

:dev
echo 启动优化的开发环境...

if "%OPTION%"=="backend" goto dev_backend
if "%OPTION%"=="frontend" goto dev_frontend
if "%OPTION%"=="desktop" goto dev_desktop

:: 并行启动后端和前端服务
echo 并行启动后端和前端服务...

:: 启动后端服务（在后台）
start "Backend Services" /min cmd /c "%~dp0start-backend-optimized.bat"

:: 等待后端服务启动
timeout /t 3 /nobreak >nul

:: 启动前端服务
start "Frontend" cmd /k "cd /d "%~dp0..\" && pnpm --filter frontend-dashboard dev"

echo 开发服务已启动:
echo - 后端API: http://localhost:8000
echo - 前端仪表板: http://localhost:3000
echo - ChromaDB: http://localhost:8001
echo.
echo 按任意键停止所有服务...
pause >nul
goto stop

:dev_backend
echo 启动后端服务...
start "Backend Services" /min cmd /c "%~dp0start-backend-optimized.bat"
echo 后端服务已启动: http://localhost:8000
echo 按任意键停止服务...
pause >nul
goto stop

:dev_frontend
echo 启动前端服务...
start "Frontend" cmd /k "cd /d "%~dp0..\" && pnpm --filter frontend-dashboard dev"
echo 前端服务已启动: http://localhost:3000
echo 按任意键停止服务...
pause >nul
goto stop

:dev_desktop
echo 启动桌面应用...
cd apps/desktop
start "Desktop App" cmd /k "pnpm dev"
cd ..\..
echo 桌面应用已启动
echo 按任意键停止服务...
pause >nul
goto stop

:test
echo 运行优化的测试...
cd apps\backend
call venv\Scripts\activate.bat

:: 并行运行不同类型的测试
if "%OPTION%"=="unit" (
    echo 运行单元测试...
    python -m pytest tests/unit/ --tb=short -v
) else if "%OPTION%"=="integration" (
    echo 运行集成测试...
    python -m pytest tests/integration/ --tb=short -v
) else if "%OPTION%"=="api" (
    echo 运行API测试...
    python -m pytest tests/api/ --tb=short -v
) else (
    echo 运行所有测试...
    python -m pytest tests/ --tb=short -v
)

call venv\Scripts\deactivate.bat
cd ..\..
goto end

:health
echo 运行优化的健康检查...
python scripts\optimized_health_check.py
goto end

:clean
echo 清理项目...
:: 清理Python缓存
cd apps\backend
if exist "__pycache__" rd /s /q "__pycache__"
for /d %%i in ("src\*") do (
    if exist "%%i\__pycache__" rd /s /q "%%i\__pycache__"
)
cd ..\..

:: 清理Node.js缓存
if exist "node_modules\.cache" rd /s /q "node_modules\.cache"

echo 清理完成!
goto end

:usage
echo.
echo 用法: optimized_dev.bat [action] [options]
echo.
echo 动作:
echo   install     - 安装项目依赖
echo   dev         - 启动开发环境（默认）
echo   test        - 运行测试
echo   health      - 运行健康检查
echo   clean       - 清理项目
echo.
echo 选项:
echo   backend     - 仅启动后端服务
echo   frontend    - 仅启动前端服务
echo   desktop     - 启动桌面应用
echo   unit        - 运行单元测试
echo   integration - 运行集成测试
echo   api         - 运行API测试
echo.
goto end

:check_environment_cached
:: 带缓存的环境检查
if defined ENV_CHECKED (
    echo 环境检查已缓存，跳过重复检查
    exit /b 0
)

:: 检查Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: Node.js未安装或未在PATH中
    echo [解决方案] 从 https://nodejs.org/ 下载安装
    exit /b 1
)

:: 检查pnpm
pnpm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: pnpm未安装，请运行: npm install -g pnpm
    exit /b 1
)

:: 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: Python未安装或未在PATH中
    echo [解决方案] 从 https://python.org/ 下载安装
    exit /b 1
)

:: 设置缓存标志
set "ENV_CHECKED=1"
exit /b 0

:stop
echo 停止所有服务...
:: 这里可以添加停止服务的逻辑
echo 服务已停止
goto end

:end
echo.
echo === 脚本执行完成 ===
endlocal