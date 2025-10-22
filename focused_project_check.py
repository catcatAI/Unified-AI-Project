#!/usr/bin/env python3
"""
聚焦的项目检查脚本
重点检查统一自动修复系统目录下的文件
"""

import os
import sys
import subprocess
import json
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple
import time

# 全局变量用于存储结果
lock = threading.Lock()
total_files = 0
checked_files = 0
error_count = 0
error_files = []
checked_count = 0

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
        
        with lock:
            global checked_count
            checked_count += 1
            if checked_count % 5 == 0 or checked_count == total_files:
                print(f"进度: {checked_count}/{total_files} ({checked_count/total_files*100:.1f}%)")
        
        if result.returncode == 0:
            return (file_path, False, "")
        else:
            return (file_path, True, result.stderr)
    except subprocess.TimeoutExpired:
        with lock:
            checked_count += 1
        return (file_path, True, "检查超时")
    except Exception as e:
        with lock:
            checked_count += 1
        return (file_path, True, str(e))

def collect_python_files(directory: str) -> List[str]:
    """
    收集目录下所有Python文件
    
    Args:
        directory: 要检查的目录
        
    Returns:
        List[str]: Python文件路径列表
    """
    python_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    return python_files

def check_focused_project_syntax(project_root: str, max_workers: int = 4):
    """
    检查项目中关键目录的Python文件语法
    
    Args:
        project_root: 项目根目录
        max_workers: 最大并发线程数
    """
    global total_files, error_count, error_files, checked_count
    
    # 重点检查的目录
    focus_dirs = [
        "unified_auto_fix_system",
        "unified_system_manager.py",
        "unified_agi_ecosystem.py",
        "complete_system_validator.py",
        "complete_systems_summary_generator.py",
        "final_system_validation.py"
    ]
    
    print("正在收集关键Python文件...")
    python_files = []
    
    for dir_name in focus_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            if dir_path.is_file() and dir_path.name.endswith('.py'):
                python_files.append(str(dir_path))
            elif dir_path.is_dir():
                python_files.extend(collect_python_files(str(dir_path)))
    
    total_files = len(python_files)
    checked_count = 0
    
    print(f"找到 {total_files} 个关键Python文件需要检查")
    
    if total_files == 0:
        print("没有找到需要检查的关键Python文件")
        return
    
    # 使用线程池并发检查
    print("开始检查语法...")
    start_time = time.time()
    
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
                        error_preview = error_msg[:200] + "..." if len(error_msg) > 200 else error_msg
                        print(f"   错误详情: {error_preview}")
                else:
                    print(f"✅ 语法正确: {file_path}")
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    # 输出汇总信息
    print(f"\n{'='*60}")
    print(f"检查完成!")
    print(f"总耗时: {elapsed_time:.2f} 秒")
    print(f"总文件数: {total_files}")
    print(f"错误文件数: {error_count}")
    print(f"正确文件数: {total_files - error_count}")
    print(f"成功率: {(total_files - error_count) / total_files * 100:.2f}%")
    
    # 保存错误文件列表到JSON文件
    if error_files:
        error_report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_files": total_files,
            "error_count": error_count,
            "success_rate": (total_files - error_count) / total_files * 100,
            "errors": [
                {
                    "file_path": file_path,
                    "error_message": error_msg
                }
                for file_path, error_msg in error_files
            ]
        }
        
        report_file = project_root / "focused_syntax_check_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(error_report, f, indent=2, ensure_ascii=False)
        
        print(f"\n错误报告已保存到: {report_file}")
        print(f"\n存在语法错误的文件:")
        for i, (file_path, error_msg) in enumerate(error_files):
            print(f"  {i+1:2d}. {file_path}")
    else:
        print(f"\n🎉 恭喜! 所有关键Python文件语法正确!")

def main():
    """主函数"""
    project_root = Path(__file__).parent.absolute()
    print(f"开始检查项目关键目录: {project_root}")
    
    # 检查项目语法
    check_focused_project_syntax(project_root, max_workers=4)

if __name__ == "__main__":
    main()