# 备份目录清理脚本
# 定期清理项目中的备份目录，只保留最近的几个重要备份

param(
    [string]$RootPath = ".",
    [int]$KeepDays = 7
)

function Find-BackupDirs {
    param(
        [string]$Path = "."
    )
    
    $backupDirs = @()
    
    # 查找所有可能的备份目录
    Get-ChildItem -Path $Path -Recurse -Directory | ForEach-Object {
        $dirName = $_.Name
        if ($dirName -like "backup*" -or $dirName -like "auto_fix_*" -or $dirName -match "backup_.*") {
            $backupDirs += $_.FullName
        }
    }
    
    return $backupDirs
}

function Should-KeepBackupDir {
    param(
        [string]$DirPath
    )
    
    $dirName = Split-Path $DirPath -Leaf
    
    # 保留特定重要备份目录
    $importantPatterns = @(
        "backup_\d{8}_\d{6}",  # 格式如 backup_20250901_153000
        "backup_archive_\d+"   # 归档备份
    )
    
    foreach ($pattern in $importantPatterns) {
        if ($dirName -match $pattern) {
            return $true
        }
    }
    
    return $false
}

function Cleanup-BackupDirs {
    param(
        [string]$RootPath = ".",
        [int]$KeepDays = 7
    )
    
    Write-Host "备份目录清理工具"
    Write-Host "=================="
    
    $backupDirs = Find-BackupDirs -Path $RootPath
    
    if ($backupDirs.Count -eq 0) {
        Write-Host "未找到备份目录"
        return
    }
    
    Write-Host "找到 $($backupDirs.Count) 个备份目录:"
    $backupDirs | ForEach-Object { Write-Host "  - $_" }
    
    # 确定要删除的目录
    $dirsToDelete = @()
    $dirsToKeep = @()
    
    foreach ($dirPath in $backupDirs) {
        if (Should-KeepBackupDir -DirPath $dirPath) {
            $dirsToKeep += $dirPath
        } else {
            $dirsToDelete += $dirPath
        }
    }
    
    Write-Host "`n将保留 $($dirsToKeep.Count) 个目录:"
    $dirsToKeep | ForEach-Object { Write-Host "  - $_" }
    
    Write-Host "`n将删除 $($dirsToDelete.Count) 个目录:"
    $dirsToDelete | ForEach-Object { Write-Host "  - $_" }
    
    # 确认删除
    if ($dirsToDelete.Count -gt 0) {
        $confirm = Read-Host "`n确认删除这些目录吗? (y/N)"
        if ($confirm -match "^[yY]") {
            foreach ($dirPath in $dirsToDelete) {
                try {
                    Remove-Item -Path $dirPath -Recurse -Force
                    Write-Host "已删除: $dirPath"
                } catch {
                    Write-Host "删除失败 $dirPath: $($_.Exception.Message)"
                }
            }
        } else {
            Write-Host "取消删除操作"
        }
    } else {
        Write-Host "没有需要删除的目录"
    }
}

# 执行清理
Cleanup-BackupDirs -RootPath $RootPath -KeepDays $KeepDays
