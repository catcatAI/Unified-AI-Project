"""
Game Strategy - L4 元策略層

功能：
- 長期統計收集與分析
- 探索/利用 平衡動態調整
- 風險容忍度自適應
- 策略權重持久化
- 異常模式檢測
"""

import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class StrategyWeights:
    """策略權重 (0-1 之間)"""

    exploration_weight: float = 0.5  # 探索 vs 利用
    risk_tolerance: float = 0.5  # 風險承受
    survival_priority: float = 0.7  # 生存優先級
    resource_priority: float = 0.6  # 資源收集優先級
    building_priority: float = 0.3  # 建築優先級
    combat_priority: float = 0.4  # 戰鬥優先級
    social_priority: float = 0.1  # 社交/合作優先級

    def clamp(self):
        """限制在 [0, 1]"""
        for k in self.__dataclass_fields__:
            v = getattr(self, k)
            setattr(self, k, max(0.0, min(1.0, v)))

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, float]) -> "StrategyWeights":
        return cls(
            **{
                k: float(d.get(k, v.default))  # type: ignore[arg-type]  # dataclass MISSING 哨兵窄化
                for k, v in cls.__dataclass_fields__.items()
            }
        )


@dataclass
class StrategyConfig:
    update_interval_sec: float = 60.0  # 策略更新間隔
    stats_window_min: float = 30.0  # 統計窗口
    min_exploration: float = 0.1  # 最小探索權重
    max_exploration: float = 0.9  # 最大探索權重
    min_risk: float = 0.1  # 最小風險容忍
    max_risk: float = 0.9  # 最大風險容忍
    death_penalty: float = 0.15  # 死亡懲罰幅度
    anomaly_penalty: float = 0.05  # 異常懲罰幅度
    success_bonus: float = 0.05  # 成功獎勵幅度
    persistence_path: str = "data/strategy_weights.json"


@dataclass
class SessionStats:
    """會話統計"""

    session_start: float = field(default_factory=time.time)
    duration_min: float = 0.0
    goals_completed: int = 0
    goals_failed: int = 0
    subgoals_completed: int = 0
    subgoals_failed: int = 0
    death_count: int = 0
    anomaly_count: int = 0
    stuck_count: int = 0
    resource_collected: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    distance_traveled: float = 0.0
    blocks_placed: int = 0
    blocks_dug: int = 0
    items_crafted: int = 0
    combat_wins: int = 0
    combat_losses: int = 0

    def collection_rate(self) -> Dict[str, float]:
        """資源收集率 (每分鐘)"""
        if self.duration_min <= 0:
            return {}
        return {k: v / self.duration_min for k, v in self.resource_collected.items()}


