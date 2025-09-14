@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Git Cleanup
color 0D

:: Add error handling and logging
set "LOG_FILE=%~dp0..\logs\git-cleanup.log"
set "SCRIPT_NAME=git-cleanup.bat"

:: Log script start
echo [%date% %time%] Script started: %SCRIPT_NAME% >> "%LOG_FILE%" 2>nul

:: Create logs directory if it doesn't exist
if not exist "%~dp0..\logs" mkdir "%~dp0..\logs"

echo ==========================================
echo   Unified AI Project - Git Cleanup
echo ==========================================
echo.

:: Parse command line arguments
set "CLEANUP_TYPE=status"
set "FORCE=false"
set "VERBOSE=false"
set "BACKUP=true"

:parse_args
if "%1"=="" goto args_done
if "%1"=="--status" (
    set "CLEANUP_TYPE=status"
    shift
    goto parse_args
)
if "%1"=="--clean" (
    set "CLEANUP_TYPE=clean"
    shift
    goto parse_args
)
if "%1"=="--reset" (
    set "CLEANUP_TYPE=reset"
    shift
    goto parse_args
)
if "%1"=="--stash" (
    set "CLEANUP_TYPE=stash"
    shift
    goto parse_args
)
if "%1"=="--fix-10k" (
    set "CLEANUP_TYPE=fix-10k"
    shift
    goto parse_args
)
if "%1"=="--emergency" (
    set "CLEANUP_TYPE=emergency"
    shift
    goto parse_args
)
if "%1"=="--force" (
    set "FORCE=true"
    shift
    goto parse_args
)
if "%1"=="--verbose" (
    set "VERBOSE=true"
    shift
    goto parse_args
)
if "%1"=="--no-backup" (
    set "BACKUP=false"
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

echo [INFO] Running Git cleanup: %CLEANUP_TYPE%
echo [INFO] Force: %FORCE%, Verbose: %VERBOSE%, Backup: %BACKUP%
echo.

:: Check if git is available
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git not found. Please install Git.
    echo [%date% %time%] ERROR: Git not found >> "%LOG_FILE%" 2>nul
    exit /b 1
)

:: Check if we're in a git repository
git status >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Not in a git repository
    echo [%date% %time%] ERROR: Not in a git repository >> "%LOG_FILE%" 2>nul
    exit /b 1
)

:: Create backup if requested
if "%BACKUP%"=="true" (
    echo [INFO] Creating backup before cleanup...
    call "%~dp0..\tools\utilities\backup.bat" --config --name "git_cleanup_%date:~0,10%"
    if errorlevel 1 (
        echo [WARNING] Backup creation failed, continuing with cleanup
    )
)

:: Run cleanup based on type
if "%CLEANUP_TYPE%"=="status" goto git_status
if "%CLEANUP_TYPE%"=="clean" goto git_clean
if "%CLEANUP_TYPE%"=="reset" goto git_reset
if "%CLEANUP_TYPE%"=="stash" goto git_stash
if "%CLEANUP_TYPE%"=="fix-10k" goto git_fix_10k
if "%CLEANUP_TYPE%"=="emergency" goto git_emergency

:git_status
echo [INFO] Checking Git status...
echo.
git status
if errorlevel 1 (
    echo [ERROR] Failed to get git status
    echo [%date% %time%] ERROR: Failed to get git status >> "%LOG_FILE%" 2>nul
    exit /b 1
)

echo.
echo [INFO] Git status check completed
goto cleanup_complete

:git_clean
echo [INFO] Cleaning untracked files...

:: Show what will be cleaned
echo [INFO] Files to be cleaned:
git clean -n
if errorlevel 1 (
    echo [ERROR] Failed to preview clean operation
    echo [%date% %time%] ERROR: Failed to preview clean operation >> "%LOG_FILE%" 2>nul
    exit /b 1
)

if "%FORCE%"=="true" (
    echo [INFO] Force cleaning untracked files...
    git clean -f -d
    if errorlevel 1 (
        echo [ERROR] Failed to clean untracked files
        echo [%date% %time%] ERROR: Failed to clean untracked files >> "%LOG_FILE%" 2>nul
        exit /b 1
    )
) else (
    echo [INFO] Use --force to actually clean files
)

goto cleanup_complete

:git_reset
echo [INFO] Resetting Git repository...

:: Show current status
echo [INFO] Current status:
git status --short

if "%FORCE%"=="true" (
    echo [INFO] Force resetting repository...
    git reset --hard HEAD
    if errorlevel 1 (
        echo [ERROR] Failed to reset repository
        echo [%date% %time%] ERROR: Failed to reset repository >> "%LOG_FILE%" 2>nul
        exit /b 1
    )
    
    git clean -f -d
    if errorlevel 1 (
        echo [ERROR] Failed to clean untracked files
        echo [%date% %time%] ERROR: Failed to clean untracked files >> "%LOG_FILE%" 2>nul
        exit /b 1
    )
) else (
    echo [INFO] Use --force to actually reset repository
)

