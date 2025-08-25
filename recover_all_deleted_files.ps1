# Unified-AI-Project 全面文件恢复脚本
# 用于恢复所有被误删的重要文件

Write-Host "开始全面恢复被误删的文件..." -ForegroundColor Green

# 定义需要恢复的批处理文件列表
$batchFilesToRestore = @(
    "health-check.bat",
    "run-tests.bat", 
    "safe-git-cleanup.bat",
    "setup-training.bat",
    "start-dev.bat",
    "comprehensive-test.bat",
    "quick-dev.bat",
    "run-script-tests.bat",
    "syntax-check.bat",
    "test-all-scripts.bat",
    "test-runner.bat"
)

# 定义需要恢复的脚本目录下的文件
$scriptFilesToRestore = @(
    "scripts/dev.bat",
    "scripts/run_backend_tests.bat",
    "scripts/setup_env.bat"
)

# 定义需要恢复的重要文档
$docsToRestore = @(
    "AUDIO_SERVICE_FIX_REPORT.md",
    "BATCH_FILES_README.md",
    "FINAL_TRAINING_READINESS_REPORT.md",
    "PROJECT_TRAINING_READY.md",
    "READY_FOR_TRAINING.md",
    "TEST_FIXES_SUMMARY.md",
    "TRAINING_READINESS_REPORT.md",
    "docs/BATCH_SCRIPTS_AUDIT_REPORT.md",
    "docs/BATCH_SCRIPTS_FIX_SUMMARY.md",
    "docs/BATCH_SCRIPTS_INTEGRATION_REPORT.md",
    "docs/BATCH_SCRIPTS_TEST_REPORT.md",
    "docs/COMMON_VOICE_PROCESSING_REPORT.md",
    "docs/DEVELOPMENT_GUIDE.md",
    "docs/Documentation_Update_Status.md",
    "docs/FINAL_BAT_CHECK_REPORT.md",
    "docs/FLASH_EXIT_FIX_REPORT.md",
    "docs/GEMINI.md",
    "docs/GIT_10K_SAFE_USAGE_GUIDE.md",
    "docs/GIT_10K_SOLUTION_REPORT.md",
    "docs/IMPLEMENTATION_STATUS.md",
    "docs/MANUAL_TESTING_REQUIRED.md",
    "docs/PLACEHOLDER_REPORT.md",
    "docs/PROJECT_CLEANUP_PLAN.md",
    "docs/PROJECT_STRUCTURE_ANALYSIS.md",
    "docs/PROJECT_TEST_REPORT.md",
    "docs/QUICK_START.md",
    "docs/RECOMMENDATIONS.md",
    "docs/SCRIPTS_USAGE.md",
    "docs/SCRIPT_VERIFICATION_REPORT.md",
    "docs/TESTING_TROUBLESHOOTING.md",
    "docs/TEST_SCRIPTS_USAGE.md",
    "docs/TODO_ANALYSIS.md",
    "docs/TRAINING_SETUP_GUIDE.md"
)

# 尝试从不同历史提交中恢复文件，使用更广泛的提交范围
$commitRefs = @("HEAD~5", "HEAD~10", "HEAD~15", "HEAD~20", "HEAD~25", "HEAD~30", "HEAD~40", "HEAD~50", "HEAD~75", "HEAD~100", "HEAD~150", "HEAD~200")

Write-Host "正在恢复批处理文件..." -ForegroundColor Cyan

