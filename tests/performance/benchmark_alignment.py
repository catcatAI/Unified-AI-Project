"""Benchmarks for alignment and knowledge system components."""
import pytest

from tests.conftest import benchmark


@pytest.mark.benchmark
def test_emotion_system_speed():
    """Benchmark EmotionSystem operations."""
    try:
        from ai.alignment.emotion_system import EmotionSystem
    except ImportError as e:
        pytest.skip(f"ImportError: {e}")

    def _run():
        system = EmotionSystem()
        for i in range(50):
            system.analyze_emotional_context({
                "text": f"This is test input number {i} with some emotional content",
                "stress_level": (i % 10) / 10.0,
            })
        summary = system.get_emotion_summary()
        assert "dominant_emotion" in summary

    stats = benchmark(_run, iterations=5)
    print(f"  EmotionSystem 50 context analyses: avg={stats['avg']:.4f}s")
    assert stats["avg"] > 0


@pytest.mark.benchmark
def test_alignment_manager_speed():
    """Benchmark AlignmentManager checks (skip if module is stub-only)."""
    try:
        from ai.alignment.alignment_manager import AlignmentManager
        manager = AlignmentManager()
    except (ImportError, AttributeError, TypeError) as e:
        pytest.skip(f"AlignmentManager not available: {e}")

    def _run():
        _ = manager.check_alignment({"input": "test"})

    stats = benchmark(_run, iterations=10)
    print(f"  AlignmentManager: avg={stats['avg']:.4f}s")
    assert stats["avg"] > 0


@pytest.mark.benchmark
def test_knowledge_graph_speed():
    """Benchmark KnowledgeGraphAgent operations."""
    try:
        from ai.agents.specialized.knowledge_graph_agent import KnowledgeGraphAgent
    except ImportError as e:
        pytest.skip(f"ImportError: {e}")

    def _run():
        agent = KnowledgeGraphAgent()
        for i in range(100):
            agent.add_entity(f"entity_{i}", {"type": "test", "value": i, "tags": ["a", "b"]})
            agent.query_graph(f"entity_{i // 2}")
        for i in range(50):
            agent.find_relations(f"entity_{i}", f"entity_{i + 1}")

    stats = benchmark(_run, iterations=5)
    print(f"  KnowledgeGraphAgent: avg={stats['avg']:.4f}s")
    assert stats["avg"] > 0
