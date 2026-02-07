@echo off
chcp 65001 >nul
echo ============================================================
echo     Unified AI Project - Desktop Shortcut Creator
echo ============================================================
echo.

set SCRIPT_DIR=%~dp0
set LAUNCHER_PATH=%SCRIPT_DIR%enhanced_launcher.bat

echo Creating desktop shortcuts for Unified AI Project...
echo.

:: 获取桌面路径
set DESKTOP_PATH=%USERPROFILE%\Desktop

:: 创建主要快捷方式
echo [1/3] Creating main launcher shortcut...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP_PATH%\Angela AI Launcher.lnk'); $Shortcut.TargetPath = '%LAUNCHER_PATH%'; $Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; $Shortcut.IconLocation = '%LAUNCHER_PATH%'; $Shortcut.Description = 'Unified AI Project Launcher'; $Shortcut.Save()"
if %errorlevel% == 0 (
    echo [✓] Main launcher shortcut created
) else (
    echo [✗] Failed to create main launcher shortcut
)

:: 创建后台服务快捷方式
echo [2/3] Creating backend service shortcut...
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\create_backend_shortcut.vbs"
echo sLinkFile = "%DESKTOP_PATH%\Angela AI Backend.lnk" >> "%TEMP%\create_backend_shortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\create_backend_shortcut.vbs"
echo oLink.TargetPath = "%SCRIPT_DIR%apps\backend\enhanced_minimal_backend.py" >> "%TEMP%\create_backend_shortcut.vbs"
echo oLink.WorkingDirectory = "%SCRIPT_DIR%apps\backend" >> "%TEMP%\create_backend_shortcut.vbs"
echo oLink.Description = "Angela AI Backend Service" >> "%TEMP%\create_backend_shortcut.vbs"
echo oLink.Save >> "%TEMP%\create_backend_shortcut.vbs"
cscript "%TEMP%\create_backend_shortcut.vbs" >nul 2>&1
del "%TEMP%\create_backend_shortcut.vbs"
if exist "%DESKTOP_PATH%\Angela AI Backend.lnk" (
    echo [✓] Backend service shortcut created
) else (
    echo [✗] Failed to create backend service shortcut
)

:: 创建桌面应用快捷方式
echo [3/3] Creating desktop app shortcut...
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\create_desktop_shortcut.vbs"
echo sLinkFile = "%DESKTOP_PATH%\Angela AI Desktop.lnk" >> "%TEMP%\create_desktop_shortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\create_desktop_shortcut.vbs"
echo oLink.TargetPath = "%SYSTEMROOT%\System32\cmd.exe" >> "%TEMP%\create_desktop_shortcut.vbs"
echo oLink.Arguments = "/c cd /d ""%SCRIPT_DIR%apps\desktop-app\electron_app"" && npm start" >> "%TEMP%\create_desktop_shortcut.vbs"
echo oLink.WorkingDirectory = "%SCRIPT_DIR%apps\desktop-app\electron_app" >> "%TEMP%\create_desktop_shortcut.vbs"
echo oLink.Description = "Angela AI Desktop Application" >> "%TEMP%\create_desktop_shortcut.vbs"
echo oLink.Save >> "%TEMP%\create_desktop_shortcut.vbs"
cscript "%TEMP%\create_desktop_shortcut.vbs" >nul 2>&1
del "%TEMP%\create_desktop_shortcut.vbs"
if exist "%DESKTOP_PATH%\Angela AI Desktop.lnk" (
    echo [✓] Desktop app shortcut created
) else (
    echo [✗] Failed to create desktop app shortcut
)

echo.
echo ============================================================
echo Shortcut Creation Summary:
echo ============================================================
echo [✓] Main Launcher: %DESKTOP_PATH%\Angela AI Launcher.lnk
echo [✓] Backend Service: %DESKTOP_PATH%\Angela AI Backend.lnk  
echo [✓] Desktop App: %DESKTOP_PATH%\Angela AI Desktop.lnk
echo.
echo You can now launch Angela AI directly from your desktop!
echo.
pause