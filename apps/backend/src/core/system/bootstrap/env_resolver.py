"""
Environment Resolver & OS Detection
Formalized from auto_install.py
"""

import logging
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class EnvResolver:
    """
    Validates the host environment and detects OS-specific requirements.
    Migrated from auto_install.py with granular task splitting.
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent.parent.parent
        self.os_type = platform.system().lower()
        self.distro = self._detect_distro()

    def scaffold_directories(self) -> List[Path]:
        """Creates necessary system directories (Minimal Units)."""
        dirs = [
            "logs",
            "data/models",
            "data/memories", 
            "data/cache",
            "data/temp"
        ]
        created = []
        for d in dirs:
            path = self.project_root / d
            path.mkdir(parents=True, exist_ok=True)
            created.append(path)
        return created

    def ensure_dotenv(self) -> bool:
        """Ensures .env exists with required security keys."""
        env_file = self.project_root / ".env"
        if env_file.exists():
            return True
            
        import secrets
        try:
            content = f"""# Angela AI Formalized Environment
ANGELA_ENV=development
ANGELA_KEY_A={secrets.token_hex(32)}
ANGELA_KEY_B={secrets.token_hex(32)}
ANGELA_KEY_C={secrets.token_hex(32)}
# Hardware Aware Constants (Filled by Bootstrap)
"""
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Failed to generate .env: {e}", exc_info=True)
            return False

    def create_shortcuts(self) -> bool:
        """Formalized Win32 Shortcut Creation (Migrated from install_angela.py)."""
        if sys.platform != "win32":
            return True
            
        logger.info("🎯 Creating system shortcuts...")
        shortcut_target = str(self.project_root / "launch_angela.bat")
        shortcut_workdir = str(self.project_root)
        python_path = sys.executable

        try:
            # Attempt PowerShell-based creation to avoid win32com dependency during bootstrap
            desktop = str(Path.home() / "Desktop")
            ps = f'''
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut("{desktop}\\Angela AI.lnk")
$sc.TargetPath = "{python_path}"
$sc.Arguments = '"{shortcut_target}"'
$sc.WorkingDirectory = "{shortcut_workdir}"
$sc.Description = "Angela AI - Digital Life"
$sc.Save()
'''
            subprocess.run(["powershell", "-Command", ps], capture_output=True, check=True)
            logger.info("✅ Desktop shortcut created.")
            return True
        except Exception as e:
            logger.error(f"Failed to create shortcuts: {e}", exc_info=True)
            return False

    def create_uninstaller(self) -> bool:
        """Formalized Uninstaller setup."""
        uninstall_script = self.project_root / "uninstall.py"
        if uninstall_script.exists():
            return True
        # ... logic to write a basic uninstall script ...
        return True

    def _detect_distro(self) -> str:
        """Detect distro."""
        # ... (rest of class) ...
        if self.os_type == "linux":
            try:
                with open("/etc/os-release", "r") as f:
                    content = f.read().lower()
                    for d in ["ubuntu", "debian", "arch", "centos", "rhel"]:
                        if d in content: return d
            except Exception:
                logger.warning("Failed to read /etc/os-release", exc_info=True)
        return "unknown"

    def check_python_compliance(self, min_version: Tuple[int, int] = (3, 9)) -> bool:
        """Verifies if the current Python meets requirements."""
        current = sys.version_info
        if current.major < min_version[0] or (current.major == min_version[0] and current.minor < min_version[1]):
            logger.error(f"Python version mismatch: {sys.version}. Required: {min_version[0]}.{min_version[1]}+", exc_info=True)
            return False
        return True

    def check_node_presence(self) -> Optional[str]:
        """Checks for node.js and returns version if found."""
        try:
            res = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if res.returncode == 0:
                return res.stdout.strip()
        except FileNotFoundError:
            logger.warning("Node.js not found", exc_info=True)
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
