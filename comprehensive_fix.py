#!/usr/bin/env python3
"""
Comprehensive script to fix remaining syntax errors in the project.
"""

import os
import re

def fix_syntax_errors_in_file(file_path):
    """Fix various syntax errors in a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        changes_made = False

        # Fix _ = "key" value syntax errors (dictionary syntax)
        pattern = r'_ = "([^"]+)":\s*([^,\n}]+)(,?)'
        replacement = r'"\1": \2\3'
        content = re.sub(pattern, replacement, content)

        # Fix _ = 'key' value syntax errors (dictionary syntax)
        pattern = r"_ = '([^']+)':\s*([^,\n}]+)(,?)"
        replacement = r"'\1': \2\3"
        content = re.sub(pattern, replacement, content)

        # Fix _ = raise Exception syntax errors
        content = re.sub(r'_ = raise\s+', 'raise ', content)

        # Fix _ = import syntax errors
        content = re.sub(r'_ = import\s+', 'import ', content)

        # Fix _ = from syntax errors
        content = re.sub(r'_ = from\s+', 'from ', content)

        # Fix _ = def syntax errors
        content = re.sub(r'_ = def\s+', 'def ', content)

        # Fix _ = class syntax errors
        content = re.sub(r'_ = class\s+', 'class ', content)

        # Fix _ = if syntax errors
        content = re.sub(r'_ = if\s+', 'if ', content)

        # Fix _ = for syntax errors
        content = re.sub(r'_ = for\s+', 'for ', content)

        # Fix _ = while syntax errors
        content = re.sub(r'_ = while\s+', 'while ', content)

        # Fix _ = try syntax errors
        content = re.sub(r'_ = try\s+', 'try ', content)

        # Fix _ = with syntax errors
        content = re.sub(r'_ = with\s+', 'with ', content)

        # Fix _ = assert syntax errors
        content = re.sub(r'_ = assert\s+', 'assert ', content)

        # Fix _ = return syntax errors
        content = re.sub(r'_ = return\s+', 'return ', content)

        # Fix _ = yield syntax errors
        content = re.sub(r'_ = yield\s+', 'yield ', content)

        # Fix _ = global syntax errors
        content = re.sub(r'_ = global\s+', 'global ', content)

        # Fix _ = nonlocal syntax errors
        content = re.sub(r'_ = nonlocal\s+', 'nonlocal ', content)

        # Fix _ = pass syntax errors
        content = re.sub(r'_ = pass\s+', 'pass ', content)

        # Fix _ = break syntax errors
        content = re.sub(r'_ = break\s+', 'break ', content)

        # Fix _ = continue syntax errors
        content = re.sub(r'_ = continue\s+', 'continue ', content)

        # Write the fixed content back to the file if anything was fixed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Successfully fixed syntax errors in {file_path}")
            return True
        else:
            print(f"No syntax errors found in {file_path}")
            return False

    except Exception as e:
        print(f"Error fixing syntax errors in {file_path}: {e}")
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

    for root, dirs, files in os.walk(root_path):
        # 排除不需要检查的目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]

        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                # 检查文件是否有语法错误
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    ast.parse(content)
                except SyntaxError:
                    python_files_with_errors.append(file_path)
                except Exception:
                    # 文件可能有其他问题，也加入列表
                    python_files_with_errors.append(file_path)
    
    return python_files_with_errors

def main():
    """Main function to fix all syntax errors in the project."""
    print("Starting comprehensive syntax fix for all Python files...")
    
    # 获取项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # 查找所有有语法错误的Python文件
    files_with_errors = find_python_files_with_syntax_errors(project_root)
    
    print(f"Found {len(files_with_errors)} Python files with syntax errors")
    
    # 修复每个文件
    fixed_count = 0
    for file_path in files_with_errors:
        print(f"Processing {file_path}...")
        if fix_syntax_errors_in_file(file_path):
            fixed_count += 1
    
    print(f"Fixed syntax errors in {fixed_count} files")
    print("Comprehensive syntax fix finished.")

if __name__ == "__main__":
    main()