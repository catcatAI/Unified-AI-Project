class HAMMemoryError(Exception):
    """Base exception for HAM memory operations."""
    pass

class HAMQueryError(HAMMemoryError):
    """Exception raised for errors in HAM memory queries."""
    pass

class HAMStoreError(HAMMemoryError):
    """Exception raised for errors during HAM memory storage operations."""
    pass

class VectorStoreError(HAMMemoryError):
    """Exception raised for errors in vector store operations."""
    pass