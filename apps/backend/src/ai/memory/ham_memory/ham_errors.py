class HAMMemoryError(Exception):
    """Custom exception for HAM memory operations."""
    pass

class HAMInitializationError(HAMMemoryError):
    """Exception raised for errors during HAM memory initialization."""
    pass

class HAMStorageError(HAMMemoryError):
    """Exception raised for errors during HAM memory storage operations."""
    pass

class HAMRetrievalError(HAMMemoryError):
    """Exception raised for errors during HAM memory retrieval operations."""
    pass
