"""
Tiered Configuration Loader
Implements the Default -> User -> Angela (evolved) priority chain.

Config files live under ``apps/backend/configs/`` and are organised by
dotted path.  For example ``get_config("system/llm")`` loads and merges:

  configs/system/llm.default.yaml  (lowest priority)
  configs/system/llm.user.yaml
  configs/system/llm.evolved.yaml  (highest priority)
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Resolve the configs root directory (apps/backend/configs/)
#
# There are two ``configs/`` dirs in the project:
#   - apps/backend/configs/      ← the canonical one we want
#   - apps/backend/src/configs/  ← a smaller supplementary dir
#
# We prefer the canonical one by checking for ``system/llm.default.yaml``.
# ---------------------------------------------------------------------------
_THIS_FILE = Path(__file__).resolve()
_CONFIGS_ROOT: Optional[Path] = None

# Walk up from this file to find candidate configs directories
_candidates: list = []
_candidate = _THIS_FILE.parent
for _ in range(10):  # safety bound
    cfg_dir = _candidate / "configs"
    if cfg_dir.is_dir():
        _candidates.append(cfg_dir)
    _candidate = _candidate.parent

# Pick the one that looks like the canonical configs root
# (has system/llm.default.yaml or at least system/ subdirectory with .yaml files)
for cand in _candidates:
    if (cand / "system" / "llm.default.yaml").is_file():
        _CONFIGS_ROOT = cand
        break

# Fallback: use the first candidate found
if _CONFIGS_ROOT is None and _candidates:
    _CONFIGS_ROOT = _candidates[0]

# ---------------------------------------------------------------------------
# Priority layers (lowest → highest)
# ---------------------------------------------------------------------------
LAYERS = ("default", "user", "evolved")


def _read_config_file(path: Path) -> Optional[Dict[str, Any]]:
    """Read a single YAML/JSON config file and return its dict content."""
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8")
        text = text.strip()
        if not text:
            return None
        # Try JSON first (some .yaml files use JSON syntax)
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # Fall back to YAML if PyYAML is available
            try:
                import yaml
                data = yaml.safe_load(text)
            except ImportError:
                logger.warning(
                    "PyYAML not installed and file is not valid JSON: %s", path
                )
                return None
        if isinstance(data, dict):
            return data
        return None
    except Exception as exc:
        logger.warning("Failed to read config file %s: %s", path, exc)
        return None


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge *override* into a copy of *base*.

    - Dict values are merged recursively.
    - All other types in *override* replace the corresponding *base* value.
    """
    result = dict(base)
    for key, over_val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(over_val, dict):
            result[key] = _deep_merge(result[key], over_val)
        else:
            result[key] = over_val
    return result


def _load_merged_config(dotted_path: str) -> Optional[Dict[str, Any]]:
    """Load and merge the three layers for a given dotted config path.

    ``dotted_path`` uses ``/`` as separator (e.g. ``"system/llm"``).
    The corresponding directory on disk is ``<configs_root>/<path>/`` and
    files are ``<name>.{default,user,evolved}.yaml``.
    """
    if _CONFIGS_ROOT is None:
        return None

    # The dotted path maps to a directory + base file name.
    # "system/llm"          → dir: configs/system/          base: "llm"
    # "standard/behavior/thresholds" → dir: configs/standard/behavior/  base: "thresholds"
    parts = dotted_path.split("/")
    base_name = parts[-1]
    dir_path = _CONFIGS_ROOT / "/".join(parts[:-1])
    if not dir_path.is_dir():
        return None

    merged: Optional[Dict[str, Any]] = None
    for layer in LAYERS:
        candidate = dir_path / f"{base_name}.{layer}.yaml"
        layer_data = _read_config_file(candidate)
        if layer_data is not None:
            if merged is None:
                merged = layer_data
            else:
                merged = _deep_merge(merged, layer_data)
            logger.debug("Loaded config layer %s from %s", layer, candidate)

    return merged


# ---------------------------------------------------------------------------
# In-memory cache so we only read from disk once per process lifetime.
# ---------------------------------------------------------------------------
_cache: Dict[str, Optional[Dict[str, Any]]] = {}


def get_config(path: str) -> Optional[Dict[str, Any]]:
    """Retrieve config by dotted path (e.g. ``'system/llm'``).

    Returns the deep-merged result of default → user → evolved layers,
    or ``None`` if no config files exist for the given path.
    """
    if path in _cache:
        return _cache[path]

    config = _load_merged_config(path)
    _cache[path] = config

    if config is not None:
        logger.info("Config loaded for path '%s' (%d keys)", path, len(config))
    else:
        logger.debug("No config files found for path '%s'", path)

    return config
