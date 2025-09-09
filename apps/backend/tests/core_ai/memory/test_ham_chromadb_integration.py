import pytest
import asyncio
import os
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import time
import gc

# Mock SentenceTransformer at the top level to prevent import errors
class MockSentenceTransformer:
    def encode(self, texts, *args, **kwargs):
        # Return a dummy embedding (e.g., a list of zeros or ones)
        # The size (384) should match the expected model output for 'all-MiniLM-L6-v2'
        return [[0.1] * 384 for _ in texts]

class MockEmbeddingFunction:
    def __call__(self, input: List[str]) -> List[List[float]]:
        # Return dummy embeddings of the correct dimension
        return [[0.1] * 384 for _ in input]

    def name(self) -> str:
        return "mock_embedding_function"

# Patch the SentenceTransformer class before HAMMemoryManager is imported
# This needs to be done carefully to avoid circular imports or issues with how pytest loads modules
# For this specific test, we'll patch it within the fixture setup.

# Add the backend to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.backend.src.ai.memory.ham_memory_manager import HAMMemoryManager
from apps.backend.src.ai.memory.ham_types import HAMRecallResult

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

# Define a consistent test output directory (relative to project root)
TEST_STORAGE_DIR = os.path.join(project_root, "tests", "test_output_data", "ham_memory_chroma")

import chromadb # Added for fixture

@pytest.fixture(scope="function")
def ham_chroma_manager_fixture():
    # Use PersistentClient to avoid HTTP-only mode issues
    import tempfile
    import shutil
    temp_dir = tempfile.mkdtemp()
    client = chromadb.PersistentClient(path=temp_dir)

    # Create the manager and inject the client
    ham_manager = HAMMemoryManager(
        core_storage_filename="test_ham_chroma_core_memory.json",
        storage_dir=TEST_STORAGE_DIR, # Still provide a dummy storage_dir for HAMMemoryManager init
        chroma_client=client  # Pass the initialized client here
    )

    yield ham_manager

    # Teardown: Clean up temporary directory
    try:
        del client
        gc.collect()
        time.sleep(0.1) # Small delay to help with resource release
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception as e:
        print(f"Warning: Failed to clean up temp directory {temp_dir}: {e}")

@pytest.mark.asyncio
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_01_store_experience_and_verify_chromadb_entry(ham_chroma_manager_fixture):
    print("\n--- Test 01: Store Experience and Verify ChromaDB Entry ---")
    ham = ham_chroma_manager_fixture
    raw_text = "The quick brown fox jumps over the lazy dog."
    metadata: Dict[str, Any] = {"source": "test_chroma_store", "timestamp": datetime.now(timezone.utc).isoformat()}

    memory_id = await ham.store_experience(raw_text, "dialogue_text", metadata)
    assert memory_id is not None

    # Directly query ChromaDB to verify the entry
    # Note: ChromaDB's query method returns a dict with lists of results
    chroma_results = ham.chroma_collection.get(ids=[memory_id], include=['embeddings', 'documents', 'metadatas'])
    
    assert len(chroma_results['ids']) == 1
    assert chroma_results['ids'][0] == memory_id
    assert chroma_results['documents'][0] == raw_text
    assert 'source' in chroma_results['metadatas'][0]
    assert chroma_results['metadatas'][0]['source'] == "test_chroma_store"
    assert len(chroma_results['embeddings'][0]) > 0 # Check if embedding was generated
    print("Test 01 PASSED")

@pytest.mark.asyncio
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_02_semantic_search_chromadb_first(ham_chroma_manager_fixture):
    print("\n--- Test 02: Semantic Search (ChromaDB first) ---")
    ham = ham_chroma_manager_fixture

    # Store several distinct experiences
    await ham.store_experience("Apple is a fruit.", "fact", {"topic": "food"})
    await ham.store_experience("Python is a programming language.", "fact", {"topic": "programming"})
    await ham.store_experience("The sun is a star.", "fact", {"topic": "astronomy"})
    await ham.store_experience("A red delicious apple.", "fact", {"topic": "food"})

    # Perform a semantic query
    query_text = "What kind of fruit is red?"
    results = ham.query_core_memory(semantic_query=query_text, limit=1, sort_by_confidence=True)

    assert len(results) == 1
    # The exact content might vary based on embedding model, but it should be related to apples
    assert "apple" in results[0]["rehydrated_gist"].lower()
    print("Test 02 PASSED")

@pytest.mark.asyncio
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_03_semantic_search_chromadb_failure_fallback(ham_chroma_manager_fixture):
    print("\n--- Test 03: Semantic Search Fallback (ChromaDB failure) ---")
    ham = ham_chroma_manager_fixture

    # Store some experiences
    await ham.store_experience("This is a fallback test sentence.", "test_type", {"tag": "fallback"})
    await ham.store_experience("Another sentence for testing.", "test_type", {"tag": "general"})

    # Simulate ChromaDB query failure
    with patch.object(ham.chroma_collection, 'query', side_effect=Exception("ChromaDB is down")):
        query_text = "Test sentence for fallback."
        results = ham.query_core_memory(semantic_query=query_text, limit=1, sort_by_confidence=True)

        assert len(results) == 1
        assert "fallback test sentence" in results[0]["rehydrated_gist"].lower()
        print("Test 03 PASSED")