# 创建备份目录
$backupDir = "full_recovery_backup"
if (!(Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir | Out-Null
    Write-Host "创建备份目录: $backupDir" -ForegroundColor Yellow
}

# 恢复批处理文件
foreach ($file in $batchFilesToRestore) {
    # 检查文件是否已存在且非空
    if (Test-Path $file) {
        $fileInfo = Get-Item $file
        if ($fileInfo.Length -gt 100) {  # 如果文件大于100字节，认为是完整文件
            Write-Host "文件已存在且非空，跳过: $file" -ForegroundColor Yellow
            continue
        } else {
            Write-Host "文件存在但可能不完整，尝试恢复: $file" -ForegroundColor Cyan
            # 备份现有文件
            Copy-Item $file "$backupDir\$($file.Replace('\', '_'))_before_restore" -Force
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
                if ($content.Trim().Length -gt 100) {  # 如果内容大于100字符，认为是有效内容
                    # 保存内容到文件
                    $content | Out-File -FilePath $file -Encoding UTF8 -Force
                    $fileInfo = Get-Item $file
                    if ($fileInfo.Length -gt 100) {
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
        # 创建占位符文件（如果文件不存在或非常小）
        $fileInfo = Get-Item $file -ErrorAction SilentlyContinue
        if (-not $fileInfo -or $fileInfo.Length -lt 100) {
            "# 恢复失败的文件: $file`n# 请手动恢复此文件" | Out-File -FilePath $file -Encoding UTF8 -Force
        }
    }
}

Write-Host "正在恢复scripts目录下的文件..." -ForegroundColor Cyan

# 恢复scripts目录下的文件
foreach ($file in $scriptFilesToRestore) {
    # 检查文件是否已存在且非空
    if (Test-Path $file) {
        $fileInfo = Get-Item $file
        if ($fileInfo.Length -gt 100) {  # 如果文件大于100字节，认为是完整文件
            Write-Host "文件已存在且非空，跳过: $file" -ForegroundColor Yellow
            continue
        } else {
            Write-Host "文件存在但可能不完整，尝试恢复: $file" -ForegroundColor Cyan
            # 备份现有文件
            Copy-Item $file "$backupDir\$($file.Replace('\', '_'))_before_restore" -Force
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
                if ($content.Trim().Length -gt 100) {  # 如果内容大于100字符，认为是有效内容
                    # 保存内容到文件
                    $content | Out-File -FilePath $file -Encoding UTF8 -Force
                    $fileInfo = Get-Item $file
                    if ($fileInfo.Length -gt 100) {
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
        # 创建占位符文件（如果文件不存在或非常小）
        $fileInfo = Get-Item $file -ErrorAction SilentlyContinue
        if (-not $fileInfo -or $fileInfo.Length -lt 100) {
            "# 恢复失败的文件: $file`n# 请手动恢复此文件" | Out-File -FilePath $file -Encoding UTF8 -Force
        }
    }
}

Write-Host "正在恢复重要文档..." -ForegroundColor Cyan

# 恢复重要文档
foreach ($file in $docsToRestore) {
    # 检查文件是否已存在且非空
    if (Test-Path $file) {
        $fileInfo = Get-Item $file
        if ($fileInfo.Length -gt 100) {  # 如果文件大于100字节，认为是完整文件
            Write-Host "文件已存在且非空，跳过: $file" -ForegroundColor Yellow
            continue
        } else {
            Write-Host "文件存在但可能不完整，尝试恢复: $file" -ForegroundColor Cyan
            # 备份现有文件
            Copy-Item $file "$backupDir\$($file.Replace('\', '_'))_before_restore" -Force
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
                if ($content.Trim().Length -gt 100) {  # 如果内容大于100字符，认为是有效内容
                    # 保存内容到文件
                    $content | Out-File -FilePath $file -Encoding UTF8 -Force
                    $fileInfo = Get-Item $file
                    if ($fileInfo.Length -gt 100) {
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
        # 创建占位符文件（如果文件不存在或非常小）
        $fileInfo = Get-Item $file -ErrorAction SilentlyContinue
        if (-not $fileInfo -or $fileInfo.Length -lt 100) {
            "# 恢复失败的文件: $file`n# 请手动恢复此文件" | Out-File -FilePath $file -Encoding UTF8 -Force
        }
    }
}

Write-Host "文件恢复完成!" -ForegroundColor Green
Write-Host "请检查恢复的文件并根据需要进行调整。" -ForegroundColor Cyan
Write-Host "备份文件保存在: $backupDir" -ForegroundColor Yellow