"""
Cognitive Operations — StateMatrix4D 空間推理與意圖系統
=========================================================

提取自 state_matrix.py 的空間推理相關功能：
- 原生空間推理 (Native Spatial Reasoning)
- 數學表達式評估 (Mathematical Expression Evaluation)
- 意圖重力系統 (Intent Gravity System)
- 維度連動拖拽 (Inter-Dimensional Drag)

Author: Angela AI v6.2
Version: 6.4.0
"""

from __future__ import annotations

import logging
import math
import re
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class CognitiveOp(Enum):
    """
    原生空間運算類型，將抽象數學邏輯轉化為幾何變換。
    Native spatial operations that transform abstract logic into geometry.
    """
    ACCUMULATE = auto()
    DECREMENT = auto()
    AMPLIFY = auto()
    DIMINISH = auto()
    RESONATE = auto()


# [auto] spatial ratio: controls how much each axis participates in operations
# X is primary axis (1.0), Y and Z are secondary with reduced sensitivity
# Can be overridden per operation via state_matrix config
SPATIAL_RATIO: Tuple[float, float, float] = (1.0, 0.3, 0.15)


def compute_spatial_influence_factor(
    dimensions: Dict[str, Any], source: str, target: str
) -> float:
    """
    [Task N.20.1] 向量場計算 / Vector Field Computation
    Calculates the spatial distance and influence factor between two dimensions
    in the coordinate-based cognitive space.
    """
    source_coord = dimensions[source].coordinate
    target_coord = dimensions[target].coordinate

    distance = sum((a - b) ** 2 for a, b in zip(source_coord, target_coord)) ** 0.5

    softening = _get_spatial_config("influence_factor_softening", 10.0)
    numerator = _get_spatial_config("influence_factor_numerator", 25.0)
    influence_factor = numerator / (distance**2 + softening)

    return max(0.5, min(2.0, influence_factor))


def perform_spatial_reasoning(
    dimensions: Dict[str, Any],
    target_dim: str,
    op: CognitiveOp,
    magnitude: float,
    ratio: Tuple[float, float, float] = SPATIAL_RATIO,
) -> Tuple[float, float, float]:
    """執行原生空間推理（X 主軸 + 設定檔控制副軸敏感度）"""
    if target_dim not in dimensions:
        return (0.0, 0.0, 0.0)

    state = dimensions[target_dim]
    x, y, z = state.coordinate

    rx, ry, rz = ratio

    if op == CognitiveOp.ACCUMULATE:
        new_coord = (x + magnitude * rx, y + magnitude * ry, z + magnitude * rz)
    elif op == CognitiveOp.DECREMENT:
        new_coord = (x - magnitude * rx, y - magnitude * ry, z - magnitude * rz)
    elif op == CognitiveOp.AMPLIFY:
        new_coord = (x * magnitude, y, z)
    elif op == CognitiveOp.DIMINISH:
        dmag = magnitude if magnitude != 0 else 1.0
        new_coord = (x / dmag, y, z)
    else:
        new_coord = (x, y, z)

    state.coordinate = new_coord

    logger.info(f"[SpatialReasoning] {target_dim} moved to {new_coord} via {op.name}({magnitude}) ratio={ratio}")
    return new_coord


def get_dimension_value(dimensions: Dict[str, Any], dim_name: str) -> float:
    """獲取維度的「標量解析」(取 X 軸作為結果)"""
    if dim_name in dimensions:
        return dimensions[dim_name].coordinate[0]
    return 0.0


