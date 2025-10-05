#!/usr/bin/env python3
"""
修复项目中剩余的语法错误
"""

import os
import re
from pathlib import Path

def fix_missing_colons(file_path):
    """修复缺少冒号的语法错误"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修复类定义缺少冒号的问题
        content = re.sub(r'class\s+(\w+\s*\([^)]*\))\s*(?=\n)', r'class \1:', content)
        content = re.sub(r'class\s+(\w+)\s*(?=\n)', r'class \1:', content)
        
        # 修复函数定义缺少冒号的问题
        content = re.sub(r'def\s+(\w+\s*\([^)]*\))\s*(?=\n)', r'def \1:', content)
        
        # 修复if语句缺少冒号的问题
        content = re.sub(r'if\s+(.+?)\s*(?=\n)', r'if \1:', content)
        
        # 修复for循环缺少冒号的问题
        content = re.sub(r'for\s+(.+?)\s*(?=\n)', r'for \1:', content)
        
        # 修复try语句缺少冒号的问题
        content = re.sub(r'try\s*(?=\n)', r'try:', content)
        
        # 修复except语句缺少冒号的问题
        content = re.sub(r'except\s*(?=\n)', r'except:', content)
        content = re.sub(r'except\s+(.+?)\s*(?=\n)', r'except \1:', content)
        
        # 修复with语句缺少冒号的问题
        content = re.sub(r'with\s+(.+?)\s*(?=\n)', r'with \1:', content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"✓ 修复了缺少冒号的问题: {file_path}")
        return True
    except Exception as e:
        print(f"✗ 修复缺少冒号时出错: {file_path} - {e}")
        return False

def fix_invalid_syntax(file_path):
    """修复无效语法错误"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修复无效的语法错误
        content = content.replace('MemoryStorage:', 'MemoryStorage')
        content = content.replace('ModelRegistry:', 'ModelRegistry')
        content = content.replace('components: Dict[str, Any] =', 'components: Dict[str, Any] = {}')
        content = content.replace('import .c4_utils', 'from . import c4_utils')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"✓ 修复了无效语法错误: {file_path}")
        return True
    except Exception as e:
        print(f"✗ 修复无效语法时出错: {file_path} - {e}")
        return False

def fix_indentation_errors(file_path):
    """修复缩进错误"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        fixed_lines = []
        for i, line in enumerate(lines):
            # 如果当前行是类或函数定义后的空行，添加pass语句
            if (line.strip().endswith(':') and 
                i + 1 < len(lines) and 
                lines[i + 1].strip() == ''):
                fixed_lines.append(line)
                fixed_lines.append('    pass\n')
            else:
                fixed_lines.append(line)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)
            
        print(f"✓ 修复了缩进错误: {file_path}")
        return True
    except Exception as e:
        print(f"✗ 修复缩进错误时出错: {file_path} - {e}")
        return False

def fix_syntax_errors_in_file(file_path):
    """修复单个文件中的语法错误"""
    print(f"正在修复文件: {file_path}")
    
    # 修复缺少冒号的问题
    fix_missing_colons(file_path)
    
    # 修复无效语法错误
    fix_invalid_syntax(file_path)
    
    # 修复缩进错误
    fix_indentation_errors(file_path)

def main():
    """主函数"""
    print("开始修复项目中剩余的语法错误...")
    print("=" * 50)
    
    # 获取所有Python文件
    python_files = list(Path(".").rglob("*.py"))
    
    # 过滤掉已归档的文件和备份文件
    filtered_files = [
        f for f in python_files 
        if "project_archives" not in str(f) and 
           "backup" not in str(f) and
           "venv" not in str(f)
    ]
    
    print(f"发现 {len(filtered_files)} 个Python文件需要检查")
    
    # 修复语法错误
    fixed_count = 0
    for file_path in filtered_files:
        try:
            fix_syntax_errors_in_file(file_path)
            fixed_count += 1
        except Exception as e:
            print(f"✗ 处理文件时出错: {file_path} - {e}")
    
    print("\n" + "=" * 50)
    print(f"✓ 成功处理了 {fixed_count} 个文件!")
    
    # 验证修复结果
    print("\n验证修复结果...")
    os.system("python -m compileall -q .")
    
    return 0

if __name__ == "__main__":
    exit(main())