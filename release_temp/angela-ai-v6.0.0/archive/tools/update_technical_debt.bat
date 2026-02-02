@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - 技术债务更新工具
color 0A

:: 添加错误处理和日志记录
set "LOG_FILE=%~dp0update_technical_debt_errors.log"
set "SCRIPT_NAME=update_technical_debt.bat"

:: 记录脚本启动
echo [%date% %time%] Script started: %SCRIPT_NAME% >> "%LOG_FILE%" 2>nul

:: 使用绝对路径派生自脚本位置
set "PROJECT_ROOT=%~dp0.."
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

:main_menu
cls
echo ==========================================
echo   🔄 Unified AI Project - 技术债务更新工具
echo ==========================================
echo.
echo 管理项目技术债务
echo.
echo 请选择操作:
echo.
echo   1. 📋 查看技术债务报告
echo   2. ➕ 添加新的技术债务
echo   3. 📝 更新技术债务状态
echo   4. 🔍 查看特定技术债务详情
echo   5. 📊 按优先级筛选技术债务
echo   6. 📊 按类型筛选技术债务
echo   7. 🔍 扫描代码库中的技术债务指示器
echo   8. 🗑️  退出
echo.
echo ==========================================
echo.

:: 获取用户选择并验证
:get_user_choice
set "main_choice="
set /p "main_choice=请输入您的选择 (1-8): "
if not defined main_choice (
    echo [ERROR] 未提供输入
    echo [%date% %time%] No input provided >> "%LOG_FILE%" 2>nul
    timeout /t 2 >nul
    goto get_user_choice
)

:: 验证菜单选择的数字输入
set "main_choice=%main_choice: =%"
for %%i in (1 2 3 4 5 6 7 8) do (
    if "%main_choice%"=="%%i" (
        goto choice_%%i
    )
)

echo [ERROR] 无效选择 '%main_choice%'。请输入有效选项。
echo [%date% %time%] Invalid choice: %main_choice% >> "%LOG_FILE%" 2>nul
timeout /t 2 >nul
goto get_user_choice

:choice_1
goto view_debt_report
:choice_2
goto add_new_debt
:choice_3
goto update_debt_status
:choice_4
goto view_debt_details
:choice_5
goto filter_by_priority
:choice_6
goto filter_by_type
:choice_7
goto scan_debt_indicators
:choice_8
goto exit_script

:: 查看技术债务报告
:view_debt_report
echo.
echo [INFO] 正在生成技术债务报告...
echo [%date% %time%] Generating technical debt report >> "%LOG_FILE%" 2>nul

:: 运行Python脚本生成报告
cd /d "%PROJECT_ROOT%"
python tools/technical_debt_tracker.py

if errorlevel 1 (
    echo [ERROR] 生成报告时出错
    echo [%date% %time%] Error generating report >> "%LOG_FILE%" 2>nul
) else (
    echo [INFO] 报告生成完成
    echo [%date% %time%] Report generated successfully >> "%LOG_FILE%" 2>nul
)

echo.
echo 按任意键继续...
pause >nul
goto main_menu

:: 添加新的技术债务
:add_new_debt
echo.
echo [INFO] 添加新的技术债务...
echo [%date% %time%] Adding new technical debt >> "%LOG_FILE%" 2>nul

:: 获取债务信息
set "debt_id="
set /p "debt_id=债务ID: "
if not defined debt_id (
    echo [ERROR] 债务ID不能为空
    timeout /t 2 >nul
    goto add_new_debt
)

set "debt_title="
set /p "debt_title=债务标题: "
if not defined debt_title (
    echo [ERROR] 债务标题不能为空
    timeout /t 2 >nul
    goto add_new_debt
)

set "debt_description="
set /p "debt_description=债务描述: "
if not defined debt_description (
    echo [ERROR] 债务描述不能为空
    timeout /t 2 >nul
    goto add_new_debt
)

echo.
echo 债务类型:
echo   1. 代码质量 (code_quality)
echo   2. 架构问题 (architecture)
echo   3. 性能问题 (performance)
echo   4. 安全问题 (security)
echo   5. 可维护性问题 (maintainability)
echo   6. 测试覆盖不足 (test_coverage)
echo   7. 依赖问题 (dependencies)
echo   8. 技术问题 (technical)
echo   9. 文档问题 (documentation)
echo.

set "type_choice="
set /p "type_choice=请选择债务类型 (1-9): "

:: 映射选择到类型
set "debt_type="
if "%type_choice%"=="1" set "debt_type=code_quality"
if "%type_choice%"=="2" set "debt_type=architecture"
if "%type_choice%"=="3" set "debt_type=performance"
if "%type_choice%"=="4" set "debt_type=security"
if "%type_choice%"=="5" set "debt_type=maintainability"
if "%type_choice%"=="6" set "debt_type=test_coverage"
if "%type_choice%"=="7" set "debt_type=dependencies"
if "%type_choice%"=="8" set "debt_type=technical"
if "%type_choice%"=="9" set "debt_type=documentation"

