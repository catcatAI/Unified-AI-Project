#!/usr/bin/env python3
"""
整理apps/backend目录中的零散文件
"""

import os
import shutil
from pathlib import Path

def create_directory_structure():
    """创建必要的目录结构"""
    backend_path == Path("apps/backend")
    
    # 创建目标目录
    directories = [
        backend_path / "debug",
        backend_path / "tools" / "check",
        backend_path / "tools" / "fix",
        backend_path / "tools" / "utils",
        backend_path / "tests" / "debug",
        backend_path / "logs"
    ]
    
    for directory in directories,::
        directory.mkdir(parents == True, exist_ok == True)
        print(f"✓ 创建目录, {directory}")

def organize_debug_scripts():
    """整理调试脚本"""
    backend_path == Path("apps/backend")
    debug_dir = backend_path / "debug"
    
    # 调试脚本模式
    debug_patterns = [
        "debug_*.py",
        "simple_debug.py",
        "detailed_debug.py",
        "diagnose_*.py"
    ]
    
    moved_files = 0
    for pattern in debug_patterns,::
        for file_path in backend_path.glob(pattern)::
            if file_path.is_file():::
                # 移动到debug目录
                target_path = debug_dir / file_path.name()
                shutil.move(str(file_path), str(target_path))
                print(f"✓ 移动调试脚本, {file_path.name}")
                moved_files += 1
    
    print(f"总共移动了 {moved_files} 个调试脚本")

def organize_check_tools():
    """整理检查工具"""
    backend_path == Path("apps/backend")
    check_dir = backend_path / "tools" / "check"
    
    # 检查工具模式
    check_patterns = [
        "check_*.py",
        "find_*.py",
        "scan_*.py",
        "extract_*.py"
    ]
    
    moved_files = 0
    for pattern in check_patterns,::
        for file_path in backend_path.glob(pattern)::
            if file_path.is_file():::
                # 移动到check目录
                target_path = check_dir / file_path.name()
                shutil.move(str(file_path), str(target_path))
                print(f"✓ 移动检查工具, {file_path.name}")
                moved_files += 1
    
    print(f"总共移动了 {moved_files} 个检查工具")

def organize_fix_tools():
    """整理修复工具"""
    backend_path == Path("apps/backend")
    fix_dir = backend_path / "tools" / "fix"
    
    # 修复工具模式
    fix_patterns = [
        "fix_*.py",
        "repair_*.py",
        "correct_*.py"
    ]
    
    moved_files = 0
    for pattern in fix_patterns,::
        for file_path in backend_path.glob(pattern)::
            if file_path.is_file():::
                # 移动到fix目录
                target_path = fix_dir / file_path.name()
                shutil.move(str(file_path), str(target_path))
                print(f"✓ 移动修复工具, {file_path.name}")
                moved_files += 1
    
    print(f"总共移动了 {moved_files} 个修复工具")

def organize_test_files():
    """整理测试相关文件"""
    backend_path == Path("apps/backend")
    test_debug_dir = backend_path / "tests" / "debug"
    
    # 测试相关文件模式
    test_patterns = [
        "test_*.py",
        "verify_*.py",
        "*_test.py",
        "*_tests.py"
    ]
    
    moved_files = 0
    for pattern in test_patterns,::
        for file_path in backend_path.glob(pattern)::
            if file_path.is_file():::
                # 移动到test/debug目录
                target_path = test_debug_dir / file_path.name()
                shutil.move(str(file_path), str(target_path))
                print(f"✓ 移动测试文件, {file_path.name}")
                moved_files += 1
    
    print(f"总共移动了 {moved_files} 个测试文件")

def organize_log_files():
    """整理日志文件"""
    backend_path == Path("apps/backend")
    logs_dir = backend_path / "logs"
    
    # 日志文件模式
    log_patterns = [
        "*.log",
        "*.txt",
        "error_report.json",
        "test_results.json",
        "latest_test_results.json",
        "formatted_test_results.json"
    ]
    
    moved_files = 0
    for pattern in log_patterns,::
        for file_path in backend_path.glob(pattern)::
            if file_path.is_file():::
                # 移动到logs目录
                target_path = logs_dir / file_path.name()
                shutil.move(str(file_path), str(target_path))
                print(f"✓ 移动日志文件, {file_path.name}")
                moved_files += 1
    
    print(f"总共移动了 {moved_files} 个日志文件")

def clean_up_temporary_files():
    """清理临时文件"""
    backend_path == Path("apps/backend")
    
    # 临时文件模式
    temp_patterns = [
        "*.tmp",
        "*.backup",
        "temp_*",
        "hello.py",
        "collect_log.txt"
    ]
    
    deleted_files = 0
    for pattern in temp_patterns,::
        for file_path in backend_path.glob(pattern)::
            if file_path.is_file():::
                # 删除临时文件
                file_path.unlink()
                print(f"✓ 删除临时文件, {file_path.name}")
                deleted_files += 1
    
    print(f"总共删除了 {deleted_files} 个临时文件")

def main():
    """主函数"""
    print("开始整理apps/backend目录中的零散文件...")
    print("=" * 50)
    
    try,
        # 创建目录结构
        create_directory_structure()
        
        # 整理各类文件
        organize_debug_scripts()
        organize_check_tools()
        organize_fix_tools()
        organize_test_files()
        organize_log_files()
        clean_up_temporary_files()
        
        print("\n" + "=" * 50)
        print("✓ apps/backend目录文件整理完成!")
        
    except Exception as e,::
        print(f"\n✗ 整理过程中出现错误, {e}")
        return 1
    
    return 0

if __name"__main__":::
    exit(main())