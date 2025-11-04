#!/usr/bin/env python3
"""
项目状态检查脚本
检查项目中是否存在语法错误
"""

import os
import sys
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from typing import List, Tuple

# 用于存储结果的锁
lock = threading.Lock()
error_count = 0
total_files = 0
error_files = []

def check_python_file(file_path: str) -> Tuple[str, bool, str]:
    """
    检查单个Python文件是否有语法错误
    
    Args:
        file_path: Python文件路径
        
    Returns:
        tuple: (文件路径, 是否有错误, 错误信息)
    """
    try:
        # 使用py_compile检查语法
        result = subprocess.run(
            [sys.executable, '-m', 'py_compile', file_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return (file_path, False, "")
        else:
            return (file_path, True, result.stderr)
    except subprocess.TimeoutExpired:
        return (file_path, True, "检查超时")
    except Exception as e:
        return (file_path, True, str(e))

def check_directory(directory: str, max_workers: int = 4):
    """
    检查目录下所有Python文件的语法
    
    Args:
        directory: 要检查的目录
        max_workers: 最大并发线程数
    """
    global error_count, total_files, error_files
    
    # 收集所有Python文件
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"找到 {len(python_files)} 个Python文件需要检查")
    total_files = len(python_files)
    
    # 使用线程池并发检查
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_file = {
            executor.submit(check_python_file, file_path): file_path 
            for file_path in python_files
        }
        
        # 处理完成的任务
        for future in as_completed(future_to_file):
            file_path, has_error, error_msg = future.result()
            
            with lock:
                if has_error:
                    error_count += 1
                    error_files.append((file_path, error_msg))
                    print(f"❌ 语法错误: {file_path}")
                    # 只显示前200个字符的错误信息
                    if error_msg:
                        print(f"   错误详情: {error_msg[:200]}{'...' if len(error_msg) > 200 else ''}")
                else:
                    print(f"✅ 语法正确: {file_path}")

def main():
    """主函数"""
    project_root = Path(__file__).parent.absolute()
    print(f"开始检查项目目录: {project_root}")
    
    # 检查统一自动修复系统目录
    fix_system_dir = project_root / "unified_auto_fix_system"
    if fix_system_dir.exists():
        print(f"\n检查统一自动修复系统目录: {fix_system_dir}")
        check_directory(str(fix_system_dir))
    
    # 输出汇总信息
    print(f"\n{'='*50}")
    print(f"检查完成!")
    print(f"总文件数: {total_files}")
    print(f"错误文件数: {error_count}")
    print(f"正确文件数: {total_files - error_count}")
    
    if error_files:
        print(f"\n存在语法错误的文件:")
        for file_path, error_msg in error_files[:10]:  # 只显示前10个错误文件
            print(f"  - {file_path}")
        if len(error_files) > 10:
            print(f"  ... 还有 {len(error_files) - 10} 个错误文件")
    else:
        print(f"\n🎉 恭喜! 所有Python文件语法正确!")

if __name__ == "__main__":
    main()