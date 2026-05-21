"""
Bootstrap Manager - Unified Infrastructure Orchestrator
Integrates hardware probing and environment resolution.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
from .hardware_probe import HardwareProbe, HardwareSpecs
from .env_resolver import EnvResolver

logger = logging.getLogger(__name__)

class BootstrapManager:
    """
    The 'Brain' of Phase 1 Infrastructure Consolidation.
    Unifies disparate installation logic into a single source of truth.
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        self.resolver = EnvResolver(project_root)
        self.prober = HardwareProbe()
        self.state: Dict[str, Any] = {}
        self._initialized = False

    def run_full_bootstrap(self) -> Dict[str, Any]:
        """Executes the full chain of hardware and environment checks with persistence."""
        logger.info("🚀 [Bootstrap] Starting formalized system bootstrap...")
        
        # 1. Scaffolding & Env (Minimal Units)
        self.resolver.scaffold_directories()
        self.resolver.ensure_dotenv()
        self.resolver.create_shortcuts()
        self.resolver.create_uninstaller()
        
        # 2. Resolve Environment
        env_summary = self.resolver.get_env_summary()
        self.resolver.check_python_compliance()
            
        # 3. Probe Hardware
        specs = self.prober.probe()
        perf_constants = self.prober.get_performance_constants()
        
        # 4. Consolidate & Persist
        self.state = {
            "environment": env_summary,
            "hardware": specs.__dict__,
            "performance": perf_constants,
            "boot_time": datetime.now().isoformat(),
            "status": "ready" if env_summary["pnpm_workspace"] else "degraded"
        }
        
        self._persist_state()
        self._initialized = True
        logger.info(f"✅ [Bootstrap] Persistence complete. State saved to system_status.json")
        return self.state

    def _persist_state(self):
        """Saves bootstrap state to a JSON file for cross-platform access."""
        import json
        status_path = self.resolver.project_root / "system_status.json"
        try:
            with open(status_path, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist bootstrap state: {e}")

    def get_state(self) -> Dict[str, Any]:
        """Returns the current bootstrap state, running if necessary."""
        if not self._initialized:
            # Check if a recent persistence exists
            import json
            status_path = self.resolver.project_root / "system_status.json"
            if status_path.exists():
                try:
                    with open(status_path, 'r', encoding='utf-8') as f:
                        self.state = json.load(f)
                    self._initialized = True
                    return self.state
                except: pass
            return self.run_full_bootstrap()
        return self.state

# Singleton Access
_manager = None
def get_bootstrap_manager() -> BootstrapManager:
    global _manager
    if _manager is None:
        _manager = BootstrapManager()
    return _manager
