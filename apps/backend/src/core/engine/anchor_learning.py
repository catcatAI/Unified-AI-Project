"""
Anchor Learning Engine — 語義錨點學習引擎
=========================================

從軸狀態快照、分配決策歷史、θ 自糾結果中學習，
逐步調整 semantic anchor 向量，使相似度評分有意義。

Author: Angela AI v6.2
Version: 6.2.1
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, TYPE_CHECKING
import math
import time
import logging

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from core.allocation.resonance import ResonanceEngine
    from core.state.temporal import TemporalState


@dataclass
class AllocationRecord:
    """分配決策記錄"""
    vector: List[float]
    action: str
    target: Optional[str]
    confidence: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class MisallocationRecord:
    """錯誤分配記錄"""
    vector: List[float]
    wrong_axis: str
    right_axis: Optional[str]
    confidence: float
    timestamp: float = field(default_factory=time.time)


class AnchorLearningEngine:
    """
    Semantic Anchor 學習引擎

    從軸狀態快照、分配決策歷史、θ 自糾結果中學習，
    逐步調整 semantic anchor 向量，使相似度評分有意義。

    學習策略：
    - EMA (Exponential Moving Average) 更新錨點，避免劇烈波動
    - 分配反饋：ASSIGN → 錨點靠近輸入；DEFER → 記錄未分類
    - θ 驅動修正：wrong_axis 遠離，right_axis 靠近
    - 關鍵詞追蹤：建立 word→axis 權重映射
    """

    def __init__(
        self,
        resonance_engine: "ResonanceEngine",
        temporal: Optional["TemporalState"] = None,
        ema_alpha: float = 0.9,
        learning_interval: int = 10,
        defer_threshold: float = 0.3,
        assign_lr: float = 0.05,
        misalloc_lr: float = 0.03,
    ):
        """
        Args:
            resonance_engine: ResonanceEngine 實例（管理 semantic vectors）
            temporal: TemporalState 實例（用於查詢穩定狀態）
            ema_alpha: EMA 平滑因子（越大 = 調整越慢）
            learning_interval: 每 N 次軸更新觸發一次學習
            defer_threshold: ASSIGN 置信度閾值（低於此視為不可靠）
            assign_lr: ASSIGN 學習率
            misalloc_lr: Misallocation 修正學習率
        """
        self._resonance = resonance_engine
        self._temporal = temporal
        self._ema_alpha = ema_alpha
        self._learning_interval = learning_interval
        self._defer_threshold = defer_threshold
        self._assign_lr = assign_lr
        self._misalloc_lr = misalloc_lr

        self._update_counts: Dict[str, int] = {}
        self._allocation_history: List[AllocationRecord] = []
        self._misallocation_history: List[MisallocationRecord] = []
        self._unclassified: List[List[float]] = []
        self._keyword_axis_weights: Dict[str, Dict[str, float]] = {}

        self._last_anchor_stats: Dict[str, int] = {}

    # =========================================================================
    # 觸發點 1: 軸狀態更新 → 更新錨點
    # =========================================================================

    def on_axis_update(
        self,
        axis_name: str,
        snapshot: Dict[str, float],
        is_stable: bool = False,
    ) -> None:
        """
        每次軸更新時調用（從 StateMatrixAdapter 觸發）

        Args:
            axis_name: 軸名稱
            snapshot: 軸快照（field name → value）
            is_stable: 是否為穩定狀態（穩定狀態才更新 anchor）
        """
        count = self._update_counts.get(axis_name, 0) + 1
        self._update_counts[axis_name] = count

        if not is_stable and count % self._learning_interval != 0:
            return

        vec = self._snapshot_to_vector(snapshot)
        anchor = self._resonance._semantic_vectors.get(axis_name)
        if anchor is None:
            return

        prev_nonzero = sum(1 for v in anchor if abs(v) > 1e-6)
        new_anchor = self._ema_update(anchor, vec, lr=1.0 - self._ema_alpha)
        new_nonzero = sum(1 for v in new_anchor if abs(v) > 1e-6)

        self._resonance._semantic_vectors[axis_name] = new_anchor

        if new_nonzero != prev_nonzero:
            logger.debug(
                f"Axis {axis_name} sparsity changed: {prev_nonzero} -> {new_nonzero} nonzero components"
            )
            self._resonance._sparsity_shift(axis_name, new_nonzero - prev_nonzero)

    # =========================================================================
    # 觸發點 2: 分配決策 → 反饋學習
    # =========================================================================

    def on_allocation_decision(
        self,
        vector: List[float],
        action: str,
        target: Optional[str],
        confidence: float,
    ) -> None:
        """
        每次 meta_allocate() 決策後調用

        Args:
            vector: 輸入向量
            action: 決策動作（ASSIGN/COMPOSITE/CREATE/DEFER）
            target: 目標軸名
            confidence: 置信度
        """
        record = AllocationRecord(vector, action, target, confidence)
        self._allocation_history.append(record)
        if len(self._allocation_history) > 500:
            self._allocation_history = self._allocation_history[-500:]

        if action == "ASSIGN" and target and confidence >= self._defer_threshold:
            self._push_toward(vector, target, lr=self._assign_lr)
        elif action == "COMPOSITE" and confidence >= self._defer_threshold:
            if target:
                self._push_toward(vector, target, lr=self._assign_lr * 0.5)
        elif action == "DEFER":
            self._unclassified.append(vector[:])
            if len(self._unclassified) > 50:
                self._unclassified = self._unclassified[-50:]

    # =========================================================================
    # 觸發點 3: θ 自糾 → 錯誤修正
    # =========================================================================

    def on_misallocation_detected(
        self,
        input_vector: List[float],
        wrong_axis: str,
        right_axis: Optional[str],
        confidence: float,
    ) -> None:
        """
        每次 θ 自糾檢測到 misallocation 時調用

        Args:
            input_vector: 被錯誤分配的輸入向量
            wrong_axis: 被錯誤分配的軸
            right_axis: 應該分配到的軸（可選）
            confidence: θ 的置信度
        """
        record = MisallocationRecord(input_vector, wrong_axis, right_axis, confidence)
        self._misallocation_history.append(record)
        if len(self._misallocation_history) > 200:
            self._misallocation_history = self._misallocation_history[-200:]

        self._push_away(input_vector, wrong_axis, lr=self._misalloc_lr * confidence)
        if right_axis and right_axis != wrong_axis:
            self._push_toward(input_vector, right_axis, lr=self._misalloc_lr * confidence)

    # =========================================================================
    # 觸發點 4: 文本向量化 → 關鍵詞學習
    # =========================================================================

    def on_text_vectorized(
        self, text: str, vector: List[float], assigned_axis: Optional[str]
    ) -> None:
        """
        每次 text_to_vector 被調用並成功分配時

        Args:
            text: 原始文本
            vector: 生成的向量
            assigned_axis: 被分配的軸（可選）
        """
        if not assigned_axis:
            return
        words = text.lower().split()
        for word in words:
            if word not in self._keyword_axis_weights:
                self._keyword_axis_weights[word] = {
                    ax: 0.0 for ax in self._resonance._semantic_vectors
                }
            weights = self._keyword_axis_weights[word]
            if assigned_axis in weights:
                weights[assigned_axis] += 1.0

    # =========================================================================
    # 向量操作
    # =========================================================================

    def _ema_update(
        self, anchor: List[float], target: List[float], lr: float = 0.1
    ) -> List[float]:
        """
        EMA 更新錨點向量

        new = alpha * old + (1-alpha) * target
        其中 alpha = 1 - lr（即 lr 越大，anchor 調整越快）

        Args:
            anchor: 當前錨點向量
            target: 目標向量
            lr: 學習率（越大 = 錨點越接近目標）

        Returns:
            更新後的錨點向量（L2 正規化）
        """
        alpha = 1.0 - lr
        updated = [alpha * a + (1.0 - alpha) * t for a, t in zip(anchor, target)]
        return self._normalize(updated)

    def _push_toward(
        self, vector: List[float], axis_name: str, lr: float
    ) -> None:
        """將指定軸的錨點推向向量"""
        anchor = self._resonance._semantic_vectors.get(axis_name)
        if anchor:
            new_anchor = self._ema_update(anchor, vector, lr=lr)
            self._resonance._semantic_vectors[axis_name] = new_anchor

    def _push_away(
        self, vector: List[float], axis_name: str, lr: float
    ) -> None:
        """將指定軸的錨點遠離向量"""
        anchor = self._resonance._semantic_vectors.get(axis_name)
        if anchor:
            opposite = [-v for v in vector]
            new_anchor = self._ema_update(anchor, opposite, lr=lr)
            self._resonance._semantic_vectors[axis_name] = new_anchor

    def _snapshot_to_vector(
        self, snapshot: Dict[str, float], size: int = 32
    ) -> List[float]:
        """
        將軸快照轉換為 32-dim 向量

        方法：每個 field 的值 hash 到一個位置，
        field 值越大，該位置的權重越大。

        這與舊的 text_to_vector 不同：
        - text_to_vector: 詞頻 hash + 奇偶權重
        - snapshot_to_vector: field 值 hash（真實數值作為權重）

        結果：anchor 會朝向「平均穩定狀態」移動，
        自然豐富錨點的非零維度。
        """
        vector = [0.0] * size
        for field_name, value in snapshot.items():
            if value is None:
                continue
            normalized = max(0.0, min(1.0, value))
            pos = hash(field_name) % size
            vector[pos] += normalized

        return self._normalize(vector)

    def _normalize(self, vector: List[float]) -> List[float]:
        """L2 正規化"""
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 1e-10:
            return [v / norm for v in vector]
        return vector

    # =========================================================================
    # 查詢與報告
    # =========================================================================

    def get_similarity(self, vector: List[float], axis_name: str) -> float:
        """計算向量到指定軸的相似度（調用 ResonanceEngine）"""
        return self._resonance.compute_resonance(vector, axis_name)

    def get_all_similarities(self, vector: List[float]) -> Dict[str, float]:
        """計算向量到所有軸的相似度"""
        result = {}
        for axis_name in self._resonance._semantic_vectors:
            result[axis_name] = self._resonance.compute_resonance(vector, axis_name)
        return result

    def get_best_axis(self, vector: List[float]) -> str:
        """找到最佳匹配的軸"""
        sims = self.get_all_similarities(vector)
        if not sims:
            return ""
        return max(sims, key=sims.get)

    def get_learning_report(self) -> Dict[str, Any]:
        """獲取學習狀態報告"""
        anchor_stats = {}
        for ax, vec in self._resonance._semantic_vectors.items():
            nonzero = sum(1 for v in vec if abs(v) > 1e-6)
            magnitude = math.sqrt(sum(v * v for v in vec))
            anchor_stats[ax] = {
                "nonzero_dims": nonzero,
                "magnitude": round(magnitude, 4),
                "update_count": self._update_counts.get(ax, 0),
            }

        assign_count = sum(1 for r in self._allocation_history if r.action == "ASSIGN")
        defer_count = sum(1 for r in self._allocation_history if r.action == "DEFER")
        composite_count = sum(
            1 for r in self._allocation_history if r.action == "COMPOSITE"
        )

        return {
            "allocations": {
                "total": len(self._allocation_history),
                "assign": assign_count,
                "composite": composite_count,
                "defer": defer_count,
            },
            "misallocations": len(self._misallocation_history),
            "unclassified": len(self._unclassified),
            "keyword_vocabulary": len(self._keyword_axis_weights),
            "anchor_stats": anchor_stats,
            "ema_alpha": self._ema_alpha,
            "learning_interval": self._learning_interval,
        }

    def get_anchor_stats(self, axis_name: str) -> Dict[str, Any]:
        """獲取指定軸的錨點統計"""
        vec = self._resonance._semantic_vectors.get(axis_name)
        if vec is None:
            return {}
        nonzero = sum(1 for v in vec if abs(v) > 1e-6)
        magnitude = math.sqrt(sum(v * v for v in vec))
        return {
            "nonzero_dims": nonzero,
            "magnitude": round(magnitude, 4),
            "update_count": self._update_counts.get(axis_name, 0),
        }

    def get_top_keywords(self, axis_name: str, top_n: int = 10) -> List[tuple]:
        """獲取指定軸的最強關鍵詞"""
        if axis_name not in self._keyword_axis_weights:
            return []
        weights = self._keyword_axis_weights
        scored = [
            (word, w.get(axis_name, 0.0))
            for word, w in weights.items()
            if axis_name in w
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_n]

    def suggest_config_update(self) -> List[Dict[str, Any]]:
        """
        分析錨點學習數據，建議配置更新（寫入 learned_*.yaml）。

        觸發條件：
        - 某軸 keyword 學習次數 >= 10 次 → 建議新增意圖關鍵字
        - 某軸 misallocation 率 > 20% → 建議調整閾值
        - 某軸 更新次數 == 0 且有輸入 → 建議初始化錨點

        返回：建議列表（可安全地寫入 Learned 配置）
        """
        suggestions = []
        for axis in ("alpha", "beta", "gamma", "delta", "epsilon", "theta", "zeta", "eta"):
            kw = self.get_top_keywords(axis, top_n=5)
            if kw:
                strong_kw = [(w, s) for w, s in kw if s > 0.15]
                if strong_kw and self._update_counts.get(axis, 0) > 0:
                    suggestions.append({
                        "type": "intent_keyword",
                        "axis": axis,
                        "keywords": [w for w, _ in strong_kw],
                        "confidence": strong_kw[0][1],
                        "rationale": f"軸 {axis} 有 {len(strong_kw)} 個強關鍵字，置信度 > 0.15",
                    })

        misalloc_rate = len(self._misallocation_history) / max(1, len(self._allocation_history))
        if misalloc_rate > 0.2:
            suggestions.append({
                "type": "threshold_adjust",
                "metric": "misallocation_rate",
                "value": round(misalloc_rate, 3),
                "rationale": f"錯誤分配率 {misalloc_rate:.1%} 超過 20% 閾值",
            })

        return suggestions