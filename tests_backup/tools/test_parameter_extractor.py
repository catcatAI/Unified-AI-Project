import pytest
from unittest.mock import patch, MagicMock

from tools.parameter_extractor.extractor import ParameterExtractor

@pytest.fixture
def extractor():
    """Create a ParameterExtractor instance for testing."""
    return ParameterExtractor(repo_id="bert-base-uncased")

@patch('apps.backend.src.tools.parameter_extractor.extractor.hf_hub_download')
def test_download_model_parameters(mock_hf_hub_download, extractor) -> None:
    # Arrange
    mock_hf_hub_download.return_value = "/fake/path/pytorch_model.bin"

    # Act
    result = extractor.download_model_parameters(filename="pytorch_model.bin")

    # Assert
    mock_hf_hub_download.assert_called_once_with(
        repo_id="bert-base-uncased",
        filename="pytorch_model.bin",
        cache_dir="model_cache"  # Using default value
    )
    assert result == "/fake/path/pytorch_model.bin"

def test_map_parameters(extractor) -> None:
    # Arrange
    source_params = {
        "bert.embeddings.word_embeddings.weight": 1,
        "bert.pooler.dense.weight": 2,
        "bert.pooler.dense.bias": 3,
        "some.other.param": 4,
    }
    mapping_rules = {
        "bert.embeddings.word_embeddings.weight": "embeddings.weight",
        "bert.pooler.dense.weight": "pooler.weight",
    }

    # Act
    mapped_params = extractor.map_parameters(source_params, mapping_rules)

    # Assert
    expected_params = {
        "embeddings.weight": 1,
        "pooler.weight": 2,
    }
    assert mapped_params == expected_params

def test_load_parameters_to_model(extractor) -> None:
    # Arrange
    model = MagicMock()
    model.load_state_dict = MagicMock()
    params = {"param1": 1, "param2": 2}

    # Act
    extractor.load_parameters_to_model(model, params)

    # Assert
    model.load_state_dict.assert_called_once_with(params)
