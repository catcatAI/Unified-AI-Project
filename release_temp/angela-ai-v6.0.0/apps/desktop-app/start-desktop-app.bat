@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Desktop App
color 0A

:: Add error handling and logging (添加錯誤處理和日志記錄)
set "LOG_FILE=%~dp0start-desktop-app-errors.log"
set "SCRIPT_NAME=start-desktop-app.bat"

:: Log script start (記錄腳本啟動)
echo [%date% %time%] Script started: %SCRIPT_NAME% >> "%LOG_FILE%" 2>nul

echo ==========================================
echo   🖥️  Unified AI Project - Desktop App
echo ==========================================
echo.
echo This script starts the Unified AI Project desktop application. (此腳本啟動Unified AI Project桌面應用程序)
echo.
echo Process: (過程)
echo 1. 🧪 Check environment requirements (檢查環境要求)
echo 2. 📦 Install desktop app dependencies (安裝桌面應用依賴)
echo 3. 🚀 Launch desktop application (啟動桌面應用程序)
echo 4. ✅ Verify application status (驗證應用程序狀態)
echo.

:: Check environment requirements (檢查環境要求)
echo.
echo [STEP 1/4] Checking environment requirements... (檢查環境要求)
echo [%date% %time%] Checking environment requirements >> "%LOG_FILE%" 2>nul

:: Check Node.js (檢查Node.js)
where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not installed (未安裝Node.js)
    echo [INFO] Please download from: https://nodejs.org/
    echo [%date% %time%] Node.js not installed >> "%LOG_FILE%" 2>nul
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

:: Check pnpm (檢查pnpm)
where pnpm >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing pnpm... (安裝pnpm)
    echo [%date% %time%] Installing pnpm >> "%LOG_FILE%" 2>nul
    npm install -g pnpm > pnpm_install.log 2>&1
    if errorlevel 1 (
        echo [ERROR] Failed to install pnpm (無法安裝pnpm)
        echo [%date% %time%] Failed to install pnpm >> "%LOG_FILE%" 2>nul
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
)

echo [OK] Environment requirements met (環境要求滿足)

:: Install desktop app dependencies (安裝桌面應用依賴)
echo.
echo [STEP 2/4] Installing desktop app dependencies... (安裝桌面應用依賴)
echo [%date% %time%] Installing desktop app dependencies >> "%LOG_FILE%" 2>nul

:: Check if desktop app directory exists (檢查桌面應用目錄是否存在)
if not exist "..\..\packages\desktop-app" (
    echo [ERROR] Desktop app directory not found (未找到桌面應用目錄)
    echo [%date% %time%] Desktop app directory not found >> "%LOG_FILE%" 2>nul
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

:: Change to desktop app directory (切換到桌面應用目錄)
cd ..\..\packages\desktop-app
if errorlevel 1 (
    echo [ERROR] Failed to change to desktop app directory (無法切換到桌面應用目錄)
    echo [%date% %time%] Failed to change to desktop app directory >> "%LOG_FILE%" 2>nul
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

:: Install dependencies (安裝依賴)
echo [INFO] Installing desktop app dependencies... (安裝桌面應用依賴)
pnpm install > desktop_deps_install.log 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to install desktop app dependencies (無法安裝桌面應用依賴)
    echo [INFO] Check desktop_deps_install.log for details (檢查desktop_deps_install.log獲取詳細信息)
    echo [%date% %time%] Failed to install desktop app dependencies >> "%LOG_FILE%" 2>nul
    cd ..\..\apps\desktop-app
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

echo [OK] Desktop app dependencies installed (桌面應用依賴已安裝)

:: Launch desktop application (啟動桌面應用程序)
echo.
echo [STEP 3/4] Launching desktop application... (啟動桌面應用程序)
echo [%date% %time%] Launching desktop application >> "%LOG_FILE%" 2>nul

:: Start the desktop app (啟動桌面應用)
echo [INFO] Starting desktop application... (啟動桌面應用程序)
start "Desktop App" /min cmd /c "cd /d %~dp0..\..\packages\desktop-app && pnpm start > desktop_app.log 2>&1"

:: Wait a moment for the app to start (等待應用啟動)
timeout /t 3 /nobreak >nul

echo [OK] Desktop application launched (桌面應用程序已啟動)

:: Verify application status (驗證應用程序狀態)
echo.
echo [STEP 4/4] Verifying application status... (驗證應用程序狀態)
echo [%date% %time%] Verifying application status >> "%LOG_FILE%" 2>nul

:: Check if the app is running (檢查應用是否運行)
tasklist | findstr "electron" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Desktop app may not be running (桌面應用可能未運行)
    echo [INFO] Check desktop_app.log for details (檢查desktop_app.log獲取詳細信息)
) else (
    echo [OK] Desktop app is running (桌面應用正在運行)
)

:: Return to original directory (返回原始目錄)
cd ..\..\apps\desktop-app

echo.
echo [SUCCESS] Desktop app started successfully! (桌面應用啟動成功!)
echo [%date% %time%] Desktop app started successfully >> "%LOG_FILE%" 2>nul
echo.
echo Application Information: (應用信息)
echo 🖥️  Desktop App: Running in background (桌面應用: 在後台運行)
echo 📋 Logs: packages/desktop-app/desktop_app.log
echo 🛑 To stop: Use Task Manager to end Electron process (停止: 使用任務管理器結束Electron進程)
echo.
echo Next steps: (下一步)
echo 1. Check your system tray for the app icon (檢查系統托盤中的應用圖標)
echo 2. Open your browser to http://localhost:3000 if needed (如果需要，打開瀏覽器到http://localhost:3000)
echo.

:end_script
echo.
echo Press any key to exit...
pause >nul
exit /b 0