"""
Skill Selector - L1 技能基元選擇與參數化

根據 L0 latent + L2 context 選擇技能並輸出參數化動作
"""

import logging
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple
import numpy as np

from .game_structs import (
    SkillID,
    SkillSpec,
    SkillParams,
    SkillContext,
    SkillTrigger,
    SkillResult,
    GAME_SKILLS,
    check_preconditions,
    get_available_skills,
    GameState,
    Proprioception,
)

logger = logging.getLogger(__name__)


@dataclass
class SelectorConfig:
    skill_embedding_dim: int = 32
    latent_dim: int = 128
    hidden_dim: int = 128
    temperature: float = 1.0
    min_confidence: float = 0.3
    # Repeat penalty window. The poller executes at ~0.5Hz, so switching
    # skills faster than ~3s is pure flicker (observed: place/dig/move
    # churn with no commitment). 30 ticks ≈ 3s at the 10Hz agent loop.
    skill_cooldown_ticks: int = 30


@dataclass
class SkillScore:
    skill_id: SkillID
    score: float
    confidence: float
    params: Dict[str, Any]


class SkillSelector:
    """
    L1 技能選擇器

    輸入：
    - L0 latent (128) + proprioception (32) + intent (32) + L2 context
    輸出：
    - SkillParams (給 L0) 或 SkillTrigger (給 L2)

    核心邏輯：
    1. 過濾滿足前置條件的技能
    2. 計算每個技能的相關性分數
    3. 加入優先級、冷卻、連續性偏好
    4. 輸出最佳技能 + 具體參數
    """

    def __init__(self, config: Optional[SelectorConfig] = None):
        self.config = config or SelectorConfig()
        self._skill_embeddings: Dict[SkillID, np.ndarray] = {}
        self._skill_priorities: Dict[SkillID, float] = {}
        self._last_used: Dict[SkillID, int] = {}
        self._current_tick = 0
        self._prev_skill: Optional[SkillID] = None
        self._init_embeddings()

    def _init_embeddings(self):
        """初始化技能嵌入向量 (可學習，這裡用固定初始化)"""
        np.random.seed(123)
        for skill_id in SkillID:
            self._skill_embeddings[skill_id] = np.random.randn(
                self.config.skill_embedding_dim
            ).astype(np.float32)
            # 基礎優先級
            base_priority = {
                SkillID.EAT: 1.0,
                SkillID.COMBAT: 0.9,
                SkillID.MOVE: 0.8,
                SkillID.NAVIGATE: 0.7,
                SkillID.DIG: 0.6,
                SkillID.PLACE: 0.5,
                SkillID.CRAFT: 0.5,
                SkillID.BUILD: 0.4,
                SkillID.LOOK: 0.3,
            }
            self._skill_priorities[skill_id] = base_priority.get(skill_id, 0.5)

    def tick(self):
        """每幀調用，更新計時器"""
        self._current_tick += 1

    def select(
        self, latent: np.ndarray, state: GameState, context: Optional[SkillContext] = None
    ) -> SkillParams:
        """
        選擇技能並輸出參數

        Args:
            latent: L0 輸出的 latent (128,)
            state: 完整遊戲狀態
            context: L2 下發的技能上下文 (可選，若有則強制使用)

        Returns:
            SkillParams: 給 L0 的動作參數
        """
        start = time.perf_counter()

        # 1. 若 L2 指定了技能，直接參數化
        if context and context.active_skill:
            return self._parameterize_skill(context.active_skill, context.params, state, latent)

        # 2. 取得可用技能
        available = get_available_skills(state)
        if not available:
            return self._fallback_idle(state)

        # 3. 為每個技能打分
        scores = []
        for skill_id in available:
            score = self._score_skill(skill_id, latent, state)
            if score.confidence >= self.config.min_confidence:
                scores.append(score)

        if not scores:
            return self._fallback_idle(state)

        # 4. 應用 Softmax + 溫度
        scores.sort(key=lambda s: s.score, reverse=True)

        # 取 top-k 做加權隨機 (探索) 或直接取最佳 (利用)
        if np.random.random() < 0.1:  # 10% 探索
            chosen = np.random.choice(scores[:3], p=self._softmax([s.score for s in scores[:3]]))
        else:
            chosen = scores[0]

        # 5. 記錄使用
        self._last_used[chosen.skill_id] = self._current_tick
        self._prev_skill = chosen.skill_id

        # 6. 參數化
        params = self._parameterize_skill(chosen.skill_id, chosen.params, state, latent)
        params.priority = chosen.confidence

        elapsed = (time.perf_counter() - start) * 1000
        if elapsed > 2:
            logger.debug(f"SkillSelector slow: {elapsed:.1f}ms")

        return params

    def _score_skill(self, skill_id: SkillID, latent: np.ndarray, state: GameState) -> SkillScore:
        """計算技能分數"""
        # 基礎嵌入相似度
        skill_emb = self._skill_embeddings[skill_id]
        sim = np.dot(latent[: self.config.skill_embedding_dim], skill_emb) / (
            np.linalg.norm(latent[: self.config.skill_embedding_dim]) * np.linalg.norm(skill_emb)
            + 1e-8
        )

        # 基礎優先級
        priority = self._skill_priorities[skill_id]

        # 冷卻懲罰
        cooldown_penalty = 0.0
        if skill_id in self._last_used:
            ticks_since = self._current_tick - self._last_used[skill_id]
            if ticks_since < self.config.skill_cooldown_ticks:
                cooldown_penalty = 0.5 * (1 - ticks_since / self.config.skill_cooldown_ticks)

        # 連續性獎勵 (傾向繼續同一技能)
        continuity_bonus = 0.2 if skill_id == self._prev_skill else 0.0

        # 狀態相關加分
        state_bonus = self._state_relevance(skill_id, state)

        # 綜合分數
        raw_score = (
            sim * 0.4
            + priority * 0.3
            + state_bonus * 0.2
            + continuity_bonus * 0.1
            - cooldown_penalty
        )
        confidence = 1 / (1 + np.exp(-raw_score * 5))  # Sigmoid 映射到 [0,1]

        # 生成參數預估
        params = self._estimate_params(skill_id, state)

        return SkillScore(skill_id=skill_id, score=raw_score, confidence=confidence, params=params)

    def _state_relevance(self, skill_id: SkillID, state: GameState) -> float:
        """根據當前狀態計算技能相關性"""
        if not state.proprioception:
            return 0.0

        prop = state.proprioception
        bonus = 0.0

        if skill_id == SkillID.EAT:
            hunger_ratio = prop.hunger / max(prop.max_hunger, 1)
            if hunger_ratio < 0.3:
                bonus += 0.5 * (1 - hunger_ratio / 0.3)

        elif skill_id == SkillID.COMBAT:
            if prop.hp < prop.max_hp * 0.5:
                bonus += 0.3
            # 檢查附近敵對實體 (簡化)

        elif skill_id == SkillID.DIG:
            # 手持工具且面前有可挖方塊
            if (
                "pickaxe" in prop.wielded_item
                or "axe" in prop.wielded_item
                or "shovel" in prop.wielded_item
            ):
                bonus += 0.2

        elif skill_id == SkillID.CRAFT:
            # 背包有材料且配方解鎖
            if len(prop.inventory) > 5:
                bonus += 0.1

        elif skill_id == SkillID.MOVE or skill_id == SkillID.NAVIGATE:
            # 需要移動時 (有目標、卡住、探索)
            if state.task_progress and state.task_progress.blocker:
                bonus += 0.4

        return bonus

    def _estimate_params(self, skill_id: SkillID, state: GameState) -> Dict[str, Any]:
        """估算技能參數"""
        params = {}
        prop = state.proprioception

        if skill_id == SkillID.MOVE:
            params = {"forward": 1.0, "strafe": 0.0, "yaw": 0.0}

        elif skill_id == SkillID.DIG:
            # 朝著面前的方塊
            params = {"target_node": "auto", "direction": "forward", "tool": prop.wielded_item}

        elif skill_id == SkillID.PLACE:
            # 手持方塊
            for item, count in prop.inventory.items():
                if count > 0 and item not in ["pickaxe", "axe", "shovel", "sword"]:
                    params = {"block_type": item, "face": "top", "direction": "forward"}
                    break

        elif skill_id == SkillID.CRAFT:
            # 簡化：優先合成工具（背包先折短名，否則 itemstring 永遠對不上）
            from ai.multimodal.game_memory_bridge import normalize_inventory

            inv = normalize_inventory(prop.inventory)
            if inv.get("cobblestone", 0) >= 3:
                params = {"recipe_id": "stone_pickaxe", "count": 1}
            elif inv.get("wood", 0) >= 2:
                params = {"recipe_id": "stick", "count": 4}
            else:
                params = {"recipe_id": "auto", "count": 1}

        elif skill_id == SkillID.COMBAT:
            params = {
                "target_entity": "nearest_hostile",
                "weapon": prop.wielded_item,
                "tactic": "melee",
            }

        elif skill_id == SkillID.NAVIGATE:
            params = {"target_pos": None, "path": None}

        elif skill_id == SkillID.EAT:
            food = next(
                (
                    k
                    for k in prop.inventory
                    if any(f in k for f in ["apple", "bread", "meat", "carrot"])
                ),
                "apple",
            )
            params = {"food_item": food}

        elif skill_id == SkillID.BUILD:
            params = {"blueprint": "shelter_5x5x3", "origin": prop.position, "rotation": 0}

        elif skill_id == SkillID.LOOK:
            params = {"yaw": 0.0, "pitch": -0.3, "target": "scan"}

        return params

    def _parameterize_skill(
        self, skill_id: SkillID, base_params: Dict, state: GameState, latent: np.ndarray
    ) -> SkillParams:
        """將技能參數化為 L0 可用格式"""
        spec = GAME_SKILLS[skill_id]

        # 基礎參數
        params = base_params.copy()

        # 連續動作 bias (從 latent 解碼或用預設)
        continuous_bias = np.zeros(spec.continuous_dim, dtype=np.float32)
        discrete_triggers = {}

        # 使用相對索引 (每個技能自己的 continuous_dim 範圍)

        if skill_id == SkillID.MOVE:
            # 3 dims: forward, strafe, yaw
            continuous_bias[0] = params.get("forward", 1.0)
            continuous_bias[1] = params.get("strafe", 0.0)
            continuous_bias[2] = params.get("yaw", 0.0)
            if params.get("jump"):
                discrete_triggers["jump"] = 1.0
            if params.get("sprint"):
                discrete_triggers["sprint"] = 1.0
            if params.get("sneak"):
                discrete_triggers["sneak"] = 1.0

        elif skill_id == SkillID.DIG:
            # 2 dims: dig_yaw, dig_pitch
            continuous_bias[0] = 0.0  # dig_yaw
            continuous_bias[1] = 0.0  # dig_pitch
            discrete_triggers["attack"] = 1.0

        elif skill_id == SkillID.PLACE:
            # 2 dims: place_yaw, place_pitch
            continuous_bias[0] = 0.0  # place_yaw
            continuous_bias[1] = 0.0  # place_pitch
            discrete_triggers["use"] = 1.0

        elif skill_id == SkillID.COMBAT:
            # 3 dims: combat_yaw, combat_pitch, combat_strafe
            continuous_bias[0] = 0.0  # combat_yaw
            continuous_bias[1] = 0.0  # combat_pitch
            continuous_bias[2] = 0.5  # combat_strafe (左右移動)
            discrete_triggers["attack"] = 1.0
            discrete_triggers["block"] = 0.3

        elif skill_id == SkillID.NAVIGATE:
            # 3 dims: nav_yaw, nav_pitch, nav_forward
            continuous_bias[0] = 0.0  # nav_yaw
            continuous_bias[1] = 0.0  # nav_pitch
            continuous_bias[2] = 1.0  # nav_forward

        elif skill_id == SkillID.LOOK:
            # 2 dims: yaw, pitch
            continuous_bias[0] = params.get("yaw", 0.0)
            continuous_bias[1] = params.get("pitch", -0.3)

        elif skill_id == SkillID.BUILD:
            # 2 dims: build_yaw, build_pitch
            continuous_bias[0] = 0.0  # build_yaw
            continuous_bias[1] = 0.0  # build_pitch
            discrete_triggers["use"] = 1.0
            discrete_triggers["sneak"] = 0.5

        # 終止條件
        termination = self._get_termination_condition(skill_id, params, state)

        return SkillParams(
            skill_id=skill_id,
            continuous_bias=continuous_bias,
            discrete_triggers=discrete_triggers,
            termination_condition=termination,
            priority=1.0,
            params=params,
        )

    def _get_termination_condition(self, skill_id: SkillID, params: Dict, state: GameState) -> str:
        """生成終止條件字串"""
        if skill_id == SkillID.DIG:
            return "inventory_changed:*"
        elif skill_id == SkillID.PLACE:
            return "block_placed"
        elif skill_id == SkillID.CRAFT:
            return f"inventory_changed:{params.get('recipe_id', 'craft_output')}"
        elif skill_id == SkillID.COMBAT:
            return "target_dead_or_lost"
        elif skill_id == SkillID.NAVIGATE:
            return "reached_target"
        elif skill_id == SkillID.EAT:
            return "hunger_restored"
        elif skill_id == SkillID.BUILD:
            return "blueprint_complete"
        return "timeout"

    def _fallback_idle(self, state: GameState) -> SkillParams:
        """無可用技能時的待機動作"""
        return SkillParams(
            skill_id=SkillID.LOOK,
            continuous_bias=np.array([0.0, -0.2], dtype=np.float32),  # 向下看
            discrete_triggers={},
            termination_condition="timeout",
            priority=0.1,
            params={"yaw": 0.0, "pitch": -0.3, "target": "idle_scan"},
        )

    def _softmax(self, scores: List[float]) -> np.ndarray:
        arr = np.array(scores) / self.config.temperature
        arr = arr - arr.max()
        e = np.exp(arr)
        return e / e.sum()

    def get_skill_triggers(self, latent: np.ndarray, state: GameState) -> List[SkillTrigger]:
        """輸出所有技能觸發建議 (供 L2 參考)"""
        available = get_available_skills(state)
        triggers = []

        for skill_id in available:
            score = self._score_skill(skill_id, latent, state)
            if score.confidence > 0.2:
                triggers.append(
                    SkillTrigger(
                        skill_id=skill_id,
                        confidence=score.confidence,
                        params=score.params,
                        urgency=score.confidence
                        * (1.0 if skill_id in [SkillID.EAT, SkillID.COMBAT] else 0.5),
                    )
                )

        triggers.sort(key=lambda t: t.urgency, reverse=True)
        return triggers[:5]  # Top 5


class SkillLibrary:
    """技能庫管理：註冊、更新、序列化"""

    def __init__(self):
        self.skills: Dict[SkillID, SkillSpec] = GAME_SKILLS.copy()
        self.custom_skills: Dict[SkillID, SkillSpec] = {}

    def register(self, skill_id: SkillID, spec: SkillSpec):
        self.custom_skills[skill_id] = spec

    def get(self, skill_id: SkillID) -> Optional[SkillSpec]:
        return self.custom_skills.get(skill_id) or self.skills.get(skill_id)

    def all(self) -> Dict[SkillID, SkillSpec]:
        merged = self.skills.copy()
        merged.update(self.custom_skills)
        return merged

    def update_priority(self, skill_id: SkillID, priority: float):
        if skill_id in self.skills:
            # 實際上會更新 selector 的 _skill_priorities
            pass
