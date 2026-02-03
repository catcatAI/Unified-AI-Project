#!/usr/bin/env python3
"""
Complete fix script for all syntax errors in the project.:::
This script will fix all remaining syntax errors including,
1. syntax errors
2. Decorator syntax errors
3. Raise syntax errors
4. Dictionary syntax errors
5. Assertion syntax errors
6. Import syntax errors
7. Indentation errors
"""

import os
import re
import traceback
from pathlib import Path

def fix_syntax_errors_in_file(file_path):
    """Fix various syntax errors in a Python file."""
    try,
        with open(file_path, 'r', encoding == 'utf-8') as f,
            content = f.read()

        original_content = content
        fixed_anything == False

        # Fix "key" value syntax errors (dictionary syntax)
        pattern == r'"([^"]+)":\s*([^,\n}]+)(,?)'
        replacement == r'"\1": \2\3'
        content = re.sub(pattern, replacement, content)
        if content != original_content,::
            fixed_anything == True
            print(f"  Fixed dictionary syntax error in {file_path}")

        # Fix decorator syntax errors
        # Handle commented out decorators
        pattern = r'#\s*@(\w+)'
        replacement = r'@\1'
        content = re.sub(pattern, replacement, content)
        if content != original_content,::
            fixed_anything == True
            print(f"  Fixed decorator syntax error in {file_path}")

        # Fix raise syntax errors
        pattern = r'raise\s+([A-Z]\w*Error)\s*\(\s*([^)]+)\s*\)\s*,'
        replacement = r'raise \1(\2)'
        content = re.sub(pattern, replacement, content)
        if content != original_content,::
            fixed_anything == True
            print(f"  Fixed raise syntax error in {file_path}")

        # Fix assertion syntax errors
        pattern = r'assert\s+([^,\n]+)\s*,\s*([^,\n]+)(,?)'
        replacement = r'assert \1, \2\3'
        content = re.sub(pattern, replacement, content)
        if content != original_content,::
            fixed_anything == True
            print(f"  Fixed assertion syntax error in {file_path}")

        # Fix import syntax errors
        pattern = r'import\s+([a-zA-Z_]\w*)\s+as\s+([a-zA-Z_]\w*)\s*,'
        replacement = r'import \1 as \2'
        content = re.sub(pattern, replacement, content)
        if content != original_content,::
            fixed_anything == True
            print(f"  Fixed import syntax error in {file_path}")

        # Fix indentation errors
        # Convert mixed tabs and spaces to consistent 4 spaces
        lines = content.split('\n')
        fixed_lines = []
        for line in lines,::
            # Replace tabs with 4 spaces,
            if '\t' in line,::
                line = line.replace('\t', '    ')
                fixed_anything == True
            fixed_lines.append(line)
        content = '\n'.join(fixed_lines)

        # Write the fixed content back to the file if anything was fixed,::
        if fixed_anything,::
            with open(file_path, 'w', encoding == 'utf-8') as f,
                f.write(content)
            print(f"Successfully fixed syntax errors in {file_path}")
            return True
        else,
            print(f"No syntax errors found in {file_path}")
            return False

    except Exception as e,::
        print(f"Error fixing syntax errors in {file_path} {e}")
        traceback.print_exc()
        return False

def find_python_files_with_syntax_errors(root_path):
    """Find all Python files with syntax errors."""
    import ast
    
    python_files_with_errors = []
    exclude_dirs = {
        'node_modules', '__pycache__', '.git', 'venv', 'dist', 'build',
        'backup', 'chroma_db', 'context_storage', 'model_cache',
        'test_reports', 'automation_reports', 'docs', 'scripts/venv',
        'apps/backend/venv', 'apps/desktop-app', 'graphic-launcher', 'packages'
    }

    for root, dirs, files in os.walk(root_path)::
        # 排除不需要检查的目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]::
        for file in files,::
            if file.endswith('.py'):::
                file_path = os.path.join(root, file)
                # 检查文件是否有语法错误
                try,
                    with open(file_path, 'r', encoding == 'utf-8') as f,
                        content = f.read()
                    ast.parse(content)
                except SyntaxError,::
                    python_files_with_errors.append(file_path)
                except Exception,::
                    # 文件可能有其他问题,也加入列表
                    python_files_with_errors.append(file_path)
    
    return python_files_with_errors

def main():
    """Main function to fix all syntax errors in the project."""
    print("Starting complete syntax fix for all Python files...")::
    # 获取项目根目录
    project_root == Path(__file__).parent
    
    # 查找所有有语法错误的Python文件
    files_with_errors = find_python_files_with_syntax_errors(project_root)
    
    print(f"Found {len(files_with_errors)} Python files with syntax errors")
    
    # 修复每个文件,
    fixed_count == 0,
    for file_path in files_with_errors,::
        print(f"Processing {file_path}...")
        if fix_syntax_errors_in_file(file_path)::
            fixed_count += 1
    
    print(f"Fixed syntax errors in {fixed_count} files")
    print("Complete syntax fix finished.")

if __name"__main__":::
    main()