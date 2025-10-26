#!/usr/bin/env python3
"""
修复项目中的语法错误，特别是括号不匹配和缺少冒号的问题
"""

import os
import re
import ast
from pathlib import Path

def check_syntax(file_path):
    """检查文件语法是否正确"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, str(e)
    except Exception as e:
        return False, f"其他错误: {e}"

def fix_missing_colons(content):
    """修复缺少冒号的问题"""
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # 跳过空行和注释
        if not stripped or stripped.startswith('#'):
            fixed_lines.append(line)
            continue
            
        # 检查是否需要冒号
        if (stripped.startswith(('class ', 'def ', 'if ', 'elif ', 'else', 'for ', 'while ', 'try', 'except', 'finally', 'with ')) and 
            not stripped.endswith(':') and 
            not stripped.startswith('else') and  # 特殊处理else
            not stripped.startswith('finally')):  # 特殊处理finally
            
            # 处理else和finally的特殊情况
            if stripped.startswith('else') or stripped.startswith('finally'):
                if not stripped.endswith(':'):
                    fixed_line = line.rstrip() + ':'
                    fixed_lines.append(fixed_line)
                else:
                    fixed_lines.append(line)
            else:
                # 在行尾添加冒号
                fixed_line = line.rstrip() + ':'
                fixed_lines.append(fixed_line)
        else:
            fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_unmatched_parentheses(content):
    """修复不匹配的括号"""
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        # 修复圆括号
        open_parens = line.count('(')
        close_parens = line.count(')')
        
        if open_parens > close_parens:
            line += ')' * (open_parens - close_parens)
        elif close_parens > open_parens:
            # 在行首添加缺失的左括号（简化处理）
            line = '(' * (close_parens - open_parens) + line
        
        # 修复方括号
        open_brackets = line.count('[')
        close_brackets = line.count(']')
        
        if open_brackets > close_brackets:
            line += ']' * (open_brackets - close_brackets)
        elif close_brackets > open_brackets:
            line = '[' * (close_brackets - open_brackets) + line
        
        # 修复花括号
        open_braces = line.count('{')
        close_braces = line.count('}')
        
        if open_braces > close_braces:
            line += '}' * (open_braces - close_braces)
        elif close_braces > open_braces:
            line = '{' * (close_braces - open_braces) + line
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_file_syntax(file_path):
    """修复单个文件的语法错误"""
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 应用修复
        content = fix_missing_colons(content)
        content = fix_unmatched_parentheses(content)
        
        # 如果内容有变化，写回文件
        if content != original_content:
            # 创建备份
            backup_path = str(file_path) + '.backup'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # 写入修复后的内容
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 验证修复后的语法
            is_valid, error = check_syntax(file_path)
            if is_valid:
                print(f"✓ 成功修复: {file_path}")
                return True
            else:
                # 如果修复后仍有语法错误，恢复原始内容
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                print(f"✗ 修复失败（引入新错误）: {file_path} - {error}")
                return False
        else:
            # 验证原始文件语法
            is_valid, error = check_syntax(file_path)
            if is_valid:
                print(f"✓ 无需修复: {file_path}")
                return True
            else:
                print(f"✗ 语法错误（未修复）: {file_path} - {error}")
                return False
                
    except Exception as e:
        print(f"✗ 处理文件时出错: {file_path} - {e}")
        return False

def get_python_files(root_dir):
    """获取项目中的所有Python文件"""
    python_files = []
    exclude_dirs = {'.git', '__pycache__', 'venv', '.venv', 'node_modules', 'backup'}
    
    for root, dirs, files in os.walk(root_dir):
        # 排除特定目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    return python_files

def main():
    """主函数"""
    print("开始修复项目中的语法错误...")
    
    # 获取所有Python文件
    python_files = get_python_files('.')
    print(f"找到 {len(python_files)} 个Python文件")
    
    # 先检查有多少文件有语法错误
    files_with_errors = []
    for file_path in python_files:
        is_valid, error = check_syntax(file_path)
        if not is_valid:
            files_with_errors.append((file_path, error))
    
    print(f"发现 {len(files_with_errors)} 个文件存在语法错误")
    
    # 修复有语法错误的文件
    fixed_count = 0
    for file_path, error in files_with_errors:
        print(f"正在修复: {file_path} - {error}")
        if fix_file_syntax(file_path):
            fixed_count += 1
    
    print(f"\n修复完成! 成功修复 {fixed_count}/{len(files_with_errors)} 个文件")

if __name__ == "__main__":
    main()