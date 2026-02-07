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

class SecurityError(ProjectError):
    """安全性相關錯誤"""
    def __init__(self, message: str, code: int = 403):
        super().__init__(f"Security Error: {message}", code)

class ResourceError(ProjectError):
    """資源或剩餘餘額不足錯誤"""
    def __init__(self, message: str, code: int = 402):
        super().__init__(f"Resource Error: {message}", code)

def project_error_handler(error: ProjectError):
    """處理項目錯誤的中央函數"""
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Caught Project Error: {error}")

class ErrorHandler:
    """中央錯誤處理器 (Phase 14 Restoration)"""
    @staticmethod
    def handle_error(error: Exception, context: str = "Unknown"):
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in {context}: {error}")