def get_position(dimensions: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """獲取所有維度的當前座標"""
    return {
        name: {
            "x": state.coordinate[0],
            "y": state.coordinate[1],
            "z": state.coordinate[2]
        }
        for name, state in dimensions.items()
    }


def execute_thought_chain(
    dimensions: Dict[str, Any],
    dimension: str,
    instructions: List[Tuple[CognitiveOp, float]]
) -> float:
    """
    [Task N.20.5] 執行認知操作鏈
    在指定維度上依序執行一系列空間變換。
    """
    result = 0.0
    for op, magnitude in instructions:
        new_coord = perform_spatial_reasoning(dimensions, dimension, op, magnitude)
        result = new_coord[0]

    return result


def evaluate_math_spatially(dimensions: Dict[str, Any]) -> Callable[[str], float]:
    """
    [L4-Reasoning] 將數學算式原生解析為空間變換。
    Returns a closure that evaluates math expressions using epsilon dimension.
    """
    def evaluator(expression: str) -> float:
        """Log a diagnostic message."""
        logger.info(f"[SpatialMath] Resolving expression: {expression}")

        tokens = re.findall(r"\d+\.?\d*|\*\*|[\+\-\*\/\(\)]", expression)

        precedence = _get_spatial_config("operator_precedence", {"+": 1, "-": 1, "*": 2, "/": 2, "**": 3})
        output_queue = []
        operator_stack = []

        for token in tokens:
            if re.match(r"\d+\.?\d*", token):
                output_queue.append(float(token))
            elif token == "(":
                operator_stack.append(token)
            elif token == ")":
                while operator_stack and operator_stack[-1] != "(":
                    output_queue.append(operator_stack.pop())
                operator_stack.pop()
            else:
                while (operator_stack and operator_stack[-1] != "(" and
                       precedence[operator_stack[-1]] >= precedence[token]):
                    output_queue.append(operator_stack.pop())
                operator_stack.append(token)

        while operator_stack:
            output_queue.append(operator_stack.pop())

        execution_stack = []

        if "epsilon" in dimensions:
            comp_div = _get_spatial_config("complexity_divisor", 20.0)
            dimensions["epsilon"].values["complexity"] = min(1.0, len(expression) / comp_div)

        for token in output_queue:
            if isinstance(token, float):
                execution_stack.append(token)
            else:
                b = execution_stack.pop()
                a = execution_stack.pop()

                if "epsilon" in dimensions:
                    ey, ez = dimensions["epsilon"].coordinate[1], dimensions["epsilon"].coordinate[2]
                    dimensions["epsilon"].coordinate = (a, ey, ez)

                if token == "+":
                    op = CognitiveOp.ACCUMULATE
                elif token == "-":
                    op = CognitiveOp.DECREMENT
                elif token == "*":
                    op = CognitiveOp.AMPLIFY
                elif token == "/":
                    op = CognitiveOp.DIMINISH
                elif token == "**":
                    execution_stack.append(a ** b)
                    continue
                else:
                    op = CognitiveOp.ACCUMULATE

                new_coord = perform_spatial_reasoning(dimensions, "epsilon", op, b)
                execution_stack.append(new_coord[0])

        final_result = execution_stack[0] if execution_stack else 0.0

        if "epsilon" in dimensions:
            cert_base = _get_spatial_config("certainty_base", 0.5)
            cert_char = _get_spatial_config("certainty_per_char", 0.05)
            fat_inc = _get_spatial_config("fatigue_increment", 0.02)
            dimensions["epsilon"].values["certainty"] = min(
                1.0, cert_base + cert_char * len(expression)
            )
            dimensions["epsilon"].values["fatigue"] = min(
                1.0, dimensions["epsilon"].values.get("fatigue", 0.0) + fat_inc
            )

        logger.info(
            f"[SpatialMath] Epsilon calculation: {expression} = {final_result}"
        )
        return final_result

    return evaluator


def _get_spatial_config(key: str, default: Any) -> Any:
    """從 spatial_parameters.yaml 獲取配置"""
    try:
        from app_config_loader import get_formula_config
        spatial_conf = get_formula_config("spatial")
        return spatial_conf.get("gravity", {}).get(key, default)
    except Exception:
        logger.warning(f"_get_spatial_config({key}) from formula config failed, using default", exc_info=True)
        return default


class PotentialFieldEngine:
    """
    位能場引擎 / Potential Field Engine
    使用梯度下降法計算座標位移。
    """
    
    @staticmethod
    def calculate_attractive_displacement(
        current: Tuple[float, float, float],
        target: Tuple[float, float, float],
        pull_factor: float,
        threshold: Optional[float] = None
    ) -> Tuple[float, float, float]:
        """
        計算吸引力產生的位移。
        採用 Huber-like 位能場。
        """
        if threshold is None:
            threshold = _get_spatial_config("intent_gravity_threshold", 0.001)
        delta = _get_spatial_config("huber_delta", 0.5)
        
        cx, cy, cz = current
        tx, ty, tz = target
        
        dx, dy, dz = tx - cx, ty - cy, tz - cz
        dist = math.sqrt(dx**2 + dy**2 + dz**2)
        
        if dist < threshold:
            return (0.0, 0.0, 0.0)
            
        if dist > delta:
            force_mag = pull_factor * delta
        else:
            force_mag = pull_factor * dist
            
        nx = (dx / dist) * force_mag
        ny = (dy / dist) * force_mag
        nz = (dz / dist) * force_mag
        
        return (nx, ny, nz)


def apply_intent_gravity(dimensions: Dict[str, Any], pull_factor: Optional[float] = None) -> None:
    """
    將各個維度的座標向其「意圖向量」拉近。
    [Task N.26.3] 升級為位能場模型。
    """
    if pull_factor is None:
        pull_factor = _get_spatial_config("intent_gravity_pull", 0.05)
    
    engine = PotentialFieldEngine()
    
    for name, state in dimensions.items():
        dx, dy, dz = engine.calculate_attractive_displacement(
            state.coordinate,
            state.intent_vector,
            pull_factor
        )
        
        if dx != 0 or dy != 0 or dz != 0:
            cx, cy, cz = state.coordinate
            state.coordinate = (cx + dx, cy + dy, cz + dz)


def set_intent_target(dimensions: Dict[str, Any], dimension: str, target: Tuple[float, float, float]) -> None:
    """設置維度的目標意圖座標"""
    if dimension in dimensions:
        dimensions[dimension].intent_vector = target
        logger.debug(f"[IntentGravity] {dimension} target set to {target}")


def apply_inter_dimensional_drag(
    dimensions: Dict[str, Any], trigger_dim: str, drag_factor: Optional[float] = None
) -> None:
    """
    [Task N.21.7] 維度連動拖拽
    升級為位能場耦合模型。
    """
    if drag_factor is None:
        drag_factor = _get_spatial_config("inter_dimensional_drag", 0.02)
        
    if trigger_dim not in dimensions:
        return

    trigger_coord = dimensions[trigger_dim].coordinate
    engine = PotentialFieldEngine()

    for name, state in dimensions.items():
        if name == trigger_dim:
            continue

        dx, dy, dz = engine.calculate_attractive_displacement(
            state.coordinate,
            trigger_coord,
            drag_factor
        )
        
        if dx != 0 or dy != 0 or dz != 0:
            cx, cy, cz = state.coordinate
            state.coordinate = (cx + dx, cy + dy, cz + dz)