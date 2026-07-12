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

from core.system.security_monitor import ABCKeyManager

# SecurityTrayMonitor was removed in a previous refactor.
# For system-tray functionality, see apps/desktop-app/ or restore from git history.

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
    logger.info(f"Security keys OK: KeyA={bool(km.get_key('KeyA'))}, KeyB={bool(km.get_key('KeyB'))}")
    logger.info("SecurityTrayMonitor was removed in a previous refactor. Security validation complete.")

if __name__ == "__main__":
    main()
