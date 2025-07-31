#!/usr/bin/env python3
"""
启动 Atlassian API 服务器
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.atlassian_api_server import app

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/atlassian_api_server.log')
        ]
    )

def main():
    """主函数"""
    print("🚀 启动 Atlassian API 服务器...")
    
    # 确保日志目录存在
    os.makedirs('logs', exist_ok=True)
    
    # 设置日志
    setup_logging()
    
    # 启动服务器
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()