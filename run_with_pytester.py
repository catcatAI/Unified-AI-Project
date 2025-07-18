"""
使用 pytest 的 pytester 來運行測試
"""
import sys
import os
import pytest

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

def run_tests():
    """使用 pytester 運行測試"""
    # 創建一個臨時目錄來運行測試
    pytester = pytest.Pytester()
    
    # 創建一個臨時測試文件
    test_content = """
    import pytest
    
    def test_example():
        assert 1 + 1 == 2
    
    @pytest.mark.asyncio
    async def test_async_example():
        assert await asyncio.sleep(0.1, result=True)
    """
    
    # 寫入臨時測試文件
    pytester.makepyfile(test_file=test_content)
    
    # 運行測試
    result = pytester.runpytest("-v", "--timeout=10")
    
    # 打印測試結果
    print("\nTest results:")
    print(result.stdout.str())
    
    if result.ret == 0:
        print("All tests passed!")
    else:
        print("Some tests failed!")
    
    return result.ret

if __name__ == "__main__":
    # 設置環境
    setup_environment()
    
    # 運行測試
    exit_code = run_tests()
    
    # 輸出結果
    print("\n" + "=" * 40)
    print(f"Test finished with exit code: {exit_code}")
    print("=" * 40)
    
    # 強制刷新輸出緩衝區
    sys.stdout.flush()
    sys.stderr.flush()
