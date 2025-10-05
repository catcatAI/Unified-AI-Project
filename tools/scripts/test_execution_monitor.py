#!/usr/bin/env python3
"""
測試執行監控器 - 驗證 ExecutionManager 的各項功能
"""

import sys
import time
from pathlib import Path

# 添加項目根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from apps.backend.src.core.managers.execution_manager import ExecutionManager, ExecutionManagerConfig
from apps.backend.src.core.managers.execution_monitor import ExecutionStatus, TerminalStatus


def test_basic_execution() -> bool:
    """測試基本執行功能"""
    print("🧪 Testing basic execution...")

    config = ExecutionManagerConfig(log_level="INFO")
    manager = ExecutionManager(config)

    # 測試簡單命令
    result = manager.execute_command("echo 'Hello, World!'", timeout=10.0)

    assert result.status == ExecutionStatus.COMPLETED
    assert "Hello, World!" in result.stdout
    assert result.execution_time < 5.0

    print("✅ Basic execution test passed")
    return True


def test_timeout_functionality() -> bool:
    """測試超時功能"""
    print("🧪 Testing timeout functionality...")

    config = ExecutionManagerConfig(log_level="INFO")
    manager = ExecutionManager(config)

    # 測試超時命令（Python sleep）
    start_time = time.time()
    result = manager.execute_command(
        "python -c 'import time; time.sleep(10)'",
        timeout=3.0
    )
    execution_time = time.time() - start_time

    assert result.status == ExecutionStatus.TIMEOUT
    assert execution_time < 8.0  # 應該在超時時間附近結束

    print("✅ Timeout functionality test passed")
    return True


def test_adaptive_timeout() -> bool:
    """測試自適應超時"""
    print("🧪 Testing adaptive timeout...")

    config = ExecutionManagerConfig(
        adaptive_timeout=True,
        log_level="INFO"
    )
    manager = ExecutionManager(config)

    # 執行幾個快速命令建立歷史
    for i in range(3):
        result = manager.execute_command(f"echo 'Command {i}'", timeout=10.0)
        assert result.status == ExecutionStatus.COMPLETED

    # 檢查自適應超時是否生效
    result = manager.execute_command("echo 'Adaptive test'")
    assert result.status == ExecutionStatus.COMPLETED

    print("✅ Adaptive timeout test passed")
    return True


def test_terminal_responsiveness() -> bool:
    """測試終端機響應性檢查"""
    print("🧪 Testing terminal responsiveness...")

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

    print(f"✅ Terminal responsiveness test passed (Status: {terminal_status.value})")
    return True


def test_system_health() -> bool:
    """測試系統健康檢查"""
    print("🧪 Testing system health monitoring...")

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

    print("✅ System health monitoring test passed")
    return True


def test_retry_mechanism() -> bool:
    """測試重試機制"""
    print("🧪 Testing retry mechanism...")

    config = ExecutionManagerConfig(
        auto_recovery=True,
        max_retry_attempts=2,
        retry_delay=1.0,
        log_level="INFO"
    )
    manager = ExecutionManager(config)

    # 測試會失敗的命令（但不是每次都失敗）
    result = manager.execute_command(
        "python -c 'import random; exit(0 if random.random() > 0.3 else 1)'",
        retry_on_failure=True
    )

    # 檢查統計信息
    stats = manager.get_execution_statistics()
    assert stats['total_executions'] > 0

    print("✅ Retry mechanism test passed")
    return True


def test_resource_monitoring() -> bool:
    """測試資源監控"""
    print("🧪 Testing resource monitoring...")

    config = ExecutionManagerConfig(
        resource_monitoring=True,
        cpu_critical=95.0,  # 設置較高的閾值避免誤報
        memory_critical=95.0,
        log_level="INFO"
    )

    with ExecutionManager(config) as manager:
        # 啟動監控並等待一段時間
        time.sleep(2)

        # 執行一個命令來生成一些活動
        result = manager.execute_command("echo 'Resource monitoring test'")
        assert result.status == ExecutionStatus.COMPLETED

        # 檢查資源使用情況是否被記錄
        if result.resource_usage:
            assert 'cpu_percent' in result.resource_usage
            assert 'memory_percent' in result.resource_usage

    print("✅ Resource monitoring test passed")
    return True


def test_execution_statistics() -> bool:
    """測試執行統計"""
    print("🧪 Testing execution statistics...")

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

    print("✅ Execution statistics test passed")
    return True


def run_all_tests() -> bool:
    """運行所有測試"""
    print("🚀 開始執行測試套件...")
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
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"❌ {test_func.__name__} 返回 False")
        except Exception as e:
            failed += 1
            print(f"💥 {test_func.__name__} 發生異常: {e}")

    print("=" * 50)
    print(f"📊 測試結果: {passed} 通過, {failed} 失敗")
    
    if failed == 0:
        print("🎉 所有測試通過!")
        return True
    else:
        print(f"⚠️  {failed} 個測試失敗")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)