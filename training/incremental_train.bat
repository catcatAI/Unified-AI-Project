@echo off
REM Unified AI Project 增量学习脚本

echo 🤖 Unified AI Project 增量学习系统
echo ========================================

REM 检查Python环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未找到Python环境，请先安装Python 3.8或更高版本
    pause
    exit /b 1
)

REM 进入项目根目录
cd /d "%~dp0\.."

REM 根据参数执行不同操作
if "%1"=="" (
    echo 用法:
    echo   incremental_train.bat monitor     - 启动数据监控
    echo   incremental_train.bat train       - 触发增量训练
    echo   incremental_train.bat status      - 查看系统状态
    echo   incremental_train.bat status -v   - 查看详细系统状态
    goto end
)

if "%1"=="monitor" (
    echo 👀 启动数据监控...
    python training\incremental_learning_cli.py monitor
    goto end
)

if "%1"=="train" (
    echo 🚀 触发增量训练...
    python training\incremental_learning_cli.py train
    goto end
)

if "%1"=="status" (
    if "%2"=="-v" (
        echo 📊 查看详细系统状态...
        python training\incremental_learning_cli.py status --verbose
    ) else (
        echo 📊 查看系统状态...
        python training\incremental_learning_cli.py status
    )
    goto end
)

echo ❌ 未知命令: %1
echo 请使用以下命令之一: monitor, train, status
exit /b 1

:end
echo.
echo 按任意键退出...
pause >nul