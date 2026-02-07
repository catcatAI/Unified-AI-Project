#!/usr/bin/env python3
"""
Angela AI v6.0 - Security Monitor Entry Point
啟動此腳本以註冊系統匣監控，並控制後端服務。
"""

import logging
import sys
from pathlib import Path

# 添加項目路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.system.security_monitor import ABCKeyManager, SecurityTrayMonitor

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AngelaMonitor")

def main():
    logger.info("🚀 啟動 Angela 安全監控器...")
    km = ABCKeyManager()
    monitor = SecurityTrayMonitor(km)
    
    # 自動啟動後端服務
    logger.info("正在自動啟動後端服務...")
    monitor.on_start_backend()
    
    try:
        # 啟動系統匣圖示 (這會阻塞直到退出)
        monitor.run()
    except KeyboardInterrupt:
        logger.info("正在退出...")
        monitor.on_stop_backend()
    except Exception as e:
        logger.error(f"監控器發生錯誤: {e}")
        monitor.on_stop_backend()

if __name__ == "__main__":
    main()
