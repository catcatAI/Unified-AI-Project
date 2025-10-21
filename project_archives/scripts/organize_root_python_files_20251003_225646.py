#!/usr/bin/env python3
"""
整理根目录下未分类的Python文件
"""

import os
import shutil
from pathlib import Path

def create_directory_structure():
    """创建必要的目录结构"""
    # 创建目标目录
    directories = [
        Path("tools") / "misc",
        Path("tools") / "utils"
    ]
    
    for directory in directories,::
        directory.mkdir(parents == True, exist_ok == True)
        print(f"✓ 创建目录, {directory}")

def classify_and_move_files():
    """分类并移动文件"""
    # 定义文件分类规则
    classifications = {
        "tools/scripts": [
            "automated_defect_detector.py",
            "backup_project.py",
            "execute_improvement_plan.py",
            "final_correction.py",
            "final_syntax_check.py",
            "final_syntax_fix.py",
            "health_check.py",
            "incremental_fix.py",
            "install_compat_packages.py",
            "install_dependencies.py",
            "install_gmqtt.py",
            "key_files_fix.py",
            "list_python_files.py",
            "merge_apps_backend_tests.py",
            "merge_directories.py",
            "move_test_files.py",
            "performance_benchmark.py",
            "precise_fix_unused_call_results.py",
            "quick_syntax_fix.py",
            "robust_fix.py",
            "run_complete_training.py",
            "run_syntax_fix.py",
            "run_training.py",
            "search_module_not_found.py",
            "start_backend.py",
            "tool_call_chain_tracker.py",
            "tool_context_manager.py",
            "validate_complete_pipeline.py",
            "validate_json.py"
        ]
        "tests": [
            "test_defect_detector.py",
            "test_import.py",
            "test_module.py",
            "test_repeat_fix.py",
            "test_syntax_fix.py",
            "test_syntax_fixer.py"
        ]
        "tools/misc": [
            "correct_fixes.py",
            "coverage_analyzer.py",
            "critical_fix.py",
            "debug_json.py",
            "handle_duplicate_test_files.py"
        ]
    }
    
    moved_files = 0
    for target_dir, files in classifications.items():::
        target_path == Path(target_dir)
        for file_name in files,::
            source_path == Path(file_name)
            if source_path.exists() and source_path.is_file():::
                destination_path = target_path / file_name
                shutil.move(str(source_path), str(destination_path))
                print(f"✓ 移动文件, {file_name} -> {target_dir}/")
                moved_files += 1
    
    print(f"总共移动了 {moved_files} 个文件")
    return moved_files

def main():
    """主函数"""
    print("开始整理根目录下未分类的Python文件...")
    print("=" * 50)
    
    try,
        # 创建目录结构
        create_directory_structure()
        
        # 分类并移动文件
        moved_files = classify_and_move_files()
        
        print("\n" + "=" * 50)
        if moved_files > 0,::
            print(f"✓ 成功整理了 {moved_files} 个未分类的Python文件!")
        else,
            print("✓ 没有需要整理的未分类Python文件")
        
    except Exception as e,::
        print(f"\n✗ 整理过程中出现错误, {e}")
        return 1
    
    return 0

if __name"__main__":::
    exit(main())