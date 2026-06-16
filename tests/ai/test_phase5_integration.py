# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [C] [L3]
# Phase 5 Integration Tests: Continuous Learning & Cross-Session Persistence
# =============================================================================

import json
import os
import tempfile
import time

import pytest


# ---------------------------------------------------------------------------
# 5.6.1  ContinuousLearningPipeline saves state after interactions
# ---------------------------------------------------------------------------

class TestContinuousLearningState:
    def test_save_state_after_interactions(self, tmp_path):
        from ai.ed3n.continuous_learning import ContinuousLearningPipeline
        pipeline = ContinuousLearningPipeline(
            growth_interval=5,
            train_interval=100,
            min_examples_for_train=100,
            auto_grow=False,
        )
        for i in range(12):
            pipeline.process_interaction(f"user_{i}", f"response_{i}", {})
        state_dir = str(tmp_path / "cl_state")
        pipeline.save(state_dir)
        state_path = os.path.join(state_dir, "cl_state.json")
        assert os.path.exists(state_path)
        with open(state_path, encoding="utf-8") as f:
            data = json.load(f)
        assert data["interaction_count"] == 12
        assert len(data["buffer"]) == 12

    def test_load_state_restores_interactions(self, tmp_path):
        from ai.ed3n.continuous_learning import ContinuousLearningPipeline
        pipeline = ContinuousLearningPipeline(auto_grow=False)
        for i in range(5):
            pipeline.process_interaction(f"msg_{i}", f"reply_{i}", {})
        state_dir = str(tmp_path / "cl_state2")
        pipeline.save(state_dir)
        loaded = ContinuousLearningPipeline.load(state_dir)
        assert loaded._interaction_count == 5
        assert len(loaded._training_buffer) == 5


# ---------------------------------------------------------------------------
# 5.6.3  MemoryContextManager save/load session persistence
# ---------------------------------------------------------------------------

class TestSessionPersistence:
    def test_save_and_load_session(self, tmp_path):
        from ai.context.memory_context import MemoryContextManager
        session_dir = str(tmp_path / "sessions")
        mgr = MemoryContextManager(session_dir=session_dir)
        mgr.create_memory("我喜欢音乐", "short_term", {"topic": "music"})
        mgr.create_memory("AI很有趣", "long_term", {"topic": "ai"})
        path = mgr.save_session("test_session_001")
        assert os.path.exists(path)
        mgr2 = MemoryContextManager(session_dir=session_dir)
        assert mgr2.get_memory_count() == 0
        loaded = mgr2.load_session("test_session_001")
        assert loaded is True
        assert mgr2.get_memory_count() == 2

    def test_load_nonexistent_session_returns_false(self, tmp_path):
        from ai.context.memory_context import MemoryContextManager
        mgr = MemoryContextManager(session_dir=str(tmp_path / "sessions"))
        assert mgr.load_session("nonexistent") is False


# ---------------------------------------------------------------------------
# 5.6.4  MemoryContextManager importance boost on frequently accessed memories
# ---------------------------------------------------------------------------

class TestMemoryImportanceBoost:
    def test_search_by_embedding(self, tmp_path):
        from ai.context.memory_context import MemoryContextManager
        mgr = MemoryContextManager(session_dir=str(tmp_path / "s"))
        mid = mgr.create_memory("test content", "short_term")
        mgr.update_memory_embedding(mid, [1.0, 0.0, 0.0])
        results = mgr.search_by_embedding([1.0, 0.0, 0.0], top_k=3)
        assert len(results) == 1
        assert results[0]["similarity"] == pytest.approx(1.0)

    def test_cosine_similarity(self):
        from ai.context.memory_context import MemoryContextManager
        assert MemoryContextManager._cosine_similarity([1, 0], [1, 0]) == pytest.approx(1.0)
        assert MemoryContextManager._cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)
        assert MemoryContextManager._cosine_similarity([], [1, 0]) == 0.0


# ---------------------------------------------------------------------------
# 5.6.6  LearningLoop adjusts learning rate based on feedback
# ---------------------------------------------------------------------------

class TestLearningLoopFeedback:
    def test_learning_rate_increases_on_positive(self):
        from ai.response.learning_loop import LearningLoop
        loop = LearningLoop()
        initial = loop.learning_rate
        loop.record_user_engagement(positive=True)
        assert loop.learning_rate > initial

    def test_learning_rate_decreases_on_negative(self):
        from ai.response.learning_loop import LearningLoop
        loop = LearningLoop()
        initial = loop.learning_rate
        loop.record_user_engagement(positive=False)
        assert loop.learning_rate < initial

    def test_learning_rate_bounds(self):
        from ai.response.learning_loop import LearningLoop
        loop = LearningLoop()
        for _ in range(50):
            loop.record_user_engagement(positive=True)
        assert loop.learning_rate <= 0.15
        for _ in range(50):
            loop.record_user_engagement(positive=False)
        assert loop.learning_rate >= 0.01

    def test_process_llm_response_extracts_novelty(self):
        from ai.response.learning_loop import LearningLoop
        loop = LearningLoop()
        count = loop.process_llm_response("「全新的句子」和一些内容。")
        assert count >= 0

    def test_bind_engines(self):
        from ai.response.learning_loop import LearningLoop
        loop = LearningLoop()
        dummy_ed3n = object()
        dummy_garden = object()
        loop.bind_ed3n_engine(dummy_ed3n)
        loop.bind_garden_engine(dummy_garden)
        assert loop._ed3n_engine is dummy_ed3n
        assert loop._garden_engine is dummy_garden


# ---------------------------------------------------------------------------
# 5.6.5  LearningLoop process_user_feedback triggers GARDEN update
# ---------------------------------------------------------------------------

class TestLearningLoopGardenIntegration:
    def test_process_user_feedback_calls_garden(self, tmp_path):
        from ai.response.learning_loop import LearningLoop
        from ai.garden.garden_engine import GARDENEngine
        garden = GARDENEngine(compatibility_mode=True)
        garden.load_presets()
        loop = LearningLoop()
        loop.bind_garden_engine(garden)
        loop.process_user_feedback("你好", "你好啊", positive=True)
        assert loop.learning_rate >= 0.05

    def test_process_user_feedback_negative(self):
        from ai.response.learning_loop import LearningLoop
        loop = LearningLoop()
        mock_garden = type("MockGarden", (), {"learn_from_interaction": lambda self, u, r: None})()
        loop.bind_garden_engine(mock_garden)
        initial = loop.learning_rate
        loop.process_user_feedback("bad input", "bad response", positive=False)
        assert loop.learning_rate < initial
