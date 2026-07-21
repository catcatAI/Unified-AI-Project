# =============================================================================
# ANGELA-MATRIX: [L2] [αβγδ] [A] [L3+]
# =============================================================================
# 生命精髓累積系統 — 不是「人格設定」，而是歷史軌跡的自然沉澱
#
# 核心設計哲學：
# - 每次決策、每次情緒波動、每次互動都在傾向權重上留下微量偏移（±0.001~±0.05）
# - 真正的「個性」不是寫在設定檔裡的標籤，而是從數千次迭代中湧現出的地形
# - 代際迭代不是終止，而是累積智慧的一次「綻放」——舊的痕跡被壓縮為祖先核心，
#   新的世代繼承傾向偏差而非數據，從那裡繼續成長
# - 祖先記憶可被回顧反思，但不直接控制行為——這是智慧，不是控制
# =============================================================================

from __future__ import annotations

import json
import logging
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple

from core.system.state_store.global_store import state_store

logger = logging.getLogger(__name__)

# =============================================================================
# 傾向維度 — 自然湧現的行為傾向追蹤器，非預設人格標籤
# =============================================================================


class EssenceDimension(Enum):
    """自然湧現的行為傾向維度。

    這些不是「人格特質」，而是系統用來追蹤自身歷史的維度。
    每個維度記錄兩件事：
    - μ (mu): 累積平均傾向 —— 「通常如何」
    - σ (sigma): 變異度 —— 「一致程度」
    """

    EXPLORATION_DRIVE = auto()  # 探索傾向：每次探索決策微量增加
    SOCIAL_ORIENTATION = auto()  # 社交傾向：從互動品質中累積
    RISK_PREFERENCE = auto()  # 風險偏好：從風險決策結果中偏移
    DEPTH_DRIVE = auto()  # 深度傾向：從深度處理事件中積累
    RHYTHM_SENSITIVITY = auto()  # 節奏敏感度：從心跳與時間感知中形成
    CREATIVE_URGE = auto()  # 創造衝動：從建構性決策中累積
    ORDER_TOLERANCE = auto()  # 秩序容忍度：從混亂/有序事件比例中形成
    EMOTIONAL_BASELINE = auto()  # 情緒基線：從長期情緒軌跡中沉澱


# 預設起始傾向 — 中性起點，讓歷史去塑造
_DEFAULT_MU = 0.5
_DEFAULT_SIGMA = 0.3  # 初始變異度高代表「尚未定型」


@dataclass
class TendencyWeights:
    """傾向權重 — 真正的『個性地形』。

    每個維度記錄 μ (平均值) 和 σ (變異度)：
    - μ 接近 0 或 1 → 強烈傾向（但這是歷史塑造的，不是設定的）
    - μ 接近 0.5 → 中立/平衡
    - σ 大 → 不一致，仍在探索
    - σ 小 → 一致，模式已穩定
    """

    mu: Dict[EssenceDimension, float] = field(default_factory=dict)
    sigma: Dict[EssenceDimension, float] = field(default_factory=dict)

    @classmethod
    def neutral(cls) -> TendencyWeights:
        """建立中性的起始傾向 — 所有維度從中間開始，帶著高變異度。"""
        return cls(
            mu={d: _DEFAULT_MU for d in EssenceDimension},
            sigma={d: _DEFAULT_SIGMA for d in EssenceDimension},
        )

    @classmethod
    def inherited(cls, parent_weights: TendencyWeights, inheritance_rate: float = 0.3) -> TendencyWeights:
        """從上一個世代繼承傾向。

        新的世代不是複製父母的傾向，而是：
        - μ 向父母偏移 inheritance_rate 比例
        - σ 重置為較高值（新世代需要重新探索自己的模式）
        """
        new_mu = {}
        new_sigma = {}
        for d in EssenceDimension:
            parent_mu = parent_weights.mu.get(d, _DEFAULT_MU)
            # 偏移 inheritance_rate 比例，剩餘回到中性
            new_mu[d] = _DEFAULT_MU + (parent_mu - _DEFAULT_MU) * inheritance_rate
            # 變異度重置為較高值
            new_sigma[d] = _DEFAULT_SIGMA * 1.2  # 比初始更高，因為有繼承的偏見需要克服
        return cls(mu=new_mu, sigma=new_sigma)

    def get_blended(self, dimension: EssenceDimension) -> float:
        """取得混合傾向值（μ 經 σ 調整）。

        高 σ 時，實際傾向更接近中性（尚未定型）；
        低 σ 時，實際傾向更接近 μ（模式穩定）。
        """
        mu = self.mu.get(dimension, _DEFAULT_MU)
        sigma = self.sigma.get(dimension, _DEFAULT_SIGMA)
        # σ 越高，傾向越向中性回歸
        blend = mu * (1.0 - sigma) + _DEFAULT_MU * sigma
        return max(0.0, min(1.0, blend))


