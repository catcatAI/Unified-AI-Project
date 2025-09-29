#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复Python文件中的字典语法错误
将 "_ = "key": value" 修复为 ""key": value"
"""

import os
import re
import sys
from pathlib import Path

def fix_dictionary_syntax(file_path):
    """修复单个文件中的字典语法错误"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 记录原始内容用于比较
        original_content = content
        
        # 修复字典语法错误：_ = "key": value -> "key": value
        # 匹配模式：_ = "任意字符": 任意字符,
        pattern = r'_ = "([^"]+)":\s*([^,\n]+)(,?)'
        replacement = r'"\1": \2\3'
        content = re.sub(pattern, replacement, content)
        
        # 修复另一种字典语法错误：_ = key: value -> key: value
        pattern2 = r'_ = ([a-zA-Z_][a-zA-Z0-9_]*):\s*([^,\n]+)(,?)'
        replacement2 = r'\1: \2\3'
        content = re.sub(pattern2, replacement2, content)
        
        # 如果内容有变化，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {e}")
        return False

def fix_all_files(root_dir):
    """修复目录下所有Python文件的字典语法错误"""
    fixed_files = []
    error_files = []
    
    # 遍历所有Python文件
    for py_file in Path(root_dir).rglob("*.py"):
        try:
            if fix_dictionary_syntax(py_file):
                fixed_files.append(str(py_file))
                print(f"已修复: {py_file}")
        except Exception as e:
            error_files.append((str(py_file), str(e)))
            print(f"处理文件 {py_file} 时出错: {e}")
    
    return fixed_files, error_files

def main():
    """主函数"""
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = "."
    
    print(f"开始修复 {root_dir} 目录下的字典语法错误...")
    
    fixed_files, error_files = fix_all_files(root_dir)
    
    print(f"\n修复完成!")
    print(f"共修复 {len(fixed_files)} 个文件")
    print(f"遇到错误 {len(error_files)} 个文件")
    
    if fixed_files:
        print("\n已修复的文件:")
        for file in fixed_files:
            print(f"  {file}")
    
    if error_files:
        print("\n处理出错的文件:")
        for file, error in error_files:
            print(f"  {file}: {error}")

if __name__ == "__main__":
    main()