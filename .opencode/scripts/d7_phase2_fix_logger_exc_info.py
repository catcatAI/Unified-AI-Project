"""
D7 Phase 2: Batch add exc_info=True to single-line logger.error/warning/critical calls.

Pattern: logger.error("...") or logger.warning("...") or logger.critical("...") or logging.error("...")
Only targets single-line calls where the full call fits on one line.
Skips calls that already contain exc_info.
Skips test files (*/tests/*, test_*.py).
"""

import re
import os
import sys
from pathlib import Path

SRC_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    r"D:\Projects\Unified-AI-Project\apps\backend\src"
)

RE_LINE = re.compile(
    r'^(\s*)(?:self\.)?(logger|logging)\.(error|warning|critical)\s*\((.*)\)\s*$'
)


def fix_line(line: str) -> str | None:
    m = RE_LINE.match(line)
    if not m:
        return None
    indent, logger_name, level, content = m.groups()
    if "exc_info" in content:
        return None  # already has exc_info
    # Only fix if it looks like an exception context (has exception-like args) or always
    # We fix ALL calls unconditionally (defensive approach)
    return f"{indent}{logger_name}.{level}({content}, exc_info=True)\n"


def process_file(path: Path) -> tuple[int, int]:
    """Returns (fixed, skipped) counts."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"  SKIP (read error): {e}")
        return 0, 0

    fixed = 0
    new_lines = []
    for line in lines:
        fixed_line = fix_line(line)
        if fixed_line is not None:
            new_lines.append(fixed_line)
            fixed += 1
        else:
            new_lines.append(line)

    if fixed > 0:
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

    return fixed, 0


def main():
    all_files = list(SRC_DIR.rglob("*.py"))
    total_fixed = 0
    total_files = 0
    skipped_tests = 0

    for path in sorted(all_files):
        rel = path.relative_to(SRC_DIR)
        # Skip test files
        if "tests" in path.parts or path.name.startswith("test_"):
            skipped_tests += 1
            continue
        fixed, _ = process_file(path)
        if fixed > 0:
            print(f"  {rel}: {fixed} fix(es)")
            total_fixed += fixed
            total_files += 1

    print(f"\nDone: {total_files} files, {total_fixed} fixes, {skipped_tests} test files skipped")


if __name__ == "__main__":
    main()
