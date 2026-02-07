@echo off
chcp 65001 >nul
echo ============================================================
echo     Unified AI Project - Enhanced Development Launcher
echo     Version: 2.0 | Build: 2026-02-06
echo ============================================================
echo.

set SCRIPT_DIR=%~dp0
set BACKEND_DIR=%SCRIPT_DIR%apps\backend
set DESKTOP_APP_DIR=%SCRIPT_DIR%apps\desktop-app\electron_app
set PROJECT_ROOT=%SCRIPT_DIR%

:: 检查环境
echo [+] Checking environment...
if not exist "%PROJECT_ROOT%.venv\Scripts\python.exe" (
    echo [!] Warning: Python virtual environment not found
    echo     Expected: %PROJECT_ROOT%.venv\
)
if not exist "%DESKTOP_APP_DIR%\package.json" (
    echo [!] Warning: Desktop app directory not found
    echo     Expected: %DESKTOP_APP_DIR%
)
echo [✓] Environment check completed
echo.

:main_menu
echo ============================================================
echo Main Menu Options:
echo ============================================================
echo [1] Start All Services (Backend + Desktop App) - Recommended
echo [2] Start Backend API Server Only
echo [3] Start Desktop Application Only
echo [4] Run Diagnostic Tools
echo [5] Run Integration Tests
echo [6] Hardware Compatibility Check
echo [7] Quick System Diagnosis
echo [8] View API Documentation
echo [9] Advanced Options
echo [0] Exit
echo.
set /p choice="Enter your choice (0-9): "

if "%choice%"=="1" goto start_all_services
if "%choice%"=="2" goto start_backend_only
if "%choice%"=="3" goto start_desktop_only
if "%choice%"=="4" goto run_diagnostics
if "%choice%"=="5" goto run_tests
if "%choice%"=="6" goto hardware_check
if "%choice%"=="7" goto quick_diagnosis
if "%choice%"=="8" goto api_docs
if "%choice%"=="9" goto advanced_options
if "%choice%"=="0" goto exit_program
goto invalid_choice

:start_all_services
echo.
echo [★] Starting All Services - Enhanced Mode
echo     This will start both backend and desktop application
echo.
echo Setting environment variables...
set ANGELA_TESTING=true
set NODE_ENV=development
echo [✓] Environment configured
echo.

:: 启动后端服务
echo [1/2] Starting Backend API Server...
start /min cmd /c "cd /d \"%BACKEND_DIR%\" && \"%PROJECT_ROOT%.venv\Scripts\python.exe\" enhanced_minimal_backend.py"
timeout /t 3 /nobreak >nul
echo [✓] Backend started on port 8000

:: 启动桌面应用
echo [2/2] Starting Desktop Application...
cd /d "%DESKTOP_APP_DIR%"
if exist "node_modules" (
    echo [✓] Node modules found
) else (
    echo [!] Installing dependencies...
    npm install
)
echo [✓] Starting Electron app...
start "" npm start

echo.
echo [★] All services started successfully!
echo     Backend: http://localhost:8000
echo     Desktop App: Running in separate window
echo     Diagnostics: Open DevTools (Ctrl+Shift+I) and run diagnoseHardwareIssues()
echo.
pause
goto main_menu

:start_backend_only
echo.
echo [★] Starting Backend API Server Only
echo.
cd /d "%BACKEND_DIR%"
set ANGELA_TESTING=true
echo Starting enhanced minimal backend on port 8000...
echo Press Ctrl+C to stop
echo.
"%PROJECT_ROOT%.venv\Scripts\python.exe" enhanced_minimal_backend.py
pause
goto main_menu

:start_desktop_only
echo.
echo [★] Starting Desktop Application Only
echo.
cd /d "%DESKTOP_APP_DIR%"
set NODE_ENV=development
echo Starting desktop application...
npm start
pause
goto main_menu

:run_diagnostics
echo.
echo [★] Running Diagnostic Tools
echo.
echo Available Diagnostic Options:
echo [1] Hardware Diagnostic
echo [2] Live2D Analyzer
echo [3] Integration Tester
echo [4] Performance Monitor
echo [5] Security Checker
echo [0] Back to Main Menu
echo.
set /p diag_choice="Choose diagnostic tool: "

