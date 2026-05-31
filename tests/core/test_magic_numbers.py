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
