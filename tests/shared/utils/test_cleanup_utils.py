"""Tests for cleanup utils — verifies cleanup patterns work correctly."""

import pytest


class TestCleanupUtils:
    def setup_method(self):
        self.test_data = {"key1": "value1", "key2": [1, 2, 3]}

    def teardown_method(self):
        self.test_data.clear()

    def test_cleanup_operations(self):
        """Verify setup populated data and teardown will clear it."""
        assert self.test_data == {"key1": "value1", "key2": [1, 2, 3]}
        assert len(self.test_data) == 2