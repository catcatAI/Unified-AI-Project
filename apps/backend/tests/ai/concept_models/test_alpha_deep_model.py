import pytest
import asyncio
import tensorflow as tf
import numpy as np
from unittest.mock import MagicMock
from apps.backend.src.ai.concept_models.alpha_deep_model import AlphaDeepModel

@pytest.fixture
def alpha_deep_model():
    """Fixture to provide a fresh AlphaDeepModel instance for each test."""
    return AlphaDeepModel()

@pytest.mark.asyncio
async def test_alpha_deep_model_initialization(alpha_deep_model: AlphaDeepModel):
    """Test if the AlphaDeepModel initializes correctly."""
    assert alpha_deep_model.model_state["version"] == "1.0"
    assert "parameters" in alpha_deep_model.model_state
    assert isinstance(alpha_deep_model.dummy_model, MagicMock)


@pytest.mark.asyncio
async def test_learn_method_with_vector_data(alpha_deep_model: AlphaDeepModel):
    """Test the learn method with valid vector data."""
    test_data = {"type": "embedding", "vector_data": np.random.rand(1, 10).tolist()} # Needs to be list for tf.constant
    
    result = await alpha_deep_model.learn(test_data)
    
    assert result["status"] == "learned"
    assert "model_state" in result
    assert "learning_output" in result
    assert result["learning_output"]["model_processed"] is True
    assert "last_update" in alpha_deep_model.model_state["parameters"]
    # assert "learning_progress" in alpha_deep_model.model_state["parameters"]

@pytest.mark.asyncio
async def test_learn_method_without_vector_data(alpha_deep_model: AlphaDeepModel):
    """Test the learn method without vector data."""
    test_data = {"type": "text_corpus", "content": "Some text data."}
    
    result = await alpha_deep_model.learn(test_data)
    
    assert result["status"] == "learned"
    assert "model_state" in result
    assert "learning_output" in result
    assert result["learning_output"]["model_processed"] is False
    assert "reason" in result["learning_output"]
    assert "last_update" in alpha_deep_model.model_state["parameters"]
    # assert "learning_progress" in alpha_deep_model.model_state["parameters"]

@pytest.mark.asyncio
async def test_compress_method(alpha_deep_model: AlphaDeepModel):
    """Test the compress method."""
    test_data = {"image_features": [0.1, 0.2, 0.3, 0.4], "metadata": {"source": "camera"}}
    
    result = await alpha_deep_model.compress(test_data)
    
    assert result["status"] == "failed"

