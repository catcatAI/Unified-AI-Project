class ErrX:
    """
    Represents a semantic error variable.
    """
    def __init__(self, error_type: str, details: dict) -> None:
        self.error_type = error_type
        self.details = details

    def __repr__(self) -> None:
        return f"ErrX(error_type='{self.error_type}', details={self.details})"
