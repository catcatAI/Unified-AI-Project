@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Enhanced Unified Management Tool
color 0A

:: Add error handling and logging
set "LOG_FILE=%~dp0unified-ai-errors.log"
set "SCRIPT_NAME=unified-ai.bat"

:: Log script start
echo [%date% %time%] Script started: %SCRIPT_NAME% >> "%LOG_FILE%" 2>nul

:: Main menu
:main_menu
cls
echo ==========================================
echo   Unified AI Project - Enhanced Unified Management
echo ==========================================
echo.
echo Available Actions:
echo.
echo 1. Health Check - Check development environment (檢查開發環境)
echo 2. Setup Environment - Install dependencies and setup (安裝依賴和設置)
echo 3. Start Development - Launch development servers (啟動開發服務器)
echo 4. Run Tests - Execute test suite (執行測試套件)
echo 5. Git Management - Git status and cleanup (Git狀態和清理)
echo 6. Training Setup - Prepare for AI training (準備AI訓練)
echo 7. Training Manager - Manage training data and processes (管理訓練數據和過程)
echo 8. CLI Tools - Access Unified AI CLI tools (訪問Unified AI CLI工具)
echo 9. Model Management - Manage AI models and DNA chains (管理AI模型和DNA鏈)
echo 10. Data Analysis - Analyze project data and statistics (分析項目數據和統計)
echo 11. Data Pipeline - Run automated data processing pipeline (運行自動化數據處理流水線)
echo 12. Emergency Git Fix - Recover from Git issues (從Git問題中恢復)
echo 13. Fix Dependencies - Resolve dependency issues (解決依賴問題)
echo 14. System Information - Display system information (顯示系統信息)
echo 15. Unified Auto Fix - Enhanced auto-fix system with 4 modes (增強自動修復系統)
echo 16. Exit (退出)
echo.

:: Get user choice with validation
:get_user_choice
set "choice="
set /p "choice=Enter your choice (1-16): "
if not defined choice (
    echo [ERROR] No input provided
    echo [%date% %time%] No input provided >> "%LOG_FILE%" 2>nul
    timeout /t 2 >nul
    goto get_user_choice
)

:: Validate numeric input for menu choices
set "choice=%choice: =%"
for %%i in (1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16) do (
    if "%choice%"=="%%i" (
        goto choice_%%i
    )
)

echo [ERROR] Invalid choice '%choice%'. Please enter a valid option (1-16).
echo [%date% %time%] Invalid choice: %choice% >> "%LOG_FILE%" 2>nul
timeout /t 2 >nul
goto get_user_choice

:choice_1
goto health_check
:choice_2
goto setup_env
:choice_3
goto start_dev
:choice_4
goto run_tests
:choice_5
goto git_management
:choice_6
goto training_setup
:choice_7
goto training_manager
:choice_8
goto cli_tools
:choice_9
goto model_management
:choice_10
goto data_analysis
:choice_11
goto data_pipeline
:choice_12
goto emergency_git_fix
:choice_13
goto fix_dependencies
:choice_14
goto system_info
:choice_15
goto unified_auto_fix
:choice_16
goto end_script

:: Data Pipeline Function
:data_pipeline
echo.
echo [INFO] Running Automated Data Pipeline...
echo [%date% %time%] Running automated data pipeline >> "%LOG_FILE%" 2>nul
echo.

:: Check if data pipeline script exists
set "PIPELINE_SCRIPT=%~dp0tools\run_data_pipeline.bat"
if exist "%PIPELINE_SCRIPT%" (
    echo [INFO] Launching data pipeline script...
    echo.
    call "%PIPELINE_SCRIPT%"
) else (
    echo [ERROR] Data pipeline script not found: %PIPELINE_SCRIPT%
    echo [%date% %time%] Data pipeline script not found >> "%LOG_FILE%" 2>nul
)

echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu

:: Model Management Function
:model_management
echo.
echo [INFO] AI Model Management
echo.
echo Available Model Management Options:
echo.
echo 1. List All Models - Show all available AI models (顯示所有可用的AI模型)
echo 2. Model Health Check - Check status of all models (檢查所有模型的狀態)
echo 3. DNA Chain Management - Manage DNA data chains (管理DNA數據鏈)
echo 4. Model Performance Report - Generate model performance report (生成模型性能報告)
echo 5. Back to Main Menu (返回主菜單)
echo.

