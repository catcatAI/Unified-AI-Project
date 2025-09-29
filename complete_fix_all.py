#!/usr/bin/env python3
"""
Complete fix script for all syntax errors in the project.
This script will fix all remaining syntax errors including:
1. _ = syntax errors
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
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixed_anything = False
        
        # Fix _ = "key": value syntax errors (dictionary syntax)
        pattern = r'_ = "([^"]+)":\s*([^,\n}]+)(,?)'
        replacement = r'"\1": \2\3'
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            content = new_content
            fixed_anything = True
            print(f"  Fixed dictionary syntax in {file_path}")
        
        # Fix _ = raise Exception syntax errors
        pattern = r'_ = raise\s+'
        replacement = r'raise '
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            content = new_content
            fixed_anything = True
            print(f"  Fixed raise syntax in {file_path}")
        
        # Fix _ = @decorator syntax errors
        pattern = r'_ = (@\w+)'
        replacement = r'\1'
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            content = new_content
            fixed_anything = True
            print(f"  Fixed decorator syntax in {file_path}")
        
        # Fix _ = assert syntax errors
        pattern = r'_ = assert\s+'
        replacement = r'assert '
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            content = new_content
            fixed_anything = True
            print(f"  Fixed assert syntax in {file_path}")
        
        # Fix _ = **kwargs syntax errors
        pattern = r'_ = \*\*(\w+)'
        replacement = r'**\1'
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            content = new_content
            fixed_anything = True
            print(f"  Fixed **kwargs syntax in {file_path}")
        
        # Fix incomplete imports
        pattern = r'from\s+[\w\.]+\s+import\s*\n'
        replacement = ''
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            content = new_content
            fixed_anything = True
            print(f"  Fixed incomplete import in {file_path}")
        
        # Fix keyword argument repeated errors
        # This is a more complex pattern to handle cases like _ = input_data.get('enhanced_features', False)
        pattern = r'_ = (\w+\.\w+\([^)]*\))'
        replacement = r'\1'
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            content = new_content
            fixed_anything = True
            print(f"  Fixed keyword argument syntax in {file_path}")
        
        # Fix dictionary syntax errors with variables as keys
        pattern = r'_ = ([\w]+):\s*([^,\n}]+)(,?)'
        replacement = r'\1: \2\3'
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            content = new_content
            fixed_anything = True
            print(f"  Fixed variable key dictionary syntax in {file_path}")
        
        # Fix indentation errors in __init__.py files
        if file_path.endswith('__init__.py'):
            lines = content.split('\n')
            new_lines = []
            for line in lines:
                # Remove leading spaces that cause unexpected indent
                if line.startswith('    ') and not any(line.lstrip().startswith(keyword) for keyword in ['from', 'import', 'class', 'def', 'if', 'elif', 'else', 'try', 'except', 'finally', 'with', 'for', 'while']):
                    new_lines.append(line.lstrip())
                    if line.lstrip():
                        fixed_anything = True
                        print(f"  Fixed indentation in {file_path}")
                else:
                    new_lines.append(line)
            content = '\n'.join(new_lines)
        
        # Write the fixed content back to the file if changes were made
        if fixed_anything:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  Successfully fixed syntax errors in {file_path}")
            return True
        elif content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  Successfully fixed syntax errors in {file_path}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"  Error fixing {file_path}: {str(e)}")
        return False

def get_all_python_files(root_dir):
    """Get all Python files in the project."""
    python_files = []
    for root, dirs, files in os.walk(root_dir):
        # Skip __pycache__ directories
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def main():
    """Main function to fix all syntax errors in the project."""
    print("Starting complete syntax error fix...")
    
    # Get all Python files in the project
    project_root = "."
    python_files = get_all_python_files(project_root)
    
    print(f"Found {len(python_files)} Python files to check.")
    
    fixed_files = 0
    error_files = []
    
    for file_path in python_files:
        try:
            if fix_syntax_errors_in_file(file_path):
                fixed_files += 1
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            error_files.append(file_path)
    
    print(f"\nFixed syntax errors in {fixed_files} files.")
    if error_files:
        print(f"Errors occurred in {len(error_files)} files:")
        for file in error_files:
            print(f"  {file}")
    
    print("\nRunning syntax check after fixes...")
    try:
        import subprocess
        result = subprocess.run(['python', '-m', 'compileall', '-q', '.'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("All syntax errors have been fixed!")
        else:
            print("Some syntax errors remain:")
            print(result.stdout)
            print(result.stderr)
    except Exception as e:
        print(f"Error running syntax check: {str(e)}")

if __name__ == "__main__":
    main()