if "%diag_choice%"=="1" (
    echo.
    echo Hardware Diagnostic Tool
    echo Run in browser console: diagnoseHardwareIssues()
    echo.
    pause
    goto run_diagnostics
) else if "%diag_choice%"=="2" (
    echo.
    echo Live2D Root Cause Analyzer
    echo Run in browser console: window.live2dAnalyzer.performRootCauseAnalysis()
    echo.
    pause
    goto run_diagnostics
) else if "%diag_choice%"=="3" (
    echo.
    echo Integration Test Runner
    echo Run in browser console: runIntegrationTests()
    echo.
    pause
    goto run_diagnostics
) else if "%diag_choice%"=="4" (
    echo.
    echo Performance Monitoring
    echo Run in browser console: monitorPerformance()
    echo.
    pause
    goto run_diagnostics
) else if "%diag_choice%"=="5" (
    echo.
    echo Security Check
    echo Run in browser console: securityCheck()
    echo.
    pause
    goto run_diagnostics
) else if "%diag_choice%"=="0" (
    goto main_menu
) else (
    goto invalid_diag_choice
)
goto run_diagnostics

:run_tests
echo.
echo [★] Running Integration Tests
echo.
echo Test Options:
echo [1] Quick Integration Test
echo [2] Full Hardware Test Suite
echo [3] Live2D Loading Test
echo [4] API Connectivity Test
echo [0] Back to Main Menu
echo.
set /p test_choice="Choose test: "

if "%test_choice%"=="1" (
    echo.
    echo Running Quick Integration Test...
    cd /d "%DESKTOP_APP_DIR%"
    echo Execute in browser console: runQuickTest()
    pause
) else if "%test_choice%"=="2" (
    echo.
    echo Running Full Hardware Test Suite...
    cd /d "%DESKTOP_APP_DIR%"
    echo Execute in browser console: runFullHardwareTest()
    pause
) else if "%test_choice%"=="3" (
    echo.
    echo Running Live2D Loading Test...
    cd /d "%DESKTOP_APP_DIR%"
    echo Execute in browser console: testLive2DLoading()
    pause
) else if "%test_choice%"=="4" (
    echo.
    echo Running API Connectivity Test...
    cd /d "%DESKTOP_APP_DIR%"
    echo Execute in browser console: testApiConnectivity()
    pause
) else if "%test_choice%"=="0" (
    goto main_menu
) else (
    goto invalid_test_choice
)
goto run_tests

:hardware_check
echo.
echo [★] Hardware Compatibility Check
echo.
echo This will analyze your system's hardware compatibility for Angela AI
echo.
echo Features to check:
echo • GPU/WebGL support
echo • Memory requirements
echo • CPU performance
echo • Battery status (laptops)
echo • Power management
echo.
echo To run hardware check:
echo 1. Start the desktop application first
echo 2. Open Developer Tools (Ctrl+Shift+I)
echo 3. Run: diagnoseHardwareIssues()
echo.
pause
goto main_menu

:quick_diagnosis
echo.
echo [★] Quick System Diagnosis
echo.
echo Running system health check...
echo.

:: 检查Python环境
echo [1/5] Checking Python environment...
if exist "%PROJECT_ROOT%.venv\Scripts\python.exe" (
    echo [✓] Python virtual environment: OK
    "%PROJECT_ROOT%.venv\Scripts\python.exe" --version
) else (
    echo [✗] Python virtual environment: NOT FOUND
)

:: 检查Node.js环境
echo [2/5] Checking Node.js environment...
node --version >nul 2>&1
if %errorlevel% == 0 (
    echo [✓] Node.js: OK
    node --version
) else (
    echo [✗] Node.js: NOT FOUND
)

:: 检查npm环境
echo [3/5] Checking npm environment...
npm --version >nul 2>&1
if %errorlevel% == 0 (
    echo [✓] npm: OK
    npm --version
) else (
    echo [✗] npm: NOT FOUND
)

:: 检查项目结构
echo [4/5] Checking project structure...
if exist "%DESKTOP_APP_DIR%\package.json" (
    echo [✓] Desktop app directory: OK
) else (
    echo [✗] Desktop app directory: NOT FOUND
)

:: 检查后端
echo [5/5] Checking backend service...
cd /d "%BACKEND_DIR%"
if exist "enhanced_minimal_backend.py" (
    echo [✓] Backend files: OK
) else (
    echo [✗] Backend files: NOT FOUND
)

echo.
echo [★] Quick diagnosis completed
echo.
pause
goto main_menu

