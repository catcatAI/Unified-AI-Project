# 检查端口状态脚本
Write-Host "检查Unified AI Project端口状态..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# 检查8000端口（后端）
Write-Host "检查端口 8000 (后端API)..." -ForegroundColor Yellow
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($port8000) {
    Write-Host "  端口 8000 已被占用:" -ForegroundColor Red
    $port8000 | Format-Table -Property LocalAddress, LocalPort, RemoteAddress, RemotePort, State, OwningProcess
    # 获取进程信息
    $process = Get-Process -Id $port8000.OwningProcess -ErrorAction SilentlyContinue
    if ($process) {
        Write-Host "  进程名称: $($process.ProcessName)" -ForegroundColor Red
        Write-Host "  进程路径: $($process.Path)" -ForegroundColor Red
    }
} else {
    Write-Host "  端口 8000 未被占用" -ForegroundColor Green
}

Write-Host ""

# 检查3000端口（前端）
Write-Host "检查端口 3000 (前端仪表板)..." -ForegroundColor Yellow
$port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($port3000) {
    Write-Host "  端口 3000 已被占用:" -ForegroundColor Red
    $port3000 | Format-Table -Property LocalAddress, LocalPort, RemoteAddress, RemotePort, State, OwningProcess
    # 获取进程信息
    $process = Get-Process -Id $port3000.OwningProcess -ErrorAction SilentlyContinue
    if ($process) {
        Write-Host "  进程名称: $($process.ProcessName)" -ForegroundColor Red
        Write-Host "  进程路径: $($process.Path)" -ForegroundColor Red
    }
} else {
    Write-Host "  端口 3000 未被占用" -ForegroundColor Green
}

Write-Host ""
Write-Host "检查完成。" -ForegroundColor Green