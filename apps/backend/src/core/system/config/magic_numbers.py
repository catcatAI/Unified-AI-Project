"""
ANGELA-MATRIX: [L2-L3] [β] [C] [L1]
P6-3: Centralized access to previously-hardcoded magic numbers.
All values loaded from TieredConfigLoader with inline fallback defaults.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

_MAGIC_CACHE: Dict[str, Any] = {}
_HARDWARE_PROFILE: Optional[Any] = None  # lazy-loaded HardwareProfile singleton
_SUFFIX_LEAF_INDEX: Optional[Tuple[int, Dict[str, Any]]] = None  # (id(config), {key: value})


def _get_hardware_profile() -> Optional[Any]:
    """Lazy-load and cache HardwareProfile singleton.

    Returns None if import fails (graceful degradation).
    """
    global _HARDWARE_PROFILE
    if _HARDWARE_PROFILE is None:
        try:
            from core.system.config.hardware_profile import HardwareProfile

            _HARDWARE_PROFILE = HardwareProfile()
            logger = logging.getLogger(__name__)
            logger.info(
                "HardwareProfile activated: %s (multiplier=%.1f)",
                _HARDWARE_PROFILE.scenario.value,
                _HARDWARE_PROFILE.profile.base_multiplier,
            )
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.debug("HardwareProfile unavailable, using defaults: %s", e)
            _HARDWARE_PROFILE = False  # sentinel: don't retry
    return _HARDWARE_PROFILE if _HARDWARE_PROFILE is not False else None


def _load_config() -> Optional[Dict[str, Any]]:
    """Try to load config via tiered_loader; return None if unavailable."""
    global _MAGIC_CACHE
    if _MAGIC_CACHE:
        return _MAGIC_CACHE
    try:
        from pathlib import Path as _Path

        from core.system.config.tiered_loader import get_config as _tiered_get

        configs: Dict[str, Any] = {}
        # Discover all tiered config files under the configs root
        from core.system.config.tiered_loader import _CONFIGS_ROOT

        if _CONFIGS_ROOT and _CONFIGS_ROOT.is_dir():
            for default_file in sorted(_CONFIGS_ROOT.rglob("*.default.yaml")):
                rel = default_file.relative_to(_CONFIGS_ROOT)
                # e.g. system/llm.default.yaml → dotted path "system/llm"
                dotted_path = "/".join(rel.parts[:-1] + (rel.stem.replace(".default", ""),))

                layer_config = _tiered_get(dotted_path)
                if layer_config and isinstance(layer_config, dict):
                    # Nest under path segments so dotted key lookups work
                    node: Any = configs
                    for seg in dotted_path.split("/"):
                        node = node.setdefault(seg, {})
                    node.update(layer_config)

        _MAGIC_CACHE = configs
    except Exception as e:
        # broad except intentional: config loading must never crash; silent fallback to defaults
        logger = logging.getLogger(__name__)
        logger.warning("Tiered config loading failed, using defaults: %s", e, exc_info=True)
        _MAGIC_CACHE = {}
    return _MAGIC_CACHE


def _get(key: str, default: Any = None) -> Any:
    """Look up a key from the config, falling back to default.

    Two lookup strategies are tried in order:
    1. Exact dotted-path walk (e.g. ``system.compute.compute``).
    2. Suffix match: the key (or its dotted tail) must match the tail of a
       leaf path in the nested config tree (e.g. ``sleep_short`` matches
       ``system.timing.timing.loop.sleep_short``). This lets call sites use
       flat key names while the YAML stays hierarchically organized.
    """
    config = _load_config()
    if config is None:
        return default

    # 1. Exact dotted-path walk
    keys = key.split(".")
    val = config
    found = True
    for k in keys:
        if isinstance(val, dict) and k in val:
            val = val[k]
        else:
            found = False
            break
    if found:
        if isinstance(val, dict) and not val:
            return default
        return val if val is not None else default

    # 2. Suffix match against leaf paths
    candidates = _suffix_matches_indexed(config, key)
    if not candidates:
        return default
    if len(candidates) == 1:
        val = candidates[0][1]
        return val if val is not None else default
    # Multiple matches: prefer system-rooted paths (authoritative tier)
    for path, value in candidates:
        if path.split(".")[0] == "system":
            return value if value is not None else default
    return default


def _leaf_dotted_index(node: Dict[str, Any]) -> Dict[str, List[Tuple[str, Any]]]:
    """Flatten a nested config tree into {final_segment: [(full_dotted_path, value)]}.

    Built once per config object and reused by _suffix_matches_indexed; avoids a
    full recursive tree walk on every config lookup miss. Buckets preserve the
    dictionary insertion order that _suffix_matches walks, so result ordering is
    identical.
    """
    index: Dict[str, List[Tuple[str, Any]]] = {}

    def walk(current: Any, prefix: str) -> None:
        for k, v in current.items():
            path = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                walk(v, path)
            else:
                index.setdefault(k, []).append((path, v))

    walk(node, "")
    return index


def _suffix_matches_indexed(node: Dict[str, Any], key: str) -> list:
    """Exact-preserving replacement for _suffix_matches(node, key) using a leaf index.

    A leaf path is included iff ``path == key or path.endswith("." + key)``, so
    every candidate shares the query key's final segment — only that segment
    bucket is scanned instead of the whole config tree.
    """
    global _SUFFIX_LEAF_INDEX
    if _SUFFIX_LEAF_INDEX is None or _SUFFIX_LEAF_INDEX[0] != id(node):
        _SUFFIX_LEAF_INDEX = (id(node), _leaf_dotted_index(node))
    index = _SUFFIX_LEAF_INDEX[1]
    tail = key.split(".")[-1]
    result = []
    for path, value in index.get(tail, ()):
        if path == key or path.endswith("." + key):
            result.append((path, value))
    return result


def _safe_float(value: Any, default: Any = None) -> Any:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default if default is not None else value


def _safe_int(value: Any, default: Any = None) -> Any:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default if default is not None else value


def loop_sleep(key: str, default: float = 1.0) -> float:
    """Get loop sleep interval with hardware-aware frequency scaling.

    Returns the configured interval from tiered config, scaled by the
    HardwareProfile's base_multiplier so that loops run faster on
    high-performance hardware and slower on power-constrained devices.
    """
    base = _safe_float(_get(key, default), default)
    profile = _get_hardware_profile()
    if profile is not None:
        return profile.apply_multiplier(base)
    return base


def timeout_value(key: str, default: float = 30.0) -> float:
    return _safe_float(_get(key, default), default)


def cache_value(key: str, default: int = 100) -> int:
    return _safe_int(_get(key, default), default)


def batch_value(key: str, default: int = 10) -> int:
    return _safe_int(_get(key, default), default)


def llm_param(key: str, default: float = 0.7) -> float:
    return _safe_float(_get(key, default), default)


def retry_value(key: str, default: int = 3) -> int:
    return _safe_int(_get(key, default), default)


def threshold_value(key: str, default: float = 0.8) -> float:
    return _safe_float(_get(key, default), default)


def behavior_threshold(key: str, default: float = 0.5) -> float:
    return _safe_float(_get(key, default), default)


def behavior_feedback(key: str, default: float = 0.5) -> float:
    return _safe_float(_get(key, default), default)


def behavior_executor(key: str, default: float = 0.5) -> float:
    return _safe_float(_get(key, default), default)


def _apply_hw_multiplier(value: float) -> float:
    if not isinstance(value, (int, float)):
        return value
    profile = _get_hardware_profile()
    if profile is not None:
        return profile.apply_multiplier(value)
    return value


def heartbeat_value(key: str, default: float = 1.0) -> float:
    return _apply_hw_multiplier(_safe_float(_get(key, default), default))


def timing_value(key: str, default: float = 0.1) -> float:
    return _apply_hw_multiplier(_safe_float(_get(key, default), default))


def confidence_value(key: str, default: float = 0.7) -> float:
    return _safe_float(_get(key, default), default)


def learning_rate(key: str, default: float = 0.05) -> float:
    return _safe_float(_get(key, default), default)


def latency_value(key: str, default: float = 10.0) -> float:
    return _safe_float(_get(key, default), default)


def limit_value(key: str, default: int = 100) -> int:
    return _safe_int(_get(key, default), default)


def lifecycle_value(key: str, default: float = 0.5) -> float:
    """Lifecycle feedback threshold (e.g. success_rate_low, success_rate_high, adjustment)."""
    return _safe_float(_get(key, default), default)


# =============================================================================
# Capacity Limits — numeric AND percentage limits work TOGETHER.
# Every upper limit is a pair [max_bytes, max_percent]; the effective cap is
# min(max_bytes, total × max_percent). Whichever fires first is the cap.
# =============================================================================

def _get_capacity_config() -> Dict[str, Any]:
    """Get the capacity cascade from tiered config: system.capacity.capacity."""
    return _get("system.capacity.capacity", {})


def capacity_bytes(key: str, default: Optional[float] = None) -> Optional[float]:
    """Numeric (bytes) floor from capacity config. None = not set."""
    return _get_capacity_config().get(key, default)


def capacity_percent(key: str, default: Optional[float] = None) -> Optional[float]:
    """Percentage limit (0..1) for the same resource. None = not set."""
    return _get_capacity_config().get(key, default)


def capacity_loss_model(key: str, default: str = "precision") -> str:
    """Loss model on cap-hit: 'precision' (graceful) vs 'truncate' (hard)."""
    return _get_capacity_config().get(key, {}).get("loss_model", default)


def effective_capacity_bytes(
    key: str,
    total_gb: Optional[float] = None,
    numeric_mb: Optional[float] = None,
    percent: Optional[float] = None,
) -> float:
    """Joint numeric+percent cap: effective = min(numeric_bytes, total×percent).

    ``key`` is the resource block (e.g. 'memory' or 'disk'); its numeric cap
    comes from its ``default_mb`` / ``dynamic_mb`` member, and its ``percent``
    from ``max_percent``. Explicit ``numeric_mb``/``percent`` overrides win.
    ``total_gb`` = physical RAM / partition size; if absent, only numeric cap
    applies (percent requires a base to scale against). Returns bytes.
    """
    cfg = _get_capacity_config().get(key, {})
    if numeric_mb is None:
        numeric_mb = cfg.get("default_mb", cfg.get("dynamic_mb", cfg.get("max_vocab_bytes", 0)))
    if percent is None:
        percent = cfg.get("max_percent", 0.0)
    numeric_bytes = max(0.0, float(numeric_mb) * 1024 * 1024)
    if total_gb is not None and total_gb > 0 and percent and 0 < percent <= 1:
        cap_by_percent = float(total_gb) * 1024 * 1024 * 1024 * float(percent)
        return min(numeric_bytes, cap_by_percent)
    return numeric_bytes


# =============================================================================
# GPU/CPU Compute Configuration
# =============================================================================

def _get_compute_config() -> Dict[str, Any]:
    """Get compute configuration from tiered config."""
    # Config is nested: system.compute.compute
    return _get("system.compute.compute", {})


def compute_mode(feature: str, default: str = "auto") -> str:
    """Get compute mode for a specific feature: 'auto', 'on', or 'off'."""
    config = _get_compute_config()
    # Check feature-specific mode first
    feature_cfg = config.get(feature, {})
    if isinstance(feature_cfg, dict) and "mode" in feature_cfg:
        return feature_cfg["mode"]
    # Fall back to global mode
    global_cfg = config.get("global", {})
    return global_cfg.get("mode", default)


def compute_bool(feature: str, default: bool = True) -> bool:
    """Get boolean compute setting for a feature (on/off -> True/False)."""
    mode = compute_mode(feature, "auto")
    if mode == "off":
        return False
    if mode == "on":
        return True
    # auto - check hardware
    profile = _get_hardware_profile()
    if profile is not None:
        # Check per-profile override
        profile_cfg = _get_compute_config().get("profiles", {}).get(profile.scenario.value, {})
        feature_profile = profile_cfg.get(feature, {})
        if "mode" in feature_profile:
            return feature_profile["mode"] != "off"
        # Check global profile override
        global_profile = profile_cfg.get("global", {})
        if "mode" in global_profile:
            return global_profile["mode"] != "off"
        # Check force_cpu_on_low_power
        if profile_cfg.get("force_cpu_on_low_power", True):
            if profile.scenario in (HardwareScenario.LAPTOP_POWER_SAVER, HardwareScenario.LOW_POWER_DEVICE):
                return False
    return True


def compute_int(feature: str, key: str, default: int = 0) -> int:
    """Get integer compute setting for a feature (e.g., batch_size, max_vocab).
    
    Priority: profile-specific feature > profile global > global feature > default
    """
    config = _get_compute_config()
    profile = _get_hardware_profile()
    
    # Check profile-specific first
    if profile is not None:
        profile_cfg = config.get("profiles", {}).get(profile.scenario.value, {})
        feature_profile = profile_cfg.get(feature, {})
        val = feature_profile.get(key)
        if val is not None:
            return _safe_int(val, default)
        global_profile = profile_cfg.get("global", {})
        val = global_profile.get(key)
        if val is not None:
            return _safe_int(val, default)
    
    # Fall back to global feature config
    feature_cfg = config.get(feature, {})
    if isinstance(feature_cfg, dict):
        val = feature_cfg.get(key)
        if val is not None:
            return _safe_int(val, default)
    
    return default


def compute_float(feature: str, key: str, default: float = 0.0) -> float:
    """Get float compute setting for a feature.

    Priority: profile-specific feature > profile global > global feature > default
    (mirrors compute_int so hardware-profile overrides actually take effect).
    """
    config = _get_compute_config()
    profile = _get_hardware_profile()

    # Check profile-specific first
    if profile is not None:
        profile_cfg = config.get("profiles", {}).get(profile.scenario.value, {})
        feature_profile = profile_cfg.get(feature, {})
        val = feature_profile.get(key)
        if val is not None:
            return _safe_float(val, default)
        global_profile = profile_cfg.get("global", {})
        val = global_profile.get(key)
        if val is not None:
            return _safe_float(val, default)

    # Fall back to global feature config
    feature_cfg = config.get(feature, {})
    if isinstance(feature_cfg, dict):
        val = feature_cfg.get(key)
        if val is not None:
            return _safe_float(val, default)

    return default


def compute_log_fallback() -> bool:
    """Whether to log GPU->CPU fallback events."""
    config = _get_compute_config()
    global_cfg = config.get("global", {})
    return global_cfg.get("log_fallback", True)


# =============================================================================
# Dynamic Model Sizing (conservative / extended)
# =============================================================================
# GARDEN SNN weight matrix: vocab² × 4 bytes
#   vocab=10K → 400MB   (conservative)
#   vocab=52K → ~10GB   (extended — the 10 GB trained-model target)
# The 52K target comes from capacity.default.yaml (garden_snn.vocabulary
# target_keys). The matrix the model allocates is then ALSO bounded by the
# joint [bytes, %ram] capacity cascade (min of the two), so vocab can reach
# 10 GB only when physical RAM allows; otherwise app runs precision-loss.

def model_sizing_config() -> Dict[str, int]:
    """Return (max_vocab, connection_budget) based on the sizing mode.

    Conservative (default): max_vocab=10000, connection_budget=50000.
    Extended (ANGELA_EXTENDED_MODEL=1): driven by the capacity cascade — the
    vocabulary target (default 51812 → ~10 GB matrix), then clamped by the
    joint memory/% cap so it never exceeds what RAM actually holds.
    """
    import os
    extended = os.environ.get("ANGELA_EXTENDED_MODEL", "0") == "1"
    if extended:
        target_keys = _safe_int(
            _get_capacity_config().get("garden_snn", {}).get("vocabulary", {}).get(
                "target_keys"
            ),
            51812,
        )
        # Clamp by memory: bytes cap / (4 B) then sqrt → max keys RAM allows.
        ram_total = _probe_ram_total_gb()
        if ram_total and ram_total > 0:
            dynamic_mb = _get_capacity_config().get("memory", {}).get("dynamic_mb", 8192)
            cap_bytes = effective_capacity_bytes("memory", total_gb=ram_total, numeric_mb=dynamic_mb)
            max_keys_by_ram = int((cap_bytes / 4.0) ** 0.5)
            target_keys = max(1, min(target_keys, max_keys_by_ram))
        else:
            target_keys = max(1, target_keys)
        budget = _safe_int(
            _get_capacity_config().get("ed3n", {}).get("core_connections"), 200000
        )
        logger.info(
            "Model sizing: EXTENDED mode (max_vocab=%d, budget=%d ≈%.2fGB matrix)",
            target_keys,
            budget,
            target_keys * target_keys * 4 / 1024**3,
        )
        return {"max_vocab": target_keys, "connection_budget": budget}
    logger.info("Model sizing: CONSERVATIVE mode (max_vocab=10000, budget=50000)")
    return {"max_vocab": 10000, "connection_budget": 50000}


def _probe_ram_total_gb() -> Optional[float]:
    """Total physical RAM in GB (best-effort), else None."""
    try:
        import psutil  # type: ignore[import-untyped]

        return psutil.virtual_memory().total / (1024**3)
    except Exception:
        pass
    try:
        import shutil  # noqa: F401  (unused; kept for parity guard)

        return None
    except Exception:
        return None


# Re-export HardwareScenario for compute functions
from core.system.config.hardware_profile import HardwareScenario  # noqa: E402
