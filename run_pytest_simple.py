"""
簡單的 pytest 運行腳本
"""
import os
import sys
import subprocess

def main():
    # 設置工作目錄
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 構建命令
    cmd = [
        sys.executable,
        "-m", "pytest",
        "tests/core_ai/memory/test_ham_memory_manager.py",
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
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # 即時輸出
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        
        # 獲取返回碼
        return process.returncode
        
    except Exception as e:
        print(f"執行測試時出錯: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
