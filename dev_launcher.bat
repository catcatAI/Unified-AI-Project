@echo off
chcp 65001 >nul
echo ============================================================
echo     Unified AI Project - Windows Development Launcher
echo ============================================================
echo.

set SCRIPT_DIR=%~dp0
set BACKEND_DIR=%SCRIPT_DIR%apps\backend
set PROJECT_ROOT=%SCRIPT_DIR%

echo [1] Start Enhanced Minimal Backend (Recommended for dev)
echo [2] Run Comprehensive API Tests
echo [3] Start Frontend Dashboard
echo [4] Run All Tests + Backend
echo [5] Show API Documentation
echo [6] Reset Mock Data
echo [0] Exit
echo.
set /p choice="Enter your choice: "

if "%choice%"=="1" (
    echo.
    echo Starting Enhanced Minimal Backend on port 8000...
    echo Press Ctrl+C to stop
    echo.
    cd /d "%BACKEND_DIR%"
    "%PROJECT_ROOT%.venv\Scripts\python.exe" enhanced_minimal_backend.py
) else if "%choice%"=="2" (
    echo.
    echo Running Comprehensive API Tests...
    echo.
    "%PROJECT_ROOT%.venv\Scripts\python.exe" "%PROJECT_ROOT%test_enhanced_backend.py"
) else if "%choice%"=="3" (
    echo.
    echo Starting Frontend Dashboard on port 3000...
    echo.
    cd /d "%PROJECT_ROOT%apps\frontend-dashboard"
    npm run dev
) else if "%choice%"=="4" (
    echo.
    echo Starting backend and running tests...
    echo.
    start /B cmd /c "%PROJECT_ROOT%.venv\Scripts\python.exe" enhanced_minimal_backend.py"
    timeout /t 5 /nobreak >nul
    "%PROJECT_ROOT%.venv\Scripts\python.exe" "%PROJECT_ROOT%test_enhanced_backend.py"
    taskkill /F /IM python.exe >nul 2>&1
) else if "%choice%"=="5" (
    echo.
    echo ============================================================
    echo     API Documentation - Enhanced Minimal Backend
    echo ============================================================
    echo.
    echo HEALTH & STATUS:
    echo   GET /                    - Root endpoint
    echo   GET /api/v1/health       - Health check
    echo   GET /api/v1/admin/status - System status
    echo.
    echo PET SYSTEM:
    echo   GET  /api/v1/pet/status              - Get Angela's status
    echo   GET  /api/v1/pet/{pet_id}            - Get specific pet
    echo   GET  /api/v1/pet/{pet_id}/needs      - Get pet needs
    echo   POST /api/v1/pet/{pet_id}/interact   - Interact with pet (action=pet^|feed^|play^|sleep^|clean)
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
    echo   POST /api/v1/debug/reset                       - Reset mock data
    echo.
    pause
) else if "%choice%"=="6" (
    echo.
    echo Resetting mock data...
    echo.
    curl -s -X POST http://localhost:8000/api/v1/debug/reset
    echo.
    echo Done.
) else if "%choice%"=="0" (
    echo.
    echo Goodbye!
    exit /b 0
) else (
    echo.
    echo Invalid choice: %choice%
    echo.
)

echo.
pause
