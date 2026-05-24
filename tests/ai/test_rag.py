"""Tests for apps.backend.src.ai.rag.rag_manager"""
import sys
from unittest.mock import MagicMock, patch

import pytest

# Mock transformers_compat before importing rag_manager
transformers_compat_mock = MagicMock()
transformers_compat_mock.import_sentence_transformers.return_value = (None, False)
sys.modules['src.compat.transformers_compat'] = transformers_compat_mock

# Also mock faiss so module-level import succeeds
sys.modules['faiss'] = MagicMock()

from apps.backend.src.ai.rag.rag_manager import RAGManager


class TestRAGManagerInit:
    def test_init_without_sentence_transformers(self):
        """Model is None when sentence-transformers is unavailable"""
        manager = RAGManager(model_name='all-MiniLM-L6-v2')
        assert manager.model is None
        assert manager.embedding_dim == 0
        assert manager.index is None
        assert manager.documents == {}
        assert manager.next_doc_id == 0


class TestRAGManagerWithMockedModel:
    @patch('apps.backend.src.ai.rag.rag_manager.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    @patch('apps.backend.src.ai.rag.rag_manager.FAISS_AVAILABLE', True)
    @patch('apps.backend.src.ai.rag.rag_manager.SentenceTransformer')
    @patch('apps.backend.src.ai.rag.rag_manager.faiss')
    def test_init_with_model(self, mock_faiss, mock_st_cls):
        mock_model = MagicMock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_st_cls.return_value = mock_model

        mock_index = MagicMock()
        mock_faiss.IndexFlatL2.return_value = mock_index

        manager = RAGManager(model_name='all-MiniLM-L6-v2')
        assert manager.model is mock_model
        assert manager.embedding_dim == 384
        assert manager.index is mock_index

    @patch('apps.backend.src.ai.rag.rag_manager.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    @patch('apps.backend.src.ai.rag.rag_manager.FAISS_AVAILABLE', True)
    @patch('apps.backend.src.ai.rag.rag_manager.SentenceTransformer')
    @patch('apps.backend.src.ai.rag.rag_manager.faiss')
    def test_add_document(self, mock_faiss, mock_st_cls):
        mock_model = MagicMock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_model.encode.return_value = [[0.1, 0.2]]
        mock_st_cls.return_value = mock_model

        mock_index = MagicMock()
        mock_index.ntotal = 0
        mock_faiss.IndexFlatL2.return_value = mock_index
        # Simulate ntotal incrementing after add
        mock_faiss.normalize_L2 = MagicMock()
        mock_index.add = MagicMock()

        manager = RAGManager(model_name='all-MiniLM-L6-v2')
        manager.index = mock_index
        manager.model = mock_model

        manager.add_document('test document')
        mock_model.encode.assert_called_once_with(['test document'])

    @patch('apps.backend.src.ai.rag.rag_manager.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    @patch('apps.backend.src.ai.rag.rag_manager.FAISS_AVAILABLE', True)
    @patch('apps.backend.src.ai.rag.rag_manager.SentenceTransformer')
    @patch('apps.backend.src.ai.rag.rag_manager.faiss')
    def test_search_with_results(self, mock_faiss, mock_st_cls):
        mock_model = MagicMock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_model.encode.return_value = [[0.1, 0.2]]
        mock_st_cls.return_value = mock_model

        mock_index = MagicMock()
        mock_index.ntotal = 1
        mock_index.search.return_value = ([[0.2, 0.0]], [[0, -1]])
        mock_faiss.IndexFlatL2.return_value = mock_index
        mock_faiss.normalize_L2 = MagicMock()

        manager = RAGManager(model_name='all-MiniLM-L6-v2')
        manager.index = mock_index
        manager.model = mock_model
        manager.documents = {0: 'test document'}

        results = manager.search('test query', k=2)
        assert len(results) == 1
        assert results[0] == ('test document', 0.8)

    @patch('apps.backend.src.ai.rag.rag_manager.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    @patch('apps.backend.src.ai.rag.rag_manager.FAISS_AVAILABLE', True)
    @patch('apps.backend.src.ai.rag.rag_manager.SentenceTransformer')
    @patch('apps.backend.src.ai.rag.rag_manager.faiss')
    def test_search_no_documents(self, mock_faiss, mock_st_cls):
        mock_model = MagicMock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_st_cls.return_value = mock_model

        mock_index = MagicMock()
        mock_index.ntotal = 0
        mock_faiss.IndexFlatL2.return_value = mock_index

        manager = RAGManager(model_name='all-MiniLM-L6-v2')
        manager.index = mock_index
        manager.model = mock_model

        results = manager.search('test query')
        assert results == []


class TestRAGManagerNoModel:
    def test_add_document_no_model(self):
        manager = RAGManager()
        manager.add_document('test')
        assert manager.documents == {}

    def test_search_no_model(self):
        manager = RAGManager()
        results = manager.search('test query')
        assert results == []

    def test_search_empty_index(self):
        manager = RAGManager()
        manager.model = MagicMock()
        results = manager.search('test')
        assert results == []
