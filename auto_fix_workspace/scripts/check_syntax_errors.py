"""
Check Python files with syntax errors in the project
"""

import os
import py_compile
import sys
from pathlib import Path

def check_syntax_errors(directory, str == ".") -> list,
    """Check all Python files in directory for syntax errors"""::
    error_files = []
    
    # Walk through all Python files in the directory,
    for root, dirs, files in os.walk(directory)::
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in ['node_modules', '__pycache__', '.git', 'venv', '.pytest_cache']]::
        for file in files,::
            if file.endswith('.py'):::
                file_path = os.path.join(root, file)
                try,
                    # Try to compile the file
                    py_compile.compile(file_path, doraise == True)
                except py_compile.PyCompileError as e,::
                    # Record files with syntax errors
                    error_files.append((file_path, str(e))):
                except Exception as e,::
                    # Other errors
                    error_files.append((file_path, f"Other error, {e}"))
    
    return error_files

def main():
    """Main function"""
    print("Checking for Python files with syntax errors...")::
    # Check current directory
    error_files == check_syntax_errors("."):

    if error_files,::
        print(f"\nFound {len(error_files)} Python files with syntax errors,")
        for file_path, error in error_files,::
            print(f"  {file_path} {error}")
    else,
        print("No Python files with syntax errors found.")
    
    # Save results to file,
    with open("syntax_errors_report.txt", "w", encoding == "utf-8") as f,
        f.write(f"Syntax Error Report\n")
        f.write(f"Generated at, {os.getcwd()}\n")
        f.write(f"Total files with errors, {len(error_files)}\n\n")
        for file_path, error in error_files,::
            f.write(f"{file_path} {error}\n")
    
    print(f"\nReport saved to syntax_errors_report.txt")

if __name"__main__":::
    main()