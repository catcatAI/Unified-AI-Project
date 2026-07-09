"""Fix misplaced safe_error imports."""
import os
import re

IMPORT_LINE = "from core.utils import safe_error"

# Files where import was placed inside functions (deep line numbers)
BAD_PATHS = [
    "apps/backend/src/ai/agents/agent_adapter.py",
    "apps/backend/src/ai/agents/agent_manager.py",
    "apps/backend/src/ai/lifecycle/llm_decision_loop.py",
    "apps/backend/src/ai/lifecycle/proactive_interaction_system.py",
    "apps/backend/src/core/action_execution_bridge.py",
    "apps/backend/src/core/art/real_playwright_browser.py",
    "apps/backend/src/core/bio/trauma_memory.py",
    "apps/backend/src/core/engine/desktop_interaction.py",
    "apps/backend/src/core/engine/live2d_avatar_generator.py",
    "apps/backend/src/core/hardware/webgl_bridge.py",
    "apps/backend/src/core/managers/execution_monitor.py",
    "apps/backend/src/core/security/secure_eval.py",
    "apps/backend/src/core/security/security_audit.py",
    "apps/backend/src/services/llm/router.py",
    "apps/backend/src/core/engine/state_persistence.py",
    "apps/backend/src/core/life/digital_life_integrator.py",
]

project_root = "D:/Projects/Unified-AI-Project"

fixed_count = 0
already_ok_count = 0
not_found_count = 0

for rel_path in BAD_PATHS:
    full_path = os.path.join(project_root, rel_path)
    if not os.path.exists(full_path):
        print(f"NOT FOUND: {rel_path}")
        not_found_count += 1
        continue

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")

    # Check if there's already a top-level import (no leading whitespace)
    has_top_import = False
    for line in lines:
        if line.strip() == IMPORT_LINE and (len(line) == len(line.lstrip())):
            has_top_import = True
            break

    # Remove any indented (inside function) imports
    filtered_lines = []
    removed = False
    for line in lines:
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        # If the line contains the import but is indented, remove it
        if stripped == IMPORT_LINE and indent > 0:
            removed = True
            continue
        filtered_lines.append(line)

    if not has_top_import and removed:
        # Add import at top, after __future__ or docstring
        insert_idx = 0
        for i, line in enumerate(filtered_lines):
            s = line.strip()
            if s.startswith("import ") or s.startswith("from ") and "import" in s:
                insert_idx = i + 1
            elif s == "" and i > insert_idx:
                break
        # Make sure there's a blank line before the import if needed
        filtered_lines.insert(insert_idx, IMPORT_LINE)
        fixed_count += 1
        print(f"FIXED: {rel_path} (inserted at line {insert_idx + 1})")
    elif not removed and not has_top_import:
        # Need to add top-level import
        insert_idx = 0
        for i, line in enumerate(filtered_lines):
            s = line.strip()
            if s.startswith("import ") or s.startswith("from ") and "import" in s:
                insert_idx = i + 1
        filtered_lines.insert(insert_idx, IMPORT_LINE)
        fixed_count += 1
        print(f"FIXED: {rel_path} (no existing import, inserted at line {insert_idx + 1})")
    elif removed and has_top_import:
        fixed_count += 1  # The import was already there, just removed the duplicate
        print(f"FIXED: {rel_path} (removed duplicate inside function)")
    else:
        already_ok_count += 1
        print(f"OK: {rel_path} (already correct)")

    with open(full_path, "w", encoding="utf-8") as f:
        f.write("\n".join(filtered_lines))

print(f"\nSummary: {fixed_count} fixed, {already_ok_count} already OK, {not_found_count} not found")
