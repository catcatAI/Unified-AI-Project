@echo off
cd /d "%~dp0"
echo Starting project repair...
python execute_project_repair.py
echo.
echo Repair completed!
pause