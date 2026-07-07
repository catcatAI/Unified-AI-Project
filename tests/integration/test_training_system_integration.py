import pytest

pytest.importorskip("ai.ed3n.dictionary_layer")
from ai.ed3n.dictionary_layer import DictionaryLayer


class TestTrainingSystemIntegration:
    async def test_dictionary_layer_instantiation(self):
        d = DictionaryLayer()
        assert d is not None

    async def test_dictionary_layer_encode(self):
        d = DictionaryLayer()
        result = d.encode_soft("test")
        assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
