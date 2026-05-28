#!/usr/bin/env python3
"""
Angela AI - Configuration Loader
配置加载器

安全地加载和访问应用配置，提供类型安全的配置访问。
支持 YAML 多文件读取、热重载、Authority + Learned 双层配置合并。
"""

import os
import json
import copy
import yaml
import logging
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar, Generic, Union
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# ── S1 擴展：Angela 配置管理器 ─────────────────────────────────────────────

class AngelaConfigManager:
    """
    Angela 專用配置管理器（v6.3）
    支援：YAML 多文件讀取、雙層配置合併（Authority + Learned）、熱重載
    """

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True

        self._base_dir = Path(__file__).parent.parent / "config"
        self._angela_dir = self._base_dir / "angela"

        self._authority: Dict[str, Any] = {}
        self._learned: Dict[str, Dict[str, Any]] = {}
        self._merged: Dict[str, Any] = {}

        self._authority_files = [
            "angela_core.yaml",
            "llm_providers.yaml",
            "file_ops.yaml",
            "anchor_rules.yaml",
            "tickle_config.yaml",
        ]
        self._learned_files = [
            "learned_patterns.yaml",
            "learned_thresholds.yaml",
            "learned_routes.yaml",
        ]

        self._watch_lock = threading.Lock()
        self._watchers: Dict[str, float] = {}

        self._load_all()

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """載入單個 YAML 檔"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return data if data else {}
        except FileNotFoundError:
            logger.debug(f"YAML not found: {path}")
            return {}
        except yaml.YAMLError as e:
            logger.warning(f"YAML parse error {path}: {e}", exc_info=True)
            return {}

    def _load_all(self) -> None:
        """載入所有配置（Authority + Learned）"""
        self._authority = {}
        for fname in self._authority_files:
            path = self._base_dir / fname
            data = self._load_yaml(path)
            self._authority[fname.replace(".yaml", "")] = data

        self._learned = {}
        for fname in self._learned_files:
            path = self._angela_dir / fname
            data = self._load_yaml(path)
            key = fname.replace(".yaml", "").replace("learned_", "")
            self._learned[key] = data

        self._merged = self.merge_config(self._authority, self._learned)
        self._update_watchers()

    def merge_config(
        self, base: Dict[str, Any], learned: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        雙層配置合併：Authority + Learned
        規則：Learned 疊加在 Authority 上；Learned 祇能新增 key，不可覆蓋 Authority 的 key
        """
        result = copy.deepcopy(base)
        for key, value in learned.items():
            if key not in result:
                result[key] = value
            elif isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_dict(result[key], value)
        return result

    def _merge_dict(self, base: Dict, learned: Dict) -> Dict:
        """遞歸合併字典，Learned 祇能新增 key，不可覆蓋 base 的 key"""
        result = copy.deepcopy(base)
        for k, v in learned.items():
            if k not in result:
                result[k] = v
            elif isinstance(result[k], dict) and isinstance(v, dict):
                result[k] = self._merge_dict(result[k], v)
        return result

    def get_learned(self, learned_type: str, default: Any = None) -> Any:
        """取得 Learned 配置（純 Learned，未合併）"""
        fname_map = {
            "patterns": "learned_patterns.yaml",
            "thresholds": "learned_thresholds.yaml",
            "routes": "learned_routes.yaml",
        }
        fname = fname_map.get(learned_type)
        if not fname:
            return default
        key = fname.replace(".yaml", "").replace("learned_", "")
        return self._learned.get(key, default if default is not None else {})

    def get_authority(self, section: str, default: Any = None) -> Any:
        """取得 Authority 配置（原始，未合併）"""
        return self._authority.get(section, default)

    def get_merged(self, section: str, key: Optional[str] = None, default: Any = None) -> Any:
        """取得合併後配置（Authority + Learned）"""
        section_data = self._merged.get(section, default if default is not None else {})
        if key is None:
            return section_data
        return section_data.get(key, default) if isinstance(section_data, dict) else default

    def get_intents(self) -> Dict[str, Dict]:
        """取得意圖配置"""
        core = self._authority.get("angela_core", {})
        return core.get("intents", {})

    def get_intent_keywords(self, intent: str) -> list:
        """取得某意圖的關鍵字列表（Authority + Learned 回退）"""
        intents = self.get_intents()
        kw = intents.get(intent, {}).get("keywords", [])
        if not kw:
            kw = self.get_learned_intent_keywords(intent)
        return kw

    def get_complexity_thresholds(self) -> Dict:
        """取得複雜度閾值"""
        core = self._authority.get("angela_core", {})
        return core.get("complexity", {}).get("thresholds", {})

    def get_llm_config(self) -> Dict:
        """取得 LLM 配置"""
        return self._authority.get("llm_providers", {})

    def get_routing_policy(self) -> Dict:
        """取得路由策略"""
        llm = self._authority.get("llm_providers", {})
        return llm.get("routing_policy", {})

    def get_file_ops_config(self) -> Dict:
        """取得檔案操作配置"""
        return self._authority.get("file_ops", {})

    def get_anchor_rules(self) -> Dict:
        """取得軸狀態解讀規則"""
        return self._authority.get("anchor_rules", {})

    def get_google_drive_config(self) -> Dict:
        """取得 Google Drive 配置（含 sub_operations）"""
        intents = self.get_intents()
        return intents.get("google_drive", {})

    def get_drive_sub_operation(self, op: str) -> Optional[Dict]:
        """取得 Google Drive 子操作配置"""
        drive = self.get_google_drive_config()
        return drive.get("sub_operations", {}).get(op)

    def get_drive_all_operations(self) -> Dict:
        """取得所有 Google Drive 子操作配置"""
        drive = self.get_google_drive_config()
        return drive.get("sub_operations", {})

    def get_google_drive_keywords(self, op: str, key: str = "keywords") -> List:
        """取得 Google Drive 子操作的特定鍵值"""
        sub_op = self.get_drive_sub_operation(op)
        if not sub_op:
            return []
        return sub_op.get(key, [])

    def get_tickle_config(self) -> Dict:
        """取得搔癢反射配置"""
        return self._authority.get("tickle_config", {})

    def get_body_part_tickle(self, body_part: str) -> Optional[Dict]:
        """取得特定部位的搔癢配置"""
        tickle = self.get_tickle_config()
        return tickle.get("body_parts", {}).get(body_part)

    def get_intensity_threshold(self, level: str) -> float:
        """取得強度閾值（light/medium/intense）"""
        tickle = self.get_tickle_config()
        thresholds = tickle.get("intensity_thresholds", {})
        return thresholds.get(level, 0.0)

    def get_segment_timeout(self) -> float:
        """取得段落下載超時（秒）"""
        core = self._authority.get("angela_core", {})
        return core.get("document_builder", {}).get("segment_timeout_seconds", 15.0)

    def write_learned(self, learned_type: str, data: Dict) -> bool:
        """
        寫入 Learned 配置（Angela 自我學習結果）
        需校驗：祇能新增 key，不可覆蓋 Authority
        """
        fname_map = {
            "patterns": "learned_patterns.yaml",
            "thresholds": "learned_thresholds.yaml",
            "routes": "learned_routes.yaml",
        }
        fname = fname_map.get(learned_type)
        if not fname:
            return False

        path = self._angela_dir / fname

        if "metadata" not in data:
            data["metadata"] = {}
        from datetime import datetime, timezone

        data["metadata"]["updated"] = datetime.now(timezone.utc).isoformat()

        try:
            with open(path, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False)
            self._load_all()
            return True
        except Exception as e:
            logger.error(f"Failed to write learned config {fname}: {e}", exc_info=True)
            return False

    def _update_watchers(self) -> None:
        """更新監控時間戳"""
        for fname in self._authority_files:
            path = self._base_dir / fname
            self._watchers[fname] = os.path.getmtime(str(path)) if path.exists() else 0.0
        for fname in self._learned_files:
            path = self._angela_dir / fname
            self._watchers[fname] = os.path.getmtime(str(path)) if path.exists() else 0.0

    def reload_if_changed(self) -> bool:
        """熱重載：檢查配置檔是否變更，如有則重新載入"""
        changed = False
        for fname, last_mtime in list(self._watchers.items()):
            if fname in self._authority_files:
                path = self._base_dir / fname
            elif fname in self._learned_files:
                path = self._angela_dir / fname
            else:
                continue
            if path.exists():
                current_mtime = os.path.getmtime(str(path))
                if current_mtime > last_mtime:
                    changed = True
                    break
        if changed:
            logger.info("[AngelaConfigManager] Config changed, reloading...")
            self._load_all()
        return changed

    def watch(self) -> bool:
        """便捷熱重載方法（每次 call 檢查一次）"""
        return self.reload_if_changed()

    def learn(self, event_type: str, data: Dict[str, Any]) -> bool:
        """
        學習閉環入口 — 根據事件類型更新對應的 Learned 配置。

        事件類型：
        - "intent_pattern": 意圖模式學習（新增已識別意圖到 patterns）
        - "threshold_adjust": 閾值調整（根據準確率調整複雜度閾值）
        - "route_success": 路由成功（記錄成功的 LLM 路由決策）
        - "route_fail": 路由失敗（記錄失敗的 LLM 路由決策）

        校驗：Learned 祇能新增 key，不能覆蓋 Authority 已有的值。
        """
        handler_map = {
            "intent_pattern": self._learn_intent_pattern,
            "threshold_adjust": self._learn_threshold_adjust,
            "route_success": self._learn_route_success,
            "route_fail": self._learn_route_fail,
        }
        handler = handler_map.get(event_type)
        if not handler:
            logger.warning(f"[Learning] Unknown event type: {event_type}", exc_info=True)
            return False
        try:
            return handler(data)
        except Exception as e:
            logger.error(f"[Learning] Handler {event_type} failed: {e}", exc_info=True)
            return False

    def _learn_intent_pattern(self, data: Dict[str, Any]) -> bool:
        intent_name = data.get("intent", "unknown")
        keywords = data.get("keywords", [])
        if not intent_name or intent_name == "unknown":
            return False

        learned = self.get_learned("patterns", {})
        authority = self.get_authority("angela_core", {}).get("intents", {})

        patterns = learned.get("intent_patterns", {})
        existing = patterns.get(intent_name, {})
        existing_keywords = set(existing.get("keywords", []))
        for kw in keywords:
            existing_keywords.add(kw)
        patterns[intent_name] = {
            "keywords": sorted(list(existing_keywords)),
            "count": existing.get("count", 0) + 1,
            "last_seen": datetime.now(timezone.utc).isoformat(),
        }
        learned["intent_patterns"] = patterns
        return self.write_learned("patterns", learned)

    def _learn_threshold_adjust(self, data: Dict[str, Any]) -> bool:
        metric = data.get("metric", "")
        value = data.get("value", 0.5)
        learned = self.get_learned("thresholds", {})
        adjustments = learned.get("threshold_adjustments", {})
        adjustments[metric] = {
            "value": value,
            "updated": datetime.now(timezone.utc).isoformat(),
            "count": adjustments.get(metric, {}).get("count", 0) + 1,
        }
        learned["threshold_adjustments"] = adjustments
        return self.write_learned("thresholds", learned)

    def _learn_route_success(self, data: Dict[str, Any]) -> bool:
        provider = data.get("provider", "")
        intent = data.get("intent", "general")
        latency_ms = data.get("latency_ms", 0)
        learned = self.get_learned("routes", {})
        routes = learned.get("successful_routes", {})
        key = f"{intent}:{provider}"
        entry = routes.get(key, {"count": 0, "total_latency": 0.0, "intents": []})
        entry["count"] += 1
        entry["total_latency"] += latency_ms
        if intent not in entry["intents"]:
            entry["intents"].append(intent)
        entry["avg_latency"] = entry["total_latency"] / entry["count"]
        routes[key] = entry
        learned["successful_routes"] = routes
        return self.write_learned("routes", learned)

    def _learn_route_fail(self, data: Dict[str, Any]) -> bool:
        provider = data.get("provider", "")
        intent = data.get("intent", "general")
        error = data.get("error", "unknown")
        learned = self.get_learned("routes", {})
        routes = learned.get("failed_routes", {})
        key = f"{intent}:{provider}"
        entry = routes.get(key, {"count": 0, "errors": []})
        entry["count"] += 1
        if error not in entry["errors"]:
            entry["errors"].append(error[:100])
        routes[key] = entry
        learned["failed_routes"] = routes
        return self.write_learned("routes", learned)

    def get_learned_stats(self) -> Dict[str, Any]:
        """獲取學習統計摘要"""
        stats = {
            "patterns": {"learned": 0, "authority": 0},
            "thresholds": {"adjustments": 0},
            "routes": {"success": 0, "fail": 0},
        }
        try:
            patterns = self.get_learned("patterns", {})
            patterns_key = patterns.get("intent_patterns", {})
            stats["patterns"]["learned"] = len(patterns_key)
            authority_intents = self.get_authority("angela_core", {}).get("intents", {})
            stats["patterns"]["authority"] = len(authority_intents)
            thresholds = self.get_learned("thresholds", {})
            stats["thresholds"]["adjustments"] = len(thresholds.get("threshold_adjustments", {}))
            routes = self.get_learned("routes", {})
            stats["routes"]["success"] = len(routes.get("successful_routes", {}))
            stats["routes"]["fail"] = len(routes.get("failed_routes", {}))
        except Exception as e:
            logger.warning(f"[Learning] Stats collection failed: {e}", exc_info=True)
        return stats

    def _check_and_auto_optimize(self) -> bool:
        """檢查是否需要自動優化（每 100 次學習事件觸發）"""
        stats = self.get_learned_stats()
        total = sum([
            stats["patterns"]["learned"],
            stats["thresholds"]["adjustments"],
            stats["routes"]["success"],
            stats["routes"]["fail"],
        ])
        if total > 0 and total % 100 == 0:
            logger.info(f"[Learning] Auto-optimization triggered at {total} events")
            return True
        return False

    def get_learned_intent_keywords(self, intent: str) -> List[str]:
        """獲取 Learned 層意圖關鍵字（配置驅動回退）"""
        patterns = self.get_learned("patterns", {}).get("intent_patterns", {})
        entry = patterns.get(intent, {})
        return entry.get("keywords", [])

    def get_learned_thresholds(self, metric: str) -> Optional[Dict[str, Any]]:
        """獲取 Learned 層閾值調整"""
        adjustments = self.get_learned("thresholds", {}).get("threshold_adjustments", {})
        return adjustments.get(metric)

    def get_best_route(self, intent: str) -> Optional[str]:
        """根據學習歷史返回最佳路由（延遲最低的成功路由，排除已知失敗）"""
        routes = self.get_learned("routes", {})
        successful = routes.get("successful_routes", {})
        failed = routes.get("failed_routes", {})
        failed_providers = set()
        for key in failed:
            parts = key.split(":", 1)
            if len(parts) == 2 and parts[0] == intent:
                failed_providers.add(parts[1])
        best_key, best_latency = None, float("inf")
        for key, entry in successful.items():
            if key.startswith(f"{intent}:"):
                provider = key.split(":", 1)[1]
                if provider in failed_providers:
                    continue
                avg = entry.get("avg_latency", float("inf"))
                if avg < best_latency:
                    best_key = key
                    best_latency = avg
        return best_key.split(":")[1] if best_key else None

    def build_anchor_context(self, state_for_llm: Dict[str, Any]) -> str:
        """
        使用 anchor_rules.yaml 的 prompt_context_template，
        將 StateMatrix.export_for_llm() 的原始座標翻譯為自然語境，
        解決 P2.2 退化（座標計算了但 LLM 不理解含義）。
        """
        try:
            rules = self._authority.get("anchor_rules", {})
            template = rules.get("prompt_context_template", "{all_axes}")
            if "{all_axes}" in template or template == "{all_axes}":
                return self._build_axis_context(rules, state_for_llm)

            axes = state_for_llm.get("axes", {})
            context_map = {
                "alpha_context": self._interpret_axis(axes.get("alpha", {}), rules.get("alpha", {})),
                "beta_context": self._interpret_axis(axes.get("beta", {}), rules.get("beta", {})),
                "gamma_context": self._interpret_axis(axes.get("gamma", {}), rules.get("gamma", {})),
                "delta_context": self._interpret_axis(axes.get("delta", {}), rules.get("delta", {})),
                "epsilon_context": self._interpret_axis(axes.get("epsilon", {}), rules.get("epsilon", {})),
                "theta_context": self._interpret_axis(axes.get("theta", {}), rules.get("theta", {})),
                "zeta_context": self._interpret_axis(axes.get("zeta", {}), rules.get("zeta", {})),
                "eta_context": self._interpret_axis(axes.get("eta", {}), rules.get("eta", {})),
                "overall_summary": self._build_summary(axes),
            }
            return template.format(**context_map)
        except Exception as e:
            logger.warning(f"[AnchorContext] Failed to build context: {e}", exc_info=True)
            return ""

    def _interpret_axis(self, axis_data: Dict[str, Any], axis_rules: Dict[str, Any]) -> str:
        """將單軸數值翻譯為自然語境"""
        if not axis_data or not axis_rules:
            return "狀態正常"
        coords = axis_data.get("values", {})
        coord_interp = axis_rules.get("coordinate_interpretation", {})

        interpretations = []
        for coord_name, coord_rules in coord_interp.items():
            value = coords.get(coord_name, 0.5)
            if value >= 0.7:
                label = coord_rules.get("high_positive", coord_rules.get("mid_positive", ""))
            elif value >= 0.5:
                label = coord_rules.get("mid_positive", coord_rules.get("neutral", ""))
            elif value >= 0.3:
                label = coord_rules.get("mid_negative", coord_rules.get("neutral", ""))
            else:
                label = coord_rules.get("high_negative", coord_rules.get("mid_negative", ""))
            if label:
                interpretations.append(label)
        return interpretations[0] if interpretations else "狀態正常"

    def _build_axis_context(self, rules: Dict[str, Any], state_for_llm: Dict[str, Any]) -> str:
        """建構軸狀態自然語境（優先讀取 state_to_llm 配置）"""
        axes = state_for_llm.get("axes", {})
        state_desc = self._authority.get("angela_core", {}).get("state_to_llm", {})
        axis_dim_map = {"alpha": ("energy", "alpha_energy"), "beta": ("curiosity", "beta_curiosity"),
                        "gamma": ("happiness", "gamma_valence"), "delta": ("intimacy", "delta_intimacy")}
        lines = []
        for axis_name in ("alpha", "beta", "gamma", "delta", "epsilon", "theta", "zeta", "eta"):
            axis_data = axes.get(axis_name, {})
            mapping = axis_dim_map.get(axis_name)
            interp = ""
            if mapping and mapping[1] in state_desc:
                val = axis_data.get("values", {}).get(mapping[0], 0.5)
                levels = state_desc[mapping[1]]
                if val >= 0.7:
                    interp = levels.get("high", "")
                elif val >= 0.4:
                    interp = levels.get("medium", "")
                else:
                    interp = levels.get("low", "")
            if not interp:
                interp = self._interpret_axis(axis_data, rules.get(axis_name, {}))
            lines.append(f"{axis_name}({interp})")
        theta_data = state_for_llm.get("theta", {})
        eta_data = state_for_llm.get("eta", {})
        if theta_data:
            novelty = theta_data.get("novelty", 0)
            lines.append(f"θ 新穎={novelty:.1f}")
        if eta_data:
            lines.append(f"η 成功率={eta_data.get('success_rate', 0):.0%}")
        return " | ".join(lines)

    def _build_summary(self, axes: Dict[str, Any]) -> str:
        """建構總結語境"""
        try:
            gamma_vals = axes.get("gamma", {}).get("values", {})
            beta_vals = axes.get("beta", {}).get("values", {})
            alpha_vals = axes.get("alpha", {}).get("values", {})
            happy = gamma_vals.get("happiness", 0.5)
            trust = gamma_vals.get("trust", 0.5)
            focus = beta_vals.get("focus", 0.5)
            energy = alpha_vals.get("energy", 0.5)
            if happy > 0.7 and trust > 0.7:
                return "狀態良好，信任且開心"
            elif trust < 0.3:
                return "信任度低，需要建立安全感"
            elif focus > 0.7:
                return "高度專注"
            elif energy < 0.3:
                return "能量低，需要休息"
            return "狀態平穩"
        except Exception:
            return "狀態平穩"


