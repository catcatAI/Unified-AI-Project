#!/usr/bin/env python3
"""
备份模块目录清理脚本
根据项目重构计划，core_ai 已经重构为 core、ai 两个文件夹，
因此 backup_modules 目录中的备份文件不再需要，除非用于回溯目的。
"""

import os
import shutil
from pathlib import Path

def check_backup_module_usage():
    """检查项目中是否还有对 backup_modules 的引用"""
    print("检查项目中是否还有对 backup_modules 的引用...")
    
    # 搜索项目中是否还有对 backup_modules 的引用
    root_path = Path(".")
    backup_references = []
    
    # 限制搜索范围，避免搜索备份目录本身
    try:
        # 搜索 Python 文件中的引用
        for py_file in root_path.rglob("*.py"):
            # 跳过备份目录本身
            if "backup_modules" in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if "backup_modules" in content:
                        backup_references.append(py_file)
            except Exception as e:
                # 跳过无法读取的文件
                print(f"警告: 无法读取文件 {py_file}: {e}")
                continue
        
        # 搜索 Markdown 文件中的引用
        for md_file in root_path.rglob("*.md"):
            # 跳过备份目录本身
            if "backup_modules" in str(md_file):
                continue
                
            try:
                with open(md_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if "backup_modules" in content:
                        backup_references.append(md_file)
            except Exception as e:
                # 跳过无法读取的文件
                print(f"警告: 无法读取文件 {md_file}: {e}")
                continue
    except Exception as e:
        print(f"搜索过程中发生错误: {e}")
    
    print(f"找到 {len(backup_references)} 个引用文件")
    return backup_references

def remove_backup_modules():
    """删除 backup_modules 目录"""
    backup_modules_path = Path("backup_modules")
    
    if backup_modules_path.exists() and backup_modules_path.is_dir():
        print(f"删除备份目录: {backup_modules_path}")
        try:
            shutil.rmtree(backup_modules_path)
            print("备份目录删除成功")
            return True
        except Exception as e:
            print(f"删除备份目录失败: {e}")
            return False
    else:
        print("备份目录不存在")
        return True

def main():
    print("备份模块目录清理工具")
    print("=" * 30)
    
    # 检查是否还有对备份模块的引用
    references = check_backup_module_usage()
    
    if references:
        print("\n发现以下文件中仍有对 backup_modules 的引用:")
        for ref in references[:10]:  # 只显示前10个引用
            print(f"  - {ref}")
        if len(references) > 10:
            print(f"  ... 还有 {len(references) - 10} 个引用")
        
        print("\n根据项目重构计划，core_ai 已经重构为 core、ai 两个文件夹，")
        print("backup_modules 目录中的备份文件不再需要，除非用于回溯目的。")
        
        # 询问用户是否继续删除
        confirm = input("\n是否仍然要删除 backup_modules 目录? (y/N): ")
        if confirm.lower() not in ['y', 'yes']:
            print("取消删除操作")
            return
    else:
        print("\n未发现对 backup_modules 的引用，可以安全删除。")
    
    # 删除备份目录
    remove_backup_modules()
    
    print("\n清理完成")

if __name__ == "__main__":
    main()