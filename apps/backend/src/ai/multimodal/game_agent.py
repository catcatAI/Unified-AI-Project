"""
Game Agent - 主控制器，串聯 L0-L4 五層架構

完整流程：
L4 Strategy -> L3 Planner -> L2 Task Executor -> L1 Skill Selector -> L0 Policy -> Luanti
                    ^              |               |              |           |
                    |              v               v              v           v
                LLM 非同步      重規劃/記憶      卡住檢測/進度   技能選擇/參數  視覺/動作
"""

import asyncio
import logging
import signal
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple

import numpy as np
from integrations.luanti_connector import (
    GameSnapshot,
    LuantiConfig,
    LuantiConnector,
    SyncLuantiConnector,
)

from .foveated_sampler import FoveatedSampler, SamplingConfig, SamplingStrategy, create_sampler_from_config
from .game_memory_bridge import GameMemoryBridge, MockHAMManager
from .game_planner import GamePlanner, GoalManager, GoalType, PlannerConfig, PlanningContext
from .game_policy import GamePolicy, PolicyConfig, PolicyOutput
from .game_strategy import GameStrategy, StrategyConfig
from .game_structs import (
    GameState,
    Proprioception,
    StrategyDirective,
    TaskProgress,
    VisualObservation,
)
from .game_task_executor import ExecutorConfig, GameTaskExecutor, SkillContext
from .llm_game_interface import LLMConfig, LLMGameInterface, RuleBasedFallback
from .skill_selector import SelectorConfig, SkillSelector

logger = logging.getLogger(__name__)


@dataclass
class GameAgentConfig:
    # 視覺
    vision_budget_pixels: int = 83000
    vision_fovea_ratio: float = 0.7
    vision_fps: int = 20
    vision_input_size: Tuple[int, int] = (64, 64)
    sampling_strategy: SamplingStrategy = SamplingStrategy.LOG_POLAR

    # 策略
    policy_latent_dim: int = 128
    policy_continuous_dim: int = 16
    policy_discrete_dim: int = 8
    policy_use_diffusion: bool = True

    # 技能選擇
    selector_temperature: float = 1.0

    # 任務執行
    stuck_threshold_ticks: int = 600
    max_subgoal_retries: int = 3

    # 規劃
    planner_max_depth: int = 10
    planner_use_llm: bool = True
    planner_llm_timeout: float = 5.0

    # 策略
    strategy_update_interval: float = 60.0

    # LLM
    llm_enabled: bool = True
    llm_provider: Literal["ollama", "openai", "vllm", "custom", "llamacpp"] = "ollama"
    llm_base_url: str = "http://localhost:11434/v1"
    llm_model: str = "qwen2.5:7b"

    # Luanti
    luanti_host: str = "localhost"
    luanti_port: int = 30000
    luanti_password: str = ""

    # 執行
    max_ticks: int = 0  # 0 = 無限
    tick_interval: float = 0.05  # 20 FPS = 50ms
    save_interval: int = 1000

    # 路徑
    memory_path: str = "data/game_memory"
    strategy_path: str = "data/strategy_weights.json"


