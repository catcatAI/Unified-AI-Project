# 啟動文檔更新工具 - PowerShell版本

# 獲取當前腳本所在目錄
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 顯示啟動信息
Write-Host "正在啟動專案文件更新工具..." -ForegroundColor Cyan

# 檢查工具腳本是否存在
$toolPath = Join-Path $scriptDir "tools\update-docs.ps1"

if (Test-Path $toolPath) {
    # 執行工具腳本
    & $toolPath
} else {
    # 嘗試執行批處理版本
    $batchToolPath = Join-Path $scriptDir "tools\update-docs.bat"
    
    if (Test-Path $batchToolPath) {
        Write-Host "找到批處理版本的工具，正在啟動..." -ForegroundColor Yellow
        & $batchToolPath
    } else {
        Write-Host "錯誤: 未找到文檔更新工具腳本。" -ForegroundColor Red
        Write-Host "請確保 tools\update-docs.ps1 或 tools\update-docs.bat 文件存在。" -ForegroundColor Red
        Read-Host "按Enter鍵退出"
        exit 1
    }
}