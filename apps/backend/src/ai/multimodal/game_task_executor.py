"""
Game Task Executor - L2 任務執行層

功能：
- 子目標隊列管理 (FIFO + 優先級)
- 狀態機：pending -> active -> completed/failed
- 卡住檢測與自動 fallback
- 技能結果解析與下一步決策
- 與 L1/L3 介接
"""

import logging
import re
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Deque, Callable, Tuple
from enum import Enum

import numpy as np

from .game_structs import (
    SkillID,
    SkillSpec,
    SkillParams,
    SkillContext,
    SkillResult,
    Subgoal,
    TaskProgress,
    PlanDAG,
    GameState,
    GAME_SKILLS,
    check_preconditions,
    get_available_skills,
)
from .skill_selector import SkillSelector

logger = logging.getLogger(__name__)


class SubgoalStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class ExecutorState(str, Enum):
    IDLE = "idle"
    EXECUTING = "executing"
    WAITING = "waiting"
    REPLANNING = "replanning"
    STUCK = "stuck"


@dataclass
class ExecutorConfig:
    stuck_threshold_ticks: int = 600  # 30s @ 20FPS
    max_subgoal_retries: int = 3
    fallback_timeout_ticks: int = 3000  # 150s
    progress_check_interval: int = 20  # 每幀檢查開銷大，每 20 幀深度檢查
    min_progress_delta: float = 0.01  # 最小進展量
    enable_fallback: bool = True


@dataclass
class ActiveSubgoal:
    subgoal: Subgoal
    status: SubgoalStatus = SubgoalStatus.PENDING
    skill_params: Optional[SkillParams] = None
    skill_result: Optional[SkillResult] = None
    started_tick: int = 0
    last_progress_tick: int = 0
    progress_value: float = 0.0
    retry_count: int = 0
    consecutive_failures: int = 0
    blocked_ticks: int = 0


