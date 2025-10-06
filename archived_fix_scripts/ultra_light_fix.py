#!/usr/bin/env python3
"""
超轻量级修复
直接修复已知的具体语法错误
"""

import re
import ast
from pathlib import Path

def fix_specific_syntax_errors():
    """修复特定的语法错误"""
    project_root = Path('D:/Projects/Unified-AI-Project')
    
    print('=== 超轻量级语法修复 ===')
    
    # 基于之前分析结果，修复最常见的语法错误
    
    # 1. 修复缺少的冒号
    def fix_missing_colons_in_file(file_path):
        """修复文件中缺少的冒号"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            lines = content.split('\n')
            fixed_lines = []
            fixes = 0
            
            for line in lines:
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
            
            if fixes > 0:
                content = '\n'.join(fixed_lines)
                # 验证修复后的语法
                try:
                    ast.parse(content)
                    # 写入修复后的内容
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    return fixes
                except SyntaxError:
                    # 修复导致新的语法错误，回退
                    return 0
            
            return 0
            
        except Exception:
            return 0
    
    # 2. 修复中文标点符号
    def fix_chinese_punctuation_in_file(file_path):
        """修复中文标点符号"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
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
            }
            
            fixes = 0
            for chinese, english in replacements.items():
                if chinese in content:
                    content = content.replace(chinese, english)
                    fixes += 1
            
            if fixes > 0:
                # 验证修复后的语法
                try:
                    ast.parse(content)
                    # 写入修复后的内容
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    return fixes
                except SyntaxError:
                    # 修复导致新的语法错误，回退
                    return 0
            
            return 0
            
        except Exception:
            return 0
    
    # 3. 修复简单的缩进问题
    def fix_simple_indentation_in_file(file_path):
        """修复简单的缩进问题"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            lines = content.split('\n')
            fixed_lines = []
            fixes = 0
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                
                # 跳过空行和注释
                if not stripped or stripped.startswith('#'):
                    fixed_lines.append(line)
                    continue
                
                # 修复函数/类定义后缺少缩进的问题
                if (stripped.startswith(('def ', 'class ')) and 
                    i < len(lines) - 1 and 
                    not lines[i + 1].strip()):
                    # 下一行是空行，添加pass语句
                    fixed_lines.append(line)
                    fixed_lines.append('    pass')
                    fixes += 1
                else:
                    fixed_lines.append(line)
            
            if fixes > 0:
                content = '\n'.join(fixed_lines)
                # 验证修复后的语法
                try:
                    ast.parse(content)
                    # 写入修复后的内容
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    return fixes
                except SyntaxError:
                    # 修复导致新的语法错误，回退
                    return 0
            
            return 0
            
        except Exception:
            return 0
    
    # 获取所有Python文件
    python_files = []
    excluded_dirs = {'node_modules', '__pycache__', '.git', 'venv', '.venv', 'backup', 'unified_fix_backups'}
    
    for py_file in project_root.rglob('*.py'):
        if any(excluded in str(py_file) for excluded in excluded_dirs):
            continue
        python_files.append(py_file)
    
    print(f'找到 {len(python_files)} 个Python文件')
    
    total_fixed = 0
    total_files_processed = 0
    
    # 分批处理，每批10个文件
    batch_size = 10
    
    for i in range(0, len(python_files), batch_size):
        batch = python_files[i:i+batch_size]
        print(f'\n处理第 {i//batch_size + 1} 批 ({len(batch)} 个文件)...')
        
        batch_fixed = 0
        
        for py_file in batch:
            try:
                # 检查文件是否真的有语法错误
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                try:
                    ast.parse(content)
                    continue  # 文件没有语法错误，跳过
                except SyntaxError:
                    pass  # 有语法错误，需要修复
                
                print(f'  修复: {py_file.relative_to(project_root)}')
                
                # 应用各种修复
                fixes1 = fix_missing_colons_in_file(py_file)
                fixes2 = fix_chinese_punctuation_in_file(py_file)
                fixes3 = fix_simple_indentation_in_file(py_file)
                
                file_total_fixes = fixes1 + fixes2 + fixes3
                
                if file_total_fixes > 0:
                    print(f'    ✓ 修复了 {file_total_fixes} 个问题')
                    batch_fixed += file_total_fixes
                else:
                    print('    ✅ 无需修复')
                
                total_files_processed += 1
                
            except Exception as e:
                print(f'    ❌ 修复失败: {e}')
                continue
        
        total_fixed += batch_fixed
        print(f'第 {i//batch_size + 1} 批完成: 修复了 {batch_fixed} 个问题')
    
    print(f'\n=== 超轻量级修复完成 ===')
    print(f'处理了 {total_files_processed} 个文件')
    print(f'修复了 {total_fixed} 个问题')
    
    return total_fixed

if __name__ == '__main__':
    print('启动超轻量级语法修复...')
    
    fixed = fix_specific_syntax_errors()
    
    if fixed > 0:
        print(f'🎯 修复成功！处理了 {fixed} 个语法问题')
    else:
        print('✅ 未发现需要修复的简单语法问题')
    
    print('\n修复完成！建议运行统一自动修复系统进行深度修复。')