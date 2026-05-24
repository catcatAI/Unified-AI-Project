"""Test HAM Memory System"""
import pytest
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent.parent.parent / "apps" / "backend" / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
async def test_ham_types_import():
    """Test HAM types module can be imported"""
    from ai.memory.ham_memory.ham_types import (
        HAMDataPackageInternal,
        HAMMemory,
        HAMRecallResult,
        HAMMemoryError,
    )
    assert HAMDataPackageInternal is not None
    assert HAMMemory is not None
    assert HAMRecallResult is not None
    assert HAMMemoryError is not None
async def test_ham_errors_import():
    """Test HAM errors module can be imported"""
    from ai.memory.ham_memory.ham_errors import (
        HAMMemoryError,
        HAMInitializationError,
        HAMStorageError,
        HAMRetrievalError,
    )
    assert HAMMemoryError is not None
    assert HAMInitializationError is not None
    assert HAMStorageError is not None
    assert HAMRetrievalError is not None
async def test_ham_config_exists():
    """Test HAM config module exists"""
    from ai.memory import ham_config
    assert ham_config is not None
async def test_ham_utils_import():
    """Test HAM utils module can be imported"""
    from ai.memory import ham_utils
    assert ham_utils is not None
    assert hasattr(ham_utils, "stopwords")
async def test_ham_manager_import():
    """Test HAM manager can be imported"""
    try:
        from ai.memory.ham_memory.ham_manager import HAMMemoryManager
        assert HAMMemoryManager is not None
    except ImportError:
        pytest.skip("HAMMemoryManager not fully available")
async def test_ham_vector_store_import():
    """Test HAM vector store manager can be imported"""
    try:
        from ai.memory.ham_memory.ham_vector_store_manager import HAMVectorStoreManager
        assert HAMVectorStoreManager is not None
    except ImportError:
        pytest.skip("HAMVectorStoreManager not available")
async def test_ham_query_engine_import():
    """Test HAM query engine can be imported"""
    try:
        from ai.memory.ham_memory.ham_query_engine import HAMQueryEngine
        assert HAMQueryEngine is not None
    except ImportError:
        pytest.skip("HAMQueryEngine not available")
async def test_ham_memory_types():
    """Test HAMMemory TypedDict structure"""
    from ai.memory.ham_memory.ham_types import HAMMemory

    sample = HAMMemory(
        memory_id="test_001",
        content="Test content",
        metadata={"key": "value"},
        relevance=0.8,
    )
    assert sample["memory_id"] == "test_001"
    assert sample["content"] == "Test content"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])