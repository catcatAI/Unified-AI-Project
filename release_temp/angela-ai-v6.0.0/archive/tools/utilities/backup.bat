@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Backup Manager
color 0E

:: Add error handling and logging
set "LOG_FILE=%~dp0..\logs\backup.log"
set "SCRIPT_NAME=backup.bat"

:: Log script start
echo [%date% %time%] Script started: %SCRIPT_NAME% >> "%LOG_FILE%" 2>nul

:: Create logs directory if it doesn't exist
if not exist "%~dp0..\logs" mkdir "%~dp0..\logs"

echo ==========================================
echo   Unified AI Project - Backup Manager
echo ==========================================
echo.

:: Parse command line arguments
set "BACKUP_TYPE=full"
set "COMPRESS=true"
set "INCLUDE_LOGS=false"
set "INCLUDE_NODE_MODULES=false"
set "BACKUP_NAME="

:parse_args
if "%1"=="" goto args_done
if "%1"=="--full" (
    set "BACKUP_TYPE=full"
    shift
    goto parse_args
)
if "%1"=="--incremental" (
    set "BACKUP_TYPE=incremental"
    shift
    goto parse_args
)
if "%1"=="--config" (
    set "BACKUP_TYPE=config"
    shift
    goto parse_args
)
if "%1"=="--data" (
    set "BACKUP_TYPE=data"
    shift
    goto parse_args
)
if "%1"=="--compress" (
    set "COMPRESS=true"
    shift
    goto parse_args
)
if "%1"=="--no-compress" (
    set "COMPRESS=false"
    shift
    goto parse_args
)
if "%1"=="--include-logs" (
    set "INCLUDE_LOGS=true"
    shift
    goto parse_args
)
if "%1"=="--include-node-modules" (
    set "INCLUDE_NODE_MODULES=true"
    shift
    goto parse_args
)
if "%1"=="--name" (
    shift
    set "BACKUP_NAME=%1"
    shift
    goto parse_args
)
if "%1"=="--help" (
    goto show_help
)
shift
goto parse_args

:args_done

:: Set project root
set "PROJECT_ROOT=%~dp0.."

:: Change to project root
cd /d "%PROJECT_ROOT%"

:: Generate backup name if not provided
if "%BACKUP_NAME%"=="" (
    for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
    set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
    set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
    set "BACKUP_NAME=backup_%YYYY%%MM%%DD%_%HH%%Min%%Sec%"
)

:: Set backup directory
set "BACKUP_DIR=backup\current\%BACKUP_NAME%"

echo [INFO] Creating %BACKUP_TYPE% backup: %BACKUP_NAME%
echo [INFO] Compress: %COMPRESS%, Include logs: %INCLUDE_LOGS%, Include node_modules: %INCLUDE_NODE_MODULES%
echo.

:: Create backup directory
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

:: Create backup based on type
if "%BACKUP_TYPE%"=="full" goto backup_full
if "%BACKUP_TYPE%"=="incremental" goto backup_incremental
if "%BACKUP_TYPE%"=="config" goto backup_config
if "%BACKUP_TYPE%"=="data" goto backup_data

:backup_full
echo [INFO] Creating full backup...

:: Backup source code
echo [INFO] Backing up source code...
xcopy "apps" "%BACKUP_DIR%\apps" /E /I /H /Y /Q
xcopy "packages" "%BACKUP_DIR%\packages" /E /I /H /Y /Q
xcopy "tools" "%BACKUP_DIR%\tools" /E /I /H /Y /Q
xcopy "training" "%BACKUP_DIR%\training" /E /I /H /Y /Q
xcopy "tests" "%BACKUP_DIR%\tests" /E /I /H /Y /Q

:: Backup configuration files
echo [INFO] Backing up configuration files...
xcopy "*.json" "%BACKUP_DIR%\" /H /Y /Q
xcopy "*.yaml" "%BACKUP_DIR%\" /H /Y /Q
xcopy "*.yml" "%BACKUP_DIR%\" /H /Y /Q
xcopy "*.bat" "%BACKUP_DIR%\" /H /Y /Q
xcopy "*.md" "%BACKUP_DIR%\" /H /Y /Q
xcopy ".gitignore" "%BACKUP_DIR%\" /H /Y /Q

:: Backup data if exists
if exist "data" (
    echo [INFO] Backing up data...
    xcopy "data" "%BACKUP_DIR%\data" /E /I /H /Y /Q
)

:: Backup logs if requested
if "%INCLUDE_LOGS%"=="true" (
    if exist "logs" (
        echo [INFO] Backing up logs...
        xcopy "logs" "%BACKUP_DIR%\logs" /E /I /H /Y /Q
    )
)

