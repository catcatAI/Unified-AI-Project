"""
直接使用 subprocess 運行 pytest 命令
"""
import sys
import os
import subprocess

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
    """使用 subprocess 運行 pytest 命令"""
    # 構建命令
    cmd = [
        sys.executable,  # 使用當前的 Python 解釋器
        "-m", "pytest",
        "tests/test_simple.py",  # 測試文件
        "-v",  # 詳細輸出
        "--timeout=10",  # 超時設置
        "--timeout_method=thread",
        "-s"  # 禁用捕獲，顯示所有輸出
    ]
    
    print("Running command:", " ".join(cmd))
    
    # 運行命令
    try:
        result = subprocess.run(
            cmd,
            cwd=os.getcwd(),
            env=os.environ,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        print("\nTest output:")
        print(result.stdout)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\nTest failed with exit code {e.returncode}:")
        print(e.output)
        return e.returncode

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
