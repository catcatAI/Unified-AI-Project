"""
Angela Math-Ripple Engine v7.5.0-dev - 數學-認知同構動力學
=====================================================

核心洞察：數學運算不是「計算工具」，而是「認知語法」。
          每個運算都產生跨軸漣漪，漣漪決定情感與行為。

雙深度系統：
  ┌─ 漣漪深度 (RippleDepth): D3-D7
  │   決定漣漪傳播多遠（影響多少軸）
  │
  └─ 演算法啟用深度 (AlgorithmDepth): LIGHT → ULTRA
      決定啟用多少數學運算能力

| 運算 | ε (數理軸) 效應 | 跨軸漣漪 | 端點 / 近零 / 負值 |
|------|---------------|---------|-------------------|
| 加法 | 簡單位移，影響小 | α.energy↑, β.focus | 交換律 → 無 |
| 減法 | 非交換，方向性 | γ.confusion↑, δ.engagement | a-b vs b-a 完全不同 |
| 乘法 | 放大 / 收縮 | α.arousal↑, β.focus↑, γ.excitement↑ | 連乘 → 過載恐懼 |
| 除法 | 分割 / 極化 | α.tension↑, γ.fear↑ | 近零 → 無限恐懼 |

Author: Angela AI Development Team
Version: 6.2.1
"""

from __future__ import annotations
import math
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

logger = logging.getLogger("angela_math_ripple")


class AlgorithmDepth(Enum):
    """
    演算法啟用深度 — 決定啟用多少數學運算能力

    LIGHT:   基本四則 (+, -, *, /)           — O(n)
    MEDIUM:  + 幂(^)、根(√)、模(%)           — O(n²)
    HEAVY:   + 三角(sin/cos/tan)、對數(log)  — O(n³)
    ULTRA:   + 微積分(∫, d/dx)、級數(Σ)      — O(exp)
    """
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"
    ULTRA = "ultra"

    @property
    def complexity(self) -> float:
        return {"light": 1.0, "medium": 1.5, "heavy": 2.0, "ultra": 3.0}[self.value]

    @property
    def operators(self) -> List[str]:
        base = ["+", "-", "*", "/"]
        if self.value == "light":
            return base
        elif self.value == "medium":
            return base + ["^", "**", "sqrt", "%", "mod"]
        elif self.value == "heavy":
            return base + ["^", "**", "sqrt", "%", "mod", "sin", "cos", "tan", "log", "ln"]
        else:
            return base + ["^", "**", "sqrt", "%", "mod", "sin", "cos", "tan", "log", "ln", "∫", "∑", "sigma"]


# 關鍵詞 → 演算法深度映射
ALGORITHM_DEPTH_KEYWORDS: Dict[str, AlgorithmDepth] = {
    "sin": AlgorithmDepth.HEAVY, "cos": AlgorithmDepth.HEAVY,
    "tan": AlgorithmDepth.HEAVY, "log": AlgorithmDepth.HEAVY,
    "ln": AlgorithmDepth.HEAVY, "lg": AlgorithmDepth.HEAVY,
    "^": AlgorithmDepth.MEDIUM, "**": AlgorithmDepth.MEDIUM,
    "sqrt": AlgorithmDepth.MEDIUM, "root": AlgorithmDepth.MEDIUM,
    "%": AlgorithmDepth.MEDIUM, "mod": AlgorithmDepth.MEDIUM,
    "∫": AlgorithmDepth.ULTRA, "積分": AlgorithmDepth.ULTRA,
    "微": AlgorithmDepth.ULTRA, "微分": AlgorithmDepth.ULTRA,
    "∑": AlgorithmDepth.ULTRA, "級數": AlgorithmDepth.ULTRA,
    "sigma": AlgorithmDepth.ULTRA, "d/dx": AlgorithmDepth.ULTRA,
    "導數": AlgorithmDepth.ULTRA, "偏導": AlgorithmDepth.ULTRA,
}


