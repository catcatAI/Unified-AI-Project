"""
簡單的 HAM Memory Manager 測試腳本
"""
import sys
import os
import subprocess

def run_test():
    """運行測試"""
    # 設置工作目錄
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 測試文件路徑
    test_file = "tests/core_ai/memory/test_ham_memory_manager.py"
    
    # 構建命令
    cmd = [
        sys.executable,
        "-m", "pytest",
        test_file,
        "-v",
        "--timeout=10",
        "--timeout_method=thread",
        "-s"
    ]
    
    print(f"執行命令: {' '.join(cmd)}\n")
    
    # 運行命令
    try:
        # 使用 Popen 並捕獲輸出
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # 即時輸出
        for line in process.stdout:
            print(line, end='', flush=True)
        
        # 等待進程完成
        process.wait()
        return process.returncode
        
    except Exception as e:
        print(f"執行測試時出錯: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run_test())
