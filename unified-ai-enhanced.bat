@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Enhanced Unified Management Tool
color 0A

echo ==========================================
echo   Unified AI Project - Enhanced Unified Management
echo ==========================================
echo.

:: Main menu
:main_menu
cls
echo ==========================================
echo   Unified AI Project - Enhanced Unified Management
echo ==========================================
echo.
echo Available Actions:
echo.
echo 1. Health Check - Check development environment
echo 2. Setup Environment - Install dependencies and setup
echo 3. Start Development - Launch development servers
echo 4. Run Tests - Execute test suite
echo 5. Git Management - Git status and cleanup
echo 6. Training Setup - Prepare for AI training
echo 7. Training Manager - Manage training data and processes
echo 8. CLI Tools - Access Unified AI CLI tools
echo 9. Model Management - Manage AI models and DNA chains
echo 10. Data Analysis - Analyze project data and statistics
echo 11. Emergency Git Fix - Recover from Git issues
echo 12. Fix Dependencies - Resolve dependency issues
echo 13. System Information - Display system information
echo 14. Exit
echo.

set "choice="
set /p "choice=Enter your choice (1-14): "
if defined choice set "choice=%choice: =%"
if not defined choice (
    echo [ERROR] No input provided
    timeout /t 2 >nul
    goto main_menu
)

if "%choice%"=="1" goto health_check
if "%choice%"=="2" goto setup_env
if "%choice%"=="3" goto start_dev
if "%choice%"=="4" goto run_tests
if "%choice%"=="5" goto git_management
if "%choice%"=="6" goto training_setup
if "%choice%"=="7" goto training_manager
if "%choice%"=="8" goto cli_tools
if "%choice%"=="9" goto model_management
if "%choice%"=="10" goto data_analysis
if "%choice%"=="11" goto emergency_git_fix
if "%choice%"=="12" goto fix_dependencies
if "%choice%"=="13" goto system_info
if "%choice%"=="14" goto end_script

echo [ERROR] Invalid choice '%choice%'. Please enter 1-14.
timeout /t 2 >nul
goto main_menu

:: Model Management Function
:model_management
echo.
echo [INFO] AI Model Management
echo.
echo Available Model Management Options:
echo.
echo 1. List All Models - Show all available AI models
echo 2. Model Health Check - Check status of all models
echo 3. DNA Chain Management - Manage DNA data chains
echo 4. Model Performance Report - Generate model performance report
echo 5. Back to Main Menu
echo.

set "model_choice="
set /p "model_choice=Enter your choice (1-5): "
if defined model_choice set "model_choice=%model_choice: =%"
if not defined model_choice (
    echo [ERROR] No input provided
    timeout /t 2 >nul
    goto model_management
)

if "%model_choice%"=="1" goto list_all_models
if "%model_choice%"=="2" goto model_health_check
if "%model_choice%"=="3" goto dna_chain_management
if "%model_choice%"=="4" goto model_performance_report
if "%model_choice%"=="5" goto main_menu

echo [ERROR] Invalid choice '%model_choice%'. Please enter 1-5.
timeout /t 2 >nul
goto model_management

