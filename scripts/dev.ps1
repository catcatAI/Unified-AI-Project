# Unified AI Project 开发环境启动脚本
# 支持并行启动、测试和监控

param(
    [string]$Action = "dev",  # dev, test, dev-test, stop
    [switch]$Backend,         # 只启动后端
    [switch]$Frontend,        # 只启动前端
    [switch]$Desktop,         # 只启动桌面应用
    [switch]$Coverage,        # 运行测试覆盖率
    [switch]$Watch           # 监听模式
)

# 颜色输出函数
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "Green")
    Write-Host $Message -ForegroundColor $Color
}

function Write-Error-Message {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Cyan
}

# 检查依赖
function Test-Dependencies {
    Write-Info "检查项目依赖..."
    
    # 检查 Node.js 和 pnpm
    try {
        $nodeVersion = node --version 2>$null
        Write-ColorOutput "✓ Node.js: $nodeVersion"
    } catch {
        Write-Error-Message "✗ Node.js 未安装或不在 PATH 中"
        return $false
    }
    
    try {
        $pnpmVersion = pnpm --version 2>$null
        Write-ColorOutput "✓ pnpm: $pnpmVersion"
    } catch {
        Write-Error-Message "✗ pnpm 未安装，请运行: npm install -g pnpm"
        return $false
    }
    
    # 检查 Python
    try {
        $pythonVersion = python --version 2>$null
        Write-ColorOutput "✓ Python: $pythonVersion"
    } catch {
        Write-Error-Message "✗ Python 未安装或不在 PATH 中"
        return $false
    }
    
    return $true
}

# 安装依赖
function Install-Dependencies {
    Write-Info "安装项目依赖..."
    
    # 安装 Node.js 依赖
    Write-Info "安装 Node.js 依赖..."
    $nodeInstall = Start-Process -FilePath "pnpm" -ArgumentList "install" -Wait -NoNewWindow -PassThru -Timeout 300
    if ($nodeInstall.ExitCode -ne 0) {
        Write-Error-Message "Node.js 依赖安装失败"
        return $false
    }
    
    # 安装 Python 依赖
    Write-Info "安装 Python 依赖..."
    Set-Location "apps\backend"
    
    # 创建虚拟环境（如果不存在）
    if (-not (Test-Path "venv")) {
        Write-Info "创建 Python 虚拟环境..."
        $venvCreate = Start-Process -FilePath "python" -ArgumentList "-m", "venv", "venv" -Wait -NoNewWindow -PassThru -Timeout 120
        if ($venvCreate.ExitCode -ne 0) {
            Write-Error-Message "Python 虚拟环境创建失败"
            Set-Location "..\.."
            return $false
        }
    }
    
    # 激活虚拟环境并安装依赖
    Write-Info "激活虚拟环境并安装依赖..."
    & "venv\Scripts\Activate.ps1"
    
    $pipUpgrade = Start-Process -FilePath "pip" -ArgumentList "install", "--upgrade", "pip" -Wait -NoNewWindow -PassThru -Timeout 120
    if ($pipUpgrade.ExitCode -ne 0) {
        Write-Error-Message "pip 升级失败"
        Set-Location "..\.."
        return $false
    }
    
    # 分别安装 requirements.txt 和 requirements-dev.txt 中的依赖，添加重试机制
    $requirementsFiles = @("requirements.txt", "requirements-dev.txt")
    foreach ($reqFile in $requirementsFiles) {
        Write-Info "安装 $reqFile 中的依赖..."
        $retryCount = 0
        $maxRetries = 3
        $success = $false
        
        while (-not $success -and $retryCount -lt $maxRetries) {
            $pipInstall = Start-Process -FilePath "pip" -ArgumentList "install", "-r", $reqFile, "--timeout", "300" -Wait -NoNewWindow -PassThru
            if ($pipInstall.ExitCode -eq 0) {
                $success = $true
                Write-ColorOutput "✓ $reqFile 依赖安装成功"
            } else {
                $retryCount++
                if ($retryCount -lt $maxRetries) {
                    Write-Info "安装失败，第 $retryCount 次重试..."
                    Start-Sleep -Seconds 10
                } else {
                    Write-Error-Message "✗ $reqFile 依赖安装失败，已重试 $maxRetries 次"
                    Set-Location "..\.."
                    return $false
                }
            }
        }
    }
    
    Set-Location "..\.."
    return $true
}

