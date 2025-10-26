"""
Tests for the AlphaDeepModel, focusing on compression and data handling.
"""

import pytest
from apps.backend.src.core_ai.compression.alpha_deep_model import (
    AlphaDeepModel, DeepParameter, HAMGist, RelationalContext, Modalities, CompressionAlgorithm
)

@pytest.fixture
def model_and_data():
    """Provides a model instance and sample data for tests."""
    model = AlphaDeepModel()
    sample_data = DeepParameter(
        source_memory_id="mem_test_001",
        timestamp="2025-08-04T05:00:00Z",
        base_gist=HAMGist(
            summary="Test summary.",
            keywords=["test", "summary"],
            original_length=20
        ),
        relational_context=RelationalContext(
            entities=["Entity A", "Entity B"],
            relationships=[{"subject": "Entity A", "verb": "is_related_to", "object": "Entity B"}]
        ),
        modalities=Modalities(
            text_confidence=0.99,
            audio_features={"pitch": 150.5}
        ),
        dna_chain_id="test_chain_001"
    )
    return model, sample_data

def test_compress_decompress_cycle(model_and_data):
    """Test that data remains identical after a full compression-decompression cycle."""
    model, sample_data = model_and_data
    original_dict = sample_data.to_dict()

    compressed = model.compress(sample_data)
    assert isinstance(compressed, bytes)

    decompressed = model.decompress(compressed)
    assert isinstance(decompressed, dict)

    assert original_dict == decompressed

def test_invalid_input_type_raises_error(model_and_data):
    """Test that passing an invalid object type to compress raises a TypeError."""
    model, _ = model_and_data
    with pytest.raises(TypeError):
        model.compress(12345) # Invalid type

def test_dict_input(model_and_data):
    """Test that the compress method can handle a dictionary input directly."""
    model, sample_data = model_and_data
    original_dict = sample_data.to_dict()

    compressed = model.compress(original_dict)
    decompressed = model.decompress(compressed)

    assert original_dict == decompressed

@pytest.mark.parametrize("algorithm", [
    CompressionAlgorithm.ZLIB,
    CompressionAlgorithm.BZ2,
    CompressionAlgorithm.LZMA,
    CompressionAlgorithm.MSGPACK_ONLY
])
def test_different_compression_algorithms(model_and_data, algorithm):
    """Test compression and decompression with different algorithms."""
    model, sample_data = model_and_data
    original_dict = sample_data.to_dict()

    compressed = model.compress(sample_data, algorithm)
    assert isinstance(compressed, bytes)

    decompressed = model.decompress(compressed, algorithm)
    assert isinstance(decompressed, dict)

    assert original_dict == decompressed
