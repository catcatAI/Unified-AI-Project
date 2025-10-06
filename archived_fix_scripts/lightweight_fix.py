#!/usr/bin/env python3
"""
轻量级批量修复脚本 - 直接修复常见语法错误
"""

import ast
import re
import sys
import traceback
from pathlib import Path

def fix_syntax_errors_in_file(file_path: Path) -> bool:
    """修复单个文件中的语法错误"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        content = original_content
        fixed_count = 0
        
        # 常见语法错误修复
        # 1. 修复未闭合的括号
        content = fix_unmatched_parentheses(content)
        
        # 2. 修复缩进问题
        content = fix_indentation_issues(content)
        
        # 3. 修复字符串引号问题
        content = fix_string_quote_issues(content)
        
        # 4. 修复缺少的冒号
        content = fix_missing_colons(content)
        
        # 5. 修复未完成的代码块
        content = fix_incomplete_blocks(content)
        
        if content != original_content:
            # 验证修复后的代码是否语法正确
            try:
                ast.parse(content)
                # 语法正确，写入文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✓ 已修复: {file_path}")
                return True
            except SyntaxError as e:
                print(f"✗ 修复后仍有语法错误: {file_path} - {e}")
                return False
        else:
            return False
            
    except Exception as e:
        print(f"✗ 无法处理文件 {file_path}: {e}")
        return False

def fix_unmatched_parentheses(content: str) -> str:
    """修复不匹配的括号"""
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        # 简单的括号平衡检查
        open_parens = line.count('(') + line.count('[') + line.count('{')
        close_parens = line.count(')') + line.count(']') + line.count('}')
        
        if open_parens > close_parens:
            # 尝试添加缺失的右括号
            missing = open_parens - close_parens
            for _ in range(missing):
                if '(' in line and ')' not in line[line.rfind('('):]:
                    line += ')'
                elif '[' in line and ']' not in line[line.rfind('['):]:
                    line += ']'
                elif '{' in line and '}' not in line[line.rfind('{'):]:
                    line += '}'
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_indentation_issues(content: str) -> str:
    """修复缩进问题"""
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        if line.strip() and not line.startswith('#'):
            # 检查是否需要缩进
            if any(line.strip().startswith(keyword) for keyword in ['def ', 'class ', 'if ', 'for ', 'while ', 'try:', 'except', 'finally']):
                # 确保有适当的缩进
                if i > 0 and not line.startswith(' '):
                    # 可能需要缩进
                    prev_line = lines[i-1].rstrip()
                    if prev_line.endswith(':') or prev_line.endswith('\\'):
                        line = '    ' + line
            
            # 修复意外的缩进
            if line.startswith('  ') and len(line.strip()) > 0:
                # 检查前一行是否为空或注释
                if i == 0 or not lines[i-1].strip() or lines[i-1].strip().startswith('#'):
                    line = line.lstrip()
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_string_quote_issues(content: str) -> str:
    """修复字符串引号问题"""
    # 修复未终止的三重引号字符串
    triple_quotes = ['"""', "'''"]
    
    for quote in triple_quotes:
        if content.count(quote) % 2 != 0:
            # 奇数个三重引号，需要修复
            lines = content.split('\n')
            in_string = False
            fixed_lines = []
            
            for line in lines:
                if quote in line:
                    in_string = not in_string
                
                if in_string and line.strip() == '' and quote not in line:
                    # 在字符串中的空行，可能是文件结尾
                    line += quote
                    in_string = False
                
                fixed_lines.append(line)
            
            content = '\n'.join(fixed_lines)
    
    return content

def fix_missing_colons(content: str) -> str:
    """修复缺少的冒号"""
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # 检查是否需要冒号
        if (stripped.startswith(('def ', 'class ', 'if ', 'for ', 'while ')) or
            stripped.startswith(('try', 'except', 'finally', 'else', 'elif'))):
            
            # 检查是否已经以冒号结尾
            if not stripped.endswith(':'):
                # 添加缺失的冒号
                line = line.rstrip() + ':'
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_incomplete_blocks(content: str) -> str:
    """修复不完整的代码块"""
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # 检查try语句是否完整
        if stripped == 'try:' and i < len(lines) - 1:
            next_line = lines[i + 1].strip()
            if not next_line and i + 2 < len(lines):
                # try: 后面是空行，然后是文件结尾
                fixed_lines.append(line)
                fixed_lines.append('    pass')
                fixed_lines.append('except:')
                fixed_lines.append('    pass')
                continue
        
        # 检查函数定义是否完整
        if stripped.startswith('def ') and stripped.endswith(':'):
            # 检查是否有函数体
            has_body = False
            for j in range(i + 1, min(i + 5, len(lines))):
                if lines[j].strip() and not lines[j].strip().startswith('#'):
                    has_body = True
                    break
            
            if not has_body:
                fixed_lines.append(line)
                fixed_lines.append('    pass')
                continue
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def scan_and_fix_python_files():
    """扫描并修复Python文件"""
    project_root = Path('D:/Projects/Unified-AI-Project')
    python_files = []
    
    # 查找所有Python文件（排除某些目录）
    excluded_dirs = {'node_modules', '__pycache__', '.git', 'venv', '.venv', 'backup', 'unified_fix_backups'}
    
    for py_file in project_root.rglob('*.py'):
        if any(excluded in str(py_file) for excluded in excluded_dirs):
            continue
        python_files.append(py_file)
    
    print(f"找到 {len(python_files)} 个Python文件")
    
    # 检查语法错误
    files_with_errors = []
    for py_file in python_files[:50]:  # 先处理前50个文件
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
        except SyntaxError:
            files_with_errors.append(py_file)
        except Exception:
            files_with_errors.append(py_file)
    
    print(f"发现 {len(files_with_errors)} 个文件有语法错误")
    
    # 修复有问题的文件
    fixed_count = 0
    for py_file in files_with_errors:
        if fix_syntax_errors_in_file(py_file):
            fixed_count += 1
    
    print(f"成功修复 {fixed_count} 个文件")
    return fixed_count

if __name__ == '__main__':
    fixed = scan_and_fix_python_files()
    print(f"修复完成，共修复 {fixed} 个文件")