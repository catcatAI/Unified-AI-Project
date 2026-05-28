"""
Config Mutator - Secure System Evolution Engine
Responsible for atomic and validated updates to configuration files.
MODIFIED for Tiered Architecture: Angela's mutations only touch the '.evolved' layer.
"""

import os
import json
import yaml
import logging
import shutil
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class ConfigMutator:
    """
    Handles secure modifications to Angela's system DNA.
    Implements validation, and atomic write operations to the .evolved layer.
    """
    
    def __init__(self, backend_root: Optional[Path] = None):
        self.backend_root = backend_root or Path(__file__).parent.parent.parent.parent
        self.config_dir = self.backend_root / "configs"

    def propose_change(self, config_type: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a 'proposal' for a change without applying it.
        """
        validation = self.validate_updates(config_type, updates)
        return {
            "config_type": config_type,
            "proposed_updates": updates,
            "validation": validation,
            "timestamp": datetime.now().isoformat(),
            "ready_to_apply": validation["is_valid"]
        }

    def validate_updates(self, config_type: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Category-aware validation."""
        errors = []
        warnings = []
        
        # 1. Structural Validation
        if not isinstance(updates, dict):
            errors.append("Update payload must be a dictionary")
            return {"is_valid": False, "errors": errors, "warnings": warnings}

        # 2. Logic Validation (Standard Tier)
        if config_type == "biological":
            hormones = updates.get("hormones", {})
            for h_name, h_vals in hormones.items():
                if h_vals.get("half_life", 1) <= 0:
                    errors.append(f"Invalid half-life for {h_name}")

        elif config_type == "behavior":
            mov = updates.get("movement", {})
            if mov.get("jump_probability", 0) > 1.0:
                errors.append("Jump probability cannot exceed 1.0")
        
        # 3. Security Validation (System Tier)
        elif config_type == "llm":
            from core.security.key_validator import KeyValidator
            validator = KeyValidator()
            for provider, p_cfg in updates.items():
                if not isinstance(p_cfg, dict): continue
                if "api_key_env" in p_cfg:
                    env_val = os.environ.get(p_cfg["api_key_env"], "")
                    res = validator.validate_key(p_cfg["api_key_env"], env_val)
                    if not res.is_valid:
                        warnings.extend(res.issues)

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def apply_mutation(self, config_type: str, updates: Dict[str, Any]) -> bool:
        """
        Physically writes the changes to the .evolved layer.
        """
        if not self.validate_updates(config_type, updates)["is_valid"]:
            logger.error(f"[Mutator] Blocked invalid mutation attempt for {config_type}", exc_info=True)
            return False

        file_path = self._get_path(config_type)
        if not file_path: return False

        try:
            # 1. Load current EVOLVED data (if any)
            current_evolved = self._load_current(file_path)
            
            # 2. Deep update the evolved layer
            self._deep_update(current_evolved, updates)
            
            # 3. Atomic write to the evolved layer
            tmp_path = file_path.with_suffix(".tmp")
            self._write_file(tmp_path, current_evolved)
            os.replace(tmp_path, file_path)
            
            logger.info(f"✅ [Mutator] System evolved: {config_type} layer updated.")
            return True
        except Exception as e:
            logger.error(f"❌ [Mutator] Evolution write failed for {config_type}: {e}", exc_info=True)
            return False

    def _get_path(self, config_type: str) -> Optional[Path]:
        """
        Maps a config type to its physical evolved path.
        Hierarchy: 
        - System: system/*.evolved.yaml
        - Standard: standard/<cat>/*.evolved.yaml
        - MOD: mods/*.evolved.yaml
        """
        paths = {
            # S-Tier (System)
            "llm": self.config_dir / "system/llm.evolved.yaml",
            "keys": self.config_dir / "system/keys.evolved.yaml",
            "bootstrap": self.config_dir / "system/bootstrap.evolved.yaml",
            
            # A-Tier (Standard)
            "biological": self.config_dir / "standard/science/biological.evolved.yaml",
            "spatial": self.config_dir / "standard/science/spatial.evolved.yaml",
            "dynamic": self.config_dir / "standard/behavior/dynamic.evolved.yaml",
            "behavior": self.config_dir / "standard/behavior/behavior.evolved.yaml",
            "matrix": self.config_dir / "standard/matrix/matrix.evolved.yaml",
            "prompts": self.config_dir / "standard/narrative/prompts.evolved.yaml",
            "demo": self.config_dir / "standard/behavior/demo.evolved.yaml",
            
            # M-Tier (MOD)
            "mods": self.config_dir / "mods/active_mods.evolved.yaml"
        }
        return paths.get(config_type)

    def _load_current(self, path: Path) -> Dict[str, Any]:
        if not path.exists(): return {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception:
            logger.warning(f"Failed to load {path}, returning empty config", exc_info=True)
            return {}

    def _write_file(self, path: Path, data: Dict[str, Any]):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, sort_keys=False)

    def _deep_update(self, base: Dict[str, Any], updates: Dict[str, Any]):
        """Recursively updates a dictionary."""
        for k, v in updates.items():
            if isinstance(v, dict) and k in base and isinstance(base[k], dict):
                self._deep_update(base[k], v)
            else:
                base[k] = v
