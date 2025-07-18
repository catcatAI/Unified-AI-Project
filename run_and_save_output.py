"""
運行測試並將輸出保存到文件
"""
import sys
import os
import subprocess

def main():
    # 設置工作目錄
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 輸出文件路徑
    output_file = "test_output.txt"
    
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
    
    print(f"執行命令: {' '.join(cmd)}")
    print(f"輸出將保存到: {output_file}\n")
    
    try:
        # 運行命令並將輸出重定向到文件
        with open(output_file, 'w', encoding='utf-8') as f:
            result = subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                text=True,
                check=False
            )
        
        # 讀取並顯示輸出文件內容
        print("=== 測試輸出開始 ===")
        with open(output_file, 'r', encoding='utf-8') as f:
            print(f.read())
        print("=== 測試輸出結束 ===")
        
        print(f"\n測試結束，返回代碼: {result.returncode}")
        return result.returncode
        
    except Exception as e:
        print(f"執行測試時出錯: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
