# Unified-AI-Project 增强备份恢复脚本
# 提供更安全、更完整的备份和恢复功能

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("backup", "restore", "list", "verify")]
    [string]$Action = "backup",
    
    [Parameter(Mandatory=$false)]
    [string]$BackupPath = "",
    
    [Parameter(Mandatory=$false)]
    [switch]$Force = $false
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Unified AI Project 增强备份恢复工具" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 获取项目根目录
$projectRoot = Get-Location
Write-Host "项目根目录: $projectRoot" -ForegroundColor Yellow

# 定义需要备份的目录和文件模式
$backupPatterns = @(
    "apps/",
    "packages/",
    "training/",
    "tools/",
    "scripts/",
    "docs/",
    "configs/",
    "*.md",
    "package.json",
    "pnpm-workspace.yaml",
    "requirements.txt",
    "README.md"
)

# 定义排除的文件和目录模式
$excludePatterns = @(
    "node_modules/",
    "venv/",
    ".git/",
    "__pycache__/",
    ".pytest_cache/",
    "*.log",
    "*.tmp",
    "*.bak",
    "backups/",
    "snapshots/",
    "full_recovery_backup/"
)

# 默认备份目录
if (-not $BackupPath) {
    $BackupPath = Join-Path $projectRoot "backups"
}

# 确保备份目录存在
if (!(Test-Path $BackupPath)) {
    New-Item -ItemType Directory -Path $BackupPath -Force | Out-Null
    Write-Host "创建备份目录: $BackupPath" -ForegroundColor Green
}

function Get-Timestamp {
    return Get-Date -Format "yyyyMMdd_HHmmss"
}

function Get-BackupList {
    param(
        [string]$Path = $BackupPath
    )
    
    Write-Host "可用备份列表:" -ForegroundColor Cyan
    Write-Host "----------------------------------------" -ForegroundColor Gray
    
    $backups = Get-ChildItem -Path $Path -Directory | Sort-Object CreationTime -Descending
    if ($backups.Count -eq 0) {
        Write-Host "没有找到备份" -ForegroundColor Yellow
        return
    }
    
    foreach ($backup in $backups) {
        $size = (Get-ChildItem -Path $backup.FullName -Recurse | Measure-Object -Property Length -Sum).Sum
        $sizeMB = [math]::Round($size / 1MB, 2)
        Write-Host "$($backup.Name) - $($backup.CreationTime) - $($sizeMB) MB" -ForegroundColor White
    }
}

function Test-BackupIntegrity {
    param(
        [string]$BackupDir
    )
    
    Write-Host "验证备份完整性: $BackupDir" -ForegroundColor Cyan
    Write-Host "----------------------------------------" -ForegroundColor Gray
    
    if (!(Test-Path $BackupDir)) {
        Write-Host "备份目录不存在: $BackupDir" -ForegroundColor Red
        return $false
    }
    
    # 检查关键文件是否存在
    $criticalFiles = @(
        "package.json",
        "README.md",
        "apps/",
        "packages/",
        "training/"
    )
    
    $missingFiles = @()
    foreach ($file in $criticalFiles) {
        $filePath = Join-Path $BackupDir $file
        if (!(Test-Path $filePath)) {
            $missingFiles += $file
        }
    }
    
    if ($missingFiles.Count -eq 0) {
        Write-Host "✓ 备份完整性验证通过" -ForegroundColor Green
        return $true
    } else {
        Write-Host "✗ 发现缺失的文件:" -ForegroundColor Red
        foreach ($file in $missingFiles) {
            Write-Host "  - $file" -ForegroundColor Red
        }
        return $false
    }
}

