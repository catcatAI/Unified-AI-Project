import pytest

pytest.importorskip("fragmenta.element_layer")
from fragmenta.element_layer import ElementLayer


class TestElementLayer:
    async def test_element_layer_instantiation(self):
        layer = ElementLayer()
        assert layer is not None
        assert layer.transformation_count == 0

    async def test_element_layer_process(self):
        layer = ElementLayer()
        result = layer.process_elements([{"type": "text", "content": " hello "}])
        assert len(result) == 1
        assert result[0]["content"] == "hello"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
