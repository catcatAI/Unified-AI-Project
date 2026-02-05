"""
Angela AI v6.0 - Key Manager (Legacy Support & Refined)
統一金鑰管理器

提供對 A/B/C 密鑰體系的訪問，並保留對舊有配置的相容性。
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

logger = logging.getLogger(__name__)

class UnifiedKeyManager:
    """統一金鑰管理器 (明確區分通訊密鑰與模型金鑰)"""
    
    def __init__(self, config_path: str = "configs/unified_demo_config.yaml") -> None:
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # 1. 系統通訊密鑰 (Angela Secret Keys: A/B/C)
        # 用於內部組件、行動端、桌面端的加密與控制
        try:
            from ..system.security_monitor import ABCKeyManager
            self.abc_km = ABCKeyManager()
        except ImportError:
            self.abc_km = None
            logger.warning("ABCKeyManager 不可用")

    def _load_config(self) -> Dict[str, Any]:
        """載入舊有 YAML 配置 (通常包含模型 API Keys)"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.error(f"載入配置失敗: {e}")
        return {}

    def get_security_key(self, key_name: str) -> Optional[str]:
        """獲取 Angela 系統通訊密鑰 (KeyA, KeyB, KeyC)"""
        if self.abc_km and key_name in ["KeyA", "KeyB", "KeyC"]:
            return self.abc_km.get_key(key_name)
        return None

    def get_api_key(self, service_name: str) -> Optional[str]:
        """獲取外部模型服務金鑰 (如 OpenAI, Anthropic API Keys)"""
        # 優先從環境變量獲取，然後從配置文件獲取
        env_key = os.environ.get(f"{service_name.upper()}_API_KEY")
        if env_key:
            return env_key
        return self.config.get("api_keys", {}).get(service_name)

    def get_key(self, key_name: str) -> Optional[str]:
        """通用檢索 (向下相容)"""
        # 優先檢查是否為 A/B/C 密鑰
        sec_key = self.get_security_key(key_name)
        if sec_key:
            return sec_key
        
        # 否則作為 API 金鑰或環境變量處理
        return os.environ.get(key_name) or self.config.get(key_name)

    def setup_environment(self):
        """設置運行環境金鑰"""
        if self.abc_km:
            for k in ["KeyA", "KeyB", "KeyC"]:
                val = self.abc_km.get_key(k)
                if val:
                    os.environ[k] = val
        logger.info("✅ 安全金鑰環境已設置完成")
