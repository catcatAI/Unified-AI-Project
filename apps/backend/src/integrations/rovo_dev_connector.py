"""
Rovo Dev Connector - 從增強版導入
"""

from .enhanced_rovo_dev_connector import EnhancedRovoDevConnector
import logging
logger = logging.getLogger(__name__)

# 保持向後兼容性
RovoDevConnector = EnhancedRovoDevConnector
