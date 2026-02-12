#!/usr/bin/env python3
"""
ImportError 警告日志修复脚本 v3
逐行处理，为每个 ImportError 添加正确的警告日志
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
        lines = f.readlines()

    result_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        result_lines.append(line)

        # Check if this is a try block
        if line.strip().startswith('try:'):
            # Find the module name from the from statement
            module_name = None
            j = i + 1
            while j < len(lines):
                stripped = lines[j].strip()
                if stripped.startswith('from '):
                    match = re.search(r'from \.(\w+) import', lines[j])
                    if match:
                        module_name = match.group(1)
                elif stripped.startswith('except'):
                    # Found the except block
                    result_lines.append(lines[j])

                    # Check if it's "except ImportError:" or "except ImportError as e:"
                    if 'except ImportError:' in lines[j]:
                        # Change to "except ImportError as e:"
                        indent = len(lines[j]) - len(lines[j].lstrip())
                        result_lines[-1] = ' ' * indent + 'except ImportError as e:\n'
                        # Add warning log
                        result_lines.append(' ' * (indent + 4) + f'logger.warning(f"Failed to import {module_name}: {{e}}")\n')
                    elif 'except ImportError as e:' in lines[j]:
                        # Check if next lines already have logger.warning
                        k = j + 1
                        has_warning = False
                        while k < len(lines) and (lines[k].strip() != '' and not lines[k].strip().startswith('try') and not lines[k].strip().startswith('except')):
                            if 'logger.warning' in lines[k]:
                                has_warning = True
                                break
                            k += 1
                        if not has_warning:
                            indent = len(lines[j]) - len(lines[j].lstrip())
                            result_lines.append(' ' * (indent + 4) + f'logger.warning(f"Failed to import {module_name}: {{e}}")\n')
                    break
                j += 1

            # Skip the lines we already processed
            i = j
        else:
            i += 1

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(result_lines)

    print(f"✅ Successfully added warning logs to {file_path}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python fix_importerror_logs_v3.py <file_path>")
        print("\nExample:")
        print("  python fix_importerror_logs_v3.py apps/backend/src/core/autonomous/__init__.py")
        sys.exit(1)

    file_path = sys.argv[1]

    try:
        fix_importerror_warnings(file_path)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)