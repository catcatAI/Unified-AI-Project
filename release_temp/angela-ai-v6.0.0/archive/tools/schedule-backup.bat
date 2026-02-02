@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Schedule Backup
color 0D

:: Schedule backup script for Unified AI Project
:: 定期备份计划脚本

echo ==========================================
echo   ⏰ Unified AI Project - Schedule Backup
echo ==========================================
echo.

:: Check if running as administrator
net session >nul 2>&1
if !errorlevel! neq 0 (
    echo [WARNING] This script may need to run as Administrator for scheduling tasks
    echo [WARNING] 此腳本可能需要以管理員身份運行以安排任務
    echo.
)

:: Set project root
set "PROJECT_ROOT=%~dp0.."
if "!PROJECT_ROOT:~-1!"=="\" set "PROJECT_ROOT=!PROJECT_ROOT:~0,-1!"

:: Set backup script path
set "BACKUP_SCRIPT=!PROJECT_ROOT!\tools\automated-backup.bat"

echo [INFO] Project Root: !PROJECT_ROOT!
echo [INFO] Backup Script: !BACKUP_SCRIPT!
echo.

:: Check if backup script exists
if not exist "!BACKUP_SCRIPT!" (
    echo [ERROR] Backup script not found: !BACKUP_SCRIPT!
    echo [ERROR] 脚本未找到: !BACKUP_SCRIPT!
    echo.
    echo Please ensure automated-backup.bat exists in the tools directory
    echo 请确保 automated-backup.bat 存在于 tools 目录中
    echo.
    pause
    exit /b 1
)

echo ==========================================
echo   Available Scheduling Options 可用的计划选项
echo ==========================================
echo.
echo 1. 📅 Daily Backup (每日备份) - Every day at 2:00 AM (每天凌晨2点)
echo 2. 📆 Weekly Backup (每周备份) - Every Sunday at 3:00 AM (每周日凌晨3点)
echo 3. 📅 Monthly Backup (每月备份) - First day of month at 4:00 AM (每月第一天凌晨4点)
echo 4. ⏰ Custom Schedule (自定义计划)
echo 5. 🗑️  Remove All Backup Schedules (删除所有备份计划)
echo 6. 📋 List Current Schedules (列出当前计划)
echo 7. ❌ Exit (退出)
echo.

:get_choice
set "choice="
set /p "choice=Enter your choice (1-7): "
if not defined choice (
    echo [ERROR] No input provided
    goto get_choice
)

set "choice=!choice: =!"
for %%i in (1 2 3 4 5 6 7) do (
    if "!choice!"=="%%i" (
        goto choice_%%i
    )
)

echo [ERROR] Invalid choice '!choice!'. Please enter a valid option.
goto get_choice

:choice_1
:: Daily backup
echo.
echo [INFO] Scheduling daily backup...
schtasks /create /tn "UnifiedAI_DailyBackup" /tr "!BACKUP_SCRIPT!" /sc daily /st 02:00 /f >nul 2>&1
if !errorlevel! equ 0 (
    echo [SUCCESS] Daily backup scheduled successfully
    echo [SUCCESS] 每日备份计划设置成功
    echo Task: UnifiedAI_DailyBackup
    echo Schedule: Daily at 02:00 AM
    echo Schedule: 每天凌晨02:00
) else (
    echo [ERROR] Failed to schedule daily backup
    echo [ERROR] 每日备份计划设置失败
)
goto end

:choice_2
:: Weekly backup
echo.
echo [INFO] Scheduling weekly backup...
schtasks /create /tn "UnifiedAI_WeeklyBackup" /tr "!BACKUP_SCRIPT!" /sc weekly /d SUN /st 03:00 /f >nul 2>&1
if !errorlevel! equ 0 (
    echo [SUCCESS] Weekly backup scheduled successfully
    echo [SUCCESS] 每周备份计划设置成功
    echo Task: UnifiedAI_WeeklyBackup
    echo Schedule: Weekly on Sunday at 03:00 AM
    echo Schedule: 每周日凌晨03:00
) else (
    echo [ERROR] Failed to schedule weekly backup
    echo [ERROR] 每周备份计划设置失败
)
goto end

:choice_3
:: Monthly backup
echo.
echo [INFO] Scheduling monthly backup...
schtasks /create /tn "UnifiedAI_MonthlyBackup" /tr "!BACKUP_SCRIPT!" /sc monthly /d 1 /st 04:00 /f >nul 2>&1
if !errorlevel! equ 0 (
    echo [SUCCESS] Monthly backup scheduled successfully
    echo [SUCCESS] 每月备份计划设置成功
    echo Task: UnifiedAI_MonthlyBackup
    echo Schedule: Monthly on 1st at 04:00 AM
    echo Schedule: 每月第一天凌晨04:00
) else (
    echo [ERROR] Failed to schedule monthly backup
    echo [ERROR] 每月备份计划设置失败
)
goto end