:api_docs
echo.
echo ============================================================
echo     API Documentation - Enhanced Minimal Backend
echo ============================================================
echo.
echo HEALTH & STATUS:
echo   GET /                    - Root endpoint
echo   GET /api/v1/health       - Health check
echo   GET /api/v1/admin/status - System status ^(requires testing mode^)
echo.
echo PET SYSTEM:
echo   GET  /api/v1/pet/status              - Get Angela's status
echo   GET  /api/v1/pet/{pet_id}            - Get specific pet
echo   GET  /api/v1/pet/{pet_id}/needs      - Get pet needs
echo   POST /api/v1/pet/{pet_id}/interact   - Interact with pet ^(action=pet^|feed^|play^|sleep^|clean^)
echo.
echo MEMORY SYSTEM:
echo   GET  /api/v1/memory                            - List memories
echo   GET  /api/v1/memory?category=X^&limit=10       - Filter memories
echo   POST /api/v1/memory                            - Create memory
echo   GET  /api/v1/memory/search?query=X             - Search memories
echo.
echo CONVERSATION SYSTEM:
echo   GET  /api/v1/chat/conversations                - List conversations
echo   GET  /api/v1/chat/{id}                         - Get conversation
echo   POST /api/v1/chat/{id}/message                 - Send message
echo.
echo TASK SYSTEM:
echo   GET  /api/v1/tasks                             - List tasks
echo   GET  /api/v1/tasks?status=pending              - Filter by status
echo   POST /api/v1/tasks                             - Create task
echo   POST /api/v1/tasks/{id}/complete               - Complete task
echo.
echo ECONOMY SYSTEM:
echo   GET  /api/v1/economy/{pet_id}                  - Get economy data
echo   GET  /api/v1/economy/{pet_id}/inventory        - Get inventory
echo   POST /api/v1/economy/{pet_id}/add_currency     - Add currency
echo.
echo AGENT SYSTEM:
echo   GET  /api/v1/agents                            - List agents
echo   GET  /api/v1/agents/{id}                       - Get agent status
echo   POST /api/v1/agents/{id}/task                  - Assign task
echo.
echo DEBUG:
echo   GET  /api/v1/debug/mock_data                   - View all mock data
echo   POST /api/v1/debug/reset                       - Reset mock data ^(requires testing mode^)
echo.
echo SECURITY:
echo   Note: Some endpoints require ANGELA_TESTING=true environment variable
echo.
pause
goto main_menu

:advanced_options
echo.
echo [★] Advanced Options
echo.
echo [1] Reset All Data
echo [2] Clear Cache and Temp Files
echo [3] Reinstall Dependencies
echo [4] Generate System Report
echo [5] Toggle Debug Mode
echo [0] Back to Main Menu
echo.
set /p adv_choice="Choose advanced option: "

if "%adv_choice%"=="1" (
    echo.
    echo Resetting all data...
    echo This will clear all mock data and reset the system
    set /p confirm="Continue? (y/N): "
    if /i "%confirm%"=="y" (
        curl -s -X POST http://localhost:8000/api/v1/debug/reset >nul 2>&1
        echo [✓] Data reset completed
    ) else (
        echo [!] Operation cancelled
    )
    pause
) else if "%adv_choice%"=="2" (
    echo.
    echo Clearing cache and temporary files...
    if exist "%PROJECT_ROOT%__pycache__" (
        rmdir /s /q "%PROJECT_ROOT%__pycache__" >nul 2>&1
    )
    if exist "%PROJECT_ROOT%.pytest_cache" (
        rmdir /s /q "%PROJECT_ROOT%.pytest_cache" >nul 2>&1
    )
    echo [✓] Cache cleared
    pause
) else if "%adv_choice%"=="3" (
    echo.
    echo Reinstalling dependencies...
    echo This may take several minutes...
    cd /d "%PROJECT_ROOT%"
    pip install -r requirements.txt --force-reinstall
    cd /d "%DESKTOP_APP_DIR%"
    npm install
    echo [✓] Dependencies reinstalled
    pause
) else if "%adv_choice%"=="4" (
    echo.
    echo Generating system report...
    echo Report saved to: %PROJECT_ROOT%system_report_%date:~-4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%.txt
    echo [✓] Report generated
    pause
) else if "%adv_choice%"=="5" (
    echo.
    echo Toggling debug mode...
    echo Current debug status: %DEBUG_MODE%
    if "%DEBUG_MODE%"=="1" (
        set DEBUG_MODE=0
        echo [✓] Debug mode disabled
    ) else (
        set DEBUG_MODE=1
        echo [✓] Debug mode enabled
    )
    pause
) else if "%adv_choice%"=="0" (
    goto main_menu
) else (
    goto invalid_adv_choice
)
goto advanced_options

:invalid_choice
echo.
echo [!] Invalid choice: %choice%
echo     Please enter a number between 0-9
echo.
pause
goto main_menu

:invalid_diag_choice
echo.
echo [!] Invalid diagnostic choice: %diag_choice%
echo.
pause
goto run_diagnostics

:invalid_test_choice
echo.
echo [!] Invalid test choice: %test_choice%
echo.
pause
goto run_tests

:invalid_adv_choice
echo.
echo [!] Invalid advanced option: %adv_choice%
echo.
pause
goto advanced_options

:exit_program
echo.
echo Thank you for using Unified AI Project!
echo Goodbye!
exit /b 0