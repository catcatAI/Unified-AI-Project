"""P6-3 — Magic number migration tests"""


class TestMagicNumbers:

    def test_behavior_threshold_returns_default(self):
        from core.system.config.magic_numbers import behavior_threshold

        val = behavior_threshold("nonexistent_key", 42)
        assert val == 42

    def test_behavior_threshold_reads_config(self):
        from core.system.config.magic_numbers import behavior_threshold

        val = behavior_threshold("trigger_threshold_default")
        assert val is not None

    def test_timing_value_returns_default(self):
        from core.system.config.magic_numbers import timing_value

        val = timing_value("nonexistent.key", "fallback")
        assert val == "fallback"

    def test_timing_value_reads_config(self):
        from core.system.config.magic_numbers import timing_value

        val = timing_value("loop.sleep_short")
        assert val is not None

    def test_loop_sleep_default(self):
        from core.system.config.magic_numbers import loop_sleep

        val = loop_sleep("nonexistent", 0.5)
        assert val == 0.5

    def test_timeout_value_default(self):
        from core.system.config.magic_numbers import timeout_value

        val = timeout_value("nonexistent", 99.0)
        assert val == 99.0

    def test_llm_param_default(self):
        from core.system.config.magic_numbers import llm_param

        val = llm_param("nonexistent", "fallback")
        assert val == "fallback"

    def test_behavior_feedback_returns_default(self):
        from core.system.config.magic_numbers import behavior_feedback

        val = behavior_feedback("nonexistent_key", 42)
        assert val == 42

    def test_behavior_feedback_reads_config(self):
        from core.system.config.magic_numbers import behavior_feedback

        val = behavior_feedback("success_threshold")
        assert val is not None

    def test_behavior_executor_returns_default(self):
        from core.system.config.magic_numbers import behavior_executor

        val = behavior_executor("nonexistent_key", 42)
        assert val == 42

    def test_behavior_executor_reads_config(self):
        from core.system.config.magic_numbers import behavior_executor

        val = behavior_executor("default_action_timeout")
        assert val is not None


class TestMagicNumbersSuffixLookup:
    """Flat/partial key names must resolve against the nested tiered YAML tree."""

    def test_flat_key_matches_nested_yaml(self):
        from core.system.config.magic_numbers import _get

        val = _get("sleep_medium", 99.0)
        assert val == 0.5

    def test_flat_key_matches_heartbeat(self):
        from core.system.config.magic_numbers import _get

        val = _get("max_interval", 99.0)
        assert val == 60.0

    def test_partial_dotted_key_matches(self):
        from core.system.config.magic_numbers import _get

        val = _get("loop.sleep_very_long", 99.0)
        assert val == 10.0

    def test_missing_key_falls_back(self):
        from core.system.config.magic_numbers import _get

        assert _get("definitely_not_a_key", 42) == 42

    def test_exact_dotted_path_still_works(self):
        from core.system.config.magic_numbers import _get

        cfg = _get("system.compute.compute", {})
        assert isinstance(cfg, dict)
        assert "ed3n_snn" in cfg


class TestStrictNumericContracts:
    """R23: _safe_float/int 收緊後仍回 default（不透傳原值），且型別誠實。"""

    def test_safe_float_bad_value_returns_default(self):
        from core.system.config.magic_numbers import _safe_float

        assert _safe_float("abc", 1.5) == 1.5
        assert _safe_float(None, 2.0) == 2.0
        assert isinstance(_safe_float("12.5", 0.0), float)

    def test_safe_int_bad_value_returns_default(self):
        from core.system.config.magic_numbers import _safe_int

        assert _safe_int("abc", 7) == 7
        assert _safe_int(None, 3) == 3
        assert isinstance(_safe_int("12", 0), int)

    def test_wrappers_return_typed_values(self):
        from core.system.config.magic_numbers import (
            cache_value,
            compute_log_fallback,
            limit_value,
            timeout_value,
        )

        assert isinstance(timeout_value("nonexistent.key.xyz", 30.0), float)
        assert isinstance(cache_value("nonexistent.key.xyz", 100), int)
        assert isinstance(limit_value("nonexistent.key.xyz", 100), int)
        assert isinstance(compute_log_fallback(), bool)
