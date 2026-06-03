"""
Bootstrap Manager - Unified Infrastructure Orchestrator
Integrates hardware probing and environment resolution.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from .hardware_probe import HardwareProbe
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
        logger.info("✅ [Bootstrap] Persistence complete. State saved to system_status.json")
        return self.state

    def broadcast_evolution(self, config_type: str, details: Dict[str, Any]) -> None:
        """
        [Phase 6] 廣播演化事件。
        更新系統狀態並通知客戶端。
        """
        logger.info(f"📢 [Bootstrap] System evolved: {config_type}")
        
        # 1. 更新內存狀態
        self.state["last_evolution"] = {
            "type": config_type,
            "time": datetime.now().isoformat(),
            "details": details
        }
        
        # 2. 持久化
        self._persist_state()
        
        # 3. 透過 StateStore 廣播
        from core.system.state_store import state_store
        state_store.update_state("hardware", {"evolution_pending_reload": True})
        logger.info("✅ [Bootstrap] Evolution broadcast complete.")

    def _persist_state(self) -> None:
        """Saves bootstrap state to a JSON file for cross-platform access."""
        import json
        status_path = self.resolver.project_root / "system_status.json"
        try:
            with open(status_path, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist bootstrap state: {e}", exc_info=True)

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
                except json.JSONDecodeError:
                    logger.warning("Corrupted system_status.json, running full bootstrap", exc_info=True)
            return self.run_full_bootstrap()
        return self.state

# Singleton Access
_manager = None
def get_bootstrap_manager() -> BootstrapManager:
    """Get the bootstrap manager."""
    global _manager
    if _manager is None:
        _manager = BootstrapManager()
    return _manager