:: Get model management choice with validation
:get_model_choice
set "model_choice="
set /p "model_choice=Enter your choice (1-5): "
if not defined model_choice (
    echo [ERROR] No input provided
    echo [%date% %time%] No model management choice provided >> "%LOG_FILE%" 2>nul
    timeout /t 2 >nul
    goto get_model_choice
)

:: Validate numeric input for model management choices
set "model_choice=%model_choice: =%"
for %%i in (1 2 3 4 5) do (
    if "%model_choice%"=="%%i" (
        goto model_choice_%%i
    )
)

echo [ERROR] Invalid choice '%model_choice%'. Please enter a valid option.
echo [%date% %time%] Invalid model management choice: %model_choice% >> "%LOG_FILE%" 2>nul
timeout /t 2 >nul
goto get_model_choice

:model_choice_1
goto list_all_models
:model_choice_2
goto model_health_check
:model_choice_3
goto dna_chain_management
:model_choice_4
goto model_performance_report
:model_choice_5
goto main_menu

:: List All Models Function
:list_all_models
echo.
echo [INFO] Listing All AI Models...
echo [%date% %time%] Listing all AI models >> "%LOG_FILE%" 2>nul
echo.
cd /d %~dp0packages\cli
if exist "cli/ai_models_cli.py" (
    echo Running: python cli/ai_models_cli.py list
    echo.
    python cli/ai_models_cli.py list
) else (
    echo [ERROR] AI Models CLI script not found
    echo [%date% %time%] AI Models CLI script not found >> "%LOG_FILE%" 2>nul
)
cd ..\..\..
echo.
echo Press any key to return to model management menu...
pause >nul
goto model_management

:: Model Health Check Function
:model_health_check
echo.
echo [INFO] Performing Model Health Check...
echo [%date% %time%] Performing model health check >> "%LOG_FILE%" 2>nul
echo.
cd /d %~dp0packages\cli
if exist "cli/ai_models_cli.py" (
    echo Running: python cli/ai_models_cli.py health
    echo.
    python cli/ai_models_cli.py health
) else (
    echo [ERROR] AI Models CLI script not found
    echo [%date% %time%] AI Models CLI script not found >> "%LOG_FILE%" 2>nul
)
cd ..\..\..
echo.
echo Press any key to return to model management menu...
pause >nul
goto model_management

:: DNA Chain Management Function
:dna_chain_management
echo.
echo [INFO] DNA Chain Management
echo.
echo Available DNA Chain Management Options:
echo.
echo 1. List DNA Chains - Show all DNA data chains (顯示所有DNA數據鏈)
echo 2. Create DNA Chain - Create a new DNA data chain (創建新的DNA數據鏈)
echo 3. View DNA Chain Details - View details of a specific DNA chain (查看特定DNA鏈的詳細信息)
echo 4. Merge DNA Chains - Merge two DNA chains (合併兩個DNA鏈)
echo 5. Back to Model Management (返回模型管理)
echo.

:: Get DNA chain management choice with validation
:get_dna_choice
set "dna_choice="
set /p "dna_choice=Enter your choice (1-5): "
if not defined dna_choice (
    echo [ERROR] No input provided
    echo [%date% %time%] No DNA chain management choice provided >> "%LOG_FILE%" 2>nul
    timeout /t 2 >nul
    goto get_dna_choice
)

:: Validate numeric input for DNA chain management choices
set "dna_choice=%dna_choice: =%"
for %%i in (1 2 3 4 5) do (
    if "%dna_choice%"=="%%i" (
        goto dna_choice_%%i
    )
)

echo [ERROR] Invalid choice '%dna_choice%'. Please enter a valid option.
echo [%date% %time%] Invalid DNA chain management choice: %dna_choice% >> "%LOG_FILE%" 2>nul
timeout /t 2 >nul
goto get_dna_choice

:dna_choice_1
goto list_dna_chains
:dna_choice_2
goto create_dna_chain
:dna_choice_3
goto view_dna_chain
:dna_choice_4
goto merge_dna_chains
:dna_choice_5
goto model_management

:: List DNA Chains Function
:list_dna_chains
echo.
echo [INFO] Listing DNA Data Chains...
echo [%date% %time%] Listing DNA data chains >> "%LOG_FILE%" 2>nul
echo.
echo TODO: Implement DNA chain listing functionality
echo.
echo Press any key to return to DNA chain management menu...
pause >nul
goto dna_chain_management

