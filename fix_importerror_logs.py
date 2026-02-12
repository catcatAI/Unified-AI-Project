#!/usr/bin/env python3
"""
ImportError 警告日志修复脚本
自动为 core/autonomous/__init__.py 中的所有 ImportError 添加警告日志
"""

import re

def fix_importerror_warnings(file_path: str) -> None:
    """
    为所有 `except ImportError:` 添加警告日志

    Args:
        file_path: 要修复的文件路径
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern 1: except ImportError:
    pattern1 = re.compile(
        r'except ImportError:\n((?:    \w+ = None\n)+)',
        re.MULTILINE
    )

    def replacement1(match):
        indent = '    '
        none_lines = match.group(1)
        # 提取模块名称（从上一行的 from .xxx import）
        # 查找前面的 from 语句
        pre_match = re.search(
            r'from \.(\w+) import',
            content[:match.start()]
        )
        module_name = pre_match.group(1) if pre_match else "unknown_module"
        return f'except ImportError as e:\n{indent}logger.warning(f"Failed to import {module_name}: {{e}}")\n{none_lines}'

    content = pattern1.sub(replacement1, content)

    # Pattern 2: except ImportError as e: (already has e, just add log)
    pattern2 = re.compile(
        r'except ImportError as e:\n((?!logger.warning).*?)(?=\n(?:try|except|#|$))',
        re.DOTALL
    )

    def replacement2(match):
        code_after = match.group(1)
        if 'logger.warning' in code_after:
            return match.group(0)  # Already has warning
        # Extract module name
        pre_match = re.search(
            r'from \.(\w+) import',
            content[:match.start()]
        )
        module_name = pre_match.group(1) if pre_match else "unknown_module"
        indent = '    '
        return f'except ImportError as e:\n{indent}logger.warning(f"Failed to import {module_name}: {{e}}")\n{code_after}'

    content = pattern2.sub(replacement2, content)

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ Successfully added warning logs to {file_path}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python fix_importerror_logs.py <file_path>")
        print("\nExample:")
        print("  python fix_importerror_logs.py apps/backend/src/core/autonomous/__init__.py")
        sys.exit(1)

    file_path = sys.argv[1]

    try:
        fix_importerror_warnings(file_path)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)