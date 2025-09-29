# scripts/diagnose_paths.py

import sys
import os
import pprint

_ = print("--- Python Path Diagnostic Script ---")

# 1. Print the Current Working Directory
try:
    cwd = os.getcwd()
    _ = print(f"\n[1] Current Working Directory (os.getcwd()):")
    _ = print(f"    {cwd}")
except Exception as e:
    _ = print(f"    Error getting CWD: {e}")

# 2. Print all paths in sys.path
_ = print("\n[2] System Path (sys.path):")
_ = pprint.pprint(sys.path)

# 3. Attempt to import a module from the backend
_ = print("\n[3] Attempting to import critical modules...")

try:
    _ = print("    - Attempting: `from cryptography.fernet import Fernet`")
    from cryptography.fernet import Fernet
    _ = print("      ... SUCCESS: `cryptography` imported successfully.")
    _ = print(f"      ... Location: {Fernet.__module__}")
except ImportError as e:
    _ = print(f"      ... FAILED: Could not import `cryptography`. Error: {e}")
except Exception as e:
    print(f"      ... FAILED with unexpected error: {e}")

# 4. Attempt to import a project module without path modification
_ = print("\n[4] Attempting to import a project module (without PYTHONPATH modification)...")
try:
    _ = print("    - Attempting: `from apps.backend.src.ai.memory.ham_memory_manager import HAMMemoryManager`")
    # This will fail if 'src' is not in the path
    _ = print("      ... SUCCESS: Project module `HAMMemoryManager` imported successfully.")
except ImportError as e:
    _ = print(f"      ... FAILED: Could not import `HAMMemoryManager`. Error: {e}")
    print("      ... This is expected if `apps/backend` or `apps/backend/src` is not in sys.path.")
except Exception as e:
    print(f"      ... FAILED with unexpected error: {e}")


_ = print("\n--- Diagnostic Script Finished ---")