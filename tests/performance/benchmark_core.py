"""Benchmarks for core AI system components."""
import asyncio
import pytest

from tests.conftest import benchmark, PerformanceTimer


@pytest.mark.benchmark
def test_importance_scorer_speed():
    """Benchmark ImportanceScorer.calculate() with 100 documents."""
    try:
        from ai.memory.importance_scorer import ImportanceScorer
    except ImportError as e:
        pytest.skip(f"ImportError: {e}")

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
    print(f"  ImportanceScorer 100 docs: avg={stats['avg']:.4f}s")
    assert stats["avg"] > 0


@pytest.mark.benchmark
def test_importance_scorer_accuracy():
    """Verify longer docs with keyword matches get higher scores."""
    try:
        from ai.memory.importance_scorer import ImportanceScorer
    except ImportError as e:
        pytest.skip(f"ImportError: {e}")

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
def test_parallel_task_execution():
    """Benchmark PerformanceOptimizer operations."""
    try:
        from ai.ops.performance_optimizer import PerformanceOptimizer
    except ImportError as e:
        pytest.skip(f"ImportError: {e}")

    def _run():
        optimizer = PerformanceOptimizer(config={"min_history_for_analysis": 3, "latency_threshold": 50})
        for i in range(200):
            optimizer.ingest_metrics(
                f"component_{i % 10}",
                {"latency_ms": 20 + (i % 5) * 30, "throughput_qps": 100 + i},
            )
        bottlenecks = 0
        for i in range(10):
            result = optimizer.analyze_bottlenecks(f"component_{i}")
            if result is not None:
                bottlenecks += 1
        return bottlenecks

    stats = benchmark(_run, iterations=5)
    print(f"  PerformanceOptimizer: avg={stats['avg']:.4f}s, median={stats['median']:.4f}s")
    assert stats["avg"] > 0


@pytest.mark.benchmark
def test_system_monitor_metrics():
    """Benchmark SystemMonitor.collect_metrics()."""
    try:
        from monitoring.system_monitor import SystemMonitor
    except ImportError as e:
        pytest.skip(f"ImportError: {e}")

    def _run():
        monitor = SystemMonitor()
        for _ in range(10):
            monitor.collect_metrics()

    stats = benchmark(_run, iterations=5)
    print(f"  SystemMonitor collect 10x: avg={stats['avg']:.4f}s")
    assert stats["avg"] > 0


@pytest.mark.benchmark
def test_services_initialize_speed():
    """Benchmark core_services.initialize_services()."""
    try:
        from core_services import initialize_services
    except ImportError as e:
        pytest.skip(f"ImportError: {e}")

    async def _run():
        await initialize_services(config={"test": True}, use_mock_ham=True)

    with PerformanceTimer("services_init"):
        asyncio.run(_run())