# 启动后端
function Start-Backend {
    Write-Info "启动后端服务..."
    
    $backendJob = Start-Job -ScriptBlock {
        Set-Location "d:\Projects\Unified-AI-Project\apps\backend"
        & "venv\Scripts\Activate.ps1"
        
        # 启动 ChromaDB 服务器（后台）
        Start-Job -ScriptBlock {
            python start_chroma_server.py
        }
        
        # 等待一秒让 ChromaDB 启动
        Start-Sleep -Seconds 2
        
        # 启动主 API 服务器
        uvicorn src.services.main_api_server:app --reload --host 0.0.0.0 --port 8000
    }
    
    return $backendJob
}

# 启动前端
function Start-Frontend {
    Write-Info "启动前端仪表板..."
    
    $frontendJob = Start-Job -ScriptBlock {
        Set-Location "d:\Projects\Unified-AI-Project"
        pnpm --filter frontend-dashboard dev
    }
    
    return $frontendJob
}

# 启动桌面应用
function Start-Desktop {
    Write-Info "启动桌面应用..."
    
    $desktopJob = Start-Job -ScriptBlock {
        Set-Location "d:\Projects\Unified-AI-Project"
        pnpm --filter desktop-app start
    }
    
    return $desktopJob
}

# 运行测试
function Run-Tests {
    param([switch]$Coverage, [switch]$Watch)
    
    Write-Info "运行项目测试..."
    
    $jobs = @()
    
    # 后端测试
    $backendTestJob = Start-Job -ScriptBlock {
        param($Coverage, $Watch)
        Set-Location "d:\Projects\Unified-AI-Project\apps\backend"
        & "venv\Scripts\Activate.ps1"
        
        if ($Coverage) {
            pytest --cov=src --cov-report=html --cov-report=term-missing
        } elseif ($Watch) {
            pytest --tb=short -v --timeout=30 --maxfail=1 -x
        } else {
            pytest --tb=short -v
        }
    } -ArgumentList $Coverage, $Watch
    
    $jobs += $backendTestJob
    
    # 前端测试
    $frontendTestJob = Start-Job -ScriptBlock {
        param($Coverage, $Watch)
        Set-Location "d:\Projects\Unified-AI-Project"
        
        if ($Coverage) {
            pnpm --filter frontend-dashboard test:coverage
        } elseif ($Watch) {
            pnpm --filter frontend-dashboard test --watch
        } else {
            pnpm --filter frontend-dashboard test
        }
    } -ArgumentList $Coverage, $Watch
    
    $jobs += $frontendTestJob
    
    # 桌面应用测试
    $desktopTestJob = Start-Job -ScriptBlock {
        param($Coverage)
        Set-Location "d:\Projects\Unified-AI-Project"
        
        if ($Coverage) {
            pnpm --filter desktop-app test:coverage
        } else {
            pnpm --filter desktop-app test
        }
    } -ArgumentList $Coverage
    
    $jobs += $desktopTestJob
    
    return $jobs
}

# 停止所有服务
function Stop-AllServices {
    Write-Info "停止所有服务..."
    
    # 停止所有 Python 进程
    Get-Process | Where-Object {$_.ProcessName -like "*python*" -and $_.CommandLine -like "*uvicorn*"} | Stop-Process -Force
    Get-Process | Where-Object {$_.ProcessName -like "*python*" -and $_.CommandLine -like "*chroma*"} | Stop-Process -Force
    
    # 停止所有 Node.js 进程
    Get-Process | Where-Object {$_.ProcessName -like "*node*" -and $_.CommandLine -like "*dev*"} | Stop-Process -Force
    
    # 停止所有后台作业
    Get-Job | Stop-Job
    Get-Job | Remove-Job -Force
    
    Write-ColorOutput "所有服务已停止"
}

