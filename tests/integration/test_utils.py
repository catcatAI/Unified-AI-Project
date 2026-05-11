"""
测试模块 - test_utils
"""

import pytest
from unittest.mock import Mock


class TestUtils:
    @pytest.fixture(autouse=True)
    def setup_test(self):
        self.start_time = None
        yield

    def test_utils_basic(self):
        mock_util = Mock()
        mock_util.process.return_value = {"result": "success"}
        result = mock_util.process()
        assert result["result"] == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])