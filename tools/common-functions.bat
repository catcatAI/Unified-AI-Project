@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

:: Unified AI Project - Common Functions Library
:: This script contains common functions used by multiple batch files

:: Function to check if a tool is installed
:: Usage: call :check_tool tool_name
:check_tool
set "tool_name=%~1"
where %tool_name% >nul 2>&1
if errorlevel 1 (
    echo [ERROR] %tool_name% not installed
    echo [%date% %time%] %tool_name% not installed >> "%LOG_FILE%" 2>nul
    exit /b 1
)
exit /b 0

:: Function to validate user input
:: Usage: call :validate_input "input_var" "prompt_message"
:validate_input
set "input_var=%~1"
set "prompt_message=%~2"

:get_user_input
set "%input_var%="
set /p "%input_var%=%prompt_message%"
if not defined %input_var% (
    echo [ERROR] No input provided
    echo [%date% %time%] No input provided >> "%LOG_FILE%" 2>nul
    goto get_user_input
)
exit /b 0

:: Function to resolve path consistently
:: Usage: call :resolve_path "path_var" "relative_path"
:resolve_path
set "path_var=%~1"
set "relative_path=%~2"
set "%path_var%=%~dp0%relative_path%"
if "%%path_var:~-1%%"=="\" set "%path_var%=%%path_var:~0,-1%%"
exit /b 0

:: Function to setup logging
:: Usage: call :setup_logging "log_file_name"
:setup_logging
set "log_file_name=%~1"
set "LOG_FILE=%~dp0%log_file_name%"
echo [%date% %time%] Script started: %SCRIPT_NAME% >> "%LOG_FILE%" 2>nul
exit /b 0

:: Function to handle errors consistently
:: Usage: call :handle_error "error_message" "error_code"
:handle_error
set "error_message=%~1"
set "error_code=%~2"
echo [ERROR] %error_message%
echo [%date% %time%] %error_message% >> "%LOG_FILE%" 2>nul
if defined error_code (
    exit /b %error_code%
) else (
    exit /b 1
)

:: Function to check and activate virtual environment
:: Usage: call :activate_venv "venv_path"
:activate_venv
set "venv_path=%~1"
if not defined venv_path set "venv_path=venv"

if exist "%venv_path%\Scripts\activate.bat" (
    call %venv_path%\Scripts\activate.bat >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Failed to activate virtual environment
        echo [%date% %time%] Failed to activate virtual environment >> "%LOG_FILE%" 2>nul
        exit /b 1
    )
) else (
    echo [ERROR] Virtual environment not found at %venv_path%
    echo [%date% %time%] Virtual environment not found >> "%LOG_FILE%" 2>nul
    exit /b 1
)
exit /b 0

:: Function to deactivate virtual environment
:: Usage: call :deactivate_venv
:deactivate_venv
if defined VIRTUAL_ENV (
    call venv\Scripts\deactivate.bat >nul 2>&1
)
exit /b 0

:: Function to check if a directory exists
:: Usage: call :check_directory "dir_path" "description"
:check_directory
set "dir_path=%~1"
set "description=%~2"
if not exist "%dir_path%" (
    echo [WARNING] %description% directory not found: %dir_path%
    echo [%date% %time%] %description% directory not found >> "%LOG_FILE%" 2>nul
    exit /b 1
)
exit /b 0

:: Function to create directory if it doesn't exist
:: Usage: call :ensure_directory "dir_path"
:ensure_directory
set "dir_path=%~1"
if not exist "%dir_path%" (
    mkdir "%dir_path%" >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Failed to create directory: %dir_path%
        echo [%date% %time%] Failed to create directory >> "%LOG_FILE%" 2>nul
        exit /b 1
    )
)
exit /b 0

:: Function to get user confirmation
:: Usage: call :confirm_action "action_description"
:confirm_action
set "action_description=%~1"
echo [CONFIRM] %action_description%

:: 使用 set /p 替代 choice 命令
:get_user_choice
set "user_choice="
set /p "user_choice=Continue (y/N)? "
if not defined user_choice (
    set "user_choice=N"
)

:: 验证用户输入
if /i "%user_choice%"=="Y" (
    exit /b 0
) else if /i "%user_choice%"=="N" (
    echo [INFO] Operation cancelled by user
    echo [%date% %time%] Operation cancelled by user >> "%LOG_FILE%" 2>nul
    exit /b 1
) else (
    echo [ERROR] Invalid choice '%user_choice%'. Please enter 'Y' or 'N'.
    echo [%date% %time%] Invalid choice: %user_choice% >> "%LOG_FILE%" 2>nul
    goto get_user_choice
)

:: Function to log info message
:: Usage: call :log_info "message"
:log_info
set "message=%~1"
echo [INFO] %message%
echo [%date% %time%] %message% >> "%LOG_FILE%" 2>nul
exit /b 0

:: Function to log success message
:: Usage: call :log_success "message"
:log_success
set "message=%~1"
echo [SUCCESS] %message%
echo [%date% %time%] %message% >> "%LOG_FILE%" 2>nul
exit /b 0

:: Function to log warning message
:: Usage: call :log_warning "message"
:log_warning
set "message=%~1"
echo [WARNING] %message%
echo [%date% %time%] %message% >> "%LOG_FILE%" 2>nul
exit /b 0