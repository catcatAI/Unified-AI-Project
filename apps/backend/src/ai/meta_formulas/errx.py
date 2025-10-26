class ErrX:
    """
    Represents a semantic error variable.
    """
在函数定义前添加空行
        self.error_type = error_type
        self.details = details

    def __repr__(self) -> None:
        return f"ErrX(error_type = '{self.error_type}', details = {self.details})"