# ── 全域單例 ────────────────────────────────────────────────────────────────

from core.interfaces.service_registry import get_registry

_angela_config: Optional[AngelaConfigManager] = None


def get_angela_config() -> AngelaConfigManager:
    """獲取全域 Angela 配置管理器"""
    global _angela_config
    if _angela_config is None:
        _angela_config = AngelaConfigManager()
        get_registry().register("angela_config", _angela_config)
    return _angela_config


# ── 原有 Config 類（保持向後兼容）────────────────────────────────────────────

class Environment(Enum):
    """运行环境"""

    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class PerformanceMode(Enum):
    """性能模式"""

    AUTO = "auto"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"


@dataclass
class BackendConfig:
    """后端配置"""

    host: str = "127.0.0.1"
    port: int = 8000
    url: str = "http://127.0.0.1:8000"

    def get_base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


@dataclass
class SecurityConfig:
    """安全配置"""

    key_a: str = ""
    key_b: str = ""
    key_c: str = ""

    def validate(self) -> bool:
        """验证密钥配置"""
        return all(len(key) >= 32 for key in [self.key_a, self.key_b, self.key_c])


@dataclass
class DatabaseConfig:
    """数据库配置"""

    url: str = "sqlite:///./angela.db"
    pool_size: int = 10
    max_overflow: int = 20

    def get_engine_args(self) -> Dict[str, Any]:
        return {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
        }


