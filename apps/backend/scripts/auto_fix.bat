@echo off
REM Unified AI Project 自动修复脚本
REM 用于Windows环境下的快速修复

title Unified AI Project 自动修复工具

echo ========================================
echo Unified AI Project 自动修复工具
echo ========================================
echo.

REM 检查是否在项目根目录
if not exist "package.json" (
    echo 错误: 请在项目根目录运行此脚本
    echo 当前目录: %CD%
    pause
    exit /b 1
)

REM 检查虚拟环境
if not exist "apps\backend\venv" (
    echo 警告: 未找到虚拟环境，正在创建...
    cd apps\backend
    python -m venv venv
    if errorlevel 1 (
        echo 错误: 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo 虚拟环境创建完成
    cd ..\..
)

REM 激活虚拟环境
echo 激活虚拟环境...
cd apps\backend
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo 错误: 激活虚拟环境失败
    pause
    exit /b 1
)

echo 虚拟环境已激活
echo.

REM 显示菜单
:menu
echo 请选择操作:
echo 1. 简化版自动修复
echo 2. 完整版自动修复
echo 3. 增强版自动修复
echo 4. 增强版自动修复 + 测试
echo 5. 最终验证
echo 6. 自动修复 + 验证
echo 7. 退出
echo.

choice /c 1234567 /m "请选择操作"
echo.

if errorlevel 7 goto exit
if errorlevel 6 goto fix_and_validate
if errorlevel 5 goto validate
if errorlevel 4 goto advanced_test
if errorlevel 3 goto advanced
if errorlevel 2 goto complete
if errorlevel 1 goto simple

:simple
echo 运行简化版自动修复...
python tools\tools\scripts\simple_auto_fix.py
if errorlevel 1 (
    echo 修复过程中出现错误
) else (
    echo 简化版修复完成
)
goto menu

:complete
echo 运行完整版自动修复...
python tools\tools\scripts\auto_fix_complete.py
if errorlevel 1 (
    echo 修复过程中出现错误
) else (
    echo 完整版修复完成
)
goto menu

:advanced
echo 运行增强版自动修复...
python tools\tools\scripts\advanced_auto_fix.py
if errorlevel 1 (
    echo 修复过程中出现错误
) else (
    echo 增强版修复完成
)
goto menu

:advanced_test
echo 运行增强版自动修复 + 测试...
python tools\tools\scripts\advanced_auto_fix.py --test
if errorlevel 1 (
    echo 修复或测试过程中出现错误
) else (
    echo 增强版修复 + 测试完成
)
goto menu

:validate
echo 运行最终验证...
python tools\tools\scripts\final_validation.py
if errorlevel 1 (
    echo 验证过程中发现错误
) else (
    echo 验证完成，所有测试通过
)
goto menu

:fix_and_validate
echo 运行自动修复 + 验证...
python tools\tools\scripts\advanced_auto_fix.py --test
if errorlevel 1 (
    echo 修复过程中出现错误
) else (
    echo 自动修复完成
    echo.
    echo 运行最终验证...
    python tools\tools\scripts\final_validation.py
    if errorlevel 1 (
        echo 验证过程中发现错误
    ) else (
        echo 验证完成，所有测试通过
    )
)
goto menu

:exit
echo 感谢使用Unified AI Project自动修复工具！
cd ..\..
pause
exit /b 0