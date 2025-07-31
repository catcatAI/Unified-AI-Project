#!/usr/bin/env python3
"""
Execution Monitor CLI - 執行監控命令行工具
提供終端機執行監控和超時控制的命令行界面

This CLI tool provides terminal execution monitoring and timeout control
with intelligent detection of stuck processes and adaptive timeout management.

此命令行工具提供終端機執行監控和超時控制，具有智能卡住進程檢測和自適應超時管理。
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any

# 添加項目根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core_ai.execution_manager import (
    ExecutionManager, ExecutionManagerConfig, 
    execute_with_smart_monitoring, execute_async_with_smart_monitoring
)
from src.core_ai.execution_monitor import ExecutionStatus, TerminalStatus


def print_banner():
    """打印橫幅"""
    print("=" * 70)
    print("🔧 Unified AI Project - Execution Monitor CLI")
    print("   統一AI專案 - 執行監控命令行工具")
    print("=" * 70)


def print_system_health(health_report: Dict[str, Any]):
    """打印系統健康報告"""
    print("\n📊 System Health Report | 系統健康報告")
    print("-" * 50)
    
    system_health = health_report.get('system_health', {})
    
    # 系統資源
    cpu = system_health.get('cpu_percent', 'N/A')
    memory = system_health.get('memory_percent', 'N/A')
    disk = system_health.get('disk_percent', 'N/A')
    terminal_status = system_health.get('terminal_status', 'N/A')
    
    print(f"🖥️  CPU Usage:      {cpu}%")
    print(f"🧠 Memory Usage:   {memory}%")
    print(f"💾 Disk Usage:     {disk}%")
    print(f"⌨️  Terminal Status: {terminal_status}")
    
    if 'memory_available_gb' in system_health:
        print(f"📊 Available Memory: {system_health['memory_available_gb']:.1f} GB")
    if 'disk_free_gb' in system_health:
        print(f"💿 Free Disk Space: {system_health['disk_free_gb']:.1f} GB")
    
    # 執行統計
    exec_stats = health_report.get('execution_stats', {})
    if exec_stats.get('total_executions', 0) > 0:
        print(f"\n📈 Execution Statistics | 執行統計")
        print(f"   Total Executions: {exec_stats['total_executions']}")
        print(f"   Success Rate: {exec_stats.get('success_rate', 0):.1%}")
        print(f"   Average Time: {exec_stats.get('average_execution_time', 0):.2f}s")
        print(f"   Recovery Rate: {exec_stats.get('recovery_rate', 0):.1%}")
    
    # 最近問題
    recent_issues = health_report.get('recent_issues', [])
    if recent_issues:
        print(f"\n⚠️  Recent Issues | 最近問題 ({len(recent_issues)})")
        for issue in recent_issues[-3:]:  # 顯示最近3個問題
            timestamp = time.strftime('%H:%M:%S', time.localtime(issue['timestamp']))
            print(f"   [{timestamp}] {issue['type']}: {issue.get('resource', 'N/A')} - {issue.get('value', 'N/A')}")


def print_execution_result(result, command: str):
    """打印執行結果"""
    print(f"\n🚀 Execution Result | 執行結果")
    print("-" * 50)
    print(f"Command: {command}")
    print(f"Status: {result.status.value}")
    
    # 狀態圖標
    status_icons = {
        ExecutionStatus.COMPLETED: "✅",
        ExecutionStatus.TIMEOUT: "⏰",
        ExecutionStatus.ERROR: "❌",
        ExecutionStatus.STUCK: "🔄",
        ExecutionStatus.CANCELLED: "🚫"
    }
    
    icon = status_icons.get(result.status, "❓")
    print(f"Result: {icon} {result.status.value.upper()}")
    
    if result.return_code is not None:
        print(f"Return Code: {result.return_code}")
    
    print(f"Execution Time: {result.execution_time:.2f}s")
    print(f"Timeout Used: {result.timeout_used:.2f}s")
    
    if result.terminal_status:
        terminal_icons = {
            TerminalStatus.RESPONSIVE: "🟢",
            TerminalStatus.SLOW: "🟡",
            TerminalStatus.STUCK: "🟠",
            TerminalStatus.UNRESPONSIVE: "🔴"
        }
        terminal_icon = terminal_icons.get(result.terminal_status, "❓")
        print(f"Terminal Status: {terminal_icon} {result.terminal_status.value}")
    
    # 資源使用情況
    if result.resource_usage:
        print(f"Resource Usage:")
        print(f"  CPU: {result.resource_usage.get('cpu_percent', 'N/A')}%")
        print(f"  Memory: {result.resource_usage.get('memory_percent', 'N/A')}%")
    
    # 輸出內容
    if result.stdout and result.stdout.strip():
        print(f"\n📤 STDOUT:")
        print(result.stdout)
    
    if result.stderr and result.stderr.strip():
        print(f"\n📥 STDERR:")
        print(result.stderr)
    
    if result.error_message:
        print(f"\n❌ Error: {result.error_message}")


def run_command(args):
    """運行單個命令"""
    print_banner()
    
    # 創建配置
    config = ExecutionManagerConfig(
        adaptive_timeout=not args.no_adaptive,
        terminal_monitoring=not args.no_terminal_check,
        resource_monitoring=not args.no_resource_monitor,
        auto_recovery=not args.no_auto_recovery,
        log_level="DEBUG" if args.verbose else "INFO"
    )
    
    with ExecutionManager(config) as manager:
        if args.health_check:
            health_report = manager.get_system_health_report()
            print_system_health(health_report)
            return
        
        if not args.command:
            print("❌ No command specified. Use --help for usage information.")
            return
        
        print(f"🔧 Executing with smart monitoring...")
        print(f"Command: {args.command}")
        
        if args.timeout:
            print(f"Timeout: {args.timeout}s")
        
        # 執行命令
        start_time = time.time()
        result = manager.execute_command(
            args.command,
            timeout=args.timeout,
            retry_on_failure=not args.no_retry,
            shell=True
        )
        
        # 顯示結果
        print_execution_result(result, args.command)
        
        # 顯示最終健康報告
        if args.verbose:
            print(f"\n📊 Final Health Report:")
            health_report = manager.get_system_health_report()
            print_system_health(health_report)


async def run_async_command(args):
    """運行異步命令"""
    print_banner()
    print(f"🔧 Executing async command with smart monitoring...")
    
    config = ExecutionManagerConfig(
        log_level="DEBUG" if args.verbose else "INFO"
    )
    
    manager = ExecutionManager(config)
    
    try:
        result = await manager.execute_async_command(
            args.command,
            timeout=args.timeout
        )
        
        print_execution_result(result, args.command)
        
    finally:
        manager.stop_health_monitoring()


def run_stress_test(args):
    """運行壓力測試"""
    print_banner()
    print(f"🧪 Running stress test...")
    
    config = ExecutionManagerConfig(
        log_level="DEBUG" if args.verbose else "INFO"
    )
    
    commands = [
        "echo 'Test 1: Simple command'",
        "python -c 'import time; time.sleep(2); print(\"Test 2: Short delay\")'",
        "python -c 'import time; time.sleep(5); print(\"Test 3: Medium delay\")'",
        "echo 'Test 4: Another simple command'",
        "python -c 'print(\"Test 5: Quick Python\")'",
    ]
    
    if args.include_timeout_test:
        commands.append("python -c 'import time; time.sleep(60); print(\"This should timeout\")'")
    
    with ExecutionManager(config) as manager:
        print(f"Running {len(commands)} test commands...")
        
        for i, command in enumerate(commands, 1):
            print(f"\n--- Test {i}/{len(commands)} ---")
            print(f"Command: {command}")
            
            result = manager.execute_command(command, timeout=10.0)
            
            status_icon = "✅" if result.status == ExecutionStatus.COMPLETED else "❌"
            print(f"Result: {status_icon} {result.status.value} ({result.execution_time:.2f}s)")
            
            if result.error_message:
                print(f"Error: {result.error_message}")
        
        # 最終統計
        print(f"\n📊 Stress Test Results:")
        health_report = manager.get_system_health_report()
        print_system_health(health_report)


def run_monitor_mode(args):
    """運行監控模式"""
    print_banner()
    print(f"👁️  Starting continuous monitoring mode...")
    print(f"Press Ctrl+C to stop")
    
    config = ExecutionManagerConfig(
        resource_monitoring=True,
        terminal_monitoring=True,
        log_level="DEBUG" if args.verbose else "INFO"
    )
    
    with ExecutionManager(config) as manager:
        try:
            while True:
                health_report = manager.get_system_health_report()
                
                # 清屏（在支持的終端機上）
                if not args.no_clear:
                    print("\033[2J\033[H", end="")
                
                print_banner()
                print(f"🕐 Monitoring... (Update every {args.interval}s)")
                print_system_health(health_report)
                
                time.sleep(args.interval)
                
        except KeyboardInterrupt:
            print(f"\n👋 Monitoring stopped by user")


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="Execution Monitor CLI - 執行監控命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples | 使用範例:
  %(prog)s "echo Hello World"                    # 執行簡單命令
  %(prog)s "python script.py" --timeout 60      # 設定60秒超時
  %(prog)s --health-check                       # 檢查系統健康狀態
  %(prog)s --monitor --interval 5               # 每5秒監控系統狀態
  %(prog)s --stress-test                        # 運行壓力測試
  %(prog)s "long_command" --async               # 異步執行命令
        """
    )
    
    # 主要參數
    parser.add_argument("command", nargs="?", help="Command to execute | 要執行的命令")
    parser.add_argument("--timeout", type=float, help="Timeout in seconds | 超時時間（秒）")
    
    # 模式選擇
    parser.add_argument("--health-check", action="store_true", 
                       help="Show system health report | 顯示系統健康報告")
    parser.add_argument("--monitor", action="store_true", 
                       help="Start continuous monitoring | 啟動連續監控")
    parser.add_argument("--stress-test", action="store_true", 
                       help="Run stress test | 運行壓力測試")
    parser.add_argument("--async", action="store_true", 
                       help="Execute command asynchronously | 異步執行命令")
    
    # 監控選項
    parser.add_argument("--no-adaptive", action="store_true", 
                       help="Disable adaptive timeout | 禁用自適應超時")
    parser.add_argument("--no-terminal-check", action="store_true", 
                       help="Disable terminal monitoring | 禁用終端機監控")
    parser.add_argument("--no-resource-monitor", action="store_true", 
                       help="Disable resource monitoring | 禁用資源監控")
    parser.add_argument("--no-auto-recovery", action="store_true", 
                       help="Disable auto recovery | 禁用自動恢復")
    parser.add_argument("--no-retry", action="store_true", 
                       help="Disable retry on failure | 禁用失敗重試")
    
    # 顯示選項
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Verbose output | 詳細輸出")
    parser.add_argument("--interval", type=int, default=3, 
                       help="Monitor update interval in seconds | 監控更新間隔（秒）")
    parser.add_argument("--no-clear", action="store_true", 
                       help="Don't clear screen in monitor mode | 監控模式不清屏")
    
    # 測試選項
    parser.add_argument("--include-timeout-test", action="store_true", 
                       help="Include timeout test in stress test | 壓力測試包含超時測試")
    
    args = parser.parse_args()
    
    # 模式選擇邏輯
    if args.health_check or (not args.command and not args.monitor and not args.stress_test):
        run_command(args)
    elif args.monitor:
        run_monitor_mode(args)
    elif args.stress_test:
        run_stress_test(args)
    elif getattr(args, 'async'):  # 'async' 是關鍵字，需要特殊處理
        asyncio.run(run_async_command(args))
    else:
        run_command(args)


if __name__ == "__main__":
    main()