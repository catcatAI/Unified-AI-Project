#!/usr/bin/env python3
"""
全面的项目检查脚本
检查项目中是否存在语法错误，并提供详细的报告
"""

import os
import sys
import subprocess
import json
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Dict
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
            if checked_count % 100 == 0 or checked_count == total_files:
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

def collect_python_files(directory: str, exclude_dirs: List[str] = None) -> List[str]:
    """
    收集目录下所有Python文件
    
    Args:
        directory: 要检查的目录
        exclude_dirs: 要排除的目录列表
        
    Returns:
        List[str]: Python文件路径列表
    """
    if exclude_dirs is None:
        exclude_dirs = []
    
    python_files = []
    exclude_dirs = [os.path.normpath(d) for d in exclude_dirs]
    
    for root, dirs, files in os.walk(directory):
        # 检查是否需要排除当前目录
        skip_dir = False
        for exclude_dir in exclude_dirs:
            if exclude_dir in root:
                skip_dir = True
                break
        
        if skip_dir:
            continue
            
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    return python_files

def check_project_syntax(project_root: str, max_workers: int = 4):
    """
    检查项目中所有Python文件的语法
    
    Args:
        project_root: 项目根目录
        max_workers: 最大并发线程数
    """
    global total_files, error_count, error_files, checked_count
    
    # 要排除的目录（避免检查备份、归档等目录）
    exclude_dirs = [
        '.git',
        '__pycache__',
        '.benchmarks',
        '.crush',
        '.repair_backup',
        'backup_before_archive',
        'backup_before_merge',
        'backup_before_refactor',
        'backup_before_script_migration',
        'archived_docs',
        'archived_fix_scripts',
        'archived_systems',
        'auto_fix_workspace',
        'enhanced_unified_fix_backups',
        'fixed_scripts_archive',
        'project_archives',
        'repair_backups',
        'unified_fix_backups',
        'context_storage'
    ]
    
    print("正在收集Python文件...")
    python_files = collect_python_files(project_root, exclude_dirs)
    total_files = len(python_files)
    checked_count = 0
    
    print(f"找到 {total_files} 个Python文件需要检查")
    
    if total_files == 0:
        print("没有找到需要检查的Python文件")
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
                    # 只显示前100个字符的错误信息
                    error_preview = error_msg[:100] + "..." if len(error_msg) > 100 else error_msg
                    print(f"❌ 语法错误: {file_path}")
                    if error_msg:
                        print(f"   错误详情: {error_preview}")
    
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
        
        report_file = project_root / "project_syntax_check_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(error_report, f, indent=2, ensure_ascii=False)
        
        print(f"\n错误报告已保存到: {report_file}")
        print(f"\n存在语法错误的文件 (前20个):")
        for i, (file_path, error_msg) in enumerate(error_files[:20]):
            print(f"  {i+1:2d}. {file_path}")
        if len(error_files) > 20:
            print(f"  ... 还有 {len(error_files) - 20} 个错误文件")
    else:
        print(f"\n🎉 恭喜! 所有检查的Python文件语法正确!")

def main():
    """主函数"""
    project_root = Path(__file__).parent.absolute()
    print(f"开始检查项目目录: {project_root}")
    
    # 检查项目语法
    check_project_syntax(str(project_root), max_workers=8)

if __name__ == "__main__":
    main()