import pytest
from unittest.mock import patch, MagicMock
import numpy as np

# It's crucial to patch the dependencies before importing the class that uses them.
# This ensures that RAGManager gets the mocked versions of SentenceTransformer and faiss.
with patch('sentence_transformers.SentenceTransformer') as mock_st_class, \
     patch('faiss.IndexFlatL2') as mock_faiss_index, \
     patch('faiss.normalize_L2') as mock_faiss_normalize:

    # Configure the mocks before they are used by RAGManager during import/instantiation
    mock_st_instance = MagicMock()
    mock_st_instance.get_sentence_embedding_dimension.return_value = 768
    mock_st_instance.encode.return_value = np.random.rand(1, 768)
    mock_st_class.return_value = mock_st_instance

    from src.core_ai.rag.rag_manager import RAGManager

@pytest.fixture
def rag_manager():
    """Provides a RAGManager instance with mocked dependencies for each test."""
    # Reset mocks before each test to ensure isolation
    mock_st_class.reset_mock()
    mock_faiss_index.reset_mock()
    mock_faiss_normalize.reset_mock()

    # Re-configure the mock SentenceTransformer instance for the test
    mock_st_instance = MagicMock()
    mock_st_instance.get_sentence_embedding_dimension.return_value = 768
    mock_st_instance.encode.return_value = np.random.rand(1, 768)
    mock_st_class.return_value = mock_st_instance
    
    return RAGManager()

@pytest.mark.timeout(5)
def test_rag_manager_initialization(rag_manager):
    """Test that RAGManager initializes correctly."""
    assert rag_manager is not None
    # Verify that the SentenceTransformer was called with the default model
    mock_st_class.assert_called_with('all-MiniLM-L6-v2')
    # Verify that the FAISS index was created with the correct dimension
    rag_manager.model.get_sentence_embedding_dimension.assert_called_once()
    mock_faiss_index.assert_called_with(768)

@pytest.mark.timeout(5)
def test_add_document(rag_manager):
    """Test adding a document to the RAGManager."""
    text = 'This is a test document.'
    rag_manager.add_document(text)

    # Check that encode was called
    rag_manager.model.encode.assert_called_with([text])
    # Check that the index's add method was called
    rag_manager.index.add.assert_called_once()
    # Check that the document is stored
    assert rag_manager.documents[rag_manager.index.ntotal - 1] == text

@pytest.mark.timeout(5)
def test_search(rag_manager):
    """Test searching for a document."""
    rag_manager.add_document('This is a test document.')
    rag_manager.add_document('This is another test document.')

    query = 'A test query.'
    # Mock the search return value
    rag_manager.index.search.return_value = (np.array([[0.1, 0.2]]), np.array([[0, 1]]))

    results = rag_manager.search(query, k=2)

    # Check that encode was called for the query
    rag_manager.model.encode.assert_called_with([query])
    # Check that search was called on the index
    rag_manager.index.search.assert_called_with(np.any(np.ndarray), 2)
    assert len(results) == 2

    assert len(results) == 1
    assert 'doc_id' in results[0]
    assert 'text' in results[0]
    assert 'score' in results[0]