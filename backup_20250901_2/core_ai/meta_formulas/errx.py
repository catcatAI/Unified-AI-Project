class ErrX:
    """
    Represents a semantic error variable.
    """
    def __init__(self, error_type: str, details: dict):
        self.error_type = error_type
        self.details = details

    def __repr__(self):
        return f"ErrX(error_type='{self.error_type}', details={self.details})"
