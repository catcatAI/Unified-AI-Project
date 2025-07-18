"""
整理並運行測試，將輸出保存到 test_output 目錄
"""
import os
import sys
import subprocess
from datetime import datetime

def setup_environment():
    """設置環境變量和目錄"""
    # 確保 test_output 目錄存在
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_output')
    os.makedirs(output_dir, exist_ok=True)
    
    # 設置輸出文件名（包含時間戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f'test_results_{timestamp}.txt')
    
    # 添加項目根目錄到 Python 路徑
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # 設置 PYTHONPATH 環境變量
    os.environ['PYTHONPATH'] = project_root
    
    return output_file, project_root

def run_test_suite():
    """運行測試套件"""
    output_file, project_root = setup_environment()
    
    # 測試文件列表
    test_files = [
        "tests/core_ai/memory/test_ham_memory_manager.py"
        # 可以在這裡添加更多測試文件
    ]
    
    print(f"項目根目錄: {project_root}")
    print(f"測試輸出將保存到: {output_file}")
    print("-" * 80)
    
    # 構建命令
    cmd = [
        sys.executable,
        "-m", "pytest",
        *test_files,
        "-v",
        "--timeout=10",
        "--timeout_method=thread",
        "-s"
    ]
    
    print(f"執行命令: {' '.join(cmd)}\n")
    
    # 運行測試並將輸出保存到文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # 寫入標題
            f.write(f"測試執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"命令: {' '.join(cmd)}\n")
            f.write("=" * 80 + "\n\n")
            
            # 運行測試
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 同時輸出到控制台和文件
            for line in process.stdout:
                print(line, end='')
                f.write(line)
                f.flush()
            
            # 等待進程完成
            return_code = process.wait()
            
            # 寫入結束信息
            f.write("\n" + "=" * 80 + "\n")
            f.write(f"測試完成，返回代碼: {return_code}\n")
            
            return return_code
            
    except Exception as e:
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(f"\n執行測試時出錯: {str(e)}\n")
        print(f"執行測試時出錯: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run_test_suite())
