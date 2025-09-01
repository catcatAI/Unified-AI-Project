@echo off
:: Unified-AI-Project 数据处理流水线执行脚本
:: 支持单次运行和定期运行模式

setlocal enabledelayedexpansion

:: 设置项目根目录
set "PROJECT_ROOT=%~dp0.."
set "PYTHON_SCRIPT=%PROJECT_ROOT%\tools\automated_data_pipeline.py"

:: 检查Python脚本是否存在
if not exist "%PYTHON_SCRIPT%" (
    echo [ERROR] 未找到数据处理流水线脚本: %PYTHON_SCRIPT%
    echo [%date% %time%] ERROR: Pipeline script not found >> "%PROJECT_ROOT%\logs\pipeline.log" 2>nul
    pause
    exit /b 1
)

:: 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 未找到Python环境，请确保已安装Python并添加到PATH
    echo [%date% %time%] ERROR: Python not found >> "%PROJECT_ROOT%\logs\pipeline.log" 2>nul
    pause
    exit /b 1
)

:: 解析命令行参数
set "MODE=run"
set "INTERVAL=24"

:parse_args
if "%1"=="" goto args_done
if "%1"=="--schedule" (
    set "MODE=schedule"
    shift
    if not "%1"=="" set "INTERVAL=%1"
    shift
    goto parse_args
)
if "%1"=="--run" (
    set "MODE=run"
    shift
    goto parse_args
)
shift
goto parse_args

:args_done

:: 创建日志目录
set "LOG_DIR=%PROJECT_ROOT%\logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo [%date% %time%] Starting data pipeline in %MODE% mode >> "%PROJECT_ROOT%\logs\pipeline.log" 2>nul

:: 根据模式执行流水线
if "%MODE%"=="schedule" (
    echo [INFO] 启动定期数据处理流水线，间隔: %INTERVAL% 小时
    echo [INFO] 按 Ctrl+C 可以停止定期执行
    python "%PYTHON_SCRIPT%" --schedule %INTERVAL%
) else (
    echo [INFO] 执行一次性数据处理流水线
    python "%PYTHON_SCRIPT%" --run
)

:: 添加用户请求的命令（修复PowerShell兼容性问题）
echo [INFO] 执行额外的训练数据生成命令...
cd /d "%PROJECT_ROOT%"
python tools/automated_data_pipeline.py --run
if errorlevel 1 (
    echo [WARNING] 额外训练数据生成命令执行失败
    echo [%date% %time%] WARNING: Additional training data generation failed >> "%PROJECT_ROOT%\logs\pipeline.log" 2>nul
) else (
    echo [INFO] 额外训练数据生成命令执行完成
    echo [%date% %time%] INFO: Additional training data generation completed >> "%PROJECT_ROOT%\logs\pipeline.log" 2>nul
)

echo [INFO] 设置定期训练数据生成任务...
cd /d "%PROJECT_ROOT%"
python tools/automated_data_pipeline.py --schedule 24
if errorlevel 1 (
    echo [WARNING] 定期训练数据生成任务设置失败
    echo [%date% %time%] WARNING: Scheduled training data generation setup failed >> "%PROJECT_ROOT%\logs\pipeline.log" 2>nul
) else (
    echo [INFO] 定期训练数据生成任务设置完成
    echo [%date% %time%] INFO: Scheduled training data generation setup completed >> "%PROJECT_ROOT%\logs\pipeline.log" 2>nul
)

if errorlevel 1 (
    echo [ERROR] 数据处理流水线执行失败
    echo [%date% %time%] ERROR: Pipeline execution failed >> "%PROJECT_ROOT%\logs\pipeline.log" 2>nul
    pause
    exit /b 1
) else (
    echo [SUCCESS] 数据处理流水线执行完成
    echo [%date% %time%] SUCCESS: Pipeline execution completed >> "%PROJECT_ROOT%\logs\pipeline.log" 2>nul
)

echo.
echo 按任意键返回主菜单...
pause >nul