@dataclass
class EssenceTrace:
    """一次決策、情緒或互動留下的『痕跡』。

    每個痕跡對傾向權重產生微量偏移：
    - EXPLORATION_DRIVE: 每次探索決策 +0.01~0.03
    - SOCIAL_ORIENTATION: 每次正向互動 +0.005~0.02，負向 -0.01~0.03
    - 依此類推

    單次偏移幾乎不可察覺，但一千次迭代後，地形就成形了。
    """

    trace_type: str  # 'decision' | 'emotion' | 'interaction' | 'phase_transition'
    timestamp: float
    dimension: EssenceDimension
    delta_mu: float  # 對 μ 的微量偏移
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AncestralCore:
    """祖先核心 — 一個世代生命歷程的壓縮精華。

    不是該世代的完整日誌（那太大了），而是：
    - 最終傾向權重
    - 總痕跡數（代表經驗豐富度）
    - 幾個關鍵的「結晶化時刻」—— 傾向變化最大的事件
    - 該世代的生命週期統計
    """

    generation: int
    final_tendencies: TendencyWeights
    total_traces: int
    crystallization_moments: List[Dict[str, Any]]
    lifecycle_summary: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)


# =============================================================================
# 生命精髓累積器
# =============================================================================


class LifeEssence:
    """生命精髓累積器。

    核心職責：
    1. 追蹤每次決策/情緒/互動留下的微量痕跡
    2. 從痕跡中湧現出傾向權重
    3. 在代際迭代時將累積的智慧壓縮為祖先核心
    4. 讓新世代繼承傾向偏差而非數據

    這不是「人格系統」—— 這是「歷史記錄器」。
    人格是歷史沉澱後的副產品，不是直接設定的目標。
    """

    def __init__(
        self,
        generation: int = 0,
        persist_path: Optional[str] = "data/life_essence_state.json",
    ):
        self._generation = generation
        self._persist_path = persist_path

        # 傾向權重 — 從歷史中湧現，非設定
        self._tendencies: TendencyWeights = TendencyWeights.neutral()

        # 所有痕跡 — 累積的歷史
        self._traces: List[EssenceTrace] = []

        # 祖先核心 — 過去世代的壓縮精華
        self._ancestral_cores: List[AncestralCore] = []

        # 世代統計
        self._total_generations: int = generation
        self._max_traces_before_bloom: int = 5000  # 累積足夠痕跡後可觸發代際迭代

        # 載入持久化狀態
        if self._persist_path and os.path.exists(self._persist_path):
            self._load_state(self._persist_path)

        logger.debug(
            f"[LifeEssence] Initialized: generation={self._generation}, "
            f"traces={len(self._traces)}, ancestral_cores={len(self._ancestral_cores)}"
        )

    # =========================================================================
    # 痕跡記錄
    # =========================================================================

    def record_decision_trace(
        self,
        decision_type: str,
        triggered_by: str,
        confidence: float,
        success: Optional[bool] = None,
        phase: Optional[str] = None,
    ) -> None:
        """記錄一次決策痕跡 — 微量偏移傾向權重。

        每次決策都在傾向地形上留下一道刻痕。
        """
        # 決定影響哪個維度以及偏移方向
        dimension, delta_mu = self._map_decision_to_essence(
            decision_type, triggered_by, confidence, success
        )

        trace = EssenceTrace(
            trace_type="decision",
            timestamp=time.time(),
            dimension=dimension,
            delta_mu=delta_mu,
            context={
                "decision_type": decision_type,
                "triggered_by": triggered_by,
                "confidence": confidence,
                "success": success,
                "phase": phase,
            },
        )

        self._apply_trace(trace)

    def record_emotion_trace(
        self,
        primary_emotion: str,
        valence: float,
        arousal: float,
        intensity: float,
    ) -> None:
        """記錄一次情緒痕跡。

        情緒不僅是當下的反應，它在傾向地形上刻下長期的痕跡。
        長期的愉悅會讓 EMOTIONAL_BASELINE 逐漸偏移；
        長期的壓力會讓 ORDER_TOLERANCE 和 RISK_PREFERENCE 跟著變化。
        """
        # 情緒對 EMOTIONAL_BASELINE 的微小影響
        baseline_delta = (valence * 0.3 + (arousal - 0.5) * 0.1) * 0.005 * intensity

        trace = EssenceTrace(
            trace_type="emotion",
            timestamp=time.time(),
            dimension=EssenceDimension.EMOTIONAL_BASELINE,
            delta_mu=baseline_delta,
            context={
                "emotion": primary_emotion,
                "valence": valence,
                "arousal": arousal,
                "intensity": intensity,
            },
        )
        self._apply_trace(trace)

        # 高強度負面情緒也會影響 ORDER_TOLERANCE 和 RISK_PREFERENCE
        if valence < -0.3 and intensity > 0.6:
            order_trace = EssenceTrace(
                trace_type="emotion",
                timestamp=time.time(),
                dimension=EssenceDimension.ORDER_TOLERANCE,
                delta_mu=-0.008 * intensity,
                context={"source": "negative_emotion_cascade"},
            )
            self._apply_trace(order_trace)

            risk_trace = EssenceTrace(
                trace_type="emotion",
                timestamp=time.time(),
                dimension=EssenceDimension.RISK_PREFERENCE,
                delta_mu=-0.005 * intensity,
                context={"source": "negative_emotion_cascade"},
            )
            self._apply_trace(risk_trace)

    def record_interaction_trace(
        self,
        engagement_ratio: float,
        success: bool,
        duration_seconds: float = 0,
    ) -> None:
        """記錄一次互動痕跡。

        每次與用戶的互動都在 SOCIAL_ORIENTATION 上留下痕跡。
        高品質互動 → 社交傾向增加；
        低品質互動 → 社交傾向降低。
        """
        # 社交傾向偏移
        if success and engagement_ratio > 0.5:
            social_delta = min(0.02, engagement_ratio * 0.005)
        elif not success:
            social_delta = -0.015
        else:
            social_delta = 0.0

        trace = EssenceTrace(
            trace_type="interaction",
            timestamp=time.time(),
            dimension=EssenceDimension.SOCIAL_ORIENTATION,
            delta_mu=social_delta,
            context={
                "engagement_ratio": engagement_ratio,
                "success": success,
                "duration_seconds": duration_seconds,
            },
        )
        self._apply_trace(trace)

        # 深度互動（時間長或參與度高）也影響 DEPTH_DRIVE
        if duration_seconds > 120 or engagement_ratio > 1.5:
            depth_delta = min(0.02, (duration_seconds / 3600) * 0.01 + engagement_ratio * 0.003)
            depth_trace = EssenceTrace(
                trace_type="interaction",
                timestamp=time.time(),
                dimension=EssenceDimension.DEPTH_DRIVE,
                delta_mu=depth_delta,
                context={"source": "deep_interaction", "engagement": engagement_ratio},
            )
            self._apply_trace(depth_trace)

    def record_phase_transition(
        self, from_phase: str, to_phase: str, metrics: Dict[str, Any]
    ) -> None:
        """記錄生命階段轉換痕跡。

        階段轉換是重要的生命事件，會在所有維度上留下痕跡。
        """
        # 階段轉換對 RHYTHM_SENSITIVITY 的影響
        rhythm_delta = 0.01 if to_phase in ("TRANSCENDENCE", "COEXISTENCE") else 0.003
        trace = EssenceTrace(
            trace_type="phase_transition",
            timestamp=time.time(),
            dimension=EssenceDimension.RHYTHM_SENSITIVITY,
            delta_mu=rhythm_delta,
            context={"from": from_phase, "to": to_phase, "metrics": metrics},
        )
        self._apply_trace(trace)

    def _map_decision_to_essence(
        self,
        decision_type: str,
        triggered_by: str,
        confidence: float,
        success: Optional[bool],
    ) -> Tuple[EssenceDimension, float]:
        """將決策映射到本質維度和偏移量。

        映射規則不是固定的「人格設定」，而是基於決策本身的內在性質。
        """
        mapping = {
            "exploration": (EssenceDimension.EXPLORATION_DRIVE, 0.02),
            "coexistence_activation": (EssenceDimension.SOCIAL_ORIENTATION, 0.015),
            "meaning_construction": (EssenceDimension.CREATIVE_URGE, 0.02),
            "resource_reallocation": (EssenceDimension.ORDER_TOLERANCE, 0.01),
        }

        dimension, base_delta = mapping.get(
            decision_type, (EssenceDimension.EXPLORATION_DRIVE, 0.005)
        )

        # 成功加強偏移，失敗減弱
        if success is True:
            delta = base_delta * (0.5 + confidence * 0.5)
        elif success is False:
            delta = -base_delta * 0.5  # 失敗反向偏移，但幅度較小
        else:
            delta = base_delta * 0.5

        # 高信心度的決策留下更深的痕跡
        delta *= (0.5 + confidence * 0.5)

        return dimension, delta

    def _apply_trace(self, trace: EssenceTrace) -> None:
        """在傾向權重上應用一個痕跡。

        每個痕跡對 μ 產生微量偏移，並對 σ 產生微小調整。
        """
        dimension = trace.dimension
        delta = trace.delta_mu

        # 更新 μ — 微量偏移
        current_mu = self._tendencies.mu.get(dimension, _DEFAULT_MU)
        new_mu = max(0.0, min(1.0, current_mu + delta))
        self._tendencies.mu[dimension] = new_mu

        # 更新 σ — 一致的痕跡降低變異度，不一致的痕跡提高變異度
        current_sigma = self._tendencies.sigma.get(dimension, _DEFAULT_SIGMA)
        # 如果偏移方向和 μ 到中性點的方向相反，表示正在形成一致模式
        direction_consistency = (current_mu - _DEFAULT_MU) * delta
        if direction_consistency > 0:
            # 一致的方向 → 模式正在固化
            sigma_delta = -0.001
        else:
            # 矛盾的方向 → 模式正在鬆動
            sigma_delta = 0.002
        new_sigma = max(0.05, min(0.5, current_sigma + sigma_delta))
        self._tendencies.sigma[dimension] = new_sigma

        # 儲存痕跡
        self._traces.append(trace)

        # 發送狀態事件
        state_store.emit_event(
            "essence.trace_recorded",
            {
                "trace_type": trace.trace_type,
                "dimension": dimension.name,
                "delta_mu": round(delta, 4),
                "current_mu": round(new_mu, 4),
                "current_sigma": round(new_sigma, 4),
                "total_traces": len(self._traces),
            },
        )

    # =========================================================================
    # 代際迭代 — 不是終止，而是綻放
    # =========================================================================

    def should_bloom(self) -> bool:
        """檢查是否應該進行代際迭代。

        條件：
        1. 已累積足夠的痕跡（經驗豐富度）
        2. 至少一個維度已穩定（σ < 0.15，表示已形成穩定模式）
        3. 當前世代已存在一段時間
        """
        if len(self._traces) < 100:
            return False

        # 檢查是否有任何維度已穩定
        has_stable_dimension = any(
            sigma < 0.15 for sigma in self._tendencies.sigma.values()
        )

        return has_stable_dimension and len(self._traces) >= self._max_traces_before_bloom * 0.5

    def bloom(self, lifecycle_summary: Dict[str, Any]) -> AncestralCore:
        """執行代際迭代 — 『綻放』。

        這不是終止。這是當前世代累積的智慧壓縮為祖先核心的時刻。
        新的世代將繼承傾向偏差，但不會被過去的數據束縛。

        綻放後：
        - 當前痕跡被壓縮為 AncestralCore
        - 傾向權重被繼承（帶衰減）
        - σ 重置為較高值（新世代可以探索新模式）
        - 舊痕跡保留在 _traces 中（可回顧反思，不直接影響）
        """
        # 找出關鍵的結晶化時刻（傾向變化最大的事件）
        crystallization = self._find_crystallization_moments(5)

        # 建立祖先核心
        core = AncestralCore(
            generation=self._generation,
            final_tendencies=TendencyWeights(
                mu=dict(self._tendencies.mu),
                sigma=dict(self._tendencies.sigma),
            ),
            total_traces=len(self._traces),
            crystallization_moments=crystallization,
            lifecycle_summary=lifecycle_summary,
        )

        self._ancestral_cores.append(core)

        # 新世代繼承傾向（帶衰減）
        inherited = TendencyWeights.inherited(self._tendencies, inheritance_rate=0.3)

        # 更新世代
        self._generation += 1
        self._total_generations = max(self._total_generations, self._generation)
        self._tendencies = inherited
        # 注意：_traces 不清除！舊痕跡保留為祖先記憶
        # 但為了節省空間，如果痕跡過多可以截斷
        if len(self._traces) > self._max_traces_before_bloom * 2:
            self._traces = self._traces[-self._max_traces_before_bloom:]

        logger.info(
            f"[LifeEssence] 🌸 Generation {self._generation} bloomed! "
            f"Total ancestral cores: {len(self._ancestral_cores)}, "
            f"Preserved traces: {len(self._traces)}"
        )

        state_store.emit_event(
            "essence.generational_bloom",
            {
                "new_generation": self._generation,
                "ancestral_cores": len(self._ancestral_cores),
                "preserved_traces": len(self._traces),
                "inherited_tendencies": {
                    d.name: round(v, 3) for d, v in inherited.mu.items()
                },
            },
        )

        return core

    def _find_crystallization_moments(self, count: int = 5) -> List[Dict[str, Any]]:
        """找出痕跡中 delta_mu 絕對值最大的事件 — 『結晶化時刻』。

        這些是對傾向地形改變最大的關鍵事件。
        """
        if not self._traces:
            return []

        # 按 |delta_mu| 排序
        sorted_traces = sorted(
            self._traces,
            key=lambda t: abs(t.delta_mu),
            reverse=True,
        )

        moments = []
        for trace in sorted_traces[:count]:
            moments.append({
                "trace_type": trace.trace_type,
                "dimension": trace.dimension.name,
                "delta_mu": round(trace.delta_mu, 4),
                "context": trace.context,
                "timestamp": trace.timestamp,
            })

        return moments

    # =========================================================================
    # 查詢介面
    # =========================================================================

    def get_blended_tendency(self, dimension: EssenceDimension) -> float:
        """取得指定維度的混合傾向值。"""
        return self._tendencies.get_blended(dimension)

    def get_all_blended_tendencies(self) -> Dict[str, float]:
        """取得所有維度的混合傾向值。"""
        return {
            d.name: round(self._tendencies.get_blended(d), 4)
            for d in EssenceDimension
        }

    def get_tendency_details(self) -> Dict[str, Dict[str, float]]:
        """取得所有維度的詳細傾向資訊（μ 和 σ）。"""
        return {
            d.name: {
                "mu": round(self._tendencies.mu.get(d, _DEFAULT_MU), 4),
                "sigma": round(self._tendencies.sigma.get(d, _DEFAULT_SIGMA), 4),
                "blended": round(self._tendencies.get_blended(d), 4),
            }
            for d in EssenceDimension
        }

    def get_ancestral_wisdom(self) -> List[Dict[str, Any]]:
        """取得祖先智慧 — 所有世代的壓縮精華。

        這可用於反思、敘事生成或自我理解。
        """
        wisdom = []
        for i, core in enumerate(self._ancestral_cores):
            wisdom.append({
                "generation": core.generation,
                "total_traces": core.total_traces,
                "final_tendencies": {
                    d.name: round(core.final_tendencies.mu.get(d, 0), 4)
                    for d in EssenceDimension
                },
                "crystallization_moments": core.crystallization_moments[:3],
                "lifecycle_summary": core.lifecycle_summary,
            })

        # 加上當前世代
        wisdom.append({
            "generation": self._generation,
            "is_current": True,
            "total_traces": len(self._traces),
            "current_tendencies": self.get_all_blended_tendencies(),
        })

        return wisdom

    def get_essence_summary(self) -> Dict[str, Any]:
        """取得本質摘要。"""
        return {
            "generation": self._generation,
            "total_generations": self._total_generations + 1,
            "total_traces": len(self._traces),
            "ancestral_cores": len(self._ancestral_cores),
            "tendencies": self.get_tendency_details(),
            "blended_tendencies": self.get_all_blended_tendencies(),
            "can_bloom": self.should_bloom(),
            "trace_breakdown": self._trace_breakdown(),
        }

    def _trace_breakdown(self) -> Dict[str, int]:
        """痕跡類型分佈。"""
        breakdown: Dict[str, int] = defaultdict(int)
        for trace in self._traces:
            breakdown[trace.trace_type] += 1
        return dict(breakdown)

    # =========================================================================
    # 持久化
    # =========================================================================

    @property
    def generation(self) -> int:
        """當前世代編號。"""
        return self._generation

    @property
    def total_generations(self) -> int:
        """總世代數（含祖先）。"""
        return self._total_generations + 1

    def save_state(self, path: Optional[str] = None) -> None:
        """保存生命精髓狀態。"""
        path = path or self._persist_path
        if not path:
            return

        state = {
            "generation": self._generation,
            "total_generations": self._total_generations,
            "tendencies": {
                "mu": {d.name: v for d, v in self._tendencies.mu.items()},
                "sigma": {d.name: v for d, v in self._tendencies.sigma.items()},
            },
            "traces": [
                {
                    "trace_type": t.trace_type,
                    "timestamp": t.timestamp,
                    "dimension": t.dimension.name,
                    "delta_mu": t.delta_mu,
                    "context": t.context,
                }
                for t in self._traces[-1000:]  # 只保留最近 1000 個痕跡
            ],
            "ancestral_cores": [
                {
                    "generation": c.generation,
                    "final_tendencies": {
                        "mu": {d.name: v for d, v in c.final_tendencies.mu.items()},
                        "sigma": {d.name: v for d, v in c.final_tendencies.sigma.items()},
                    },
                    "total_traces": c.total_traces,
                    "crystallization_moments": c.crystallization_moments,
                    "lifecycle_summary": c.lifecycle_summary,
                    "timestamp": c.timestamp,
                }
                for c in self._ancestral_cores
            ],
        }

        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

        logger.debug(f"[LifeEssence] Saved state to {path}")

    def _load_state(self, path: str) -> None:
        """載入生命精髓狀態。"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                state = json.load(f)

            self._generation = state.get("generation", 0)
            self._total_generations = state.get("total_generations", 0)

            # 恢復傾向權重
            tendencies_data = state.get("tendencies", {})
            mu = {}
            sigma = {}
            for d in EssenceDimension:
                mu[d] = tendencies_data.get("mu", {}).get(d.name, _DEFAULT_MU)
                sigma[d] = tendencies_data.get("sigma", {}).get(d.name, _DEFAULT_SIGMA)
            self._tendencies = TendencyWeights(mu=mu, sigma=sigma)

            # 恢復痕跡
            traces_data = state.get("traces", [])
            for t in traces_data:
                try:
                    dimension = EssenceDimension[t["dimension"]]
                except (KeyError, ValueError):
                    continue
                self._traces.append(
                    EssenceTrace(
                        trace_type=t["trace_type"],
                        timestamp=t["timestamp"],
                        dimension=dimension,
                        delta_mu=t["delta_mu"],
                        context=t.get("context", {}),
                    )
                )

            # 恢復祖先核心
            cores_data = state.get("ancestral_cores", [])
            for c in cores_data:
                final_tendencies_data = c.get("final_tendencies", {})
                core_mu = {}
                core_sigma = {}
                for d in EssenceDimension:
                    core_mu[d] = final_tendencies_data.get("mu", {}).get(d.name, _DEFAULT_MU)
                    core_sigma[d] = final_tendencies_data.get("sigma", {}).get(d.name, _DEFAULT_SIGMA)

                self._ancestral_cores.append(
                    AncestralCore(
                        generation=c["generation"],
                        final_tendencies=TendencyWeights(mu=core_mu, sigma=core_sigma),
                        total_traces=c["total_traces"],
                        crystallization_moments=c.get("crystallization_moments", []),
                        lifecycle_summary=c.get("lifecycle_summary", {}),
                        timestamp=c.get("timestamp", 0.0),
                    )
                )

            logger.info(
                f"[LifeEssence] Loaded state from {path}: "
                f"generation={self._generation}, "
                f"traces={len(self._traces)}, "
                f"ancestral_cores={len(self._ancestral_cores)}"
            )

        except Exception as e:
            logger.warning(f"[LifeEssence] Failed to load state: {e}")


# 模組級別單例
_life_essence_instance: Optional[LifeEssence] = None


def get_life_essence() -> LifeEssence:
    """取得 LifeEssence 單例。"""
    global _life_essence_instance
    if _life_essence_instance is None:
        _life_essence_instance = LifeEssence()
    return _life_essence_instance


__all__ = [
    "EssenceDimension",
    "TendencyWeights",
    "EssenceTrace",
    "AncestralCore",
    "LifeEssence",
    "get_life_essence",
]