:: List All Models Function
:list_all_models
echo.
echo [INFO] Listing All AI Models...
echo.
cd /d %~dp0packages\cli
if exist "cli/ai_models_cli.py" (
    echo Running: python cli/ai_models_cli.py list
    echo.
    python cli/ai_models_cli.py list
) else (
    echo [ERROR] AI Models CLI script not found
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
echo.
cd /d %~dp0packages\cli
if exist "cli/ai_models_cli.py" (
    echo Running: python cli/ai_models_cli.py health
    echo.
    python cli/ai_models_cli.py health
) else (
    echo [ERROR] AI Models CLI script not found
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
echo 1. List DNA Chains - Show all DNA data chains
echo 2. Create DNA Chain - Create a new DNA data chain
echo 3. View DNA Chain Details - View details of a specific DNA chain
echo 4. Merge DNA Chains - Merge two DNA chains
echo 5. Back to Model Management
echo.

set "dna_choice="
set /p "dna_choice=Enter your choice (1-5): "
if defined dna_choice set "dna_choice=%dna_choice: =%"
if not defined dna_choice (
    echo [ERROR] No input provided
    timeout /t 2 >nul
    goto dna_chain_management
)

if "%dna_choice%"=="1" goto list_dna_chains
if "%dna_choice%"=="2" goto create_dna_chain
if "%dna_choice%"=="3" goto view_dna_chain
if "%dna_choice%"=="4" goto merge_dna_chains
if "%dna_choice%"=="5" goto model_management

echo [ERROR] Invalid choice '%dna_choice%'. Please enter 1-5.
timeout /t 2 >nul
goto dna_chain_management

:: List DNA Chains Function
:list_dna_chains
echo.
echo [INFO] Listing DNA Data Chains...
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
echo.
set /p "chain_name=Enter DNA chain name: "
if defined chain_name (
    echo Creating DNA chain: %chain_name%
    echo TODO: Implement DNA chain creation functionality
) else (
    echo [ERROR] No chain name provided
)
echo.
echo Press any key to return to DNA chain management menu...
pause >nul
goto dna_chain_management

:: View DNA Chain Details Function
:view_dna_chain
echo.
echo [INFO] Viewing DNA Chain Details...
echo.
set /p "chain_name=Enter DNA chain name: "
if defined chain_name (
    echo Viewing DNA chain: %chain_name%
    echo TODO: Implement DNA chain viewing functionality
) else (
    echo [ERROR] No chain name provided
)
echo.
echo Press any key to return to DNA chain management menu...
pause >nul
goto dna_chain_management

:: Merge DNA Chains Function
:merge_dna_chains
echo.
echo [INFO] Merging DNA Chains...
echo.
set /p "chain1=Enter first DNA chain name: "
set /p "chain2=Enter second DNA chain name: "
if defined chain1 if defined chain2 (
    echo Merging DNA chains: %chain1% and %chain2%
    echo TODO: Implement DNA chain merging functionality
) else (
    echo [ERROR] Both chain names must be provided
)
echo.
echo Press any key to return to DNA chain management menu...
pause >nul
goto dna_chain_management

:: Model Performance Report Function
:model_performance_report
echo.
echo [INFO] Generating Model Performance Report...
echo.
echo TODO: Implement model performance reporting functionality
echo.
echo Press any key to return to model management menu...
pause >nul
goto model_management

:: Data Analysis Function
:data_analysis
echo.
echo [INFO] Project Data Analysis
echo.
echo Available Data Analysis Options:
echo.
echo 1. Code Analysis - Analyze code structure and complexity
echo 2. Training Data Statistics - Show training data statistics
echo 3. Model Usage Statistics - Show model usage statistics
echo 4. Performance Metrics - Show system performance metrics
echo 5. Back to Main Menu
echo.

set "data_choice="
set /p "data_choice=Enter your choice (1-5): "
if defined data_choice set "data_choice=%data_choice: =%"
if not defined data_choice (
    echo [ERROR] No input provided
    timeout /t 2 >nul
    goto data_analysis
)

if "%data_choice%"=="1" goto code_analysis
if "%data_choice%"=="2" goto training_data_stats
if "%data_choice%"=="3" goto model_usage_stats
if "%data_choice%"=="4" goto performance_metrics
if "%data_choice%"=="5" goto main_menu

echo [ERROR] Invalid choice '%data_choice%'. Please enter 1-5.
timeout /t 2 >nul
goto data_analysis

:: Code Analysis Function
:code_analysis
echo.
echo [INFO] Performing Code Analysis...
echo.
echo TODO: Implement code analysis functionality
echo.
echo Press any key to return to data analysis menu...
pause >nul
goto data_analysis

:: Training Data Statistics Function
:training_data_stats
echo.
echo [INFO] Showing Training Data Statistics...
echo.
echo TODO: Implement training data statistics functionality
echo.
echo Press any key to return to data analysis menu...
pause >nul
goto data_analysis

:: Model Usage Statistics Function
:model_usage_stats
echo.
echo [INFO] Showing Model Usage Statistics...
echo.
echo TODO: Implement model usage statistics functionality
echo.
echo Press any key to return to data analysis menu...
pause >nul
goto data_analysis

:: Performance Metrics Function
:performance_metrics
echo.
echo [INFO] Showing Performance Metrics...
echo.
echo TODO: Implement performance metrics functionality
echo.
echo Press any key to return to data analysis menu...
pause >nul
goto data_analysis

:: System Information Function
:system_info
echo.
echo [INFO] System Information
echo.
echo Unified AI Project Enhanced Management Tool
echo Version: 2.0.0
echo.
echo System Information:
echo =================
systeminfo | findstr /C:"OS Name" /C:"OS Version" /C:"System Type" /C:"Total Physical Memory"
echo.
echo Python Version:
python --version 2>nul || echo Python not found
echo.
echo Node.js Version:
node --version 2>nul || echo Node.js not found
echo.
echo Git Version:
git --version 2>nul || echo Git not found
echo.
echo Project Directory: %~dp0
echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu

:: CLI Tools Function
:cli_tools
echo.
echo [INFO] Unified AI CLI Tools
echo.
echo Available CLI Tools:
echo.
echo 1. Unified CLI - General AI interactions
echo 2. AI Models CLI - Model management and interactions
echo 3. HSP CLI - Hyper-Structure Protocol tools
echo 4. CLI Runner - Dedicated CLI tool launcher
echo 5. Back to Main Menu
echo.

set "cli_choice="
set /p "cli_choice=Enter your choice (1-5): "
if defined cli_choice set "cli_choice=%cli_choice: =%"
if not defined cli_choice (
    echo [ERROR] No input provided
    timeout /t 2 >nul
    goto cli_tools
)

if "%cli_choice%"=="1" goto unified_cli
if "%cli_choice%"=="2" goto ai_models_cli
if "%cli_choice%"=="3" goto hsp_cli
if "%cli_choice%"=="4" goto cli_runner
if "%cli_choice%"=="5" goto main_menu

echo [ERROR] Invalid choice '%cli_choice%'. Please enter 1-5.
timeout /t 2 >nul
goto cli_tools

:: CLI Runner Function
:cli_runner
echo.
echo [INFO] Starting CLI Runner...
echo.
if exist "tools\cli-runner.bat" (
    call tools\cli-runner.bat
) else (
    echo [ERROR] CLI Runner script not found
    echo.
    echo Press any key to return to CLI tools menu...
    pause >nul
)
goto cli_tools

:: Unified CLI Function
:unified_cli
echo.
echo [INFO] Starting Unified CLI...
echo.
cd /d %~dp0packages\cli
if exist "cli/unified_cli.py" (
    echo Running: python cli/unified_cli.py --help
    echo.
    python cli/unified_cli.py --help
    echo.
    echo Enter CLI command (or press Enter to return to menu):
    echo Example: health, chat "Hello", analyze --code "def x(): pass"
    echo.
    set /p "cli_cmd=Command: "
    if defined cli_cmd (
        echo.
        echo Running: python cli/unified_cli.py %cli_cmd%
        echo.
        python cli/unified_cli.py %cli_cmd%
    )
) else (
    echo [ERROR] Unified CLI script not found
)
cd ..\..\..
echo.
echo Press any key to return to CLI tools menu...
pause >nul
goto cli_tools

:: AI Models CLI Function
:ai_models_cli
echo.
echo [INFO] Starting AI Models CLI...
echo.
cd /d %~dp0packages\cli
if exist "cli/ai_models_cli.py" (
    echo Running: python cli/ai_models_cli.py --help
    echo.
    python cli/ai_models_cli.py --help
    echo.
    echo Enter AI Models CLI command (or press Enter to return to menu):
    echo Example: list, health, query "Explain quantum computing"
    echo.
    set /p "ai_cmd=Command: "
    if defined ai_cmd (
        echo.
        echo Running: python cli/ai_models_cli.py %ai_cmd%
        echo.
        python cli/ai_models_cli.py %ai_cmd%
    )
) else (
    echo [ERROR] AI Models CLI script not found
)
cd ..\..\..
echo.
echo Press any key to return to CLI tools menu...
pause >nul
goto cli_tools

:: HSP CLI Function
:hsp_cli
echo.
echo [INFO] Starting HSP CLI...
echo.
cd /d %~dp0packages\cli
if exist "cli/main.py" (
    echo Running: python cli/main.py --help
    echo.
    python cli/main.py --help
    echo.
    echo Enter HSP CLI command (or press Enter to return to menu):
    echo Example: query "Hello", publish_fact "The sky is blue" --confidence 0.9
    echo.
    set /p "hsp_cmd=Command: "
    if defined hsp_cmd (
        echo.
        echo Running: python cli/main.py %hsp_cmd%
        echo.
        python cli/main.py %hsp_cmd%
    )
) else (
    echo [ERROR] HSP CLI script not found
)
cd ..\..\..
echo.
echo Press any key to return to CLI tools menu...
pause >nul
goto cli_tools

:: Health Check Function
:health_check
echo.
echo [INFO] Running Health Check...
echo.
echo Checking system environment...
echo =============================
echo.
echo Python:
python --version 2>nul || echo [ERROR] Python not found
echo.
echo Node.js:
node --version 2>nul || echo [WARNING] Node.js not found
echo.
echo Git:
git --version 2>nul || echo [WARNING] Git not found
echo.
echo Checking project dependencies...
echo ==============================
echo.
cd /d %~dp0
if exist "apps/backend/requirements.txt" (
    echo [INFO] Backend requirements found
) else (
    echo [WARNING] Backend requirements not found
)
echo.
if exist "package.json" (
    echo [INFO] Frontend package.json found
) else (
    echo [WARNING] Frontend package.json not found
)
echo.
echo Running detailed health check...
echo ==============================
echo.
if exist "tools\health-check.bat" (
    call tools\health-check.bat
) else (
    echo [ERROR] Health check script not found
)
echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu

:: Setup Environment Function
:setup_env
echo.
echo [INFO] Setting up Environment...
echo.
echo This will install all required dependencies for the project.
echo.
echo 1. Install Python dependencies
echo 2. Install Node.js dependencies
echo 3. Setup development environment
echo 4. Back to Main Menu
echo.
set /p "setup_choice=Enter your choice (1-4): "
if "%setup_choice%"=="1" goto install_python_deps
if "%setup_choice%"=="2" goto install_node_deps
if "%setup_choice%"=="3" goto setup_dev_env
if "%setup_choice%"=="4" goto main_menu

echo [ERROR] Invalid choice '%setup_choice%'. Please enter 1-4.
timeout /t 2 >nul
goto setup_env

:: Install Python Dependencies Function
:install_python_deps
echo.
echo [INFO] Installing Python Dependencies...
echo.
cd /d %~dp0
if exist "apps/backend/requirements.txt" (
    echo Installing backend dependencies...
    pip install -r apps/backend/requirements.txt
    if !errorlevel! equ 0 (
        echo [SUCCESS] Backend dependencies installed successfully
    ) else (
        echo [ERROR] Failed to install backend dependencies
    )
) else (
    echo [ERROR] Backend requirements file not found
)
echo.
echo Press any key to return to setup menu...
pause >nul
goto setup_env

:: Install Node.js Dependencies Function
:install_node_deps
echo.
echo [INFO] Installing Node.js Dependencies...
echo.
cd /d %~dp0
if exist "package.json" (
    echo Installing frontend dependencies...
    npm install
    if !errorlevel! equ 0 (
        echo [SUCCESS] Frontend dependencies installed successfully
    ) else (
        echo [ERROR] Failed to install frontend dependencies
    )
) else (
    echo [ERROR] package.json not found
)
echo.
echo Press any key to return to setup menu...
pause >nul
goto setup_env

:: Setup Development Environment Function
:setup_dev_env
echo.
echo [INFO] Setting up Development Environment...
echo.
echo TODO: Implement development environment setup functionality
echo.
echo Press any key to return to setup menu...
pause >nul
goto setup_env

:: Start Development Function
:start_dev
echo.
echo [INFO] Starting Development Environment...
echo.
echo Available Development Options:
echo.
echo 1. Start Backend Server
echo 2. Start Frontend Server
echo 3. Start Both Servers
echo 4. Back to Main Menu
echo.
set /p "dev_choice=Enter your choice (1-4): "
if "%dev_choice%"=="1" goto start_backend
if "%dev_choice%"=="2" goto start_frontend
if "%dev_choice%"=="3" goto start_both
if "%dev_choice%"=="4" goto main_menu

echo [ERROR] Invalid choice '%dev_choice%'. Please enter 1-4.
timeout /t 2 >nul
goto start_dev

:: Start Backend Server Function
:start_backend
echo.
echo [INFO] Starting Backend Server...
echo.
cd /d %~dp0apps\backend
if exist "main.py" (
    echo Starting backend server...
    python main.py
) else (
    echo [ERROR] Backend main.py not found
)
echo.
echo Press any key to return to development menu...
pause >nul
goto start_dev

:: Start Frontend Server Function
:start_frontend
echo.
echo [INFO] Starting Frontend Server...
echo.
cd /d %~dp0
if exist "package.json" (
    echo Starting frontend server...
    npm run dev
) else (
    echo [ERROR] package.json not found
)
echo.
echo Press any key to return to development menu...
pause >nul
goto start_dev

:: Start Both Servers Function
:start_both
echo.
echo [INFO] Starting Both Servers...
echo.
echo TODO: Implement starting both servers functionality
echo.
echo Press any key to return to development menu...
pause >nul
goto start_dev

:: Run Tests Function
:run_tests
echo.
echo [INFO] Running Tests...
echo.
echo Available Test Options:
echo.
echo 1. Run All Tests
echo 2. Run Backend Tests
echo 3. Run Frontend Tests
echo 4. Run Specific Test
echo 5. Back to Main Menu
echo.
set /p "test_choice=Enter your choice (1-5): "
if "%test_choice%"=="1" goto run_all_tests
if "%test_choice%"=="2" goto run_backend_tests
if "%test_choice%"=="3" goto run_frontend_tests
if "%test_choice%"=="4" goto run_specific_test
if "%test_choice%"=="5" goto main_menu

echo [ERROR] Invalid choice '%test_choice%'. Please enter 1-5.
timeout /t 2 >nul
goto run_tests

:: Run All Tests Function
:run_all_tests
echo.
echo [INFO] Running All Tests...
echo.
cd /d %~dp0
if exist "tools\run-tests.bat" (
    call tools\run-tests.bat
) else (
    echo [ERROR] Test runner script not found
)
echo.
echo Press any key to return to tests menu...
pause >nul
goto run_tests

:: Run Backend Tests Function
:run_backend_tests
echo.
echo [INFO] Running Backend Tests...
echo.
cd /d %~dp0apps\backend
if exist "tests" (
    echo Running backend tests...
    python -m pytest tests -v
) else (
    echo [ERROR] Backend tests directory not found
)
echo.
echo Press any key to return to tests menu...
pause >nul
goto run_tests

:: Run Frontend Tests Function
:run_frontend_tests
echo.
echo [INFO] Running Frontend Tests...
echo.
cd /d %~dp0
if exist "package.json" (
    echo Running frontend tests...
    npm test
) else (
    echo [ERROR] package.json not found
)
echo.
echo Press any key to return to tests menu...
pause >nul
goto run_tests

:: Run Specific Test Function
:run_specific_test
echo.
echo [INFO] Running Specific Test...
echo.
set /p "test_path=Enter test file or directory path: "
if defined test_path (
    echo Running test: %test_path%
    python -m pytest %test_path% -v
) else (
    echo [ERROR] No test path provided
)
echo.
echo Press any key to return to tests menu...
pause >nul
goto run_tests

:: Git Management Function
:git_management
echo.
echo [INFO] Git Management
echo.
echo Available Git Options:
echo.
echo 1. Git Status
echo 2. Git Add
echo 3. Git Commit
echo 4. Git Push
echo 5. Git Pull
echo 6. Git Log
echo 7. Back to Main Menu
echo.
set /p "git_choice=Enter your choice (1-7): "
if "%git_choice%"=="1" goto git_status
if "%git_choice%"=="2" goto git_add
if "%git_choice%"=="3" goto git_commit
if "%git_choice%"=="4" goto git_push
if "%git_choice%"=="5" goto git_pull
if "%git_choice%"=="6" goto git_log
if "%git_choice%"=="7" goto main_menu

echo [ERROR] Invalid choice '%git_choice%'. Please enter 1-7.
timeout /t 2 >nul
goto git_management

:: Git Status Function
:git_status
echo.
echo [INFO] Git Status
echo.
git status
echo.
echo Press any key to return to Git management menu...
pause >nul
goto git_management

:: Git Add Function
:git_add
echo.
echo [INFO] Git Add
echo.
set /p "add_path=Enter file or directory to add (or . for all): "
if defined add_path (
    git add %add_path%
    if !errorlevel! equ 0 (
        echo [SUCCESS] Files added successfully
    ) else (
        echo [ERROR] Failed to add files
    )
) else (
    echo [ERROR] No path provided
)
echo.
echo Press any key to return to Git management menu...
pause >nul
goto git_management

:: Git Commit Function
:git_commit
echo.
echo [INFO] Git Commit
echo.
set /p "commit_msg=Enter commit message: "
if defined commit_msg (
    git commit -m "%commit_msg%"
    if !errorlevel! equ 0 (
        echo [SUCCESS] Changes committed successfully
    ) else (
        echo [ERROR] Failed to commit changes
    )
) else (
    echo [ERROR] No commit message provided
)
echo.
echo Press any key to return to Git management menu...
pause >nul
goto git_management

:: Git Push Function
:git_push
echo.
echo [INFO] Git Push
echo.
git push
if !errorlevel! equ 0 (
    echo [SUCCESS] Changes pushed successfully
) else (
    echo [ERROR] Failed to push changes
)
echo.
echo Press any key to return to Git management menu...
pause >nul
goto git_management

:: Git Pull Function
:git_pull
echo.
echo [INFO] Git Pull
echo.
git pull
if !errorlevel! equ 0 (
    echo [SUCCESS] Changes pulled successfully
) else (
    echo [ERROR] Failed to pull changes
)
echo.
echo Press any key to return to Git management menu...
pause >nul
goto git_management

:: Git Log Function
:git_log
echo.
echo [INFO] Git Log
echo.
git log --oneline -10
echo.
echo Press any key to return to Git management menu...
pause >nul
goto git_management

:: Training Setup Function
:training_setup
echo.
echo [INFO] Training Setup
echo.
echo Available Training Setup Options:
echo.
echo 1. Generate Training Data
echo 2. Download Training Data
echo 3. Configure Training Environment
echo 4. Back to Main Menu
echo.
set /p "train_setup_choice=Enter your choice (1-4): "
if "%train_setup_choice%"=="1" goto generate_train_data
if "%train_setup_choice%"=="2" goto download_train_data
if "%train_setup_choice%"=="3" goto configure_train_env
if "%train_setup_choice%"=="4" goto main_menu

echo [ERROR] Invalid choice '%train_setup_choice%'. Please enter 1-4.
timeout /t 2 >nul
goto training_setup

:: Generate Training Data Function
:generate_train_data
echo.
echo [INFO] Generating Training Data...
echo.
echo TODO: Implement training data generation functionality
echo.
echo Press any key to return to training setup menu...
pause >nul
goto training_setup

:: Download Training Data Function
:download_train_data
echo.
echo [INFO] Downloading Training Data...
echo.
echo TODO: Implement training data download functionality
echo.
echo Press any key to return to training setup menu...
pause >nul
goto training_setup

:: Configure Training Environment Function
:configure_train_env
echo.
echo [INFO] Configuring Training Environment...
echo.
echo TODO: Implement training environment configuration functionality
echo.
echo Press any key to return to training setup menu...
pause >nul
goto training_setup

:: Training Manager Function
:training_manager
echo.
echo [INFO] Training Manager
echo.
if exist "tools\train-manager.bat" (
    call tools\train-manager.bat
) else (
    echo [ERROR] Training manager script not found
    echo.
    echo Press any key to return to main menu...
    pause >nul
)
goto main_menu

:: Emergency Git Fix Function
:emergency_git_fix
echo.
echo [INFO] Emergency Git Fix
echo.
if exist "tools\emergency-git-fix.bat" (
    call tools\emergency-git-fix.bat
) else (
    echo [ERROR] Emergency Git fix script not found
    echo.
    echo Press any key to return to main menu...
    pause >nul
)
goto main_menu

:: Fix Dependencies Function
:fix_dependencies
echo.
echo [INFO] Fixing Dependencies
echo.
echo Available Dependency Fix Options:
echo.
echo 1. Fix All Dependencies
echo 2. Fix Python Dependencies
echo 3. Fix Node.js Dependencies
echo 4. Recreate Virtual Environment
echo 5. Back to Main Menu
echo.
set /p "fix_deps_choice=Enter your choice (1-5): "
if "%fix_deps_choice%"=="1" goto fix_all_deps
if "%fix_deps_choice%"=="2" goto fix_python_deps
if "%fix_deps_choice%"=="3" goto fix_node_deps
if "%fix_deps_choice%"=="4" goto recreate_venv
if "%fix_deps_choice%"=="5" goto main_menu

echo [ERROR] Invalid choice '%fix_deps_choice%'. Please enter 1-5.
timeout /t 2 >nul
goto fix_dependencies

:: Fix All Dependencies Function
:fix_all_deps
echo.
echo [INFO] Fixing All Dependencies...
echo.
if exist "tools\fix-dependencies.bat" (
    call tools\fix-dependencies.bat
) else (
    echo [ERROR] Fix dependencies script not found
)
echo.
echo Press any key to return to fix dependencies menu...
pause >nul
goto fix_dependencies

:: Fix Python Dependencies Function
:fix_python_deps
echo.
echo [INFO] Fixing Python Dependencies...
echo.
if exist "tools\fix-deps-simple.bat" (
    call tools\fix-deps-simple.bat
) else (
    echo [ERROR] Fix Python dependencies script not found
)
echo.
echo Press any key to return to fix dependencies menu...
pause >nul
goto fix_dependencies

:: Fix Node.js Dependencies Function
:fix_node_deps
echo.
echo [INFO] Fixing Node.js Dependencies...
echo.
echo TODO: Implement Node.js dependencies fix functionality
echo.
echo Press any key to return to fix dependencies menu...
pause >nul
goto fix_dependencies

:: Recreate Virtual Environment Function
:recreate_venv
echo.
echo [INFO] Recreating Virtual Environment...
echo.
if exist "tools\recreate-venv.bat" (
    call tools\recreate-venv.bat
) else (
    echo [ERROR] Recreate virtual environment script not found
)
echo.
echo Press any key to return to fix dependencies menu...
pause >nul
goto fix_dependencies

:: End Script Function
:end_script
echo.
echo [INFO] Exiting Unified AI Project Enhanced Management Tool
echo.
echo Thank you for using Unified AI Project!
echo.
timeout /t 2 >nul
exit /b 0