:choice_4
:: Custom schedule
echo.
echo [INFO] Custom schedule setup...
echo Please enter custom schedule details:
echo 请输入自定义计划详情:
echo.

set "task_name="
set /p "task_name=Task Name (任务名称): "
if not defined task_name set "task_name=UnifiedAI_CustomBackup"

set "schedule="
set /p "schedule=Schedule (计划) - Examples: daily, weekly, monthly: "
if not defined schedule set "schedule=daily"

set "time="
set /p "time=Time (时间) - Format HH:MM (格式 HH:MM): "
if not defined time set "time=02:00"

echo.
echo Creating custom schedule...
echo 创建自定义计划...

if "!schedule!"=="daily" (
    schtasks /create /tn "!task_name!" /tr "!BACKUP_SCRIPT!" /sc daily /st !time! /f >nul 2>&1
) else if "!schedule!"=="weekly" (
    set "day="
    set /p "day=Day of week (周几) - SUN, MON, TUE, WED, THU, FRI, SAT: "
    if not defined day set "day=SUN"
    schtasks /create /tn "!task_name!" /tr "!BACKUP_SCRIPT!" /sc weekly /d !day! /st !time! /f >nul 2>&1
) else if "!schedule!"=="monthly" (
    set "day="
    set /p "day=Day of month (几号) - 1-31: "
    if not defined day set "day=1"
    schtasks /create /tn "!task_name!" /tr "!BACKUP_SCRIPT!" /sc monthly /d !day! /st !time! /f >nul 2>&1
) else (
    echo [ERROR] Unsupported schedule type: !schedule!
    echo [ERROR] 不支持的计划类型: !schedule!
    goto end
)

if !errorlevel! equ 0 (
    echo [SUCCESS] Custom backup schedule created successfully
    echo [SUCCESS] 自定义备份计划创建成功
    echo Task: !task_name!
    echo Schedule: !schedule! at !time!
    echo Schedule: !schedule! 于 !time!
) else (
    echo [ERROR] Failed to create custom backup schedule
    echo [ERROR] 自定义备份计划创建失败
)
goto end

:choice_5
:: Remove all backup schedules
echo.
echo [WARNING] This will remove all Unified AI backup schedules
echo [WARNING] 这将删除所有Unified AI备份计划
set /p "confirm=Are you sure? (y/N): "
if /i not "!confirm!"=="y" (
    echo [INFO] Operation cancelled
    echo [INFO] 操作已取消
    goto end
)

echo.
echo [INFO] Removing backup schedules...
schtasks /delete /tn "UnifiedAI_DailyBackup" /f >nul 2>&1
schtasks /delete /tn "UnifiedAI_WeeklyBackup" /f >nul 2>&1
schtasks /delete /tn "UnifiedAI_MonthlyBackup" /f >nul 2>&1

:: Remove any custom tasks (pattern match)
for /f "tokens=*" %%i in ('schtasks /query /fo csv ^| findstr "UnifiedAI.*Backup" 2^>nul') do (
    for /f "tokens=1 delims=," %%j in ("%%i") do (
        set "task_name=%%j"
        :: Remove quotes
        set "task_name=!task_name:"=!"
        echo [INFO] Removing task: !task_name!
        schtasks /delete /tn "!task_name!" /f >nul 2>&1
    )
)

echo [SUCCESS] All backup schedules removed
echo [SUCCESS] 所有备份计划已删除
goto end

:choice_6
:: List current schedules
echo.
echo [INFO] Current backup schedules:
echo [INFO] 当前备份计划:
echo.
schtasks /query /fo table | findstr "UnifiedAI.*Backup" >nul 2>&1
if !errorlevel! equ 0 (
    schtasks /query /fo table | findstr "UnifiedAI.*Backup"
) else (
    echo [INFO] No Unified AI backup schedules found
    echo [INFO] 未找到Unified AI备份计划
)
goto end

:choice_7
:: Exit
echo.
echo [INFO] Exiting schedule backup setup...
echo [INFO] 退出计划备份设置...
goto end

:end
echo.
echo ==========================================
echo   Schedule Backup Setup Complete
echo   计划备份设置完成
echo ==========================================
echo.
pause