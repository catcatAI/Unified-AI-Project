"""上下文系统配置"""

import os
from typing import Dict, Any

class ContextConfig:
    """上下文系统配置类"""
    
    def __init__(self) -> None:
        # 存储配置
        self.storage_dir = os.environ.get("CONTEXT_STORAGE_DIR", "./context_storage")
        self.memory_max_size = int(os.environ.get("CONTEXT_MEMORY_MAX_SIZE", "1000"))
        self.disk_storage_enabled = os.environ.get("CONTEXT_DISK_STORAGE_ENABLED", "true").lower() == "true"
        self.database_storage_enabled = os.environ.get("CONTEXT_DATABASE_STORAGE_ENABLED", "false").lower() == "true"
        
        # 缓存配置
        self.cache_enabled = os.environ.get("CONTEXT_CACHE_ENABLED", "true").lower() == "true"
        self.cache_max_size = int(os.environ.get("CONTEXT_CACHE_MAX_SIZE", "100"))
        
        # 性能配置
        self.compression_enabled = os.environ.get("CONTEXT_COMPRESSION_ENABLED", "false").lower() == "true"
        self.async_processing_enabled = os.environ.get("CONTEXT_ASYNC_PROCESSING_ENABLED", "true").lower() == "true"
        
        # 安全配置
        self.encryption_enabled = os.environ.get("CONTEXT_ENCRYPTION_ENABLED", "false").lower() == "true"
        self.access_control_enabled = os.environ.get("CONTEXT_ACCESS_CONTROL_ENABLED", "false").lower() == "true"
        
        # 日志配置
        self.log_level = os.environ.get("CONTEXT_LOG_LEVEL", "INFO")
        self.audit_logging_enabled = os.environ.get("CONTEXT_AUDIT_LOGGING_ENABLED", "true").lower() == "true"
        
        # 集成配置
        self.ham_integration_enabled = os.environ.get("CONTEXT_HAM_INTEGRATION_ENABLED", "true").lower() == "true"
        self.mcp_integration_enabled = os.environ.get("CONTEXT_MCP_INTEGRATION_ENABLED", "true").lower() == "true"
        
    def get_storage_config(self) -> Dict[str, Any]:
        """获取存储配置"""
        return {
            "storage_dir": self.storage_dir,
            "memory_max_size": self.memory_max_size,
            "disk_storage_enabled": self.disk_storage_enabled,
            "database_storage_enabled": self.database_storage_enabled
        }
    
    def get_cache_config(self) -> Dict[str, Any]:
        """获取缓存配置"""
        return {
            "cache_enabled": self.cache_enabled,
            "cache_max_size": self.cache_max_size
        }
    
    def get_performance_config(self) -> Dict[str, Any]:
        """获取性能配置"""
        return {
            "compression_enabled": self.compression_enabled,
            "async_processing_enabled": self.async_processing_enabled
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """获取安全配置"""
        return {
            "encryption_enabled": self.encryption_enabled,
            "access_control_enabled": self.access_control_enabled
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return {
            "log_level": self.log_level,
            "audit_logging_enabled": self.audit_logging_enabled
        }
    
    def get_integration_config(self) -> Dict[str, Any]:
        """获取集成配置"""
        return {
            "ham_integration_enabled": self.ham_integration_enabled,
            "mcp_integration_enabled": self.mcp_integration_enabled
        }

# 全局配置实例
config = ContextConfig

# 配置说明
CONFIGURATION_DOCS = """
# 上下文系统配置说明

## 环境变量配置

### 存储配置
- CONTEXT_STORAGE_DIR: 磁盘存储目录,默认为"./context_storage"
- CONTEXT_MEMORY_MAX_SIZE: 内存存储最大大小,默认为1000
- CONTEXT_DISK_STORAGE_ENABLED: 是否启用磁盘存储,默认为true
- CONTEXT_DATABASE_STORAGE_ENABLED: 是否启用数据库存储,默认为false

### 缓存配置
- CONTEXT_CACHE_ENABLED: 是否启用缓存,默认为true
- CONTEXT_CACHE_MAX_SIZE: 缓存最大大小,默认为100

### 性能配置
- CONTEXT_COMPRESSION_ENABLED: 是否启用数据压缩,默认为false
- CONTEXT_ASYNC_PROCESSING_ENABLED: 是否启用异步处理,默认为true

### 安全配置
- CONTEXT_ENCRYPTION_ENABLED: 是否启用数据加密,默认为false
- CONTEXT_ACCESS_CONTROL_ENABLED: 是否启用访问控制,默认为false

### 日志配置
- CONTEXT_LOG_LEVEL: 日志级别,默认为INFO
- CONTEXT_AUDIT_LOGGING_ENABLED: 是否启用审计日志,默认为true

### 集成配置
- CONTEXT_HAM_INTEGRATION_ENABLED: 是否启用HAM集成,默认为true
- CONTEXT_MCP_INTEGRATION_ENABLED: 是否启用MCP集成,默认为true

## 使用示例

```python
from context.config import config

# 获取存储配置
storage_config = config.get_storage_config
print(f"Storage directory: {storage_config['storage_dir']}")

# 获取缓存配置
cache_config = config.get_cache_config
if cache_config['cache_enabled']:
    print(f"Cache max size: {cache_config['cache_max_size']}")
```
"""