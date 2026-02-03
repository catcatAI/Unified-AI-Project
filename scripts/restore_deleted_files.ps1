# Unified-AI-Project 文件恢复脚本
# 用于恢复被误删的重要文件

Write-Host "开始恢复被误删的文件..." -ForegroundColor Green

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
    "tools/tools/scripts/run_backend_tests.bat",
    "tools/tools/scripts/setup_env.bat",
    "syntax-check.bat",
    "test-all-scripts.bat",
    "test-runner.bat",
    "tools/tools/scripts/dev.bat"
)

# 创建备份目录
$backupDir = "restored_files_backup"
if (!(Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir | Out-Null
    Write-Host "创建备份目录: $backupDir" -ForegroundColor Yellow
}

Write-Host "正在恢复批处理文件..." -ForegroundColor Cyan

# 恢复每个文件
foreach ($file in $filesToRestore) {
    # 检查文件是否已存在
    if (Test-Path $file) {
        Write-Host "文件已存在，跳过: $file" -ForegroundColor Yellow
        continue
    }
    
    # 确保目录存在
    $dir = Split-Path $file -Parent
    if ($dir -and !(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "创建目录: $dir" -ForegroundColor Yellow
    }
    
    # 从Git历史恢复文件
    try {
        git show HEAD~10:$file > $file 2>$null
        if (Test-Path $file) {
            Write-Host "成功恢复文件: $file" -ForegroundColor Green
        } else {
            # 尝试从更早的提交恢复
            git show HEAD~20:$file > $file 2>$null
            if (Test-Path $file) {
                Write-Host "成功恢复文件(从较早提交): $file" -ForegroundColor Green
            } else {
                Write-Host "无法恢复文件: $file" -ForegroundColor Red
            }
        }
    } catch {
        Write-Host "恢复文件时出错: $file" -ForegroundColor Red
    }
}

Write-Host "文件恢复完成!" -ForegroundColor Green
Write-Host "请检查恢复的文件并根据需要进行调整。" -ForegroundColor Cyan