# Execution Monitor - 執行監控系統

## 概述 | Overview

執行監控系統為統一AI專案提供智能的命令執行監控、超時控制和自動恢復功能。系統能夠檢測終端機響應性、監控系統資源使用情況，並根據歷史執行數據自動調整超時時間。

The Execution Monitor system provides intelligent command execution monitoring, timeout control, and automatic recovery features for the Unified AI Project. It can detect terminal responsiveness, monitor system resource usage, and automatically adjust timeout values based on historical execution data.

## 主要功能 | Key Features

### 🔧 智能執行監控 | Intelligent Execution Monitoring
- **自適應超時控制** - 根據歷史執行時間動態調整超時值
- **終端機響應性檢測** - 實時監控終端機狀態
- **進程健康監控** - 檢測卡住或無響應的進程
- **執行統計分析** - 追蹤成功率、平均執行時間等指標

### 🛡️ 自動恢復機制 | Automatic Recovery
- **智能重試策略** - 失敗時自動重試，支持可配置的重試次數和延遲
- **資源問題檢測** - 監控CPU、記憶體、磁碟使用率
- **問題升級處理** - 自動處理資源瓶頸和系統問題

### 📊 系統健康監控 | System Health Monitoring
- **實時資源監控** - CPU、記憶體、磁碟使用率監控
- **健康報告生成** - 詳細的系統狀態和執行統計報告
- **問題記錄追蹤** - 記錄和分析系統問題歷史

## 快速開始 | Quick Start

### 基本使用 | Basic Usage

```python
from src.core_ai.execution_manager import ExecutionManager

# 創建執行管理器
with ExecutionManager() as manager:
    # 執行命令
    result = manager.execute_command("echo 'Hello World'", timeout=30.0)
    
    print(f"Status: {result.status.value}")
    print(f"Output: {result.stdout}")
    print(f"Execution time: {result.execution_time:.2f}s")
```

### 便捷函數 | Convenience Functions

```python
from src.core_ai.execution_manager import execute_with_smart_monitoring

# 直接執行命令
result = execute_with_smart_monitoring("python script.py", timeout=60.0)
```

### 異步執行 | Async Execution

```python
import asyncio
from src.core_ai.execution_manager import execute_async_with_smart_monitoring

async def run_async_command():
    result = await execute_async_with_smart_monitoring("long_running_command")
    return result

# 運行異步命令
result = asyncio.run(run_async_command())
```

## 命令行工具 | CLI Tools

### 執行監控CLI | Execution Monitor CLI

```bash
# 執行單個命令
python scripts/execution_monitor_cli.py "echo 'Hello World'"

# 設定超時時間
python scripts/execution_monitor_cli.py "python script.py" --timeout 60

# 檢查系統健康狀態
python scripts/execution_monitor_cli.py --health-check

# 啟動連續監控模式
python scripts/execution_monitor_cli.py --monitor --interval 5

# 運行壓力測試
python scripts/execution_monitor_cli.py --stress-test

# 異步執行命令
python scripts/execution_monitor_cli.py "long_command" --async
```

### 測試腳本 | Test Script

```bash
# 運行所有測試
python scripts/test_execution_monitor.py

# 運行演示
python scripts/test_execution_monitor.py --demo

# 運行特定測試
python scripts/test_execution_monitor.py --test test_basic_execution
```

## 配置 | Configuration

### 系統配置文件 | System Configuration

在 `configs/system_config.yaml` 中配置執行監控：

```yaml
operational_configs:
  execution_monitor:
    enabled: true                    # 啟用執行監控
    adaptive_timeout: true           # 啟用自適應超時
    terminal_monitoring: true        # 啟用終端機監控
    resource_monitoring: true        # 啟用資源監控
    auto_recovery: true              # 啟用自動恢復
    
    # 資源閾值
    thresholds:
      cpu_warning: 80.0              # CPU警告閾值（%）
      cpu_critical: 90.0             # CPU危險閾值（%）
      memory_warning: 75.0           # 記憶體警告閾值（%）
      memory_critical: 85.0          # 記憶體危險閾值（%）
    
    # 自適應超時參數
    adaptive_timeout_config:
      history_size: 50               # 執行歷史記錄大小
      timeout_multiplier: 2.5        # 超時倍數
      slow_terminal_multiplier: 1.5  # 慢速終端機超時倍數
    
    # 恢復策略
    recovery_strategies:
      max_retry_attempts: 3          # 最大重試次數
      retry_delay: 5                 # 重試延遲（秒）
      escalation_enabled: true       # 啟用問題升級
```

### 程式化配置 | Programmatic Configuration

```python
from src.core_ai.execution_manager import ExecutionManagerConfig, ExecutionManager

config = ExecutionManagerConfig(
    adaptive_timeout=True,
    terminal_monitoring=True,
    resource_monitoring=True,
    auto_recovery=True,
    default_timeout=30.0,
    max_timeout=300.0,
    cpu_critical=90.0,
    memory_critical=85.0,
    max_retry_attempts=3,
    retry_delay=5.0
)

manager = ExecutionManager(config)
```

## 進階功能 | Advanced Features

### 自適應超時 | Adaptive Timeout

系統會根據歷史執行時間自動調整超時值：

```python
# 系統會學習命令的執行模式
for i in range(10):
    result = manager.execute_command("python data_processing.py")
    # 超時時間會根據歷史數據自動調整
```

