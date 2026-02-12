"""依赖检查器"""

import os
from typing import Dict, Any, List
import logging
logger = logging.getLogger(__name__)


def check_dependencies() -> Dict[str, Any]:
    """检查项目依赖"""
    required_packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "sqlalchemy",
        "chromadb"
    ]

    results = {}
    for package in required_packages:
        try:
            __import__(package)
            results[package] = {"installed": True}
        except ImportError:
            results[package] = {"installed": False, "error": "Not installed"}

    return results


def install_missing_dependencies():
    """安装缺失的依赖"""
    print("请在项目根目录运行以下命令安装依赖:")
    print("pip install -r requirements.txt")