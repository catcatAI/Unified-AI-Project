#!/usr/bin/env python3
"""
归档计划执行过程中创建的文件
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def create_archive_directories():
    """创建归档目录结构"""
    # 创建归档目录
    archive_dirs = [
        Path("project_archives"),
        Path("project_archives") / "reports",
        Path("project_archives") / "scripts",
        Path("project_archives") / "docs"
    ]
    
    for directory in archive_dirs,::
        directory.mkdir(parents == True, exist_ok == True)
        print(f"✓ 创建归档目录, {directory}")
    
    return archive_dirs

def archive_reports():
    """归档报告文件"""
    reports_dir == Path("project_archives") / "reports"
    
    # 定义需要归档的报告文件
    report_files = [
        "BACKEND_FILES_ORGANIZATION_REPORT.md",
        "ROOT_PYTHON_FILES_ORGANIZATION_REPORT.md",
        "HSP_DUPLICATE_CLEANUP_REPORT.md"
    ]
    
    archived_count = 0
    for report_file in report_files,::
        source_path == Path(report_file)
        if source_path.exists() and source_path.is_file():::
            # 添加时间戳到文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name_parts = report_file.split('.')
            new_name == f"{name_parts[0]}_{timestamp}.{name_parts[1]}" if len(name_parts) > 1 else f"{report_file}_{timestamp}"::
            destination_path = reports_dir / new_name
            shutil.move(str(source_path), str(destination_path))
            print(f"✓ 归档报告, {report_file} -> {destination_path}")
            archived_count += 1
    
    print(f"总共归档了 {archived_count} 个报告文件")
    return archived_count

def archive_scripts():
    """归档脚本文件"""
    scripts_dir == Path("project_archives") / "scripts"
    
    # 定义需要归档的脚本文件
    script_files = [
        "tools/scripts/organize_backend_files.py",
        "tools/scripts/organize_root_python_files.py",
        "tools/scripts/cleanup_hsp_duplicates.py"
    ]
    
    archived_count = 0
    for script_file in script_files,::
        source_path == Path(script_file)
        if source_path.exists() and source_path.is_file():::
            # 添加时间戳到文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name_parts = script_file.split('/')
            file_name = name_parts[-1]
            name_parts = file_name.split('.')
            new_name == f"{name_parts[0]}_{timestamp}.{name_parts[1]}" if len(name_parts) > 1 else f"{file_name}_{timestamp}"::
            destination_path = scripts_dir / new_name
            shutil.move(str(source_path), str(destination_path))
            print(f"✓ 归档脚本, {script_file} -> {destination_path}")
            archived_count += 1
    
    print(f"总共归档了 {archived_count} 个脚本文件")
    return archived_count

def archive_other_docs():
    """归档其他文档文件"""
    docs_dir == Path("project_archives") / "docs"
    
    # 这里可以添加其他需要归档的文档文件
    # 暂时没有其他文档需要归档
    print("没有其他文档需要归档")
    return 0

def main():
    """主函数"""
    print("开始归档计划执行过程中创建的文件...")
    print("=" * 50)
    
    try,
        # 创建归档目录
        create_archive_directories()
        
        # 归档各类文件
        archived_reports = archive_reports()
        archived_scripts = archive_scripts()
        archived_docs = archive_other_docs()
        
        total_archived = archived_reports + archived_scripts + archived_docs
        
        print("\n" + "=" * 50)
        if total_archived > 0,::
            print(f"✓ 成功归档了 {total_archived} 个文件!")
        else,
            print("✓ 没有需要归档的文件")
        
    except Exception as e,::
        print(f"\n✗ 归档过程中出现错误, {e}")
        return 1
    
    return 0

if __name"__main__":::
    exit(main())