function Start-Backup {
    param(
        [string]$Destination = $BackupPath,
        [bool]$ForceBackup = $false
    )
    
    $timestamp = Get-Timestamp
    $backupName = "backup_$timestamp"
    $backupDir = Join-Path $Destination $backupName
    
    Write-Host "开始创建备份: $backupName" -ForegroundColor Cyan
    Write-Host "目标目录: $backupDir" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Gray
    
    # 检查是否已存在同名备份
    if (Test-Path $backupDir) {
        if (-not $ForceBackup) {
            Write-Host "备份已存在: $backupName" -ForegroundColor Yellow
            $confirm = Read-Host "是否覆盖? (y/N)"
            if ($confirm -ne 'y' -and $confirm -ne 'Y') {
                Write-Host "备份操作已取消" -ForegroundColor Yellow
                return
            }
        }
        Remove-Item -Path $backupDir -Recurse -Force
    }
    
    # 创建备份目录
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    
    # 复制文件
    $copiedCount = 0
    $errorCount = 0
    
    foreach ($pattern in $backupPatterns) {
        Write-Host "处理模式: $pattern" -ForegroundColor Gray
        
        try {
            $items = Get-ChildItem -Path $projectRoot -Recurse -Include $pattern -ErrorAction SilentlyContinue
            
            # 排除不需要的文件
            $items = $items | Where-Object {
                $itemPath = $_.FullName.Replace($projectRoot, "")
                $shouldExclude = $false
                foreach ($exclude in $excludePatterns) {
                    if ($itemPath -like "*$exclude*") {
                        $shouldExclude = $true
                        break
                    }
                }
                -not $shouldExclude
            }
            
            foreach ($item in $items) {
                try {
                    $relativePath = $item.FullName.Replace($projectRoot, "").TrimStart("\")
                    $destPath = Join-Path $backupDir $relativePath
                    
                    # 创建目标目录
                    $destDir = Split-Path -Path $destPath -Parent
                    if (!(Test-Path $destDir)) {
                        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
                    }
                    
                    # 复制文件或目录
                    if ($item.PSIsContainer) {
                        # 对于目录，创建空目录
                        if (!(Test-Path $destPath)) {
                            New-Item -ItemType Directory -Path $destPath -Force | Out-Null
                        }
                    } else {
                        Copy-Item -Path $item.FullName -Destination $destPath -Force
                    }
                    
                    $copiedCount++
                    if ($copiedCount % 100 -eq 0) {
                        Write-Host "已复制 $copiedCount 个文件..." -ForegroundColor Gray
                    }
                } catch {
                    Write-Host "复制文件失败: $($item.FullName) - $($_.Exception.Message)" -ForegroundColor Red
                    $errorCount++
                }
            }
        } catch {
            Write-Host "处理模式失败: $pattern - $($_.Exception.Message)" -ForegroundColor Red
            $errorCount++
        }
    }
    
    # 创建备份信息文件
    $backupInfo = @{
        "timestamp" = $timestamp
        "project_root" = $projectRoot
        "backup_name" = $backupName
        "files_copied" = $copiedCount
        "errors" = $errorCount
        "backup_patterns" = $backupPatterns
        "exclude_patterns" = $excludePatterns
    }
    
    $backupInfoPath = Join-Path $backupDir "backup_info.json"
    $backupInfo | ConvertTo-Json | Out-File -FilePath $backupInfoPath -Encoding UTF8
    
    Write-Host "----------------------------------------" -ForegroundColor Gray
    Write-Host "备份完成!" -ForegroundColor Green
    Write-Host "备份名称: $backupName" -ForegroundColor White
    Write-Host "文件数量: $copiedCount" -ForegroundColor White
    if ($errorCount -gt 0) {
        Write-Host "错误数量: $errorCount" -ForegroundColor Yellow
    }
    Write-Host "备份目录: $backupDir" -ForegroundColor White
}

function Start-Restore {
    param(
        [string]$BackupName,
        [string]$Destination = $projectRoot,
        [bool]$ForceRestore = $false
    )
    
    if (-not $BackupName) {
        Write-Host "请指定要恢复的备份名称" -ForegroundColor Red
        Get-BackupList
        return
    }
    
    $backupDir = Join-Path $BackupPath $BackupName
    
    Write-Host "开始恢复备份: $BackupName" -ForegroundColor Cyan
    Write-Host "源目录: $backupDir" -ForegroundColor Yellow
    Write-Host "目标目录: $Destination" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Gray
    
    # 验证备份完整性
    if (-not (Test-BackupIntegrity -BackupDir $backupDir)) {
        if (-not $ForceRestore) {
            Write-Host "备份完整性验证失败，是否继续恢复? (y/N)" -ForegroundColor Yellow
            $confirm = Read-Host
            if ($confirm -ne 'y' -and $confirm -ne 'Y') {
                Write-Host "恢复操作已取消" -ForegroundColor Yellow
                return
            }
        }
    }
    
    # 确认恢复操作
    if (-not $ForceRestore) {
        Write-Host "警告: 恢复操作将覆盖现有文件!" -ForegroundColor Red
        Write-Host "是否继续? (y/N)" -ForegroundColor Yellow
        $confirm = Read-Host
        if ($confirm -ne 'y' -and $confirm -ne 'Y') {
            Write-Host "恢复操作已取消" -ForegroundColor Yellow
            return
        }
    }
    
    # 恢复文件
    $restoredCount = 0
    $errorCount = 0
    
    # 获取备份中的所有文件
    $backupItems = Get-ChildItem -Path $backupDir -Recurse -File
    
    foreach ($item in $backupItems) {
        try {
            $relativePath = $item.FullName.Replace($backupDir, "").TrimStart("\")
            $destPath = Join-Path $Destination $relativePath
            
            # 创建目标目录
            $destDir = Split-Path -Path $destPath -Parent
            if (!(Test-Path $destDir)) {
                New-Item -ItemType Directory -Path $destDir -Force | Out-Null
            }
            
            # 复制文件
            Copy-Item -Path $item.FullName -Destination $destPath -Force
            $restoredCount++
            
            if ($restoredCount % 100 -eq 0) {
                Write-Host "已恢复 $restoredCount 个文件..." -ForegroundColor Gray
            }
        } catch {
            Write-Host "恢复文件失败: $($item.FullName) - $($_.Exception.Message)" -ForegroundColor Red
            $errorCount++
        }
    }
    
    Write-Host "----------------------------------------" -ForegroundColor Gray
    Write-Host "恢复完成!" -ForegroundColor Green
    Write-Host "恢复文件数量: $restoredCount" -ForegroundColor White
    if ($errorCount -gt 0) {
        Write-Host "错误数量: $errorCount" -ForegroundColor Yellow
    }
}

# 主逻辑
switch ($Action) {
    "backup" {
        Start-Backup -Destination $BackupPath -ForceBackup $Force
    }
    "restore" {
        Start-Restore -BackupName $BackupPath -Destination $projectRoot -ForceRestore $Force
    }
    "list" {
        Get-BackupList
    }
    "verify" {
        if (Test-Path $BackupPath) {
            Test-BackupIntegrity -BackupDir $BackupPath
        } else {
            Write-Host "备份目录不存在: $BackupPath" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "操作完成!" -ForegroundColor Green