# 主执行逻辑
function Main {
    Write-ColorOutput "=== Unified AI Project 开发工具 ===" "Yellow"
    
    # 检查依赖
    if (-not (Test-Dependencies)) {
        Write-Error-Message "依赖检查失败，请安装必要的依赖"
        exit 1
    }
    
    switch ($Action.ToLower()) {
        "install" {
            Install-Dependencies
        }
        
        "dev" {
            Write-Info "启动开发环境..."
            
            $jobs = @()
            
            if ($Backend -or (-not $Frontend -and -not $Desktop)) {
                $jobs += Start-Backend
            }
            
            if ($Frontend -or (-not $Backend -and -not $Desktop)) {
                $jobs += Start-Frontend
            }
            
            if ($Desktop) {
                $jobs += Start-Desktop
            }
            
            # 如果没有指定特定组件，启动后端和前端
            if (-not $Backend -and -not $Frontend -and -not $Desktop) {
                $jobs += Start-Backend
                $jobs += Start-Frontend
            }
            
            Write-ColorOutput "开发服务已启动，按 Ctrl+C 停止"
            Write-Info "后端API: http://localhost:8000"
            Write-Info "前端仪表板: http://localhost:3000"
            
            # 等待用户中断
            try {
                while ($true) {
                    Start-Sleep -Seconds 1
                    
                    # 检查作业状态
                    $failedJobs = $jobs | Where-Object {$_.State -eq "Failed"}
                    if ($failedJobs) {
                        Write-Error-Message "某些服务启动失败："
                        $failedJobs | ForEach-Object {
                            Write-Error-Message "Job ID: $($_.Id)"
                            Receive-Job -Job $_ -ErrorAction SilentlyContinue
                        }
                        break
                    }
                }
            } catch {
                Write-Info "正在停止服务..."
            } finally {
                Stop-AllServices
            }
        }
        
        "test" {
            $testJobs = Run-Tests -Coverage:$Coverage -Watch:$Watch
            
            Write-Info "等待测试完成..."
            $testJobs | Wait-Job
            
            # 显示测试结果
            $testJobs | ForEach-Object {
                Write-Info "=== Job $($_.Id) 结果 ==="
                Receive-Job -Job $_
            }
            
            # 清理作业
            $testJobs | Remove-Job
        }
        
        "dev-test" {
            Write-Info "启动开发环境和测试监控..."
            
            # 启动开发服务（后台）
            $devJobs = @()
            $devJobs += Start-Backend
            $devJobs += Start-Frontend
            
            # 等待服务启动
            Start-Sleep -Seconds 5
            
            # 运行测试（监听模式）
            $testJobs = Run-Tests -Watch
            
            Write-ColorOutput "开发环境和测试监控已启动"
            Write-Info "后端API: http://localhost:8000"
            Write-Info "前端仪表板: http://localhost:3000"
            
            try {
                # 等待用户中断
                while ($true) {
                    Start-Sleep -Seconds 1
                }
            } catch {
                Write-Info "正在停止所有服务..."
            } finally {
                Stop-AllServices
            }
        }
        
        "stop" {
            Stop-AllServices
        }
        
        default {
            Write-ColorOutput "用法: .\dev.ps1 [Action] [Options]" "Yellow"
            Write-Host ""
            Write-Host "Actions:"
            Write-Host "  install     - 安装所有依赖"
            Write-Host "  dev         - 启动开发环境"
            Write-Host "  test        - 运行测试"
            Write-Host "  dev-test    - 同时启动开发环境和测试监控"
            Write-Host "  stop        - 停止所有服务"
            Write-Host ""
            Write-Host "Options:"
            Write-Host "  -Backend    - 只启动后端"
            Write-Host "  -Frontend   - 只启动前端"
            Write-Host "  -Desktop    - 只启动桌面应用"
            Write-Host "  -Coverage   - 运行测试覆盖率"
            Write-Host "  -Watch      - 监听模式"
            Write-Host ""
            Write-Host "示例:"
            Write-Host "  .\dev.ps1 install"
            Write-Host "  .\dev.ps1 dev"
            Write-Host "  .\dev.ps1 dev -Backend"
            Write-Host "  .\dev.ps1 test -Coverage"
            Write-Host "  .\dev.ps1 dev-test"
        }
    }
}

# 执行主函数
Main