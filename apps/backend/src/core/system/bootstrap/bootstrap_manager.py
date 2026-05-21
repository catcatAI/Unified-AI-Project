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
        """Executes the full chain of hardware and environment checks."""
        logger.info("🚀 [Bootstrap] Starting formalized system bootstrap...")
        
        # 1. Resolve Environment
        env_summary = self.resolver.get_env_summary()
        if not self.resolver.check_python_compliance():
            logger.warning("⚠️ [Bootstrap] Python version may cause instability.")
            
        # 2. Probe Hardware
        specs = self.prober.probe()
        perf_constants = self.prober.get_performance_constants()
        
        # 3. Consolidate State
        self.state = {
            "environment": env_summary,
            "hardware": specs.__dict__,
            "performance": perf_constants,
            "status": "ready" if env_summary["pnpm_workspace"] else "degraded"
        }
        
        self._initialized = True
        logger.info(f"✅ [Bootstrap] System ready. Tier: {specs.performance_tier}")
        return self.state

    def get_state(self) -> Dict[str, Any]:
        """Returns the current bootstrap state, running if necessary."""
        if not self._initialized:
            return self.run_full_bootstrap()
        return self.state

# Singleton Access
_manager = None
def get_bootstrap_manager() -> BootstrapManager:
    global _manager
    if _manager is None:
        _manager = BootstrapManager()
    return _manager
