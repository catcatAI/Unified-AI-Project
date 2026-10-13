"""Benchmarks for core AI system components."""

import pytest

from tests.conftest import PerformanceTimer, benchmark


@pytest.mark.benchmark
def test_importance_scorer_speed():
    """Benchmark ImportanceScorer.calculate() with 100 documents.

    calculate() 是同步 API（曾為 async；舊 benchmark 對其 await 會炸
    TypeError——改名 test_*.py 進入收集後即暴露）。
    """
    pytest.importorskip("ai.memory.importance_scorer")
    from ai.memory.importance_scorer import ImportanceScorer

    def _run():
        scorer = ImportanceScorer()
        docs = []
        for i in range(100):
            docs.append(
                {
                    "content": f"Document {i} with some important keywords like error and critical #{i}",
                    "metadata": {
                        "source": "user",
                        "priority": 0.5 + (i % 10) * 0.05,
                        "has_code": i % 3 == 0,
                    },
                }
            )
        for doc in docs:
            scorer.calculate(doc["content"], doc["metadata"])

    stats = benchmark(_run, iterations=5)
    assert stats["avg"] > 0


@pytest.mark.benchmark
def test_importance_scorer_accuracy():
    """Verify longer docs with keyword matches get higher scores."""
    pytest.importorskip("ai.memory.importance_scorer")
    from ai.memory.importance_scorer import ImportanceScorer

    scorer = ImportanceScorer()
    short_low = scorer.calculate("hello", {"source": "internal"})
    long_high = scorer.calculate(
        "Critical error: security vulnerability in production bug crash failure urgent priority",
        {"source": "user", "priority": 0.9, "has_code": True},
    )
    long_no_keywords = scorer.calculate(
        "The quick brown fox jumps over the lazy dog near the bank of the river",
        {"source": "internal"},
    )
    assert long_high > short_low, f"Expected {long_high} > {short_low}"
    assert long_high > long_no_keywords, f"Expected {long_high} > {long_no_keywords}"


@pytest.mark.benchmark
def test_system_monitor_metrics():
    """Benchmark SystemMonitor.collect_metrics()."""
    pytest.importorskip("monitoring.system_monitor")
    from monitoring.system_monitor import SystemMonitor

    def _run():
        monitor = SystemMonitor()
        # collect_metrics() 內 psutil.cpu_percent(interval=1) 每次阻塞 ~1s，
        # 取樣數控制在 2×2=4 次（~4s）——過往 10×5=50 次令全量套件多 50s。
        for _ in range(2):
            monitor.collect_metrics()

    stats = benchmark(_run, iterations=2)
    assert stats["avg"] > 0


@pytest.mark.benchmark
def test_services_initialize_speed():
    """Benchmark core_services.initialize_services().

    initialize_services() 是同步且回傳 None——side effect 是註冊
    logger/config 服務，以此為誠實斷言（計時由 PerformanceTimer 記錄）。
    """
    pytest.importorskip("core_services")
    from core_services import get_services, initialize_services, shutdown_services

    shutdown_services()
    with PerformanceTimer("services_init"):
        initialize_services(config={"test": True}, use_mock_ham=True)

    services = get_services()
    assert "logger" in services
    assert "config" in services
    shutdown_services()
