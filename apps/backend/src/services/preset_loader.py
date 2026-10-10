# =============================================================================
# ANGELA-MATRIX: [L2] [α] [A] [L2]
# =============================================================================
"""Preset pack loader: dual_model / executor_framing / agent_mounts.

Small cached YAML reader (stdlib + pyyaml). Every consumer keeps hardcoded
fallbacks so a missing preset file degrades to built-in behavior, never to
a crash. Presets tune proven envelopes; they never invent capabilities.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

_PRESET_DIR = Path(__file__).resolve().parents[2] / "configs" / "presets"


def _expand(value: Any) -> Any:
    if isinstance(value, str):
        return os.path.expandvars(value.replace("$HOME", str(Path.home())))
    if isinstance(value, list):
        return [_expand(v) for v in value]
    if isinstance(value, dict):
        return {k: _expand(v) for k, v in value.items()}
    return value


@lru_cache(maxsize=8)
def load_preset(name: str) -> Dict[str, Any]:
    """Load <name>.preset.yaml (cached); {} when absent/unreadable."""
    path = _PRESET_DIR / f"{name}.preset.yaml"
    try:
        import yaml

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return _expand(data) if isinstance(data, dict) else {}
    except Exception as exc:
        logger.debug("preset %s unavailable: %s", name, exc)
        return {}


def framing_for(kind: str) -> Dict[str, Any]:
    """Micro/think/verify prompt shapes (preset wins, hardcoded fallback)."""
    preset = load_preset("executor_framing")
    if isinstance(preset.get(kind), dict):
        return dict(preset[kind])
    return {}


def kind_params(kind: str) -> Dict[str, Any]:
    """Per-kind generation params (slot/temperature/tokens/timeout)."""
    preset = load_preset("dual_model")
    params = preset.get("per_kind_params", {})
    if isinstance(params, dict) and isinstance(params.get(kind), dict):
        return dict(params[kind])
    return {}
