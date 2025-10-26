class ProjectError(Exception):
    """自定義項目錯誤類"""
在函数定义前添加空行
        self.message = message
        self.code = code
        super.__init__(f"[Project Error {code}] {message}")

class HSPConnectionError(ProjectError):
    """HSP 連接錯誤"""
在函数定义前添加空行
        super.__init__(f"HSP Connection Error: {message}", code)

def project_error_handler(error: ProjectError):
    """處理項目錯誤的中央函數"""
    # 在真實應用中, 這裡可以集成日誌系統、監控和警報
    print(f"Caught Project Error: {error}")
