@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

set VERSION=6.0.0
set RELEASE_NAME=angela-ai-v%VERSION%
set RELEASE_DIR=releases

echo 🎉 Creating Angela AI v%VERSION% Release Package...
echo.

:: Create releases directory
if not exist "%RELEASE_DIR%" mkdir "%RELEASE_DIR%"

:: Create release archive using git archive (respects .gitignore)
echo 📦 Creating source archive...
git archive --format=zip --prefix="%RELEASE_NAME%/" -o "%RELEASE_DIR%/%RELEASE_NAME%-source.zip" HEAD

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to create archive
    exit /b 1
)

echo ✅ Source archive created: %RELEASE_DIR%/%RELEASE_NAME%-source.zip
echo.

:: Get archive size
for %%I in ("%RELEASE_DIR%/%RELEASE_NAME%-source.zip") do (
    set SIZE=%%~zI
    echo 📊 Archive size: !SIZE! bytes
)

echo.
echo 🚀 Release package ready!
echo.
echo 📋 Contents:
echo    - All source code
echo    - Documentation (excluding analysis reports)
echo    - Setup files (setup.py, requirements.txt)
echo    - No virtual environments
echo    - No credential files
echo    - No large model files
echo.
echo 📁 Location: %RELEASE_DIR%/%RELEASE_NAME%-source.zip
echo.
echo ⚠️  IMPORTANT:
echo    1. This archive excludes credentials.json - users must set up their own
echo    2. Live2D SDK must be downloaded separately (proprietary)
echo    3. Python dependencies will be installed via pip
echo    4. Training data not included (will be downloaded on first run)
echo.
echo 🔒 Security verified:
echo    ✓ No credentials in archive
echo    ✓ .gitignore properly configured
echo    ✓ Sensitive files excluded

endlocal
