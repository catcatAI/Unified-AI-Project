"""L0 Policy 行為克隆訓練測試（R74）。

涵蓋：hold-out 學習門（可學習集過門／雜訊集擋下並完整還原權重）、
權重持久化（roundtrip、形狀漂移防護、損壞容錯）、agent 端資料收集閉環。
"""

import sys
from pathlib import Path

import numpy as np
import pytest

BACKEND_SRC = Path(__file__).resolve().parents[3] / "apps" / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from ai.multimodal.game_policy import GamePolicy, PolicyConfig, PolicyMode  # noqa: E402
from ai.multimodal.game_structs import (  # noqa: E402
    GameState,
    Proprioception,
    SkillID,
    Subgoal,
)
from ai.multimodal.game_task_executor import (  # noqa: E402
    ActiveSubgoal,
    ExecutorConfig,
    GameTaskExecutor,
    SubgoalStatus,
)

TRAINABLE_KEYS = tuple(GamePolicy(PolicyConfig())._TRAINABLE)


def _make_learnable_dataset(n: int = 400, seed: int = 0):
    """可學習合成任務：discrete = f(prop[0]>0)、continuous = tanh(vl[:16]*0.7)。"""
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        vl = rng.normal(size=128).astype(np.float32)
        pr = rng.normal(size=32).astype(np.float32)
        out.append(
            {
                "visual_latent": vl,
                "proprioception": pr,
                "continuous": np.tanh(vl[:16] * 0.7).astype(np.float32),
                "discrete": 1 if pr[0] > 0 else 0,
                "mode": PolicyMode.EXPLORATION,
            }
        )
    return out


def _make_noise_dataset(n: int = 400, seed: int = 1):
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        out.append(
            {
                "visual_latent": rng.normal(size=128).astype(np.float32),
                "proprioception": rng.normal(size=32).astype(np.float32),
                "continuous": rng.uniform(-1, 1, size=16).astype(np.float32),
                "discrete": int(rng.integers(0, 8)),
            }
        )
    return out


class TestBehaviorCloningTraining:
    def test_learnable_dataset_passes_gate(self):
        p = GamePolicy(PolicyConfig())
        result = p.train_behavior_cloning(_make_learnable_dataset(), epochs=15, lr=3e-3)
        assert result["learned"] is True
        assert result["improvement"]["acc"] > 0
        assert result["baseline"]["val_acc"] < result["after"]["val_acc"]

    def test_noise_dataset_blocked_and_weights_restored(self):
        p = GamePolicy(PolicyConfig())
        before = {k: p._params[k].copy() for k in TRAINABLE_KEYS}
        result = p.train_behavior_cloning(
            _make_noise_dataset(),
            epochs=8,
            lr=1e-3,
            min_mae_improvement=0.05,
            min_acc_improvement=0.1,
        )
        assert result["learned"] is False
        assert result["reason"] == "holdout gate not passed"
        # 門未過＝一切如舊：權重必須逐位還原，不得保留部分擬合結果
        for k in TRAINABLE_KEYS:
            assert np.array_equal(before[k], p._params[k]), f"weight {k} not restored"

    def test_dataset_too_small_rejected(self):
        p = GamePolicy(PolicyConfig())
        result = p.train_behavior_cloning(_make_learnable_dataset(5))
        assert result["learned"] is False
        assert result["reason"] == "dataset too small"

    def test_forward_still_works_after_training(self):
        p = GamePolicy(PolicyConfig())
        p.train_behavior_cloning(_make_learnable_dataset(), epochs=3, lr=1e-3)
        out = p.forward(np.zeros(128, dtype=np.float32), np.zeros(32, dtype=np.float32))
        assert out.continuous.shape == (PolicyConfig().continuous_dim,)
        assert out.discrete_logits.shape == (PolicyConfig().discrete_dim,)


