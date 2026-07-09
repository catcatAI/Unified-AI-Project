#!/usr/bin/env python3
"""
Fix str(e) → safe_error(e) across all source files.
Handles import placement at the TOP of the file only.
"""
import ast
import os
import re
import subprocess
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "apps", "backend", "src")

def get_files_with_str_e():
    """Get all Python files in src/ that contain str(e)."""
    result = subprocess.run(
        ["grep", "-rln", "str(e)", "--include=*.py", SRC_DIR],
        capture_output=True, text=True, cwd=PROJECT_ROOT, timeout=30
    )
    files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
    # Exclude test files and core/utils.py itself
    files = [f for f in files if '/test_' not in f and not f.endswith('test.py') and 'core/utils.py' not in f]
    return files

def has_import_already(content):
    """Check if safe_error is already imported."""
    return "from core.utils import safe_error" in content or "from apps.backend.src.core.utils import safe_error" in content

def find_insert_line(lines):
    """
    Find the line number where to insert the import.
    Returns index after the last top-level import, or 0 if no imports.
    Only considers module-level imports (indent == 0).
    """
    last_import_idx = -1
    in_docstring = False
    in_block = 0  # Track nested blocks
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Track docstrings
        if stripped.startswith('"""') or stripped.startswith("'''"):
            if not in_docstring:
                in_docstring = True
                if stripped.count('"""') >= 2 or stripped.count("'''") >= 2:
                    in_docstring = False
            else:
                in_docstring = False
            continue
        
        if in_docstring:
            continue
        
        # Reset block tracking at module level
        if stripped == '' and in_block == 0:
            continue
            
        # Track block depth
        indent = len(line) - len(line.lstrip())
        if indent > 0:
            continue  # Skip indented blocks (functions, classes, etc.)
        
        # Check if this is an import at module level
        if (stripped.startswith('import ') or stripped.startswith('from ')) and in_block == 0:
            last_import_idx = i
        elif stripped.startswith('def ') or stripped.startswith('class ') or stripped.startswith('@'):
            # Stop looking past the first function/class definition
            if last_import_idx >= 0:
                break
            # No imports found yet, insert before first def
            if i > 0:
                return i
            return 1
    
    if last_import_idx >= 0:
        return last_import_idx + 1
    return 1

def fix_file(filepath):
    """Fix a single file: add import and replace str(e) with safe_error(e)."""
    relpath = os.path.relpath(filepath, PROJECT_ROOT)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if has_import_already(content):
        print(f"  SKIP {relpath}: already has import")
        return False
    
    lines = content.split('\n')
    
    # Find the right insertion point
    insert_idx = find_insert_line(lines)
    
    # Count original str(e) occurrences for logging
    orig_count = content.count('str(e)')
    if orig_count == 0:
        print(f"  SKIP {relpath}: no str(e) found")
        return False
    
    # Replace str(e) with safe_error(e)
    new_content = content.replace('str(e)', 'safe_error(e)')
    
    # Add import
    lines = new_content.split('\n')
    
    # Check if there are any existing imports from core.utils or core
    has_relative_import = any('from core' in l or 'from apps.backend.src.core' in l for l in lines if l.strip().startswith('from '))
    
    if has_relative_import:
        # Insert after the last core import block
        last_core_import = -1
        for i, l in enumerate(lines):
            stripped = l.strip()
            if stripped.startswith('from core') or stripped.startswith('from apps.backend.src.core'):
                last_core_import = i
        insert_idx = last_core_import + 1
        lines.insert(insert_idx, 'from core.utils import safe_error')
    else:
        # Insert at the determined position
        # Check if we need a blank line before
        if insert_idx > 0 and lines[insert_idx - 1].strip() != '':
            lines.insert(insert_idx, '')
            insert_idx += 1
        lines.insert(insert_idx, 'from core.utils import safe_error')
    
    new_content = '\n'.join(lines)
    
    # Verify the file compiles
    try:
        ast.parse(new_content)
    except SyntaxError as e:
        print(f"  ERROR {relpath}: syntax error after fix: {e}")
        return False
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"  FIXED {relpath}: {orig_count} replacements")
    return True

def main():
    print("Finding files with str(e)...")
    files = get_files_with_str_e()
    print(f"Found {len(files)} files to process.")
    
    fixed = 0
    skipped = 0
    errors = 0
    
    for filepath in sorted(files):
        try:
            if fix_file(filepath):
                fixed += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"  ERROR {filepath}: {e}")
            errors += 1
    
    print(f"\nDone: {fixed} fixed, {skipped} skipped, {errors} errors")

if __name__ == '__main__':
    main()
