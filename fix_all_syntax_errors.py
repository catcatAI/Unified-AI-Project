#!/usr/bin/env python3
"""
Comprehensive script to fix all syntax errors in the project.
"""

import os
import re
import traceback

def fix_syntax_errors_in_file(file_path):
    """Fix various syntax errors in a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = False
        
        # Fix _ = "key": value syntax errors (dictionary syntax)
        pattern = r'_ = "([^"]+)":\s*([^,\n}]+)(,?)'
        replacement = r'"\1": \2\3'
        content = re.sub(pattern, replacement, content)
        
        # Fix _ = raise Exception syntax errors
        content = re.sub(r'_ = raise\s+', 'raise ', content)
        
        # Fix _ = @decorator syntax errors
        content = re.sub(r'_ = (@\w+)', r'\1', content)
        
        # Fix _ = assert syntax errors
        content = re.sub(r'_ = assert\s+', 'assert ', content)
        
        # Fix _ = **kwargs syntax errors
        content = re.sub(r'_ = \*\*(\w+)', r'**\1', content)
        
        # Fix dictionary syntax errors with variables as keys
        content = re.sub(r'_ = ([\w]+):\s*([^,\n}]+)(,?)', r'\1: \2\3', content)
        
        # Fix incomplete imports
        content = re.sub(r'from\s+[\w\.]+\s+import\s*\n', '', content)
        
        # Fix keyword argument repeated errors
        content = re.sub(r'_ = (\w+\.[\w\(\)\.\'\"_ ,\[\]]+)', r'\1', content)
        
        # Fix os.path.exists syntax errors
        content = re.sub(r'_ = (os\.path\.exists\([^)]+\))\s+and\s+', r'\1 and ', content)
        
        # Fix regex pattern syntax errors
        content = re.sub(r'_ = (r\'[^\']*\')', r'\1', content)
        
        # Fix assignment errors
        content = re.sub(r'_ = (\w+\([^)]*\))', r'\1', content)
        
        # If changes were made, write back to file
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed syntax errors in: {file_path}")
            changes_made = True
            
        return changes_made
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def fix_indentation_errors(file_path):
    """Fix indentation errors in Python files."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        original_lines = lines.copy()
        modified = False
        
        # Fix indentation errors
        for i, line in enumerate(lines):
            # Remove leading spaces that cause unexpected indent
            if line.startswith('    ') and not any(line.lstrip().startswith(keyword) for keyword in [
                'from', 'import', 'class', 'def', 'if', 'elif', 'else', 'try', 'except', 
                'finally', 'with', 'for', 'while', 'async', 'await', 'return', 'yield',
                'pass', 'break', 'continue', 'raise', 'assert', '@'
            ]):
                lines[i] = line.lstrip()
                if line.lstrip():
                    modified = True
        
        # Write back if modified
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"Fixed indentation errors in: {file_path}")
            return True
            
        return False
    except Exception as e:
        print(f"Error fixing indentation in {file_path}: {e}")
        return False

def get_all_python_files(root_dir):
    """Get all Python files in the project."""
    python_files = []
    for root, dirs, files in os.walk(root_dir):
        # Skip __pycache__ directories and venv
        dirs[:] = [d for d in dirs if d != '__pycache__' and d != 'venv']
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def main():
    """Main function to fix all syntax errors in the project."""
    print("Starting comprehensive syntax error fix...")
    
    # Get all Python files in the project
    python_files = get_all_python_files(".")
    
    print(f"Found {len(python_files)} Python files to check.")
    
    fixed_files = 0
    error_files = []
    
    for file_path in python_files:
        try:
            # Skip the virtual environment
            if 'venv' in file_path:
                continue
                
            # Fix syntax errors
            if fix_syntax_errors_in_file(file_path):
                fixed_files += 1
                
            # Fix indentation errors for specific files
            if any(name in file_path for name in [
                '__init__.py', 
                'test_ai_virtual_input_service.py',
                'test_resource_awareness_service.py',
                'test_security.py'
            ]):
                if fix_indentation_errors(file_path):
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
            print("Some syntax errors remain. Check output above.")
    except Exception as e:
        print(f"Error running syntax check: {str(e)}")

if __name__ == "__main__":
    main()