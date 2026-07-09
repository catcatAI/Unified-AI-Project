"""Remove ALL safe_error imports from each file, then add ONE at the top."""
import os
import subprocess

IMPORT_LINE = "from core.utils import safe_error"
PROJECT_ROOT = "D:/Projects/Unified-AI-Project"

# Get all modified Python files
result = subprocess.run(
    ["git", "diff", "--name-only"],
    capture_output=True, text=True, cwd=PROJECT_ROOT
)
modified_files = sorted(set(
    f.strip() for f in result.stdout.strip().split("\n")
    if f.strip().endswith(".py") and f.strip().startswith("apps/backend/src/")
))

print(f"Found {len(modified_files)} modified Python files")

fixed_count = 0
syntax_errors = []

for filepath in modified_files:
    full_path = os.path.join(PROJECT_ROOT, filepath)
    if not os.path.exists(full_path):
        continue

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Check if the file has the import at all
    if IMPORT_LINE not in content:
        continue

    # Remove ALL occurrences of the import line (any indent level)
    new_content = ""
    removed = False
    for line in content.split("\n"):
        if line.strip() == IMPORT_LINE:
            removed = True
            print(f"  REMOVED import from {filepath}")
            continue
        new_content += line + "\n"

    if not removed:
        continue

    # Add ONE import at the top of the file (after copyright/docstring)
    lines = new_content.split("\n")
    insert_idx = 0
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("import ") or (s.startswith("from ") and " import " in s and "safe_error" not in s):
            insert_idx = i + 1
        elif s.startswith('"""') or s.startswith("'''") or s.startswith("#"):
            # Skip docstrings and comments
            pass
    
    lines.insert(insert_idx, IMPORT_LINE)
    new_content = "\n".join(lines)
    
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    fixed_count += 1
    print(f"  ADDED import at top of {filepath}")

print(f"\nFixed {fixed_count} files")

# Verify syntax
print("\nVerifying syntax...")
for filepath in modified_files:
    full_path = os.path.join(PROJECT_ROOT, filepath)
    if not os.path.exists(full_path):
        continue
    try:
        compile(open(full_path, "r", encoding="utf-8").read(), full_path, "exec")
    except SyntaxError as e:
        syntax_errors.append((filepath, str(e)))
        print(f"  SYNTAX ERROR: {filepath}: {e}")

if syntax_errors:
    print(f"\n{len(syntax_errors)} files with syntax errors:")
    for f, err in syntax_errors[:5]:
        print(f"  {f}: {err}")
    if len(syntax_errors) > 5:
        print(f"  ... and {len(syntax_errors) - 5} more")
else:
    print("All files: OK")
