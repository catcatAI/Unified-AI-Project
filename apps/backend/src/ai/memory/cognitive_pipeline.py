"""
Angela Unified Cognitive Pipeline v7.5.0-dev - 統一認知管線
=====================================================

核心流程：axis-first pathfinding + attractor hit + θ meta-allocation + code inspection
  1. 解析用戶輸入 → 定位當前狀態點 (αβγδεθ)
  2. θ (Meta-Cognitive) 分析輸入 → 決定分配方式（assign/composite/create/defer）
    3. 領域引擎計算結果（MathVerifier 為單一計算源；中文/%/ // 均正確）
    4. 僅對「有意義」的領域運算產生有界情緒/狀態（答對高興、重複降興致、等待、
       RPG/物理量/化學物種屬性高→高興）；無意義無狀態的算式不產生任何情緒/狀態。
       支援 math / physics / chemistry 領域引擎（見 ai.memory.domain_ripple）
  5. GradientField 計算梯度，定位最近的吸引子
  6. 沿梯度導航，觸發行為輸出
  7. 觸發 epsilon-influence → γ 情緒漣漪
  8. [v7.5.0-dev] CodeInspector 原生代碼檢查（0 LLM）

θ 軸職責：
  - 分析輸入與現有軸的語義相似度
  - 決定：高匹配→分配、模糊→組合、高新穎→創建、懸決→緩存
  - 追蹤 buffer_tracking，累積足够則觸發 creation_urge → 自動創建新軸

效率：5步 × 6維 ≈ 30億次操作
      vs LLM 576層 × 12288維 ≈ 2.1萬億

Author: Angela AI Development Team
Version: 6.2.1
"""

from __future__ import annotations

import logging
import re
from collections import deque
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from ai.memory.domain_ripple import apply_domain_cognition, route_domain

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Bounded domain cognition — single design point for "domain math -> emotion".
#
# Principle (per project direction):
#   * Meaningful computation (a user-posed problem, or math/domain computation
#     tied to a stateful attribute — RPG stat, physical quantity, chemical
#     species) MAY produce bounded emotional/state responses:
#       - joy at a correctly solved problem,
#       - reduced interest when the SAME problem is repeated,
#       - a transient "waiting / attending" state while resolving,
#       - happiness scaled by a high stateful value (big number = strong).
#   * Stateless, meaningless arithmetic ("917 * 814", "1+1") MUST NOT produce
#     any emotion or state change. It is computed, answered, and forgotten.
#
# The actual domain engines (math / physics / chemistry), the ripple shapes,
# the classification, and the bounded-cognition magnitudes all live in
# ``ai.memory.domain_ripple`` — this pipeline is just the orchestrator.
# ---------------------------------------------------------------------------

# How many recent expressions to remember for repetition detection.
_RECENT_MATH_WINDOW = 6


