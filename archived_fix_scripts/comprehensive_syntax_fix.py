#!/usr/bin/env python3
"""
全面语法错误修复脚本
修复更多类型的语法错误
"""

import ast
import re
import sys
import traceback
from pathlib import Path
from typing import List, Tuple, Optional

def analyze_syntax_errors(file_path: Path) -> List[str]:
    """分析文件中的语法错误"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return []
    except SyntaxError as e:
        return [str(e)]
    except Exception as e:
        return [str(e)]

def fix_comprehensive_syntax_errors(file_path: Path) -> Tuple[bool, int]:
    """全面修复文件中的语法错误"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        content = original_content
        fixes_applied = 0
        
        # 1. 修复明显的缩进错误
        content, indent_fixes = fix_indentation_errors(content)
        fixes_applied += indent_fixes
        
        # 2. 修复括号匹配问题
        content, bracket_fixes = fix_bracket_matching(content)
        fixes_applied += bracket_fixes
        
        # 3. 修复字符串引号问题
        content, quote_fixes = fix_quote_issues(content)
        fixes_applied += quote_fixes
        
        # 4. 修复缺少的冒号
        content, colon_fixes = fix_missing_colons_detailed(content)
        fixes_applied += colon_fixes
        
        # 5. 修复不完整的代码结构
        content, structure_fixes = fix_incomplete_structures(content)
        fixes_applied += structure_fixes
        
        # 6. 修复中文标点符号
        content, punctuation_fixes = fix_chinese_punctuation(content)
        fixes_applied += punctuation_fixes
        
        # 7. 修复明显的拼写错误
        content, spelling_fixes = fix_common_spelling_errors(content)
        fixes_applied += spelling_fixes
        
        if content != original_content:
            # 验证修复后的代码
            try:
                ast.parse(content)
                # 语法正确，写入文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✓ 已修复 {fixes_applied} 个问题: {file_path}")
                return True, fixes_applied
            except SyntaxError as e:
                print(f"✗ 修复后仍有语法错误: {file_path} - {e}")
                return False, 0
        else:
            return False, 0
            
    except Exception as e:
        print(f"✗ 无法处理文件 {file_path}: {e}")
        return False, 0

def fix_indentation_errors(content: str) -> Tuple[str, int]:
    """修复缩进错误"""
    lines = content.split('\n')
    fixed_lines = []
    fixes = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # 跳过空行和注释
        if not stripped or stripped.startswith('#'):
            fixed_lines.append(line)
            continue
        
        # 修复意外的缩进
        if line.startswith('  ') and len(line.strip()) > 0:
            # 检查是否是文件开头或前一行是空行
            if i == 0 or not lines[i-1].strip():
                fixed_lines.append(line.lstrip())
                fixes += 1
                continue
        
        # 修复缺少的缩进
        if stripped.startswith(('def ', 'class ', 'if ', 'for ', 'while ', 'try:', 'except', 'finally', 'else:', 'elif ')):
            if i > 0 and lines[i-1].strip().endswith(':'):
                # 前一行以冒号结尾，这一行应该有缩进
                if not line.startswith(' '):
                    line = '    ' + line
                    fixes += 1
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines), fixes

def fix_bracket_matching(content: str) -> Tuple[str, int]:
    """修复括号匹配问题"""
    lines = content.split('\n')
    fixed_lines = []
    fixes = 0
    
    for line in lines:
        original_line = line
        
        # 检查并修复圆括号
        open_parens = line.count('(')
        close_parens = line.count(')')
        if open_parens > close_parens:
            line += ')' * (open_parens - close_parens)
            fixes += 1
        
        # 检查并修复方括号
        open_brackets = line.count('[')
        close_brackets = line.count(']')
        if open_brackets > close_brackets:
            line += ']' * (open_brackets - close_brackets)
            fixes += 1
        
        # 检查并修复花括号
        open_braces = line.count('{')
        close_braces = line.count('}')
        if open_braces > close_braces:
            line += '}' * (open_braces - close_braces)
            fixes += 1
        
        if line != original_line:
            fixes += 1
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines), fixes

def fix_quote_issues(content: str) -> Tuple[str, int]:
    """修复引号问题"""
    fixes = 0
    
    # 修复未终止的三重引号
    for quote in ['"""', "'''"]:
        count = content.count(quote)
        if count % 2 != 0:
            # 奇数个三重引号，添加缺失的
            content += quote
            fixes += 1
    
    # 修复未终止的单引号和双引号
    lines = content.split('\n')
    fixed_lines = []
    in_string = False
    string_char = None
    
    for line in lines:
        if not in_string:
            # 检查是否开始新的字符串
            if '"' in line and not line.strip().startswith('#'):
                # 简单检查：如果引号数量是奇数，可能未终止
                if line.count('"') % 2 != 0:
                    line += '"'
                    fixes += 1
            elif "'" in line and not line.strip().startswith('#'):
                if line.count("'") % 2 != 0:
                    line += "'"
                    fixes += 1
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines), fixes

def fix_missing_colons_detailed(content: str) -> Tuple[str, int]:
    """详细修复缺少的冒号"""
    lines = content.split('\n')
    fixed_lines = []
    fixes = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # 检查需要冒号的关键字
        if (stripped.startswith(('def ', 'class ', 'if ', 'for ', 'while ', 'try')) or
            stripped.startswith(('except', 'finally', 'else:', 'elif '))):
            
            # 检查是否已经以冒号结尾
            if not stripped.endswith(':'):
                # 添加冒号
                line = line.rstrip() + ':'
                fixes += 1
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines), fixes

