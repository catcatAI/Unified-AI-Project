import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "benchmark: mark tests for benchmarking")
    config.addinivalue_line("markers", "performance: mark tests for performance benchmarking")