class GameAgent:
    """
    Angela Game Agent - Luanti 自主遊戲代理

    五層架構：
    L0: Reflex (Foveated Sampler + Policy)
    L1: Skill Selector
    L2: Task Executor
    L3: Planner (+ LLM)
    L4: Strategy

    Memory: GameMemoryBridge (HAM)
    Interface: LuantiConnector
    """

    def __init__(self, config: Optional[GameAgentConfig] = None):
        self.config = config or GameAgentConfig()
        self._running = False
        self._tick = 0
        self._start_time = 0.0
        self._last_tick_time = 0.0

        # 核心組件（__init__ 內由 _init_components 必定填充，非可選）
        self._sampler: FoveatedSampler = None  # type: ignore[assignment]
        self._policy: GamePolicy = None  # type: ignore[assignment]
        self._selector: SkillSelector = None  # type: ignore[assignment]
        self._executor: GameTaskExecutor = None  # type: ignore[assignment]
        self._planner: GamePlanner = None  # type: ignore[assignment]
        self._memory: GameMemoryBridge = None  # type: ignore[assignment]
        self._strategy: GameStrategy = None  # type: ignore[assignment]
        self._luanti: LuantiConnector = None  # type: ignore[assignment]
        self._goal_manager: GoalManager = None  # type: ignore[assignment]
        # LLM 為條件式組件（config.llm_enabled=False 時保持 None）
        self._llm: Optional[LLMGameInterface] = None

        # 狀態
        self._state = GameState()
        self._current_skill_result: Optional[Any] = None
        self._pending_actions: Dict[str, Any] = {}

        # 回調
        self._tick_callbacks: List[Callable] = []

        self._init_components()

    def _init_components(self):
        """初始化所有組件"""
        # 視覺採樣器
        sampler_config = SamplingConfig(
            budget_pixels=self.config.vision_budget_pixels,
            fovea_ratio=self.config.vision_fovea_ratio,
            output_size=self.config.vision_input_size,
            strategy=self.config.sampling_strategy,
        )
        self._sampler = FoveatedSampler(sampler_config)

        # L0 Policy
        policy_config = PolicyConfig(
            latent_dim=self.config.policy_latent_dim,
            continuous_dim=self.config.policy_continuous_dim,
            discrete_dim=self.config.policy_discrete_dim,
            use_diffusion=self.config.policy_use_diffusion,
        )
        self._policy = GamePolicy(policy_config)

        # L1 Skill Selector
        selector_config = SelectorConfig(
            temperature=self.config.selector_temperature,
        )
        self._selector = SkillSelector(selector_config)

        # L2 Task Executor
        executor_config = ExecutorConfig(
            stuck_threshold_ticks=self.config.stuck_threshold_ticks,
            max_subgoal_retries=self.config.max_subgoal_retries,
        )
        self._executor = GameTaskExecutor(executor_config)
        self._executor.set_replan_callback(self._on_replan_requested)

        # L3 Planner
        planner_config = PlannerConfig(
            max_plan_depth=self.config.planner_max_depth,
            use_llm_for_complex=self.config.planner_use_llm,
            llm_timeout_sec=self.config.planner_llm_timeout,
        )
        self._planner = GamePlanner(planner_config)

        # L4 Strategy
        strategy_config = StrategyConfig(
            update_interval_sec=self.config.strategy_update_interval,
            persistence_path=self.config.strategy_path,
        )
        self._strategy = GameStrategy(strategy_config)

        # Memory Bridge
        self._memory = GameMemoryBridge()

        # LLM Interface
        if self.config.llm_enabled:
            llm_config = LLMConfig(
                enabled=True,
                provider=self.config.llm_provider,
                base_url=self.config.llm_base_url,
                model=self.config.llm_model,
            )
            self._llm = LLMGameInterface(llm_config)
            self._planner.set_llm(self._llm)
        else:
            logger.info("LLM disabled, using rule-based fallback")

        # Goal Manager
        self._goal_manager = GoalManager(self._planner)

        # 連接記憶與規劃器
        self._planner.set_memory(self._memory)

        # Luanti Connector
        luanti_config = LuantiConfig(
            host=self.config.luanti_host,
            port=self.config.luanti_port,
            password=self.config.luanti_password,
        )
        self._luanti = LuantiConnector(luanti_config)
        self._luanti.set_frame_callback(self._on_frame_received)

        logger.info("GameAgent components initialized")

    async def initialize(self) -> bool:
        """異步初始化 (連線 Luanti、載入記憶)"""
        logger.info("Initializing GameAgent...")

        # 連線 Luanti
        if not await self._luanti.connect():
            logger.error("Failed to connect to Luanti")
            return False

        # 初始化記憶
        await self._memory.initialize(MockHAMManager())

        # 載入預設目標
        self._goal_manager.add_goal(GoalType.SURVIVAL, priority=1.0)
        self._goal_manager.add_goal(GoalType.TOOL, priority=0.8)
        self._goal_manager.add_goal(GoalType.RESOURCE, priority=0.6)
        self._goal_manager.add_goal(GoalType.BUILD, priority=0.4)
        self._goal_manager.add_goal(GoalType.EXPLORE, priority=0.3)

        self._running = True
        self._start_time = time.time()
        logger.info("GameAgent initialized successfully")
        return True

    def _on_frame_received(self, frame: np.ndarray):
        """Luanti 畫面回調 (同步、需快速)"""
        if not self._running:
            return

        # Foveated Sampling
        focus = self._get_focus_point()
        result = self._sampler.sample(frame, focus)

        # 更新視覺觀測
        self._state.visual = VisualObservation(
            frame_id=self._tick,
            timestamp=time.time(),
            features=np.zeros(256, dtype=np.float32),  # 將由 visual encoder 填充
            fovea_xy=result.focus_xy,
            inverse_map=result.inverse_map,
            raw_frame_shape=frame.shape[:2],
        )

    def _get_focus_point(self) -> Tuple[int, int]:
        """獲取焦點 (來自 L1/L2/L3)"""
        # 優先級：L2 當前子目標 > L1 技能觸發 > L3 計劃焦點 > 畫面中心
        if self._executor._current and self._executor._current.subgoal.params.get("target_xy"):
            target = self._executor._current.subgoal.params["target_xy"]
            return (int(target[0]), int(target[1]))
        if self._state.visual:
            h, w = self._state.visual.raw_frame_shape
            return (w // 2, h // 2)
        return (320, 240)  # 預設

    def _on_replan_requested(self, task_id: str, blocker: str):
        """L2 請求重規劃回調"""
        logger.info(f"Replan requested for {task_id}: {blocker}")
        # 觸發 L3 重規劃 (非阻塞)
        asyncio.create_task(self._replan(blocker))

    async def _replan(self, blocker: str):
        """重規劃"""
        current_goal = self._goal_manager.get_highest_priority()
        if not current_goal:
            return

        goal, params = current_goal
        memories = await self._memory.recall_experience(goal.value, limit=10)
        strategy = self._strategy.get_directive()

        ctx = PlanningContext(
            current_goal=goal,
            goal_params=params,
            state=self._state,
            ham_memories=memories,
            strategy=StrategyDirective(**strategy),
            blocker=blocker,
        )

        new_plan = await self._planner.replan(ctx, blocker)
        self._executor.load_plan(new_plan)
        logger.info(f"Replan completed: {new_plan.plan_id}")

    async def run(self):
        """主循環"""
        if not self._running:
            if not await self.initialize():
                return

        logger.info("Starting GameAgent main loop...")

        try:
            while self._running:
                loop_start = time.perf_counter()

                # 1. 取得最新遊戲快照
                snapshot = self._luanti.get_latest_snapshot()
                if snapshot:
                    self._update_state_from_snapshot(snapshot)

                # 2. 視覺編碼 (如果有新幀)
                if self._state.visual:
                    await self._encode_visual()

                # 3. 策略更新 (L4)
                self._strategy.update(self._state)

                # 4. 規劃 (L3) - 非阻塞
                await self._maybe_replan()

                # 5. 任務執行 (L2) -> 產出 SkillContext
                skill_ctx = self._executor.tick(
                    self._current_skill_result,
                    self._state,
                    self._state.visual.features if self._state.visual else np.zeros(128),
                )

                # 5. 技能選擇 (L1) - 如果 L2 沒指定技能
                if skill_ctx is None:
                    skill_params = self._selector.select(
                        self._state.visual.features if self._state.visual else np.zeros(128),
                        self._state,
                    )
                    skill_ctx = SkillContext(
                        active_skill=skill_params.skill_id,
                        params=skill_params.params,
                        priority=skill_params.priority,
                        interrupt_on=[],
                    )

                # 6. Policy 推理 (L0)
                policy_out = self._policy.forward(
                    self._state.visual.features if self._state.visual else np.zeros(128),
                    self._proprioception_to_vector(self._state.proprioception),
                    self._state.visual.features if self._state.visual else None,  # 簡化
                )

                # 7. 合成動作
                actions = self._compose_actions(
                    policy_out, skill_ctx, skill_params if "skill_params" in locals() else None
                )

                # 8. 下發動作到 Luanti
                await self._send_actions(actions)

                # 9. 記錄技能結果 (下一幀使用)
                self._current_skill_result = self._create_skill_result(actions, policy_out)

                # 10. 記憶存儲 (非阻塞)
                if self._tick % 100 == 0:
                    asyncio.create_task(self._store_experience())

                # 11. Tick 計數與限制
                self._tick += 1
                if self.config.max_ticks > 0 and self._tick >= self.config.max_ticks:
                    break

                # 12. 回調
                for cb in self._tick_callbacks:
                    try:
                        cb(self._tick, self._state)
                    except Exception as e:
                        logger.error(f"Tick callback error: {e}")

                # 幀率控制
                elapsed = time.perf_counter() - loop_start
                sleep_time = self.config.tick_interval - elapsed
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                elif elapsed > self.config.tick_interval * 2:
                    logger.warning(f"Tick overtime: {elapsed*1000:.1f}ms")

        except asyncio.CancelledError:
            logger.info("GameAgent cancelled")
        except Exception as e:
            logger.error(f"GameAgent error: {e}", exc_info=True)
        finally:
            await self.shutdown()

    def _update_state_from_snapshot(self, snapshot: GameSnapshot):
        """從 Luanti 快照更新狀態"""
        self._state.tick = snapshot.tick
        self._state.timestamp = snapshot.timestamp
        self._state.proprioception = self._snapshot_to_proprioception(snapshot)

    def _snapshot_to_proprioception(self, snapshot: GameSnapshot) -> Proprioception:
        return Proprioception(
            health=snapshot.player.hp,
            max_health=snapshot.player.max_hp,
            hunger=snapshot.player.hunger,
            max_hunger=20,
            breath=snapshot.player.breath,
            position=snapshot.player.position,
            yaw=snapshot.player.yaw,
            pitch=snapshot.player.pitch,
            inventory=snapshot.player.inventory,
            wielded_item=snapshot.player.wielded_item,
            is_on_ground=snapshot.player.is_on_ground,
            is_in_water=snapshot.player.is_in_water,
        )

    async def _encode_visual(self):
        """視覺編碼 (使用現有 visual_encoder)"""
        # 這裡應調用 visual_encoder.encode_from_pil
        # 暫時用隨機特徵佔位
        if self._state.visual:
            # TODO: 整合 visual_encoder
            self._state.visual.features = np.random.randn(128).astype(np.float32)

    def _proprioception_to_vector(self, prop: Optional[Proprioception]) -> np.ndarray:
        """本體感覺轉向量 (32-dim)"""
        if not prop:
            return np.zeros(32, dtype=np.float32)

        vec = np.zeros(32, dtype=np.float32)
        vec[0] = prop.health / prop.max_health
        vec[1] = prop.hunger / prop.max_hunger
        vec[2] = prop.breath / 10.0
        vec[3:6] = prop.position
        vec[6] = prop.yaw / np.pi
        vec[7] = prop.pitch / (np.pi / 2)
        vec[8] = 1.0 if prop.is_on_ground else 0.0
        vec[9] = 1.0 if prop.is_in_water else 0.0
        vec[10] = 1.0 if prop.is_in_lava else 0.0
        # 背包編碼 (簡化)
        for i, (item, count) in enumerate(list(prop.inventory.items())[:20]):
            vec[11 + i] = min(count / 64.0, 1.0)
        return vec

    async def _maybe_replan(self):
        """檢查是否需要規劃"""
        if self._executor._state.value == "executing" and not self._executor._queue:
            # 隊列空，需要新計劃
            current = self._goal_manager.get_highest_priority()
            if current:
                goal, params = current
                memories = await self._memory.recall_experience(goal.value, limit=10)
                strategy = self._strategy.get_directive()

                ctx = PlanningContext(
                    current_goal=goal,
                    goal_params=params,
                    state=self._state,
                    ham_memories=memories,
                    strategy=StrategyDirective(**strategy),
                )

                plan = await self._planner.propose_plan(ctx)
                self._executor.load_plan(plan)

    def _compose_actions(
        self, policy_out: PolicyOutput, skill_ctx: SkillContext, skill_params: Optional[Any] = None
    ) -> Dict[str, Any]:
        """合成最終動作"""
        actions = {}

        # 從 policy 獲取基礎動作
        base_actions = self._policy.get_action_dict(policy_out)
        actions.update(base_actions)

        # 從 skill_params 獲取技能特定動作
        if skill_params:
            skill_actions = self._policy.get_action_dict(
                type(
                    "obj",
                    (object,),
                    {
                        "continuous": skill_params.continuous_bias,
                        "discrete_logits": np.array(
                            [
                                1.0 if k in skill_params.discrete_triggers else -1.0
                                for k in [
                                    "attack",
                                    "use",
                                    "jump",
                                    "sprint",
                                    "sneak",
                                    "inventory",
                                    "craft_grid",
                                    "craft_output",
                                ]
                            ]
                        ),
                    },
                )()
            )
            actions.update(skill_actions)

        # Grounding 點擊
        if self._state.visual and self._state.visual.inverse_map is not None:
            click = self._policy.get_grounding_click(policy_out, self._state.visual.inverse_map)
            if click:
                actions["click_xy"] = click

        return actions

    async def _send_actions(self, actions: Dict[str, Any]):
        """發送動作到 Luanti"""
        if "move" in actions:
            await self._luanti.move(**actions["move"])
        if "look" in actions:
            await self._luanti.look(**actions["look"])
        if actions.get("dig"):
            await self._luanti.dig()
        if actions.get("place"):
            await self._luanti.place()
        if "click_xy" in actions:
            # 點擊特定座標 (需 CSM 支援)
            await self._luanti.send_action(
                {"type": "click", "x": actions["click_xy"][0], "y": actions["click_xy"][1]}
            )

    def _create_skill_result(self, actions: Dict, policy_out: PolicyOutput) -> Any:
        """建立技能結果 (下一幀給 L2 用)"""
        # 簡化：實際應從 Luanti 回應解析
        from .game_structs import SkillID, SkillResult

        return SkillResult(skill_id=SkillID.MOVE, success=True, side_effects=[], duration_ticks=1)

    async def _store_experience(self):
        """存儲經驗到記憶"""
        from .game_memory_bridge import GameExperience, MemoryType

        exp = GameExperience(
            exp_id=f"exp_{self._tick}",
            memory_type=MemoryType.EPISODIC,
            timestamp=time.time(),
            position=(
                self._state.proprioception.position if self._state.proprioception else (0, 0, 0)
            ),
            action="tick",
            context={"tick": self._tick, "goals": [g.value for g, _, _ in self._goal_manager.active_goals]},
            outcome={"actions": list(self._pending_actions.keys())},
            reward=0.0,
            tags=["tick"],
        )
        await self._memory.store_experience(exp)

    def add_tick_callback(self, callback: Callable[[int, GameState], None]):
        """添加 tick 回調 (用於監控/視覺化)"""
        self._tick_callbacks.append(callback)

    async def shutdown(self):
        """關閉"""
        logger.info("Shutting down GameAgent...")
        self._running = False

        if self._luanti:
            await self._luanti.disconnect()

        if self._llm:
            await self._llm.close()

        self._strategy.on_session_end()

        logger.info(f"GameAgent stopped at tick {self._tick}")

    def get_status(self) -> Dict[str, Any]:
        """獲取狀態摘要"""
        current_subgoal = self._executor.get_current_subgoal()
        return {
            "tick": self._tick,
            "running": self._running,
            "uptime_sec": time.time() - self._start_time,
            "state": self._executor._state.value,
            "current_subgoal": current_subgoal.subgoal_id if current_subgoal else None,
            "queue_length": len(self._executor._queue),
            "strategy": self._strategy.get_directive() if self._strategy else {},
            "memory": self._memory.get_stats() if self._memory else {},
            "luanti_connected": self._luanti.state.value if self._luanti else "disconnected",
        }


async def main():
    """主入口"""
    import argparse

    parser = argparse.ArgumentParser(description="Angela Game Agent for Luanti")
    parser.add_argument("--config", type=str, help="Config file path")
    parser.add_argument("--duration", type=int, default=0, help="Max ticks (0=infinite)")
    parser.add_argument("--host", type=str, default="localhost", help="Luanti host")
    parser.add_argument("--port", type=int, default=30000, help="Luanti port")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM")
    args = parser.parse_args()

    # 設置日誌
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    config = GameAgentConfig(
        luanti_host=args.host,
        luanti_port=args.port,
        max_ticks=args.duration,
        llm_enabled=not args.no_llm,
    )

    agent = GameAgent(config)

    # 信號處理
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(agent.shutdown()))

    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
