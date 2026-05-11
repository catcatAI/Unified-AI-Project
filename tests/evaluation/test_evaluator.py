"""Tests for evaluator."""

import pytest


class TestEvaluator:
    def setup_method(self):
        self.test_data = {}

    def teardown_method(self):
        self.test_data.clear()

    def test_evaluate(self):
        assert True