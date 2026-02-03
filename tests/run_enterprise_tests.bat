@echo off
echo 🚀 启动企业级测试套件...
cd /d "D:\Projects\Unified-AI-Project"

REM 激活虚拟环境（如果存在）
if exist "venv\Scripts\activate.bat" (
    echo 📦 激活虚拟环境...
    call venv\Scripts\activate.bat
)

REM 运行测试套件
echo 🧪 执行企业级测试...
python tests\enterprise_test_suite.py

REM 检查结果
if %ERRORLEVEL% EQU 0 (
    echo ✅ 测试套件执行成功
) else (
    echo ❌ 测试套件执行失败
)

pause