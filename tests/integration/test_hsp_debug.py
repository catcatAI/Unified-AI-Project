"""
测试模块 - test_hsp_debug
"""

import pytest


class TestHSPDebug:
    @pytest.fixture(autouse=True)
    def setup_test(self):
        yield
    async def test_hsp_debug_basic(self):
        debug_info = {"timestamp": "2026-01-01", "level": "info"}
        assert debug_info is not None
    async def test_hsp_message_debugging(self):
        message = {"type": "test", "payload": {"data": "test"}}
        assert message["type"] == "test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])