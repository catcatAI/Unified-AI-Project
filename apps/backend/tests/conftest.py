"""
Standalone path bootstrap for apps/backend/tests/.

Historically this tree only ever ran AFTER tests/conftest.py (which inserts
apps/backend/src). Running `pytest apps/backend/tests/` standalone therefore
failed at collection (ModuleNotFoundError: No module named 'apps'). CI now
extends to this path, so the same path setup must live here too:

- SRC_PATH (apps/backend/src): sibling files import `from api.v1... / from services...`
- REPO_ROOT: test_drive_integration.py imports `from apps.backend.src...`
"""

import os
import sys

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_SRC_PATH = os.path.join(_PROJECT_ROOT, "apps", "backend", "src")
_ROOT = _PROJECT_ROOT  # repo root (contains the apps/ package)

for _p in (_SRC_PATH, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)
