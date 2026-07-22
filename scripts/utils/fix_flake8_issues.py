#!/usr/bin/env python3
"""
Auto-fix mechanical flake8 issues in scripts/ directory.

Safe fixes only:
  - E401: multiple imports on one line -> split into separate lines
  - Bug fixes: sys.executable(), self.project_root()
"""
import os
import re
from pathlib import Path

SCRIPTS_ROOT = Path(__file__).parent.parent

_FIXED_COUNT = 0
_SKIPPED_COUNT = 0


def fix_e401(content: str, filepath: str) -> str:
    """Split `import a, b, c` onto separate lines."""
    lines = content.split("\n")
    new_lines = []
    changed = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r"^import\s+\w+(?:\s*,\s*\w+)+", stripped):
            indent = line[: len(line) - len(line.lstrip())]
            modules = re.split(r"\s*,\s*", stripped[len("import "):])
            if len(modules) > 1:
                new_lines.append(f"{indent}import {modules[0]}")
                for mod in modules[1:]:
                    new_lines.append(f"{indent}import {mod}")
                changed = True
                print(f"  E401 FIX: {filepath}:{i+1}: split import of {len(modules)} modules")
                continue
        new_lines.append(line)
    if changed:
        return "\n".join(new_lines)
    return content


def fix_sys_executable(content: str, filepath: str) -> str:
    """Fix `sys.executable()` -> `sys.executable` (not a function)."""
    if "sys.executable()" not in content:
        return content
    lines = content.split("\n")
    new_lines = []
    changed = False
    for i, line in enumerate(lines):
        if "sys.executable()" in line:
            line = line.replace("sys.executable()", "sys.executable")
            changed = True
            print(f"  BUG FIX: {filepath}:{i+1}: sys.executable() -> sys.executable")
        new_lines.append(line)
    if changed:
        return "\n".join(new_lines)
    return content


def fix_project_root_call(content: str, filepath: str) -> str:
    """Fix `self.project_root()` -> `self.project_root` where it's a Path, not a method."""
    if "self.project_root()" not in content:
        return content
    lines = content.split("\n")
    new_lines = []
    changed = False
    for i, line in enumerate(lines):
        if "self.project_root()" in line:
            line = line.replace("self.project_root()", "self.project_root")
            changed = True
            print(f"  BUG FIX: {filepath}:{i+1}: self.project_root() -> self.project_root")
        new_lines.append(line)
    if changed:
        return "\n".join(new_lines)
    return content


def process_file(filepath: str) -> bool:
    """Apply all fixes to a file. Returns True if any changes made."""
    global _FIXED_COUNT, _SKIPPED_COUNT

    rel_path = os.path.relpath(filepath).replace(os.sep, "/")

    with open(filepath, encoding="utf-8") as f:
        original = f.read()

    content = original
    content = fix_e401(content, rel_path)
    content = fix_sys_executable(content, rel_path)
    content = fix_project_root_call(content, rel_path)

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        _FIXED_COUNT += 1
        print(f"  WROTE {rel_path}")
        return True

    _SKIPPED_COUNT += 1
    return False


def main():
    print("=" * 60)
    print("FLAKE8 AUTO-FIXER for scripts/")
    print("=" * 60)

    py_files = sorted(SCRIPTS_ROOT.rglob("*.py"))
    py_files = [f for f in py_files if f.name != "fix_flake8_issues.py"]

    print(f"\nFound {len(py_files)} Python files to process\n")

    for filepath in py_files:
        process_file(str(filepath))

    print(f"\n{'=' * 60}")
    print(f"RESULTS: {_FIXED_COUNT} files fixed, {_SKIPPED_COUNT} files skipped")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
