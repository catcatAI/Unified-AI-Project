#!/usr/bin/env python3
"""
Auto-Fix Workspace Launcher
Provides access to all auto-fix systems from their new workspace location.
"""

import sys
import os
from pathlib import Path

# Add the workspace scripts directory to Python path
workspace_root = Path(__file__).parent
scripts_path = workspace_root / "scripts"
sandbox_path = workspace_root / "sandbox"

# Add paths to sys.path
sys.path.insert(0, str(workspace_root))
sys.path.insert(0, str(scripts_path))
sys.path.insert(0, str(sandbox_path))

def get_workspace_path():
    """Return the path to the auto-fix workspace."""
    return str(workspace_root)

def get_scripts_path():
    """Return the path to the auto-fix scripts."""
    return str(scripts_path)

def get_sandbox_path():
    """Return the path to the sandbox systems."""
    return str(sandbox_path)

# Export paths for easy access:
UTO_FIX_WORKSPACE_ROOT = str(workspace_root)
AUTO_FIX_SCRIPTS_PATH = str(scripts_path)
AUTO_FIX_SANDBOX_PATH = str(sandbox_path)

if __name__ == "__main__":
    print(f"Auto-Fix Workspace Root: {AUTO_FIX_WORKSPACE_ROOT}")
    print(f"Auto-Fix Scripts Path: {AUTO_FIX_SCRIPTS_PATH}")
    print(f"Auto-Fix Sandbox Path: {AUTO_FIX_SANDBOX_PATH}")