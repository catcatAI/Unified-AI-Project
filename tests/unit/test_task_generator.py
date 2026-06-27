"""Tests for ai.memory.task_generator"""
import pytest


class TestTaskGenerator:
    def test_import(self):
        try:
            from ai.memory.task_generator import TaskGenerator
            assert TaskGenerator is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")

    def test_instantiation(self):
        try:
            from ai.memory.task_generator import TaskGenerator
            instance = TaskGenerator()
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")

    def test_analyze_patterns_empty(self):
        from ai.memory.task_generator import TaskGenerator
        tg = TaskGenerator()
        result = tg.analyze_patterns([])
        assert result["total_analyzed"] == 0
        assert result["topics"] == {}

    def test_analyze_patterns_tracks_topics(self):
        from ai.memory.task_generator import TaskGenerator
        tg = TaskGenerator()
        interactions = [
            {"topic": "math", "content": "2+2"},
            {"topic": "science", "content": "gravity"},
            {"topic": "math", "content": "3*4"},
        ]
        result = tg.analyze_patterns(interactions)
        assert result["total_analyzed"] == 3
        assert result["topics"]["math"] == 2
        assert result["topics"]["science"] == 1
        assert result["dominant_topic"] == "math"

    def test_analyze_patterns_tracks_transitions(self):
        from ai.memory.task_generator import TaskGenerator
        tg = TaskGenerator()
        interactions = [
            {"topic": "math", "content": "2+2"},
            {"topic": "science", "content": "gravity"},
            {"topic": "science", "content": "biology"},
        ]
        tg.analyze_patterns(interactions)
        transitions = tg._topic_chain
        assert "math" in transitions
        assert transitions["math"]["science"] == 1

    def test_generate_tasks_returns_list(self):
        from ai.memory.task_generator import TaskGenerator
        tg = TaskGenerator()
        tasks = tg.generate_tasks({"user": "test"})
        assert isinstance(tasks, list)
        assert len(tasks) >= 1
        assert any(t["task_type"] == "precompute_response" for t in tasks)

    def test_generate_tasks_with_history(self):
        from ai.memory.task_generator import TaskGenerator
        tg = TaskGenerator()
        tg.analyze_patterns([
            {"topic": "math", "content": "2+2"},
            {"topic": "math", "content": "3+3"},
            {"topic": "science", "content": "physics"},
        ])
        tasks = tg.generate_tasks()
        types = [t["task_type"] for t in tasks]
        assert "prefetch_knowledge" in types

    def test_predict_next_query_no_history(self):
        from ai.memory.task_generator import TaskGenerator
        tg = TaskGenerator()
        assert tg.predict_next_query("user1") is None

    def test_predict_next_query_with_history(self):
        from ai.memory.task_generator import TaskGenerator
        tg = TaskGenerator()
        tg.analyze_patterns([
            {"topic": "math", "content": "2+2"},
            {"topic": "science", "content": "gravity"},
            {"topic": "math", "content": "3*4"},
            {"topic": "science", "content": "biology"},
        ])
        prediction = tg.predict_next_query("user1")
        # Last topic was "science", historically followed by "math"
        assert prediction == "math"
