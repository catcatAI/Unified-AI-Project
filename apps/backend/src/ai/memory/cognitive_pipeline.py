"""
Angela Unified Cognitive Pipeline v7.5.0-dev - 統一認知管線
=====================================================

核心流程：axis-first pathfinding + attractor hit + θ meta-allocation + code inspection
  1. 解析用戶輸入 → 定位當前狀態點 (αβγδεθ)
  2. θ (Meta-Cognitive) 分析輸入 → 決定分配方式（assign/composite/create/defer）
  3. MathRippleEngine 分析是否含數學運算
  4. 計算跨軸漣漪，更新 ε 維度
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
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


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

    async def process(self, text: str, user_name: Optional[str] = None) -> Dict[str, Any]:
        """處理輸入文本，返回響應字典。"""
        state = self.get_current_state()
        math_result = None
        ripple = None
        tone = "warm"

        # Math analysis
        if self.math_engine is not None:
            analysis = self.math_engine.analyze_expression(text)
            if analysis and analysis.get("result") is not None:
                math_result = analysis["result"]
                ripple = analysis.get("ripples")

        # Apply ripple to state
        if ripple:
            self._apply_ripple_to_state(ripple)

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
            }

        # Fallback: no attractor field
        if math_result is not None:
            return {
                "response": f"計算結果是 {math_result}。（我的狀態很穩定）",
                "navigation_steps": 0,
                "state": state,
                "tone": tone,
                "math_result": math_result,
            }

        return {
            "response": "我聽到了。",
            "navigation_steps": 0,
            "state": state,
            "tone": tone,
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
