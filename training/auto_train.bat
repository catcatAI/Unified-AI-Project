@echo off
REM Unified AI Project 自动训练脚本

echo 🤖 Unified AI Project 自动训练系统
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

REM 执行自动训练
echo 🚀 启动自动训练流程...
python training\run_auto_training.py --verbose

if %errorlevel% equ 0 (
    echo.
    echo ✅ 自动训练完成！
    echo 请查看 training\reports 目录中的训练报告
) else (
    echo.
    echo ❌ 自动训练失败，请检查错误信息
    pause
    exit /b 1
)

echo.
echo 按任意键退出...
pause >nul