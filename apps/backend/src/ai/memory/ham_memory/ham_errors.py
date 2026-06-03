class HAMMemoryError(Exception):
    """Custom exception for HAM memory operations."""



class HAMInitializationError(HAMMemoryError):
    """Exception raised for errors during HAM memory initialization."""



class HAMStorageError(HAMMemoryError):
    """Exception raised for errors during HAM memory storage operations."""



class HAMRetrievalError(HAMMemoryError):
    """Exception raised for errors during HAM memory retrieval operations."""

