# Unified-AI-Project 文件恢复脚本 (版本3)
# 用于恢复被误删的重要文件，从更早的Git历史中恢复

Write-Host "开始恢复被误删的文件(版本3)..." -ForegroundColor Green

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

# 尝试从不同历史提交中恢复文件
$commitRefs = @("HEAD~10", "HEAD~20", "HEAD~30", "HEAD~50")

Write-Host "正在恢复批处理文件..." -ForegroundColor Cyan

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
            # 修复了变量引用问题，使用 {} 包围变量名
            git show ${commitRef}:$file 2>$null > $file
            if (Test-Path $file) {
                $fileInfo = Get-Item $file
                if ($fileInfo.Length -gt 0) {
                    Write-Host "成功从 $commitRef 恢复文件: $file" -ForegroundColor Green
                    $recovered = $true
                    break
                }
            }
        } catch {
            # 继续尝试下一个提交
        }
    }
    
    if (-not $recovered) {
        Write-Host "无法恢复文件: $file" -ForegroundColor Red
    }
}

Write-Host "文件恢复完成!" -ForegroundColor Green
Write-Host "请检查恢复的文件并根据需要进行调整。" -ForegroundColor Cyan