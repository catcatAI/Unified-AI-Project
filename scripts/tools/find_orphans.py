#!/usr/bin/env python3
"""
Orphan File Detector for Angela AI project.

Finds Python files in a given directory that have zero importers (orphans).
Uses the ast module for true import relationship analysis — no regex, no grep.
"""

import ast
import argparse
import json
import sys
from pathlib import Path
from collections import defaultdict


def find_py_files(root_dir):
    """Walk directory recursively and return all .py files."""
    return sorted(root_dir.rglob("*.py"))


def get_module_path(file_path, root_dir):
    """Convert a file path to its dotted module name relative to root_dir.

    Examples:
        services/chat_service.py  ->  services.chat_service
        services/__init__.py      ->  services
        __init__.py               ->  (empty string for root package)
    """
    rel = file_path.relative_to(root_dir)
    parts = list(rel.parts)

    if parts[-1] == "__init__.py":
        parts.pop()
    else:
        parts[-1] = parts[-1][:-3]

    return ".".join(parts)


def build_module_map(py_files, root_dir):
    """Build {dotted_name: Path} mapping for all scanned files."""
    module_map = {}
    for f in py_files:
        mod = get_module_path(f, root_dir)
        module_map[mod] = f
    return module_map


def resolve_dotted_name(name, module_map):
    """Resolve a dotted module name to one or more known file paths.

    For 'a.b.c', tries suffixes 'a.b.c', 'a.b', 'a' in order and returns
    every Path that exists in module_map.
    """
    results = []
    parts = name.split(".")
    for i in range(len(parts), 0, -1):
        prefix = ".".join(parts[:i])
        if prefix in module_map:
            results.append(module_map[prefix])
    return results


def extract_imports(file_path, module_map, root_dir):
    """Parse a Python file with ast and return set of imported file Paths."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception:
        return set()

    try:
        tree = ast.parse(content, filename=str(file_path))
    except SyntaxError:
        return set()

    imports = set()
    file_module = get_module_path(file_path, root_dir)
    file_parts = file_module.split(".") if file_module else []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "__future__":
                    continue
                imports.update(resolve_dotted_name(alias.name, module_map))

        elif isinstance(node, ast.ImportFrom):
            if node.module == "__future__":
                continue

            if node.level == 0:
                # Absolute import: from X import Y
                if node.module:
                    imports.update(resolve_dotted_name(node.module, module_map))
                    for alias in node.names:
                        full = f"{node.module}.{alias.name}"
                        imports.update(resolve_dotted_name(full, module_map))
            else:
                # Relative import: from .X import Y, from ..X import Y, ...
                if node.level <= len(file_parts):
                    base_parts = file_parts[:-node.level] if file_parts else []
                    if node.module:
                        base = ".".join(base_parts + [node.module])
                        imports.update(resolve_dotted_name(base, module_map))
                        for alias in node.names:
                            full = f"{base}.{alias.name}"
                            imports.update(resolve_dotted_name(full, module_map))
                    else:
                        if base_parts:
                            base = ".".join(base_parts)
                            for alias in node.names:
                                full = f"{base}.{alias.name}"
                                imports.update(resolve_dotted_name(full, module_map))

    return imports


def file_contains_text(file_path, text):
    """Check whether a file's content contains the given text."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return text in content
    except Exception:
        return False


def is_test_file(file_path, root_dir):
    """Heuristic: a file is a test file if 'test' is in its relative path."""
    try:
        rel = file_path.relative_to(root_dir)
    except ValueError:
        return False
    return "test" in rel.parts or rel.name.startswith("test_") or rel.name.endswith("_test.py")


def main():
    parser = argparse.ArgumentParser(
        description="Find orphan Python files with zero importers"
    )
    parser.add_argument(
        "--dir",
        default="apps/backend/src",
        help="Directory to scan (default: apps/backend/src)",
    )
    parser.add_argument(
        "--exclude",
        type=str,
        default=None,
        metavar="TEXT",
        help="Exclude files whose content contains this text",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in machine-readable JSON format",
    )
    parser.add_argument(
        "--minimal",
        action="store_true",
        help="Only show orphans with no importers whatsoever (exclude test imports)",
    )

    args = parser.parse_args()

    root_dir = Path(args.dir).resolve()
    if not root_dir.is_dir():
        print(f"Error: '{root_dir}' is not a valid directory", file=sys.stderr)
        return 1

    # ------------------------------------------------------------------
    # 1. Discover files & optionally filter
    # ------------------------------------------------------------------
    all_py_files = find_py_files(root_dir)

    if args.exclude:
        excluded = {f for f in all_py_files if file_contains_text(f, args.exclude)}
        py_files = [f for f in all_py_files if f not in excluded]
    else:
        excluded = set()
        py_files = list(all_py_files)

    # ------------------------------------------------------------------
    # 2. Build module map & reverse dependency graph
    # ------------------------------------------------------------------
    module_map = build_module_map(py_files, root_dir)

    importers = defaultdict(set)  # imported_file -> {files that import it}

    for source_file in py_files:
        imported = extract_imports(source_file, module_map, root_dir)
        for imp in imported:
            importers[imp].add(source_file)

    # ------------------------------------------------------------------
    # 3. Determine orphans
    # ------------------------------------------------------------------
    imported_set = set(importers.keys())
    orphans = set(py_files) - imported_set

    if args.minimal:
        # Files that are only imported by test files count as orphans
        for f, srcs in importers.items():
            if all(is_test_file(s, root_dir) for s in srcs):
                orphans.add(f)

    orphans = sorted(orphans)
    total = len(py_files)
    orphan_count = len(orphans)
    excluded_count = len(excluded)

    # Group by subdirectory
    by_dir = defaultdict(list)
    for f in orphans:
        try:
            key = str(f.parent.relative_to(root_dir)) or "(root)"
        except ValueError:
            key = "(root)"
        by_dir[key].append(f)

    # ------------------------------------------------------------------
    # 4. Output
    # ------------------------------------------------------------------
    if args.json:
        output = {
            "root_dir": str(root_dir),
            "total_files": total,
            "excluded_files": excluded_count,
            "orphan_count": orphan_count,
            "orphan_percentage": round(orphan_count / total * 100, 1) if total else 0,
            "orphans": sorted(str(f) for f in orphans),
            "orphans_by_directory": {
                d: sorted(str(f) for f in files)
                for d, files in sorted(by_dir.items())
            },
        }
        print(json.dumps(output, indent=2))
    else:
        pct = orphan_count / total * 100 if total else 0
        print("=" * 70)
        print("  Orphan File Detector")
        print("=" * 70)
        print(f"  Scanned:  {root_dir}")
        print(f"  Files:    {total}")
        if excluded_count:
            print(f"  Excluded: {excluded_count} (containing '{args.exclude}')")
        print(f"  Orphans:  {orphan_count} / {total} ({pct:.1f}%)")
        print("=" * 70)

        if orphans:
            for dir_name in sorted(by_dir):
                files = by_dir[dir_name]
                print(f"\n  [{dir_name}/] ({len(files)} file(s))")
                for f in files:
                    print(f"    - {f.relative_to(root_dir)}")
        else:
            print("\n  No orphan files found!")

        print()
        print("=" * 70)
        print(f"  Summary: {orphan_count} orphans out of {total} files ({pct:.1f}%)")
        print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