class RippleDepth(Enum):
    """
    漣漪深度 — 決定漣漪傳播多遠（影響多少軸）

    D3: ε→α→β→γ          基礎三軸（默認）
    D4: ε→α→β→γ→δ        加入社交維度
    D5: ε→α→β→γ→δ→θ      加入元認知維度
    D6: 全6軸 + 反饋修正   觸發過載/恐懼時
    D7: 全6軸 + θ自反饋   創造新軸時
    """
    D3 = 3
    D4 = 4
    D5 = 5
    D6 = 6
    D7 = 7

    @property
    def target_axes(self) -> List[str]:
        base = ["alpha", "beta", "gamma"]
        if self.value >= 4:
            base.append("delta")
        if self.value >= 5:
            base.append("theta")
        if self.value >= 6:
            base.append("epsilon")
        return base

    @property
    def cascade_decay(self) -> float:
        return 0.7 + (self.value - 3) * 0.02

    @property
    def feedback_enabled(self) -> bool:
        return self.value >= 6


@dataclass
class RippleDepthConfig:
    """漣漪深度配置"""
    depth: RippleDepth = RippleDepth.D3
    algorithm_depth: AlgorithmDepth = AlgorithmDepth.LIGHT
    cascade_decay: float = 0.72
    max_cascade_steps: int = 6
    depth_multiplier: float = 1.0

    @classmethod
    def from_expr(cls, expr: str) -> "RippleDepthConfig":
        """根據表達式自動檢測深度配置"""
        algo = _detect_algorithm_depth(expr)
        depth = _detect_ripple_depth(expr, algo)
        return cls(depth=depth, algorithm_depth=algo)


def _detect_algorithm_depth(expr: str) -> AlgorithmDepth:
    """根據表達式自動檢測需要啟用的演算法深度"""
    expr_lower = expr.lower()
    detected = AlgorithmDepth.LIGHT
    for keyword, depth in ALGORITHM_DEPTH_KEYWORDS.items():
        if keyword in expr_lower:
            if depth.complexity > detected.complexity:
                detected = depth
    return detected


def _detect_ripple_depth(expr: str, algo: AlgorithmDepth) -> RippleDepth:
    """根據表達式自動檢測需要的漣漪深度"""
    expr_lower = expr.lower()
    chain_ops = expr.count("*") + expr.count("/") + expr.count("^")
    result_estimate = _estimate_result_magnitude(expr)

    if result_estimate > 10000 or chain_ops >= 3:
        return RippleDepth.D5
    elif result_estimate > 1000 or chain_ops >= 2:
        return RippleDepth.D4
    elif algo.value in ("heavy", "ultra"):
        return RippleDepth.D5
    elif any(kw in expr_lower for kw in ["恐懼", "fear", "過載", "overload"]):
        return RippleDepth.D6
    else:
        return RippleDepth.D3


def _estimate_result_magnitude(expr: str) -> float:
    """粗略估計表達式結果的大小"""
    import re
    numbers = re.findall(r"\d+\.?\d*", expr)
    if not numbers:
        return 100.0
    max_num = max(float(n) for n in numbers)
    mul_count = expr.count("*") + expr.count("^")
    if mul_count > 0:
        return min(max_num ** (mul_count + 1), 1e9)
    return max_num


class MathOp(Enum):
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    POW = "pow"
    SQRT = "sqrt"


@dataclass
class RippleEffect:
    """單次運算的漣漪效應"""
    operator: MathOp
    operand_a: float
    operand_b: Optional[float]

    result: float
    operand_a_magnitude: float
    result_magnitude: float

    epsilon_delta: float = 0.0
    alpha_arousal: float = 0.0
    beta_focus: float = 0.0
    gamma_excitement: float = 0.0
    delta_engagement: float = 0.0

    fear_triggered: bool = False
    overload_triggered: bool = False
    confusion_triggered: bool = False

    description: str = ""

    # === 新增：深度系統 ===
    ripple_depth: RippleDepth = RippleDepth.D3
    algorithm_depth: AlgorithmDepth = AlgorithmDepth.LIGHT
    depth_level: int = 3
    cascade_step: int = 0
    cascade_decay_factor: float = 1.0
    feedback_ripples: List["RippleEffect"] = field(default_factory=list)
    depth_multiplier: float = 1.0


