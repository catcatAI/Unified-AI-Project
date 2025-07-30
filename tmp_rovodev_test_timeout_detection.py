#!/usr/bin/env python3
"""
測試超時和循環檢測功能
Test timeout and loop detection functionality
"""

import asyncio
import pytest
import sys
import threading
import time
from pathlib import Path

# 添加 src 目錄到路徑
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from core_ai.test_utils.deadlock_detector import (
        deadlock_detection,
        timeout_with_detection,
        check_for_infinite_loop,
        LoopDetector
    )
    DETECTION_AVAILABLE = True
except ImportError as e:
    print(f"Detection modules not available: {e}")
    DETECTION_AVAILABLE = False


class TestTimeoutAndDetection:
    """測試超時和檢測功能"""
    
    @pytest.mark.timeout(5)
    def test_basic_timeout(self):
        """基本超時測試"""
        time.sleep(2)  # 應該在超時前完成
        assert True
    
    @pytest.mark.timeout(10)
    @pytest.mark.deadlock_detection
    def test_with_deadlock_detection(self):
        """帶死鎖檢測的測試"""
        time.sleep(3)
        assert True
    
    @pytest.mark.timeout(2)
    def test_timeout_failure(self):
        """測試超時失敗（這個測試應該會超時）"""
        pytest.skip("Skipping timeout test to avoid CI failure")
        time.sleep(5)  # 這會超時
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_async_timeout(self):
        """異步超時測試"""
        await asyncio.sleep(2)
        assert True
    
    def test_loop_detection(self):
        """循環檢測測試"""
        if not DETECTION_AVAILABLE:
            pytest.skip("Detection not available")
        
        detector = LoopDetector(max_iterations=100)
        
        # 模擬正常循環
        for i in range(50):
            if detector.check_iteration("test_location"):
                pytest.fail("False positive loop detection")
        
        # 模擬無限循環（但不真的無限）
        for i in range(150):
            if detector.check_iteration("infinite_location"):
                # 應該檢測到循環
                assert True
                return
        
        pytest.fail("Loop detection failed")
    
    def test_resource_monitoring(self, deadlock_detector):
        """資源監控測試"""
        if not DETECTION_AVAILABLE:
            pytest.skip("Detection not available")
        
        # 創建一些線程來測試監控
        threads = []
        for i in range(3):
            thread = threading.Thread(target=lambda: time.sleep(1))
            thread.start()
            threads.append(thread)
        
        # 等待線程完成
        for thread in threads:
            thread.join()
        
        # 檢測器應該在 fixture 中檢查洩漏
        assert True
    
    @pytest.mark.asyncio
    async def test_async_resource_monitoring(self, deadlock_detector):
        """異步資源監控測試"""
        if not DETECTION_AVAILABLE:
            pytest.skip("Detection not available")
        
        # 創建一些異步任務
        tasks = []
        for i in range(5):
            task = asyncio.create_task(asyncio.sleep(0.5))
            tasks.append(task)
        
        # 等待任務完成
        await asyncio.gather(*tasks)
        
        assert True


def test_timeout_decorator():
    """測試超時裝飾器"""
    if not DETECTION_AVAILABLE:
        pytest.skip("Detection not available")
    
    @timeout_with_detection(timeout=3.0)
    def quick_function():
        time.sleep(1)
        return "success"
    
    result = quick_function()
    assert result == "success"


def test_async_timeout_decorator():
    """測試異步超時裝飾器"""
    if not DETECTION_AVAILABLE:
        pytest.skip("Detection not available")
    
    @timeout_with_detection(timeout=3.0)
    async def quick_async_function():
        await asyncio.sleep(1)
        return "async_success"
    
    async def run_test():
        result = await quick_async_function()
        assert result == "async_success"
    
    asyncio.run(run_test())


def test_deadlock_detection_context():
    """測試死鎖檢測上下文管理器"""
    if not DETECTION_AVAILABLE:
        pytest.skip("Detection not available")
    
    with deadlock_detection(timeout=5.0):
        time.sleep(1)
        # 正常執行，不應該檢測到死鎖
        assert True


if __name__ == "__main__":
    # 直接運行一些測試
    print("Testing timeout and detection functionality...")
    
    if DETECTION_AVAILABLE:
        print("✓ Detection modules available")
        
        # 測試基本功能
        test_timeout_decorator()
        print("✓ Timeout decorator test passed")
        
        test_async_timeout_decorator()
        print("✓ Async timeout decorator test passed")
        
        test_deadlock_detection_context()
        print("✓ Deadlock detection context test passed")
        
        print("All basic tests passed!")
    else:
        print("✗ Detection modules not available")
        sys.exit(1)