class TestWeightPersistence:
    def test_save_load_roundtrip(self, tmp_path):
        p1 = GamePolicy(PolicyConfig())
        path = str(tmp_path / "w.json")
        # 讓 p1 與出廠值不同（跑一步訓練）
        p1.train_behavior_cloning(_make_learnable_dataset(), epochs=2, lr=1e-3)
        assert p1.save_weights(path) is True
        p2 = GamePolicy(PolicyConfig())
        assert p2.load_weights(path) is True
        for k in TRAINABLE_KEYS:
            assert np.allclose(p1._params[k], p2._params[k]), k

    def test_load_shape_drift_rejected(self, tmp_path):
        p1 = GamePolicy(PolicyConfig())
        path = str(tmp_path / "w.json")
        assert p1.save_weights(path) is True
        p2 = GamePolicy(PolicyConfig(hidden_dim=64))
        assert p2.load_weights(path) is False
        # 失敗後保持 Xavier 原狀（不被半套覆蓋）
        p3 = GamePolicy(PolicyConfig(hidden_dim=64))
        for k in TRAINABLE_KEYS:
            assert np.array_equal(p2._params[k], p3._params[k]), k

    def test_load_missing_file_returns_false(self, tmp_path):
        p = GamePolicy(PolicyConfig())
        assert p.load_weights(str(tmp_path / "nope.json")) is False

    def test_load_corrupt_json_returns_false(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{not valid json", encoding="utf-8")
        p = GamePolicy(PolicyConfig())
        assert p.load_weights(str(path)) is False


def _make_agent(policy_training_enabled: bool = True):
    from ai.autonomous.angela_agent import AngelaAutonomousAgent, AngelaConfig

    cfg = AngelaConfig()
    cfg.policy_training_enabled = policy_training_enabled
    agent = AngelaAutonomousAgent(cfg)
    agent.executor = GameTaskExecutor(ExecutorConfig())
    agent.current_state = GameState(
        tick=1,
        timestamp=0.0,
        proprioception=Proprioception(health=18.0, position=(10.0, 5.0, -3.0)),
    )
    return agent


def _push_completed(agent, subgoal_id="s1", skill=SkillID.DIG, params=None):
    sg = Subgoal(
        subgoal_id=subgoal_id,
        skill_id=skill,
        params=params or {"continuous_bias": [0.5, 0.0, 1.0]},
        preconditions=[],
        success_criteria="x",
        timeout_ticks=300,
    )
    agent.executor._completed.append(
        ActiveSubgoal(
            subgoal=sg,
            status=SubgoalStatus.COMPLETED,
            started_tick=0,
            last_progress_tick=1,
        )
    )


class TestAgentBCWiring:
    @pytest.mark.asyncio
    async def test_capture_on_completed_subgoal(self):
        agent = _make_agent()
        _push_completed(agent)
        await agent._execute_tasks()
        assert len(agent._bc_buffer) == 1
        sample = agent._bc_buffer[0]
        assert sample["discrete"] == list(SkillID).index(SkillID.DIG)
        assert sample["continuous"][0] == pytest.approx(0.5)
        assert sample["continuous"][2] == pytest.approx(1.0)
        # 本體感覺有正規化血量
        assert sample["proprioception"][0] == pytest.approx(0.9)

    @pytest.mark.asyncio
    async def test_same_subgoal_not_captured_twice(self):
        agent = _make_agent()
        _push_completed(agent)
        await agent._execute_tasks()
        await agent._execute_tasks()
        assert len(agent._bc_buffer) == 1

    @pytest.mark.asyncio
    async def test_failed_subgoal_not_captured(self):
        agent = _make_agent()
        _push_completed(agent, subgoal_id="f1")
        agent.executor._completed.clear()  # 只留失敗紀錄
        agent.executor._failed.append(
            ActiveSubgoal(
                subgoal=Subgoal(
                    subgoal_id="f1",
                    skill_id=SkillID.DIG,
                    params={},
                    preconditions=[],
                    success_criteria="x",
                    timeout_ticks=300,
                ),
                status=SubgoalStatus.FAILED,
                started_tick=0,
                last_progress_tick=1,
            )
        )
        await agent._execute_tasks()
        # 失敗動作不示範：buffer 必須是空的
        assert len(agent._bc_buffer) == 0

    @pytest.mark.asyncio
    async def test_periodic_training_respects_min_samples(self):
        agent = _make_agent()
        agent.config.policy_min_samples = 10
        agent._bc_buffer.append(
            {
                "visual_latent": np.zeros(128, dtype=np.float32),
                "proprioception": np.zeros(32, dtype=np.float32),
                "continuous": np.zeros(16, dtype=np.float32),
                "discrete": 0,
            }
        )
        await agent._train_policy_periodic()
        # 樣本不足：不訓練、不報錯、_policy_trained 維持 False
        assert agent._policy_trained is False

    def test_disabled_config_no_capture(self):
        agent = _make_agent(policy_training_enabled=False)
        _push_completed(agent)

        import asyncio

        asyncio.run(agent._execute_tasks())
        assert len(agent._bc_buffer) == 0