if not defined debt_type (
    echo [ERROR] 无效的债务类型选择
    timeout /t 2 >nul
    goto add_new_debt
)

echo.
echo 债务优先级:
echo   1. 低 (low)
echo   2. 中 (medium)
echo   3. 高 (high)
echo   4. 关键 (critical)
echo.

set "priority_choice="
set /p "priority_choice=请选择债务优先级 (1-4): "

:: 映射选择到优先级
set "debt_priority="
if "%priority_choice%"=="1" set "debt_priority=low"
if "%priority_choice%"=="2" set "debt_priority=medium"
if "%priority_choice%"=="3" set "debt_priority=high"
if "%priority_choice%"=="4" set "debt_priority=critical"

if not defined debt_priority (
    echo [ERROR] 无效的债务优先级选择
    timeout /t 2 >nul
    goto add_new_debt
)

set "file_path="
set /p "file_path=相关文件路径 (可选): "

set "line_number="
set /p "line_number=行号 (可选): "

set "assigned_to="
set /p "assigned_to=负责人 (可选): "

set "estimated_hours="
set /p "estimated_hours=预估工时 (小时，可选): "

:: 这里应该调用Python脚本来添加债务，但为了简化，我们显示信息
echo.
echo 债务信息摘要:
echo   ID: %debt_id%
echo   标题: %debt_title%
echo   描述: %debt_description%
echo   类型: %debt_type%
echo   优先级: %debt_priority%
echo   文件: %file_path%
echo   行号: %line_number%
echo   负责人: %assigned_to%
echo   工时: %estimated_hours%
echo.
echo 注意: 实际实现需要修改 technical_debt.json 文件
echo.

echo.
echo 按任意键继续...
pause >nul
goto main_menu

:: 更新技术债务状态
:update_debt_status
echo.
echo [INFO] 更新技术债务状态...
echo [%date% %time%] Updating technical debt status >> "%LOG_FILE%" 2>nul

:: 显示现有债务列表
echo 现有技术债务:
cd /d "%PROJECT_ROOT%"
python -c "import json; data=json.load(open('technical_debt.json')); [print(f'  {i+1}. {f[\"id\"]} - {f[\"title\"]} ({f[\"status\"]})') for i, f in enumerate(data['debts'])]"

echo.
set "debt_id="
set /p "debt_id=请输入要更新的债务ID: "

if not defined debt_id (
    echo [ERROR] 债务ID不能为空
    timeout /t 2 >nul
    goto update_debt_status
)

echo.
echo 新状态:
echo   1. 开放 (open)
echo   2. 处理中 (in_progress)
echo   3. 已解决 (resolved)
echo   4. 不修复 (wont_fix)
echo.

set "status_choice="
set /p "status_choice=请选择新状态 (1-4): "

:: 映射选择到状态
set "new_status="
if "%status_choice%"=="1" set "new_status=open"
if "%status_choice%"=="2" set "new_status=in_progress"
if "%status_choice%"=="3" set "new_status=resolved"
if "%status_choice%"=="4" set "new_status=wont_fix"

if not defined new_status (
    echo [ERROR] 无效的状态选择
    timeout /t 2 >nul
    goto update_debt_status
)

set "resolution="
if "%new_status%"=="resolved" (
    set /p "resolution=解决方案 (可选): "
)

:: 这里应该调用Python脚本来更新债务状态
echo.
echo [INFO] 正在更新技术债务状态...
echo   债务ID: %debt_id%
echo   新状态: %new_status%
echo   解决方案: %resolution%
echo.
echo 注意: 实际实现需要修改 technical_debt.json 文件
echo.

echo.
echo 按任意键继续...
pause >nul
goto main_menu

:: 查看特定技术债务详情
:view_debt_details
echo.
echo [INFO] 查看技术债务详情...
echo [%date% %time%] Viewing technical debt details >> "%LOG_FILE%" 2>nul

:: 显示现有债务列表
echo 现有技术债务:
cd /d "%PROJECT_ROOT%"
python -c "import json; data=json.load(open('technical_debt.json')); [print(f'  {i+1}. {f[\"id\"]} - {f[\"title\"]}') for i, f in enumerate(data['debts'])]"

echo.
set "debt_id="
set /p "debt_id=请输入要查看的债务ID: "

if not defined debt_id (
    echo [ERROR] 债务ID不能为空
    timeout /t 2 >nul
    goto view_debt_details
)

:: 显示债务详情
echo.
echo [INFO] 正在获取技术债务详情...
cd /d "%PROJECT_ROOT%"
python -c "import json; data=json.load(open('technical_debt.json')); f=[x for x in data['debts'] if x['id']=='%debt_id%']; print('技术债务详情:') if f else print('未找到债务'); [print(f'  ID: {x[\"id\"]}\n  标题: {x[\"title\"]}\n  描述: {x[\"description\"]}\n  类型: {x[\"debt_type\"]}\n  优先级: {x[\"priority\"]}\n  文件: {x[\"file_path\"]}\n  行号: {x[\"line_number\"]}\n  创建时间: {x[\"created_date\"]}\n  负责人: {x[\"assigned_to\"]}\n  预估工时: {x[\"estimated_hours\"]}\n  状态: {x[\"status\"]}\n  解决方案: {x[\"resolution\"]}\n  解决时间: {x[\"resolved_date\"]}') for x in f]"