:: Backup node_modules if requested
if "%INCLUDE_NODE_MODULES%"=="true" (
    if exist "node_modules" (
        echo [INFO] Backing up node_modules...
        xcopy "node_modules" "%BACKUP_DIR%\node_modules" /E /I /H /Y /Q
    )
)

goto backup_complete

:backup_incremental
echo [INFO] Creating incremental backup...

:: Get last backup date
set "LAST_BACKUP="
for /f "delims=" %%i in ('dir /b /ad /o-d backup\current 2^>nul') do (
    set "LAST_BACKUP=%%i"
    goto :found_last_backup
)
:found_last_backup

if "%LAST_BACKUP%"=="" (
    echo [WARNING] No previous backup found, creating full backup instead
    goto backup_full
)

echo [INFO] Last backup: %LAST_BACKUP%
echo [INFO] Backing up changed files since %LAST_BACKUP%...

:: Use robocopy for incremental backup
robocopy "apps" "%BACKUP_DIR%\apps" /E /XO /XD node_modules .git
robocopy "packages" "%BACKUP_DIR%\packages" /E /XO /XD node_modules .git
robocopy "tools" "%BACKUP_DIR%\tools" /E /XO
robocopy "training" "%BACKUP_DIR%\training" /E /XO
robocopy "tests" "%BACKUP_DIR%\tests" /E /XO

:: Backup configuration files
xcopy "*.json" "%BACKUP_DIR%\" /H /Y /Q /D
xcopy "*.yaml" "%BACKUP_DIR%\" /H /Y /Q /D
xcopy "*.yml" "%BACKUP_DIR%\" /H /Y /Q /D
xcopy "*.bat" "%BACKUP_DIR%\" /H /Y /Q /D
xcopy "*.md" "%BACKUP_DIR%\" /H /Y /Q /D

goto backup_complete

:backup_config
echo [INFO] Creating configuration backup...

:: Backup only configuration files
xcopy "*.json" "%BACKUP_DIR%\" /H /Y /Q
xcopy "*.yaml" "%BACKUP_DIR%\" /H /Y /Q
xcopy "*.yml" "%BACKUP_DIR%\" /H /Y /Q
xcopy "*.bat" "%BACKUP_DIR%\" /H /Y /Q
xcopy ".gitignore" "%BACKUP_DIR%\" /H /Y /Q

:: Backup app configurations
if exist "apps\backend\configs" (
    xcopy "apps\backend\configs" "%BACKUP_DIR%\apps\backend\configs" /E /I /H /Y /Q
)

goto backup_complete

:backup_data
echo [INFO] Creating data backup...

:: Backup only data files
if exist "data" (
    xcopy "data" "%BACKUP_DIR%\data" /E /I /H /Y /Q
)

if exist "logs" (
    xcopy "logs" "%BACKUP_DIR%\logs" /E /I /H /Y /Q
)

goto backup_complete

:backup_complete
:: Create backup info file
echo [INFO] Creating backup info file...
(
echo Backup created: %date% %time%
echo Backup type: %BACKUP_TYPE%
echo Compress: %COMPRESS%
echo Include logs: %INCLUDE_LOGS%
echo Include node_modules: %INCLUDE_NODE_MODULES%
echo Project root: %PROJECT_ROOT%
echo Backup directory: %BACKUP_DIR%
) > "%BACKUP_DIR%\backup_info.txt"

:: Compress backup if requested
if "%COMPRESS%"=="true" (
    echo [INFO] Compressing backup...
    if exist "7z.exe" (
        7z a -tzip "%BACKUP_DIR%.zip" "%BACKUP_DIR%\*"
        if errorlevel 1 (
            echo [WARNING] Failed to compress backup
        ) else (
            echo [INFO] Backup compressed to %BACKUP_DIR%.zip
            rmdir /s /q "%BACKUP_DIR%"
        )
    ) else (
        echo [WARNING] 7z not found, backup not compressed
    )
)

echo.
echo [SUCCESS] Backup created successfully: %BACKUP_NAME%
echo [INFO] Backup location: %BACKUP_DIR%
echo [%date% %time%] Backup created successfully: %BACKUP_NAME% >> "%LOG_FILE%" 2>nul
exit /b 0

:show_help
echo.
echo Usage: backup.bat [options]
echo.
echo Options:
echo   --full           Create full backup (default)
echo   --incremental    Create incremental backup
echo   --config         Backup configuration files only
echo   --data           Backup data files only
echo   --compress       Compress backup (default)
echo   --no-compress    Don't compress backup
echo   --include-logs   Include log files
echo   --include-node-modules  Include node_modules
echo   --name NAME      Specify backup name
echo   --help           Show this help message
echo.
echo Examples:
echo   backup.bat --full --compress
echo   backup.bat --incremental --name daily_backup
echo   backup.bat --config --no-compress
echo.
pause
exit /b 0
