# 專案文件更新工具 - PowerShell版本

function Show-Menu {
    Clear-Host
    Write-Host "===================================" -ForegroundColor Cyan
    Write-Host "專案文件更新工具" -ForegroundColor Cyan
    Write-Host "===================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "請選擇操作:"
    Write-Host "1. 掃描專案並生成文檔更新計畫"
    Write-Host "2. 列出所有文檔及其狀態"
    Write-Host "3. 列出待更新的文檔"
    Write-Host "4. 列出更新中的文檔"
    Write-Host "5. 列出已更新的文檔"
    Write-Host "6. 查看文檔詳細信息"
    Write-Host "7. 更新文檔狀態"
    Write-Host "8. 生成更新報告"
    Write-Host "9. 打開文檔更新指南"
    Write-Host "0. 退出"
    Write-Host ""
}

function Check-Python {
    try {
        $pythonVersion = python --version 2>&1
        return $true
    } catch {
        Write-Host "錯誤: 未找到Python環境，請確保Python已安裝並添加到PATH中。" -ForegroundColor Red
        return $false
    }
}

function Scan-Project {
    Write-Host ""
    Write-Host "正在掃描專案並生成文檔更新計畫..." -ForegroundColor Yellow
    python "$docPlanScript"
    Write-Host ""
    Write-Host "操作完成。" -ForegroundColor Green
    Read-Host "按Enter繼續"
}

function List-AllDocs {
    Write-Host ""
    Write-Host "列出所有文檔及其狀態..." -ForegroundColor Yellow
    python "$docStatusScript" list
    Write-Host ""
    Write-Host "操作完成。" -ForegroundColor Green
    Read-Host "按Enter繼續"
}

function List-PendingDocs {
    Write-Host ""
    Write-Host "列出待更新的文檔..." -ForegroundColor Yellow
    python "$docStatusScript" list --status "待更新"
    Write-Host ""
    Write-Host "操作完成。" -ForegroundColor Green
    Read-Host "按Enter繼續"
}

function List-InProgressDocs {
    Write-Host ""
    Write-Host "列出更新中的文檔..." -ForegroundColor Yellow
    python "$docStatusScript" list --status "更新中"
    Write-Host ""
    Write-Host "操作完成。" -ForegroundColor Green
    Read-Host "按Enter繼續"
}

function List-CompletedDocs {
    Write-Host ""
    Write-Host "列出已更新的文檔..." -ForegroundColor Yellow
    python "$docStatusScript" list --status "已更新"
    Write-Host ""
    Write-Host "操作完成。" -ForegroundColor Green
    Read-Host "按Enter繼續"
}

function Show-DocDetails {
    Write-Host ""
    $docPath = Read-Host "請輸入文檔路徑"
    Write-Host ""
    Write-Host "顯示文檔詳細信息..." -ForegroundColor Yellow
    python "$docStatusScript" show "$docPath"
    Write-Host ""
    Write-Host "操作完成。" -ForegroundColor Green
    Read-Host "按Enter繼續"
}

function Update-DocStatus {
    Write-Host ""
    $docPath = Read-Host "請輸入文檔路徑"
    Write-Host ""
    Write-Host "可用狀態: 待更新, 更新中, 已更新, 需審查, 無需更新" -ForegroundColor Yellow
    $status = Read-Host "請輸入新狀態"
    $notes = Read-Host "請輸入註釋 (可選)"

    if ([string]::IsNullOrEmpty($notes)) {
        python "$docStatusScript" update "$docPath" "$status"
    } else {
        python "$docStatusScript" update "$docPath" "$status" --notes "$notes"
    }

    Write-Host ""
    Write-Host "操作完成。" -ForegroundColor Green
    Read-Host "按Enter繼續"
}

function Generate-Report {
    Write-Host ""
    Write-Host "生成更新報告..." -ForegroundColor Yellow
    python "$docStatusScript" report
    Write-Host ""
    Write-Host "報告已生成: $projectRoot\doc_update_report.md" -ForegroundColor Green
    Write-Host ""
    $openReport = Read-Host "是否打開報告? (y/n)"
    if ($openReport -eq "y") {
        Start-Process "$projectRoot\doc_update_report.md"
    }
    Write-Host "操作完成。" -ForegroundColor Green
    Read-Host "按Enter繼續"
}

function Open-Guide {
    Write-Host ""
    Write-Host "打開文檔更新指南..." -ForegroundColor Yellow
    Start-Process "$projectRoot\DOCUMENT_UPDATE_GUIDE.md"
    Write-Host ""
    Write-Host "操作完成。" -ForegroundColor Green
    Read-Host "按Enter繼續"
}

# 主程序

# 檢查Python環境
if (-not (Check-Python)) {
    exit 1
}

# 設置腳本路徑
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$docPlanScript = Join-Path $projectRoot "scripts\document_update_plan.py"
$docStatusScript = Join-Path $projectRoot "scripts\update_doc_status.py"

# 檢查腳本是否存在
if (-not (Test-Path $docPlanScript)) {
    Write-Host "錯誤: 未找到文檔更新計畫腳本: $docPlanScript" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $docStatusScript)) {
    Write-Host "錯誤: 未找到文檔狀態管理腳本: $docStatusScript" -ForegroundColor Red
    exit 1
}

# 主循環
while ($true) {
    Show-Menu
    $choice = Read-Host "請輸入選項 (0-9)"

    switch ($choice) {
        "1" { Scan-Project }
        "2" { List-AllDocs }
        "3" { List-PendingDocs }
        "4" { List-InProgressDocs }
        "5" { List-CompletedDocs }
        "6" { Show-DocDetails }
        "7" { Update-DocStatus }
        "8" { Generate-Report }
        "9" { Open-Guide }
        "0" { 
            Write-Host ""
            Write-Host "感謝使用專案文件更新工具！" -ForegroundColor Cyan
            Write-Host ""
            exit 0 
        }
        default { 
            Write-Host "無效的選項，請重新選擇。" -ForegroundColor Red
            Start-Sleep -Seconds 2
        }
    }
}