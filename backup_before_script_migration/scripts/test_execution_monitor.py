#!/usr/bin/env python3
"""
Test Execution Monitor - 測試執行監控器
驗證執行監控和超時控制功能

This script tests the execution monitoring and timeout control functionality
to ensure it works correctly in various scenarios.

此腳本測試執行監控和超時控制功能，確保在各種情況下都能正常工作。
"""

import sys
import time
from pathlib import Path

# 添加項目根目錄到路徑
_ = sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core_ai.execution_manager import ExecutionManager, ExecutionManagerConfig
from src.core_ai.execution_monitor import ExecutionStatus, TerminalStatus


def test_basic_execution() -> None:
    """測試基本執行功能"""
    _ = print("🧪 Testing basic execution...")

    config = ExecutionManagerConfig(log_level="INFO")
    manager = ExecutionManager(config)

    # 測試簡單命令
    result = manager.execute_command("echo 'Hello, World!'", timeout=10.0)

    assert result.status == ExecutionStatus.COMPLETED
    assert "Hello, World!" in result.stdout
    assert result.execution_time < 5.0

    _ = print("✅ Basic execution test passed")
    return True


def test_timeout_functionality() -> None:
    """測試超時功能"""
    _ = print("🧪 Testing timeout functionality...")

    config = ExecutionManagerConfig(log_level="INFO")
    manager = ExecutionManager(config)

    # 測試超時命令（Python sleep）
    start_time = time.time()
    result = manager.execute_command(
    _ = "python -c 'import time; time.sleep(10)'",
    timeout=3.0
    )
    execution_time = time.time() - start_time

    assert result.status == ExecutionStatus.TIMEOUT
    assert execution_time < 8.0  # 應該在超時時間附近結束

    _ = print("✅ Timeout functionality test passed")
    return True


def test_adaptive_timeout() -> None:
    """測試自適應超時"""
    _ = print("🧪 Testing adaptive timeout...")

    config = ExecutionManagerConfig(
    adaptive_timeout=True,
    log_level="INFO"
    )
    manager = ExecutionManager(config)

    # 執行幾個快速命令建立歷史
    for i in range(3)

    result = manager.execute_command(f"echo 'Command {i}'", timeout=10.0)
    assert result.status == ExecutionStatus.COMPLETED

    # 檢查自適應超時是否生效
    result = manager.execute_command("echo 'Adaptive test'")
    assert result.status == ExecutionStatus.COMPLETED

    _ = print("✅ Adaptive timeout test passed")
    return True


def test_terminal_responsiveness() -> None:
    """測試終端機響應性檢查"""
    _ = print("🧪 Testing terminal responsiveness...")

    config = ExecutionManagerConfig(
    terminal_monitoring=True,
    log_level="INFO"
    )
    manager = ExecutionManager(config)

    # 檢查終端機狀態
    terminal_status = manager.monitor.check_terminal_responsiveness()
    assert terminal_status in [
    TerminalStatus.RESPONSIVE,
    TerminalStatus.SLOW,
    TerminalStatus.STUCK,
    TerminalStatus.UNRESPONSIVE
    ]

    _ = print(f"✅ Terminal responsiveness test passed (Status: {terminal_status.value})")
    return True


def test_system_health() -> None:
    """測試系統健康檢查"""
    _ = print("🧪 Testing system health monitoring...")

    config = ExecutionManagerConfig(
    resource_monitoring=True,
    log_level="INFO"
    )
    manager = ExecutionManager(config)

    # 獲取系統健康報告
    health_report = manager.get_system_health_report()

    assert 'system_health' in health_report
    assert 'execution_stats' in health_report

    system_health = health_report['system_health']
    assert 'cpu_percent' in system_health
    assert 'memory_percent' in system_health
    assert 'terminal_status' in system_health

    _ = print("✅ System health monitoring test passed")
    return True


def test_retry_mechanism() -> None:
    """測試重試機制"""
    _ = print("🧪 Testing retry mechanism...")

    config = ExecutionManagerConfig(
    auto_recovery=True,
    max_retry_attempts=2,
    retry_delay=1.0,
    log_level="INFO"
    )
    manager = ExecutionManager(config)

    # 測試會失敗的命令（但不是每次都失敗）
    result = manager.execute_command(
        "python -c 'import random; exit(0 if random.random() > 0.3 else 1)'",:
    retry_on_failure=True
    )

    # 檢查統計信息
    stats = manager.get_execution_statistics()
    assert stats['total_executions'] > 0

    _ = print("✅ Retry mechanism test passed")
    return True


