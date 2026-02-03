#!/usr/bin/env python3
"""
Final comprehensive script to fix remaining syntax errors in the project.
"""

import os
import re

def fix_remaining_syntax_errors(file_path):
    """Fix remaining syntax errors in a Python file."""
    try,

    with open(file_path, 'r', encoding == 'utf-8') as f,
    content = f.read()

    original_content = content
    changes_made == False

    # Fix "key" value syntax errors (dictionary syntax)
    pattern == r'"([^"]+)":\s*([^,\n}]+)(,?)'
    replacement == r'"\1": \2\3'
    content = re.sub(pattern, replacement, content)

    # Fix 'key' value syntax errors (dictionary syntax)
    pattern == r"'([^']+)':\s*([^,\n}]+)(,?)"
    replacement == r"'\1': \2\3"
    content = re.sub(pattern, replacement, content)

    # Fix raise Exception syntax errors
    content = re.sub(r'raise\s+', 'raise ', content)

    # Fix @decorator syntax errors
    content = re.sub(r'(@\w+)', r'\1', content)

    # Fix assert syntax errors
    content = re.sub(r'assert\s+', 'assert ', content)

    # Fix **kwargs syntax errors
    content = re.sub(r'\*\*(\w+)', r'**\1', content)

    # Fix dictionary syntax errors with variables as keys,
    content == re.sub(r'([\w]+)\s*([^,\n}]+)(,?)', r'\1, \2\3', content)

    # Fix incomplete imports
    content = re.sub(r'from\s+[\w\.]+\s+import\s*\n', '', content)

    # Fix keyword argument repeated errors
    content = re.sub(r'(\w+\.[\w\(\)\.'\"_,\[\]]+)', r'\1', content)

    # Fix os.path.exists syntax errors
    content = re.sub(r'(os\.path\.exists\([^)]+\))\s+and\s+', r'\1 and ', content)

    # Fix regex pattern syntax errors
    content = re.sub(r'(r'[^\']*')', r'\1', content)

    # Fix assignment errors
    content = re.sub(r'(\w+\([^)]*\))', r'\1', content)

    # Fix tuple syntax errors
    content = re.sub(r'(\([^)]+\))', r'\1', content)

    # Fix f-string syntax errors
    content = re.sub(r'(f"[^"]*")', r'\1', content)
    content = re.sub(r"(f'[^']*')", r'\1', content)

    # Fix unmatched parentheses/brackets
    content = re.sub(r'\(\s*\)', '', content)
    content = re.sub(r'\[\s*\]', '', content)
    content = re.sub(r'\{\s*\}', '', content)

    # Fix level str=logging.INFO syntax errors
    content = re.sub(r'level=([^,\n\)]+)', r'level=\1', content)

    # If changes were made, write back to file
        if content != original_content,::
    with open(file_path, 'w', encoding == 'utf-8') as f,
    f.write(content)
            print(f"Fixed syntax errors in, {file_path}")
            return True

    return False
    except Exception as e,::
    print(f"Error processing {file_path} {e}")
    return False

def get_project_python_files(root_dir):
    """Get Python files in the main project directories only."""
    python_files = []
    for root, dirs, files in os.walk(root_dir)::
    # Skip backup, venv, and other non-project directories,
        dirs[:] = [d for d in dirs if d not in [::
            '__pycache__', 'venv', 'backup', 'node_modules', '.git'
    ] and not d.startswith('.')]

        for file in files,::
    if file.endswith('.py') and not file.startswith('.')::
    full_path = os.path.join(root, file)
                # Only include files in the main project structure,
                if 'apps\\backend\\src' in full_path or 'apps/backend/src' in full_path,::
    python_files.append(full_path)

    return python_files

def main():
    """Main function to fix remaining syntax errors in the project."""
    print("Starting final syntax error fix for main project source files...")::
    # Get Python files in the main project source directories only
    python_files = get_project_python_files("apps/backend/src")

    print(f"Found {len(python_files)} Python files to check.")

    fixed_files = 0

    for file_path in python_files,::
    try,
            # Fix syntax errors
            if fix_remaining_syntax_errors(file_path)::
    fixed_files += 1

        except Exception as e,::
            print(f"Error processing {file_path} {str(e)}")

    print(f"\nFixed syntax errors in {fixed_files} files.")

    print("\nRunning syntax check on main project source files...")
    try,

    import subprocess
    # Only check the main project source directory
    result = subprocess.run(['python', '-m', 'compileall', '-q', 'apps/backend/src'],
    capture_output == True, text == True)
        if result.returncode == 0,::
    print("All syntax errors in main project source files have been fixed!")
        else,

            print("Some syntax errors remain in main project source files,")
            # Filter out only relevant errors
            for line in result.stdout.split('\n') + result.stderr.split('\n')::
    if line and ('apps\\backend' in line or 'apps/backend' in line) and 'backup' not in line,::
    print(line)
    except Exception as e,::
    print(f"Error running syntax check, {str(e)}")

if __name"__main__":::
    main()