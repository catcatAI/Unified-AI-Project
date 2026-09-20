#!/usr/bin/env python3
"""
Angela AI - Complete Autonomous Agent
Single executable integrating L0-L4 architecture for fully autonomous behavior.
"""

import asyncio
import json
import logging
import os
import signal
import sys
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Deque

import numpy as np

# Add project paths
sys.path.insert(0, "/home/cxuo/文件/GitHub/Unified-AI-Project/apps/backend/src")

from ai.multimodal.foveated_sampler import FoveatedSampler, SamplingConfig, SamplingStrategy
from ai.multimodal.game_policy import GamePolicy, PolicyConfig, PolicyOutput
from ai.multimodal.skill_selector import SkillSelector, SelectorConfig
from ai.multimodal.game_task_executor import (
    ActiveSubgoal,
    ExecutorState,
    GameTaskExecutor,
    ExecutorConfig,
    Subgoal,
    SubgoalStatus,
    SkillContext,
    SkillResult,
)
from ai.multimodal.game_planner import (
    GamePlanner,
    PlannerConfig,
    PlanningContext,
    GoalManager,
    GoalType,
)
from ai.multimodal.game_memory_bridge import GameMemoryBridge
from ai.multimodal.game_strategy import GameStrategy, StrategyConfig, StrategyWeights
from ai.multimodal.llm_game_interface import LLMGameInterface, LLMConfig, RuleBasedFallback
from luanti_polling_bridge import PollingBridge
from luanti_connector import PlayerState
from ai.multimodal.game_structs import (
    SkillID,
    SkillSpec,
    SkillParams,
    SkillContext,
    SkillResult,
    SkillTrigger,
    Subgoal,
    TaskProgress,
    PlanDAG,
    GameState,
    VisualObservation,
    Proprioception,
    StrategyDirective,
    GAME_SKILLS,
    check_preconditions,
    get_available_skills,
)
from ai.multimodal.game_policy import PolicyConfig, PolicyOutput
from ai.multimodal.skill_selector import SelectorConfig
from ai.multimodal.game_task_executor import ExecutorConfig
from ai.multimodal.game_planner import PlannerConfig, GoalManager, GoalType, PlanningContext
from ai.multimodal.game_memory_bridge import GameMemoryBridge
from ai.multimodal.game_strategy import GameStrategy, StrategyConfig
from ai.multimodal.llm_game_interface import LLMGameInterface, LLMConfig, RuleBasedFallback
from luanti_polling_bridge import PollingBridge
from ai.multimodal.game_policy import PolicyConfig, PolicyOutput
from ai.multimodal.skill_selector import SelectorConfig
from ai.multimodal.game_task_executor import ExecutorConfig
from ai.multimodal.game_planner import PlannerConfig, GoalManager, GoalType, PlanningContext
from ai.multimodal.game_memory_bridge import GameMemoryBridge
from ai.multimodal.game_strategy import GameStrategy, StrategyConfig
from ai.multimodal.llm_game_interface import LLMGameInterface, LLMConfig
from luanti_polling_bridge import PollingBridge
from luanti_connector import LuantiConnector, LuantiConfig, GameSnapshot, PlayerState
from ai.multimodal.game_structs import (
    SkillID,
    SkillSpec,
    SkillParams,
    SkillContext,
    SkillResult,
    SkillTrigger,
    Subgoal,
    TaskProgress,
    PlanDAG,
    GameState,
    VisualObservation,
    Proprioception,
    StrategyDirective,
    GAME_SKILLS,
    check_preconditions,
    get_available_skills,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class AngelaConfig:
    """Complete configuration for Angela autonomous agent"""

    # Luanti connection
    luanti_host: str = "192.168.1.112"
    luanti_port: int = 30000
    bridge_port: int = 30003
    target_player: str = "AngelaBot"

    # L0 Reflex
    vision_budget: int = 83000
    vision_fovea_ratio: float = 0.7
    policy_latent_dim: int = 128
    policy_continuous_dim: int = 16
    policy_discrete_dim: int = 8

    # L1 Skill
    skill_temperature: float = 1.0
    skill_cooldown: float = 2.0

    # L2 Task
    stuck_threshold: float = 30.0  # seconds
    max_retries: int = 3

    # L3 Planner
    planner_depth: int = 10
    use_llm: bool = True
    llm_timeout: float = 5.0

    # L4 Strategy
    strategy_update_interval: float = 30.0

    # Memory
    memory_path: str = "data/angela_memory"

    # Agent
    target_player_name: str = "AngelaBot"
    tick_interval: float = 0.1  # 10Hz main loop
    max_ticks: int = 0  # 0 = infinite


class AngelaAutonomousAgent:
    """
    Angela AI - Complete Autonomous Agent
    Integrates L0-L4 architecture for fully autonomous behavior in Luanti.
    """

    def __init__(self, config: Optional[AngelaConfig] = None):
        self.config = config or AngelaConfig()
        self.running = False
        self.tick_count = 0
        self.start_time = time.time()

        # Components (initialized in start())
        self.bridge: Optional[PollingBridge] = None
        # self.connector removed - using polling bridge instead
        self.sampler: Optional[FoveatedSampler] = None
        self.visual_encoder: Optional[Any] = None
        self.policy: Optional[GamePolicy] = None
        self.selector: Optional[SkillSelector] = None
        self.executor: Optional[GameTaskExecutor] = None
        self.planner: Optional[GamePlanner] = None
        self.memory: Optional[GameMemoryBridge] = None
        self.strategy: Optional[GameStrategy] = None
        self.llm: Optional[LLMGameInterface] = None
        self.planner_wrapper: Optional[GamePlanner] = None
        self.goal_manager: Optional[GoalManager] = None
        self.strategy_engine: Optional[GameStrategy] = None
        self.emotion: Optional[Any] = None
        self.lifecycle: Optional[Any] = None
        self._last_completed = 0
        self._last_failed = 0
        self._last_inventory: Dict[str, Any] = {}

        # State
        self.running = False
        self.tick_count = 0
        self.current_state: Optional[GameState] = None
        self.last_poll = 0
        self.agent_player_name = "AngelaBot"

        # Autonomous behavior state
        self.autonomous_mode = True
        self.current_goal: Optional[GoalType] = None
        self.current_plan: Optional[Any] = None
        self.last_strategy_update = 0
        self.last_replan_tick = -1000

    async def initialize(self) -> bool:
        """Initialize all components"""
        logger.info("Initializing Angela Autonomous Agent...")

        # Create memory directory
        Path(self.config.memory_path).mkdir(parents=True, exist_ok=True)

        # Initialize memory bridge with the REAL HAM backend
        # (previously MockHAMManager — experiences never persisted)
        self.memory = GameMemoryBridge()
        try:
            from ai.memory.ham_memory.ham_manager import HAMMemoryManager

            ham = HAMMemoryManager(
                memory_file=str(Path(self.config.memory_path) / "ham_game_memory.json"),
            )
            await self.memory.initialize(ham)
            logger.info("Memory bridge initialized with real HAM backend")
        except Exception as e:
            logger.warning(f"Real HAM unavailable, memory stays local-only: {e}")
            await self.memory.initialize(None)

        # Initialize LLM interface
        llm_config = LLMConfig(
            enabled=True,
            provider="ollama",
            base_url="http://localhost:11434/v1",
            model="qwen2.5:7b",
            timeout_sec=self.config.llm_timeout,
        )
        self.llm = LLMGameInterface(llm_config)
        logger.info("LLM interface initialized")

        # Initialize polling bridge (only if not already set)
        if not hasattr(self, "bridge") or self.bridge is None:
            self.bridge = PollingBridge(http_port=30003)
        await self.bridge.start()
        logger.info("Polling bridge started on port 30003")

        # Initialize Luanti connector
        logger.info("Luanti connection skipped - using polling bridge instead")

        # Initialize perception (L0)
        self.sampler = FoveatedSampler(
            SamplingConfig(
                budget_pixels=83000,
                fovea_ratio=0.7,
                output_size=(64, 64),
                strategy=SamplingStrategy.LOG_POLAR,
            )
        )

        # Real VisualEncoder for when frames arrive (currently the poller
        # reports state only, so visual stays None until /api/frame lands)
        try:
            from ai.multimodal.visual_encoder import VisualEncoder

            self.visual_encoder = VisualEncoder()
            logger.info("VisualEncoder wired (awaiting frame source)")
        except Exception as e:
            logger.warning(f"VisualEncoder unavailable: {e}")
            self.visual_encoder = None

        self.policy = GamePolicy(
            PolicyConfig(latent_dim=128, continuous_dim=16, discrete_dim=8, use_diffusion=True)
        )

        # L1 Skill Selector
        self.selector = SkillSelector(
            SelectorConfig(temperature=1.0, skill_embedding_dim=32, latent_dim=128)
        )

        # L2 Task Executor
        self.executor = GameTaskExecutor(
            ExecutorConfig(
                stuck_threshold_ticks=int(self.config.stuck_threshold * 10),
                max_subgoal_retries=self.config.max_retries,
            )
        )

        # L3 Planner
        self.planner = GamePlanner(
            PlannerConfig(
                max_plan_depth=self.config.planner_depth,
                use_llm_for_complex=self.config.use_llm,
                llm_timeout_sec=self.config.llm_timeout,
            )
        )
        self.planner.set_memory(self.memory)
        self.planner.set_llm(self.llm)

        # Goal manager
        self.goal_manager = GoalManager(self.planner)

        # Add initial autonomous goals
        self.goal_manager.add_goal(GoalType.SURVIVAL, priority=1.0)
        self.goal_manager.add_goal(GoalType.TOOL, priority=0.8)
        self.goal_manager.add_goal(GoalType.RESOURCE, priority=0.7)
        self.goal_manager.add_goal(GoalType.BUILD, priority=0.5)
        self.goal_manager.add_goal(GoalType.EXPLORE, priority=0.3)

        # L4 Strategy
        self.strategy_engine = GameStrategy(
            StrategyConfig(update_interval_sec=self.config.strategy_update_interval)
        )

        # Emotion + Lifecycle: wire the REAL project systems so game
        # outcomes feed the same loops the chat pipeline uses
        try:
            from ai.alignment.emotion_system import EmotionSystem

            self.emotion = EmotionSystem(system_id="angela_game_agent")
            logger.info("EmotionSystem wired into game agent")
        except Exception as e:
            logger.warning(f"EmotionSystem unavailable, game affect disabled: {e}")
            self.emotion = None
        try:
            from core.life.autonomous_life_cycle import AutonomousLifeCycle

            self.lifecycle = AutonomousLifeCycle()
            logger.info("AutonomousLifeCycle wired into game agent")
        except Exception as e:
            logger.warning(f"AutonomousLifeCycle unavailable: {e}")
            self.lifecycle = None

        logger.info("All components initialized successfully")
        return True

    async def start(self):
        """Start the autonomous agent main loop"""
        if not await self.initialize():
            logger.error("Failed to initialize agent")
            return

        self.running = True
        logger.info("Starting Angela Autonomous Agent main loop...")

        # Register signal handlers
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.stop()))

        try:
            await self._main_loop()
        except asyncio.CancelledError:
            logger.info("Main loop cancelled")
        except Exception as e:
            logger.error(f"Main loop error: {e}", exc_info=True)
        finally:
            await self.cleanup()

    async def _main_loop(self):
        """Main autonomous agent loop - runs at configured tick rate"""
        tick_interval = self.config.tick_interval
        last_tick = time.time()

        while self.running:
            loop_start = time.time()
            self.tick_count += 1

            try:
                # 1. Perceive - get game state
                await self._perceive()

                # 2. Update strategy (L4) - periodically
                if (
                    self.tick_count
                    % int(self.config.strategy_update_interval / self.config.tick_interval)
                    == 0
                ):
                    await self._update_strategy()

                # 3. Select initial goal if none set
                if self.current_goal is None:
                    goal = self.goal_manager.get_highest_priority()
                    if goal:
                        self.current_goal, _ = goal
                        logger.info(f"Selected initial goal: {self.current_goal.value}")

                # 3. Plan/Replan (L3) - if needed
                if self._should_replan() and self.current_state is not None:
                    await self._replan()

                # 4. Execute tasks (L2)
                await self._execute_tasks()

                # 5. Skill selection (L1) - if no active subgoal
                if not self.executor._current:
                    await self._select_skill()

                # 6. Reflex execution (L0) - continuous
                await self._execute_reflex()

                # 6. Memory consolidation
                if self.tick_count % 100 == 0:
                    await self._consolidate_memory()

            except Exception as e:
                logger.error(f"Tick error: {e}", exc_info=True)

            # Tick rate control
            elapsed = time.time() - loop_start
            sleep_time = max(0, self.config.tick_interval - elapsed)
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

            # Log progress periodically
            if self.tick_count % 100 == 0:
                self._log_status()

    @staticmethod
    def _normalize_position(pos) -> Tuple[float, float, float]:
        """Bridge sends dict {x,y,z}; policy stack needs a tuple."""
        if isinstance(pos, dict):
            return (
                float(pos.get("x", 0.0)),
                float(pos.get("y", 0.0)),
                float(pos.get("z", 0.0)),
            )
        try:
            return (float(pos[0]), float(pos[1]), float(pos[2]))
        except Exception:
            return (0.0, 0.0, 0.0)

    async def _perceive(self):
        """L0: Perception - get game state from polling bridge"""
        try:
            # Get state from polling bridge
            state = self.bridge.player_state
            if state:
                self.current_state = GameState(
                    tick=self.tick_count,
                    timestamp=time.time(),
                    proprioception=PlayerState(
                        position=self._normalize_position(state.get("position", (0, 0, 0))),
                        yaw=state.get("yaw", 0.0),
                        pitch=state.get("pitch", 0.0),
                        hp=state.get("hp", 20),
                        max_hp=state.get("max_hp", 20),
                        hunger=state.get("hunger", 20),
                        breath=state.get("breath", 10),
                        inventory=state.get("inventory") or {},
                        wielded_item=state.get("wielded", ""),
                        is_on_ground=state.get("on_ground", True),
                        velocity=(0.0, 0.0, 0.0),
                    ),
                    visual=None,  # Filled below when a frame is present
                )

                # Encode a frame when the bridge provides one; otherwise
                # visual stays None and the policy runs on proprioception.
                # (Honest stub: /api/frame is still a placeholder.)
                frame = state.get("frame")
                if frame is not None and self.visual_encoder is not None:
                    try:
                        import numpy as _np
                        from PIL import Image as _Image
                        import io as _io

                        if isinstance(frame, (bytes, bytearray)):
                            img = _Image.open(_io.BytesIO(bytes(frame))).convert("RGB")
                        else:
                            img = _Image.fromarray(_np.asarray(frame, dtype=_np.uint8))
                        feats = self.visual_encoder.encode_from_pil(img)
                        self.current_state.visual = VisualObservation(
                            frame_id=self.tick_count,
                            timestamp=time.time(),
                            features=_np.asarray(feats, dtype=_np.float32),
                            fovea_xy=(320, 240),
                            inverse_map=None,
                            raw_frame_shape=img.size[::-1],
                        )
                    except Exception as e:
                        logger.debug(f"Frame encode failed: {e}")

        except Exception as e:
            logger.error(f"Perception error: {e}")

    async def _update_strategy(self):
        """L4: Update strategy weights based on performance"""
        try:
            self.strategy_engine.update(self.current_state)
            self.last_strategy_update = time.time()

            # Get directive for planner
            directive = self.strategy_engine.get_directive()
            logger.debug(f"Strategy update: {directive}")
        except Exception as e:
            logger.error(f"Strategy update error: {e}")

    def _should_replan(self) -> bool:
        """Determine if replanning is needed.

        Note: an empty _current with a non-empty _queue is NORMAL
        (executor pops the next subgoal on its next tick), not a
        reason to replan — replanning there caused a reload loop.
        """
        if self.executor._current and self.executor._current.status == SubgoalStatus.BLOCKED:
            # 冷卻：同一 plan 最多每 50 tick 重規劃一次，防止 BLOCKED 死循環洗版
            if self.tick_count - self.last_replan_tick >= 50:
                return True
            return False
        if self.executor._state.value in ("REPLANNING", "STUCK"):
            return True
        if self.current_goal and not self.current_plan and not self.executor._queue:
            return True
        return False

    async def _replan(self):
        """L3: Replan based on current state and goals"""
        if not self.current_goal:
            # Select highest priority goal
            goal = self.goal_manager.get_highest_priority()
            if goal:
                self.current_goal, params = goal
                logger.info(f"Selected goal: {self.current_goal.value}")
            else:
                return

        # Get relevant memories
        memories = []
        if self.memory:
            memories = await self.memory.recall_experience(self.current_goal.value, limit=10)

        # Get strategy directive
        strategy = self.strategy_engine.get_directive() if self.strategy_engine else {}

        # Build planning context
        ctx = PlanningContext(
            current_goal=self.current_goal,
            goal_params={},
            state=self.current_state,
            ham_memories=memories,
            strategy=(
                StrategyDirective(**self.strategy_engine.get_directive())
                if self.strategy_engine
                else StrategyDirective()
            ),
        )

        try:
            plan = await self.planner.propose_plan(ctx)
            if plan:
                self.current_plan = plan
                self.last_replan_tick = self.tick_count
                self.executor.load_plan(plan)
                logger.info(f"New plan: {plan.plan_id} with {len(plan.nodes)} subgoals")
        except Exception as e:
            logger.error(f"Replan error: {e}", exc_info=True)

    def _derive_skill_result(self) -> Optional[SkillResult]:
        """Derive a SkillResult from inventory diffs since the last tick.

        The poller reports no per-action results, so completion is inferred:
        if the active subgoal's success_criteria names an item that appeared
        or grew, report success with side_effects the executor understands.
        """
        try:
            active = self.executor._current if self.executor else None
            prop = self.current_state.proprioception if self.current_state else None
            inv = dict((prop.inventory or {}) if prop else {})
            prev = self._last_inventory
            self._last_inventory = inv
            if not active or not prev:
                return None
            criteria = active.subgoal.success_criteria or ""
            if not criteria.startswith("inventory_changed:"):
                return None
            item = criteria.split(":", 1)[1]
            if item in ("*", "craft_output"):
                grown = [k for k, v in inv.items() if v > prev.get(k, 0)]
                if grown:
                    return SkillResult(
                        skill_id=active.subgoal.skill_id,
                        success=True,
                        side_effects=[f"inventory_changed:{g}" for g in grown],
                    )
                return None
            if inv.get(item, 0) > prev.get(item, 0):
                return SkillResult(
                    skill_id=active.subgoal.skill_id,
                    success=True,
                    side_effects=[f"inventory_changed:{item}"],
                )
        except Exception as e:
            logger.debug(f"Derive skill result failed: {e}")
        return None

    async def _execute_tasks(self):
        """L2: Execute current subgoal"""
        if not self.current_state:
            return

        # Create a mock latent for skill selector
        latent = np.zeros(128, dtype=np.float32)
        if self.current_state.visual:
            latent = self.current_state.visual.features

        # Proprioception vector
        proprio = np.zeros(32, dtype=np.float32)
        if self.current_state.proprioception:
            prop = self.current_state.proprioception
            proprio[0] = prop.hp / prop.max_hp
            proprio[1] = prop.hunger / 20.0  # max_hunger is 20
            proprio[2] = prop.breath / 10.0
            proprio[3:6] = self._normalize_position(prop.position)
            proprio[6] = prop.yaw / np.pi
            proprio[7] = prop.pitch / (np.pi / 2)
            proprio[8] = 1.0 if prop.is_on_ground else 0.0
            for i, (item, count) in enumerate(list((prop.inventory or {}).items())[:20]):
                try:
                    proprio[9 + i] = min(float(count) / 64.0, 1.0)
                except (TypeError, ValueError):
                    continue

        full_latent = np.concatenate([latent[:96], proprio])

        # Execute task executor tick
        # Derive skill_result from inventory diffs: the poller reports no
        # explicit per-action results, so a subgoal whose success_criteria
        # names an item (inventory_changed:X) completes when X appears/grows.
        skill_result = self._derive_skill_result()
        skill_ctx = self.executor.tick(skill_result, self.current_state, full_latent)

        if skill_ctx:
            # Queue skill for execution
            self._queue_skill(skill_ctx)

    async def _select_skill(self):
        """L1: Select skill based on context"""
        if not self.current_state:
            return

        latent = np.zeros(128, dtype=np.float32)
        if self.current_state.visual:
            latent = self.current_state.visual.features

        skill_params = self.selector.select(latent, self.current_state)
        if skill_params:
            ctx = SkillContext(
                active_skill=skill_params.skill_id,
                params=skill_params.params,
                priority=skill_params.priority,
                interrupt_on=[],
            )
            # Must wrap in ActiveSubgoal: the executor invariant is
            # _current: ActiveSubgoal (raw Subgoal here crashed
            # get_current_subgoal/_derive_skill_result/_log_status).
            self.executor._current = ActiveSubgoal(
                subgoal=Subgoal(
                    subgoal_id=f"skill_{skill_params.skill_id.value}_{uuid.uuid4().hex[:8]}",
                    skill_id=skill_params.skill_id,
                    params=skill_params.params,
                    preconditions=[],
                    success_criteria="skill_complete",
                    timeout_ticks=300,
                ),
                status=SubgoalStatus.ACTIVE,
                started_tick=self.executor._tick,
                last_progress_tick=self.executor._tick,
            )
            # The plan is exhausted (IDLE) at this point; without forcing
            # EXECUTING the injected skill never drives, times out, or
            # completes — a live loop with a zombie subgoal and no actions.
            self.executor._state = ExecutorState.EXECUTING
            self.executor._current.skill_params = skill_params
            ctx.continuous_bias = skill_params.continuous_bias
            ctx.discrete_triggers = skill_params.discrete_triggers
            self._queue_skill(ctx)

    def _queue_skill(self, skill_ctx: SkillContext):
        """Queue skill for execution via bridge (poller-compatible action)."""
        # 背壓：poller 2s 取一次，agent 10Hz 生產會淹沒 queue；超過上限就丟棄
        try:
            if len(getattr(self.bridge, "pending_actions", [])) >= 3:
                return
        except Exception:
            pass
        skill_id = skill_ctx.active_skill.value
        params = skill_ctx.params or {}
        bias = getattr(skill_ctx, "continuous_bias", None)
        triggers = getattr(skill_ctx, "discrete_triggers", {}) or {}

        def _f(i, default=0.0):
            try:
                return float(bias[i])
            except Exception:
                return default

        if skill_id in ("move", "navigate"):
            action = {
                "type": "move",
                "forward": params.get("forward", _f(0, 1.0)),
                "strafe": params.get("strafe", _f(1, 0.0)),
                "jump": bool(params.get("jump", triggers.get("jump", 0) > 0.5)),
            }
        elif skill_id == "look":
            action = {
                "type": "look",
                "yaw_delta": params.get("yaw", _f(0, 0.0)),
                "pitch_delta": params.get("pitch", _f(1, 0.0)),
            }
        elif skill_id in ("dig", "combat"):
            action = {"type": "dig"}
        elif skill_id in ("place", "build", "eat"):
            action = {"type": "place"}
        elif skill_id == "craft":
            action = {"type": "craft", "recipe": params.get("recipe_id", "auto")}
        else:
            action = {"type": "move", "forward": 0.5, "strafe": 0.0}
        try:
            self.bridge.queue_action(action)
        except Exception as e:
            logger.error(f"Queue skill failed: {e}")

    async def _execute_reflex(self):
        """L0: Execute reflex actions via bridge"""
        if not self.current_state or not self.current_state.proprioception:
            return

        # Get pending actions from bridge
        # This is handled by the polling bridge automatically
        pass

    async def _consolidate_memory(self):
        """Consolidate experiences into long-term memory"""
        if not self.memory or not self.current_state:
            return

        # Store recent experience
        exp = {
            "tick": self.tick_count,
            "position": (
                self.current_state.proprioception.position
                if self.current_state.proprioception
                else (0, 0, 0)
            ),
            "action": "autonomous",
            "context": {
                "goal": self.current_goal.value if self.current_goal else None,
                "subgoal": (
                    self.executor._current.subgoal.subgoal_id if self.executor._current else None
                ),
            },
            "outcome": {"position_change": True},
            "reward": 0.1,  # Small positive reward for surviving
            "tags": ["autonomous", "tick_" + str(self.tick_count)],
        }

        from ai.multimodal.game_memory_bridge import GameExperience, MemoryType

        exp_obj = GameExperience(
            exp_id=f"exp_{self.tick_count}",
            memory_type=MemoryType.EPISODIC,
            timestamp=time.time(),
            position=(
                self.current_state.proprioception.position
                if self.current_state.proprioception
                else (0, 0, 0)
            ),
            action="autonomous_tick",
            context=exp["context"],
            outcome=exp["outcome"],
            reward=exp["reward"],
            tags=exp["tags"],
        )
        await self.memory.store_experience(exp_obj)

        # Feed task outcomes into the shared affect/lifecycle loops so the
        # game agent and the chat pipeline react to the same history
        try:
            completed = len(getattr(self.executor, "_completed", []) or [])
            failed = len(getattr(self.executor, "_failed", []) or [])
            d_done = completed - self._last_completed
            d_fail = failed - self._last_failed
            self._last_completed, self._last_failed = completed, failed
            if d_done or d_fail:
                total = max(1, d_done + d_fail)
                engagement = (1.0 + d_done) / (1.0 + total)
                success = d_done >= d_fail
                if self.emotion is not None:
                    self.emotion.process_interaction_feedback(
                        engagement_ratio=engagement,
                        had_error=not success,
                        response_success=success,
                    )
                if self.lifecycle is not None and hasattr(
                    self.lifecycle, "feed_interaction_outcome"
                ):
                    self.lifecycle.feed_interaction_outcome(
                        engagement_ratio=engagement, success=success
                    )
        except Exception as e:
            logger.debug(f"Affect feedback failed: {e}")

    def _log_status(self):
        """Log agent status"""
        uptime = time.time() - self.start_time
        directive = self.strategy_engine.get_directive() if self.strategy_engine else {}
        logger.info(
            f"Tick {self.tick_count} | Uptime: {uptime:.1f}s | "
            f"Goal: {self.current_goal.value if self.current_goal else 'None'} | "
            f"Subgoal: {self.executor.get_current_subgoal().subgoal_id if self.executor and self.executor.get_current_subgoal() else 'None'} | "
            f"Exploration: {directive.get('exploration_weight', 0):.2f} | "
            f"Risk: {directive.get('risk_tolerance', 0):.2f}"
        )

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Shutting down Angela...")
        self.running = False

        if self.bridge:
            await self.bridge.stop()
        if self.llm:
            await self.llm.close()
        if self.memory:
            # Final save - create a proper experience object
            try:
                from ai.multimodal.game_memory_bridge import GameExperience, MemoryType

                exp = GameExperience(
                    exp_id=f"shutdown_{int(time.time())}",
                    memory_type=MemoryType.EPISODIC,
                    timestamp=time.time(),
                    position=(0, 0, 0),
                    action="shutdown",
                    context={},
                    outcome={},
                    reward=0.0,
                    tags=["shutdown"],
                )
                await self.memory.store_experience(exp)
            except Exception as e:
                logger.warning(f"Final memory save failed: {e}")

        logger.info("Angela shutdown complete")

    async def stop(self):
        """Stop the agent"""
        self.running = False


async def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    config = AngelaConfig()
    agent = AngelaAutonomousAgent(config)

    # Setup signal handlers
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(agent.stop()))

    try:
        await agent.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
