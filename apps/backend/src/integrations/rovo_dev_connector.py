"""
Rovo Dev Connector - 從增強版導入
"""

import logging

from .enhanced_rovo_dev_connector import EnhancedRovoDevConnector

logger = logging.getLogger(__name__)

# 保持向後兼容性
RovoDevConnector = EnhancedRovoDevConnector
