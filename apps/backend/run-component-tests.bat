@echo off
chcp 65001 >nul 2>&1
echo ================================================
echo AGI Component Diagnostic Test
echo ================================================
echo.

cd /d "D:\Projects\Unified-AI-Project\apps\backend"

echo Running component diagnostic...
echo.

python diagnose_components.py

echo.
echo ================================================
echo Diagnostic completed. Check output above.
echo ================================================
echo.

echo Press any key to run AGI integration test...
pause >nul

echo.
echo ================================================
echo Running AGI Integration Test
echo ================================================
echo.

python test_agi_integration.py

echo.
echo ================================================
echo All tests completed
echo ================================================
echo.

pause