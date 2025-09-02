@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Enhanced File Recovery
color 0A

:: Enhanced file recovery script for Unified AI Project
:: 增强的文件恢复脚本

echo ==========================================
echo   🔄 Unified AI Project - Enhanced File Recovery
echo ==========================================
echo.

:: Set project root
set "PROJECT_ROOT=%~dp0.."
if "!PROJECT_ROOT:~-1!"=="\" set "PROJECT_ROOT=!PROJECT_ROOT:~0,-1!"

:: Set backup root
set "BACKUP_ROOT=!PROJECT_ROOT!\backups"

echo [INFO] Project Root: !PROJECT_ROOT!
echo [INFO] Backup Root: !BACKUP_ROOT!
echo.

:: Check if backup directory exists
if not exist "!BACKUP_ROOT!" (
    echo [WARNING] Backup directory not found: !BACKUP_ROOT!
    echo [WARNING] 备份目录未找到: !BACKUP_ROOT!
    echo.
    echo Please ensure backups have been created using automated-backup.bat
    echo 请确保已使用 automated-backup.bat 创建备份
    echo.
    pause
    exit /b 1
)

echo ==========================================
echo   Available Recovery Options 可用的恢复选项
echo ==========================================
echo.
echo 1. 📋 List Available Backups (列出可用备份)
echo 2. 📂 Restore from Specific Backup (从特定备份恢复)
echo 3. 🕐 Restore from Latest Backup (从最新备份恢复)
echo 4. 🎯 Selective File Recovery (选择性文件恢复)
echo 5. 🧪 Recovery Verification (恢复验证)
echo 6. ❌ Exit (退出)
echo.

:get_choice
set "choice="
set /p "choice=Enter your choice (1-6): "
if not defined choice (
    echo [ERROR] No input provided
    goto get_choice
)

set "choice=!choice: =!"
for %%i in (1 2 3 4 5 6) do (
    if "!choice!"=="%%i" (
        goto choice_%%i
    )
)

echo [ERROR] Invalid choice '!choice!'. Please enter a valid option.
goto get_choice

:choice_1
:: List available backups
echo.
echo [INFO] Available backups:
echo [INFO] 可用备份:
echo.
if exist "!BACKUP_ROOT!" (
    for /f "delims=" %%i in ('dir "!BACKUP_ROOT!" /b /o-d 2^>nul') do (
        echo   - %%i
    )
) else (
    echo [INFO] No backups found
    echo [INFO] 未找到备份
)
goto end

:choice_2
:: Restore from specific backup
echo.
echo [INFO] Available backups for restoration:
echo [INFO] 可用于恢复的备份:
echo.
set "backup_count=0"
if exist "!BACKUP_ROOT!" (
    for /f "delims=" %%i in ('dir "!BACKUP_ROOT!" /b /o-d 2^>nul') do (
        set /a "backup_count+=1"
        echo   !backup_count!. %%i
        set "backup_!backup_count!=%%i"
    )
)

if !backup_count! equ 0 (
    echo [INFO] No backups found
    echo [INFO] 未找到备份
    goto end
)

echo.
set "backup_choice="
set /p "backup_choice=Select backup to restore (1-!backup_count!): "
if not defined backup_choice (
    echo [ERROR] No input provided
    goto end
)

:: Validate choice
set "valid_choice=false"
for /l %%i in (1,1,!backup_count!) do (
    if "!backup_choice!"=="%%i" (
        set "valid_choice=true"
        set "selected_backup=!backup_%%i!"
    )
)

if "!valid_choice!"=="false" (
    echo [ERROR] Invalid choice
    echo [ERROR] 无效选择
    goto end
)

echo.
echo [WARNING] This will restore all files from backup: !selected_backup!
echo [WARNING] 这将从备份 !selected_backup! 恢复所有文件!
set /p "confirm=Are you sure you want to proceed? (y/N): "
if /i not "!confirm!"=="y" (
    echo [INFO] Restoration cancelled
    echo [INFO] 恢复已取消
    goto end
)

