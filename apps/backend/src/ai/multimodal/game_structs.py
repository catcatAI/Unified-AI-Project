"""
Game AI Data Structures - 共享結構定義
供 L0-L4 各層使用的標準化資料契約
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
import numpy as np


class SkillID(str, Enum):
    MOVE = "move"
    DIG = "dig"
    PLACE = "place"
    CRAFT = "craft"
    COMBAT = "combat"
    NAVIGATE = "navigate"
    EAT = "eat"
    BUILD = "build"
    LOOK = "look"


@dataclass
class SkillSpec:
    continuous_dim: int
    discrete_triggers: List[str]
    params: List[str]
    preconditions: List[str]
    duration_ticks: range
    description: str = ""


@dataclass
class SkillParams:
    skill_id: SkillID
    continuous_bias: np.ndarray
    discrete_triggers: Dict[str, float]
    termination_condition: str
    priority: float = 1.0
    params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.continuous_bias, np.ndarray):
            self.continuous_bias = np.array(self.continuous_bias, dtype=np.float32)


@dataclass
class SkillResult:
    skill_id: SkillID
    success: bool
    side_effects: List[str] = field(default_factory=list)
    next_suggested: List[str] = field(default_factory=list)
    duration_ticks: int = 0
    error: Optional[str] = None


@dataclass
class SkillTrigger:
    skill_id: SkillID
    confidence: float
    params: Dict[str, Any]
    urgency: float = 0.5


@dataclass
class SkillContext:
    active_skill: SkillID
    params: Dict[str, Any]
    priority: float
    interrupt_on: List[str] = field(default_factory=list)
    continuous_bias: Any = None
    discrete_triggers: Any = None


@dataclass
class Subgoal:
    subgoal_id: str
    skill_id: SkillID
    params: Dict[str, Any]
    preconditions: List[str]
    success_criteria: str
    timeout_ticks: int
    fallback: Optional[str] = None
    status: str = "pending"  # pending, active, completed, failed
    started_tick: Optional[int] = None


@dataclass
class TaskProgress:
    task_id: str
    completed: List[str] = field(default_factory=list)
    remaining: List[str] = field(default_factory=list)
    blocker: Optional[str] = None
    eta_ticks: int = 0
    current_subgoal: Optional[str] = None


@dataclass
class PlanDAG:
    plan_id: str
    root_goal: str
    nodes: Dict[str, Subgoal] = field(default_factory=dict)
    edges: List[Tuple[str, str]] = field(default_factory=list)  # (from, to)
    created_tick: int = 0


@dataclass
class StrategyDirective:
    exploration_weight: float = 0.5
    risk_tolerance: float = 0.5
    priority_goals: List[str] = field(default_factory=list)
    forbidden_actions: List[str] = field(default_factory=list)


@dataclass
class VisualObservation:
    """L0 輸出給 L1 的觀測結構"""

    frame_id: int
    timestamp: float
    features: np.ndarray  # (256,) visual encoder output
    fovea_xy: Tuple[int, int]  # 焦點位置 (原圖座標)
    inverse_map: Optional[np.ndarray] = None  # 座標逆映射矩陣
    raw_frame_shape: Tuple[int, int] = (0, 0)


@dataclass
class Proprioception:
    """本體感覺：生命值、飢餓、背包、位置、朝向等"""

    health: float = 20.0
    max_health: float = 20.0
    hunger: float = 20.0
    max_hunger: float = 20.0
    breath: float = 10.0
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    yaw: float = 0.0
    pitch: float = 0.0
    inventory: Dict[str, int] = field(default_factory=dict)
    wielded_item: str = ""
    is_on_ground: bool = True
    is_in_water: bool = False
    is_in_lava: bool = False
    light_level: int = 15

    # 別名屬性 (兼容性)
    @property
    def hp(self) -> float:
        return self.health

    @property
    def max_hp(self) -> float:
        return self.max_health


@dataclass
class GameState:
    """完整遊戲狀態快照，供各層讀取"""

    tick: int = 0
    timestamp: float = 0.0
    visual: Optional[VisualObservation] = None
    proprioception: Optional[Proprioception] = None
    task_progress: Optional[TaskProgress] = None
    plan: Optional[PlanDAG] = None
    strategy: Optional[StrategyDirective] = None


# 技能規格註冊表
GAME_SKILLS: Dict[SkillID, SkillSpec] = {
    SkillID.MOVE: SkillSpec(
        continuous_dim=3,
        discrete_triggers=["jump", "sprint", "sneak"],
        params=["forward", "strafe", "yaw"],
        preconditions=[],
        duration_ticks=range(1, 400),
        description="基礎移動：前進/後退/左右/跳躍/衝刺/潛行",
    ),
    SkillID.DIG: SkillSpec(
        continuous_dim=2,
        discrete_triggers=["attack"],
        params=["target_node", "direction", "tool"],
        preconditions=["has_tool:pickaxe"],
        duration_ticks=range(5, 200),
        description="挖掘方塊：需對應工具，持續按住 attack",
    ),
    SkillID.PLACE: SkillSpec(
        continuous_dim=2,
        discrete_triggers=["use"],
        params=["block_type", "face", "direction"],
        preconditions=["has_block:*"],
        duration_ticks=range(1, 20),
        description="放置方塊：需背包有對應方塊",
    ),
    SkillID.CRAFT: SkillSpec(
        continuous_dim=0,
        discrete_triggers=["inventory", "craft_grid", "craft_output"],
        params=["recipe_id", "count"],
        preconditions=["recipe_unlocked", "ingredients_in_inv"],
        duration_ticks=range(10, 60),
        description="合成物品：打開背包、放入材料、取出成品",
    ),
    SkillID.COMBAT: SkillSpec(
        continuous_dim=3,
        discrete_triggers=["attack", "block"],
        params=["target_entity", "weapon", "tactic"],
        preconditions=["hostile_in_range"],
        duration_ticks=range(10, 600),
        description="戰鬥：攻擊/格擋/閃避/走位",
    ),
    SkillID.NAVIGATE: SkillSpec(
        continuous_dim=3,
        discrete_triggers=["jump", "sprint"],
        params=["target_pos", "path"],
        preconditions=[],
        duration_ticks=range(10, 2000),
        description="導航到座標：避開障礙、跳躍、游泳",
    ),
    SkillID.EAT: SkillSpec(
        continuous_dim=0,
        discrete_triggers=["use"],
        params=["food_item"],
        preconditions=["hunger_low", "has_food"],
        duration_ticks=range(20, 40),
        description="進食：飢餓度低時自動執行",
    ),
    SkillID.BUILD: SkillSpec(
        continuous_dim=2,
        discrete_triggers=["use", "sneak"],
        params=["blueprint", "origin", "rotation"],
        preconditions=["has_materials", "space_available"],
        duration_ticks=range(100, 5000),
        description="按藍圖建造：依序放置方塊",
    ),
    SkillID.LOOK: SkillSpec(
        continuous_dim=2,
        discrete_triggers=[],
        params=["yaw", "pitch", "target"],
        preconditions=[],
        duration_ticks=range(1, 100),
        description="視線控制：注視目標、掃視環境",
    ),
}


def check_preconditions(skill_id: SkillID, state: GameState) -> Tuple[bool, List[str]]:
    """檢查技能前置條件"""
    spec = GAME_SKILLS[skill_id]
    failed = []
    inv = state.proprioception.inventory if state.proprioception else {}

    for cond in spec.preconditions:
        if cond.startswith("has_tool:"):
            tool = cond.split(":")[1]
            if not any(tool in k for k in inv.keys()):
                failed.append(f"缺少工具: {tool}")
        elif cond.startswith("has_block:"):
            block = cond.split(":")[1]
            if block != "*" and block not in inv:
                failed.append(f"缺少方塊: {block}")
        elif cond == "has_food":
            food_items = ["apple", "bread", "meat", "cooked", "carrot", "potato"]
            if not any(f in inv for f in food_items):
                failed.append("無食物")
        elif cond == "hunger_low":
            if (
                state.proprioception
                and state.proprioception.hunger > state.proprioception.max_hunger * 0.3
            ):
                failed.append("飢餓度未低")
        elif cond == "recipe_unlocked":
            # 簡化：假設基本配方都解鎖
            pass
        elif cond == "ingredients_in_inv":
            # 具體檢查在執行時做
            pass
        elif cond == "hostile_in_range":
            # 由視覺/實體感知判斷
            pass
        elif cond == "has_materials":
            pass
        elif cond == "space_available":
            pass

    return len(failed) == 0, failed


def get_available_skills(state: GameState) -> List[SkillID]:
    """取得當前狀態下可用的技能"""
    available = []
    for sid in SkillID:
        ok, _ = check_preconditions(sid, state)
        if ok:
            available.append(sid)
    return available
