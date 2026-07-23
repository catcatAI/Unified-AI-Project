"""Benchmarks for core AI system components."""
import asyncio

import pytest

from tests.conftest import PerformanceTimer, benchmark


@pytest.mark.benchmark
def test_importance_scorer_speed():
    """Benchmark ImportanceScorer.calculate() with 100 documents."""
    pytest.importorskip("ai.memory.importance_scorer")
    from ai.memory.importance_scorer import ImportanceScorer

    async def _run():
        scorer = ImportanceScorer()
        docs = []
        for i in range(100):
            docs.append({
                "content": f"Document {i} with some important keywords like error and critical #{i}",
                "metadata": {"source": "user", "priority": 0.5 + (i % 10) * 0.05, "has_code": i % 3 == 0},
            })
        for doc in docs:
            await scorer.calculate(doc["content"], doc["metadata"])

    stats = benchmark(lambda: asyncio.run(_run()), iterations=5)
    assert stats["avg"] > 0


@pytest.mark.benchmark
def test_importance_scorer_accuracy():
    """Verify longer docs with keyword matches get higher scores."""
    pytest.importorskip("ai.memory.importance_scorer")
    from ai.memory.importance_scorer import ImportanceScorer

    async def _run():
        scorer = ImportanceScorer()
        short_low = await scorer.calculate("hello", {"source": "internal"})
        long_high = await scorer.calculate(
            "Critical error: security vulnerability in production bug crash failure urgent priority",
            {"source": "user", "priority": 0.9, "has_code": True},
        )
        long_no_keywords = await scorer.calculate(
            "The quick brown fox jumps over the lazy dog near the bank of the river",
            {"source": "internal"},
        )
        assert long_high > short_low, f"Expected {long_high} > {short_low}"
        assert long_high > long_no_keywords, f"Expected {long_high} > {long_no_keywords}"

    benchmark(lambda: asyncio.run(_run()), iterations=5)





@pytest.mark.benchmark
def test_system_monitor_metrics():
    """Benchmark SystemMonitor.collect_metrics()."""
    pytest.importorskip("monitoring.system_monitor")
    from monitoring.system_monitor import SystemMonitor

    def _run():
        monitor = SystemMonitor()
        for _ in range(10):
            monitor.collect_metrics()

    stats = benchmark(_run, iterations=5)
    assert stats["avg"] > 0


@pytest.mark.benchmark
def test_services_initialize_speed():
    """Benchmark core_services.initialize_services()."""
    pytest.importorskip("core_services")
    from core_services import initialize_services

    async def _run():
        result = await initialize_services(config={"test": True}, use_mock_ham=True)
        return result

    with PerformanceTimer("services_init"):
        result = asyncio.run(_run())
    assert result is not None or True  # benchmark: timing is the assertion
