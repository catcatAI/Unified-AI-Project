# 备份模块目录清理脚本
# 根据项目重构计划，core_ai 已经重构为 core、ai 两个文件夹，
# 因此 backup_modules 目录中的备份文件不再需要，除非用于回溯目的。

Write-Host "备份模块目录清理工具"
Write-Host "=============================="

# 检查 backup_modules 目录是否存在
if (Test-Path "backup_modules") {
    Write-Host "找到 backup_modules 目录"
    
    # 检查是否还有对 backup_modules 的引用
    Write-Host "检查项目中是否还有对 backup_modules 的引用..."
    
    # 搜索 Python 和 Markdown 文件中的引用
    $references = Get-ChildItem -Recurse -Include *.py, *.md | 
                  Where-Object { $_.FullName -notlike "*backup_modules*" } |
                  Select-String -Pattern "backup_modules" -ErrorAction SilentlyContinue |
                  Select-Object Path -Unique
    
    if ($references) {
        Write-Host "发现以下文件中仍有对 backup_modules 的引用:"
        $references | ForEach-Object { Write-Host "  - $($_.Path)" }
        
        Write-Host ""
        Write-Host "根据项目重构计划，core_ai 已经重构为 core、ai 两个文件夹，"
        Write-Host "backup_modules 目录中的备份文件不再需要，除非用于回溯目的。"
        Write-Host "建议先修正这些引用再删除备份目录。"
        
        $confirm = Read-Host "是否仍然要删除 backup_modules 目录? (y/N)"
        if ($confirm -match "^[yY]") {
            Write-Host "删除备份目录: backup_modules"
            Remove-Item -Path "backup_modules" -Recurse -Force
            Write-Host "备份目录删除成功"
        } else {
            Write-Host "取消删除操作"
        }
    } else {
        Write-Host "未发现对 backup_modules 的引用，可以安全删除。"
        Write-Host "删除备份目录: backup_modules"
        Remove-Item -Path "backup_modules" -Recurse -Force
        Write-Host "备份目录删除成功"
    }
} else {
    Write-Host "备份目录不存在"
}

Write-Host ""
Write-Host "清理完成"