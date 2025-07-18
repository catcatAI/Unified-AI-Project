"""
運行 HAM Memory Manager 測試的最終版本
"""
import sys
import os
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
    
    # 運行命令並捕獲輸出
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # 行緩衝
            universal_newlines=True
        )
        
        # 即時輸出
        for line in process.stdout:
            print(line, end='')
            sys.stdout.flush()
            
        # 等待進程完成
        return_code = process.wait()
        
    except Exception as e:
        print(f"執行測試時出錯: {e}")
        return 1
    
    return return_code

if __name__ == "__main__":
    sys.exit(main())
