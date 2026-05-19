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
from typing import Dict, Tuple, List, Any, Callable
from enum import Enum, auto
import re
import logging


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

    softening = 10.0
    influence_factor = 25.0 / (distance**2 + softening)

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
        logger.info(f"[SpatialMath] Resolving expression: {expression}")

        tokens = re.findall(r"\d+\.?\d*|[\+\-\*\/\(\)]", expression)

        precedence = {"+": 1, "-": 1, "*": 2, "/": 2}
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
            dimensions["epsilon"].values["complexity"] = min(1.0, len(expression) / 20.0)

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
                else:
                    op = CognitiveOp.ACCUMULATE

                new_coord = perform_spatial_reasoning(dimensions, "epsilon", op, b)
                execution_stack.append(new_coord[0])

        final_result = execution_stack[0] if execution_stack else 0.0

        if "epsilon" in dimensions:
            dimensions["epsilon"].values["certainty"] = min(
                1.0, 0.5 + 0.05 * len(expression)
            )
            dimensions["epsilon"].values["fatigue"] = min(
                1.0, dimensions["epsilon"].values.get("fatigue", 0.0) + 0.02
            )

        logger.info(
            f"[SpatialMath] Epsilon calculation: {expression} = {final_result}"
        )
        return final_result

    return evaluator


def apply_intent_gravity(dimensions: Dict[str, Any], pull_factor: float = 0.05) -> None:
    """將各個維度的座標向其「意圖向量」緩緩拉近"""
    for name, state in dimensions.items():
        tx, ty, tz = state.intent_vector
        cx, cy, cz = state.coordinate

        if abs(tx - cx) > 0.001 or abs(ty - cy) > 0.001 or abs(tz - cz) > 0.001:
            nx = cx + (tx - cx) * pull_factor
            ny = cy + (ty - cy) * pull_factor
            nz = cz + (tz - cz) * pull_factor
            state.coordinate = (nx, ny, nz)


def set_intent_target(dimensions: Dict[str, Any], dimension: str, target: Tuple[float, float, float]) -> None:
    """設置維度的目標意圖座標"""
    if dimension in dimensions:
        dimensions[dimension].intent_vector = target
        logger.debug(f"[IntentGravity] {dimension} target set to {target}")


def apply_inter_dimensional_drag(
    dimensions: Dict[str, Any], trigger_dim: str, drag_factor: float = 0.02
) -> None:
    """
    [Task N.21.7] 維度連動拖拽
    當一個維度移動時，會將其他維度也往相同方向「拉動」一點點。
    """
    if trigger_dim not in dimensions:
        return

    tx, ty, tz = dimensions[trigger_dim].coordinate

    for name, state in dimensions.items():
        if name == trigger_dim:
            continue

        cx, cy, cz = state.coordinate
        nx = cx + (tx - cx) * drag_factor
        ny = cy + (ty - cy) * drag_factor
        nz = cz + (tz - cz) * drag_factor
        state.coordinate = (nx, ny, nz)