class GameTaskExecutor:
    """
    L2 任務執行器

    核心職責：
    1. 維護子目標隊列 (支援優先級、依賴關係)
    2. 驅動當前子目標 -> 產出 SkillContext 給 L1
    3. 接收 L1 技能結果 -> 更新進度、判斷完成/失敗
    4. 卡住檢測 -> 觸發 fallback 或請求 L3 重規劃
    4. 向 L3 回報 TaskProgress
    """

    def __init__(self, config: Optional[ExecutorConfig] = None):
        self.config = config or ExecutorConfig()
        self._queue: Deque[ActiveSubgoal] = deque()
        self._completed: List[ActiveSubgoal] = []
        self._failed: List[ActiveSubgoal] = []
        self._current: Optional[ActiveSubgoal] = None
        self._state = ExecutorState.IDLE
        self._tick = 0
        self._last_progress_check = 0
        self._task_progress = TaskProgress(task_id="")
        self._replan_callback: Optional[Callable[[str, str], None]] = (
            None  # (task_id, blocker) -> None
        )
        self._selector = SkillSelector()

        # 進度追蹤
        self._progress_history: Deque[float] = deque(maxlen=100)
        self._stuck_detector = StuckDetector(self.config.stuck_threshold_ticks)

    def set_replan_callback(self, callback: Callable[[str, str], None]):
        """設定重規劃回調 (通知 L3)"""
        self._replan_callback = callback

    def load_plan(self, plan: PlanDAG):
        """載入 L3 產出的計劃 DAG"""
        self._queue.clear()
        self._completed.clear()
        self._failed.clear()
        self._current = None
        self._state = ExecutorState.EXECUTING
        self._task_progress = TaskProgress(
            task_id=plan.plan_id, remaining=list(plan.nodes.keys()), completed=[]
        )

        # 按拓撲順序加入隊列 (簡化：直接按節點順序)
        # 實際應做拓撲排序
        for subgoal_id in plan.nodes:
            sg = plan.nodes[subgoal_id]
            self._queue.append(ActiveSubgoal(subgoal=sg))

        logger.info(f"Loaded plan {plan.plan_id} with {len(self._queue)} subgoals")

    def load_subgoals(self, subgoals: List[Subgoal], task_id: str = ""):
        """直接載入子目標列表"""
        self._queue.clear()
        for sg in subgoals:
            self._queue.append(ActiveSubgoal(subgoal=sg))
        self._task_progress = TaskProgress(
            task_id=task_id, remaining=[sg.subgoal_id for sg in subgoals]
        )
        self._state = ExecutorState.EXECUTING

    def tick(
        self, skill_result: Optional[SkillResult], state: GameState, latent: np.ndarray
    ) -> Optional[SkillContext]:
        """
        主迴圈：每幀調用一次

        Returns:
            SkillContext: 給 L1 的技能上下文，None 表示待機
        """
        self._tick += 1
        self._selector.tick()

        # 1. 處理上一幀技能結果
        if skill_result and self._current:
            self._process_skill_result(skill_result)

        # 2. 狀態機驅動
        if self._state == ExecutorState.EXECUTING:
            return self._drive_execution(state, latent)
        elif self._state == ExecutorState.WAITING:
            return self._handle_waiting(state, latent)
        elif self._state == ExecutorState.STUCK:
            return self._handle_stuck(state, latent)
        elif self._state == ExecutorState.REPLANNING:
            return self._handle_replanning(state, latent)

        return None

    def _drive_execution(self, state: GameState, latent: np.ndarray) -> Optional[SkillContext]:
        """執行階段：啟動/繼續當前子目標"""

        # 沒有當前子目標，取下一個
        if self._current is None:
            self._current = self._pop_next_subgoal()
            if self._current is None:
                self._state = ExecutorState.IDLE
                self._task_progress.remaining = []
                logger.info("All subgoals completed")
                return None

            # 啟動子目標
            self._start_subgoal(self._current)

        # 檢查前置條件
        if not self._check_preconditions(self._current, state):
            self._current.status = SubgoalStatus.BLOCKED
            return self._handle_blocked(state, latent)

        # 生成/更新技能參數
        if self._current.skill_params is None:
            self._current.skill_params = self._generate_skill_params(self._current, state, latent)

        # 檢查超時
        if self._tick - self._current.started_tick > self._current.subgoal.timeout_ticks:
            logger.warning(f"Subgoal {self._current.subgoal.subgoal_id} timeout")
            self._current.status = SubgoalStatus.FAILED
            self._current.consecutive_failures += 1
            return self._handle_failure(state, latent)

        # 定期進度檢查
        if self._tick - self._last_progress_check >= self.config.progress_check_interval:
            self._check_progress(state)
            self._last_progress_check = self._tick

        # 卡住檢測
        if self._stuck_detector.check(self._tick, self._current.progress_value):
            self._state = ExecutorState.STUCK
            return self._handle_stuck(state, latent)

        # 輸出技能上下文
        ctx = SkillContext(
            active_skill=self._current.subgoal.skill_id,
            params=self._current.subgoal.params,
            priority=self._current.skill_params.priority if self._current.skill_params else 1.0,
            interrupt_on=self._current.subgoal.preconditions,
        )
        return ctx

    def _pop_next_subgoal(self) -> Optional[ActiveSubgoal]:
        """取得下一個可執行子目標 (跳過已完成/失敗)"""
        while self._queue:
            candidate = self._queue[0]
            # 檢查依賴 (簡化：檢查前置條件)
            if self._are_dependencies_met(candidate):
                return self._queue.popleft()
            else:
                # 依賴未滿足，放回隊尾 (避免死循環需標記)
                self._queue.rotate(-1)
                # 防止無限旋轉
                if candidate.subgoal.status == SubgoalStatus.PENDING:
                    candidate.subgoal.status = SubgoalStatus.BLOCKED
        return None

    def _are_dependencies_met(self, active: ActiveSubgoal) -> bool:
        """檢查依賴是否滿足 (簡化：檢查前置條件字串)"""
        for cond in active.subgoal.preconditions:
            if cond.startswith("completed:"):
                dep_id = cond.split(":")[1]
                if dep_id not in self._task_progress.completed:
                    return False
        return True

    def _start_subgoal(self, active: ActiveSubgoal):
        """啟動子目標"""
        active.status = SubgoalStatus.ACTIVE
        active.started_tick = self._tick
        active.last_progress_tick = self._tick
        active.progress_value = 0.0
        active.skill_params = None
        active.skill_result = None

        self._task_progress.current_subgoal = active.subgoal.subgoal_id
        logger.info(
            f"Started subgoal: {active.subgoal.subgoal_id} ({active.subgoal.skill_id.value})"
        )

    def _generate_skill_params(
        self, active: ActiveSubgoal, state: GameState, latent: np.ndarray
    ) -> SkillParams:
        """生成技能參數 (委託 L1 Selector 或用預設)"""
        ctx = SkillContext(
            active_skill=active.subgoal.skill_id,
            params=active.subgoal.params,
            priority=1.0,
            interrupt_on=active.subgoal.preconditions,
        )
        return self._selector.select(latent, state, ctx)

    def _check_preconditions(self, active: ActiveSubgoal, state: GameState) -> bool:
        """檢查前置條件（技能規格＋子目標自帶條件都要過）"""
        ok, failed = check_preconditions(active.subgoal.skill_id, state)
        if not ok:
            logger.debug(f"Preconditions failed for {active.subgoal.subgoal_id}: {failed}")
            return False
        ok2, failed2 = self._check_subgoal_preconditions(active.subgoal.preconditions, state)
        if not ok2:
            logger.debug(f"Subgoal preconditions failed for {active.subgoal.subgoal_id}: {failed2}")
            return False
        return True

    @staticmethod
    def _check_subgoal_preconditions(
        preconditions: List[str], state: GameState
    ) -> Tuple[bool, List[str]]:
        """評估子目標自帶的前置字串（模板如 has_wood / has_X>=N / has_tool:X）。

        之前執行期只檢查技能規格的前置，子目標的 has_wood 等形同虛設：
        沒木頭也照排 craft，6 秒超時、重試、重規劃無限空轉。
        """
        prop = state.proprioception if state else None
        inv = dict((prop.inventory if prop else {}) or {})
        failed: List[str] = []

        def _count(needle: str) -> int:
            total = 0
            for key, val in inv.items():
                if needle in str(key):
                    try:
                        total += int(val)
                    except (TypeError, ValueError):
                        pass
            return total

        for cond in preconditions or []:
            if cond.startswith("completed:"):
                continue  # 依賴在出隊時已驗過
            elif cond in (
                "recipe_unlocked",
                "ingredients_in_inv",
                "hostile_in_range",
                "has_materials",
                "space_available",
            ):
                continue  # 具體檢查在執行時做（與規格層一致）
            elif cond == "has_food":
                food_items = ["apple", "bread", "meat", "cooked", "carrot", "potato"]
                if not any(f in str(k) for k in inv for f in food_items):
                    failed.append("無食物")
            elif cond == "hunger_low":
                max_hunger = getattr(prop, "max_hunger", 20) if prop else 20
                hunger = getattr(prop, "hunger", 20) if prop else 20
                try:
                    if float(hunger) > float(max_hunger) * 0.3:
                        failed.append("飢餓度未低")
                except (TypeError, ValueError):
                    pass
            elif cond.startswith("has_tool:"):
                tool = cond.split(":", 1)[1]
                if _count(tool) <= 0:
                    failed.append(f"缺少工具: {tool}")
            elif cond.startswith("has_"):
                # has_wood / has_wood>=3 / has_cobblestone>=3
                m = re.match(r"has_([a-z_]+)(>=(\d+))?", cond)
                if m:
                    item, _, need = m.groups()
                    have = _count(item)
                    if need is not None and have < int(need):
                        failed.append(f"缺少材料: {item} ({have}/{need})")
                    elif need is None and have <= 0:
                        failed.append(f"缺少材料: {item}")
                else:
                    logger.debug(f"Unknown subgoal precondition (ignored): {cond}")
            else:
                logger.debug(f"Unknown subgoal precondition (ignored): {cond}")

        return len(failed) == 0, failed

    def _process_skill_result(self, result: SkillResult):
        """處理技能執行結果"""
        if not self._current:
            return

        self._current.skill_result = result

        if result.success:
            self._current.consecutive_failures = 0
            self._current.progress_value = min(1.0, self._current.progress_value + 0.2)
            self._current.last_progress_tick = self._tick

            # 檢查是否滿足成功條件
            if self._check_success_condition(self._current, result):
                self._complete_subgoal()
        else:
            self._current.consecutive_failures += 1
            if self._current.consecutive_failures >= 3:
                self._current.status = SubgoalStatus.FAILED

    def _check_success_condition(self, active: ActiveSubgoal, result: SkillResult) -> bool:
        """檢查成功條件"""
        criteria = active.subgoal.success_criteria

        if criteria.startswith("inventory_changed:"):
            item = criteria.split(":")[1]
            if item in ("*", "craft_output"):
                # 通配：_derive_skill_result 只在真有物品增長時才回傳成功，
                # 收到即視為完成（"*" 字面比對永遠 False，不可直接 in）。
                return True
            return any(item in effect for effect in result.side_effects)
        elif criteria == "block_placed":
            return any("placed" in effect for effect in result.side_effects)
        elif criteria == "target_dead_or_lost":
            return any("killed" in effect or "lost" in effect for effect in result.side_effects)
        elif criteria == "reached_target":
            return any("arrived" in effect for effect in result.side_effects)
        elif criteria == "hunger_restored":
            return any("hunger" in effect for effect in result.side_effects)
        elif criteria == "blueprint_complete":
            return any("build_complete" in effect for effect in result.side_effects)

        # 預設：技能成功即視為完成
        return True

    def _complete_subgoal(self):
        """完成子目標"""
        if not self._current:
            return

        self._current.status = SubgoalStatus.COMPLETED
        self._completed.append(self._current)
        self._task_progress.completed.append(self._current.subgoal.subgoal_id)
        if self._current.subgoal.subgoal_id in self._task_progress.remaining:
            self._task_progress.remaining.remove(self._current.subgoal.subgoal_id)

        logger.info(f"Completed subgoal: {self._current.subgoal.subgoal_id}")
        self._current = None

    def _handle_failure(self, state: GameState, latent: np.ndarray) -> Optional[SkillContext]:
        """處理失敗"""
        if not self._current:
            return None

        self._current.status = SubgoalStatus.FAILED
        self._failed.append(self._current)

        if (
            self._current.retry_count < self.config.max_subgoal_retries
            and self.config.enable_fallback
        ):
            self._current.retry_count += 1
            logger.warning(
                f"Retrying subgoal {self._current.subgoal.subgoal_id} (attempt {self._current.retry_count})"
            )

            # 使用 fallback
            if self._current.subgoal.fallback:
                fallback_sg = Subgoal(
                    subgoal_id=f"{self._current.subgoal.subgoal_id}_fallback_{self._current.retry_count}",
                    skill_id=SkillID(self._current.subgoal.fallback),
                    params={},
                    preconditions=[],
                    success_criteria="fallback_done",
                    timeout_ticks=self.config.fallback_timeout_ticks,
                )
                self._queue.appendleft(ActiveSubgoal(subgoal=fallback_sg))

            self._current = None
            return self._drive_execution(state, latent)
        else:
            # 徹底失敗，請求 L3 重規劃
            self._request_replan(f"subgoal_failed:{self._current.subgoal.subgoal_id}")
            self._current = None
            return None

    def _handle_blocked(self, state: GameState, latent: np.ndarray) -> Optional[SkillContext]:
        """處理前置條件不滿足"""
        # 嘗試插入前置子目標 (如缺工具 -> 去挖石頭)
        # 簡化：等待或請求重規劃
        if self.config.enable_fallback and self._current.subgoal.fallback:
            fallback_sg = Subgoal(
                subgoal_id=f"{self._current.subgoal.subgoal_id}_unblock",
                skill_id=SkillID(self._current.subgoal.fallback),
                params={},
                preconditions=[],
                success_criteria="unblocked",
                timeout_ticks=300,
            )
            self._queue.appendleft(ActiveSubgoal(subgoal=fallback_sg))
            self._current = None
            return self._drive_execution(state, latent)

        # 無 fallback：累計 blocked 次數，超過閾值則跳過此子目標，
        # 避免卡在 BLOCKED 觸發每 tick 重規劃的死循環
        self._current.blocked_ticks += 1
        if self._current.blocked_ticks >= 10:
            logger.warning(
                f"Subgoal {self._current.subgoal.subgoal_id} blocked "
                f"for {self._current.blocked_ticks} ticks, skipping"
            )
            self._current.status = SubgoalStatus.FAILED
            self._failed.append(self._current)
            self._current = None
            return self._drive_execution(state, latent)

        return None  # 待機

    def _handle_stuck(self, state: GameState, latent: np.ndarray) -> Optional[SkillContext]:
        """處理卡住"""
        logger.warning(
            f"Stuck detected at subgoal {self._current.subgoal.subgoal_id if self._current else 'unknown'}"
        )

        # 嘗試簡單恢復：隨機移動、跳躍、轉向
        recovery_sg = Subgoal(
            subgoal_id=f"recovery_{self._tick}",
            skill_id=SkillID.MOVE,
            params={
                "forward": 0.5,
                "strafe": np.random.uniform(-1, 1),
                "yaw": np.random.uniform(-1, 1),
            },
            preconditions=[],
            success_criteria="moved",
            timeout_ticks=100,
        )
        self._queue.appendleft(ActiveSubgoal(subgoal=recovery_sg))
        self._current = None
        self._stuck_detector.reset(self._tick)
        self._state = ExecutorState.EXECUTING
        return self._drive_execution(state, latent)

    def _handle_waiting(self, state: GameState, latent: np.ndarray) -> Optional[SkillContext]:
        """等待狀態 (外部事件)"""
        return None

    def _handle_replanning(self, state: GameState, latent: np.ndarray) -> Optional[SkillContext]:
        """重規劃中"""
        return None

    def _check_progress(self, state: GameState):
        """深度進度檢查"""
        if not self._current:
            return

        # 計算具體進度 (根據技能類型)
        progress = self._calculate_progress(self._current, state)
        self._current.progress_value = progress
        self._progress_history.append(progress)

        # 更新任務進度
        self._task_progress.eta_ticks = int((len(self._queue) + 1) * 300)  # 粗略估算

    def _calculate_progress(self, active: ActiveSubgoal, state: GameState) -> float:
        """計算子目標進度 0-1"""
        skill = active.subgoal.skill_id

        if skill == SkillID.DIG:
            # 根據收集物品判斷
            return min(1.0, active.progress_value + 0.1)
        elif skill == SkillID.CRAFT:
            return 1.0 if active.skill_result and active.skill_result.success else 0.5
        elif skill == SkillID.NAVIGATE:
            # 根據距離目標
            return 0.5  # 簡化
        return active.progress_value

    def _request_replan(self, blocker: str):
        """請求 L3 重規劃"""
        self._state = ExecutorState.REPLANNING
        self._task_progress.blocker = blocker
        if self._replan_callback:
            self._replan_callback(self._task_progress.task_id, blocker)

    def get_progress(self) -> TaskProgress:
        """取得當前任務進度 (給 L3)"""
        return self._task_progress

    def get_current_subgoal(self) -> Optional[Subgoal]:
        return self._current.subgoal if self._current else None

    def force_subgoal(self, subgoal: Subgoal):
        """強制插入子目標 (高優先級，如緊急進食、戰鬥)"""
        self._queue.appendleft(ActiveSubgoal(subgoal=subgoal))
        if self._current:
            self._current.status = SubgoalStatus.BLOCKED
            self._current = None


