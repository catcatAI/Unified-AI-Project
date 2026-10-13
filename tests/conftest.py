"""
Configuration for pytest: Add project source directories to the Python path.
"""

import logging
import os
import sys
import time
from typing import Any, Callable, Dict

import pytest

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_PATH = os.path.join(PROJECT_ROOT, "apps", "backend", "src")

if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)


@pytest.fixture(autouse=True)
def _reset_emotion_threshold_adjustment():
    """Isolate semantic_qa's process-global emotion→threshold increment.

    chat_routes injects it once per turn via set_emotion_threshold_adjustment().
    Path 0 of semantic_qa._emotion_threshold_adjustment() then PREFERS that
    injected value over the state_store event path, so a test that drives the
    chat flow leaves a leaked increment that silently overrides later tests'
    event-driven expectations — cross-file pollution, order dependent (found by
    CI's random directory-combination guard: tests/unit + tests/ai failed,
    tests/ai alone passed). Only touch the module when it is already imported,
    so the fixture stays free for the rest of the suite.
    """
    # `getattr`: an autouse fixture must never be able to break unrelated tests,
    # and this repo has a documented history of replacing sys.modules entries
    # with MagicMock() objects (a stand-in has no state of ours to reset).
    module = sys.modules.get("ai.unified_engine.semantic_qa")
    reset = getattr(module, "reset_emotion_threshold_adjustment", None)
    if reset is None:
        yield
        return
    reset()
    yield
    reset()


def pytest_addoption(parser):
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="run slow stress tests marked pytest.mark.slow_stress "
        "(e.g. tests/benchmarks/test_multimodal_stress.py, ~55s standalone)",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-slow"):
        return
    skip_slow_stress = pytest.mark.skip(
        reason="slow stress test (~55s, stalls combined run); rerun with --run-slow"
    )
    for item in items:
        if "slow_stress" in item.keywords:
            item.add_marker(skip_slow_stress)


def pytest_configure(config):
    config.addinivalue_line("markers", "benchmark: mark tests for benchmarking")
    config.addinivalue_line("markers", "performance: mark tests for performance benchmarking")
    config.addinivalue_line(
        "markers",
        "slow_stress: multi-minute stress tests; deselected unless --run-slow",
    )
    # Prevent ED3NEngine from lazy-loading the full external dictionary
    # (hundreds of thousands of entries) on every test's first process() call.
    # Tests exercise presets/reflex logic, not the production dictionary corpus.
    os.environ.setdefault("ANGELA_SKIP_EXTERNAL_DICTS", "1")


def benchmark(func: Callable, *args, iterations: int = 10, **kwargs) -> Dict[str, float]:
    """Benchmark a function and return timing stats."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func(*args, **kwargs)
        end = time.perf_counter()
        times.append(end - start)
    return {
        "min": min(times),
        "max": max(times),
        "avg": sum(times) / len(times),
        "median": sorted(times)[len(times) // 2],
        "total": sum(times),
        "iterations": iterations,
    }


class PerformanceTimer:
    """Context manager for timing code blocks."""

    def __init__(self, name: str = "block"):
        self.name = name
        self.elapsed = 0.0

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed = time.perf_counter() - self.start
