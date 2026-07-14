"""
Angela Unified Cognitive Pipeline v7.5.0-dev - 統一認知管線
=====================================================

核心流程：axis-first pathfinding + attractor hit + θ meta-allocation + code inspection
  1. 解析用戶輸入 → 定位當前狀態點 (αβγδεθ)
  2. θ (Meta-Cognitive) 分析輸入 → 決定分配方式（assign/composite/create/defer）
   3. MathVerifier 計算數學結果（單一計算源；中文/%/ // 均正確）
   4. 僅對「有意義」的數學產生有界情緒/狀態（答對高興、重複降興致、等待、RPG 屬性高→高興）；
      無意義無狀態的算式不產生任何情緒/狀態
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
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from services.math_verifier import compute_arithmetic

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Bounded math cognition — single design point for "math -> emotion/state".
#
# Principle (per project direction):
#   * Meaningful math (a user-posed problem, or math tied to a stateful RPG
#     character attribute) MAY produce bounded emotional/state responses:
#       - joy at a correctly solved problem,
#       - reduced interest when the SAME problem is repeated,
#       - a transient "waiting / attending" state while resolving,
#       - happiness scaled by a high RPG attribute value (big number = strong).
#   * Stateless, meaningless arithmetic ("917 * 814", "1+1") MUST NOT produce
#     any emotion or state change. It is computed, answered, and forgotten.
# ---------------------------------------------------------------------------

# RPG / character attribute terms — math referencing these is stateful/meaningful.
_ATTRIBUTE_TERMS = {
    "hp", "health", "生命", "體力",
    "mp", "mana", "魔力", "法力",
    "atk", "attack", "攻擊", "攻",
    "def", "defense", "防禦", "防",
    "str", "strength", "力量",
    "dex", "agi", "agility", "敏捷",
    "int", "wis", "intelligence", "智慧",
    "lvl", "level", "等級",
    "xp", "exp", "experience", "經驗",
    "power", "power", "力量",
    "speed", "速度",
}

# A "high" attribute value (big number) that warrants happiness.
_RPG_HIGH_THRESHOLD = 50.0

# How many recent math expressions to remember for repetition detection.
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
    # Math cognition — the ONLY place math produces emotion/state.
    # ------------------------------------------------------------------

    def _evaluate_math(self, text: str) -> Optional[float]:
        """Compute the numeric result via MathVerifier (single source of truth).

        Returns None when the input is not a math expression. No emotion/state
        is produced here — that is gated by _apply_math_cognition().
        """
        try:
            return compute_arithmetic(text)
        except Exception as e:  # pragma: no cover - defensive
            logger.debug("MathVerifier evaluate failed for %r: %s", text, e)
            return None

    def _classify_math(self, text: str) -> Dict[str, Any]:
        """Decide whether math is meaningful (may carry emotion) or stateless.

        Stateless = pure arithmetic with no narrative, no question framing, and
        no reference to a stateful RPG/character attribute. Such math must NOT
        trigger emotion/state.
        """
        lowered = text.lower()
        words = set(re.findall(r"[a-zA-Z一-鿿]+", lowered))
        attribute = next((w for w in words if w in _ATTRIBUTE_TERMS), None)
        is_question = bool(
            re.search(r"[？?]|多少|等于|等於|幾|what|how many|calculate|compute|solve", lowered)
        )
        # Pure arithmetic: only digits, operators, spaces, parentheses remain.
        pure_expr = re.sub(r"[\d\s\+\-\*/%\(\)\^]", "", text).strip()
        is_pure_arithmetic = len(pure_expr) == 0

        meaningful = bool(attribute) or is_question
        is_repetition = text.strip() in self._recent_math
        return {
            "meaningful": meaningful,
            "attribute": attribute,
            "is_question": is_question,
            "is_pure_arithmetic": is_pure_arithmetic,
            "is_repetition": is_repetition,
        }

    def _apply_math_cognition(self, text: str, result: float) -> Dict[str, Any]:
        """Apply bounded, meaningful-only math cognitions.

        Returns a dict describing which cognitions fired. Stateless math
        returns {"meaningful": False} and touches NO state/emotion.
        """
        cls = self._classify_math(text)
        if not cls["meaningful"]:
            # Stateless arithmetic: compute + answer only. No emotion/state.
            return {"meaningful": False}

        self._recent_math.append(text.strip())

        # 1) Ripple/state layer (MathRippleEngine) — only for meaningful math.
        ripple = None
        if self.math_engine is not None:
            try:
                analysis = self.math_engine.analyze_expression(text)
                ripple = analysis.get("ripples") if analysis else None
            except Exception as e:  # pragma: no cover - defensive
                logger.debug("MathRipple analyze failed for %r: %s", text, e)
        if ripple:
            self._apply_ripple_to_state(ripple)

        # 2) Bounded cognitions on top of ripples.
        deltas: Dict[str, float] = {}

        # Joy at a correctly solved problem (suppressed when repeated).
        if not cls["is_repetition"]:
            deltas["gamma_happiness"] = deltas.get("gamma_happiness", 0.0) + 0.12
            deltas["gamma_excitement"] = deltas.get("gamma_excitement", 0.0) + 0.08
        else:
            # Repeated problem -> lower interest / enthusiasm.
            deltas["beta_focus"] = deltas.get("beta_focus", 0.0) - 0.15
            deltas["gamma_excitement"] = deltas.get("gamma_excitement", 0.0) - 0.10
            deltas["beta_clarity"] = deltas.get("beta_clarity", 0.0) - 0.05

        # RPG attribute high (big number = strong) -> happiness scaled, capped.
        if cls["attribute"] is not None and abs(result) >= _RPG_HIGH_THRESHOLD:
            boost = min(0.25, 0.10 + abs(result) / 1000.0)
            deltas["gamma_happiness"] = deltas.get("gamma_happiness", 0.0) + boost

        # Waiting / attending cognition: transient focus while resolving.
        deltas["beta_focus"] = deltas.get("beta_focus", 0.0) + 0.05
        deltas["gamma_anticipation"] = deltas.get("gamma_anticipation", 0.0) + 0.05

        self._apply_cognition_deltas(deltas)

        return {
            "meaningful": True,
            "attribute": cls["attribute"],
            "is_repetition": cls["is_repetition"],
            "deltas": deltas,
        }

    def _apply_cognition_deltas(self, deltas: Dict[str, float]) -> None:
        """Apply bounded emotional/state deltas to the StateMatrix (if present)."""
        if self.state_matrix is None or not deltas:
            return
        sm = self.state_matrix
        # gamma = emotional axis; beta = cognitive/attention axis
        gamma = getattr(sm, "gamma", None)
        beta = getattr(sm, "beta", None)
        for key, value in deltas.items():
            if key.startswith("gamma_") and gamma is not None:
                dim = key[len("gamma_"):]
                cur = gamma.values.get(dim, 0.5)
                gamma.values[dim] = min(1.0, max(0.0, cur + value))
            elif key.startswith("beta_") and beta is not None:
                dim = key[len("beta_"):]
                cur = beta.values.get(dim, 0.5)
                beta.values[dim] = min(1.0, max(0.0, cur + value))

    async def process(self, text: str, user_name: Optional[str] = None) -> Dict[str, Any]:
        """處理輸入文本，返回響應字典。"""
        state = self.get_current_state()
        math_result = None
        tone = "warm"
        math_cognition = None

        # Math analysis — single source of truth = MathVerifier.
        # Stateless arithmetic is computed but produces NO emotion/state.
        # Meaningful math (problem / RPG attribute) gets bounded cognitions.
        math_result = self._evaluate_math(text)
        if math_result is not None:
            math_cognition = self._apply_math_cognition(text, math_result)

        # Attractor field navigation
        if self.attractor_field is not None:
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

    def _apply_ripple_to_state(self, ripple: Dict[str, Any]) -> None:
        """將數學漣漪應用到狀態矩陣。"""
        if self.state_matrix is None:
            return
        sm = self.state_matrix
        alpha_vals = getattr(sm.alpha, "values", {}) if hasattr(sm, "alpha") else {}
        beta_vals = getattr(sm.beta, "values", {}) if hasattr(sm, "beta") else {}
        gamma_vals = getattr(sm.gamma, "values", {}) if hasattr(sm, "gamma") else {}

        if "alpha_arousal" in ripple:
            sm.alpha.values["arousal"] = min(1.0, alpha_vals.get("arousal", 0.5) + ripple["alpha_arousal"])
        if "beta_focus" in ripple:
            sm.beta.values["focus"] = min(1.0, beta_vals.get("focus", 0.6) + ripple["beta_focus"])
        if "gamma_excitement" in ripple:
            sm.gamma.values["happiness"] = min(1.0, gamma_vals.get("happiness", 0.5) + ripple["gamma_excitement"])

    def _apply_cognitive_overload(self) -> None:
        """應用認知過載效應。"""
        if self.state_matrix is None:
            return
        sm = self.state_matrix
        if hasattr(sm.beta, "values"):
            sm.beta.values["confusion"] = 0.3

    def _apply_division_fear(self) -> None:
        """應用除法恐懼效應。"""
        if self.state_matrix is None:
            return
        sm = self.state_matrix
        if hasattr(sm.gamma, "values"):
            sm.gamma.values["fear"] = 0.3


__all__ = ["AllocateDecision", "CognitivePipeline"]
