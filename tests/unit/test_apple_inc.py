"""Tests for Apple Inc integration."""
import pytest


class TestAppleInc:
    def setup_method(self):
        self.test_data = {}

    def teardown_method(self):
        self.test_data.clear()

    def test_apple_inc_data_dict(self):
        assert isinstance(self.test_data, dict)

    def test_setup_populated(self):
        assert len(self.test_data) == 0