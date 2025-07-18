"""
運行 HAM Memory Manager 測試的腳本
"""
import sys
import os
import asyncio

def setup_environment():
    """設置測試環境"""
    # 獲取項目根目錄
    project_root = os.path.abspath('.')
    
    # 添加項目根目錄到 Python 路徑
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # 設置 PYTHONPATH 環境變量
    os.environ['PYTHONPATH'] = project_root
    
    # 打印調試信息
    print("=" * 80)
    print(f"Working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    print("=" * 80)

async def run_async_test(test_func, *args, **kwargs):
    """運行異步測試函數"""
    print(f"\nRunning test: {test_func.__name__}...")
    try:
        await test_func(*args, **kwargs)
        print(f"Test {test_func.__name__} passed!")
        return 0
    except Exception as e:
        print(f"Test {test_func.__name__} failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

def run_ham_tests():
    """運行 HAM Memory Manager 測試"""
    print("\nSetting up HAM Memory Manager tests...")
    
    # 導入測試模組
    from tests.core_ai.memory.test_ham_memory_manager import (
        ham_manager_fixture,
        test_01_initialization_and_empty_store
    )
    
    # 設置事件循環
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # 獲取 fixture
        print("Setting up fixture...")
        fixture = ham_manager_fixture()
        
        # 運行測試
        print("Running tests...")
        exit_code = loop.run_until_complete(
            run_async_test(test_01_initialization_and_empty_store, fixture)
        )
        
        return exit_code
    except Exception as e:
        print(f"Error running tests: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        loop.close()

if __name__ == "__main__":
    # 設置環境
    setup_environment()
    
    # 運行測試
    exit_code = run_ham_tests()
    
    # 輸出結果
    print("\n" + "=" * 40)
    print(f"Test finished with exit code: {exit_code}")
    print("=" * 40)
    
    # 強制刷新輸出緩衝區
    sys.stdout.flush()
    sys.stderr.flush()
