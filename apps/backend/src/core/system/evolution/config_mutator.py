"""
Config Mutator - Secure System Evolution Engine
Responsible for atomic and validated updates to configuration files.
MODIFIED for Tiered Architecture: Angela's mutations only touch the '.evolved' layer.
"""

import os
from typing import Any, Dict, Optional


class ConfigMutator:
    """提议并验证配置变更, 确保原子性与安全性."""

    def __init__(self, config: Optional[dict] = None) -> None:
        self.config = config or {}

    def propose_change(self, category: str, updates: dict) -> Dict[str, Any]:
        validation = self._validate(category, updates)
        is_valid = validation.get("is_valid", False)
        return {
            "ready_to_apply": is_valid,
            "validation": validation,
            "updates": updates,
            "category": category,
        }

    def _validate(self, category: str, updates: dict) -> Dict[str, Any]:
        if category == "biological":
            return self._validate_biological(updates)
        if category == "llm":
            return self._validate_llm(updates)
        return {"is_valid": True, "reason": "unknown category"}

    def _validate_biological(self, updates: dict) -> Dict[str, Any]:
        hormones = updates.get("hormones", {})
        for name, params in hormones.items():
            half_life = params.get("half_life", 0)
            if half_life < 0:
                return {"is_valid": False, "reason": f"{name}.half_life must be non-negative"}
        return {"is_valid": True, "reason": "ok"}

    def _validate_llm(self, updates: dict) -> Dict[str, Any]:
        for provider, params in updates.items():
            env_key = params.get("api_key_env", "")
            if env_key and not os.environ.get(env_key, ""):
                return {"is_valid": False, "reason": f"env var {env_key} not set"}
            value = params.get("api_key", "")
            if value and len(value) < 8:
                return {"is_valid": False, "reason": f"{provider} api_key too short"}
        return {"is_valid": True, "reason": "ok"}
