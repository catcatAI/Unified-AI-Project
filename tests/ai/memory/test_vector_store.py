import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch

from ai.memory.vector_store import VectorMemoryStore, _NumpyBackend, _NUMPY_EMBED_DIM


# =============================================================================
# Numpy backend unit tests
# =============================================================================

class TestNumpyBackendEmbed:
    def test_embed_empty_string(self):
        vec = _NumpyBackend._embed("")
        assert vec.shape == (_NUMPY_EMBED_DIM,)
        assert vec.sum() == 0.0

    def test_embed_single_char(self):
        vec = _NumpyBackend._embed("a")
        assert vec.shape == (_NUMPY_EMBED_DIM,)
        assert vec.sum() == 0.0

    def test_embed_normal_text(self):
        vec = _NumpyBackend._embed("hello world")
        assert vec.shape == (_NUMPY_EMBED_DIM,)
        assert abs(np.linalg.norm(vec) - 1.0) < 1e-6

    def test_embed_deterministic(self):
        v1 = _NumpyBackend._embed("你好世界")
        v2 = _NumpyBackend._embed("你好世界")
        assert np.allclose(v1, v2)

    def test_embed_similar_texts(self):
        v1 = _NumpyBackend._embed("how are you")
        v2 = _NumpyBackend._embed("how are u")
        sim = float(v1 @ v2)
        assert sim > 0.3


