@echo off

:: 啟動文檔更新工具
echo 正在啟動專案文件更新工具...

:: 檢查工具腳本是否存在
if exist "%~dp0tools\update-docs.bat" (
    call "%~dp0tools\update-docs.bat"
) else (
    echo 錯誤: 未找到文檔更新工具腳本。
    echo 請確保 tools\update-docs.bat 文件存在。
    pause
    exit /b 1
)