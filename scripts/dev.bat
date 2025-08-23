@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

:: Unified AI Project Development Environment Script
:: Usage: dev.bat [action] [options]

set "ACTION=%1"
set "OPTION=%2"

if "%ACTION%"=="" set "ACTION=dev"

echo === Unified AI Project Development Tool ===

goto %ACTION% 2>nul || goto usage

:install
echo Installing project dependencies...
echo Checking Node.js and pnpm...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Node.js not installed or not in PATH
    echo [SOLUTION] Download from: https://nodejs.org/
    exit /b 1
)

pnpm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: pnpm not installed, please run: npm install -g pnpm
    exit /b 1
)

echo Installing Node.js dependencies...
pnpm install
if %errorlevel% neq 0 (
    echo Error: Node.js dependencies installation failed
    exit /b 1
)

echo Setting up Python environment...
cd apps\backend

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python not installed or not in PATH
    echo [SOLUTION] Download from: https://python.org/
    exit /b 1
)

:: Create virtual environment if not exists
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

:: Activate virtual environment and install dependencies
echo Installing Python dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

cd ..\..
echo Dependencies installation completed!
goto end

:dev
echo Starting development environment...

if "%OPTION%"=="backend" goto dev_backend
if "%OPTION%"=="frontend" goto dev_frontend
if "%OPTION%"=="desktop" goto dev_desktop

:: Start backend and frontend by default
echo Starting backend and frontend services...
start "Backend" cmd /k "cd /d "%~dp0..\apps\backend" && call venv\Scripts\activate.bat && python start_chroma_server.py"
timeout /t 3 /nobreak >nul
start "API Server" cmd /k "cd /d "%~dp0..\apps\backend" && call venv\Scripts\activate.bat && uvicorn src.services.main_api_server:app --reload --host 0.0.0.0 --port 8000"
start "Frontend" cmd /k "cd /d "%~dp0..\" && pnpm --filter frontend-dashboard dev"

echo Development services started:
echo - Backend API: http://localhost:8000
echo - Frontend Dashboard: http://localhost:3000
echo - ChromaDB: http://localhost:8001
echo.
echo Press any key to stop all services...
pause >nul
goto stop

:dev_backend
echo Starting backend services...
start "Backend" cmd /k "cd /d "%~dp0..\apps\backend" && call venv\Scripts\activate.bat && python start_chroma_server.py"
timeout /t 3 /nobreak >nul
start "API Server" cmd /k "cd /d "%~dp0..\apps\backend" && call venv\Scripts\activate.bat && uvicorn src.services.main_api_server:app --reload --host 0.0.0.0 --port 8000"
echo Backend services started: http://localhost:8000
echo Press any key to stop services...
pause >nul
goto stop

:dev_frontend
echo Starting frontend services...
start "Frontend" cmd /k "cd /d "%~dp0..\" && pnpm --filter frontend-dashboard dev"
echo Frontend services started: http://localhost:3000
echo Press any key to stop services...
pause >nul
goto stop

:dev_desktop
echo Starting desktop application...
start "Desktop App" cmd /k "cd /d "%~dp0..\" && pnpm --filter desktop-app start"
echo Desktop application started
echo Press any key to stop application...
pause >nul
goto stop

:test
echo Running project tests...

if "%OPTION%"=="backend" goto test_backend
if "%OPTION%"=="frontend" goto test_frontend
if "%OPTION%"=="desktop" goto test_desktop
if "%OPTION%"=="coverage" goto test_coverage

:: Run all tests
echo Running backend tests...
cd apps\backend
call venv\Scripts\activate.bat
pytest --tb=short -v
set "BACKEND_RESULT=%errorlevel%"
cd ..\..

echo Running frontend tests...
pnpm --filter frontend-dashboard test
set "FRONTEND_RESULT=%errorlevel%"

echo Running desktop application tests...
pnpm --filter desktop-app test
set "DESKTOP_RESULT=%errorlevel%"

echo.
echo === Test Results ===
if %BACKEND_RESULT% equ 0 (echo [PASS] Backend tests) else (echo [FAIL] Backend tests)
if %FRONTEND_RESULT% equ 0 (echo [PASS] Frontend tests) else (echo [FAIL] Frontend tests)
if %DESKTOP_RESULT% equ 0 (echo [PASS] Desktop tests) else (echo [FAIL] Desktop tests)
goto end

:test_backend
echo Running backend tests...
cd apps\backend
call venv\Scripts\activate.bat
pytest --tb=short -v
cd ..\..
goto end

:test_frontend
echo Running frontend tests...
pnpm --filter frontend-dashboard test
goto end

:test_desktop
echo Running desktop application tests...
pnpm --filter desktop-app test
goto end

:test_coverage
echo Running test coverage...
cd apps\backend
call venv\Scripts\activate.bat
pytest --cov=src --cov-report=html --cov-report=term-missing
cd ..\..

pnpm --filter frontend-dashboard test:coverage
pnpm --filter desktop-app test:coverage
goto end

:dev-test
echo Starting development environment and test monitoring...
start "Backend" cmd /k "cd /d "%~dp0..\apps\backend" && call venv\Scripts\activate.bat && python start_chroma_server.py"
timeout /t 3 /nobreak >nul
start "API Server" cmd /k "cd /d "%~dp0..\apps\backend" && call venv\Scripts\activate.bat && uvicorn src.services.main_api_server:app --reload --host 0.0.0.0 --port 8000"
start "Frontend" cmd /k "cd /d "%~dp0..\" && pnpm --filter frontend-dashboard dev"

:: Wait for services to start
timeout /t 5 /nobreak >nul

start "Backend Tests" cmd /k "cd /d "%~dp0..\apps\backend" && call venv\Scripts\activate.bat && pytest --tb=short -v --timeout=30 -f"
start "Frontend Tests" cmd /k "cd /d "%~dp0..\" && pnpm --filter frontend-dashboard test --watch"

echo Development environment and test monitoring started
echo - Backend API: http://localhost:8000
echo - Frontend Dashboard: http://localhost:3000
echo - Backend test monitoring is running
echo - Frontend test monitoring is running
echo.
echo Press any key to stop all services...
pause >nul
goto stop

:stop
echo Stopping all services...
taskkill /f /im "python.exe" 2>nul
taskkill /f /im "node.exe" 2>nul
taskkill /f /im "uvicorn.exe" 2>nul
echo All services stopped
goto end

:usage
echo Usage: dev.bat [action] [option]
echo.
echo Actions:
echo   install     - Install all dependencies
echo   dev         - Start development environment
echo   test        - Run tests
echo   dev-test    - Start development environment and test monitoring
echo   stop        - Stop all services
echo.
echo Options:
echo   backend     - Backend only
echo   frontend    - Frontend only
echo   desktop     - Desktop application only
echo   coverage    - Run test coverage (test command only)
echo.
echo Examples:
echo   dev.bat install
echo   dev.bat dev
echo   dev.bat dev backend
echo   dev.bat test coverage
echo   dev.bat dev-test

:end
endlocal