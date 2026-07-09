#!/usr/bin/env python3
"""
Fix str(e) → safe_error(e) across all source files.
Uses AST parsing for robust import placement.
"""
import ast
import os
import re
import subprocess
import sys

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "apps", "backend", "src")


def get_files():
    """Get all Python files in src/ that contain str(e), excluding tests and core/utils.py."""
    result = subprocess.run(
        ["grep", "-rln", "str(e)", "--include=*.py", SRC],
        capture_output=True, text=True, timeout=30
    )
    files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
    # Exclude test files and core/utils.py
    files = [f for f in files
             if '/test_' not in f
             and not f.endswith('test.py')
             and 'core/utils.py' not in f
             and '__pycache__' not in f]
    return files


def find_last_import_line(lines):
    """
    Find the line number of the last top-level import.
    Returns -1 if no imports found.
    Only considers module-level (indent 0) imports.
    """
    last_import = -1
    # Track whether we're in a multi-line string/docstring
    in_multiline = False
    delim = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Track multi-line strings
        if not in_multiline:
            if stripped.startswith('"""') or stripped.startswith("'''"):
                in_multiline = True
                delim = stripped[:3]
                # Check if it ends on same line
                remainder = stripped[3:]
                if delim in remainder:
                    in_multiline = False
            continue
        else:
            if delim in stripped:
                in_multiline = False
            continue

        # Skip blank lines
        if not stripped:
            continue

        # Check indent level
        indent = len(line) - len(line.lstrip())
        if indent > 0:
            # We're inside a block - no more top-level imports after this
            # But skip if this is inside a function/class that started at module level
            continue

        # Now at indent 0 - check if it's an import
        if stripped.startswith('import ') or stripped.startswith('from '):
            last_import = i
        elif stripped.startswith('def ') or stripped.startswith('class ') or stripped.startswith('@'):
            # First function/class after imports signals end of import block
            if last_import >= 0:
                break
            # No imports found yet, insert before first def
            return i

    return last_import


def fix_file(filepath):
    """Fix a single file: add import and replace str(e) with safe_error(e)."""
    relpath = os.path.relpath(filepath, os.path.dirname(SRC))

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Skip if already has the import
    if "from core.utils import safe_error" in content:
        print(f"  SKIP {relpath}: already has import")
        return False

    # Count occurrences
    orig_count = content.count('str(e)')
    if orig_count == 0:
        print(f"  SKIP {relpath}: no str(e)")
        return False

    lines = content.split('\n')

    # Find the last top-level import line
    insert_at = find_last_import_line(lines)

    # Replace str(e) with safe_error(e) in content
    new_content = content.replace('str(e)', 'safe_error(e)')
    new_lines = new_content.split('\n')

    if insert_at < 0:
        # No imports found - insert after docstring or at top
        # Find first non-blank, non-comment, non-docstring line
        for i, line in enumerate(new_lines):
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'''"):
                insert_at = i
                break
        if insert_at < 0:
            insert_at = 0
        # Insert before the first content line
        new_lines.insert(insert_at, 'from core.utils import safe_error')
        # Add blank line after import if needed
        if insert_at + 1 < len(new_lines) and new_lines[insert_at + 1].strip():
            new_lines.insert(insert_at + 1, '')
    else:
        # Insert after the last import
        insert_idx = insert_at + 1
        # Check if we need a blank line
        if insert_idx < len(new_lines) and new_lines[insert_idx].strip():
            new_lines.insert(insert_idx, '')
            insert_idx += 1
        new_lines.insert(insert_idx, 'from core.utils import safe_error')
        # Add blank line after if needed (but before next non-blank)
        if insert_idx + 1 < len(new_lines) and new_lines[insert_idx + 1].strip():
            new_lines.insert(insert_idx + 1, '')

    new_content = '\n'.join(new_lines)

    # Verify with AST
    try:
        ast.parse(new_content)
    except SyntaxError as e:
        print(f"  ERROR {relpath}: syntax error after fix: {e}")
        return False

    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"  FIXED {relpath}: {orig_count} replacements")
    return True


def main():
    print("Scanning for str(e) occurrences...")
    files = get_files()
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
