"""
Configuration for pytest: Add project source directories to the Python path.
"""

import logging
import os
import sys
import time
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_PATH = os.path.join(PROJECT_ROOT, "apps", "backend", "src")

if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)


def pytest_configure(config):
    config.addinivalue_line("markers", "benchmark: mark tests for benchmarking")
    config.addinivalue_line("markers", "performance: mark tests for performance benchmarking")


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
