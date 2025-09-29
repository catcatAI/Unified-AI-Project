"""
ChromaDB配置模块，用于解决导入问题
"""

class Settings:
    """ChromaDB设置类的简化实现"""
    def __init__(self, anonymized_telemetry: bool = False, **kwargs: Any) -> None:
        self.anonymized_telemetry = anonymized_telemetry
        self.data = kwargs

    def __getattr__(self, name: str) -> Any:
        return self.data.get(name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ['anonymized_telemetry', 'data']:
            super.__setattr__(name, value)
        else:
            if not hasattr(self, 'data'):
                super.__setattr__('data', )
            self.data[name] = value