"""
Tiered Configuration Loader
Implements the Default -> User -> Angela priority chain.
"""

import os
import yaml
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class TieredConfigLoader:
    """
    Advanced loader that merges three layers of configuration:
    1. Default (*.default.yaml)
    2. User (*.user.yaml)
    3. Angela (*.evolved.yaml)
    """
    
    def __init__(self, backend_root: Optional[Path] = None):
        self.backend_root = backend_root or Path(__file__).resolve().parent.parent.parent.parent.parent
        self.config_dir = self.backend_root / "configs"
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get_config(self, tier_path: str) -> Dict[str, Any]:
        """
        Loads and merges configuration for a given relative path (e.g., 'standard/science/biological')
        """
        if tier_path in self._cache:
            return self._cache[tier_path]

        base_path = self.config_dir / tier_path
        
        # 1. Load Default (Lowest Priority)
        config = self._load_file(base_path.with_suffix(".default.yaml"))
        
        # 2. Merge User Overrides
        user_config = self._load_file(base_path.with_suffix(".user.yaml"))
        self._deep_merge(config, user_config)
        
        # 3. Merge Angela's Evolution (Highest Priority)
        evolved_config = self._load_file(base_path.with_suffix(".evolved.yaml"))
        self._deep_merge(config, evolved_config)
        
        self._cache[tier_path] = config
        return config

    def _load_file(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"[ConfigLoader] Failed to load {path}: {e}", exc_info=True)
            return {}

    def _deep_merge(self, base: Dict[str, Any], overrides: Dict[str, Any]):
        """Recursively merges overrides into base."""
        for k, v in overrides.items():
            if isinstance(v, dict) and k in base and isinstance(base[k], dict):
                self._deep_merge(base[k], v)
            else:
                base[k] = v

    def clear_cache(self):
        self._cache = {}

# Singleton instance
loader = TieredConfigLoader()

def get_config(tier_path: str) -> Dict[str, Any]:
    return loader.get_config(tier_path)