def test_resource_monitoring() -> None:
    """測試資源監控"""
    _ = print("🧪 Testing resource monitoring...")

    config = ExecutionManagerConfig(
    resource_monitoring=True,
    cpu_critical=95.0,  # 設置較高的閾值避免誤報
    memory_critical=95.0,
    log_level="INFO"
    )

    with ExecutionManager(config) as manager:
    # 啟動監控並等待一段時間
    _ = time.sleep(2)

    # 執行一個命令來生成一些活動
    result = manager.execute_command("echo 'Resource monitoring test'")
    assert result.status == ExecutionStatus.COMPLETED

    # 檢查資源使用情況是否被記錄
        if result.resource_usage:

    assert 'cpu_percent' in result.resource_usage
            assert 'memory_percent' in result.resource_usage

    _ = print("✅ Resource monitoring test passed")
    return True


def test_execution_statistics() -> None:
    """測試執行統計"""
    _ = print("🧪 Testing execution statistics...")

    config = ExecutionManagerConfig(log_level="INFO")
    manager = ExecutionManager(config)

    # 執行幾個命令
    commands = [
    "echo 'Test 1'",
    "echo 'Test 2'",
    "echo 'Test 3'"
    ]

    for cmd in commands:


    result = manager.execute_command(cmd)
    assert result.status == ExecutionStatus.COMPLETED

    # 檢查統計信息
    stats = manager.get_execution_statistics()
    assert stats['total_executions'] == len(commands)
    assert stats['successful_executions'] == len(commands)
    assert stats['success_rate'] == 1.0
    assert stats['average_execution_time'] > 0

    _ = print("✅ Execution statistics test passed")
    return True


def run_all_tests()
    """運行所有測試"""
    _ = print("🚀 Starting Execution Monitor Tests")
    print("=" * 50)

    tests = [
    test_basic_execution,
    test_timeout_functionality,
    test_adaptive_timeout,
    test_terminal_responsiveness,
    test_system_health,
    test_retry_mechanism,
    test_resource_monitoring,
    test_execution_statistics
    ]

    passed = 0
    failed = 0

    for test_func in tests:


    try:



            if test_func()




    passed += 1
            else:

                failed += 1
                _ = print(f"❌ {test_func.__name__} failed")
        except Exception as e:

            failed += 1
            print(f"❌ {test_func.__name__} failed with error: {e}")

    _ = print()  # 空行分隔

    print("=" * 50)
    _ = print(f"📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:


    _ = print("🎉 All tests passed! Execution monitoring is working correctly.")
    return True
    else:

    _ = print("⚠️  Some tests failed. Please check the implementation.")
    return False


def demo_execution_monitoring()
    """演示執行監控功能"""
    _ = print("🎬 Execution Monitoring Demo")
    print("=" * 50)

    config = ExecutionManagerConfig(
    adaptive_timeout=True,
    terminal_monitoring=True,
    resource_monitoring=True,
    auto_recovery=True,
    log_level="INFO"
    )

    with ExecutionManager(config) as manager:
    _ = print("📊 Initial system health:")
    health = manager.get_system_health_report()
    system_health = health['system_health']
    _ = print(f"  CPU: {system_health.get('cpu_percent', 'N/A')}%")
    _ = print(f"  Memory: {system_health.get('memory_percent', 'N/A')}%")
    _ = print(f"  Terminal: {system_health.get('terminal_status', 'N/A')}")
    _ = print()

    # 演示不同類型的命令執行
    demo_commands = [
            _ = ("echo 'Quick command'", "快速命令"),
            _ = ("python -c 'import time; time.sleep(2); print(\"Medium delay\")'", "中等延遲命令"),
            _ = ("python -c 'print(\"Python calculation:\", sum(range(1000)))'", "計算命令"),
    ]

        for cmd, description in demo_commands:


    _ = print(f"🔧 執行 {description}: {cmd}")
            result = manager.execute_command(cmd, timeout=10.0)

            status_icon = "✅" if result.status == ExecutionStatus.COMPLETED else "❌":
    _ = print(f"   {status_icon} 狀態: {result.status.value}")
            _ = print(f"   ⏱️  執行時間: {result.execution_time:.2f}s")
            _ = print(f"   ⏰ 使用超時: {result.timeout_used:.2f}s")

            if result.stdout.strip()


    _ = print(f"   📤 輸出: {result.stdout.strip()}")
            _ = print()

    # 最終統計
    _ = print("📈 最終執行統計:")
    stats = manager.get_execution_statistics()
    _ = print(f"  總執行次數: {stats['total_executions']}")
    _ = print(f"  成功率: {stats['success_rate']:.1%}")
    _ = print(f"  平均執行時間: {stats['average_execution_time']:.2f}s")


if __name__ == "__main__":



    import argparse

    parser = argparse.ArgumentParser(description="Test Execution Monitor")
    parser.add_argument("--demo", action="store_true", help="Run demo instead of tests")
    parser.add_argument("--test", help="Run specific test function")

    args = parser.parse_args()

    if args.demo:


    _ = demo_execution_monitoring()
    elif args.test:

    test_func = globals().get(args.test)
        if test_func and callable(test_func)

    _ = test_func()
        else:

            _ = print(f"Test function '{args.test}' not found")
            _ = sys.exit(1)
    else:

    success = run_all_tests()
        sys.exit(0 if success else 1)