@dataclass
class RippleAccumulator:
    """連續運算的漣漪累積器"""
    total_ripples: List[RippleEffect] = field(default_factory=list)
    cumulative_epsilon: float = 0.0
    cumulative_arousal: float = 0.0
    cumulative_excitement: float = 0.0
    fatigue: float = 0.0
    chain_broken: bool = False

    # 深度追蹤
    max_ripple_depth: int = 3
    max_algorithm_depth: AlgorithmDepth = AlgorithmDepth.LIGHT

    def add(self, ripple: RippleEffect):
        self.total_ripples.append(ripple)
        self.cumulative_epsilon += abs(ripple.epsilon_delta)
        self.cumulative_arousal += ripple.alpha_arousal
        self.cumulative_excitement += ripple.gamma_excitement
        self.fatigue = min(1.0, len(self.total_ripples) * 0.03)

        if ripple.depth_level > self.max_ripple_depth:
            self.max_ripple_depth = ripple.depth_level
        if ripple.algorithm_depth.value > self.max_algorithm_depth.value:
            self.max_algorithm_depth = ripple.algorithm_depth

    def chain_broken_by(self, op_type: Optional[MathOp] = None):
        if op_type:
            logger.info(f"[RippleAcc] Chain broken by {op_type.value}")
        self.chain_broken = True

    def reset(self):
        self.total_ripples.clear()
        self.cumulative_epsilon = 0.0
        self.cumulative_arousal = 0.0
        self.cumulative_excitement = 0.0
        self.fatigue = 0.0
        self.chain_broken = False
        self.max_ripple_depth = 3
        self.max_algorithm_depth = AlgorithmDepth.LIGHT