class StuckDetector:
    """卡住檢測器"""

    def __init__(self, threshold_ticks: int):
        self.threshold = threshold_ticks
        self.last_progress_tick = 0
        self.last_progress_value = 0.0

    def check(self, current_tick: int, current_progress: float) -> bool:
        """檢查是否卡住"""
        if current_progress > self.last_progress_value + 0.01:
            self.last_progress_value = current_progress
            self.last_progress_tick = current_tick
            return False

        return (current_tick - self.last_progress_tick) > self.threshold

    def reset(self, current_tick: int = 0):
        # 必須錨定到當前 tick；歸零會讓 (tick - 0) > threshold 立即成立，
        # 造成 _handle_stuck ↔ _drive_execution 無限遞迴
        self.last_progress_tick = current_tick
        self.last_progress_value = 0.0


class PriorityTaskQueue:
    """優先級任務隊列 (支援依賴關係)"""

    def __init__(self):
        self._tasks: List[ActiveSubgoal] = []
        self._dependency_graph: Dict[str, List[str]] = {}

    def add(self, subgoal: ActiveSubgoal, dependencies: List[str] = None):
        self._tasks.append(subgoal)
        if dependencies:
            self._dependency_graph[subgoal.subgoal.subgoal_id] = dependencies

    def pop_ready(self, completed: List[str]) -> Optional[ActiveSubgoal]:
        for i, task in enumerate(self._tasks):
            deps = self._dependency_graph.get(task.subgoal.subgoal_id, [])
            if all(d in completed for d in deps):
                return self._tasks.pop(i)
        return None
