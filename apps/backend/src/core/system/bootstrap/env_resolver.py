"""
Environment Resolver & OS Detection
Formalized from auto_install.py
"""

import os
import sys
import platform
import subprocess
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class EnvResolver:
    """
    Validates the host environment and detects OS-specific requirements.
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent.parent.parent
        self.os_type = platform.system().lower()
        self.distro = self._detect_distro()

    def _detect_distro(self) -> str:
        if self.os_type == "linux":
            try:
                with open("/etc/os-release", "r") as f:
                    content = f.read().lower()
                    for d in ["ubuntu", "debian", "arch", "centos", "rhel"]:
                        if d in content: return d
            except Exception: pass
        return "unknown"

    def check_python_compliance(self, min_version: Tuple[int, int] = (3, 9)) -> bool:
        """Verifies if the current Python meets requirements."""
        current = sys.version_info
        if current.major < min_version[0] or (current.major == min_version[0] and current.minor < min_version[1]):
            logger.error(f"Python version mismatch: {sys.version}. Required: {min_version[0]}.{min_version[1]}+")
            return False
        return True

    def check_node_presence(self) -> Optional[str]:
        """Checks for node.js and returns version if found."""
        try:
            res = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if res.returncode == 0:
                return res.stdout.strip()
        except FileNotFoundError: pass
        return None

    def resolve_pnpm_workspace(self) -> bool:
        """Ensures pnpm-workspace.yaml exists at root."""
        workspace_file = self.project_root / "pnpm-workspace.yaml"
        return workspace_file.exists()

    def get_env_summary(self) -> Dict[str, Any]:
        """Returns a comprehensive environment state."""
        return {
            "os": self.os_type,
            "distro": self.distro,
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "node": self.check_node_presence(),
            "pnpm_workspace": self.resolve_pnpm_workspace()
        }
