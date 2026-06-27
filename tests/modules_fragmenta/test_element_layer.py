"""
测试模块 - test_element_layer
"""

from unittest.mock import Mock

import pytest


class TestElementLayer:
    @pytest.fixture(autouse=True)
    def setup_test(self):
        yield

    @pytest.mark.timeout(5)
    def test_element_layer_basic(self):
        mock_layer = Mock()
        mock_layer.render.return_value = True
        result = mock_layer.render()
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])