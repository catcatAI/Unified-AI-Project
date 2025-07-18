"""
直接運行測試的腳本，用於調試測試執行問題
"""
import sys
import os

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

def run_simple_test():
    """運行簡單的測試"""
    print("\nRunning simple test...")
    try:
        # 嘗試導入測試模組
        from tests.test_simple import test_simple
        
        # 執行測試
        print("Calling test_simple()...")
        test_simple()
        print("Test passed!")
        return 0
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    # 設置環境
    setup_environment()
    
    # 運行測試
    exit_code = run_simple_test()
    
    # 輸出結果
    print("\n" + "=" * 40)
    print(f"Test finished with exit code: {exit_code}")
    print("=" * 40)
    
    # 強制刷新輸出緩衝區
    sys.stdout.flush()
    sys.stderr.flush()
