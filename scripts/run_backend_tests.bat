@echo off
REM scripts\run_backend_tests.bat

REM This script runs the backend Python tests on Windows.
REM It navigates to apps\backend where pytest.ini is located.

SETLOCAL ENABLEDELAYEDEXPANSION

SET SCRIPT_DIR=%~dp0
PUSHD "%SCRIPT_DIR%..\apps\backend"

ECHO --- Running Backend Python Tests (Windows) ---

REM Ensure Python is available
python -V >NUL 2>&1
IF ERRORLEVEL 1 (
  ECHO Python is not installed or not in PATH.
  POPD
  EXIT /B 1
)

REM Install minimal test dependencies if a virtual environment is already active
IF EXIST requirements.min.txt (
  ECHO Installing minimal test dependencies...
  python -m pip install -r requirements.min.txt >NUL 2>&1
)

REM Run pytest with config from pytest.ini
python -m pytest

SET EXITCODE=%ERRORLEVEL%
ECHO --- Backend Python Tests Finished with code %EXITCODE% ---

POPD
ENDLOCAL
EXIT /B %EXITCODE%