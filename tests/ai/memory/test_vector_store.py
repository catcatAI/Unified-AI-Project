import pytest
from unittest.mock import MagicMock, patch

from apps.backend.src.ai.memory.vector_store import VectorMemoryStore


@pytest.fixture
def mock_collection():
    return MagicMock()


@pytest.fixture
def mock_client(mock_collection):
    client = MagicMock()
    client.get_or_create_collection.return_value = mock_collection
    return client


@pytest.fixture
def vector_store(mock_client):
    with patch('apps.backend.src.ai.memory.vector_store.chromadb.Client', return_value=mock_client):
        store = VectorMemoryStore()
        return store


@pytest.fixture
def vector_store_persist(mock_client):
    with patch('apps.backend.src.ai.memory.vector_store.chromadb.PersistentClient', return_value=mock_client):
        store = VectorMemoryStore(persist_directory='/tmp/test')
        return store


class TestVectorMemoryStoreInit:

    def test_init_ephemeral(self, mock_client):
        with patch('apps.backend.src.ai.memory.vector_store.chromadb.Client', return_value=mock_client) as mock_cls:
            store = VectorMemoryStore()
            mock_cls.assert_called_once()
            assert store.client is not None
            assert store.collection is not None

    def test_init_persistent(self, mock_client):
        with patch('apps.backend.src.ai.memory.vector_store.chromadb.PersistentClient', return_value=mock_client) as mock_cls:
            store = VectorMemoryStore(persist_directory='/tmp/test')
            mock_cls.assert_called_once_with(path='/tmp/test')
            assert store.client is not None
            assert store.collection is not None

    def test_init_collection_name_and_metadata(self, mock_client):
        with patch('apps.backend.src.ai.memory.vector_store.chromadb.Client', return_value=mock_client):
            store = VectorMemoryStore()
            mock_client.get_or_create_collection.assert_called_once_with(
                name='ham_memories', metadata={'hnsw:space': 'cosine'}
            )

    def test_init_failure_sets_none(self):
        with patch('apps.backend.src.ai.memory.vector_store.chromadb.Client', side_effect=Exception('fail')):
            store = VectorMemoryStore()
            assert store.client is None
            assert store.collection is None


class TestVectorMemoryStoreAddMemory:

    @pytest.mark.asyncio
    async def test_add_memory_success(self, vector_store, mock_collection):
        await vector_store.add_memory('mem1', 'hello world', {'key': 'val'})
        mock_collection.add.assert_called_once_with(
            documents=['hello world'], metadatas=[{'key': 'val'}], ids=['mem1']
        )

    @pytest.mark.asyncio
    async def test_add_memory_no_metadata(self, vector_store, mock_collection):
        await vector_store.add_memory('mem2', 'content')
        mock_collection.add.assert_called_once_with(
            documents=['content'], metadatas=[{}], ids=['mem2']
        )

    @pytest.mark.asyncio
    async def test_add_memory_not_initialized(self, mock_collection):
        store = VectorMemoryStore()
        store.collection = None
        await store.add_memory('mem1', 'content')
        mock_collection.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_add_memory_exception_handled(self, vector_store, mock_collection):
        mock_collection.add.side_effect = Exception('add error')
        await vector_store.add_memory('mem1', 'content')
        mock_collection.add.assert_called_once()


class TestVectorMemoryStoreSemanticSearch:

    @pytest.mark.asyncio
    async def test_search_success(self, vector_store, mock_collection):
        mock_collection.query.return_value = {'ids': [['id1']], 'documents': [['doc1']]}
        results = await vector_store.semantic_search('test query', limit=5)
        mock_collection.query.assert_called_once_with(query_texts=['test query'], n_results=5)
        assert results['ids'] == [['id1']]

    @pytest.mark.asyncio
    async def test_search_default_limit(self, vector_store, mock_collection):
        mock_collection.query.return_value = {'ids': []}
        await vector_store.semantic_search('hello')
        mock_collection.query.assert_called_once_with(query_texts=['hello'], n_results=10)

    @pytest.mark.asyncio
    async def test_search_not_initialized(self, mock_collection):
        store = VectorMemoryStore()
        store.collection = None
        results = await store.semantic_search('query')
        assert results == {}
        mock_collection.query.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_exception_returns_empty(self, vector_store, mock_collection):
        mock_collection.query.side_effect = Exception('query error')
        results = await vector_store.semantic_search('query')
        assert results == {}
