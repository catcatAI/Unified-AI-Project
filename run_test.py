import pytest
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

def run_tests():
    """運行測試"""
    # 測試參數
    test_args = [
        "tests/",  # 運行所有測試
        "-v",
        "--timeout=30",
        "--timeout_method=thread",
        "-s",  # 禁用捕獲，顯示所有輸出
        "--tb=long",  # 顯示詳細的錯誤跟蹤
        "--showlocals",  # 顯示局部變量
        "--log-cli-level=DEBUG",  # 啟用調試日誌
        "-k", "not (test_rag_manager or test_translation_model or test_tonal_repair_engine or test_game or test_hsp_integration or test_logic_model or test_math_model)"
    ]
    
    print("Starting tests with arguments:", " ".join(test_args))
    exit_code = pytest.main(test_args)
    return exit_code

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