@dataclass
class Live2DConfig:
    """Live2D 配置"""

    model_path: Optional[str] = None
    sdk_cdn: str = "https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js"

    def get_model_path(self) -> Optional[Path]:
        if self.model_path:
            return Path(self.model_path).resolve()
        return None


@dataclass
class PerformanceConfig:
    """性能配置"""

    mode: PerformanceMode = PerformanceMode.AUTO
    target_fps: int = 60
    enable_hardware_acceleration: bool = True

    def get_fps_settings(self) -> Dict[str, Any]:
        mode_settings = {
            PerformanceMode.LOW: {"target_fps": 30, "effects": "basic"},
            PerformanceMode.MEDIUM: {"target_fps": 45, "effects": "standard"},
            PerformanceMode.HIGH: {"target_fps": 60, "effects": "enhanced"},
            PerformanceMode.ULTRA: {"target_fps": 120, "effects": "all"},
        }
        return mode_settings.get(self.mode, {"target_fps": self.target_fps, "effects": "auto"})


@dataclass
class LoggingConfig:
    """日志配置"""

    level: str = "info"
    file_path: str = "./logs/angela.log"
    max_size: str = "10MB"
    backup_count: int = 5

    def get_log_level(self) -> int:
        levels = {"debug": 10, "info": 20, "warning": 30, "error": 40, "critical": 50}
        return levels.get(self.level.lower(), 20)