def fix_incomplete_structures(content: str) -> Tuple[str, int]:
    """修复不完整的代码结构"""
    lines = content.split('\n')
    fixed_lines = []
    fixes = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # 修复不完整的try语句
        if stripped == 'try:' and i < len(lines) - 1:
            next_line = lines[i + 1].strip()
            if not next_line or next_line.startswith('#'):
                # try: 后面没有实际内容
                fixed_lines.append(line)
                fixed_lines.append('    pass')
                fixes += 1
                continue
        
        # 修复不完整的函数定义
        if stripped.startswith('def ') and stripped.endswith(':'):
            # 检查函数体
            has_body = False
            for j in range(i + 1, min(i + 5, len(lines))):
                if lines[j].strip() and not lines[j].strip().startswith('#'):
                    has_body = True
                    break
            
            if not has_body:
                fixed_lines.append(line)
                fixed_lines.append('    pass')
                fixes += 1
                continue
        
        # 修复不完整的类定义
        if stripped.startswith('class ') and stripped.endswith(':'):
            # 检查类体
            has_body = False
            for j in range(i + 1, min(i + 5, len(lines))):
                if lines[j].strip() and not lines[j].strip().startswith('#'):
                    has_body = True
                    break
            
            if not has_body:
                fixed_lines.append(line)
                fixed_lines.append('    pass')
                fixes += 1
                continue
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines), fixes

def fix_chinese_punctuation(content: str) -> Tuple[str, int]:
    """修复中文标点符号"""
    fixes = 0
    
    # 常见的中文标点符号替换
    replacements = {
        '，': ',',  # 中文逗号
        '。': '.',  # 中文句号
        '：': ':',  # 中文冒号
        '；': ';',  # 中文分号
        '（': '(',  # 中文左括号
        '）': ')',  # 中文右括号
        '【': '[',  # 中文左方括号
        '】': ']',  # 中文右方括号
        '「': '"',  # 中文左引号
        '」': '"',  # 中文右引号
        '『': '"',  # 中文左引号
        '』': '"',  # 中文右引号
    }
    
    for chinese, english in replacements.items():
        if chinese in content:
            content = content.replace(chinese, english)
            fixes += 1
    
    return content, fixes

def fix_common_spelling_errors(content: str) -> Tuple[str, int]:
    """修复常见的拼写错误"""
    fixes = 0
    
    # 常见的拼写错误和修正
    spelling_corrections = {
        'pritn': 'print',
        'prnt': 'print',
        'retrun': 'return',
        'retunr': 'return',
        'defn': 'def',
        'fucntion': 'function',
        'funciton': 'function',
        'calss': 'class',
        'improt': 'import',
        'form': 'from',  # 注意上下文
        'exept': 'except',
        'finnaly': 'finally',
    }
    
    for wrong, correct in spelling_corrections.items():
        if wrong in content:
            content = content.replace(wrong, correct)
            fixes += 1
    
    return content, fixes

def scan_and_fix_project():
    """扫描并修复整个项目"""
    project_root = Path('D:/Projects/Unified-AI-Project')
    
    # 查找所有Python文件
    python_files = []
    excluded_dirs = {'node_modules', '__pycache__', '.git', 'venv', '.venv', 'backup', 'unified_fix_backups', 'dist', 'build'}
    
    for py_file in project_root.rglob('*.py'):
        if any(excluded in str(py_file) for excluded in excluded_dirs):
            continue
        python_files.append(py_file)
    
    print(f"找到 {len(python_files)} 个Python文件")
    
    # 分批处理，先处理前100个
    batch_size = 100
    batches = [python_files[i:i+batch_size] for i in range(0, len(python_files), batch_size)]
    
    total_files_with_errors = 0
    total_files_fixed = 0
    total_fixes_applied = 0
    
    for batch_num, batch_files in enumerate(batches[:1]):  # 先处理第一批
        print(f"\n处理第 {batch_num + 1} 批文件 ({len(batch_files)} 个)...")
        
        batch_files_with_errors = 0
        batch_files_fixed = 0
        batch_fixes_applied = 0
        
        for py_file in batch_files:
            errors = analyze_syntax_errors(py_file)
            if errors:
                batch_files_with_errors += 1
                print(f"  发现语法错误: {py_file}")
                for error in errors:
                    print(f"    - {error}")
                
                # 尝试修复
                fixed, fixes = fix_comprehensive_syntax_errors(py_file)
                if fixed:
                    batch_files_fixed += 1
                    batch_fixes_applied += fixes
        
        total_files_with_errors += batch_files_with_errors
        total_files_fixed += batch_files_fixed
        total_fixes_applied += batch_fixes_applied
        
        print(f"第 {batch_num + 1} 批结果:")
        print(f"  发现错误文件: {batch_files_with_errors}")
        print(f"  成功修复文件: {batch_files_fixed}")
        print(f"  应用修复数: {batch_fixes_applied}")
    
    print(f"\n总计结果:")
    print(f"  发现错误文件: {total_files_with_errors}")
    print(f"  成功修复文件: {total_files_fixed}")
    print(f"  应用修复数: {total_fixes_applied}")
    
    return total_files_fixed

if __name__ == '__main__':
    fixed = scan_and_fix_project()
    print(f"\n修复完成，共修复 {fixed} 个文件")