@dataclass
class AllocateDecision:
    action: str = ""
    confidence: float = 0.5
    reasoning: str = ""
    target: Optional[str] = None
    targets: Optional[List[str]] = None
    proposed_name: Optional[str] = None
    buffer: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CognitivePipeline:
    """統一認知管線 — 將輸入轉化為狀態更新和行為輸出。"""

    def __init__(
        self,
        state_matrix: Any = None,
        attractor_field: Any = None,
        math_ripple_engine: Any = None,
        code_inspector: Any = None,
    ):
        self.state_matrix = state_matrix
        self.attractor_field = attractor_field
        self.math_engine = math_ripple_engine
        self.code_inspector = code_inspector
        self._recent_math: deque = deque(maxlen=_RECENT_MATH_WINDOW)
        self._init_subsystems()

    def _init_subsystems(self) -> None:
        """初始化子系統（鈎子，供測試 mock）。"""
        pass

    def get_current_state(self) -> List[float]:
        """從 state_matrix 提取當前 5 維狀態向量。"""
        if self.state_matrix is None:
            return [0.5, 0.5, 0.5, 0.5, 0.5]

        sm = self.state_matrix
        alpha_vals = getattr(sm.alpha, "values", {}) if hasattr(sm, "alpha") else {}
        beta_vals = getattr(sm.beta, "values", {}) if hasattr(sm, "beta") else {}
        gamma_vals = getattr(sm.gamma, "values", {}) if hasattr(sm, "gamma") else {}
        delta_vals = getattr(sm.delta, "values", {}) if hasattr(sm, "delta") else {}
        epsilon_vals = getattr(sm.epsilon, "values", {}) if hasattr(sm, "epsilon") else {}

        def _first_val(d: Dict[str, float], default: float = 0.5) -> float:
            return next(iter(d.values()), default)

        return [
            _first_val(alpha_vals),
            _first_val(beta_vals),
            _first_val(gamma_vals),
            _first_val(delta_vals),
            _first_val(epsilon_vals),
        ]

    def _extract_label(self, text: str) -> str:
        """從文本提取關鍵詞標籤。"""
        words = re.findall(r"[a-zA-Z]+", text)
        filtered = [w.lower() for w in words if len(w) > 2]
        return " ".join(filtered[:8])

    # ------------------------------------------------------------------
    # Domain cognition — the ONLY place domain math produces emotion/state.
    # Delegates compute + ripple shape + bounded cognitions to domain_ripple.
    # ------------------------------------------------------------------

    def _apply_domain_cognition(
        self, engine, text: str, value: float, cls: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply bounded, meaningful-only domain cognitions.

        Delegates to the SINGLE shared entry point ``apply_domain_cognition``
        (ai.memory.domain_ripple) so the lab pipeline and the production chat
        dual-rail can never diverge. Stateless math returns {"meaningful":
        False} and touches NO state/emotion.
        """
        if not cls.get("meaningful"):
            # Stateless arithmetic: compute + answer only. No emotion/state.
            return {"meaningful": False}

        # NOTE: classify for repetition must use the *previous* window, so we
        # pass ``self._recent_math`` to apply_domain_cognition BEFORE appending
        # this text. Appending first would make apply_domain_cognition
        # re-classify the current input as a repetition of itself (false
        # positive). We append only after the cognition pass has run.
        applied = apply_domain_cognition(self.state_matrix, text, self._recent_math)
        self._recent_math.append(text.strip())
        return {
            "meaningful": True,
            "domain": cls.get("domain"),
            "attribute": cls.get("attribute"),
            "is_repetition": cls.get("is_repetition"),
            "applied": applied.get("applied", False),
        }

    async def process(self, text: str, user_name: Optional[str] = None) -> Dict[str, Any]:
        """處理輸入文本，返回響應字典。"""
        state = self.get_current_state()
        math_result = None
        tone = "warm"
        math_cognition = None

        # Domain analysis via the router (math / physics / chemistry engines).
        # Stateless arithmetic is computed but produces NO emotion/state.
        # Meaningful computation (problem / stateful attribute) gets bounded
        # ripple + cognitions.
        engine, value, cls = route_domain(text, self._recent_math)
        if value is not None:
            math_result = value
            math_cognition = self._apply_domain_cognition(engine, text, value, cls)

        # Attractor field navigation (T3, heavy). Only run for MEANINGFUL domain
        # input — stateless arithmetic must NOT pay the ~1ms navigation cost
        # (§11.6 / §11.9 B5). This is the lab-level fast-path; the same gate is
        # mirrored by the production dual-rail in chat_routes._try_math_verification.
        if self.attractor_field is not None and math_cognition and math_cognition.get("meaningful"):
            nav_result = self.attractor_field.navigate(state, max_steps=5, dt=0.15)
            if isinstance(nav_result, tuple):
                nav_state, behavior_result = nav_result
                state = nav_state
                response = behavior_result.blended_behavior
                tone_val = behavior_result.blended_tone
                tone = tone_val.value if hasattr(tone_val, "value") else str(tone_val)
                nav_steps = behavior_result.navigation_steps
                certainty = behavior_result.certainty
            else:
                response = nav_result.blended_behavior
                tone_val = nav_result.blended_tone
                tone = tone_val.value if hasattr(tone_val, "value") else str(tone_val)
                nav_steps = nav_result.navigation_steps
                certainty = nav_result.certainty

            if math_result is not None:
                response = f"計算結果是 {math_result}。（我的狀態很穩定）"

            return {
                "response": response,
                "navigation_steps": nav_steps,
                "state": state,
                "tone": tone,
                "certainty": certainty,
                "math_result": math_result,
                "math_cognition": math_cognition,
            }

        # Fallback: no attractor field
        if math_result is not None:
            return {
                "response": f"計算結果是 {math_result}。（我的狀態很穩定）",
                "navigation_steps": 0,
                "state": state,
                "tone": tone,
                "math_result": math_result,
                "math_cognition": math_cognition,
            }

        return {
            "response": "我聽到了。",
            "navigation_steps": 0,
            "state": state,
            "tone": tone,
            "math_result": math_result,
            "math_cognition": math_cognition,
        }

    def query_attractors(self, state: Optional[List[float]] = None) -> List[Any]:
        """查詢當前狀態附近的吸引子。"""
        if self.attractor_field is None:
            return []
        query_state = state if state is not None else self.get_current_state()
        result = self.attractor_field.compute_gradient(query_state)
        return result.nearest_attractors if result.nearest_attractors else []


__all__ = ["AllocateDecision", "CognitivePipeline"]