:: Perform restoration
echo.
echo [INFO] Restoring from backup: !selected_backup!
echo [INFO] 从备份恢复: !selected_backup!

set "backup_path=!BACKUP_ROOT!\!selected_backup!"
if not exist "!backup_path!" (
    echo [ERROR] Backup path not found: !backup_path!
    echo [ERROR] 备份路径未找到: !backup_path!
    goto end
)

:: Restore files
echo [INFO] Restoring files...
xcopy "!backup_path!\*" "!PROJECT_ROOT!\" /E /I /H /Y >nul 2>&1

if !errorlevel! equ 0 (
    echo [SUCCESS] Files restored successfully from backup: !selected_backup!
    echo [SUCCESS] 文件已成功从备份 !selected_backup! 恢复!
) else (
    echo [ERROR] Failed to restore files from backup: !selected_backup!
    echo [ERROR] 从备份 !selected_backup! 恢复文件失败!
)

goto end

:choice_3
:: Restore from latest backup
echo.
echo [INFO] Finding latest backup...
set "latest_backup="
for /f "delims=" %%i in ('dir "!BACKUP_ROOT!" /b /o-d 2^>nul') do (
    set "latest_backup=%%i"
    goto found_latest
)

:found_latest
if not defined latest_backup (
    echo [ERROR] No backups found
    echo [ERROR] 未找到备份
    goto end
)

echo.
echo [WARNING] This will restore all files from the latest backup: !latest_backup!
echo [WARNING] 这将从最新备份 !latest_backup! 恢复所有文件!
set /p "confirm=Are you sure you want to proceed? (y/N): "
if /i not "!confirm!"=="y" (
    echo [INFO] Restoration cancelled
    echo [INFO] 恢复已取消
    goto end
)

:: Perform restoration
echo.
echo [INFO] Restoring from latest backup: !latest_backup!

set "backup_path=!BACKUP_ROOT!\!latest_backup!"
if not exist "!backup_path!" (
    echo [ERROR] Backup path not found: !backup_path!
    echo [ERROR] 备份路径未找到: !backup_path!
    goto end
)

:: Restore files
echo [INFO] Restoring files...
xcopy "!backup_path!\*" "!PROJECT_ROOT!\" /E /I /H /Y >nul 2>&1

if !errorlevel! equ 0 (
    echo [SUCCESS] Files restored successfully from latest backup: !latest_backup!
    echo [SUCCESS] 文件已成功从最新备份 !latest_backup! 恢复!
) else (
    echo [ERROR] Failed to restore files from latest backup: !latest_backup!
    echo [ERROR] 从最新备份 !latest_backup! 恢复文件失败!
)

goto end

:choice_4
:: Selective file recovery
echo.
echo [INFO] Selective file recovery
echo [INFO] 选择性文件恢复
echo.

:: List available backups
echo [INFO] Available backups:
set "backup_count=0"
if exist "!BACKUP_ROOT!" (
    for /f "delims=" %%i in ('dir "!BACKUP_ROOT!" /b /o-d 2^>nul') do (
        set /a "backup_count+=1"
        echo   !backup_count!. %%i
        set "backup_!backup_count!=%%i"
    )
)

if !backup_count! equ 0 (
    echo [INFO] No backups found
    echo [INFO] 未找到备份
    goto end
)

echo.
set "backup_choice="
set /p "backup_choice=Select backup to browse (1-!backup_count!): "
if not defined backup_choice (
    echo [ERROR] No input provided
    goto end
)

:: Validate choice
set "valid_choice=false"
for /l %%i in (1,1,!backup_count!) do (
    if "!backup_choice!"=="%%i" (
        set "valid_choice=true"
        set "selected_backup=!backup_%%i!"
    )
)

