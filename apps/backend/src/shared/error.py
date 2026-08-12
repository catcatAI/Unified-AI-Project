class ProjectError(Exception):
    """自定義項目錯誤類"""

    def __init__(self, message: str, code: int = 500) -> None:
        self.message = message
        self.code = code
        super().__init__(f"[Project Error {code}] {message}")


class HSPConnectionError(ProjectError):
    """HSP 連接錯誤"""

    def __init__(self, message: str, code: int = 501):
        super().__init__(f"HSP Connection Error: {message}", code)


def project_error_handler(error: ProjectError) -> None:
    """處理項目錯誤的中央函數"""
    import logging

    logger = logging.getLogger(__name__)
    logger.error(f"Caught Project Error: {error}", exc_info=True)


# ErrorHandler / SecurityError / ResourceError were previously duplicated here as
# ProjectError subclasses, conflicting with the canonical Angela error hierarchy.
# They now re-export the single source of truth from core.angela_error.
from core.angela_error import ErrorHandler, ResourceError, SecurityError  # noqa: F401
