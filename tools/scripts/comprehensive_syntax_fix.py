#!/usr/bin/env python3
"""
全面修复项目中的语法错误
"""

import os
import re
import shutil
from pathlib import Path

def fix_function_definitions(content):
    """修复函数定义后缺少冒号的问题"""
    # 匹配函数定义行但没有冒号的情况
    pattern = r'(def\s+\w+\s*\([^)]*\))\s*(?:\n\s*[^\s#])'
    replacement = r'\1:\n'
    return re.sub(pattern, replacement, content, flags=re.MULTILINE)

def fix_class_definitions(content):
    """修复类定义后缺少冒号的问题"""
    # 匹配类定义行但没有冒号的情况
    pattern = r'(class\s+\w+(?:\([^)]*\))?)\s*(?:\n\s*[^\s#])'
    replacement = r'\1:\n'
    return re.sub(pattern, replacement, content, flags=re.MULTILINE)

def fix_if_statements(content):
    """修复if语句后缺少冒号的问题"""
    pattern = r'(if\s+.*?)(?<!:)(?:\s*\n\s*[^\s#])'
    replacement = r'\1:\n'
    return re.sub(pattern, replacement, content, flags=re.MULTILINE)

def fix_for_loops(content):
    """修复for循环后缺少冒号的问题"""
    pattern = r'(for\s+.*?)(?<!:)(?:\s*\n\s*[^\s#])'
    replacement = r'\1:\n'
    return re.sub(pattern, replacement, content, flags=re.MULTILINE)

def fix_while_loops(content):
    """修复while循环后缺少冒号的问题"""
    pattern = r'(while\s+.*?)(?<!:)(?:\s*\n\s*[^\s#])'
    replacement = r'\1:\n'
    return re.sub(pattern, replacement, content, flags=re.MULTILINE)

def fix_try_blocks(content):
    """修复try块后缺少冒号的问题"""
    pattern = r'(try)(?<!:)(?:\s*\n\s*[^\s#])'
    replacement = r'\1:\n'
    return re.sub(pattern, replacement, content, flags=re.MULTILINE)

def fix_with_statements(content):
    """修复with语句后缺少冒号的问题"""
    pattern = r'(with\s+.*?)(?<!:)(?:\s*\n\s*[^\s#])'
    replacement = r'\1:\n'
    return re.sub(pattern, replacement, content, flags=re.MULTILINE)

def fix_decorators(content):
    """修复装饰器前的下划线问题"""
    # 修复 @@decorator 的问题
    pattern = r'_\s*=\s*(@\w+)'
    replacement = r'\1'
    return re.sub(pattern, replacement, content)

def fix_syntax_issues(file_path):
    """修复文件中的语法问题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 应用各种修复
        content = fix_function_definitions(content)
        content = fix_class_definitions(content)
        content = fix_if_statements(content)
        content = fix_for_loops(content)
        content = fix_while_loops(content)
        content = fix_try_blocks(content)
        content = fix_with_statements(content)
        content = fix_decorators(content)
        
        # 如果内容有变化，写回文件
        if content != original_content:
            # 创建备份
            backup_path = str(file_path) + '.bak'
            shutil.copy2(file_path, backup_path)
            
            # 写入修复后的内容
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        return False
    except Exception as e:
        print(f"修复文件 {file_path} 时出错: {e}")
        return False

def main():
    """主函数"""
    project_root = Path(__file__).parent.parent.parent
    fixed_count = 0
    error_count = 0
    
    print("开始全面修复项目中的语法错误...")
    
    # 遍历项目中的所有Python文件
    for py_file in project_root.rglob("*.py"):
        # 跳过备份文件和归档目录
        if 'backup' in str(py_file) or 'archive' in str(py_file):
            continue
            
        try:
            if fix_syntax_issues(py_file):
                print(f"✅ 已修复文件: {py_file}")
                fixed_count += 1
        except Exception as e:
            print(f"❌ 处理文件 {py_file} 时出错: {e}")
            error_count += 1
    
    print(f"\n修复完成!")
    print(f"成功修复: {fixed_count} 个文件")
    print(f"处理错误: {error_count} 个文件")

if __name__ == "__main__":
    main()