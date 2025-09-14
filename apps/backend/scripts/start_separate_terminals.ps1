# Unified AI Project - 分离终端启动脚本
# 启动测试和修复在不同终端中显示

param(
    [string]$PytestArgs = ""
)

# 设置项目路径
$projectRoot = "d:\Projects\Unified-AI-Project"
$backendPath = "$projectRoot\apps\backend"

Write-Host "==========================================" -ForegroundColor Yellow
Write-Host "Unified AI Project 分离终端启动器" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Yellow
Write-Host ""

# 启动测试终端 (终端1)
Write-Host "[TERMINAL 1] 启动测试执行终端..." -ForegroundColor Green
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$backendPath'; Write-Host '[TEST TERMINAL] 测试执行终端' -ForegroundColor Green; python scripts/test_runner.py $PytestArgs"
)

# 等待测试终端启动
Start-Sleep -Seconds 3

# 启动分析和修复终端 (终端2)
Write-Host "[TERMINAL 2] 启动错误分析和修复终端..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$backendPath'; Write-Host '[FIX TERMINAL] 错误分析和修复终端' -ForegroundColor Cyan; Write-Host '等待测试结果...' -ForegroundColor Gray; while(`$true) { if(Test-Path 'test_results.json') { Write-Host '[FIX TERMINAL] 检测到测试结果，开始分析...' -ForegroundColor Cyan; python scripts/error_analyzer.py; `$report = Get-Content 'error_report.json' | ConvertFrom-Json; if(`$report.total_errors -gt 0) { Write-Host '[FIX TERMINAL] 发现错误，开始自动修复...' -ForegroundColor Cyan; python scripts/fix_executor.py } else { Write-Host '[FIX TERMINAL] 所有测试通过，无需修复' -ForegroundColor Green } }; Start-Sleep -Seconds 5 }"
)

Write-Host ""
Write-Host "==========================================" -ForegroundColor Yellow
Write-Host "两个终端已启动:" -ForegroundColor Yellow
Write-Host "  终端 1: 测试执行终端" -ForegroundColor Yellow
Write-Host "  终端 2: 错误分析和修复终端" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Yellow