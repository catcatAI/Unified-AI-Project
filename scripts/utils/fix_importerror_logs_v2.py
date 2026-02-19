#!/usr/bin/env python3
"""
ImportError 警告日志修复脚本 v2
自动为 core/autonomous/__init__.py 中的所有 ImportError 添加正确的警告日志
"""

import re
import logging
logger = logging.getLogger(__name__)

def fix_importerror_warnings(file_path: str) -> None:
    """
    为所有 `except ImportError:` 添加正确的警告日志

    Args:
        file_path: 要修复的文件路径
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    result_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]
        result_lines.append(line)

        # Check if this is a try block with import
        if line.strip().startswith('try:'):
            # Look ahead to find the from statement
            j = i + 1
            module_name = None
            while j < len(lines) and not lines[j].strip().startswith('except'):
                match = re.search(r'from \.(\w+) import', lines[j])
                if match:
                    module_name = match.group(1)
                j += 1

            # Now process the except block
            if j < len(lines) and lines[j].strip().startswith('except'):
                except_line = lines[j]
                result_lines.append(except_line)

                # Check if it already has a warning
                has_warning = False
                k = j + 1
                indent = len(except_line) - len(except_line.lstrip()) + 4

                # Look ahead to see if logger.warning already exists
                while k < len(lines) and (lines[k].strip() != '' and not lines[k].strip().startswith('try') and not lines[k].strip().startswith('except')):
                    if 'logger.warning' in lines[k]:
                        has_warning = True
                    k += 1

                # If no warning and we have a module name, add it
                if not has_warning and module_name:
                    indent_str = ' ' * indent
                    warning_line = f'{indent_str}logger.warning(f"Failed to import {module_name}: {{e}}")'
                    result_lines.append(warning_line)

                i = j
            else:
                i = j
        else:
            i += 1

    # Write back
    new_content = '\n'.join(result_lines)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✅ Successfully added warning logs to {file_path}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python fix_importerror_logs_v2.py <file_path>")
        print("\nExample:")
        print("  python fix_importerror_logs_v2.py apps/backend/src/core/autonomous/__init__.py")
        sys.exit(1)

    file_path = sys.argv[1]

    try:
        fix_importerror_warnings(file_path)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)