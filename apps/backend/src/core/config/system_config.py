"""
系统配置模块
"""

import os
from typing import Dict, Any

def get_system_config() -> Dict[str, Any]:
    """获取系统配置"""
    return {
        "environment": os.getenv("ENVIRONMENT", "development"),
        "debug": os.getenv("DEBUG", "true").lower() == "true",
        "host": os.getenv("HOST", "0.0.0.0"),
        "port": int(os.getenv("PORT", "8000")),
        "log_level": os.getenv("LOG_LEVEL", "INFO")
    }