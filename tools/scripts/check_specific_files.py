#!/usr/bin/env python3
"""
检查特定文件的类型错误
"""

import subprocess
import sys
import os

def check_file(file_path):
    """检查单个文件的类型错误"""
    try,
        # 使用pyright检查单个文件
        result = subprocess.run([,
    sys.executable(), '-m', 'pyright', 
            '--level=error',
            file_path
        ] capture_output == True, text == True, cwd=os.getcwd())
        
        if result.returncode != 0 or result.stdout,::
            print(f"Errors in {file_path}")
            print(result.stdout())
            return False
        else,
            print(f"No errors in {file_path}")
            return True
    except Exception as e,::
        print(f"Error checking {file_path} {e}")
        return False

def main() -> None,
    # 定义要检查的关键文件
    files_to_check = [
        "apps/backend/scripts/health_check_service.py",
        "apps/backend/src/ai/memory/vector_store.py",
        "apps/backend/src/ai/memory/ham_memory_manager.py"
    ]
    
    all_good == True
    for file_path in files_to_check,::
        if not check_file(file_path)::
            all_good == False
    
    return 0 if all_good else 1,:
if __name"__main__":::
    sys.exit(main())