"""
Integration Tests for Game Agent (L0-L4)

Tests the complete pipeline:
- Foveated Sampler
- Game Policy (L0)
- Skill Selector (L1)
- Task Executor (L2)
- Game Planner (L3)
- Game Strategy (L4)
- Memory Bridge
- LLM Interface (with fallback)
"""

import pytest
import asyncio
import time
import numpy as np
from unittest.mock import Mock, AsyncMock, patch

from ai.multimodal.game_structs import (
    SkillID,
    SkillSpec,
    SkillParams,
    SkillContext,
    SkillResult,
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
from ai.multimodal.foveated_sampler import FoveatedSampler, SamplingConfig, SamplingStrategy
from ai.multimodal.game_policy import GamePolicy, PolicyConfig, PolicyOutput
from ai.multimodal.skill_selector import SkillSelector, SelectorConfig
from ai.multimodal.game_task_executor import GameTaskExecutor, ExecutorConfig, SubgoalStatus
from ai.multimodal.game_planner import (
    GamePlanner,
    PlannerConfig,
    PlanningContext,
    GoalManager,
    GoalType,
)
from ai.multimodal.game_memory_bridge import (
    GameMemoryBridge,
    MockHAMManager,
    MemoryType,
    GameExperience,
)
from ai.multimodal.game_strategy import GameStrategy, StrategyConfig, StrategyWeights
from ai.multimodal.llm_game_interface import (
    LLMGameInterface,
    LLMConfig,
    RuleBasedFallback,
    PlanProposal,
    AnomalyContext,
    RecoveryStrategy,
    StrategyContext,
    StrategyAdjustment,
)
from ai.multimodal.game_agent import GameAgent, GameAgentConfig


class TestGameStructs:
    """測試基礎資料結構"""

    def test_skill_specs_complete(self):
        """所有技能都有規格"""
        for skill_id in SkillID:
            assert skill_id in GAME_SKILLS
            spec = GAME_SKILLS[skill_id]
            assert isinstance(spec, SkillSpec)
            assert spec.continuous_dim >= 0
            assert isinstance(spec.preconditions, list)

    def test_check_preconditions(self):
        """測試前置條件檢查"""
        state = GameState(
            proprioception=Proprioception(
                inventory={"wood": 10, "cobblestone": 5, "stick": 3},
                health=20,
                max_health=20,
                hunger=15,
                max_hunger=20,
            )
        )

        # 空手也可挖掘（Minetest Game 真值：土/沙/木可手挖）
        ok, failed = check_preconditions(SkillID.DIG, state)
        assert ok

        # EAT 無食物 -> 不可執行（仍被前置擋下）
        ok, failed = check_preconditions(SkillID.EAT, state)
        assert not ok
        assert "無食物" in failed

    def test_get_available_skills(self):
        """測試可用技能列表"""
        state = GameState(
            proprioception=Proprioception(
                inventory={"wood": 10, "pickaxe": 1},
                health=20,
                max_health=20,
                hunger=15,
                max_hunger=20,
            )
        )
        available = get_available_skills(state)
        assert SkillID.MOVE in available
        assert SkillID.DIG in available
        assert SkillID.CRAFT in available


class TestFoveatedSampler:
    """測試 Foveated Sampler"""

    @pytest.fixture
    def sampler(self):
        config = SamplingConfig(
            budget_pixels=10000, output_size=(32, 32), strategy=SamplingStrategy.LOG_POLAR
        )
        return FoveatedSampler(config)

    def test_uniform_sampling(self, sampler):
        """均勻採樣基準測試"""
        frame = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
        sampler.config.strategy = SamplingStrategy.UNIFORM
        result = sampler.sample(frame, (160, 120))

        assert result.sampled_frame.shape == (32, 32, 3)
        assert result.inverse_map.shape == (32, 32, 2)
        assert result.density_map.shape == (32, 32)

    def test_log_polar_sampling(self, sampler):
        """Log-polar 採樣"""
        frame = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
        result = sampler.sample(frame, (160, 120))

        assert result.sampled_frame.shape == (32, 32, 3)
        assert result.strategy == SamplingStrategy.LOG_POLAR
        assert result.focus_xy == (160, 120)

    def test_deformable_sampling(self, sampler):
        """Deformable mesh 採樣"""
        frame = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
        sampler.config.strategy = SamplingStrategy.DEFORMABLE
        result = sampler.sample(frame, (160, 120))

        assert result.sampled_frame.shape == (32, 32, 3)
        assert result.strategy == SamplingStrategy.DEFORMABLE

    def test_map_to_original(self, sampler):
        """座標逆映射"""
        frame = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
        result = sampler.sample(frame, (160, 120))

        # 中心點應映射回焦點附近
        orig_x, orig_y = sampler.map_to_original((16, 16), result.inverse_map)
        assert abs(orig_x - 160) < 50
        assert abs(orig_y - 120) < 50


class TestGamePolicy:
    """測試 L0 Policy"""

    @pytest.fixture
    def policy(self):
        config = PolicyConfig(
            latent_dim=128, continuous_dim=16, discrete_dim=8, hidden_dim=64, use_diffusion=False
        )
        return GamePolicy(config)

    def test_forward(self, policy):
        """前向傳播"""
        visual_latent = np.random.randn(128).astype(np.float32)
        proprioception = np.random.randn(32).astype(np.float32)

        output = policy.forward(visual_latent, proprioception)

        assert isinstance(output, PolicyOutput)
        assert output.continuous.shape == (16,)
        assert output.discrete_logits.shape == (8,)
        assert output.grounding_heatmap.shape == (32, 32)
        assert output.confidence >= 0.0 and output.confidence <= 1.0

    def test_get_action_dict(self, policy):
        """動作字典轉換"""
        output = PolicyOutput(
            continuous=np.array([0.5, 0.0, 0.1] + [0] * 13, dtype=np.float32),
            discrete_logits=np.array(
                [2.0, -1.0, 0.5, -2.0, 0.0, -1.0, -1.0, -1.0], dtype=np.float32
            ),
            grounding_heatmap=np.zeros((32, 32)),
            mode=type("Mode", (), {"value": "exploration"})(),
            confidence=0.8,
            latent=np.zeros(128),
        )

        actions = policy.get_action_dict(output)

        assert "move" in actions
        assert actions["move"]["forward"] == 0.5
        assert abs(actions["move"]["yaw"] - 0.1) < 1e-6
        assert "dig" in actions  # attack logit > 0

    def test_mode_setting(self, policy):
        """策略模式設定"""
        from ai.multimodal.game_policy import PolicyMode

        policy.set_mode(PolicyMode.COMBAT)
        assert policy._mode == PolicyMode.COMBAT


class TestSkillSelector:
    """測試 L1 Skill Selector"""

    @pytest.fixture
    def selector(self):
        config = SelectorConfig(temperature=1.0)
        return SkillSelector(config)

    @pytest.fixture
    def state(self):
        return GameState(
            proprioception=Proprioception(
                inventory={"wood": 10, "cobblestone": 5, "stick": 3, "pickaxe": 1},
                health=20,
                max_health=20,
                hunger=15,
                max_hunger=20,
                position=(100, 64, 100),
            )
        )

    def test_select_returns_skill_params(self, selector, state):
        """選擇返回技能參數"""
        latent = np.random.randn(128).astype(np.float32)

        params = selector.select(latent, state)

        assert isinstance(params, SkillParams)
        assert params.skill_id in SkillID
        assert params.continuous_bias.shape[0] == GAME_SKILLS[params.skill_id].continuous_dim

    def test_get_skill_triggers(self, selector, state):
        """技能觸發建議"""
        latent = np.random.randn(128).astype(np.float32)

        triggers = selector.get_skill_triggers(latent, state)

        assert len(triggers) <= 5
        for t in triggers:
            assert hasattr(t, "skill_id")
            assert hasattr(t, "confidence")
            assert hasattr(t, "urgency")

    def test_precondition_filtering(self, selector, state):
        """前置條件過濾"""
        # 沒有食物時不應選 EAT（DIG 已改為空手可挖，不再以此為例）
        state.proprioception.inventory = {"wood": 10}
        latent = np.random.randn(128).astype(np.float32)

        available = selector.get_skill_triggers(latent, state)
        eat_triggers = [t for t in available if t.skill_id == SkillID.EAT]
        # EAT 應被過濾或低優先級
        if eat_triggers:
            assert eat_triggers[0].confidence < 0.5


class TestGameTaskExecutor:
    """測試 L2 Task Executor"""

    @pytest.fixture
    def executor(self):
        config = ExecutorConfig(stuck_threshold_ticks=100)
        return GameTaskExecutor(config)

    @pytest.fixture
    def state(self):
        return GameState(
            proprioception=Proprioception(
                inventory={"cobblestone": 10, "stick": 5},
                health=20,
                max_health=20,
                hunger=15,
                max_hunger=20,
            )
        )

    def test_load_subgoals(self, executor):
        """載入子目標"""
        subgoals = [
            Subgoal(
                subgoal_id="test_1",
                skill_id=SkillID.DIG,
                params={},
                preconditions=[],
                success_criteria="inventory_changed:cobblestone",
                timeout_ticks=100,
            ),
            Subgoal(
                subgoal_id="test_2",
                skill_id=SkillID.CRAFT,
                params={"recipe_id": "stone_pickaxe"},
                preconditions=["completed:test_1"],
                success_criteria="inventory_changed:stone_pickaxe",
                timeout_ticks=100,
            ),
        ]
        executor.load_subgoals(subgoals, "test_task")

        assert len(executor._queue) == 2
        assert executor._task_progress.task_id == "test_task"

    def test_tick_drives_execution(self, executor, state):
        """Tick 驅動執行"""
        # 給予工具讓前置條件通過
        state.proprioception.inventory["pickaxe"] = 1

        subgoals = [
            Subgoal(
                subgoal_id="dig_wood",
                skill_id=SkillID.DIG,
                params={"target_node": "tree"},
                preconditions=[],
                success_criteria="inventory_changed:wood",
                timeout_ticks=200,
            )
        ]
        executor.load_subgoals(subgoals, "test")

        latent = np.random.randn(128).astype(np.float32)
        ctx = executor.tick(None, state, latent)

        assert ctx is not None
        assert ctx.active_skill == SkillID.DIG
        assert executor._current is not None

    def test_skill_result_processing(self, executor, state):
        """技能結果處理"""
        subgoals = [
            Subgoal(
                subgoal_id="dig_test",
                skill_id=SkillID.DIG,
                params={},
                preconditions=[],
                success_criteria="inventory_changed:cobblestone",
                timeout_ticks=200,
            )
        ]
        executor.load_subgoals(subgoals, "test")

        latent = np.random.randn(128).astype(np.float32)
        ctx = executor.tick(None, state, latent)

        # 模擬技能成功
        result = SkillResult(
            skill_id=SkillID.DIG,
            success=True,
            side_effects=["collected:cobblestone:3"],
            duration_ticks=10,
        )

        ctx2 = executor.tick(result, state, latent)

        # 子目標應完成
        assert executor._task_progress.completed == ["dig_test"]
        assert executor._current is None

    def test_fallback_on_failure(self, executor, state):
        """失敗時 fallback"""
        subgoals = [
            Subgoal(
                subgoal_id="fail_test",
                skill_id=SkillID.DIG,
                params={},
                preconditions=[],
                success_criteria="inventory_changed:diamond",  # 不可能
                timeout_ticks=10,
                fallback="move",  # 有 fallback
            )
        ]
        executor.load_subgoals(subgoals, "test")

        latent = np.random.randn(128).astype(np.float32)

        # 執行第一 tick 觸發 fallback
        ctx1 = executor.tick(None, state, latent)
        assert ctx1 is not None  # fallback ctx

        # 執行更多 tick（timeout_ticks=10 需第 12 tick 才觸發超時判定）
        for _ in range(14):
            executor.tick(None, state, latent)

        # 應觸發 fallback (前置阻塞走 unblock，超時失敗走 fallback_N)
        def _is_fallback(sg_id: str) -> bool:
            return "unblock" in sg_id or "fallback" in sg_id

        fallback_triggered = (
            any(_is_fallback(sg.subgoal_id) for sg in executor._queue)
            or any(_is_fallback(sg.subgoal_id) for sg in executor._completed)
            or (executor._current and _is_fallback(executor._current.subgoal.subgoal_id))
        )
        assert (
            fallback_triggered
        ), f"Fallback should have been triggered. Queue: {[sg.subgoal_id for sg in executor._queue]}, Current: {executor._current.subgoal.subgoal_id if executor._current else None}"


class TestGamePlanner:
    """測試 L3 Planner"""

    @pytest.fixture
    def planner(self):
        config = PlannerConfig(use_llm_for_complex=False)
        return GamePlanner(config)

    @pytest.fixture
    def state(self):
        return GameState(
            proprioception=Proprioception(
                inventory={"wood": 10}, health=20, max_health=20, hunger=15, max_hunger=20
            )
        )

    @pytest.mark.asyncio
    async def test_rule_based_plan(self, planner, state):
        """規則基礎規劃"""
        ctx = PlanningContext(
            current_goal=GoalType.SURVIVAL,
            goal_params={},
            state=state,
            ham_memories=[],
            strategy=StrategyDirective(exploration_weight=0.5, risk_tolerance=0.5),
        )

        plan = await planner.propose_plan(ctx)

        assert isinstance(plan, PlanDAG)
        assert len(plan.nodes) > 0
        assert plan.root_goal == "survival"

    @pytest.mark.asyncio
    async def test_tool_progression_plan(self, planner, state):
        """工具進度規劃"""
        ctx = PlanningContext(
            current_goal=GoalType.TOOL,
            goal_params={},
            state=state,
            ham_memories=[],
            strategy=StrategyDirective(),
        )

        plan = await planner.propose_plan(ctx)

        # 應包含木鎬 -> 石鎬 進度
        skill_ids = [n.skill_id for n in plan.nodes.values()]
        assert SkillID.CRAFT in skill_ids
        assert SkillID.DIG in skill_ids

    @pytest.mark.asyncio
    async def test_plan_validation(self, planner, state):
        """計劃驗證"""
        ctx = PlanningContext(
            current_goal=GoalType.BUILD,
            goal_params={"blueprint": "large_house"},
            state=state,
            ham_memories=[],
            strategy=StrategyDirective(),
        )

        plan = await planner.propose_plan(ctx)

        # 驗證：無循環、技能存在、深度限制
        assert len(plan.nodes) <= planner.config.max_subgoals_per_plan
        for node in plan.nodes.values():
            assert node.skill_id in GAME_SKILLS


class TestGameMemoryBridge:
    """測試記憶橋接"""

    @pytest.fixture
    def memory(self):
        return GameMemoryBridge()

    @pytest.mark.asyncio
    async def test_store_and_recall_experience(self, memory):
        """存儲與檢索經驗"""
        exp = GameExperience(
            exp_id="test_1",
            memory_type=MemoryType.EPISODIC,
            timestamp=time.time(),
            position=(100, 64, 100),
            action="dig",
            context={"tool": "pickaxe"},
            outcome={"collected": {"cobblestone": 3}},
            reward=0.5,
            tags=["resource", "stone"],
        )

        await memory.store_experience(exp)

        results = await memory.recall_experience("stone", limit=5)
        assert len(results) > 0
        assert "cobblestone" in results[0]

    def test_recipe_queries(self, memory):
        """配方查詢"""
        # 預設配方
        recipe = memory.get_recipe("stone_pickaxe")
        assert recipe is not None
        assert recipe.ingredients["cobblestone"] == 3
        assert recipe.ingredients["stick"] == 2

        # 可製作配方
        craftable = memory.get_craftable_recipes({"cobblestone": 10, "stick": 5})
        assert len(craftable) > 0
        assert any(r.recipe_id == "stone_pickaxe" for r in craftable)

    def test_recipe_chain(self, memory):
        """製作鏈"""
        chain = memory.get_recipe_chain("iron_pickaxe")
        assert len(chain) > 1
        # 應包含鐵錠、木棍、熔爐等前置 (通過 get_all_recipe_dependencies)
        deps = memory.get_all_recipe_dependencies("iron_pickaxe")
        assert "furnace" in deps
        assert "iron_ingot" in deps
        assert "stick" in deps

    def test_spatial_memory(self, memory):
        """空間記憶"""
        memory.mark_base((100, 64, 100))
        memory._spatial_index["200_64_200"] = type(
            "Node",
            (),
            {
                "position": (200, 64, 200),
                "node_type": "resource",
                "resources": {"diamond": 5},
                "danger_level": 0.0,
            },
        )()

        nearest = memory.find_nearest_resource((100, 64, 100), "diamond", max_dist=200)
        assert nearest is not None
        assert nearest.resources.get("diamond", 0) > 0

    def test_danger_marking(self, memory):
        """危險標記"""
        memory.mark_danger((150, 64, 150), 0.8)

        # 檢查是否標記
        safe = memory.find_safe_location((100, 64, 100), radius=100)
        # 危險區不應被選為安全點
        if safe:
            assert safe.position != (150, 64, 150)


class TestGameStrategy:
    """測試 L4 Strategy"""

    @pytest.fixture
    def strategy(self):
        config = StrategyConfig(update_interval_sec=0.1)
        return GameStrategy(config)

    def test_get_directive(self, strategy):
        """獲取策略指令"""
        directive = strategy.get_directive()

        assert "exploration_weight" in directive
        assert "risk_tolerance" in directive
        assert "priority_goals" in directive
        assert "forbidden_actions" in directive
        assert 0 <= directive["exploration_weight"] <= 1
        assert 0 <= directive["risk_tolerance"] <= 1

    def test_weight_adjustment_on_death(self):
        """死亡時調整權重"""
        config = StrategyConfig(update_interval_sec=0.0)  # 無間隔
        strategy = GameStrategy(config)

        # 記錄多次死亡
        for _ in range(5):
            strategy.record_event("death", {})

        # 更新
        strategy.update()

        # 風險容忍應降低
        assert strategy.weights.risk_tolerance < 0.5
        assert strategy.weights.survival_priority > 0.7

    def test_weight_adjustment_on_low_resources(self):
        """資源低時增加探索"""
        config = StrategyConfig(update_interval_sec=0.0)
        strategy = GameStrategy(config)
        strategy.stats.duration_min = 10
        strategy.stats.resource_collected = {}
        strategy.stats.death_count = 0
        strategy.stats.anomaly_count = 0
        strategy.stats.stuck_count = 0
        strategy.stats.goals_completed = 0
        strategy.stats.goals_failed = 0
        # 重置權重到預設
        strategy.weights = StrategyWeights()

        strategy.update()

        # 探索權重應增加 (預設 0.5 + bonus)
        assert strategy.weights.exploration_weight >= 0.5

    def test_forbidden_actions(self, strategy):
        """禁止動作計算"""
        strategy.weights.risk_tolerance = 0.2
        strategy.weights.survival_priority = 0.9

        directive = strategy.get_directive()

        assert "deep_mining" in directive["forbidden_actions"]
        assert "unnecessary_combat" in directive["forbidden_actions"]


class TestLLMGameInterface:
    """測試 LLM 介面"""

    @pytest.fixture
    def llm_config(self):
        return LLMConfig(enabled=False)  # 使用 fallback

    @pytest.fixture
    def llm(self, llm_config):
        return LLMGameInterface(llm_config)

    def test_fallback_plan(self, llm):
        """Fallback 規劃"""
        from ai.multimodal.llm_game_interface import PlanContext

        ctx = PlanContext(
            current_goal="survival", goal_params={}, state=None, ham_memories=[], strategy={}
        )

        # 直接測試 fallback
        plan = RuleBasedFallback.propose_plan(ctx)

        assert isinstance(plan, PlanProposal)
        assert len(plan.subgoals) > 0
        assert plan.subgoals[0].skill == "eat"

    def test_fallback_diagnose(self, llm):
        """Fallback 異常診斷"""
        from ai.multimodal.llm_game_interface import AnomalyContext

        ctx = AnomalyContext(
            stuck_reason="missing_resource",
            current_subgoal="craft_iron_pickaxe",
            recent_actions=["dig", "craft"],
            inventory={"cobblestone": 5},
            position={"x": 100, "y": 64, "z": 100},
            health=15.0,
            hunger=10.0,
        )

        strategy = RuleBasedFallback.diagnose_anomaly(ctx)

        assert isinstance(strategy, RecoveryStrategy)
        assert strategy.immediate_action.type == "fallback_subgoal"
        assert strategy.fallback_subgoal is not None

    def test_fallback_strategy(self, llm):
        """Fallback 策略調整"""
        from ai.multimodal.llm_game_interface import StrategyContext

        ctx = StrategyContext(
            session_duration_min=15.0,
            goals_completed=["survival", "wood_tools"],
            goals_failed=[],
            death_count=5,
            resource_collection_rate={"cobblestone": 0.5},
            anomaly_count=12,
            current_strategy={"exploration_weight": 0.5, "risk_tolerance": 0.5},
        )

        adj = RuleBasedFallback.evaluate_strategy(ctx)

        assert isinstance(adj, StrategyAdjustment)
        assert adj.risk_tolerance_delta < 0  # 死亡多 -> 降低風險


class TestGoalManager:
    """測試目標管理"""

    @pytest.fixture
    def planner(self):
        config = PlannerConfig(use_llm_for_complex=False)
        return GamePlanner(config)

    @pytest.fixture
    def goal_manager(self, planner):
        return GoalManager(planner)

    def test_add_and_get_goal(self, goal_manager):
        """添加與獲取目標"""
        goal_manager.add_goal(GoalType.SURVIVAL, priority=1.0)
        goal_manager.add_goal(GoalType.TOOL, priority=0.8)

        current = goal_manager.get_highest_priority()
        assert current is not None
        assert current[0] == GoalType.SURVIVAL

    def test_complete_goal(self, goal_manager):
        """完成目標"""
        goal_manager.add_goal(GoalType.SURVIVAL, priority=1.0)
        goal_manager.complete_goal(GoalType.SURVIVAL)

        current = goal_manager.get_highest_priority()
        assert current is None or current[0] != GoalType.SURVIVAL


class TestGameAgentIntegration:
    """端到端整合測試 (Mock Luanti)"""

    @pytest.fixture
    def agent_config(self):
        return GameAgentConfig(
            luanti_host="localhost",
            luanti_port=30000,
            max_ticks=10,
            tick_interval=0.01,
            llm_enabled=False,
        )

    @pytest.fixture
    def agent(self, agent_config):
        return GameAgent(agent_config)

    @pytest.mark.asyncio
    async def test_initialization(self, agent):
        """初始化測試 (不連線 Luanti)"""
        # Mock Luanti 連線
        with patch.object(agent._luanti, "connect", new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = True
            with patch.object(agent._luanti, "state", Mock(value="ready")):
                result = await agent.initialize()
                assert result is True

    @pytest.mark.asyncio
    async def test_single_tick(self, agent):
        """單 tick 執行"""
        with patch.object(agent._luanti, "connect", new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = True
            with patch.object(agent._luanti, "state", Mock(value="ready")):
                await agent.initialize()

                # Mock 視覺幀
                agent._state.visual = VisualObservation(
                    frame_id=1,
                    timestamp=time.time(),
                    features=np.random.randn(128).astype(np.float32),
                    fovea_xy=(320, 240),
                    inverse_map=np.zeros((64, 64, 2)),
                    raw_frame_shape=(480, 640),
                )
                agent._state.proprioception = Proprioception(
                    inventory={"wood": 5}, health=20, max_health=20, hunger=15, max_hunger=20
                )

                # Mock Luanti 動作發送
                agent._luanti.move = AsyncMock()
                agent._luanti.look = AsyncMock()
                agent._luanti.dig = AsyncMock()

                # 執行一個 tick
                agent._executor.tick(None, agent._state, np.random.randn(128).astype(np.float32))
                policy_out = agent._policy.forward(
                    agent._state.visual.features,
                    agent._proprioception_to_vector(agent._state.proprioception),
                )
                actions = agent._compose_actions(
                    policy_out, SkillContext(active_skill=SkillID.MOVE, params={}, priority=1.0)
                )

                # 發送動作
                await agent._send_actions(actions)

                # 驗證動作被發送
                assert (
                    agent._luanti.move.called
                    or agent._luanti.look.called
                    or agent._luanti.dig.called
                )


# ==================== Fixtures ====================


@pytest.fixture
def event_loop():
    """事件循環"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ==================== Main ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