### 終端機狀態監控 | Terminal Status Monitoring

```python
# 檢查終端機響應性
terminal_status = manager.monitor.check_terminal_responsiveness()
print(f"Terminal status: {terminal_status.value}")

# 可能的狀態：RESPONSIVE, SLOW, STUCK, UNRESPONSIVE
```

### 系統健康報告 | System Health Report

```python
# 獲取詳細的系統健康報告
health_report = manager.get_system_health_report()

print(f"CPU使用率: {health_report['system_health']['cpu_percent']}%")
print(f"記憶體使用率: {health_report['system_health']['memory_percent']}%")
print(f"成功率: {health_report['execution_stats']['success_rate']:.1%}")
```

### 資源監控和自動恢復 | Resource Monitoring and Auto Recovery

```python
# 啟用資源監控
with ExecutionManager() as manager:
    # 系統會自動監控資源使用情況
    # 當資源使用率過高時會觸發恢復機制
    result = manager.execute_command("memory_intensive_task.py")
```

## 整合指南 | Integration Guide

### 與現有服務整合 | Integration with Existing Services

```python
# 在現有的服務中使用執行監控
from src.core_ai.execution_manager import get_execution_manager

class MyService:
    def __init__(self):
        self.execution_manager = get_execution_manager()
    
    def run_task(self, command):
        return self.execution_manager.execute_command(command)
```

### 與對話管理器整合 | Integration with Dialogue Manager

```python
# 在對話管理器中使用執行監控
from src.core_ai.execution_manager import execute_with_smart_monitoring

class DialogueManager:
    async def execute_tool(self, tool_command):
        result = execute_with_smart_monitoring(
            tool_command, 
            timeout=60.0,
            retry_on_failure=True
        )
        return result
```

## 監控指標 | Monitoring Metrics

### 執行統計 | Execution Statistics

- **total_executions** - 總執行次數
- **successful_executions** - 成功執行次數
- **failed_executions** - 失敗執行次數
- **timeout_executions** - 超時執行次數
- **recovered_executions** - 恢復執行次數
- **success_rate** - 成功率
- **average_execution_time** - 平均執行時間

### 系統健康指標 | System Health Metrics

- **cpu_percent** - CPU使用率
- **memory_percent** - 記憶體使用率
- **disk_percent** - 磁碟使用率
- **terminal_status** - 終端機狀態
- **load_average** - 系統負載平均值

## 故障排除 | Troubleshooting

### 常見問題 | Common Issues

#### 1. 命令執行超時
```bash
# 檢查系統負載
python scripts/execution_monitor_cli.py --health-check

# 調整超時設定
python scripts/execution_monitor_cli.py "your_command" --timeout 120
```

#### 2. 終端機無響應
```bash
# 檢查終端機狀態
python scripts/execution_monitor_cli.py --monitor

# 禁用終端機監控（如果需要）
python scripts/execution_monitor_cli.py "command" --no-terminal-check
```

#### 3. 資源使用率過高
```bash
# 監控資源使用情況
python scripts/execution_monitor_cli.py --monitor --interval 2

# 檢查最近的問題記錄
python scripts/execution_monitor_cli.py --health-check --verbose
```

### 日誌分析 | Log Analysis

執行監控器會記錄詳細的執行信息：

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 啟用詳細日誌
config = ExecutionManagerConfig(log_level="DEBUG")
manager = ExecutionManager(config)
```

## 性能優化 | Performance Optimization

### 最佳實踐 | Best Practices

1. **合理設置超時時間** - 根據命令特性設置適當的超時值
2. **啟用自適應超時** - 讓系統學習和優化超時設置
3. **監控資源使用** - 定期檢查系統健康狀態
4. **使用重試機制** - 對於可能失敗的命令啟用自動重試
5. **定期清理統計** - 在長期運行的應用中定期重置統計信息

### 配置調優 | Configuration Tuning

```python
# 高性能配置
high_performance_config = ExecutionManagerConfig(
    adaptive_timeout=True,
    history_size=100,           # 更大的歷史記錄
    timeout_multiplier=2.0,     # 較小的超時倍數
    max_retry_attempts=2,       # 較少的重試次數
    cpu_critical=95.0,          # 較高的CPU閾值
    memory_critical=90.0        # 較高的記憶體閾值
)

# 穩定性優先配置
stability_config = ExecutionManagerConfig(
    adaptive_timeout=True,
    timeout_multiplier=3.0,     # 較大的超時倍數
    max_retry_attempts=5,       # 更多的重試次數
    cpu_critical=80.0,          # 較低的CPU閾值
    memory_critical=75.0,       # 較低的記憶體閾值
    auto_recovery=True
)
```

## 更新日誌 | Changelog

### v1.0.0 (2024-01)
- ✨ 初始版本發布
- 🔧 基本執行監控功能
- ⏰ 自適應超時控制
- 🖥️ 終端機響應性檢測
- 📊 系統健康監控
- 🛡️ 自動恢復機制
- 🔄 智能重試策略
- 📈 執行統計分析
- 🛠️ 命令行工具
- 📋 詳細配置選項

## 貢獻 | Contributing

歡迎提交問題報告和功能請求！請參考主專案的貢獻指南。

Welcome to submit issue reports and feature requests! Please refer to the main project's contribution guidelines.

## 授權 | License

此模組遵循主專案的授權條款。

This module follows the main project's license terms.