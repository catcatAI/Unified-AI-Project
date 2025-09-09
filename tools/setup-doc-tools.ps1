# 文檔更新工具安裝 - PowerShell版本

Write-Host "===================================" -ForegroundColor Cyan
Write-Host "文檔更新工具安裝" -ForegroundColor Cyan
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

Write-Host "正在檢查並安裝必要的Python套件..." -ForegroundColor Yellow

# 安裝必要的Python套件
try {
    python -m pip install --upgrade pip
    python -m pip install pyyaml colorama tqdm
    
    Write-Host "Python套件安裝成功。" -ForegroundColor Green
} catch {
    Write-Host "錯誤: 安裝Python套件失敗: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "檢查文檔更新工具腳本..." -ForegroundColor Yellow

# 檢查文檔更新工具腳本是否存在
$docPlanScript = Join-Path $projectRoot "scripts\document_update_plan.py"
$docStatusScript = Join-Path $projectRoot "scripts\update_doc_status.py"

if (-not (Test-Path $docPlanScript)) {
    Write-Host "錯誤: 未找到文檔更新計畫腳本: $docPlanScript" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $docStatusScript)) {
    Write-Host "錯誤: 未找到文檔狀態管理腳本: $docStatusScript" -ForegroundColor Red
    exit 1
}

Write-Host "文檔更新工具腳本檢查通過。" -ForegroundColor Green

Write-Host ""
Write-Host "運行測試以確保一切正常..." -ForegroundColor Yellow

# 運行測試腳本
$testScript = Join-Path $projectRoot "scripts\test_doc_tools.py"

if (Test-Path $testScript) {
    try {
        python $testScript
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "測試成功完成！" -ForegroundColor Green
        } else {
            Write-Host "警告: 測試失敗，但將繼續安裝。" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "警告: 測試執行過程中發生錯誤: $_" -ForegroundColor Yellow
        Write-Host "將繼續安裝。" -ForegroundColor Yellow
    }
} else {
    Write-Host "警告: 未找到測試腳本，跳過測試步驟。" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "創建快捷方式..." -ForegroundColor Yellow

# 創建桌面快捷方式
$desktopPath = [System.Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "文檔更新工具.lnk"
$targetPath = Join-Path $projectRoot "update-docs.ps1"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = $targetPath
$Shortcut.WorkingDirectory = $projectRoot
$Shortcut.Description = "專案文件更新工具"
$Shortcut.Save()

Write-Host "桌面快捷方式創建成功。" -ForegroundColor Green

Write-Host ""
Write-Host "安裝完成！" -ForegroundColor Green
Write-Host "您可以通過以下方式啟動文檔更新工具：" -ForegroundColor Cyan
Write-Host "1. 雙擊桌面上的「文檔更新工具」快捷方式" -ForegroundColor White
Write-Host "2. 在專案根目錄執行 update-docs.ps1" -ForegroundColor White
Write-Host "3. 在tools目錄執行 update-docs.ps1" -ForegroundColor White
Write-Host ""
Write-Host "詳細使用說明請參考 $projectRoot\DOCUMENT_UPDATE_GUIDE.md" -ForegroundColor Cyan

Read-Host "按Enter鍵退出"