if "!valid_choice!"=="false" (
    echo [ERROR] Invalid choice
    echo [ERROR] 无效选择
    goto end
)

:: Browse backup contents
echo.
echo [INFO] Browsing backup: !selected_backup!
set "backup_path=!BACKUP_ROOT!\!selected_backup!"

if not exist "!backup_path!" (
    echo [ERROR] Backup path not found: !backup_path!
    goto end
)

echo.
echo Backup contents:
echo 备份内容:
echo.
dir "!backup_path!" /s /b

echo.
set "file_path="
set /p "file_path=Enter relative path of file to restore (relative to project root): "
if not defined file_path (
    echo [ERROR] No file path provided
    goto end
)

set "source_file=!backup_path!\!file_path!"
set "dest_file=!PROJECT_ROOT!\!file_path!"

if not exist "!source_file!" (
    echo [ERROR] File not found in backup: !file_path!
    echo [ERROR] 备份中未找到文件: !file_path!
    goto end
)

echo.
echo [WARNING] This will restore file: !file_path!
echo [WARNING] 这将恢复文件: !file_path!
set /p "confirm=Are you sure you want to proceed? (y/N): "
if /i not "!confirm!"=="y" (
    echo [INFO] Restoration cancelled
    echo [INFO] 恢复已取消
    goto end
)

:: Create destination directory if needed
for %%i in ("!dest_file!") do (
    mkdir "%%~dpi" 2>nul
)

:: Restore file
copy "!source_file!" "!dest_file!" >nul 2>&1

if !errorlevel! equ 0 (
    echo [SUCCESS] File restored successfully: !file_path!
    echo [SUCCESS] 文件已成功恢复: !file_path!
) else (
    echo [ERROR] Failed to restore file: !file_path!
    echo [ERROR] 恢复文件失败: !file_path!
)

goto end

:choice_5
:: Recovery verification
echo.
echo [INFO] Recovery verification
echo [INFO] 恢复验证
echo.

:: Check if project structure is intact
echo [INFO] Checking project structure...
set "critical_dirs=apps packages tools scripts training"
set "missing_dirs=0"

for %%d in (!critical_dirs!) do (
    if not exist "!PROJECT_ROOT!\%%d" (
        echo [WARNING] Critical directory missing: %%d
        set /a "missing_dirs+=1"
    )
)

if !missing_dirs! equ 0 (
    echo [SUCCESS] All critical directories present
    echo [SUCCESS] 所有关键目录都存在
) else (
    echo [WARNING] !missing_dirs! critical directories missing
    echo [WARNING] 缺少 !missing_dirs! 个关键目录
)

:: Check critical files
echo.
echo [INFO] Checking critical files...
set "critical_files=package.json pnpm-workspace.yaml README.md"
set "missing_files=0"

for %%f in (!critical_files!) do (
    if not exist "!PROJECT_ROOT!\%%f" (
        echo [WARNING] Critical file missing: %%f
        set /a "missing_files+=1"
    )
)

if !missing_files! equ 0 (
    echo [SUCCESS] All critical files present
    echo [SUCCESS] 所有关键文件都存在
) else (
    echo [WARNING] !missing_files! critical files missing
    echo [WARNING] 缺少 !missing_files! 个关键文件
)

:: Check Git repository
echo.
echo [INFO] Checking Git repository...
if exist "!PROJECT_ROOT!\.git" (
    echo [SUCCESS] Git repository present
    echo [SUCCESS] Git仓库存在
) else (
    echo [WARNING] Git repository not found
    echo [WARNING] 未找到Git仓库
)

echo.
echo [INFO] Recovery verification complete
echo [INFO] 恢复验证完成
goto end

:choice_6
:: Exit
echo.
echo [INFO] Exiting enhanced file recovery...
echo [INFO] 退出增强文件恢复...
goto end

:end
echo.
echo ==========================================
echo   Enhanced File Recovery Complete
echo   增强文件恢复完成
echo ==========================================
echo.
pause