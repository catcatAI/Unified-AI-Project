#!/usr/bin/env python3
"""
全面检查项目中所有Python文件的语法错误
"""

import os
import sys
import subprocess
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple

# 需要排除的目录
EXCLUDE_DIRS = {
    '.git', 'node_modules', '__pycache__', '.venv', 'venv', 
    'backup', 'unified_fix_backups', '.benchmarks', 'logs',
    'model_cache', '.crush', '.repair_backup', 'backup_before_archive',
    'backup_before_merge', 'backup_before_refactor', 'backup_before_script_migration',
    'archived_docs', 'archived_fix_scripts', 'archived_systems',
    'auto_fix_system_tests', 'auto_fix_workspace', 'backup_before_archive',
    'enhanced_unified_fix_backups', 'fixed_scripts_archive', 'graphic-launcher',
    'miscellaneous', 'packages', 'project_archives', 'repair_backups',
    'stubs', 'templates', 'test_data', 'test_reports', 'tools', 'training',
    'unified_fix_backups'
}

# 需要排除的文件
EXCLUDE_FILES = {
    'temp_head.py', 'test.py'
}

def should_exclude_path(path: Path) -> bool:
    """检查路径是否应该被排除"""
    # 检查目录
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
    
    # 检查文件
    if path.name in EXCLUDE_FILES:
        return True
    
    return False

def find_python_files(root_dir: Path) -> List[Path]:
    """查找所有Python文件"""
    python_files = []
    
    for py_file in root_dir.rglob("*.py"):
        if not should_exclude_path(py_file):
            python_files.append(py_file)
    
    return python_files

def check_single_file(file_path: Path) -> Tuple[Path, bool, str]:
    """检查单个文件的语法"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(file_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return (file_path, True, "")
        else:
            return (file_path, False, result.stderr)
            
    except subprocess.TimeoutExpired:
        return (file_path, False, "检查超时")
    except Exception as e:
        return (file_path, False, str(e))

def check_syntax_errors(root_dir: Path = Path(".")) -> List[Tuple[Path, str]]:
    """检查指定目录下所有Python文件的语法错误"""
    print("正在查找Python文件...")
    python_files = find_python_files(root_dir)
    print(f"找到 {len(python_files)} 个Python文件")
    
    error_files = []
    
    # 使用线程池并发检查文件
    with ThreadPoolExecutor(max_workers=10) as executor:
        # 提交所有任务
        future_to_file = {
            executor.submit(check_single_file, py_file): py_file 
            for py_file in python_files
        }
        
        # 处理结果
        for future in as_completed(future_to_file):
            file_path, is_valid, error_msg = future.result()
            
            if not is_valid:
                error_files.append((file_path, error_msg))
                print(f"❌ 语法错误: {file_path}")
                if error_msg:
                    print(f"   错误详情: {error_msg}")
            else:
                print(f"✅ 语法正确: {file_path}")
    
    return error_files

def main():
    """主函数"""
    print("开始全面检查项目中的Python文件语法错误...")
    print("=" * 50)
    
    errors = check_syntax_errors(Path("."))
    
    print("\n" + "=" * 50)
    if errors:
        print(f"发现 {len(errors)} 个文件存在语法错误:")
        for file_path, error_msg in errors:
            print(f"\n  ❌ {file_path}")
            if error_msg:
                print(f"     错误: {error_msg}")
    else:
        print("\n🎉 恭喜！所有Python文件都没有语法错误。")

if __name__ == "__main__":
    main()