@dataclass
class FeatureFlags:
    """功能开关"""

    enable_voice_recognition: bool = True
    enable_tts: bool = True
    enable_websocket: bool = True
    enable_mobile_bridge: bool = True

    @classmethod
    def from_env(cls) -> "FeatureFlags":
        return cls(
            enable_voice_recognition=_get_bool("ENABLE_VOICE_RECOGNITION", True),
            enable_tts=_get_bool("ENABLE_TTS", True),
            enable_websocket=_get_bool("ENABLE_WEBSOCKET", True),
            enable_mobile_bridge=_get_bool("ENABLE_MOBILE_BRIDGE", True),
        )


@dataclass
class Config:
    """主配置类"""

    environment: Environment = Environment.DEVELOPMENT
    backend: BackendConfig = field(default_factory=BackendConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    live2d: Live2DConfig = field(default_factory=Live2DConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    features: FeatureFlags = field(default_factory=FeatureFlags)

    # 调试和开发设置
    debug_mode: bool = True
    hot_reload: bool = True
    enable_cors: bool = True

    # 测试配置
    test_mode: bool = False
    mock_external_apis: bool = False

    @classmethod
    def load(cls, env_file: Optional[Path] = None) -> "Config":
        """加载配置"""
        # 加载 .env 文件
        if env_file:
            _load_env_file(env_file)

        # 创建配置对象
        return cls(
            environment=Environment(_get_str("ANGELA_ENV", "development")),
            backend=BackendConfig(
                host=_get_str("BACKEND_HOST", "127.0.0.1"),
                port=_get_int("BACKEND_PORT", 8000),
                url=_get_str("BACKEND_URL", "http://127.0.0.1:8000"),
            ),
            security=SecurityConfig(
                key_a=_get_str("ANGELA_KEY_A", ""),
                key_b=_get_str("ANGELA_KEY_B", ""),
                key_c=_get_str("ANGELA_KEY_C", ""),
            ),
            database=DatabaseConfig(
                url=_get_str("DATABASE_URL", "sqlite:///./angela.db"),
                pool_size=_get_int("DATABASE_POOL_SIZE", 10),
                max_overflow=_get_int("DATABASE_MAX_OVERFLOW", 20),
            ),
            live2d=Live2DConfig(
                model_path=_get_str("LIVE2D_MODEL_PATH"),
                sdk_cdn=_get_str(
                    "LIVE2D_SDK_CDN",
                    "https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js",
                ),
            ),
            performance=PerformanceConfig(
                mode=PerformanceMode(_get_str("PERFORMANCE_MODE", "auto")),
                target_fps=_get_int("TARGET_FPS", 60),
                enable_hardware_acceleration=_get_bool("ENABLE_HARDWARE_ACCELERATION", True),
            ),
            logging=LoggingConfig(
                level=_get_str("LOG_LEVEL", "info"),
                file_path=_get_str("LOG_FILE", "./logs/angela.log"),
                max_size=_get_str("LOG_MAX_SIZE", "10MB"),
                backup_count=_get_int("LOG_BACKUP_COUNT", 5),
            ),
            features=FeatureFlags.from_env(),
            debug_mode=_get_bool("DEBUG_MODE", True),
            hot_reload=_get_bool("HOT_RELOAD", True),
            enable_cors=_get_bool("ENABLE_CORS", True),
            test_mode=_get_bool("TEST_MODE", False),
            mock_external_apis=_get_bool("MOCK_EXTERNAL_APIS", False),
        )

    def validate(self) -> tuple[bool, list[str]]:
        """验证配置"""
        errors = []

        # 验证环境
        if self.environment == Environment.PRODUCTION and self.debug_mode:
            errors.append("生产环境不应启用调试模式")

        # 验证安全配置
        if not self.security.validate():
            errors.append("安全密钥配置无效，密钥长度至少需要 32 字符")

        # 验证数据库
        if not self.database.url:
            errors.append("数据库 URL 不能为空")

        # 验证性能配置
        if self.performance.target_fps < 30 or self.performance.target_fps > 144:
            errors.append(f"目标帧率无效: {self.performance.target_fps}")

        return (len(errors) == 0, errors)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "environment": self.environment.value,
            "backend": {
                "host": self.backend.host,
                "port": self.backend.port,
                "url": self.backend.url,
            },
            "security": {
                "key_a": "***" if self.security.key_a else None,
                "key_b": "***" if self.security.key_b else None,
                "key_c": "***" if self.security.key_c else None,
            },
            "database": {
                "url": self.database.url,
                "pool_size": self.database.pool_size,
            },
            "performance": {
                "mode": self.performance.mode.value,
                "target_fps": self.performance.target_fps,
            },
            "logging": {
                "level": self.logging.level,
                "file_path": self.logging.file_path,
            },
            "features": {
                "enable_voice_recognition": self.features.enable_voice_recognition,
                "enable_tts": self.features.enable_tts,
                "enable_websocket": self.features.enable_websocket,
            },
        }


# 辅助函数
def _load_env_file(env_file: Path) -> None:
    """加载 .env 文件"""
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()


def _get_str(key: str, default: Optional[str] = None) -> str:
    """获取字符串配置"""
    return os.environ.get(key, default or "")


def _get_int(key: str, default: int = 0) -> int:
    """获取整数配置"""
    value = os.environ.get(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_bool(key: str, default: bool = False) -> bool:
    """获取布尔配置"""
    value = os.environ.get(key, "").lower()
    if value in ("true", "1", "yes", "on"):
        return True
    elif value in ("false", "0", "no", "off"):
        return False
    return default


# 全局配置实例
_config: Optional[Config] = None


def get_config() -> Config:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = Config.load()
    return _config


def reload_config(env_file: Optional[Path] = None) -> Config:
    """重新加载配置"""
    global _config
    _config = Config.load(env_file)
    return _config


def init_config(env_file: Optional[Path] = None) -> None:
    """初始化配置"""
    global _config
    _config = Config.load(env_file)

    # 验证配置
    valid, errors = _config.validate()
    if not valid:
        error_msg = "配置验证失败:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValueError(error_msg)


if __name__ == "__main__":
    # 测试配置加载
    config = Config.load()
    logger.info(json.dumps(config.to_dict(), indent=2, ensure_ascii=False))
