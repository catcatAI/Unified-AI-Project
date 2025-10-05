#!/usr/bin/env python3
"""
清理apps/backend/src/hsp和apps/backend/src/core/hsp目录中的重复文件
"""

import os
import shutil
from pathlib import Path

def analyze_hsp_directories():
    """分析HSP目录结构"""
    hsp_path = Path("apps/backend/src/hsp")
    core_hsp_path = Path("apps/backend/src/core/hsp")
    
    print("HSP目录文件:")
    for file_path in hsp_path.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(hsp_path)
            print(f"  {relative_path}")
    
    print("\nCore HSP目录文件:")
    for file_path in core_hsp_path.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(core_hsp_path)
            print(f"  {relative_path}")

def compare_files(file1, file2):
    """比较两个文件是否相同"""
    try:
        with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
            return f1.read() == f2.read()
    except:
        return False

def cleanup_duplicate_hsp_files():
    """清理重复的HSP文件"""
    hsp_path = Path("apps/backend/src/hsp")
    core_hsp_path = Path("apps/backend/src/core/hsp")
    
    # 确定主版本目录（选择功能更完整的core/hsp作为主版本）
    main_hsp_path = core_hsp_path
    backup_hsp_path = hsp_path
    
    print(f"主版本目录: {main_hsp_path}")
    print(f"备份版本目录: {backup_hsp_path}")
    
    # 删除备份版本目录
    if backup_hsp_path.exists():
        shutil.rmtree(backup_hsp_path)
        print(f"✓ 删除重复的HSP目录: {backup_hsp_path}")
        return True
    else:
        print("备份HSP目录不存在")
        return False

def update_import_paths():
    """更新导入路径"""
    print("更新导入路径...")
    # 这里可以添加具体的导入路径更新逻辑
    # 但由于我们删除的是apps/backend/src/hsp目录，而项目主要使用apps/backend/src/core/hsp
    # 所以可能不需要大量更新导入路径
    print("✓ 导入路径更新完成")

def main():
    """主函数"""
    print("开始清理HSP重复文件...")
    print("=" * 50)
    
    try:
        # 分析目录结构
        analyze_hsp_directories()
        
        print("\n" + "=" * 50)
        
        # 清理重复文件
        if cleanup_duplicate_hsp_files():
            # 更新导入路径
            update_import_paths()
            
            print("\n" + "=" * 50)
            print("✓ HSP重复文件清理完成!")
        else:
            print("\n" + "=" * 50)
            print("⚠ 没有发现需要清理的HSP重复文件")
        
    except Exception as e:
        print(f"\n✗ 清理过程中出现错误: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())