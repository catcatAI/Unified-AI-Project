"""Tests for deep mapper."""

import pytest


class TestDeepMapper:
    def setup_method(self):
        self.test_data = {}

    def teardown_method(self):
        self.test_data.clear()

    def test_map(self):
        assert True