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
from ai.multimodal.game_behaviors import BEHAVIORS, BehaviorFeedback, expand_behavior
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
        # Dialogue + behavior-runner state (in-game interaction loop)
        self._pending_chats: List[Dict[str, Any]] = []
        self._chat_history: Deque[str] = deque(maxlen=12)
        self._active_behavior: Optional[Dict[str, Any]] = None
        self._last_behavior_feed_tick: int = 0
        self._behavior_followup: Optional[Dict[str, Any]] = None
        # Cooperative action slot: the runner's feed sets a hold so the
        # 10Hz executor doesn't overwrite it before the 0.5Hz poll drains
        # it (observed: 4 consecutive vision actions died in queue).
        # Auto-expires after 30 ticks so a stuck runner can't mute plans.
        self._behavior_hold_tick: int = -1000
        self._last_goto: Optional[Dict[str, Any]] = None
        self._last_scan: Optional[Dict[str, Any]] = None
        self._last_vision: Optional[Dict[str, Any]] = None

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

        # Initialize LLM interface: local llama.cpp server (fully offline).
        # Falls back to rules per-call when the model is unreachable.
        llm_config = LLMConfig(
            enabled=True,
            provider="llamacpp",
            base_url="http://127.0.0.1:8080/v1",
            model="data/models/qwen2.5-1.5b-instruct-q4_k_m.gguf",
            timeout_sec=60.0,
            max_tokens=512,
            temperature=0.4,
        )
        self.llm = LLMGameInterface(llm_config)
        logger.info("LLM interface initialized (local llama.cpp)")

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

                # 4b. In-game dialogue: one reply task per overheard chat
                if self._pending_chats:
                    chats, self._pending_chats = self._pending_chats, []
                    for ev in chats:
                        asyncio.create_task(self._handle_chat_event(ev))

                # 4c. Behavior runner: feed LLM-composed behavior actions
                await self._tick_behavior()

                # 4d. Periodic eyes: look around every ~15s when idle, so
                # aiming and water-flinch run without chat prompts.
                if (
                    not self._active_behavior
                    and self.current_state
                    and self.tick_count % 150 == 0
                ):
                    self._start_behavior("look_vision", {"range": 24}, "periodic-eyes")

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

            # Drain overheard player chat (in-process bridge, no HTTP)
            try:
                fresh = self.bridge.take_chat_events()
                if fresh:
                    self._pending_chats.extend(fresh)
            except Exception as e:
                logger.debug(f"Chat drain failed: {e}")

            # Coordinate-walk + survey + vision status
            try:
                self._last_goto = state.get("goto_") if state else None
                scan = state.get("scan") if state else None
                if scan:
                    self._last_scan = scan
                vision = state.get("vision") if state else None
                if vision:
                    self._last_vision = vision
            except Exception as e:
                logger.debug(f"Goto/scan/vision perception failed: {e}")

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
            from ai.multimodal.game_memory_bridge import ITEM_ALIASES, normalize_inventory

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
            # Both sides folded to short names: the game reports
            # default:pick_wood, criteria says wooden_pickaxe.
            norm = normalize_inventory(inv)
            norm_prev = normalize_inventory(prev)
            item = ITEM_ALIASES.get(criteria.split(":", 1)[1], criteria.split(":", 1)[1])
            if item in ("*", "craft_output"):
                grown = [k for k, v in norm.items() if v > norm_prev.get(k, 0)]
                if grown:
                    return SkillResult(
                        skill_id=active.subgoal.skill_id,
                        success=True,
                        side_effects=[f"inventory_changed:{g}" for g in grown],
                    )
                return None
            if norm.get(item, 0) > norm_prev.get(item, 0):
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
            # Undirected L1 placement entombs the agent (observed: boxed
            # herself in cobble/sand, then "no free cell" forever). Placement
            # only comes from plans, LLM behaviors, or chat from now on.
            # BUILD maps to the same place action (no blueprint runner
            # exists), so it abstains too — observed stacking dirt piles.
            if skill_params.skill_id in (SkillID.PLACE, SkillID.BUILD):
                logger.info(f"L1 {skill_params.skill_id.value} abstained (undirected placement)")
                return
            # Abstain from uncraftable crafts: the L1 path carries no
            # template preconditions, so without this gate it queues
            # doomed auto-crafts every tick (observed log spam). The
            # selector already recorded _last_used, so cooldown rotates.
            if skill_params.skill_id == SkillID.CRAFT and self.memory:
                from ai.multimodal.game_memory_bridge import normalize_inventory

                prop = self.current_state.proprioception
                inv = dict((prop.inventory if prop else {}) or {})
                rid = (skill_params.params or {}).get("recipe_id", "auto")
                craftable = False
                if rid and rid != "auto":
                    rec = self.memory.get_recipe(rid)
                    if rec:
                        norm = normalize_inventory(inv)
                        craftable = all(
                            norm.get(ing, 0) >= cnt
                            for ing, cnt in rec.ingredients.items()
                        )
                else:
                    craftable = bool(self.memory.get_craftable_recipes(inv))
                if not craftable:
                    logger.info(f"L1 craft abstained (nothing craftable for {rid})")
                    return
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
        # Yield to a runner-fed behavior action: the executor's 10Hz writes
        # would otherwise overwrite it before the 0.5Hz poll drains it.
        if self.tick_count - self._behavior_hold_tick < 30:
            return
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
            # All locomotion is coordinate-grounded: step_ahead resolves
            # facing in Lua (exact); blind directional moves are gone.
            # A nonzero yaw param (recovery unstick) becomes a real turn —
            # it used to be silently dropped, so recovery never turned.
            try:
                yaw_param = float(params.get("yaw", 0.0) or 0.0)
            except (TypeError, ValueError):
                yaw_param = 0.0
            if yaw_param != 0.0 and self.tick_count % 3 == 0:
                # Spiral out: turn one tick in three, step the others.
                action = {"type": "look", "yaw_delta": yaw_param, "pitch_delta": 0.0}
            else:
                try:
                    fwd = float(params.get("forward", _f(0, 1.0)))
                except (TypeError, ValueError):
                    fwd = 1.0
                action = {
                    "type": "step_ahead",
                    "dist": 4.5,
                    "backward": bool(fwd < 0),
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

    def _state_summary(self) -> str:
        """One-paragraph snapshot for LLM prompts (dialogue/compose)."""
        try:
            prop = self.current_state.proprioception if self.current_state else None
            pos = getattr(prop, "position", (0, 0, 0)) if prop else (0, 0, 0)
            inv = dict(getattr(prop, "inventory", {}) or {}) if prop else {}
            hp = f"{getattr(prop, 'hp', '?')}/{getattr(prop, 'max_hp', 20)}" if prop else "?"
            goal = self.current_goal.value if self.current_goal else "none"
            cur = self.executor.get_current_subgoal() if self.executor else None
            sg = cur.subgoal_id if cur else "none"
            return f"位置 {pos}，背包 {inv or '空'}，血量 {hp}，當前目標 {goal}，子目標 {sg}"
        except Exception:
            return "狀態未知"

    async def _handle_chat_event(self, ev: Dict[str, Any]):
        """Overheard a player: LLM decides what to say + do (with fallback)."""
        player = str(ev.get("player", "?"))
        message = str(ev.get("message", "")).strip()
        if not message or player == "Angela" or message.startswith("[Angela]"):
            return
        logger.info(f"Overheard chat from {player}: {message}")

        summary = self._state_summary()
        history = list(self._chat_history)
        say, bid, bparams = "", "", {}
        try:
            dec = await self.llm.adecide_chat(player, message, summary, history)
            say, bid, bparams = (dec.say or "").strip(), dec.behavior_id or "", dec.params or {}
        except Exception as e:
            logger.warning(f"LLM chat decision failed, keyword fallback: {e}")
            say, bid, bparams = self._fallback_chat(player, message)

        say = say[:300]
        # Echo guard: small models sometimes parrot the input as the reply.
        if say and message and (say.strip() == message.strip() or message.strip() in say and len(say) < len(message) + 8):
            logger.warning(f"LLM echoed chat, using fallback line instead")
            say, bid, bparams = self._fallback_chat(player, message)
            say = say[:300]
        logger.info(f"Angela replies to {player}: {say}")
        if say:
            self._chat_history.append(f"{player}: {message}")
            self._chat_history.append(f"Angela: {say}")
            try:
                self.bridge.queue_action({"type": "chat", "message": say})
            except Exception as e:
                logger.error(f"Queue chat failed: {e}")
        if bid and bid in BEHAVIORS:
            self._start_behavior(bid, bparams, f"chat:{player}")

        try:
            if self.memory:
                from ai.multimodal.game_memory_bridge import GameExperience, MemoryType

                prop = self.current_state.proprioception if self.current_state else None
                pos = tuple(getattr(prop, "position", (0, 0, 0)) or (0, 0, 0))
                await self.memory.store_experience(
                    GameExperience(
                        exp_id=f"chat_{int(time.time() * 1000)}",
                        memory_type=MemoryType.EPISODIC,
                        timestamp=time.time(),
                        position=(float(pos[0]), float(pos[1]), float(pos[2])),
                        action="chat",
                        context={"player": player, "message": message},
                        outcome={"say": say, "behavior": bid},
                        reward=0.5,
                        tags=["chat", player],
                    )
                )
        except Exception as e:
            logger.debug(f"Chat memory store failed: {e}")

    @staticmethod
    def _fallback_chat(player: str, message: str):
        """Keyword intent fallback when the LLM is unreachable."""
        if any(k in message for k in ("砍", "樹", "tree", "chop")):
            return "好，我去找棵樹砍！", "scout", {"node": "default:tree"}
        if any(k in message for k in ("挖", "dig", "採")):
            return "收到，我來挖！", "dig_burst", {"n": 5}
        if any(k in message for k in ("來", "過來", "come", "follow", "跟")):
            return "我來了！", "walk", {"steps": 3}
        if any(k in message for k in ("停", "等", "wait", "stop")):
            return "好，我待一下。", "wait", {"ticks": 30}
        if any(k in message for k in ("轉", "看", "turn", "look")):
            return "我看看四周。", "look_scan", {}
        return "我在呢，我聽到了！", "", {}

    def _start_behavior(self, bid: str, params: Dict[str, Any], reason: str):
        b = BEHAVIORS.get(bid)
        if not b:
            return
        ok, missing = b.preconditions(self.current_state)
        merged = b.with_defaults(params)
        basis = self._last_vision if b.wait_for == "vision" else self._last_scan
        basis_seq = basis.get("seq", 0) if isinstance(basis, dict) else 0
        self._active_behavior = {
            "id": bid,
            "params": merged,
            "reason": reason,
            "actions": expand_behavior(bid, merged, self.current_state) if ok else [],
            "idx": 0,
            "started": self.tick_count,
            "inv_start": dict(self._last_inventory or {}),
            "retries": 0,
            "blocked": not ok,
            "missing": missing,
            "wait_for": b.wait_for,
            "scan_seq": basis_seq,
            "goto_basis": self._last_goto,
        }
        logger.info(f"Behavior started: {bid} ({reason}) blocked={not ok} {missing}")

    async def _tick_behavior(self):
        """Feed one behavior action per drain; settle on done/timeout."""
        ab = self._active_behavior
        if not ab:
            return
        b = BEHAVIORS.get(ab["id"])
        if not b:
            self._active_behavior = None
            return

        if ab.get("blocked"):
            await self._settle_behavior(False, f"blocked:{','.join(ab.get('missing', []))}")
            return

        actions = ab["actions"]
        if not actions:
            # wait counts ticks; anything else expanding to nothing means
            # bad params (e.g. LLM goto without pos) — fail, don't fake success.
            if ab["id"] != "wait":
                await self._settle_behavior(False, "empty_expand")
                return
            target = int(ab["params"].get("ticks", 20))
            if self.tick_count - ab["started"] >= max(target, 1):
                await self._settle_behavior(True, "")
            return

        if ab["idx"] >= len(actions):
            # Two-phase grounding: scout/vision wait for their survey, then
            # either flinch (rule) or the LLM picks a coordinate and chains
            # the next behavior. Timeouts guard lost surveys.
            wait_for = ab.get("wait_for", "")
            if wait_for in ("scan", "vision"):
                store = self._last_scan if wait_for == "scan" else self._last_vision
                store = store if isinstance(store, dict) else None
                if store and store.get("seq", 0) != ab.get("scan_seq", 0):
                    if wait_for == "scan":
                        await self._finish_scout(ab, store)
                    else:
                        await self._finish_vision(ab, store)
                    return
                if self.tick_count - ab["started"] > 120:
                    await self._settle_behavior(False, f"{wait_for}_timeout")
                return
            if b.success_criteria == "arrived":
                # Freshness: ignore reports predating this behavior, or a
                # previous walk's failure settles the new one instantly.
                cur = self._last_goto if isinstance(self._last_goto, dict) else None
                if cur is not None and cur is not ab.get("goto_basis"):
                    status = cur.get("status")
                    if status == "arrived":
                        await self._settle_behavior(True, "")
                        return
                    if status in ("failed", "aborted"):
                        await self._settle_behavior(
                            False, f"goto_{cur.get('reason', 'unknown')}"
                        )
                        return
                return
            pickups = self._behavior_pickups(ab)
            if b.success_criteria == "any_pickup" and not pickups:
                # Give the last fed action a full poll cycle to land before
                # calling it a miss (observed: dig_at judged 0.1s after feed).
                if (self.tick_count - self._last_behavior_feed_tick) < 25:
                    return
                if b.adjust and ab["retries"] < 1:
                    ab["params"] = b.adjust(
                        ab["params"],
                        BehaviorFeedback(
                            behavior_id=ab["id"],
                            params=ab["params"],
                            ticks_used=self.tick_count - ab["started"],
                            pickups=pickups,
                            completed=False,
                            fail_reason="no_pickup",
                        ),
                    )
                    ab["actions"] = b.expand(ab["params"], self.current_state)
                    ab["idx"] = 0
                    ab["started"] = self.tick_count
                    ab["retries"] += 1
                    logger.info(f"Behavior adjusted: {ab['id']} -> {ab['params']}")
                    return
                await self._settle_behavior(False, "no_pickup")
                return
            # steps_done: settle only after the queue demonstrably drained
            # (slot-hold mutes the executor, so empty really means consumed).
            try:
                drained = len(getattr(self.bridge, "pending_actions", [])) == 0
            except Exception:
                drained = False
            if drained and (self.tick_count - self._last_behavior_feed_tick) >= 15:
                await self._settle_behavior(True, "")
            return

        try:
            pending = len(getattr(self.bridge, "pending_actions", []))
        except Exception:
            pending = 0
        if pending == 0 or (self.tick_count - self._last_behavior_feed_tick) >= 20:
            nxt = actions[ab["idx"]]
            ab["idx"] += 1
            self._last_behavior_feed_tick = self.tick_count
            self._behavior_hold_tick = self.tick_count
            try:
                self.bridge.queue_action(nxt)
            except Exception as e:
                logger.error(f"Queue behavior action failed: {e}")

        limit = 600 if b.success_criteria == "arrived" else 60 + 25 * len(actions)
        if self.tick_count - ab["started"] > limit:
            await self._settle_behavior(False, "timeout")

    def _behavior_pickups(self, ab: Dict[str, Any]) -> Dict[str, int]:
        try:
            prop = self.current_state.proprioception if self.current_state else None
            cur = dict((prop.inventory if prop else {}) or {})
        except Exception:
            cur = {}
        start = ab.get("inv_start", {}) or {}
        out = {}
        for k, v in cur.items():
            try:
                grown = int(v) - int(start.get(k, 0))
            except (TypeError, ValueError):
                continue
            if grown > 0:
                out[str(k)] = grown
        return out

    async def _settle_behavior(self, completed: bool, reason: str):
        ab = self._active_behavior
        self._active_behavior = None
        if not ab:
            return
        pickups = self._behavior_pickups(ab)
        logger.info(
            f"Behavior settled: {ab['id']} completed={completed} "
            f"reason={reason} pickups={pickups}"
        )
        # Follow-up chain (e.g. scout -> goto -> dig_at the tree): the
        # finished behavior leaves the next link, run only on success.
        if completed:
            follow = getattr(self, "_behavior_followup", None)
            self._behavior_followup = None
            if follow and follow.get("behavior_id") in BEHAVIORS:
                logger.info(f"Behavior follow-up: {follow['behavior_id']}")
                self._start_behavior(
                    follow["behavior_id"], follow.get("params", {}), "follow-up"
                )
        try:
            if self.memory:
                from ai.multimodal.game_memory_bridge import GameExperience, MemoryType

                prop = self.current_state.proprioception if self.current_state else None
                pos = tuple(getattr(prop, "position", (0, 0, 0)) or (0, 0, 0))
                await self.memory.store_experience(
                    GameExperience(
                        exp_id=f"behavior_{int(time.time() * 1000)}",
                        memory_type=MemoryType.PROCEDURAL,
                        timestamp=time.time(),
                        position=(float(pos[0]), float(pos[1]), float(pos[2])),
                        action=ab["id"],
                        context={"params": ab["params"], "reason": ab.get("reason", "")},
                        outcome={"completed": completed, "reason": reason, "pickups": pickups},
                        reward=1.0 if completed else -0.2,
                        tags=["behavior", ab["id"]],
                    )
                )
        except Exception as e:
            logger.debug(f"Behavior memory store failed: {e}")

    async def _finish_scout(self, ab: Dict[str, Any], scan: Dict[str, Any]):
        """Scout phase two: LLM turns surveyed nodes into a goto coordinate."""
        nodes = scan.get("nodes", []) or []
        node_lines = "\n".join(
            f"- {n.get('node')} at ({n.get('x')},{n.get('y')},{n.get('z')})" for n in nodes[:12]
        )
        await self._settle_behavior(True, "scan_done")
        if not nodes:
            logger.info("Scout found nothing")
            return
        task = (
            f"從掃描結果選一個地點走過去（{ab['params'].get('node', '')}，"
            f"原因是: {ab.get('reason', '')}）。偏好最近的，目的地站在目標旁邊 "
            f"2 米（y 取目標 y）。\n掃描結果:\n{node_lines}"
        )
        picked_pos = None
        picked_walked = False
        try:
            from ai.multimodal.game_behaviors import AIM_BEHAVIORS

            order = await self.llm.acompose_behavior(
                task, self._state_summary(), [], only_behaviors=AIM_BEHAVIORS, max_tokens=128
            )
            if order.behavior_id in ("goto", "look_at", "dig_at") and order.params.get(
                "pos"
            ):
                picked_pos = order.params["pos"]
                picked_walked = order.behavior_id == "goto"
                self._start_behavior(
                    order.behavior_id, order.params, f"scout-pick:{ab['id']}"
                )
            else:
                logger.warning(f"Scout pick rejected (no pos): {order.behavior_id}")
        except Exception as e:
            logger.warning(f"Scout pick LLM failed, nearest fallback: {e}")
        if picked_pos is None:
            if not nodes:
                return
            n0 = nodes[0]
            picked_pos = {"x": n0["x"], "y": n0["y"], "z": n0["z"]}
            picked_walked = True
            self._start_behavior("goto", {"pos": picked_pos}, "scout-fallback")
        # After walking to a scouted resource, dig it: scout -> goto ->
        # dig_at completes "go chop that tree" as one intent. Only when
        # she actually walked there (dig_at reaches 6.5m).
        if picked_walked:
            self._behavior_followup = {"behavior_id": "dig_at", "params": {"pos": picked_pos}}

    async def _finish_vision(self, ab: Dict[str, Any], vision: Dict[str, Any]):
        """Vision phase two: aim at interest (LLM).

        Water avoidance is NOT here: it lives in the poller as a per-poll
        forward-ray reflex. A 15s-cadence runner branch is a decision, and
        calling it a reflex was a layering mistake.
        """
        rays = vision.get("rays", []) or []
        await self._settle_behavior(True, "vision_done")
        if not rays:
            return
        boring = {"air", "default:dirt", "default:sand", "default:dirt_with_grass"}
        if all(str(r.get("node", "air")) in boring for r in rays):
            logger.debug("Vision: nothing interesting")
            return
        ray_lines = "\n".join(
            f"- {r.get('node')} {r.get('dist')}m (yaw {r.get('yaw_off')})" for r in rays
        )
        task = (
            "你剛睜眼看了四周。選一個最值得注意的東西（優先樹/煤/石頭，忽略空氣；"
            "全是土和沙就選個近的）：3 米內用 look_at 面對它或 dig_at 挖它，"
            "3 米外用 goto 走過去。只做一步。\n"
            f"視線:\n{ray_lines}"
        )
        try:
            from ai.multimodal.game_behaviors import AIM_BEHAVIORS

            order = await self.llm.acompose_behavior(
                task, self._state_summary(), [], only_behaviors=AIM_BEHAVIORS, max_tokens=128
            )
            if order.behavior_id in ("look_at", "goto", "dig_at") and order.params.get("pos"):
                self._start_behavior(order.behavior_id, order.params, "vision-aim")
                return
            logger.info(f"Vision aim stood down: {order.behavior_id}")
        except Exception as e:
            logger.warning(f"Vision aim LLM failed: {e}")

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
