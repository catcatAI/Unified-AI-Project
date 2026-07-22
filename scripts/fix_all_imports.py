"""Fix all misplaced safe_error imports across all modified files."""
import os
import subprocess
import sys

IMPORT_LINE="from core.utils import safe_error"
PROJECT_ROOT="D:/Projects/Unified-AI-Project"

# Get all modified Python files
result = subprocess.run(
    ["git", "diff", "--name-only"],
    capture_output=True, text=True, cwd=PROJECT_ROOT
)
modified_files=[f.strip() for f in result.stdout.strip().split("\n") if f.strip().endswith(".py")]

print(f"Found {len(modified_files)} modified Python files")

fixed_count=0
error_count=0

for filepath in modified_files:
    full_path = os.path.join(PROJECT_ROOT, filepath)
    if not os.path.exists(full_path):
        continue

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    original = content
    lines = content.split("\n")
    
    # Check if there's already a top-level import (no leading whitespace)
    has_top_import=False
    for line in lines:
        if line.strip() == IMPORT_LINE and line.lstrip() == line:
            has_top_import=True
            break
    
    # Remove ALL indented (inside function/class) imports
    filtered_lines=[]
    removed_inside=False
    for line in lines:
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if stripped == IMPORT_LINE and indent > 0:
            removed_inside=True
            print(f"  REMOVED misplaced import in {filepath} (indent={indent})")
            continue
        filtered_lines.append(line)
    
    # If we removed inside imports but have no top-level import, add one
    if removed_inside and not has_top_import:
        # Find insertion point (after last import, before first non-import)
        insert_idx=0
        for i, line in enumerate(filtered_lines):
            s = line.strip()
            if s.startswith("import ") or (s.startswith("from ") and " import " in s):
                insert_idx = i + 1
        
        filtered_lines.insert(insert_idx, IMPORT_LINE)
        fixed_count += 1
        print(f"  ADDED top-level import in {filepath} at line {insert_idx + 1}")
    
    if content != "\n".join(filtered_lines):
        with open(full_path, "w", encoding="utf-8") as f:
            f.write("\n".join(filtered_lines))
        fixed_count += 1
        print(f"  FIXED: {filepath}")
    else:
        print(f"  OK: {filepath}")

print(f"\nFixed {fixed_count} files")

# Now verify syntax of all modified files
print("\nVerifying syntax...")
syntax_errors=[]
for filepath in modified_files:
    full_path = os.path.join(PROJECT_ROOT, filepath)
    if not os.path.exists(full_path):
        continue
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            compile(f.read(), full_path, "exec")
    except SyntaxError as e:
        syntax_errors.append((filepath, str(e)))
        print(f"  SYNTAX ERROR: {filepath}: {e}")

if syntax_errors:
    print(f"\n{len(syntax_errors)} files with syntax errors:")
    for filepath, err in syntax_errors:
        print(f"  {filepath}: {err}")
else:
    print("All files: OK")