goto cleanup_complete

:git_stash
echo [INFO] Stashing changes...

:: Check if there are changes to stash
git diff --quiet
if errorlevel 1 (
    echo [INFO] Stashing uncommitted changes...
    git stash push -m "Auto-stash before cleanup %date% %time%"
    if errorlevel 1 (
        echo [ERROR] Failed to stash changes
        echo [%date% %time%] ERROR: Failed to stash changes >> "%LOG_FILE%" 2>nul
        exit /b 1
    )
    echo [SUCCESS] Changes stashed successfully
) else (
    echo [INFO] No changes to stash
)

goto cleanup_complete

:git_fix_10k
echo [INFO] Fixing Git 10K+ files issue...

:: Check if there are too many files
git status --porcelain | find /c /v "" > temp_count.txt
set /p FILE_COUNT=<temp_count.txt
del temp_count.txt

if %FILE_COUNT% GTR 10000 (
    echo [WARNING] Found %FILE_COUNT% files, this may cause Git issues
    echo [INFO] Attempting to fix...
    
    :: Add .gitignore rules
    echo [INFO] Adding .gitignore rules...
    (
        echo.
        echo # Ignore large directories
        echo node_modules/
        echo venv/
        echo .venv/
        echo __pycache__/
        echo .pytest_cache/
        echo .coverage
        echo htmlcov/
        echo .mypy_cache/
        echo .dmypy.json
        echo dmypy.json
        echo .pyre/
        echo .python-version
        echo celerybeat-schedule
        echo *.sage.py
        echo.
        echo # Ignore build outputs
        echo build/
        echo develop-eggs/
        echo dist/
        echo downloads/
        echo eggs/
        echo lib/
        echo lib64/
        echo parts/
        echo sdist/
        echo var/
        echo wheels/
        echo .installed.cfg
        echo.
        echo # Ignore data directories
        echo data/
        echo !data/README.md
        echo !data/TRAINING_DATA_GUIDE.md
        echo !data/data_config.json
        echo.
        echo # Ignore backup directories
        echo backup/
        echo docs/
        echo !docs/README.md
    ) >> .gitignore
    
    :: Remove files from git index
    echo [INFO] Removing files from git index...
    git rm -r --cached node_modules/ 2>nul
    git rm -r --cached venv/ 2>nul
    git rm -r --cached .venv/ 2>nul
    git rm -r --cached data/ 2>nul
    git rm -r --cached backup/ 2>nul
    git rm -r --cached docs/ 2>nul
    
    :: Commit changes
    echo [INFO] Committing changes...
    git add .gitignore
    git commit -m "Fix Git 10K+ files issue by updating .gitignore"
    
    echo [SUCCESS] Git 10K+ files issue fixed
) else (
    echo [INFO] File count (%FILE_COUNT%) is within normal limits
)

goto cleanup_complete

:git_emergency
echo [INFO] Emergency Git recovery...

:: Create emergency backup
echo [INFO] Creating emergency backup...
call "%~dp0..\tools\utilities\backup.bat" --full --name "emergency_backup_%date:~0,10%"
if errorlevel 1 (
    echo [WARNING] Emergency backup failed, continuing with recovery
)

:: Reset to last known good state
echo [INFO] Resetting to last known good state...
git reset --hard HEAD~1
if errorlevel 1 (
    echo [ERROR] Failed to reset to previous commit
    echo [%date% %time%] ERROR: Failed to reset to previous commit >> "%LOG_FILE%" 2>nul
    exit /b 1
)

:: Clean untracked files
echo [INFO] Cleaning untracked files...
git clean -f -d
if errorlevel 1 (
    echo [ERROR] Failed to clean untracked files
    echo [%date% %time%] ERROR: Failed to clean untracked files >> "%LOG_FILE%" 2>nul
    exit /b 1
)

echo [SUCCESS] Emergency recovery completed

:cleanup_complete
echo.
echo [SUCCESS] Git cleanup completed successfully
echo [%date% %time%] Git cleanup completed successfully >> "%LOG_FILE%" 2>nul
exit /b 0

:show_help
echo.
echo Usage: git-cleanup.bat [options]
echo.
echo Options:
echo   --status        Show Git status (default)
echo   --clean         Clean untracked files
echo   --reset         Reset repository to HEAD
echo   --stash         Stash uncommitted changes
echo   --fix-10k       Fix Git 10K+ files issue
echo   --emergency     Emergency recovery
echo   --force         Force operation without confirmation
echo   --verbose       Verbose output
echo   --no-backup     Don't create backup before cleanup
echo   --help          Show this help message
echo.
echo Examples:
echo   git-cleanup.bat --status
echo   git-cleanup.bat --clean --force
echo   git-cleanup.bat --fix-10k --verbose
echo   git-cleanup.bat --emergency --no-backup
echo.
pause
exit /b 0
