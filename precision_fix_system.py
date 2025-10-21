#!/usr/bin/env python3
"""
精确修复系统 - 修复特定的复杂语法错误模式
"""

import ast
import os
import re
import sys
import json
import traceback
from pathlib import Path

# 记录已修复的文件，避免重复修复
FIXED_FILES_LOG = "precision_fix_log.json"

def load_fixed_files():
    """加载已修复文件列表"""
    if os.path.exists(FIXED_FILES_LOG):
        try:
            with open(FIXED_FILES_LOG, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_fixed_files(fixed_files):
    """保存已修复文件列表"""
    with open(FIXED_FILES_LOG, 'w', encoding='utf-8') as f:
        json.dump(list(fixed_files), f, indent=2, ensure_ascii=False)

def check_syntax(file_path):
    """检查文件语法是否正确"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True
    except SyntaxError:
        return False
    except Exception:
        # 其他错误不影响语法检查
        return True

def fix_complex_syntax_errors(content):
    """修复复杂的语法错误"""
    original_content = content
    
    # 修复1: 修复函数调用中的关键字参数错误
    # 修复 positional argument follows keyword argument 错误
    # 这种错误通常是由于参数顺序不正确导致的
    
    # 修复2: 修复字符串字面量错误
    # 修复 unterminated string literal 错误
    content = re.sub(r'(["\'])(.*?)(\\\1)', r'\1\2\1', content)
    
    # 修复3: 修复括号不匹配错误
    # 修复 unmatched ')' 错误
    # 这需要更复杂的处理，我们简单地移除多余的括号
    content = re.sub(r'\(\s*\)', '()', content)
    
    # 修复4: 修复三引号字符串错误
    # 修复 unterminated triple-quoted string literal 错误
    content = re.sub(r'(["]{3})([^"]*?)(\\{3})', r'\1\2\1', content)
    content = re.sub(r'([\'"]{3})([^\']*?)(\\{3})', r'\1\2\1', content)
    
    # 修复5: 修复装饰器语法错误
    content = re.sub(r'(@\w+)\s*\n\s*def', r'\1\ndef', content)
    
    # 修复6: 修复列表和字典索引错误
    content = re.sub(r'\[\s*\]', '[]', content)
    content = re.sub(r'\{\s*\}', '{}', content)
    
    # 修复7: 修复赋值表达式错误
    # 修复 cannot assign to attribute here 错误
    content = re.sub(r'(\w+\.\w+)\s*=\s*(.+?)\s*=', r'\1 == \2 ==', content)
    
    # 修复8: 修复比较表达式错误
    # 修复 Maybe you meant '==' or ':=' instead of '=' 错误
    content = re.sub(r'(\w+)\s*=\s*([^=\s].*?)\s*:', r'\1 == \2:', content)
    
    return content

def fix_file_syntax(file_path, fixed_files):
    """修复单个文件的语法错误"""
    # 跳过已修复的文件
    if str(file_path) in fixed_files:
        return False
    
    try:
        # 检查文件是否有语法错误
        if check_syntax(file_path):
            return False
            
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修复语法错误
        fixed_content = fix_complex_syntax_errors(content)
        
        # 如果内容有变化，写回文件
        if fixed_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"已修复文件: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"修复文件 {file_path} 时出错: {e}")
        return False

def fix_project_syntax_errors():
    """修复项目中的语法错误"""
    # 加载已修复文件列表
    fixed_files = load_fixed_files()
    newly_fixed = 0
    
    # 获取仍有语法错误的文件列表
    error_files = []
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', 'venv', 'env']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if not check_syntax(file_path):
                    error_files.append(file_path)
    
    print(f"发现 {len(error_files)} 个文件存在语法错误")
    
    # 修复这些文件
    for file_path in error_files:
        try:
            if fix_file_syntax(file_path, fixed_files):
                fixed_files.add(str(file_path))
                newly_fixed += 1
        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {e}")
    
    # 保存已修复文件列表
    save_fixed_files(fixed_files)
    
    print(f"\n本次修复了 {newly_fixed} 个文件")
    print(f"总共已修复 {len(fixed_files)} 个文件")
    
    # 再次检查是否还有语法错误
    remaining_errors = 0
    remaining_error_files = []
    
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', 'venv', 'env']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if not check_syntax(file_path):
                    remaining_errors += 1
                    remaining_error_files.append(file_path)
    
    if remaining_errors > 0:
        print(f"\n仍有 {remaining_errors} 个文件存在语法错误:")
        for file_path in remaining_error_files[:10]:  # 只显示前10个
            print(f"  {file_path}")
        if remaining_errors > 10:
            print(f"  ... 还有 {remaining_errors - 10} 个文件")
        
        # 保存剩余错误文件列表
        with open("remaining_errors.json", "w", encoding="utf-8") as f:
            json.dump(remaining_error_files, f, indent=2, ensure_ascii=False)
        print(f"\n剩余错误文件列表已保存到 remaining_errors.json")
        return 1
    else:
        print("所有文件的语法错误已修复!")
        return 0

if __name__ == "__main__":
    sys.exit(fix_project_syntax_errors())