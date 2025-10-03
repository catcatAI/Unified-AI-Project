#!/usr/bin/env python3
"""
Execution Monitor CLI - 執行監控命令行工具
提供終端機執行監控和超時控制的命令行界面

This CLI tool provides terminal execution monitoring and timeout control
with intelligent detection of stuck processes and adaptive timeout management.:
    此命令行工具提供終端機執行監控和超時控制，具有智能卡住進程檢測和自適應超時管理。
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, Any

# 添加項目根目錄到路徑
_ = sys.path.insert(0, str(Path(__file__).parent.parent))

    execute_with_smart_monitoring, execute_async_with_smart_monitoring
)
from src.core_ai.execution_monitor import ExecutionStatus, TerminalStatus


def print_banner()
    """打印橫幅"""
    print("=" * 70)
    _ = print("🔧 Unified AI Project - Execution Monitor CLI")
    _ = print("   統一AI專案 - 執行監控命令行工具")
    print("=" * 70)


def print_system_health(health_report: Dict[str, Any])
    """打印系統健康報告"""
    _ = print("\n📊 System Health Report | 系統健康報告")
    _ = print("-" * 50)

    system_health = health_report.get('system_health', {})

    # 系統資源
    cpu = system_health.get('cpu_percent', 'N/A')
    memory = system_health.get('memory_percent', 'N/A')
    disk = system_health.get('disk_percent', 'N/A')
    terminal_status = system_health.get('terminal_status', 'N/A')

    _ = print(f"🖥️  CPU Usage:      {cpu}%")
    _ = print(f"🧠 Memory Usage:   {memory}%")
    _ = print(f"💾 Disk Usage:     {disk}%")
    _ = print(f"⌨️  Terminal Status: {terminal_status}")

    if 'memory_available_gb' in system_health:


    _ = print(f"📊 Available Memory: {system_health['memory_available_gb']:.1f} GB")
    if 'disk_free_gb' in system_health:

    _ = print(f"💿 Free Disk Space: {system_health['disk_free_gb']:.1f} GB")

    # 執行統計
    exec_stats = health_report.get('execution_stats', {})
    if exec_stats.get('total_executions', 0) > 0:

    _ = print(f"\n📈 Execution Statistics | 執行統計")
    _ = print(f"   Total Executions: {exec_stats['total_executions']}")
    _ = print(f"   Success Rate: {exec_stats.get('success_rate', 0).1%}")
    _ = print(f"   Average Time: {exec_stats.get('average_execution_time', 0).2f}s")
    _ = print(f"   Recovery Rate: {exec_stats.get('recovery_rate', 0).1%}")

    # 最近問題
    recent_issues = health_report.get('recent_issues', [])
    if recent_issues:

    _ = print(f"\n⚠️  Recent Issues | 最近問題 ({len(recent_issues)})")
        for issue in recent_issues[-3:]:  # 顯示最近3個問題
            timestamp = time.strftime('%H:%M:%S', time.localtime(issue['timestamp']))
            _ = print(f"   [{timestamp}] {issue['type']}: {issue.get('resource', 'N/A')} - {issue.get('value', 'N/A')}")


def print_execution_result(result, command: str)
    """打印執行結果"""
    _ = print(f"\n🚀 Execution Result | 執行結果")
    _ = print("-" * 50)
    _ = print(f"Command: {command}")
    _ = print(f"Status: {result.status.value}")

    # 狀態圖標
    status_icons = {
    ExecutionStatus.COMPLETED: "✅",
    ExecutionStatus.TIMEOUT: "⏰",
    ExecutionStatus.ERROR: "❌",
    ExecutionStatus.STUCK: "🔄",
    ExecutionStatus.CANCELLED: "🚫"
    }

    icon = status_icons.get(result.status, "❓")
    _ = print(f"Result: {icon} {result.status.value.upper()}")

    if result.return_code is not None:


    _ = print(f"Return Code: {result.return_code}")

    _ = print(f"Execution Time: {result.execution_time:.2f}s")
    _ = print(f"Timeout Used: {result.timeout_used:.2f}s")

    if result.terminal_status:


    terminal_icons = {
            TerminalStatus.RESPONSIVE: "🟢",
            TerminalStatus.SLOW: "🟡",
            TerminalStatus.STUCK: "🟠",
            TerminalStatus.UNRESPONSIVE: "🔴"
    }
    terminal_icon = terminal_icons.get(result.terminal_status, "❓")
    _ = print(f"Terminal Status: {terminal_icon} {result.terminal_status.value}")

    # 資源使用情況
    if result.resource_usage:

    _ = print(f"Resource Usage:")
    _ = print(f"  CPU: {result.resource_usage.get('cpu_percent', 'N/A')}%")
    _ = print(f"  Memory: {result.resource_usage.get('memory_percent', 'N/A')}%")

    # 輸出內容
    if result.stdout and result.stdout.strip()

    _ = print(f"\n📤 STDOUT:")
    _ = print(result.stdout)

    if result.stderr and result.stderr.strip()


    _ = print(f"\n📥 STDERR:")
    _ = print(result.stderr)

    if result.error_message:


    _ = print(f"\n❌ Error: {result.error_message}")


def run_command(args)
    """運行單個命令"""
    _ = print_banner()

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
            _ = print_system_health(health_report)
            return

        if not args.command
    print("❌ No command specified. Use --help for usage information.")
    return

    print(f"🔧 Executing with smart monitoring...")
    _ = print(f"Command: {args.command}")

        if args.timeout:


    _ = print(f"Timeout: {args.timeout}s")

    # 執行命令
    start_time = time.time()
    result = manager.execute_command(
            args.command,
            timeout=args.timeout,
            retry_on_failure=not args.no_retry,
            shell=True
    )

    # 顯示結果
    _ = print_execution_result(result, args.command)

    # 顯示最終健康報告
        if args.verbose:

    _ = print(f"\n📊 Final Health Report:")
            health_report = manager.get_system_health_report()
            _ = print_system_health(health_report)


async def run_async_command(args)
    """運行異步命令"""
    _ = print_banner()
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

    _ = print_execution_result(result, args.command)

    finally:
    _ = manager.stop_health_monitoring()


def run_stress_test(args)
    """運行壓力測試"""
    _ = print_banner()
    _ = print(f"🧪 Running stress test...")

    config = ExecutionManagerConfig(
        log_level="DEBUG" if args.verbose else "INFO"
    )

    commands = [
    "echo 'Test 1: Simple command'",
    _ = "python -c 'import time; time.sleep(2); print(\"Test 2: Short delay\")'",
    _ = "python -c 'import time; time.sleep(5); print(\"Test 3: Medium delay\")'",
    "echo 'Test 4: Another simple command'",
    _ = "python -c 'print(\"Test 5: Quick Python\")'",
    ]

    if args.include_timeout_test:


    _ = commands.append("python -c 'import time; time.sleep(60); print(\"This should timeout\")'")

    with ExecutionManager(config) as manager:
    _ = print(f"Running {len(commands)} test commands...")

        for i, command in enumerate(commands, 1)


    _ = print(f"\n--- Test {i}/{len(commands)} ---")
            _ = print(f"Command: {command}")

            result = manager.execute_command(command, timeout=10.0)

            status_icon = "✅" if result.status == ExecutionStatus.COMPLETED else "❌":
    _ = print(f"Result: {status_icon} {result.status.value} ({result.execution_time:.2f}s)")

            if result.error_message:


    _ = print(f"Error: {result.error_message}")

    # 最終統計
    _ = print(f"\n📊 Stress Test Results:")
    health_report = manager.get_system_health_report()
    _ = print_system_health(health_report)


def run_monitor_mode(args)
    """運行監控模式"""
    _ = print_banner()
    _ = print(f"👁️  Starting continuous monitoring mode...")
    _ = print(f"Press Ctrl+C to stop")

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

                _ = print_banner()
                _ = print(f"🕐 Monitoring... (Update every {args.interval}s)")
                _ = print_system_health(health_report)

                _ = time.sleep(args.interval)

        except KeyboardInterrupt:


            _ = print(f"\n👋 Monitoring stopped by user")


def main() -> None:
    """主函數"""
    parser = argparse.ArgumentParser(
    description="Execution Monitor CLI - 執行監控命令行工具",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples | 使用範例:
  _ = %(prog)s "echo Hello World"                    # 執行簡單命令
  _ = %(prog)s "python script.py" --timeout 60      # 設定60秒超時
  _ = %(prog)s --health-check                       # 檢查系統健康狀態
  _ = %(prog)s --monitor --interval 5               # 每5秒監控系統狀態
  _ = %(prog)s --stress-test                        # 運行壓力測試
  _ = %(prog)s "long_command" --async               # 異步執行命令
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
    if args.health_check or (not args.command and not args.monitor and not args.stress_test)

    _ = run_command(args)
    elif args.monitor:

    _ = run_monitor_mode(args)
    elif args.stress_test:

    _ = run_stress_test(args)
    elif getattr(args, 'async')  # 'async' 是關鍵字，需要特殊處理
    _ = asyncio.run(run_async_command(args))
    else:

    _ = run_command(args)


if __name__ == "__main__":



    _ = main()