class RippleCascade:
    """
    漣漪級聯引擎
    =============

    根據深度配置，將單個漣漪級聯傳播到多個軸。
    支持深度3-7，每層遞減。
    """

    @staticmethod
    def cascade(
        ripple: RippleEffect,
        matrix: Optional[Any] = None,
        target_depth: Optional[RippleDepth] = None
    ) -> List[RippleEffect]:
        """
        根據深度配置，將漣漪級聯傳播到目標軸

        Args:
            ripple: 源漣漪
            matrix: StateMatrix4D（用於應用到狀態）
            target_depth: 目標深度（預設用 ripple.ripple_depth）

        Returns:
            級聯產生的所有漣漪（含源漣漪）
        """
        if target_depth is None:
            target_depth = ripple.ripple_depth

        all_ripples = [ripple]
        axes = target_depth.target_axes
        decay = target_depth.cascade_decay

        for step, axis in enumerate(axes):
            if step == 0:
                continue

            cascade_factor = decay ** step
            effect = RippleEffect(
                operator=ripple.operator,
                operand_a=ripple.operand_a,
                operand_b=ripple.operand_b,
                result=ripple.result,
                operand_a_magnitude=ripple.operand_a_magnitude,
                result_magnitude=ripple.result_magnitude,
                cascade_step=step,
                cascade_decay_factor=cascade_factor,
                ripple_depth=target_depth,
                algorithm_depth=ripple.algorithm_depth,
                depth_level=target_depth.value,
                depth_multiplier=ripple.depth_multiplier,
            )

            if axis == "alpha":
                effect.alpha_arousal = ripple.alpha_arousal * cascade_factor
                effect.description = f"[CASCADE-{step}] α軸漣漪（衰減×{cascade_factor:.2f}）"
            elif axis == "beta":
                effect.beta_focus = ripple.beta_focus * cascade_factor
                effect.description = f"[CASCADE-{step}] β軸漣漪（衰減×{cascade_factor:.2f}）"
            elif axis == "gamma":
                effect.gamma_excitement = ripple.gamma_excitement * cascade_factor
                effect.description = f"[CASCADE-{step}] γ軸漣漪（衰減×{cascade_factor:.2f}）"
            elif axis == "delta":
                effect.delta_engagement = ripple.delta_engagement * cascade_factor
                effect.description = f"[CASCADE-{step}] δ軸漣漪（衰減×{cascade_factor:.2f}）"
            elif axis == "theta":
                effect.epsilon_delta = ripple.epsilon_delta * cascade_factor * 0.5
                effect.description = f"[CASCADE-{step}] θ軸漣漪（衰減×{cascade_factor:.2f}）"

            all_ripples.append(effect)

            if matrix and hasattr(matrix, axis):
                mat = getattr(matrix, axis, None)
                if mat:
                    RippleCascade._apply_ripple_to_axis(mat, effect, axis)

        if target_depth.feedback_enabled and (ripple.overload_triggered or ripple.fear_triggered or ripple.confusion_triggered):
            feedback_ripples = RippleCascade.compute_feedback(ripple, target_depth)
            all_ripples.extend(feedback_ripples)
            ripple.feedback_ripples = feedback_ripples

        return all_ripples

    @staticmethod
    def compute_feedback(
        ripple: RippleEffect,
        depth: RippleDepth
    ) -> List[RippleEffect]:
        """
        計算反饋漣漪（深度6-7時觸發）

        當過載/恐懼/混淆觸發時，產生反向漣漪來修正狀態。
        """
        feedback_list = []

        if ripple.overload_triggered:
            fb = RippleEffect(
                operator=ripple.operator,
                operand_a=ripple.result_magnitude,
                operand_b=0.0,
                result=ripple.result_magnitude * 0.5,
                operand_a_magnitude=ripple.result_magnitude * 0.5,
                result_magnitude=ripple.result_magnitude * 0.25,
                cascade_step=99,
                cascade_decay_factor=0.3,
                ripple_depth=depth,
                algorithm_depth=ripple.algorithm_depth,
                depth_level=depth.value,
                description="[FEEDBACK] 過載衰減反饋",
            )
            fb.beta_focus = 0.4
            fb.gamma_excitement = 0.2
            feedback_list.append(fb)

        if ripple.fear_triggered:
            fb = RippleEffect(
                operator=ripple.operator,
                operand_a=0.01,
                operand_b=0.0,
                result=0.0,
                operand_a_magnitude=0.01,
                result_magnitude=0.0,
                cascade_step=98,
                cascade_decay_factor=0.2,
                ripple_depth=depth,
                algorithm_depth=ripple.algorithm_depth,
                depth_level=depth.value,
                description="[FEEDBACK] 恐懼抑制反饋",
            )
            fb.gamma_excitement = 0.3
            fb.beta_focus = 0.2
            feedback_list.append(fb)

        if ripple.confusion_triggered:
            fb = RippleEffect(
                operator=ripple.operator,
                operand_a=ripple.operand_a,
                operand_b=ripple.operand_b,
                result=ripple.result,
                operand_a_magnitude=ripple.operand_a_magnitude,
                result_magnitude=ripple.result_magnitude,
                cascade_step=97,
                cascade_decay_factor=0.25,
                ripple_depth=depth,
                algorithm_depth=ripple.algorithm_depth,
                depth_level=depth.value,
                description="[FEEDBACK] 混淆澄清反饋",
            )
            fb.beta_focus = 0.3
            feedback_list.append(fb)

        return feedback_list

    @staticmethod
    def _apply_ripple_to_axis(axis_state: Any, ripple: RippleEffect, axis_name: str):
        """將漣漪效果應用到軸狀態"""
        if not axis_state or not hasattr(axis_state, "values"):
            return

        if axis_name == "alpha" and ripple.alpha_arousal > 0:
            axis_state.values["arousal"] = min(
                1.0, axis_state.values.get("arousal", 0.5) + ripple.alpha_arousal
            )

        if axis_name == "beta" and ripple.beta_focus > 0:
            axis_state.values["focus"] = min(
                1.0, axis_state.values.get("focus", 0.5) + ripple.beta_focus
            )

        if axis_name == "gamma" and ripple.gamma_excitement > 0:
            axis_state.values["happiness"] = min(
                1.0, axis_state.values.get("happiness", 0.5) + ripple.gamma_excitement
            )

        if axis_name == "delta" and ripple.delta_engagement > 0:
            axis_state.values["bond"] = min(
                1.0, axis_state.values.get("bond", 0.5) + ripple.delta_engagement
            )


