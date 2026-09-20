"""
Game Planner - L3 規劃推理層

功能：
- 目標分解為子目標 DAG
- 前置條件檢查與依賴解析
- LLM 非同步輔助規劃 (複雜目標)
- 運行時重規劃 (卡住、環境變化)
- 與 HAM 記憶整合 (經驗、配方、空間知識)
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Set, Tuple, Callable
from collections import defaultdict
from enum import Enum

import numpy as np

from .game_structs import (
    SkillID,
    Subgoal,
    PlanDAG,
    TaskProgress,
    GameState,
    GAME_SKILLS,
    StrategyDirective,
)
from .game_memory_bridge import GameMemoryBridge
from .llm_game_interface import LLMGameInterface, PlanContext, PlanProposal

logger = logging.getLogger(__name__)


class GoalType(str, Enum):
    SURVIVAL = "survival"  # 生存：食物、血量、安全
    RESOURCE = "resource"  # 資源收集：木頭、石頭、鐵
    TOOL = "tool"  # 工具製作
    BUILD = "build"  # 建築
    EXPLORE = "explore"  # 探索
    COMBAT = "combat"  # 戰鬥/防禦
    CUSTOM = "custom"  # 自訂


@dataclass
class PlannerConfig:
    max_plan_depth: int = 10
    max_subgoals_per_plan: int = 20
    replan_on_blocker: bool = True
    llm_timeout_sec: float = 5.0
    use_llm_for_complex: bool = True
    complexity_threshold: int = 5  # 子目標超過此數用 LLM
    cache_ttl_sec: float = 300.0


@dataclass
class PlanningContext:
    current_goal: GoalType
    goal_params: Dict[str, Any]
    state: GameState
    ham_memories: List[str]
    strategy: StrategyDirective
    existing_plan: Optional[PlanDAG] = None
    blocker: Optional[str] = None


class GamePlanner:
    """
    L3 規劃器

    兩條路徑：
    1. 規則基礎規劃 (快速、確定性) - 簡單目標
    2. LLM 輔助規劃 (彈性、創造性) - 複雜目標

    輸出：PlanDAG (子目標節點 + 依賴邊)
    """

    def __init__(self, config: Optional[PlannerConfig] = None):
        self.config = config or PlannerConfig()
        self._memory: Optional[GameMemoryBridge] = None
        self._llm: Optional[LLMGameInterface] = None
        self._plan_cache: Dict[str, Tuple[PlanDAG, float]] = {}  # plan_id -> (plan, timestamp)
        self._recipe_graph = self._build_recipe_graph()
        self._goal_templates = self._build_goal_templates()

    def set_memory(self, memory: GameMemoryBridge):
        self._memory = memory

    def set_llm(self, llm: LLMGameInterface):
        self._llm = llm

    def _build_recipe_graph(self) -> Dict[str, Dict]:
        """建立配方依賴圖 (簡化版)"""
        return {
            "wooden_pickaxe": {"ingredients": {"wood": 3}, "unlocks": ["stone_pickaxe"]},
            "stone_pickaxe": {
                "ingredients": {"cobblestone": 3, "stick": 2},
                "unlocks": ["stone_axe", "stone_shovel", "stone_sword"],
            },
            "stone_axe": {"ingredients": {"cobblestone": 3, "stick": 2}},
            "stone_shovel": {"ingredients": {"cobblestone": 1, "stick": 2}},
            "stone_sword": {"ingredients": {"cobblestone": 2, "stick": 1}},
            "iron_pickaxe": {"ingredients": {"iron_ingot": 3, "stick": 2}, "requires": "furnace"},
            "furnace": {"ingredients": {"cobblestone": 8}},
            "chest": {"ingredients": {"wood": 8}},
            "crafting_table": {"ingredients": {"wood": 4}},
        }

    def _build_goal_templates(self) -> Dict[GoalType, List[Dict]]:
        """預定義目標模板 (規則基礎規劃)"""
        return {
            GoalType.SURVIVAL: [
                {
                    "skill": SkillID.EAT,
                    "params": {},
                    "preconditions": ["hunger_low", "has_food"],
                    "criteria": "hunger_restored",
                },
                {
                    "skill": SkillID.CRAFT,
                    "params": {"recipe_id": "wooden_pickaxe"},
                    "preconditions": ["has_wood"],
                    "criteria": "inventory_changed:wooden_pickaxe",
                },
                {
                    "skill": SkillID.DIG,
                    "params": {"target_node": "tree"},
                    "preconditions": ["has_tool:pickaxe"],
                    "criteria": "inventory_changed:wood",
                },
            ],
            GoalType.TOOL: [
                {
                    "skill": SkillID.CRAFT,
                    "params": {"recipe_id": "wooden_pickaxe"},
                    "preconditions": ["has_wood>=3"],
                    "criteria": "inventory_changed:wooden_pickaxe",
                },
                {
                    "skill": SkillID.DIG,
                    "params": {"target_node": "stone"},
                    "preconditions": ["has_tool:pickaxe"],
                    "criteria": "inventory_changed:cobblestone",
                },
                {
                    "skill": SkillID.CRAFT,
                    "params": {"recipe_id": "stone_pickaxe"},
                    "preconditions": ["has_cobblestone>=3", "has_stick>=2"],
                    "criteria": "inventory_changed:stone_pickaxe",
                },
            ],
            GoalType.RESOURCE: [
                {
                    "skill": SkillID.NAVIGATE,
                    "params": {"target_pos": "resource_area"},
                    "preconditions": [],
                    "criteria": "reached_target",
                },
                {
                    "skill": SkillID.DIG,
                    "params": {"target_node": "auto"},
                    "preconditions": ["has_tool:pickaxe"],
                    "criteria": "inventory_changed:*",
                },
            ],
            GoalType.BUILD: [
                {
                    "skill": SkillID.NAVIGATE,
                    "params": {"target_pos": "build_site"},
                    "preconditions": [],
                    "criteria": "reached_target",
                },
                {
                    "skill": SkillID.BUILD,
                    "params": {"blueprint": "shelter_5x5x3"},
                    "preconditions": ["has_materials"],
                    "criteria": "blueprint_complete",
                },
            ],
            GoalType.EXPLORE: [
                {
                    "skill": SkillID.NAVIGATE,
                    "params": {"target_pos": "unexplored"},
                    "preconditions": [],
                    "criteria": "reached_target",
                },
                {
                    "skill": SkillID.LOOK,
                    "params": {"target": "scan"},
                    "preconditions": [],
                    "criteria": "scanned",
                },
            ],
        }

    async def propose_plan(self, context: PlanningContext) -> PlanDAG:
        """
        提出計劃

        流程：
        1. 檢查快取
        2. 判斷複雜度 -> 選擇規則/LLM
        3. 生成 PlanDAG
        4. 驗證並快取
        """
        start = time.perf_counter()

        # 生成計劃 ID
        plan_id = f"plan_{context.current_goal.value}_{uuid.uuid4().hex[:8]}"

        # 檢查快取
        cache_key = f"{context.current_goal.value}_{hash(str(context.goal_params))}"
        if cache_key in self._plan_cache:
            cached_plan, ts = self._plan_cache[cache_key]
            if time.time() - ts < self.config.cache_ttl_sec:
                cached_plan.plan_id = plan_id
                logger.info(f"Using cached plan for {context.current_goal.value}")
                return cached_plan

        # 判斷複雜度
        estimated_steps = self._estimate_complexity(context)

        if (
            estimated_steps <= self.config.complexity_threshold
            or not self.config.use_llm_for_complex
        ):
            plan = await self._rule_based_plan(context, plan_id)
        else:
            plan = await self._llm_assisted_plan(context, plan_id)

        # 驗證計劃
        plan = self._validate_plan(plan, context)

        # 快取
        self._plan_cache[cache_key] = (plan, time.time())

        elapsed = (time.perf_counter() - start) * 1000
        logger.info(f"Planned {plan.plan_id}: {len(plan.nodes)} subgoals in {elapsed:.1f}ms")

        return plan

    def _estimate_complexity(self, context: PlanningContext) -> int:
        """估算計劃複雜度 (子目標數)"""
        base = len(self._goal_templates.get(context.current_goal, []))

        # 根據狀態調整
        if context.state.proprioception:
            inv = context.state.proprioception.inventory
            if not inv:
                base += 3  # 空手起家需更多步驟
            if "iron_ingot" in str(context.goal_params):
                base += 5  # 鐵器需熔爐、燃料等

        return base

    async def _rule_based_plan(self, context: PlanningContext, plan_id: str) -> PlanDAG:
        """規則基礎規劃 (快速、確定性)"""
        template = self._goal_templates.get(context.current_goal, [])
        nodes = {}
        edges = []

        for i, step in enumerate(template):
            sg_id = f"{context.current_goal.value}_{i}_{step['skill'].value}"

            # 檢查前置條件是否已滿足
            preconditions = step.get("preconditions", [])
            met_deps = []
            for pre in preconditions:
                dep_id = self._find_dependency(pre, nodes)
                if dep_id:
                    met_deps.append(dep_id)

            subgoal = Subgoal(
                subgoal_id=sg_id,
                skill_id=step["skill"],
                params=step.get("params", {}),
                preconditions=preconditions,
                success_criteria=step.get("criteria", "completed"),
                timeout_ticks=self._estimate_timeout(step["skill"]),
            )
            nodes[sg_id] = subgoal

            for dep in met_deps:
                edges.append((dep, sg_id))

        # 添加策略導向的額外子目標
        self._add_strategy_subgoals(nodes, edges, context)

        return PlanDAG(
            plan_id=plan_id,
            root_goal=context.current_goal.value,
            nodes=nodes,
            edges=edges,
            created_tick=0,
        )

    def _find_dependency(self, precondition: str, nodes: Dict) -> Optional[str]:
        """在現有節點中找滿足前置條件的節點"""
        for nid, node in nodes.items():
            if node.success_criteria == precondition or precondition in node.success_criteria:
                return nid
        return None

    def _estimate_timeout(self, skill: SkillID) -> int:
        timeouts = {
            SkillID.MOVE: 400,
            SkillID.DIG: 200,
            SkillID.PLACE: 50,
            SkillID.CRAFT: 60,
            SkillID.COMBAT: 600,
            SkillID.NAVIGATE: 2000,
            SkillID.EAT: 40,
            SkillID.BUILD: 5000,
            SkillID.LOOK: 100,
        }
        return timeouts.get(skill, 300)

    def _add_strategy_subgoals(self, nodes: Dict, edges: List, context: PlanningContext):
        """根據策略添加額外子目標"""
        strat = context.strategy

        if strat.exploration_weight > 0.7:
            # 添加探索子目標
            explore_id = f"explore_{len(nodes)}"
            nodes[explore_id] = Subgoal(
                subgoal_id=explore_id,
                skill_id=SkillID.NAVIGATE,
                params={"target_pos": "random_direction"},
                preconditions=[],
                success_criteria="explored_new_area",
                timeout_ticks=1000,
            )
            # 連接到最後一個資源收集節點
            last_resource = max(
                [n for n in nodes if nodes[n].skill_id == SkillID.DIG], default=None
            )
            if last_resource:
                edges.append((last_resource, explore_id))

        if strat.risk_tolerance < 0.3:
            # 保守策略：添加安全檢查
            pass

    async def _llm_assisted_plan(self, context: PlanningContext, plan_id: str) -> PlanDAG:
        """LLM 輔助規劃 (複雜目標)"""
        if not self._llm:
            logger.warning("LLM not available, falling back to rule-based")
            return await self._rule_based_plan(context, plan_id)

        # 準備 LLM 上下文 (llm_game_interface.PlanContext 會自行從 state 導出 position/inventory)
        llm_ctx = PlanContext(
            current_goal=context.current_goal.value,
            goal_params=context.goal_params,
            state=context.state,
            ham_memories=context.ham_memories[:10],
            strategy=dict(
                exploration_weight=context.strategy.exploration_weight,
                risk_tolerance=context.strategy.risk_tolerance,
            ),
        )
        llm_ctx.known_recipes = list(self._recipe_graph.keys())

        try:
            proposal = await asyncio.wait_for(
                self._llm.apropose_plan(llm_ctx), timeout=self.config.llm_timeout_sec
            )
            return self._parse_llm_proposal(proposal, plan_id)
        except asyncio.TimeoutError:
            logger.warning("LLM planning timeout, using rule-based")
            return await self._rule_based_plan(context, plan_id)
        except Exception as e:
            logger.error(f"LLM planning failed: {e}")
            return await self._rule_based_plan(context, plan_id)

    def _parse_llm_proposal(self, proposal: PlanProposal, plan_id: str) -> PlanDAG:
        """解析 LLM 回傳的計劃提案"""
        nodes = {}
        edges = []

        for i, sg_dict in enumerate(proposal.subgoals):
            sg_id = sg_dict.get("id", f"llm_{i}")
            skill_str = sg_dict.get("skill", "move")
            try:
                skill_id = SkillID(skill_str)
            except ValueError:
                skill_id = SkillID.MOVE

            subgoal = Subgoal(
                subgoal_id=sg_id,
                skill_id=skill_id,
                params=sg_dict.get("params", {}),
                preconditions=sg_dict.get("preconditions", []),
                success_criteria=sg_dict.get("success_criteria", "completed"),
                timeout_ticks=sg_dict.get("timeout", self._estimate_timeout(skill_id)),
            )
            nodes[sg_id] = subgoal

            # 依賴關係
            for dep in sg_dict.get("depends_on", []):
                edges.append((dep, sg_id))

        return PlanDAG(
            plan_id=plan_id, root_goal=proposal.plan_id, nodes=nodes, edges=edges, created_tick=0
        )

    def _validate_plan(self, plan: PlanDAG, context: PlanningContext) -> PlanDAG:
        """驗證計劃有效性"""
        # 1. 檢查循環依賴
        if self._has_cycle(plan):
            logger.warning("Plan has cycles, removing problematic edges")
            plan.edges = self._remove_cycles(plan)

        # 2. 檢查前置條件可滿足性
        available_skills = set(GAME_SKILLS.keys())
        for sg_id, node in plan.nodes.items():
            if node.skill_id not in available_skills:
                logger.warning(f"Unknown skill {node.skill_id} in plan, replacing with MOVE")
                node.skill_id = SkillID.MOVE

        # 3. 限制深度
        if len(plan.nodes) > self.config.max_subgoals_per_plan:
            logger.warning(f"Plan too deep ({len(plan.nodes)}), truncating")
            # 保留前 N 個
            keep_ids = list(plan.nodes.keys())[: self.config.max_subgoals_per_plan]
            plan.nodes = {k: v for k, v in plan.nodes.items() if k in keep_ids}
            plan.edges = [(f, t) for f, t in plan.edges if f in keep_ids and t in keep_ids]

        return plan

    def _has_cycle(self, plan: PlanDAG) -> bool:
        """檢測循環依賴 (Tarjan/Kahn)"""
        visited = set()
        rec_stack = set()

        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            for f, t in plan.edges:
                if f == node:
                    if t not in visited:
                        if dfs(t):
                            return True
                    elif t in rec_stack:
                        return True
            rec_stack.remove(node)
            return False

        for node in plan.nodes:
            if node not in visited:
                if dfs(node):
                    return True
        return False

    def _remove_cycles(self, plan: PlanDAG) -> List[Tuple[str, str]]:
        """移除循環 (簡化：拓撲排序保留可行邊)"""
        # Kahn's algorithm
        in_degree = defaultdict(int)
        for f, t in plan.edges:
            in_degree[t] += 1

        queue = [n for n in plan.nodes if in_degree[n] == 0]
        topo_order = []
        edges_kept = []

        while queue:
            n = queue.pop(0)
            topo_order.append(n)
            for f, t in plan.edges:
                if f == n:
                    edges_kept.append((f, t))
                    in_degree[t] -= 1
                    if in_degree[t] == 0:
                        queue.append(t)

        return edges_kept

    async def replan(self, context: PlanningContext, blocker: str) -> PlanDAG:
        """重規劃 (卡住、失敗、環境劇變)"""
        logger.info(f"Replanning due to: {blocker}")
        context.blocker = blocker
        context.existing_plan = None  # 不重用舊計劃
        return await self.propose_plan(context)

    def get_next_subgoal(self, plan: PlanDAG, completed: List[str]) -> Optional[Subgoal]:
        """取得下一個可執行子目標 (拓撲順序)"""
        # 計算入度
        in_degree = defaultdict(int)
        for f, t in plan.edges:
            in_degree[t] += 1

        # 找入度為 0 且未完成的
        for sg_id, node in plan.nodes.items():
            if sg_id in completed:
                continue
            if in_degree[sg_id] == 0:
                # 檢查依賴是否都完成
                deps = [f for f, t in plan.edges if t == sg_id]
                if all(d in completed for d in deps):
                    return node
        return None


class GoalManager:
    """目標管理：優先級、生成、衝突解決"""

    def __init__(self, planner: GamePlanner):
        self.planner = planner
        self.active_goals: List[Tuple[GoalType, Dict, float]] = []  # (goal, params, priority)
        self.completed_goals: List[GoalType] = []

    def add_goal(self, goal: GoalType, params: Dict = None, priority: float = 1.0):
        params = params or {}
        # 去重
        self.active_goals = [(g, p, pr) for g, p, pr in self.active_goals if g != goal]
        self.active_goals.append((goal, params, priority))
        self.active_goals.sort(key=lambda x: -x[2])  # 高優先級在前

    def get_highest_priority(self) -> Optional[Tuple[GoalType, Dict]]:
        if self.active_goals:
            g, p, _ = self.active_goals[0]
            return g, p
        return None

    def complete_goal(self, goal: GoalType):
        if goal in [g for g, _, _ in self.active_goals]:
            self.active_goals = [(g, p, pr) for g, p, pr in self.active_goals if g != goal]
            self.completed_goals.append(goal)

    async def plan_for_current(
        self, state: GameState, strategy: StrategyDirective
    ) -> Optional[PlanDAG]:
        """為當前最高優先級目標規劃"""
        current = self.get_highest_priority()
        if not current:
            return None

        goal, params = current

        # 從記憶獲取相關經驗
        memories = []
        if self.planner._memory:
            memories = await self.planner._memory.recall_experience(goal.value, limit=10)

        ctx = PlanningContext(
            current_goal=goal,
            goal_params=params,
            state=state,
            ham_memories=memories,
            strategy=strategy,
        )

        return await self.planner.propose_plan(ctx)
