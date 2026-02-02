#!/usr/bin/env python3
"""
Angela AI v6.0.0 发布包创建脚本
Release Package Creator
"""

import tarfile
import os
from pathlib import Path
from datetime import datetime

def create_release_package():
    """创建发布包"""
    
    print("="*70)
    print("🎁 Angela AI v6.0.0 发布包创建")
    print("="*70)
    
    # 发布包名称
    archive_name = "angela-ai-v6.0.0-final.tar.gz"
    
    # 要包含的文件和目录
    include_items = [
        "apps/backend/src",
        "apps/backend/tests",
        "docs",
        "cli",
        "tools/scripts",
        "unified_auto_fix_system",
        "training",
        "tests",
        "README.md",
        "LICENSE",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "SECURITY.md",
        "requirements.txt",
        "setup.py",
        "pyproject.toml",
        ".env.example",
        "FINAL_QUALITY_REPORT.md",
        "RELEASE_CHECKLIST_FINAL.md",
        "RELEASE_NOTES_v6.0.0.md",
        "verify_installation.py",
        "check_system_completeness.py",
    ]
    
    # 要排除的模式
    exclude_patterns = [
        "__pycache__",
        "*.pyc",
        "*.pyo",
        ".git",
        ".gitignore",
        ".env",
        "venv",
        "env",
        "node_modules",
        ".vscode",
        ".idea",
        "*.log",
        "*.tmp",
        "temp",
        "tmp",
        "backup_",
        "archived_",
        "release_temp",
        "*.tar.gz",
        "data/",
        "logs/",
    ]
    
    print(f"\n📦 创建发布包: {archive_name}")
    print(f"📁 包含项目: {len(include_items)} 个")
    print(f"🚫 排除模式: {len(exclude_patterns)} 个")
    
    # 统计信息
    files_added = 0
    total_size = 0
    
    with tarfile.open(archive_name, "w:gz") as tar:
        for item in include_items:
            item_path = Path(item)
            if not item_path.exists():
                print(f"  ⚠️  跳过 (不存在): {item}")
                continue
            
            if item_path.is_file():
                # 添加文件
                tar.add(item, arcname=item)
                files_added += 1
                total_size += item_path.stat().st_size
                print(f"  ✅ 添加文件: {item}")
            elif item_path.is_dir():
                # 添加目录
                for file_path in item_path.rglob("*"):
                    # 检查是否应排除
                    should_exclude = False
                    for pattern in exclude_patterns:
                        if pattern in str(file_path):
                            should_exclude = True
                            break
                    
                    if not should_exclude and file_path.is_file():
                        arcname = str(file_path).replace("\\", "/")
                        tar.add(file_path, arcname=arcname)
                        files_added += 1
                        total_size += file_path.stat().st_size
                
                print(f"  ✅ 添加目录: {item} ({sum(1 for _ in item_path.rglob('*') if _.is_file())} 个文件)")
    
    # 验证包
    print(f"\n🔍 验证发布包...")
    with tarfile.open(archive_name, "r:gz") as tar:
        members = tar.getmembers()
        print(f"  📊 包内文件数: {len(members)}")
        
        # 检查关键文件
        key_files = [
            "README.md",
            "LICENSE",
            "requirements.txt",
            "setup.py",
            "FINAL_QUALITY_REPORT.md",
            "RELEASE_NOTES_v6.0.0.md",
        ]
        
        all_present = True
        for key_file in key_files:
            found = any(key_file in m.name for m in members)
            status = "✅" if found else "❌"
            print(f"  {status} {key_file}")
            if not found:
                all_present = False
    
    # 输出统计
    archive_size = Path(archive_name).stat().st_size
    print(f"\n📊 发布包统计:")
    print(f"  文件总数: {files_added}")
    print(f"  原始大小: {total_size / 1024 / 1024:.2f} MB")
    print(f"  包大小: {archive_size / 1024 / 1024:.2f} MB")
    print(f"  压缩率: {(1 - archive_size/total_size)*100:.1f}%")
    
    if all_present:
        print(f"\n✅ 发布包创建成功: {archive_name}")
        print(f"\n🚀 Angela AI v6.0.0 准备就绪!")
        return True
    else:
        print(f"\n⚠️  发布包已创建，但部分关键文件缺失")
        return False

if __name__ == "__main__":
    success = create_release_package()
    exit(0 if success else 1)
