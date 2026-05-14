"""
Resonance Engine — 語義共振統一引擎
====================================

所有軸的相似度計算通過這裡：
- 計算向量與軸的共振度
- 找最佳軸 / 複合軸
- 計算跨軸不確定性（entropy）

使用方式:
    from core.allocation.resonance import ResonanceEngine

    engine = ResonanceEngine(axes=[alpha, beta, gamma, delta, epsilon])
    resonance = engine.compute_resonance(vector, target=alpha)
    best_axis = engine.find_best_axis(vector)

Author: Angela AI v6.2
Version: 6.2.1
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import math
import logging

logger = logging.getLogger("angela_resonance")


@dataclass
class ResonanceResult:
    """共振計算結果"""
    axis_name: str
    resonance: float
    confidence: float

    def __repr__(self) -> str:
        return f"Resonance({self.axis_name}={self.resonance:.3f}, conf={self.confidence:.2f})"


@dataclass
class ResonanceProfile:
    """完整共振配置"""
    similarities: Dict[str, float]
    best_axis: Optional[str]
    max_resonance: float
    num_high_sim: int
    entropy: float
    active_count: int

    def __repr__(self) -> str:
        best_str = f"best={self.best_axis}({self.max_resonance:.2f})" if self.best_axis else "no_match"
        return f"Profile({best_str}, high_sim={self.num_high_sim}, entropy={self.entropy:.3f})"


class ResonanceEngine:
    """
    語義共振引擎
    ============

    將向量映射到軸空間，計算每個軸的匹配程度。
    支持 cosine similarity 和 weighted resonance。
    """

    def __init__(self, axes: Optional[List["Axis"]] = None):
        self._axes: Dict[str, "Axis"] = {}
        self._semantic_vectors: Dict[str, List[float]] = {}
        if axes:
            for axis in axes:
                self.register_axis(axis)
        else:
            self.init_default_anchors()

    def init_default_anchors(self) -> None:
        """
        從 6 個軸的 field 定義初始化 semantic anchors

        方法：多通道語意向量構建
          - channel 0: field name 哈希（3個位置，用 default 加權）
          - channel 1: field description 分詞哈希（5個位置）
          - channel 2: axis label + cn_name 哈希（3個位置）
          - channel 3: field label 哈希（2個位置）

        結果：每個軸 ~13 個非零維度（對比舊方法的 ~5-8）
        通過 AnchorLearningEngine 的 EMA 更新逐步豐富。
        """
        from core.state.axis_field import AxisFieldRegistry
        reg = AxisFieldRegistry()
        for axis_name in reg.all_axes():
            fields = reg.fields_for(axis_name)
            vector = [0.0] * 32

            for f in fields:
                weight = f.default + 0.3

                p0 = hash(f.name) % 32
                p1 = (hash(f.name + '_A') % 31) + 1
                p2 = (hash(f.name + '_B') % 30) + 2
                vector[p0] += weight * 0.6
                vector[p1] += weight * 0.3
                vector[p2] += weight * 0.1

                desc_words = f.description.lower().split()
                for i, word in enumerate(desc_words[:4]):
                    pos = (hash(word + axis_name) % 31) + 1
                    vector[pos] += 0.15 * (1.0 / (i + 1))

                for i, word in enumerate(f.label.lower().split()[:2]):
                    pos = (hash(word + '_label') % 31) + 1
                    vector[pos] += 0.1

            for word in [axis_name, "cognitive", "emotional", "social", "mathematical", "meta"]:
                pos = (hash(word + '_axis') % 31) + 1
                vector[pos] += 0.15

            vector = self._normalize(vector)
            self._semantic_vectors[axis_name] = vector

            nonzero = sum(1 for v in vector if abs(v) > 0.01)
            logger.debug(f"[Resonance] {axis_name}: {nonzero} non-zero dims")

    def _normalize(self, vector: List[float]) -> List[float]:
        """L2 正規化"""
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 1e-10:
            return [v / norm for v in vector]
        return vector

    def register_axis(self, axis: "Axis") -> None:
        """註冊一個軸及其語義向量"""
        self._axes[axis.name] = axis
        if hasattr(axis, '_semantic_vector') and axis._semantic_vector:
            self._semantic_vectors[axis.name] = axis._semantic_vector
        elif hasattr(axis, 'semantic_anchor') and hasattr(axis.semantic_anchor, 'semantic_vector'):
            self._semantic_vectors[axis.name] = list(axis.semantic_anchor.semantic_vector)
        else:
            axis_label = getattr(axis, 'label', None) or getattr(axis, 'cn_name', axis.name)
            field_names = axis.field_names() if hasattr(axis, 'field_names') else list(getattr(axis, 'values', {}).keys())
            semantic_text = axis_label + " " + " ".join(field_names)
            self._semantic_vectors[axis.name] = self._text_to_vector(semantic_text, 32)

    def _text_to_vector(self, text: str, size: int) -> List[float]:
        """將文本轉換為低維語義向量"""
        from core.state.text_to_vector import text_to_vector as ttv
        return ttv(text, size)

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """計算兩個向量的 cosine similarity"""
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a < 1e-10 or norm_b < 1e-10:
            return 0.0
        return dot / (norm_a * norm_b)

    def compute_resonance(self, vector: List[float], target_name: str) -> float:
        """
        計算向量與目標軸的共振度

        Args:
            vector: 輸入向量（32維）
            target_name: 目標軸名

        Returns:
            共振度 [0, 1]
        """
        if target_name not in self._semantic_vectors:
            return 0.0
        anchor = self._semantic_vectors[target_name]
        return max(0.0, self._cosine_similarity(vector, anchor))

    def find_best_axis(self, vector: List[float]) -> Tuple[Optional[str], float]:
        """
        找到共振度最高的軸

        Returns:
            (axis_name, resonance)
        """
        if not self._axes:
            return None, 0.0

        similarities = {name: self.compute_resonance(vector, name) for name in self._axes}
        if not similarities:
            return None, 0.0

        best_name = max(similarities, key=similarities.get)
        return best_name, similarities[best_name]

    def find_composite_axes(
        self,
        vector: List[float],
        threshold: float = 0.3,
        top_k: Optional[int] = None
    ) -> List[Tuple[str, float]]:
        """
        找到共振度超過閾值的多個軸

        Args:
            vector: 輸入向量
            threshold: 最低共振度閾值
            top_k: 最多返回多少個（None=全部）

        Returns:
            [(axis_name, resonance), ...] 按共振度降序
        """
        similarities = {
            name: self.compute_resonance(vector, name)
            for name in self._axes
        }
        filtered = [(n, s) for n, s in similarities.items() if s >= threshold]
        filtered.sort(key=lambda x: -x[1])
        if top_k:
            filtered = filtered[:top_k]
        return filtered

    def compute_entropy(self, vector: List[float]) -> float:
        """
        計算跨軸的不確定性（entropy）

        用於 θ 的 ambiguity 測量：
        - entropy 低 → 某個軸明顯主導
        - entropy 高 → 分散在多個軸，不確定
        """
        if not self._axes:
            return 1.0

        similarities = [self.compute_resonance(vector, name) for name in self._axes]
        total = sum(similarities)
        if total < 1e-10:
            return 1.0

        probs = [s / total for s in similarities]
        entropy = -sum(p * math.log(p + 1e-10) for p in probs if p > 0)

        max_entropy = math.log(len(probs) + 1e-10)
        if max_entropy > 0:
            entropy /= max_entropy

        return entropy

    def compute_profile(self, vector: List[float]) -> ResonanceProfile:
        """
        計算完整共振配置

        返回包含所有關鍵指標的 ResonanceProfile
        """
        similarities = {
            name: self.compute_resonance(vector, name)
            for name in self._axes
        }

        best_name = None
        max_sim = 0.0
        for name, sim in similarities.items():
            if sim > max_sim:
                max_sim = sim
                best_name = name

        num_high = sum(1 for s in similarities.values() if s > 0.5)
        active_count = sum(1 for s in similarities.values() if s > 0.1)

        entropy = self.compute_entropy(vector)

        return ResonanceProfile(
            similarities=similarities,
            best_axis=best_name,
            max_resonance=max_sim,
            num_high_sim=num_high,
            entropy=entropy,
            active_count=active_count,
        )

    def update_semantic_vector(self, axis_name: str, vector: List[float]) -> None:
        """更新某個軸的語義向量"""
        self._semantic_vectors[axis_name] = vector
        if axis_name in self._axes and hasattr(self._axes[axis_name], '_semantic_vector'):
            self._axes[axis_name]._semantic_vector = vector

    def get_all_resonances(self, vector: List[float]) -> Dict[str, float]:
        """取得所有軸的共振度字典"""
        return {name: self.compute_resonance(vector, name) for name in self._axes}

    def __repr__(self) -> str:
        return f"ResonanceEngine(axes={list(self._axes.keys())})"


from core.state.axis import Axis