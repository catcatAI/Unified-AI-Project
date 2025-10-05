#!/usr/bin/env python3
"""
启动 Atlassian API 服务器
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 注意：这个导入可能需要根据实际项目结构调整
try:
    from src.services.atlassian_api_server import app
except ImportError:
    print("警告: 无法导入 Atlassian API 服务器模块")
    app = None

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

def main() -> None:
    """主函数"""
    print("🚀 启动 Atlassian API 服务器...")

    # 确保日志目录存在
    os.makedirs('logs', exist_ok=True)

    # 设置日志
    setup_logging()

    # 启动服务器
    if app is not None:
        import uvicorn
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    else:
        print("❌ 无法启动服务器: 缺少必要的模块")

if __name__ == "__main__":
    main()