echo.
echo 按任意键继续...
pause >nul
goto main_menu

:: 按优先级筛选技术债务
:filter_by_priority
echo.
echo [INFO] 按优先级筛选技术债务...
echo [%date% %time%] Filtering technical debts by priority >> "%LOG_FILE%" 2>nul

echo 可用优先级:
echo   1. 低 (low)
echo   2. 中 (medium)
echo   3. 高 (high)
echo   4. 关键 (critical)
echo.

set "priority_choice="
set /p "priority_choice=请选择优先级 (1-4): "

:: 映射选择到优先级
set "filter_priority="
if "%priority_choice%"=="1" set "filter_priority=low"
if "%priority_choice%"=="2" set "filter_priority=medium"
if "%priority_choice%"=="3" set "filter_priority=high"
if "%priority_choice%"=="4" set "filter_priority=critical"

if not defined filter_priority (
    echo [ERROR] 无效的优先级选择
    timeout /t 2 >nul
    goto filter_by_priority
)

:: 显示筛选结果
echo.
echo [PRIORITY] 优先级为 %filter_priority% 的技术债务:
cd /d "%PROJECT_ROOT%"
python -c "import json; data=json.load(open('technical_debt.json')); filtered=[f for f in data['debts'] if f['priority']=='%filter_priority%']; print(f'找到 {len(filtered)} 项债务:') if filtered else print('未找到匹配的债务'); [print(f'  - {f[\"id\"]} - {f[\"title\"]}') for f in filtered]"

echo.
echo 按任意键继续...
pause >nul
goto main_menu

:: 按类型筛选技术债务
:filter_by_type
echo.
echo [INFO] 按类型筛选技术债务...
echo [%date% %time%] Filtering technical debts by type >> "%LOG_FILE%" 2>nul

echo 可用类型:
echo   1. 代码质量 (code_quality)
echo   2. 架构问题 (architecture)
echo   3. 性能问题 (performance)
echo   4. 安全问题 (security)
echo   5. 可维护性问题 (maintainability)
echo   6. 测试覆盖不足 (test_coverage)
echo   7. 依赖问题 (dependencies)
echo   8. 技术问题 (technical)
echo   9. 文档问题 (documentation)
echo.

set "type_choice="
set /p "type_choice=请选择类型 (1-9): "

:: 映射选择到类型
set "filter_type="
if "%type_choice%"=="1" set "filter_type=code_quality"
if "%type_choice%"=="2" set "filter_type=architecture"
if "%type_choice%"=="3" set "filter_type=performance"
if "%type_choice%"=="4" set "filter_type=security"
if "%type_choice%"=="5" set "filter_type=maintainability"
if "%type_choice%"=="6" set "filter_type=test_coverage"
if "%type_choice%"=="7" set "filter_type=dependencies"
if "%type_choice%"=="8" set "filter_type=technical"
if "%type_choice%"=="9" set "filter_type=documentation"

if not defined filter_type (
    echo [ERROR] 无效的类型选择
    timeout /t 2 >nul
    goto filter_by_type
)

:: 显示筛选结果
echo.
echo [TYPE] 类型为 %filter_type% 的技术债务:
cd /d "%PROJECT_ROOT%"
python -c "import json; data=json.load(open('technical_debt.json')); filtered=[f for f in data['debts'] if f['debt_type']=='%filter_type%']; print(f'找到 {len(filtered)} 项债务:') if filtered else print('未找到匹配的债务'); [print(f'  - {f[\"id\"]} - {f[\"title\"]}') for f in filtered]"

echo.
echo 按任意键继续...
pause >nul
goto main_menu

:: 扫描代码库中的技术债务指示器
:scan_debt_indicators
echo.
echo [INFO] 扫描代码库中的技术债务指示器...
echo [%date% %time%] Scanning for technical debt indicators >> "%LOG_FILE%" 2>nul

:: 运行Python脚本扫描债务指示器
cd /d "%PROJECT_ROOT%"
python -c "from tools.technical_debt_tracker import TechnicalDebtTracker; tracker=TechnicalDebtTracker(); tracker.scan_for_debt_indicators()"

if errorlevel 1 (
    echo [ERROR] 扫描债务指示器时出错
    echo [%date% %time%] Error scanning debt indicators >> "%LOG_FILE%" 2>nul
) else (
    echo [INFO] 债务指示器扫描完成
    echo [%date% %time%] Debt indicators scan completed >> "%LOG_FILE%" 2>nul
)

echo.
echo 按任意键继续...
pause >nul
goto main_menu

:: 退出脚本
:exit_script
echo.
echo [INFO] 退出技术债务更新工具...
echo [%date% %time%] Exiting technical debt update tool >> "%LOG_FILE%" 2>nul
echo.
echo 返回主菜单...
echo.
echo 按任意键继续...
pause >nul
goto :eof