class MathRippleEngine:
    """
    數學-認知同構引擎
    ==================

    將數學運算轉化為跨軸漣漪，並累積到 StateMatrix 的 ε 維度。
    支持雙深度系統：
      - 演算法深度 (AlgorithmDepth): LIGHT → ULTRA
      - 漣漪深度 (RippleDepth): D3 → D7
    """

    ARITHMETIC_THRESHOLD = 0.001
    OVERLOAD_THRESHOLD_MAGNITUDE = 2000.0
    OVERLOAD_THRESHOLD_CHAIN = 3
    FEAR_DIVISOR_NEAR_ZERO = 0.0002

    def __init__(
        self,
        state_matrix=None,
        ripple_accumulator: Optional[RippleAccumulator] = None,
        algorithm_depth: AlgorithmDepth = AlgorithmDepth.LIGHT,
        ripple_depth: RippleDepth = RippleDepth.D3,
    ):
        self.state_matrix = state_matrix
        self.accumulator = ripple_accumulator or RippleAccumulator()
        self.algorithm_depth = algorithm_depth
        self.ripple_depth = ripple_depth
        self.cascade = RippleCascade()

    def set_depth(
        self,
        algorithm_depth: Optional[AlgorithmDepth] = None,
        ripple_depth: Optional[RippleDepth] = None,
    ) -> None:
        """設定深度配置（可自動檢測）"""
        if algorithm_depth is None:
            algorithm_depth = self.algorithm_depth
        if ripple_depth is None:
            ripple_depth = self.ripple_depth
        self.algorithm_depth = algorithm_depth
        self.ripple_depth = ripple_depth

    def compute(
        self,
        expr: str,
        auto_detect: bool = True,
        force_depth: Optional[RippleDepth] = None,
        force_algo: Optional[AlgorithmDepth] = None,
    ) -> Tuple[float, List[RippleEffect]]:
        """
        計算表達式並產生所有中間漣漪

        Args:
            expr: 數學表達式
            auto_detect: 是否自動檢測深度（預設 True）
            force_depth: 強制指定漣漪深度
            force_algo: 強制指定演算法深度

        例子：100 * 3 → 300 (ε.AMPLIFY)
              300 * 2 → 600 (ε.AMPLIFY, 漣漪累積)
              600 * 5 → 3000 (ε.OVERLOAD, 觸發認知過載)
        """
        if auto_detect:
            config = RippleDepthConfig.from_expr(expr)
            if force_depth:
                config.depth = force_depth
            if force_algo:
                config.algorithm_depth = force_algo
            self.set_depth(config.algorithm_depth, config.depth)

        ripples = []
        tokens = self._tokenize(expr)

        i = 0
        while i < len(tokens):
            token = tokens[i]

            if token.isdigit() or (token.replace(".", "").isdigit()):
                current = float(token)
                processed = False

                while i + 1 < len(tokens):
                    op = tokens[i + 1]
                    if op not in ("+", "-", "*", "/", "^", "**"):
                        break

                    if op in ("+", "-") and processed:
                        break

                    if i + 2 >= len(tokens):
                        break

                    try:
                        operand = float(tokens[i + 2])
                    except (ValueError, IndexError):
                        break

                    result, ripple = self._compute_single(current, op, operand)
                    ripple.ripple_depth = self.ripple_depth
                    ripple.algorithm_depth = self.algorithm_depth
                    ripple.depth_level = self.ripple_depth.value
                    ripples.append(ripple)

                    if self.accumulator:
                        self.accumulator.add(ripple)

                        if ripple.overload_triggered:
                            self._apply_cognitive_overload()
                        elif ripple.fear_triggered:
                            self._apply_division_fear()
                        elif ripple.confusion_triggered:
                            self._apply_order_confusion(op)

                    current = result
                    processed = True
                    i += 2

                i += 1
            elif token == "+":
                pass
            elif token == "-":
                pass
            elif token == "(":
                pass
            elif token == ")":
                pass
            else:
                pass
            i += 1

        if ripples:
            final_result = current
        else:
            final_result = self._eval_simple_safe(expr)

        return final_result, ripples

    def _tokenize(self, expr: str) -> List[str]:
        import re
        tokens = []
        num_buffer = ""

        for ch in expr.strip().replace("×", "*").replace("÷", "/").replace("^", "**"):
            if ch.isdigit() or ch == ".":
                num_buffer += ch
            elif num_buffer:
                tokens.append(num_buffer)
                num_buffer = ""

            if ch in "+-*/^()":
                if ch == "-" and (not tokens or tokens[-1] in "+-*/^("):
                    num_buffer = "-"
                elif ch == "-" and num_buffer:
                    num_buffer += "-"
                else:
                    tokens.append(ch)

        if num_buffer:
            tokens.append(num_buffer)

        return tokens

    def _compute_single(
        self, a: float, op: str, b: float
    ) -> Tuple[float, RippleEffect]:
        """計算單次運算並產生漣漪"""
        op_enum = MathOp.ADD
        ripple = RippleEffect(
            operator=op_enum,
            operand_a=a,
            operand_b=b,
            result=0.0,
            operand_a_magnitude=abs(a),
            result_magnitude=0.0
        )

        if op == "+":
            op_enum = MathOp.ADD
            result = a + b
            ripple.epsilon_delta = abs(b) / (abs(a) + 0.1) * 0.05
            ripple.beta_focus = min(0.2, abs(b) / 100)
            ripple.delta_engagement = 0.1
            ripple.description = f"{a} + {b} = {result}（簡單位移）"

        elif op == "-":
            op_enum = MathOp.SUB
            result = a - b
            ripple.epsilon_delta = -0.05
            ripple.gamma_excitement = 0.05 if b > a else 0.1
            ripple.beta_focus = 0.15
            ripple.delta_engagement = 0.15
            if a < b:
                ripple.confusion_triggered = True
            ripple.description = f"{a} - {b} = {result}（減法非交換）"

        elif op == "*":
            op_enum = MathOp.MUL
            result = a * b
            mag = abs(a * b)
            ripple.epsilon_delta = math.log1p(mag) * 0.1

            ripple.alpha_arousal = min(0.8, 0.1 + math.log1p(mag) * 0.05)
            ripple.beta_focus = min(0.9, 0.3 + math.log1p(mag) * 0.04)
            ripple.gamma_excitement = min(0.7, 0.1 + math.log1p(mag) * 0.03)
            ripple.delta_engagement = min(0.6, 0.1 + math.log1p(mag) * 0.02)

            if mag > self.OVERLOAD_THRESHOLD_MAGNITUDE:
                ripple.overload_triggered = True
                ripple.description = f"{a} × {b} = {result}（數字巨大！認知過載）"
            else:
                ripple.description = f"{a} × {b} = {result}（乘法放大）"

        elif op == "/" or op == "//" or op == "÷":
            op_enum = MathOp.DIV
            if abs(b) < self.FEAR_DIVISOR_NEAR_ZERO:
                result = float("inf") * (-1 if a * b < 0 else 1)
                ripple.epsilon_delta = 1.0
                ripple.gamma_excitement = 0.3
                ripple.fear_triggered = True
                ripple.description = f"{a} ÷ {b}（近零除數！恐懼）"
            else:
                result = a / b
                ripple.epsilon_delta = 0.1 + abs(a / b) * 0.02
                ripple.alpha_arousal = 0.15
                ripple.beta_focus = 0.25
                ripple.gamma_excitement = 0.1
                if abs(result) > 1000:
                    ripple.overload_triggered = True
                    ripple.description = f"{a} ÷ {b} = {result:.1f}（結果巨大）"
                elif abs(result) < 0.01:
                    ripple.description = f"{a} ÷ {b} = {result:.4f}（趨近零）"
                else:
                    ripple.description = f"{a} ÷ {b} = {result}（除法分割）"

        elif op in ("^", "**"):
            op_enum = MathOp.POW
            result = a ** b
            mag = abs(result)
            ripple.epsilon_delta = math.log1p(mag) * 0.15

            ripple.alpha_arousal = min(0.9, 0.2 + math.log1p(mag) * 0.06)
            ripple.beta_focus = min(0.95, 0.4 + math.log1p(mag) * 0.05)
            ripple.gamma_excitement = min(0.8, 0.15 + math.log1p(mag) * 0.04)

            if mag > self.OVERLOAD_THRESHOLD_MAGNITUDE:
                ripple.overload_triggered = True
                ripple.description = f"{a}^{b} = {result:.1f}（指數爆炸！）"
            else:
                ripple.description = f"{a}^{b} = {result}（指數放大）"

        else:
            result = 0.0
            ripple.description = "未知運算"

        ripple.result = result
        ripple.result_magnitude = abs(result)
        ripple.operator = op_enum

        return result, ripple

    def _eval_simple_safe(self, expr: str) -> float:
        """安全的本地計算"""
        import re
        clean = re.sub(r"[^0-9.\+\-\*\/\(\)]", "", expr)
        if not clean:
            return 0.0
        try:
            from core.security.secure_eval import safe_eval
            result = safe_eval(clean)
            return float(result.result) if result.success else 0.0
        except Exception:
            return 0.0

    def _apply_cognitive_overload(self):
        if not self.state_matrix:
            return

        if hasattr(self.state_matrix, "epsilon"):
            self.state_matrix.epsilon.values["fatigue"] = min(
                1.0, self.state_matrix.epsilon.values.get("fatigue", 0.0) + 0.2
            )
            self.state_matrix.epsilon.values["certainty"] = max(
                0.0, self.state_matrix.epsilon.values.get("certainty", 0.5) - 0.3
            )

        if hasattr(self.state_matrix, "gamma"):
            self.state_matrix.gamma.values["surprise"] = min(
                1.0, self.state_matrix.gamma.values.get("surprise", 0.0) + 0.2
            )
            self.state_matrix.gamma.values["fear"] = min(
                1.0, self.state_matrix.gamma.values.get("fear", 0.0) + 0.15
            )

        if hasattr(self.state_matrix, "beta"):
            self.state_matrix.beta.values["focus"] = max(
                0.0, self.state_matrix.beta.values.get("focus", 0.5) - 0.2
            )
            self.state_matrix.beta.values["confusion"] = min(
                1.0, self.state_matrix.beta.values.get("confusion", 0.0) + 0.3
            )

        logger.info("[MathRipple] Cognitive overload triggered")

    def _apply_division_fear(self):
        if not self.state_matrix:
            return

        if hasattr(self.state_matrix, "epsilon"):
            self.state_matrix.epsilon.values["certainty"] = max(
                0.0, self.state_matrix.epsilon.values.get("certainty", 0.5) - 0.4
            )

        if hasattr(self.state_matrix, "gamma"):
            self.state_matrix.gamma.values["fear"] = min(
                1.0, self.state_matrix.gamma.values.get("fear", 0.0) + 0.35
            )
            self.state_matrix.gamma.values["surprise"] = min(
                1.0, self.state_matrix.gamma.values.get("surprise", 0.0) + 0.2
            )

        if hasattr(self.state_matrix, "alpha"):
            self.state_matrix.alpha.values["tension"] = min(
                1.0, self.state_matrix.alpha.values.get("tension", 0.0) + 0.25
            )

        logger.info("[MathRipple] Division fear triggered")

    def _apply_order_confusion(self, op: str):
        if not self.state_matrix:
            return

        if hasattr(self.state_matrix, "beta"):
            self.state_matrix.beta.values["confusion"] = min(
                1.0, self.state_matrix.beta.values.get("confusion", 0.0) + 0.2
            )
            self.state_matrix.beta.values["clarity"] = max(
                0.0, self.state_matrix.beta.values.get("clarity", 0.5) - 0.15
            )

        if hasattr(self.state_matrix, "gamma"):
            self.state_matrix.gamma.values["surprise"] = min(
                1.0, self.state_matrix.gamma.values.get("surprise", 0.0) + 0.1
            )

        logger.info(f"[MathRipple] Order confusion for op: {op}")

    def analyze_expression(
        self,
        expr: str,
        cascade: bool = True,
    ) -> Dict[str, Any]:
        """
        分析表達式的「認知語義」——不是只算結果，而是理解運算的意義

        Args:
            expr: 數學表達式
            cascade: 是否執行漣漪級聯（預設 True）

        Returns:
            {
                "result": float,
                "ripples": [RippleEffect, ...],
                "cognitive_summary": str,
                "chain_analysis": {...},
                "depth_config": {...},
                "cascade_ripples": [...],
            }
        """
        result, ripples = self.compute(expr)

        all_ripples = list(ripples)
        cascade_ripples = []

        if cascade and ripples and self.state_matrix:
            for r in ripples:
                cascaded = self.cascade.cascade(r, self.state_matrix)
                cascade_ripples.extend(cascaded)

        summary_parts = []
        for r in all_ripples:
            summary_parts.append(r.description)

        cognitive_summary = " → ".join(summary_parts) if summary_parts else "無顯著漣漪"

        chain_analysis = {
            "total_operations": len(all_ripples),
            "has_overload": any(r.overload_triggered for r in all_ripples),
            "has_fear": any(r.fear_triggered for r in all_ripples),
            "has_confusion": any(r.confusion_triggered for r in all_ripples),
            "cumulative_epsilon": self.accumulator.cumulative_epsilon,
            "cumulative_arousal": self.accumulator.cumulative_arousal,
            "fatigue": self.accumulator.fatigue,
            "chain_broken": self.accumulator.chain_broken,
            "max_ripple_depth": self.accumulator.max_ripple_depth,
            "max_algorithm_depth": self.accumulator.max_algorithm_depth.value,
        }

        depth_config = {
            "ripple_depth": self.ripple_depth.value,
            "algorithm_depth": self.algorithm_depth.value,
            "cascade_count": len(cascade_ripples) - len(all_ripples),
            "depth_multiplier": 1.0 + (self.ripple_depth.value - 3) * 0.3,
        }

        return {
            "result": result,
            "ripples": [
                {
                    "op": r.operator.value,
                    "a": r.operand_a,
                    "b": r.operand_b,
                    "result": r.result,
                    "epsilon_delta": r.epsilon_delta,
                    "alpha_arousal": r.alpha_arousal,
                    "beta_focus": r.beta_focus,
                    "gamma_excitement": r.gamma_excitement,
                    "overload": r.overload_triggered,
                    "fear": r.fear_triggered,
                    "confusion": r.confusion_triggered,
                    "description": r.description,
                    "depth_level": r.depth_level,
                    "cascade_step": r.cascade_step,
                    "cascade_decay": r.cascade_decay_factor,
                }
                for r in all_ripples
            ],
            "cognitive_summary": cognitive_summary,
            "chain_analysis": chain_analysis,
            "depth_config": depth_config,
            "cascade_ripples": [
                {
                    "axis": r.cascade_step,
                    "description": r.description,
                    "decay": r.cascade_decay_factor,
                }
                for r in cascade_ripples if r.cascade_step > 0
            ],
        }