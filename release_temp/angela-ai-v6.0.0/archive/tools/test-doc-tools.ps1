# 文檔更新工具測試 - PowerShell版本

Write-Host "===================================" -ForegroundColor Cyan
Write-Host "文檔更新工具測試" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

# 檢查Python環境
try {
    $pythonVersion = python --version 2>&1
    Write-Host "檢測到Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "錯誤: 未找到Python環境，請確保Python已安裝並添加到PATH中。" -ForegroundColor Red
    exit 1
}

# 設置腳本路徑
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$testScript = Join-Path $projectRoot "scripts\test_doc_tools.py"

# 檢查測試腳本是否存在
if (-not (Test-Path $testScript)) {
    Write-Host "錯誤: 未找到測試腳本: $testScript" -ForegroundColor Red
    exit 1
}

Write-Host "運行文檔更新工具測試..." -ForegroundColor Yellow
Write-Host ""

try {
    # 運行測試腳本
    python $testScript
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "測試成功完成！文檔更新工具功能正常。" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "測試失敗！請檢查錯誤信息。" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "測試執行過程中發生錯誤: $_" -ForegroundColor Red
    exit 1
}

Read-Host "按Enter鍵退出"