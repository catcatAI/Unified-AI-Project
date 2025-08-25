# Unified-AI-Project 文件恢复脚本 (版本4)
# 用于恢复被误删的重要文件，使用更广泛的Git历史搜索

Write-Host "开始恢复被误删的文件(版本4)..." -ForegroundColor Green

# 定义需要恢复的文件列表
$filesToRestore = @(
    "health-check.bat",
    "run-tests.bat", 
    "safe-git-cleanup.bat",
    "setup-training.bat",
    "start-dev.bat",
    "comprehensive-test.bat",
    "quick-dev.bat",
    "run-script-tests.bat",
    "scripts/run_backend_tests.bat",
    "scripts/setup_env.bat",
    "syntax-check.bat",
    "test-all-scripts.bat",
    "test-runner.bat",
    "scripts/dev.bat"
)

# 尝试从不同历史提交中恢复文件，使用更广泛的提交范围
$commitRefs = @("HEAD~5", "HEAD~10", "HEAD~15", "HEAD~20", "HEAD~25", "HEAD~30", "HEAD~40", "HEAD~50", "HEAD~75", "HEAD~100")

Write-Host "正在恢复批处理文件..." -ForegroundColor Cyan

# 创建备份目录
$backupDir = "restored_files_backup_v4"
if (!(Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir | Out-Null
    Write-Host "创建备份目录: $backupDir" -ForegroundColor Yellow
}

# 恢复每个文件
foreach ($file in $filesToRestore) {
    # 检查文件是否已存在且非空
    if (Test-Path $file) {
        $fileInfo = Get-Item $file
        if ($fileInfo.Length -gt 0) {
            Write-Host "文件已存在且非空，跳过: $file" -ForegroundColor Yellow
            continue
        } else {
            Write-Host "文件存在但为空，尝试恢复: $file" -ForegroundColor Cyan
            # 备份空文件
            Copy-Item $file "$backupDir\$($file.Replace('\', '_'))_empty" -Force
        }
    }
    
    # 确保目录存在
    $dir = Split-Path $file -Parent
    if ($dir -and !(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "创建目录: $dir" -ForegroundColor Yellow
    }
    
    # 尝试从不同历史提交恢复文件
    $recovered = $false
    foreach ($commitRef in $commitRefs) {
        try {
            # 使用更安全的方式调用git show
            $content = git show ${commitRef}:$file 2>$null
            if ($LASTEXITCODE -eq 0 -and $content) {
                # 检查内容是否非空
                if ($content.Trim().Length -gt 0) {
                    # 保存内容到文件
                    $content | Out-File -FilePath $file -Encoding UTF8 -Force
                    $fileInfo = Get-Item $file
                    if ($fileInfo.Length -gt 0) {
                        Write-Host "成功从 $commitRef 恢复文件: $file (大小: $($fileInfo.Length) 字节)" -ForegroundColor Green
                        $recovered = $true
                        # 备份恢复的文件
                        Copy-Item $file "$backupDir\$($file.Replace('\', '_'))_restored" -Force
                        break
                    }
                }
            }
        } catch {
            # 继续尝试下一个提交
            Write-Host "从 $commitRef 恢复失败: $file" -ForegroundColor Gray
        }
    }
    
    if (-not $recovered) {
        Write-Host "无法从历史提交中恢复文件: $file" -ForegroundColor Red
        # 创建占位符文件
        "# 恢复失败的文件: $file`n# 请手动恢复此文件" | Out-File -FilePath $file -Encoding UTF8 -Force
    }
}

Write-Host "文件恢复完成!" -ForegroundColor Green
Write-Host "请检查恢复的文件并根据需要进行调整。" -ForegroundColor Cyan
Write-Host "备份文件保存在: $backupDir" -ForegroundColor Yellow