:: Create DNA Chain Function
:create_dna_chain
echo.
echo [INFO] Creating DNA Data Chain...
echo [%date% %time%] Creating DNA data chain >> "%LOG_FILE%" 2>nul
echo.
set /p "chain_name=Enter DNA chain name: "
if defined chain_name (
    echo TODO: Implement DNA chain creation functionality for %chain_name%
) else (
    echo [ERROR] No DNA chain name provided
    echo [%date% %time%] No DNA chain name provided >> "%LOG_FILE%" 2>nul
)
echo.
echo Press any key to return to DNA chain management menu...
pause >nul
goto dna_chain_management

:: View DNA Chain Details Function
:view_dna_chain
echo.
echo [INFO] Viewing DNA Chain Details...
echo [%date% %time%] Viewing DNA chain details >> "%LOG_FILE%" 2>nul
echo.
set /p "chain_id=Enter DNA chain ID: "
if defined chain_id (
    echo TODO: Implement DNA chain details view for %chain_id%
) else (
    echo [ERROR] No DNA chain ID provided
    echo [%date% %time%] No DNA chain ID provided >> "%LOG_FILE%" 2>nul
)
echo.
echo Press any key to return to DNA chain management menu...
pause >nul
goto dna_chain_management

:: Merge DNA Chains Function
:merge_dna_chains
echo.
echo [INFO] Merging DNA Chains...
echo [%date% %time%] Merging DNA chains >> "%LOG_FILE%" 2>nul
echo.
set /p "chain1_id=Enter first DNA chain ID: "
set /p "chain2_id=Enter second DNA chain ID: "
if defined chain1_id if defined chain2_id (
    echo TODO: Implement DNA chain merging functionality for %chain1_id% and %chain2_id%
) else (
    echo [ERROR] Both DNA chain IDs must be provided
    echo [%date% %time%] Missing DNA chain IDs for merge >> "%LOG_FILE%" 2>nul
)
echo.
echo Press any key to return to DNA chain management menu...
pause >nul
goto dna_chain_management

:: Model Performance Report Function
:model_performance_report
echo.
echo [INFO] Generating Model Performance Report...
echo [%date% %time%] Generating model performance report >> "%LOG_FILE%" 2>nul
echo.
echo TODO: Implement model performance report generation
echo.
echo Press any key to return to model management menu...
pause >nul
goto model_management

:: Health Check Function
:health_check
echo.
echo [INFO] Running Health Check...
echo [%date% %time%] Running health check >> "%LOG_FILE%" 2>nul
echo.
if exist "tools\health-check.bat" (
    call tools\health-check.bat
) else (
    echo [ERROR] Health check script not found
    echo [%date% %time%] Health check script not found >> "%LOG_FILE%" 2>nul
)
echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu

:: Setup Environment Function
:setup_env
echo.
echo [INFO] Setting up Environment...
echo [%date% %time%] Setting up environment >> "%LOG_FILE%" 2>nul
echo.
if exist "tools\start-dev.bat" (
    call tools\start-dev.bat
) else (
    echo [ERROR] Environment setup script not found
    echo [%date% %time%] Environment setup script not found >> "%LOG_FILE%" 2>nul
)
echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu

:: Start Development Function
:start_dev
echo.
echo [INFO] Starting Development Environment...
echo [%date% %time%] Starting development environment >> "%LOG_FILE%" 2>nul
echo.
if exist "tools\start-dev.bat" (
    call tools\start-dev.bat
) else (
    echo [ERROR] Development start script not found
    echo [%date% %time%] Development start script not found >> "%LOG_FILE%" 2>nul
)
echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu

:: Run Tests Function
:run_tests
echo.
echo [INFO] Running Tests...
echo [%date% %time%] Running tests >> "%LOG_FILE%" 2>nul
echo.

:: Run the unified test script
if exist "tools\core\run-tests.bat" (
    echo [INFO] Executing unified test script...
    call "tools\core\run-tests.bat" --all --verbose
    if errorlevel 1 (
        echo [ERROR] Test execution failed
        echo [%date% %time%] ERROR: Test execution failed >> "%LOG_FILE%" 2>nul
    ) else (
        echo [SUCCESS] Tests completed successfully
        echo [%date% %time%] SUCCESS: Tests completed successfully >> "%LOG_FILE%" 2>nul
    )
) else if exist "tools\run-tests.bat" (
    echo [INFO] Executing legacy test script...
    call tools\run-tests.bat
    if errorlevel 1 (
        echo [ERROR] Test execution failed
        echo [%date% %time%] ERROR: Test execution failed >> "%LOG_FILE%" 2>nul
    ) else (
        echo [SUCCESS] Tests completed successfully
        echo [%date% %time%] SUCCESS: Tests completed successfully >> "%LOG_FILE%" 2>nul
    )
) else (
    echo [ERROR] Test script not found
    echo [%date% %time%] ERROR: Test script not found >> "%LOG_FILE%" 2>nul
)

echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu

:: Git Management Function
:git_management
echo.
echo [INFO] Git Management...
echo [%date% %time%] Git management >> "%LOG_FILE%" 2>nul
echo.
echo Available Git Management Options:
echo.
echo 1. Git Status - Show Git status (顯示Git狀態)
echo 2. Safe Git Cleanup - Clean Git status safely (安全清理Git狀態)
echo 3. Fix Git 10K+ Files - Fix Git 10K+ files issue (修復Git 10K+文件問題)
echo 4. Emergency Git Fix - Emergency Git recovery (緊急Git恢復)
echo 5. View Error Logs - View error logs (查看錯誤日志)
echo 6. Back to Main Menu (返回主菜單)
echo.

:: Get git management choice with validation
:get_git_choice
set "git_choice="
set /p "git_choice=Enter your choice (1-6): "
if not defined git_choice (
    echo [ERROR] No input provided
    echo [%date% %time%] No git management choice provided >> "%LOG_FILE%" 2>nul
    timeout /t 2 >nul
    goto get_git_choice
)

:: Validate numeric input for git management choices
set "git_choice=%git_choice: =%"
for %%i in (1 2 3 4 5 6) do (
    if "%git_choice%"=="%%i" (
        goto git_choice_%%i
    )
)

echo [ERROR] Invalid choice '%git_choice%'. Please enter a valid option.
echo [%date% %time%] Invalid git management choice: %git_choice% >> "%LOG_FILE%" 2>nul
timeout /t 2 >nul
goto get_git_choice

:git_choice_1
goto git_status
:git_choice_2
goto safe_git_cleanup
:git_choice_3
goto fix_git_10k
:git_choice_4
goto emergency_git_fix
:git_choice_5
goto view_error_logs
:git_choice_6
goto main_menu

:: Git Status Function
:git_status
echo.
echo [INFO] Showing Git Status...
echo [%date% %time%] Showing git status >> "%LOG_FILE%" 2>nul
echo.

:: Run the unified git cleanup script for status
if exist "tools\maintenance\git-cleanup.bat" (
    echo [INFO] Executing git status check...
    call "tools\maintenance\git-cleanup.bat" --status
    if errorlevel 1 (
        echo [ERROR] Git status check failed
        echo [%date% %time%] ERROR: Git status check failed >> "%LOG_FILE%" 2>nul
    )
) else if exist "tools\safe-git-cleanup.bat" (
    echo [INFO] Executing legacy git status check...
    call tools\safe-git-cleanup.bat
    if errorlevel 1 (
        echo [ERROR] Git status check failed
        echo [%date% %time%] ERROR: Git status check failed >> "%LOG_FILE%" 2>nul
    )
) else (
    echo [ERROR] Git cleanup script not found
    echo [%date% %time%] ERROR: Git cleanup script not found >> "%LOG_FILE%" 2>nul
)

echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu

:: Fix Git 10K+ Files Function
:fix_git_10k
echo.
echo [INFO] Fixing Git 10K+ Files Issue...
echo [%date% %time%] Fixing git 10k files issue >> "%LOG_FILE%" 2>nul
echo.

:: Run the unified git cleanup script for 10K fix
if exist "tools\maintenance\git-cleanup.bat" (
    echo [INFO] Executing git 10K fix...
    call "tools\maintenance\git-cleanup.bat" --fix-10k --verbose
    if errorlevel 1 (
        echo [ERROR] Git 10K fix failed
        echo [%date% %time%] ERROR: Git 10K fix failed >> "%LOG_FILE%" 2>nul
    ) else (
        echo [SUCCESS] Git 10K fix completed successfully
        echo [%date% %time%] SUCCESS: Git 10K fix completed successfully >> "%LOG_FILE%" 2>nul
    )
) else if exist "tools\fix-git-10k.bat" (
    echo [INFO] Executing legacy git 10K fix...
    call tools\fix-git-10k.bat
    if errorlevel 1 (
        echo [ERROR] Git 10K fix failed
        echo [%date% %time%] ERROR: Git 10K fix failed >> "%LOG_FILE%" 2>nul
    ) else (
        echo [SUCCESS] Git 10K fix completed successfully
        echo [%date% %time%] SUCCESS: Git 10K fix completed successfully >> "%LOG_FILE%" 2>nul
    )
) else (
    echo [ERROR] Git 10K fix script not found
    echo [%date% %time%] ERROR: Git 10K fix script not found >> "%LOG_FILE%" 2>nul
)

echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu

:: Emergency Git Fix Function
:emergency_git_fix
echo.
echo [INFO] Emergency Git Fix...
echo [%date% %time%] Emergency git fix >> "%LOG_FILE%" 2>nul
echo.

:: Run the unified git cleanup script for emergency fix
if exist "tools\maintenance\git-cleanup.bat" (
    echo [INFO] Executing emergency git fix...
    call "tools\maintenance\git-cleanup.bat" --emergency --force
    if errorlevel 1 (
        echo [ERROR] Emergency git fix failed
        echo [%date% %time%] ERROR: Emergency git fix failed >> "%LOG_FILE%" 2>nul
    ) else (
        echo [SUCCESS] Emergency git fix completed successfully
        echo [%date% %time%] SUCCESS: Emergency git fix completed successfully >> "%LOG_FILE%" 2>nul
    )
) else if exist "tools\emergency-git-fix.bat" (
    echo [INFO] Executing legacy emergency git fix...
    call tools\emergency-git-fix.bat
    if errorlevel 1 (
        echo [ERROR] Emergency git fix failed
        echo [%date% %time%] ERROR: Emergency git fix failed >> "%LOG_FILE%" 2>nul
    ) else (
        echo [SUCCESS] Emergency git fix completed successfully
        echo [%date% %time%] SUCCESS: Emergency git fix completed successfully >> "%LOG_FILE%" 2>nul
    )
) else (
    echo [ERROR] Emergency git fix script not found
    echo [%date% %time%] ERROR: Emergency git fix script not found >> "%LOG_FILE%" 2>nul
)

echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu

:: Safe Git Cleanup Function
:safe_git_cleanup
echo.
echo [INFO] Running Safe Git Cleanup...
echo [%date% %time%] Running safe git cleanup >> "%LOG_FILE%" 2>nul
echo.
if exist "tools\safe-git-cleanup.bat" (
    call tools\safe-git-cleanup.bat
) else (
    echo [ERROR] Safe Git cleanup script not found
    echo [%date% %time%] Safe Git cleanup script not found >> "%LOG_FILE%" 2>nul
)
echo.
echo Press any key to return to Git management menu...
pause >nul
goto git_management

:: View Error Logs Function
:view_error_logs
echo.
echo [INFO] Viewing Error Logs...
echo [%date% %time%] Viewing error logs >> "%LOG_FILE%" 2>nul
echo.
if exist "tools\view-error-logs.bat" (
    call tools\view-error-logs.bat
) else (
    echo [ERROR] Error log viewer script not found
    echo [%date% %time%] Error log viewer script not found >> "%LOG_FILE%" 2>nul
)
echo.
echo Press any key to return to Git management menu...
pause >nul
goto git_management

:: Training Setup Function
:training_setup
echo.
echo [INFO] Setting up Training Environment...
echo [%date% %time%] Setting up training environment >> "%LOG_FILE%" 2>nul
echo.
if exist "tools\setup-training.bat" (
    call tools\setup-training.bat
) else (
    echo [ERROR] Training setup script not found
    echo [%date% %time%] Training setup script not found >> "%LOG_FILE%" 2>nul
)
echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu

:: Training Manager Function
:training_manager
echo.
echo [INFO] Launching Training Manager...
echo [%date% %time%] Launching training manager >> "%LOG_FILE%" 2>nul
echo.
if exist "tools\train-manager.bat" (
    call tools\train-manager.bat
) else (
    echo [ERROR] Training manager script not found
    echo [%date% %time%] Training manager script not found >> "%LOG_FILE%" 2>nul
)
echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu

:: CLI Tools Function
:cli_tools
echo.
echo [INFO] Launching CLI Tools...
echo [%date% %time%] Launching CLI tools >> "%LOG_FILE%" 2>nul
echo.
if exist "tools\cli-runner.bat" (
    call tools\cli-runner.bat
) else (
    echo [ERROR] CLI runner script not found
    echo [%date% %time%] CLI runner script not found >> "%LOG_FILE%" 2>nul
)
echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu

:: Data Analysis Function
:data_analysis
echo.
echo [INFO] Performing Data Analysis...
echo [%date% %time%] Performing data analysis >> "%LOG_FILE%" 2>nul
echo.
echo TODO: Implement data analysis functionality
echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu

:: Emergency Git Fix Function
:emergency_git_fix
echo.
echo [INFO] Running Emergency Git Fix...
echo [%date% %time%] Running emergency Git fix >> "%LOG_FILE%" 2>nul
echo.
if exist "tools\emergency-git-fix.bat" (
    call tools\emergency-git-fix.bat
) else (
    echo [ERROR] Emergency Git fix script not found
    echo [%date% %time%] Emergency Git fix script not found >> "%LOG_FILE%" 2>nul
)
echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu

:: Fix Dependencies Function
:fix_dependencies
echo.
echo [INFO] Fixing Dependencies...
echo [%date% %time%] Fixing dependencies >> "%LOG_FILE%" 2>nul
echo.

:: Run the unified dependency fix script
if exist "tools\maintenance\fix-deps.bat" (
    echo [INFO] Executing unified dependency fix...
    call "tools\maintenance\fix-deps.bat" --all --verbose
    if errorlevel 1 (
        echo [ERROR] Dependency fix failed
        echo [%date% %time%] ERROR: Dependency fix failed >> "%LOG_FILE%" 2>nul
    ) else (
        echo [SUCCESS] Dependencies fixed successfully
        echo [%date% %time%] SUCCESS: Dependencies fixed successfully >> "%LOG_FILE%" 2>nul
    )
) else if exist "tools\fix-dependencies.bat" (
    echo [INFO] Executing legacy dependency fix...
    call tools\fix-dependencies.bat
    if errorlevel 1 (
        echo [ERROR] Dependency fix failed
        echo [%date% %time%] ERROR: Dependency fix failed >> "%LOG_FILE%" 2>nul
    ) else (
        echo [SUCCESS] Dependencies fixed successfully
        echo [%date% %time%] SUCCESS: Dependencies fixed successfully >> "%LOG_FILE%" 2>nul
    )
) else (
    echo [ERROR] Dependency fix script not found
    echo [%date% %time%] ERROR: Dependency fix script not found >> "%LOG_FILE%" 2>nul
)

echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu

:: System Information Function
:system_info
echo.
echo [INFO] Displaying System Information...
echo [%date% %time%] Displaying system information >> "%LOG_FILE%" 2>nul
echo.
systeminfo
echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu

:: Unified Auto Fix Function
:unified_auto_fix
echo.
echo [INFO] Unified Auto Fix System
echo [%date% %time%] Starting unified auto fix system >> "%LOG_FILE%" 2>nul
echo.

:: Check if unified auto fix script exists
set "UNIFIED_FIX_SCRIPT=%~dp0tools\scripts\unified_auto_fix.bat"
if exist "%UNIFIED_FIX_SCRIPT%" (
    echo [INFO] Launching unified auto fix system...
    echo.
    call "%UNIFIED_FIX_SCRIPT%"
    if errorlevel 1 (
        echo [ERROR] Unified auto fix failed
        echo [%date% %time%] ERROR: Unified auto fix failed >> "%LOG_FILE%" 2>nul
    ) else (
        echo [SUCCESS] Unified auto fix completed successfully
        echo [%date% %time%] SUCCESS: Unified auto fix completed successfully >> "%LOG_FILE%" 2>nul
    )
) else (
    echo [ERROR] Unified auto fix script not found: %UNIFIED_FIX_SCRIPT%
    echo [%date% %time%] ERROR: Unified auto fix script not found >> "%LOG_FILE%" 2>nul
)

echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu

:: End Script Function
:end_script
echo.
echo [INFO] Exiting Unified AI Project Management Tool...
echo [%date% %time%] Exiting Unified AI Project Management Tool >> "%LOG_FILE%" 2>nul
echo.
echo Thank you for using the Unified AI Project Management Tool!
echo 感謝您使用Unified AI Project管理工具！
echo.
echo Press any key to exit...
pause >nul
exit /b 0