class TestNumpyBackendCRUD:
    @pytest.fixture
    def backend(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            b = _NumpyBackend(tmpdir)
            yield b

    @pytest.mark.asyncio
    async def test_add_and_search(self, backend):
        await backend.add_memory("id1", "hello world", {"source": "test"})
        await backend.add_memory("id2", "goodbye world", {"source": "test"})
        results = await backend.semantic_search("hello", limit=5)
        assert "ids" in results
        assert len(results["ids"][0]) == 2
        assert "id1" in results["ids"][0]

    @pytest.mark.asyncio
    async def test_search_empty(self, backend):
        results = await backend.semantic_search("anything")
        assert results == {}

    @pytest.mark.asyncio
    async def test_add_memory_no_metadata(self, backend):
        await backend.add_memory("id1", "content")
        assert len(backend) == 1

    @pytest.mark.asyncio
    async def test_persist(self, backend):
        await backend.add_memory("id1", "hello world")
        assert backend._dirty is False  # auto-saved

    @pytest.mark.asyncio
    async def test_persist_and_reload(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            b1 = _NumpyBackend(tmpdir)
            await b1.add_memory("id1", "hello world", {"k": "v"})
            await b1.add_memory("id2", "goodbye world")
            del b1

            b2 = _NumpyBackend(tmpdir)
            assert len(b2) == 2
            results = await b2.semantic_search("hello", limit=5)
            assert len(results["ids"][0]) == 2


# =============================================================================
# VectorMemoryStore integration tests
# =============================================================================

@pytest.fixture
def mock_chromadb():
    """Mock chromadb module to be importable."""
    m = MagicMock()
    client = MagicMock()
    collection = MagicMock()
    client.get_or_create_collection.return_value = collection
    m.PersistentClient.return_value = client
    m.Client.return_value = client
    return m


class TestVectorMemoryStoreInit:
    def test_uses_numpy_when_chromadb_unavailable(self):
        with patch("ai.memory.vector_store._lazy_chromadb", return_value=None):
            with tempfile.TemporaryDirectory() as tmpdir:
                store = VectorMemoryStore(persist_directory=tmpdir)
                assert store.client is None
                assert store.collection is None
                assert store._numpy_backend is not None

    def test_uses_chromadb_when_available(self, mock_chromadb):
        with patch("ai.memory.vector_store._lazy_chromadb", return_value=mock_chromadb):
            with tempfile.TemporaryDirectory() as tmpdir:
                store = VectorMemoryStore(persist_directory=tmpdir)
                assert store.client is not None
                assert store.collection is not None
                assert store._numpy_backend is None

    def test_falls_back_when_chromadb_init_fails(self, mock_chromadb):
        mock_chromadb.PersistentClient.side_effect = Exception("init failed")
        with patch("ai.memory.vector_store._lazy_chromadb", return_value=mock_chromadb):
            with tempfile.TemporaryDirectory() as tmpdir:
                store = VectorMemoryStore(persist_directory=tmpdir)
                assert store.client is None
                assert store.collection is None
                assert store._numpy_backend is not None


class TestVectorMemoryStoreNumpyBackend:
    @pytest.fixture
    def store(self):
        with patch("ai.memory.vector_store._lazy_chromadb", return_value=None):
            with tempfile.TemporaryDirectory() as tmpdir:
                yield VectorMemoryStore(persist_directory=tmpdir)

    @pytest.mark.asyncio
    async def test_add_memory_success(self, store):
        await store.add_memory("mem1", "hello world", {"key": "val"})
        assert len(store) == 1

    @pytest.mark.asyncio
    async def test_add_memory_no_metadata(self, store):
        await store.add_memory("mem2", "content")
        assert len(store) == 1

    @pytest.mark.asyncio
    async def test_add_memory_not_initialized(self):
        with patch("ai.memory.vector_store._lazy_chromadb", return_value=None):
            store = VectorMemoryStore()
            store._numpy_backend = None
            await store.add_memory("mem1", "content")

    @pytest.mark.asyncio
    async def test_search_success(self, store):
        await store.add_memory("mem1", "hello world", {"key": "val"})
        await store.add_memory("mem2", "goodbye world")
        results = await store.semantic_search("hello", limit=5)
        assert "ids" in results
        assert len(results["ids"][0]) == 2

    @pytest.mark.asyncio
    async def test_search_default_limit(self, store):
        for i in range(15):
            await store.add_memory(f"mem{i}", f"content {i}")
        results = await store.semantic_search("content")
        assert len(results["ids"][0]) == 10

    @pytest.mark.asyncio
    async def test_search_empty_store(self):
        with patch("ai.memory.vector_store._lazy_chromadb", return_value=None):
            with tempfile.TemporaryDirectory() as tmpdir:
                store = VectorMemoryStore(persist_directory=tmpdir)
                results = await store.semantic_search("query")
                assert results == {}

    @pytest.mark.asyncio
    async def test_persist(self, store):
        await store.add_memory("mem1", "hello world")
        store.persist()

    @pytest.mark.asyncio
    async def test_load_existing_data(self, store):
        await store.add_memory("persist1", "hello world")
        persist_dir = store.persist_directory
        store.persist()

        with patch("ai.memory.vector_store._lazy_chromadb", return_value=None):
            store2 = VectorMemoryStore(persist_directory=persist_dir)
            assert len(store2) == 1
            results = await store2.semantic_search("hello", limit=5)
            assert "persist1" in results["ids"][0]

    @pytest.mark.asyncio
    async def test_corrupted_data_starts_fresh(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_json = os.path.join(tmpdir, "metadata.json")
            with open(bad_json, "w") as f:
                f.write("not json")
            with patch("ai.memory.vector_store._lazy_chromadb", return_value=None):
                store = VectorMemoryStore(persist_directory=tmpdir)
                assert len(store) == 0


class TestVectorMemoryStoreChromadbBackend:
    @pytest.mark.asyncio
    async def test_add_memory_delegates_to_collection(self, mock_chromadb):
        with patch("ai.memory.vector_store._lazy_chromadb", return_value=mock_chromadb):
            with tempfile.TemporaryDirectory() as tmpdir:
                store = VectorMemoryStore(persist_directory=tmpdir)
                await store.add_memory("mem1", "hello", {"k": "v"})
                collection = mock_chromadb.PersistentClient.return_value.get_or_create_collection.return_value
                collection.add.assert_called_once_with(
                    documents=["hello"], metadatas=[{"k": "v"}], ids=["mem1"]
                )

    @pytest.mark.asyncio
    async def test_semantic_search_delegates(self, mock_chromadb):
        with patch("ai.memory.vector_store._lazy_chromadb", return_value=mock_chromadb):
            with tempfile.TemporaryDirectory() as tmpdir:
                store = VectorMemoryStore(persist_directory=tmpdir)
                collection = mock_chromadb.PersistentClient.return_value.get_or_create_collection.return_value
                collection.query.return_value = {"ids": [["id1"]]}
                results = await store.semantic_search("test", limit=5)
                collection.query.assert_called_once_with(query_texts=["test"], n_results=5)


# Re-run original tests for backward compatibility
@pytest.mark.asyncio
async def test_backward_compatible_add_memory():
    with patch("ai.memory.vector_store._lazy_chromadb", return_value=None):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = VectorMemoryStore(persist_directory=tmpdir)
            await store.add_memory("mem1", "hello world", {"key": "val"})
            assert len(store) == 1


import numpy as np
