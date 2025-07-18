"""
直接運行 HAM Memory Manager 測試
"""
import asyncio
import sys
import os

def setup_environment():
    """設置環境變量"""
    # 添加項目根目錄到 Python 路徑
    project_root = os.path.abspath('.')
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # 設置 PYTHONPATH 環境變量
    os.environ['PYTHONPATH'] = project_root
    
    print("=" * 60)
    print(f"工作目錄: {os.getcwd()}")
    print(f"Python 路徑: {sys.path}")
    print("=" * 60)

async def run_test():
    """運行測試"""
    try:
        # 導入測試模組
        from tests.core_ai.memory.test_ham_memory_manager import (
            ham_manager_fixture,
            test_01_initialization_and_empty_store
        )
        
        print("\n準備測試環境...")
        
        # 設置 fixture
        print("設置 fixture...")
        fixture = ham_manager_fixture()
        
        # 運行測試
        print("\n開始運行測試: test_01_initialization_and_empty_store")
        print("-" * 60)
        
        # 設置超時
        try:
            await asyncio.wait_for(
                test_01_initialization_and_empty_store(fixture),
                timeout=10.0
            )
            print("\n測試通過!")
            return 0
        except asyncio.TimeoutError:
            print("\n測試超時!")
            return 1
        except Exception as e:
            print(f"\n測試失敗: {e}")
            import traceback
            traceback.print_exc()
            return 1
            
    except Exception as e:
        print(f"運行測試時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1

def main():
    """主函數"""
    # 設置環境
    setup_environment()
    
    # 運行測試
    print("\n啟動測試...")
    return asyncio.run(run_test())

if __name__ == "__main__":
    sys.exit(main())