class GameStrategy:
    """
    L4 元策略控制器

    職責：
    1. 收集長期統計
    2. 根據統計動態調整權重
    3. 向 L3 提供 StrategyDirective
    4. 異常模式檢測 (死亡螺旋、資源耗盡、循環卡住)
    5. 權重持久化
    """

    def __init__(self, config: Optional[StrategyConfig] = None):
        self.config = config or StrategyConfig()
        self.weights = StrategyWeights()
        self.stats = SessionStats()
        self._last_update = time.time()
        self._history: deque = deque(maxlen=1000)  # (timestamp, event_type, data)
        self._anomaly_patterns: Dict[str, int] = defaultdict(int)
        self._load_weights()

    def _load_weights(self):
        """載入持久化權重"""
        path = Path(self.config.persistence_path)
        if path.exists():
            try:
                with open(path) as f:
                    data = json.load(f)
                self.weights = StrategyWeights.from_dict(data.get("weights", {}))
                logger.info(f"Loaded strategy weights from {path}")
            except Exception as e:
                logger.warning(f"Failed to load strategy weights: {e}")

    def _save_weights(self):
        """保存權重"""
        path = Path(self.config.persistence_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(path, "w") as f:
                json.dump(
                    {
                        "weights": self.weights.to_dict(),
                        "updated": time.time(),
                        "stats": {
                            "total_sessions": getattr(self, "_total_sessions", 0),
                            "total_deaths": getattr(self, "_total_deaths", 0),
                        },
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            logger.error(f"Failed to save strategy weights: {e}")

    def record_event(self, event_type: str, data: Dict[str, Any]):
        """記錄事件"""
        self._history.append((time.time(), event_type, data))

        # 更新統計
        if event_type == "goal_completed":
            self.stats.goals_completed += 1
        elif event_type == "goal_failed":
            self.stats.goals_failed += 1
        elif event_type == "subgoal_completed":
            self.stats.subgoals_completed += 1
        elif event_type == "subgoal_failed":
            self.stats.subgoals_failed += 1
        elif event_type == "death":
            self.stats.death_count += 1
            self._total_deaths = getattr(self, "_total_deaths", 0) + 1
            self._record_anomaly("death", data)
        elif event_type == "anomaly":
            self.stats.anomaly_count += 1
            self._record_anomaly(data.get("reason", "unknown"), data)
        elif event_type == "stuck":
            self.stats.stuck_count += 1
            self._record_anomaly("stuck", data)
        elif event_type == "resource_collected":
            for res, count in data.items():
                self.stats.resource_collected[res] += count
        elif event_type == "distance":
            self.stats.distance_traveled += data.get("delta", 0)
        elif event_type == "block_placed":
            self.stats.blocks_placed += 1
        elif event_type == "block_dug":
            self.stats.blocks_dug += 1
        elif event_type == "item_crafted":
            self.stats.items_crafted += 1
        elif event_type == "combat_win":
            self.stats.combat_wins += 1
        elif event_type == "combat_loss":
            self.stats.combat_losses += 1

    def _record_anomaly(self, reason: str, data: Dict):
        """記錄異常模式"""
        key = f"{reason}:{data.get('context', '')}"
        self._anomaly_patterns[key] += 1

        # 檢測模式
        if self._anomaly_patterns[key] >= 3:
            logger.warning(
                f"Repeated anomaly pattern detected: {key} (count: {self._anomaly_patterns[key]})"
            )

    def update(self, state: Any = None) -> bool:
        """定期更新策略 (每分鐘調用)"""
        now = time.time()
        if now - self._last_update < self.config.update_interval_sec:
            return False

        self._last_update = now
        self.stats.duration_min = (now - self.stats.session_start) / 60.0

        if state and hasattr(state, "proprioception") and state.proprioception:
            prop = state.proprioception
            # 記錄當前狀態快照
            pass

        self._adjust_weights()
        self._save_weights()

        return True

    def _adjust_weights(self):
        """根據統計調整權重"""
        # 計算關鍵指標
        death_rate = self.stats.death_count / max(
            self.stats.duration_min / 30.0, 1.0
        )  # 每30分鐘死亡率
        anomaly_rate = self.stats.anomaly_count / max(self.stats.duration_min / 10.0, 1.0)
        stuck_rate = self.stats.stuck_count / max(self.stats.duration_min / 10.0, 1.0)
        goal_success_rate = self.stats.goals_completed / max(
            self.stats.goals_completed + self.stats.goals_failed, 1
        )
        resource_rate = sum(self.stats.collection_rate().values())

        adjustments = []

        # 1. 死亡率過高 -> 降低風險、增加生存優先級
        if death_rate > 0.5:  # 超過 0.5 次/30分鐘
            self.weights.risk_tolerance = max(
                self.config.min_risk, self.weights.risk_tolerance - self.config.death_penalty
            )
            self.weights.survival_priority = min(
                1.0, self.weights.survival_priority + self.config.death_penalty
            )
            self.weights.exploration_weight = max(
                self.config.min_exploration,
                self.weights.exploration_weight - self.config.death_penalty * 0.5,
            )
            adjustments.append(f"death_rate={death_rate:.2f} -> lower risk")

        # 2. 異常/卡住頻繁 -> 降低探索、增加保守
        if anomaly_rate > 1.0 or stuck_rate > 1.0:
            self.weights.exploration_weight = max(
                self.config.min_exploration,
                self.weights.exploration_weight - self.config.anomaly_penalty,
            )
            self.weights.risk_tolerance = max(
                self.config.min_risk, self.weights.risk_tolerance - self.config.anomaly_penalty
            )
            adjustments.append(
                f"anomaly_rate={anomaly_rate:.2f}, stuck_rate={stuck_rate:.2f} -> more conservative"
            )

        # 3. 目標成功率低 -> 降低風險
        if goal_success_rate < 0.5 and (self.stats.goals_completed + self.stats.goals_failed) > 5:
            self.weights.risk_tolerance = max(
                self.config.min_risk, self.weights.risk_tolerance - 0.1
            )
            adjustments.append(f"goal_success_rate={goal_success_rate:.2f} -> lower risk")

        # 4. 資源收集率低 -> 增加探索
        if resource_rate < 5.0 and self.stats.duration_min > 5:  # 少於 5 個/分鐘
            self.weights.exploration_weight = min(
                self.config.max_exploration,
                self.weights.exploration_weight + self.config.success_bonus,
            )
            self.weights.resource_priority = min(1.0, self.weights.resource_priority + 0.05)
            adjustments.append(f"resource_rate={resource_rate:.1f}/min -> more exploration")

        # 5. 成功獎勵 (目標完成)
        if self.stats.goals_completed > 0 and goal_success_rate > 0.8:
            self.weights.exploration_weight = min(
                self.config.max_exploration,
                self.weights.exploration_weight + self.config.success_bonus,
            )
            adjustments.append("high success rate -> more exploration")

        # 限制範圍
        self.weights.clamp()

        if adjustments:
            logger.info(
                f"Strategy adjusted: {'; '.join(adjustments)} | weights: {self.weights.to_dict()}"
            )

    def get_directive(self) -> Dict[str, Any]:
        """獲取策略指令 (給 L3)"""
        return {
            "exploration_weight": self.weights.exploration_weight,
            "risk_tolerance": self.weights.risk_tolerance,
            "priority_goals": self._compute_priority_goals(),
            "forbidden_actions": self._compute_forbidden_actions(),
        }

    def _compute_priority_goals(self) -> List[str]:
        """根據權重計算優先目標"""
        priorities = [
            ("survival", self.weights.survival_priority),
            ("resource_securing", self.weights.resource_priority),
            ("base_building", self.weights.building_priority),
            ("combat_readiness", self.weights.combat_priority),
            ("exploration", self.weights.exploration_weight),
        ]
        priorities.sort(key=lambda x: -x[1])
        return [p[0] for p in priorities if p[1] > 0.3]

    def _compute_forbidden_actions(self) -> List[str]:
        """計算禁止動作"""
        forbidden = []
        if self.weights.risk_tolerance < 0.3:
            forbidden.extend(
                ["deep_mining", "cave_exploration", "night_surface_travel", "boss_fight"]
            )
        if self.weights.survival_priority > 0.8:
            forbidden.extend(["unnecessary_combat", "risky_parkour"])
        return forbidden

    def get_stats_summary(self) -> Dict[str, Any]:
        """獲取統計摘要"""
        return {
            "session_duration_min": self.stats.duration_min,
            "goals_completed": self.stats.goals_completed,
            "goals_failed": self.stats.goals_failed,
            "death_count": self.stats.death_count,
            "anomaly_count": self.stats.anomaly_count,
            "stuck_count": self.stats.stuck_count,
            "resource_collection_rate": self.stats.collection_rate(),
            "weights": self.weights.to_dict(),
            "priority_goals": self._compute_priority_goals(),
            "anomaly_patterns": dict(self._anomaly_patterns),
        }

    def on_session_end(self):
        """會話結束"""
        self._save_weights()
        self._total_sessions = getattr(self, "_total_sessions", 0) + 1
        logger.info(f"Session ended: {self.get_stats_summary()}")


class StrategyDirectiveBuilder:
    """構建給 L3 的 StrategyDirective"""

    @staticmethod
    def build(strategy: GameStrategy) -> Dict[str, Any]:
        directive = strategy.get_directive()
        return {
            "exploration_weight": directive["exploration_weight"],
            "risk_tolerance": directive["risk_tolerance"],
            "priority_goals": directive["priority_goals"],
            "forbidden_actions": directive["forbidden_actions"],
        }

    @staticmethod
    def merge(base: Dict, override: Dict) -> Dict:
        """合併策略指令 (L4 + LLM)"""
        merged = base.copy()
        for k, v in override.items():
            if k in ["exploration_weight", "risk_tolerance"]:
                merged[k] = max(0.0, min(1.0, (merged.get(k, 0.5) + v) / 2))
            elif k in ["priority_goals", "forbidden_actions"]:
                merged[k] = list(set(merged.get(k, []) + v))
        return merged
