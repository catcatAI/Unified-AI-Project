#!/usr/bin/env python3
"""
Angela AI - Configuration Loader
配置加载器

安全地加载和访问应用配置，提供类型安全的配置访问。
支持 YAML 多文件读取、热重载、Authority + Learned 双层配置合并。

Authority 層（src/config/*.yaml）由人類維護，Learned 層（data/angela_learned/*.yaml）
由 Angela 運行時學習寫入。Learned 不能覆蓋 Authority 的意圖定義。
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


def _value_to_level(value: float) -> str:
    """Map a scalar (expected 0.0-1.0) to a coordinate interpretation level."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "neutral"
    if v >= 0.75:
        return "high_positive"
    if v >= 0.55:
        return "mid_positive"
    if v >= 0.45:
        return "neutral"
    if v >= 0.25:
        return "mid_negative"
    return "high_negative"


class AngelaConfig:
    """Central configuration holder with tiered authority + learned access."""

    def __init__(self, config_dir: Optional[str] = None):
        self._config_dir = (
            Path(config_dir) if config_dir else Path(__file__).parent.parent / "config"
        )
        # Learned config lives outside the authority tree (runtime-writable).
        self._angela_dir = Path(__file__).resolve().parents[2] / "data" / "angela_learned"
        # Per-file config keyed by filename stem (authority access).
        self._files: Dict[str, Dict[str, Any]] = {}
        # Flattened merge of all files (backward-compatible ``get()`` access).
        self._data: Dict[str, Dict[str, Any]] = {}
        # Track mtimes for hot-reload.
        self._file_paths: Dict[str, Path] = {}
        self._mtimes: Dict[str, float] = {}
        self._load_all()

    # ------------------------------------------------------------------ #
    # Loading
    # ------------------------------------------------------------------ #
    def _load_all(self) -> None:
        """Load all YAML config files from the config directory."""
        self._files = {}
        self._data = {}
        self._file_paths = {}
        self._mtimes = {}
        if not self._config_dir.exists():
            logger.warning(f"Config directory not found: {self._config_dir}")
            return
        for yaml_file in sorted(self._config_dir.glob("*.yaml")):
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                if not isinstance(data, dict):
                    continue
                stem = yaml_file.stem
                self._files[stem] = data
                self._file_paths[stem] = yaml_file
                try:
                    self._mtimes[stem] = yaml_file.stat().st_mtime
                except OSError as e:
                    logger.debug("Config file stat failed: %s (%s)", yaml_file, e)
                # Flatten into the merged view for backward compatibility.
                for key, value in data.items():
                    if isinstance(value, dict) and isinstance(self._data.get(key), dict):
                        self._data[key].update(value)
                    else:
                        self._data[key] = value
            except Exception as e:
                logger.warning(f"Failed to load config {yaml_file}: {e}")

    # ------------------------------------------------------------------ #
    # Authority access
    # ------------------------------------------------------------------ #
    def get_authority(self, section: str, default: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get authority config for a section (by config filename stem)."""
        default = default if default is not None else {}
        if section in self._files:
            return self._files[section]
        return self._data.get(section, default)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    # ------------------------------------------------------------------ #
    # Intent access
    # ------------------------------------------------------------------ #
    def get_intents(self) -> Dict[str, Any]:
        """Return the authority intent definitions from angela_core."""
        return self.get_authority("angela_core", {}).get("intents", {})

    def get_intent_keywords(self, intent: str) -> List[str]:
        """Return keywords for an intent (authority first, registry fallback)."""
        intents = self.get_intents()
        entry = intents.get(intent, {})
        keywords = entry.get("keywords", []) if isinstance(entry, dict) else []
        if keywords:
            return list(keywords)
        try:
            from core.intent_registry import IntentRegistry

            return IntentRegistry().get_keywords(intent)
        except Exception as e:
            logger.debug("Intent registry lookup failed: %s", e)
            return []

    def get_drive_all_operations(self) -> Dict[str, Any]:
        """Return google_drive sub-operations config (list/sync/search/...)."""
        gd = self.get_intents().get("google_drive", {})
        if isinstance(gd, dict):
            return gd.get("sub_operations", {})
        return {}

    # ------------------------------------------------------------------ #
    # LLM / complexity access
    # ------------------------------------------------------------------ #
    def get_llm_config(self) -> Dict[str, Any]:
        """Return LLM provider config with a guaranteed ``providers`` key.

        Prefers the unified ``system/llm`` config (the single source of truth);
        falls back to the legacy ``llm_providers`` authority file.
        """
        merged: Dict[str, Any] = {}
        try:
            from core.system.config.tiered_loader import get_config

            unified = get_config("system/llm")
            backends = unified.get("backends", {})
            if isinstance(backends, dict) and backends:
                merged["providers"] = {
                    bid: {
                        "provider": bcfg.get("provider"),
                        "model": bcfg.get("model") or bcfg.get("model_name"),
                    }
                    for bid, bcfg in backends.items()
                    if isinstance(bcfg, dict)
                }
                routing = unified.get("routing", {})
                if isinstance(routing, dict):
                    merged["routing_policy"] = routing.get("policy", {})
                    merged["fallback_chain"] = routing.get("fallback_chain", {})
                    merged["prompt_templates"] = routing.get("prompt_templates", {})
                return merged
        except Exception:
            logger.warning(
                "get_llm_config: unified system/llm read failed, falling back", exc_info=True
            )
        providers_cfg = self.get_authority("llm_providers", {})
        if isinstance(providers_cfg, dict) and providers_cfg.get("providers"):
            return providers_cfg
        # Fall back to angela_core.llm.backend_priority.
        ac_llm = self.get_authority("angela_core", {}).get("llm", {})
        priority = ac_llm.get("backend_priority", ["ollama"])
        merged = dict(providers_cfg) if isinstance(providers_cfg, dict) else {}
        merged["providers"] = {p: {} for p in priority}
        return merged

    def get_routing_policy(self) -> Dict[str, Any]:
        """Return LLM routing policy including the fallback chain.

        Prefers the unified ``system/llm`` config; falls back to the legacy
        ``llm_providers`` authority file.
        """
        try:
            from core.system.config.tiered_loader import get_config

            unified = get_config("system/llm")
            routing = unified.get("routing", {})
            if isinstance(routing, dict) and routing.get("policy"):
                policy = dict(routing.get("policy", {}))
                if "fallback_chain" not in policy and routing.get("fallback_chain") is not None:
                    policy["fallback_chain"] = routing.get("fallback_chain")
                return policy
        except Exception:
            logger.warning(
                "get_routing_policy: unified system/llm read failed, falling back", exc_info=True
            )
        providers_cfg = self.get_authority("llm_providers", {})
        policy = (
            dict(providers_cfg.get("routing_policy", {})) if isinstance(providers_cfg, dict) else {}
        )
        if "fallback_chain" not in policy:
            fc = providers_cfg.get("fallback_chain") if isinstance(providers_cfg, dict) else None
            if fc is not None:
                policy["fallback_chain"] = fc
        return policy

    def get_complexity_thresholds(self) -> Dict[str, Any]:
        """Return complexity thresholds with guaranteed low/high keys."""
        thresholds = (
            self.get_authority("angela_core", {}).get("complexity", {}).get("thresholds", {})
        )
        if isinstance(thresholds, dict) and "low" in thresholds and "high" in thresholds:
            return dict(thresholds)
        return {"low": 20, "high": 100}

    def get_tickle_config(self) -> Dict[str, Any]:
        """Return tickle reflex config with guaranteed intensity thresholds."""
        tc = self.get_authority("tickle_config", {})
        if isinstance(tc, dict) and tc.get("intensity_thresholds"):
            return tc
        return {
            "intensity_thresholds": {
                "light": 0.25,
                "medium": 0.55,
                "intense": 0.60,
                "sustained_seconds": 5.0,
            }
        }

    # ------------------------------------------------------------------ #
    # Anchor context (natural-language state injection)
    # ------------------------------------------------------------------ #
    def _interpret_axis(self, axis_data: Dict[str, Any], axis_rules: Dict[str, Any]) -> str:
        """Interpret one axis's values into natural language via its rules."""
        if not axis_data or not axis_rules:
            return ""
        values = axis_data.get("values", {})
        interpretation = axis_rules.get("coordinate_interpretation", {})
        if not isinstance(values, dict) or not isinstance(interpretation, dict):
            return ""
        parts: List[str] = []
        for dim, val in values.items():
            dim_rules = interpretation.get(dim)
            if not isinstance(dim_rules, dict):
                continue
            level = _value_to_level(val)
            text = dim_rules.get(level) or dim_rules.get("neutral")
            if text:
                parts.append(str(text))
        return "，".join(parts)

    def build_anchor_context(self, state: Dict[str, Any]) -> str:
        """Build a natural-language context string from a state snapshot."""
        if not state or not isinstance(state, dict):
            return ""
        axes = state.get("axes", {})
        if not isinstance(axes, dict) or not axes:
            return ""
        rules = self.get_authority("anchor_rules", {})
        axis_names = ["alpha", "beta", "gamma", "delta", "epsilon", "theta", "zeta", "eta"]
        contexts: Dict[str, str] = {}
        for name in axis_names:
            axis_data = axes.get(name, {})
            axis_rules = rules.get(name, {}) if isinstance(rules, dict) else {}
            contexts[f"{name}_context"] = self._interpret_axis(axis_data, axis_rules)

        # Overall summary from meta signals.
        summary_bits: List[str] = []
        theta = state.get("theta", {})
        if isinstance(theta, dict) and theta.get("novelty") is not None:
            summary_bits.append(f"新奇度 {theta.get('novelty')}")
        eta = state.get("eta", {})
        if isinstance(eta, dict) and eta.get("success_rate") is not None:
            summary_bits.append(f"成功率 {eta.get('success_rate')}")
        overall_summary = "，".join(summary_bits)

        template = rules.get("prompt_context_template", "") if isinstance(rules, dict) else ""
        if template:
            try:
                return template.format(overall_summary=overall_summary, **contexts)
            except (KeyError, IndexError, ValueError):
                pass
        parts = [v for v in contexts.values() if v]
        if overall_summary:
            parts.append(overall_summary)
        return "\n".join(parts)

    # ------------------------------------------------------------------ #
    # Learned config (runtime learning closed loop)
    # ------------------------------------------------------------------ #
    def _learned_path(self, kind: str) -> Path:
        return self._angela_dir / f"learned_{kind}.yaml"

    def get_learned(self, kind: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Read a learned config file (patterns/routes/thresholds)."""
        default = {} if default is None else default
        path = self._learned_path(kind)
        if not path.is_file():
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return data if isinstance(data, dict) else default
        except Exception as e:
            logger.warning(f"Failed to read learned config {path}: {e}")
            return default

    def write_learned(self, kind: str, data: Dict[str, Any]) -> bool:
        """Persist a learned config file. Returns True on success."""
        try:
            self._angela_dir.mkdir(parents=True, exist_ok=True)
            path = self._learned_path(kind)
            with open(path, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
            return True
        except Exception as e:
            logger.warning(f"Failed to write learned config {kind}: {e}")
            return False

    def learn(self, kind: str, data: Dict[str, Any]) -> bool:
        """Record a runtime learning event.

        Supported kinds:
          - ``intent_pattern`` : {intent, keywords} (blocked for authority intents)
          - ``route_success``  : {provider, intent, latency_ms?}
          - ``route_fail``     : {provider, intent, error?}
        Returns True when the event was persisted.
        """
        if not isinstance(data, dict):
            return False

        if kind == "intent_pattern":
            intent = data.get("intent")
            if not intent:
                return False
            # Authority intents cannot be overwritten by learned patterns.
            if intent in self.get_intents():
                return False
            learned = self.get_learned("patterns", {})
            patterns = learned.setdefault("intent_patterns", {})
            patterns[intent] = {"keywords": list(data.get("keywords", []))}
            return self.write_learned("patterns", learned)

        if kind in ("route_success", "route_fail"):
            learned = self.get_learned("routes", {})
            bucket = "successful_routes" if kind == "route_success" else "failed_routes"
            routes = learned.setdefault(bucket, {})
            key = f"{data.get('provider', '')}:{data.get('intent', '')}"
            entry = routes.setdefault(key, {"count": 0})
            entry["count"] = int(entry.get("count", 0)) + 1
            if "latency_ms" in data:
                entry["last_latency_ms"] = data["latency_ms"]
            if "error" in data:
                entry["last_error"] = data["error"]
            return self.write_learned("routes", learned)

        return False

    def get_learned_stats(self) -> Dict[str, Any]:
        """Return counts of learned vs authority config entries."""
        patterns = self.get_learned("patterns", {})
        routes = self.get_learned("routes", {})
        thresholds = self.get_learned("thresholds", {})
        authority_intents = self.get_intents()
        authority_complexity = self.get_authority("angela_core", {}).get("complexity", {})
        return {
            "patterns": {
                "learned": len(patterns.get("intent_patterns", {})),
                "authority": len(authority_intents),
            },
            "thresholds": {
                "learned": len(thresholds),
                "authority": len(authority_complexity),
            },
            "routes": {
                "learned": (
                    len(routes.get("successful_routes", {})) + len(routes.get("failed_routes", {}))
                ),
                "successful": len(routes.get("successful_routes", {})),
                "failed": len(routes.get("failed_routes", {})),
            },
        }

    # ------------------------------------------------------------------ #
    # Hot reload
    # ------------------------------------------------------------------ #
    def reload_if_changed(self) -> bool:
        """Reload config files if any has changed on disk. Returns True if reloaded."""
        changed = False
        for stem, path in self._file_paths.items():
            try:
                mtime = path.stat().st_mtime
            except OSError as e:
                logger.debug("Config file stat failed: %s (%s)", path, e)
                continue
            if self._mtimes.get(stem) != mtime:
                changed = True
                break
        if changed:
            self._load_all()
        return changed

    def watch(self) -> bool:
        """Poll for config changes once (alias of reload_if_changed)."""
        return self.reload_if_changed()


_global_config: Optional[AngelaConfig] = None


def get_angela_config() -> AngelaConfig:
    """Get or create the global AngelaConfig singleton."""
    global _global_config
    if _global_config is None:
        _global_config = AngelaConfig()
    return _global_config
